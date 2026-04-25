#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m community.server --host 127.0.0.1 --port "${PORT:-8765}" --data-dir .community-state

