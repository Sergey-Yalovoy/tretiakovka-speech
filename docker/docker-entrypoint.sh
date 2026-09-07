#!/bin/sh
set -e

ROLE="${1:-api}"

wait_for_postgres() {
    echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
    python - <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("DB_HOST", "postgres")
port = int(os.environ.get("DB_PORT", "5432"))

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            sys.exit(0)
    except OSError:
        time.sleep(1)

print(f"PostgreSQL {host}:{port} is not reachable", file=sys.stderr)
sys.exit(1)
PY
}

case "$ROLE" in
api)
    wait_for_postgres
    alembic upgrade head
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    ;;
parser)
    wait_for_postgres
    # Миграции применяет api-контейнер; парсер ждёт своей очереди на старте стека.
    exec python -m app.parser.worker
    ;;
*)
    exec "$@"
    ;;
esac
