#!/usr/bin/env sh
set -e

echo "[entrypoint] aguardando o PostgreSQL..."
python - <<'PY'
import os, sys, time
import psycopg

dsn = (
    f"host={os.environ.get('POSTGRES_HOST', 'db')} "
    f"port={os.environ.get('POSTGRES_PORT', '5432')} "
    f"dbname={os.environ.get('POSTGRES_DB', 'ieducar')} "
    f"user={os.environ.get('POSTGRES_USER', 'ieducar')} "
    f"password={os.environ.get('POSTGRES_PASSWORD', 'ieducar')}"
)
for tentativa in range(1, 31):
    try:
        with psycopg.connect(dsn, connect_timeout=3):
            print("[entrypoint] PostgreSQL disponível.")
            sys.exit(0)
    except Exception as erro:  # noqa: BLE001
        print(f"[entrypoint] tentativa {tentativa}/30 falhou: {erro}")
        time.sleep(2)
sys.exit("[entrypoint] PostgreSQL indisponível após 60s.")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "[entrypoint] garantindo superusuário..."
  python manage.py createsuperuser --noinput 2>/dev/null || true
fi

exec "$@"
