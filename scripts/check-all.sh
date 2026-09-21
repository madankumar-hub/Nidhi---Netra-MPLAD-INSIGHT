#!/usr/bin/env bash
# Run every check that does not need a running server.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "── risk engine tests ─────────────────────────────────"
(cd "$ROOT/backend" && python -m tests.test_risk_engine)

echo
echo "── backend static analysis ───────────────────────────"
(cd "$ROOT/backend" && python tools/static_check.py)

echo
echo "── frontend / backend API contract ───────────────────"
(cd "$ROOT" && python tools/check_api_contract.py)

echo
echo "── frontend type check and build ─────────────────────"
if [ -d "$ROOT/frontend/node_modules" ]; then
  (cd "$ROOT/frontend" && npm run build)
else
  echo "  skipped: run 'npm install' in frontend/ first"
fi
