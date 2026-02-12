# Jira Cloud → Jira Data Center Migration App Plan

## 1) Goal and Scope
Build an application that migrates Jira projects from **Jira Cloud** to **Jira Data Center (DC)** with high fidelity, including:
- Company-managed projects
- Team-managed projects (next-gen)
- Issues and history-rich artifacts where possible
- Configurations needed to keep behavior close to source

The app should support both one-time migrations and incremental reruns.

## 2) Design Principles
1. **Fidelity first**: Preserve IDs/references through mapping tables.
2. **Deterministic reruns**: Same input should produce same mapped output.
3. **Chunked + resumable**: Handle large projects with checkpoints.
4. **Transparent gaps**: Explicitly report items that cannot be migrated exactly.
5. **Safe by default**: Dry-run mode, rate limiting, and rollback-oriented strategy.

## 3) High-Level Architecture
- **Connector Layer**
  - Jira Cloud REST client (v3 + Agile APIs where needed)
  - Jira DC REST client (v2 + admin endpoints available in DC)
- **Discovery & Extraction**
  - Export project metadata, schemes, users, custom fields, workflows, screens, issue types, boards, sprints, issues, comments, attachments, links
- **Canonical Intermediate Model**
  - Internal normalized representation of project config + data
- **Transformation Engine**
  - Cloud model → DC-compatible model
  - Team-managed decomposition to classic/DC constructs
- **Load Engine**
  - Ordered creation: global dependencies, project, then issues/artifacts
- **State Store**
  - Mapping DB (Cloud IDs ↔ DC IDs), checkpoints, run logs, audit records
- **Validation & Reporting**
  - Reconciliation reports and post-migration checks
- **UI + API**
  - Job orchestration, dry-run diff views, progress and exception handling

## 4) Core Migration Phases

### Phase A — Readiness & Preflight
- Validate source/destination permissions.
- Inspect DC version and installed apps.
- Detect unsupported entities and app-owned data.
- Build migration inventory and risk matrix.

### Phase B — Foundation Objects
- Migrate users/groups strategy (federated identity vs local).
- Create/reconcile custom fields.
- Create issue types, priorities, resolutions, statuses.
- Rebuild workflows and workflow schemes.
- Rebuild screens/screen schemes/field configurations.
- Recreate permission and notification schemes.

### Phase C — Project Layer
- Create target projects and apply mapped schemes.
- For team-managed projects:
  - Convert project-scoped configs into DC-compatible schemes.
  - Split unique statuses/workflows into project-specific schemes when needed.
  - Preserve board semantics as closely as possible.

### Phase D — Agile Layer
- Recreate boards, filters, sprints (active/closed ordering).
- Rehydrate backlog ordering where API allows.

### Phase E — Issue/Data Layer
- Create issue hierarchy in dependency order (epics/parents/subtasks).
- Migrate issue fields, comments, worklogs, attachments, links, watchers, votes.
- Preserve timestamps/authors where DC permissions allow.
- Migrate changelog/history where feasible; otherwise attach archived history artifact.

### Phase F — Validation & Cutover
- Count checks (issues/comments/attachments/worklogs).
- Randomized deep record diff checks.
- JQL parity checks for agreed critical filters.
- Produce final report with hard/soft mismatches.

## 5) Team-Managed Project Handling Strategy
Team-managed is the hardest part because Cloud allows project-local configuration patterns that don't map 1:1 to DC.

Approach:
1. **Discover local schema** for each team-managed project (statuses, fields, workflows, boards).
2. **Generate project-dedicated DC schemes** to avoid cross-project collisions.
3. **Field mapping policy**:
   - Reuse existing equivalent DC fields where safe.
   - Otherwise create namespaced fields (e.g., `TM_<projectkey>_<fieldname>`).
4. **Workflow translation**:
   - Convert simplified workflow transitions into explicit DC workflow XML model.
   - Preserve transition names/conditions/post-functions when representable.
5. **Entity fallback**:
   - Unsupported constructs are serialized to migration notes attached to project.

## 6) Data Mapping Model (Critical)
Maintain durable mapping tables:
- `project_map(cloud_project_id, dc_project_id)`
- `issue_map(cloud_issue_id, dc_issue_id, cloud_key, dc_key)`
- `field_map(cloud_field_id, dc_field_id)`
- `user_map(cloud_account_id, dc_user_key)`
- `sprint_map`, `board_map`, `version_map`, `component_map`

Use these maps to ensure idempotent retries and relation preservation.

## 7) API/Execution Workflow
1. Create migration job.
2. Run preflight and show migration plan/diff.
3. Optional user edits to mapping policies.
4. Execute with checkpoints per stage + batch.
5. Retry failed batches with exponential backoff.
6. Final verification + downloadable audit package.

## 8) Non-Functional Requirements
- **Performance**: parallel fetch/load workers with API budget control.
- **Scalability**: support 1M+ issues through chunking/streaming.
- **Reliability**: checkpointing, idempotent upserts, resumable jobs.
- **Security**: encrypted secrets, least-privilege credentials, audit trails.
- **Observability**: structured logs, stage metrics, per-entity error catalog.

## 9) Suggested Tech Stack
- Backend: TypeScript (NestJS) or Python (FastAPI)
- Queue: Redis + BullMQ / Celery
- DB: PostgreSQL for mappings/checkpoints
- Object store: S3-compatible for attachment staging + history archives
- Frontend: React for run setup and progress dashboards

## 10) Milestone Plan

### Milestone 1 (2–3 weeks): POC
- Single company-managed project
- Core configs + issues/comments/attachments
- Mapping DB + dry-run + basic report

### Milestone 2 (3–4 weeks): Team-managed MVP
- Team-managed config extraction and translation
- Project-dedicated scheme synthesis
- Agile artifacts (boards/sprints) baseline

### Milestone 3 (3–4 weeks): Scale & hardening
- Parallelization, checkpoint resume, retry mechanics
- Large dataset performance tuning
- Enhanced validation and mismatch classification

### Milestone 4 (2 weeks): Cutover readiness
- Incremental delta migration mode
- Operational runbooks + rollback/cutover guides
- Security/compliance and UAT support

## 11) Key Risks and Mitigations
- **Plugin/app data incompatibility** → plugin adapters + explicit exclusions.
- **History fidelity limits** → archive strategy + reference links.
- **Identity mismatch** → pre-migration identity reconciliation tooling.
- **Rate limits and timeouts** → adaptive throttling + queue backpressure.

## 12) Immediate Next Steps
1. Confirm supported Jira Cloud and Jira DC versions.
2. Define exact fidelity targets (must-have vs nice-to-have).
3. Build API inventory matrix (source endpoint ↔ destination endpoint).
4. Implement preflight + canonical model first before load logic.
5. Pilot with one company-managed and one team-managed project.
