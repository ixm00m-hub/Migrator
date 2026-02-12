from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from jira_migrator.jira_client import JiraAuth, JiraClient
from jira_migrator.migrator import Migrator
from jira_migrator.models import (
    DiscoverProjectsRequest,
    DiscoverProjectsResponse,
    MigrationRequest,
    MigrationResult,
)

app = FastAPI(title="Jira Cloud to DC Migrator", version="0.2.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/projects/discover", response_model=DiscoverProjectsResponse)
def discover_projects(request: DiscoverProjectsRequest) -> DiscoverProjectsResponse:
    try:
        cloud = JiraClient(request.cloud_base_url, JiraAuth(request.cloud_user, request.cloud_token))
        projects = cloud.list_projects_cloud()
        return DiscoverProjectsResponse(
            projects=[
                {
                    "key": p.get("key", ""),
                    "name": p.get("name", ""),
                    "project_type_key": p.get("projectTypeKey", "unknown"),
                    "style": p.get("style", "unknown"),
                }
                for p in projects
                if p.get("key")
            ]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/migrate", response_model=MigrationResult)
def migrate(request: MigrationRequest) -> MigrationResult:
    try:
        migrator = Migrator(request)
        return migrator.run()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
