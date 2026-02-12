from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List

from .jira_client import JiraAuth, JiraClient, safe_get
from .mapping_store import MappingStore
from .models import (
    DiscoverProjectsResponse,
    MigrationRequest,
    MigrationResult,
    ProjectMigrationResult,
    ProjectSummary,
)


class Migrator:
    def __init__(self, request: MigrationRequest) -> None:
        self.request = request
        self.run_id = str(uuid.uuid4())
        self.store = MappingStore(request.db_path)
        self.cloud = JiraClient(request.cloud_base_url, JiraAuth(request.cloud_user, request.cloud_token))
        self.dc = JiraClient(request.dc_base_url, JiraAuth(request.dc_user, request.dc_token))

    def _log(self, level: str, message: str) -> None:
        self.store.log(self.run_id, level, message)

    @staticmethod
    def _normalize_key(raw: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9]", "", raw.upper())
        return clean[:10] if clean else "MIG"

    def discover_projects(self) -> DiscoverProjectsResponse:
        projects = self.cloud.list_projects_cloud()
        transformed = [
            ProjectSummary(
                key=p.get("key", ""),
                name=p.get("name", ""),
                project_type_key=p.get("projectTypeKey", "unknown"),
                style=p.get("style", "unknown"),
            )
            for p in projects
            if p.get("key")
        ]
        transformed.sort(key=lambda p: p.key)
        return DiscoverProjectsResponse(projects=transformed)

    def _target_key(self, source_project_key: str) -> str:
        prefix = self._normalize_key(self.request.target_project_prefix)
        source = self._normalize_key(source_project_key)
        composed = f"{prefix}{source}"
        return composed[:10]

    def _build_project_payload(self, target_project_key: str, source_project_key: str) -> Dict[str, Any]:
        return {
            "key": target_project_key,
            "name": f"{self.request.target_project_name_prefix} {source_project_key}",
            "projectTypeKey": "software",
            "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-scrum-classic",
            "lead": self.request.dc_user,
            "assigneeType": "PROJECT_LEAD",
        }

    def _ensure_project(self, source_project_key: str, target_project_key: str) -> bool:
        mapped = self.store.get_project_map(source_project_key)
        if mapped:
            self._log("info", f"project mapping exists: {source_project_key} -> {mapped}")
            return False

        if self.request.dry_run:
            self._log("info", f"dry-run: would create project {target_project_key}")
            self.store.set_project_map(source_project_key, target_project_key)
            return True

        try:
            self.dc.get_project_dc(target_project_key)
            self._log("info", f"destination project exists: {target_project_key}")
        except Exception:
            payload = self._build_project_payload(target_project_key, source_project_key)
            self.dc.create_project_dc(payload)
            self._log("info", f"created destination project {target_project_key}")

        self.store.set_project_map(source_project_key, target_project_key)
        return True

    def _iter_source_issues(self, source_project_key: str):
        done_clause = "" if self.request.include_done else " AND statusCategory != Done"
        jql = f"project = {source_project_key}{done_clause} ORDER BY created ASC"
        start_at = 0
        total_seen = 0
        while True:
            page = self.cloud.search_issues(jql, start_at=start_at, max_results=self.request.issue_batch_size)
            issues = page.get("issues", [])
            if not issues:
                break
            for issue in issues:
                yield issue
                total_seen += 1
                if total_seen >= self.request.max_issues_per_project:
                    return
            start_at += len(issues)

    def _map_issue_payload(self, issue: Dict[str, Any], target_project_key: str) -> Dict[str, Any]:
        fields = issue.get("fields", {})
        summary = fields.get("summary") or f"Migrated issue from {issue['key']}"
        description = fields.get("description")
        issue_type_name = safe_get(fields, "issuetype", "name", default="Task")
        priority_name = safe_get(fields, "priority", "name")

        payload: Dict[str, Any] = {
            "fields": {
                "project": {"key": target_project_key},
                "summary": summary,
                "issuetype": {"name": issue_type_name},
                "labels": fields.get("labels", []),
            }
        }

        if description:
            payload["fields"]["description"] = description
        if priority_name:
            payload["fields"]["priority"] = {"name": priority_name}

        return payload

    def _migrate_comments(self, cloud_issue_key: str, dc_issue_key: str) -> int:
        if not self.request.migrate_comments:
            return 0
        comments = self.cloud.list_comments_cloud(cloud_issue_key)
        created = 0
        for comment in comments:
            body = comment.get("body")
            if not body:
                continue
            body_text = body if isinstance(body, str) else str(body)
            if self.request.dry_run:
                created += 1
                continue
            self.dc.create_comment_dc(dc_issue_key, f"[migrated from {cloud_issue_key}]\n{body_text}")
            created += 1
        return created

    def _migrate_single_project(self, source_project_key: str) -> ProjectMigrationResult:
        target_project_key = self._target_key(source_project_key)
        notes: List[str] = []

        source_project = self.cloud.get_project(source_project_key)
        source_style = source_project.get("style", "unknown")
        source_type = source_project.get("projectTypeKey", "unknown")

        if source_style.lower() == "next-gen":
            notes.append("Team-managed project detected. Project config parity may need manual follow-up.")

        created_project = self._ensure_project(source_project_key, target_project_key)
        issues_scanned = 0
        issues_created = 0
        comments_created = 0
        skipped_issues = 0

        for issue in self._iter_source_issues(source_project_key):
            issues_scanned += 1
            cloud_key = issue["key"]
            if self.store.get_issue_map(cloud_key):
                skipped_issues += 1
                continue

            payload = self._map_issue_payload(issue, target_project_key)
            if self.request.dry_run:
                dc_issue_key = f"{target_project_key}-DRY-{issues_scanned}"
            else:
                created_issue = self.dc.create_issue_dc(payload)
                dc_issue_key = created_issue["key"]

            self.store.set_issue_map(cloud_key, dc_issue_key)
            issues_created += 1
            comments_created += self._migrate_comments(cloud_key, dc_issue_key)

        return ProjectMigrationResult(
            source_project_key=source_project_key,
            target_project_key=target_project_key,
            created_project=created_project,
            source_project_type=f"{source_type}/{source_style}",
            issues_scanned=issues_scanned,
            issues_created=issues_created,
            comments_created=comments_created,
            skipped_issues=skipped_issues,
            notes=notes,
        )

    def run(self) -> MigrationResult:
        project_results = [self._migrate_single_project(key) for key in self.request.source_project_keys]
        self._log("info", f"run complete for {len(project_results)} project(s)")
        return MigrationResult(run_id=self.run_id, dry_run=self.request.dry_run, projects=project_results)
