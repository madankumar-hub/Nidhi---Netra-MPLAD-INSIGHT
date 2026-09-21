#!/usr/bin/env bash
# One-shot local setup for MPLAD Insight (macOS / Linux).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backend"
cd "$ROOT/backend"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  # Portable in-place edit (GNU sed and BSD sed differ on -i).
  python - "$SECRET" <<'PY'
import pathlib, sys
secret = sys.argv[1]
path = pathlib.Path('.env')
text = path.read_text()
text = text.replace('JWT_SECRET_KEY=change-me-generate-a-long-random-secret',
                    f'JWT_SECRET_KEY={secret}')
path.write_text(text)
PY
  echo "    created backend/.env with a generated JWT_SECRET_KEY"
fi

echo "==> Seeding the database"
python -m seed.seed_data --reset --projects 600

echo "==> Checks"
python -m tests.test_risk_engine
python tools/static_check.py

echo "==> Frontend"
cd "$ROOT/frontend"
npm install
[ -f .env ] || cp .env.example .env
npm run build

cd "$ROOT"
python3 tools/check_api_contract.py

cat <<'MSG'

Setup complete.

  Terminal 1:  cd backend  && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
  Terminal 2:  cd frontend && npm run dev

  Web app: http://localhost:5173
  API docs: http://localhost:8000/docs

  Sign-in credentials: backend/.seed-credentials.txt (delete it when you are done).
MSG
