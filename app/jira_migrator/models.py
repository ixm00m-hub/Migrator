from __future__ import annotations

from pydantic import BaseModel, Field


class JiraConnection(BaseModel):
    base_url: str
    user: str
    token: str


class ProjectSummary(BaseModel):
    key: str
    name: str
    project_type_key: str = "unknown"
    style: str = "unknown"


class DiscoverProjectsRequest(BaseModel):
    cloud_base_url: str
    cloud_user: str
    cloud_token: str


class DiscoverProjectsResponse(BaseModel):
    projects: list[ProjectSummary]


class MigrationRequest(BaseModel):
    cloud_base_url: str
    cloud_user: str
    cloud_token: str
    dc_base_url: str
    dc_user: str
    dc_token: str
    source_project_keys: list[str] = Field(..., description="Cloud project keys to migrate")
    target_project_prefix: str = Field("MIG", description="Prefix for destination keys")
    target_project_name_prefix: str = Field("Migrated", description="Prefix for destination names")
    dry_run: bool = True
    max_issues_per_project: int = 500
    migrate_comments: bool = True
    include_done: bool = True
    issue_batch_size: int = 100
    db_path: str = "./.migrator/mappings.sqlite3"


class ProjectMigrationResult(BaseModel):
    source_project_key: str
    target_project_key: str
    created_project: bool
    source_project_type: str
    issues_scanned: int
    issues_created: int
    comments_created: int
    skipped_issues: int
    notes: list[str]


class MigrationResult(BaseModel):
    run_id: str
    dry_run: bool
    projects: list[ProjectMigrationResult]
