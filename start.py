from __future__ import annotations

import argparse
import importlib
import sys

REQUIRED_MODULES = ["fastapi", "uvicorn", "pydantic", "requests"]


def _missing_modules() -> list[str]:
    missing: list[str] = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception:
            missing.append(module)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start the Jira Cloud -> Data Center migrator web app."
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8080, type=int)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only validate runtime dependencies and exit.",
    )
    args = parser.parse_args()

    missing = _missing_modules()
    if missing:
        print(
            "Missing dependencies: "
            + ", ".join(missing)
            + "\nRun: pip install -r requirements.txt"
        )
        return 1

    if args.check:
        print("Dependency check passed.")
        return 0

    import uvicorn

    uvicorn.run("main:app", app_dir="app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
