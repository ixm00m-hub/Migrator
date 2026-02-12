from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class JiraAuth:
    username: str
    token: str


class JiraClient:
    def __init__(self, base_url: str, auth: JiraAuth, timeout_s: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.auth = (auth.username, auth.token)
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        retries = 3
        for attempt in range(retries):
            response = self.session.request(method, url, timeout=self.timeout_s, **kwargs)
            if response.status_code in (429, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            if response.text:
                return response.json()
            return None
        raise RuntimeError(f"request failed after retries: {method} {path}")

    # Cloud endpoints
    def list_projects_cloud(self) -> List[Dict[str, Any]]:
        # returns all visible projects to provided principal
        return self._request("GET", "/rest/api/3/project/search?maxResults=1000").get("values", [])

    def get_project(self, project_key: str) -> Dict[str, Any]:
        return self._request("GET", f"/rest/api/3/project/{project_key}")

    def search_issues(self, jql: str, start_at: int = 0, max_results: int = 100) -> Dict[str, Any]:
        payload = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": [
                "summary",
                "description",
                "issuetype",
                "priority",
                "labels",
                "project",
            ],
        }
        return self._request("POST", "/rest/api/3/search", json=payload)

    def list_comments_cloud(self, issue_key: str) -> List[Dict[str, Any]]:
        data = self._request("GET", f"/rest/api/3/issue/{issue_key}/comment")
        return data.get("comments", [])

    # DC endpoints (compatible with v2)
    def get_project_dc(self, project_key: str) -> Dict[str, Any]:
        return self._request("GET", f"/rest/api/2/project/{project_key}")

    def create_project_dc(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/rest/api/2/project", json=payload)

    def create_issue_dc(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/rest/api/2/issue", json=payload)

    def create_comment_dc(self, issue_key: str, body: str) -> Dict[str, Any]:
        return self._request("POST", f"/rest/api/2/issue/{issue_key}/comment", json={"body": body})


def safe_get(d: Dict[str, Any], *keys: str, default: Optional[Any] = None) -> Any:
    current: Any = d
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            return default
        current = current[k]
    return current
