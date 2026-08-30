#!/usr/bin/env bash
# Start the local dev server. Any flags are passed through to dev-server.py,
# e.g. ./serve.sh --port 8080 --no-open
set -euo pipefail
cd "$(dirname "$0")"
exec python3 dev-server.py "$@"
