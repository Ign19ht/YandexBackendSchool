set -e

. /opt/pysetup/.venv/bin/activate
#alembic upgrade head

exec "$@"
