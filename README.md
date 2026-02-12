# Jira Cloud → Data Center Migrator (Runnable App)

This is a **run-now MVP app** with a web UI for Cloud → Data Center migration runs.

## What you get
- Browser-based front end to enter source/target credentials
- Project discovery from Jira Cloud and checkbox-based project selection
- Migration options (dry-run, comments, batch size, limits)
- Backend API that executes migration and stores mappings in SQLite
- Dockerized deployment option

## Fastest way to run locally (Windows/Linux/macOS)
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python start.py
```
Then open:
- http://localhost:8080

## One-command Docker run
```bash
./run.sh
```
Then open:
- http://localhost:8080

## VS Code + Codex workflow
If you run this repository in VS Code with Codex tooling attached, Codex can start it with:
```bash
python start.py
```
And then you access:
- http://localhost:8080

## Dependency sanity check (no server start)
```bash
python start.py --check
```

## Main API endpoints
- `GET /health`
- `POST /api/projects/discover`
- `POST /api/migrate`

## Why you might not see it when someone else "ran it"
If the app is started inside a remote container/VM, that environment's `localhost` is not your laptop's `localhost` unless port-forwarding is enabled. Running `python start.py` directly on your machine avoids that confusion.

## Notes
- Team-managed (`next-gen`) projects are detected and migrated with issue/comment-first strategy.
- Mappings are persisted in `./.migrator/mappings.sqlite3` for resumable reruns.
- This version prioritizes fast usability and core migration flow.

## Next upgrades
- Attachments, issue links, worklogs
- Better ADF translation for descriptions/comments
- Workflow/scheme migration helpers for deeper parity
- Job queue + progress bars for very large migrations
