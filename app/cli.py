from __future__ import annotations

import argparse
import json

from jira_migrator.migrator import Migrator
from jira_migrator.models import MigrationRequest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate Jira Cloud projects to Jira Data Center")
    parser.add_argument("--cloud-base-url", required=True)
    parser.add_argument("--cloud-user", required=True)
    parser.add_argument("--cloud-token", required=True)
    parser.add_argument("--dc-base-url", required=True)
    parser.add_argument("--dc-user", required=True)
    parser.add_argument("--dc-token", required=True)
    parser.add_argument("--source-project-keys", required=True, help="Comma-separated list, e.g. SRC1,SRC2")
    parser.add_argument("--target-project-prefix", default="MIG")
    parser.add_argument("--target-project-name-prefix", default="Migrated")
    parser.add_argument("--max-issues-per-project", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--db-path", default="./.migrator/mappings.sqlite3")
    parser.add_argument("--include-done", action="store_true")
    parser.add_argument("--migrate-comments", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_project_keys = [x.strip() for x in args.source_project_keys.split(",") if x.strip()]
    request = MigrationRequest(
        cloud_base_url=args.cloud_base_url,
        cloud_user=args.cloud_user,
        cloud_token=args.cloud_token,
        dc_base_url=args.dc_base_url,
        dc_user=args.dc_user,
        dc_token=args.dc_token,
        source_project_keys=source_project_keys,
        target_project_prefix=args.target_project_prefix,
        target_project_name_prefix=args.target_project_name_prefix,
        dry_run=args.dry_run,
        max_issues_per_project=args.max_issues_per_project,
        migrate_comments=args.migrate_comments,
        include_done=args.include_done,
        issue_batch_size=args.batch_size,
        db_path=args.db_path,
    )
    result = Migrator(request).run()
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
