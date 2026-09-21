#!/usr/bin/env bash
#
# Run every check in one command.
#
#   ./verify.sh
#
# Nothing here needs the npm registry or a database, so it runs on a fresh
# clone. The TypeScript check uses the generated stubs in tools/typecheck/ when
# node_modules is absent, and the real typings when it is present.
set -uo pipefail

cd "$(dirname "$0")"

GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

failures=0

step() {
  local title="$1"
  shift
  printf '\n%s==> %s%s\n' "$BOLD" "$title" "$RESET"
  if "$@"; then
    printf '%s    ok%s\n' "$GREEN" "$RESET"
  else
    printf '%s    FAILED%s\n' "$RED" "$RESET"
    failures=$((failures + 1))
  fi
}

run_backend_tests() {
  (cd backend && PYTHONPATH=. python3 tests/run_all.py)
}

run_static_check() {
  (cd backend && python3 tools/static_check.py)
}

run_typecheck() {
  # Prefer the project's own TypeScript once dependencies are installed; that
  # is the authoritative check. Otherwise fall back to the generated stubs,
  # which need a `tsc` on PATH but never the npm registry.
  if [ -x frontend/node_modules/.bin/tsc ]; then
    (cd frontend && ./node_modules/.bin/tsc --noEmit)
  elif command -v tsc >/dev/null 2>&1; then
    python3 tools/typecheck/generate_stubs.py >/dev/null
    tsc -p tools/typecheck/tsconfig.json
  else
    printf '    skipped: no tsc on PATH and frontend/node_modules is absent.\n'
    printf '    Run "cd frontend && npm install" for the authoritative check.\n'
  fi
}

step "Backend tests"        run_backend_tests
step "Backend static check" run_static_check
step "API contract"         python3 tools/check_api_contract.py
step "Translations"         python3 tools/check_i18n.py
step "TypeScript"           run_typecheck

printf '\n%s' "$BOLD"
if [ "$failures" -eq 0 ]; then
  printf '%sAll checks passed.%s\n' "$GREEN" "$RESET"
else
  printf '%s%d check(s) failed.%s\n' "$RED" "$failures" "$RESET"
fi
exit "$failures"
