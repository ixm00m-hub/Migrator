#!/usr/bin/env bash
set -euo pipefail

mkdir -p .migrator

docker compose up --build
