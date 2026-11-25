#!/usr/bin/env bash
# Starts ONLY a new disposable PostgreSQL instance; never accepts a target URL.
set -euo pipefail
cd "$(dirname "$0")/../.."
fixture=$(cat tests/golden/ownership-compatibility.json)
if [[ -n ${PG_BINDIR:-} ]]; then
  [[ $("$PG_BINDIR/postgres" --version) == *" 16."* ]] || { echo "Expected PostgreSQL 16" >&2; exit 1; }
  tmp=$(mktemp -d /tmp/pibras-pg16.XXXXXXXX)
  cleanup() {
    if [[ -e $tmp/data/postmaster.pid ]]; then
      "$PG_BINDIR/pg_ctl" -D "$tmp/data" -m immediate -w stop >/dev/null || { echo "Cleanup failed: $tmp" >&2; exit 1; }
    fi
    rm -rf "$tmp"
    echo "Removed disposable PostgreSQL cluster"
  }
  trap cleanup EXIT
  trap 'exit 1' HUP INT TERM
  "$PG_BINDIR/initdb" -D "$tmp/data" -U postgres -A trust --encoding=UTF8 --no-locale >/dev/null
  "$PG_BINDIR/pg_ctl" -D "$tmp/data" -l "$tmp/log" -o "-h '' -k $tmp -p 5432" -w start >/dev/null
  client=(env -i PATH="$PATH" "$PG_BINDIR/psql" -h "$tmp" -p 5432)
else
  container=$(docker run -d --network none -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine)
  cleanup() { docker rm -f "$container" >/dev/null && echo "Removed disposable PostgreSQL container"; }
  trap cleanup EXIT
  trap 'exit 1' HUP INT TERM
  # The official entrypoint starts a temporary socket-only server before the
  # final postmaster. Probe loopback TCP inside this network-isolated container.
  for ((i=0; i<60; i++)); do
    if docker exec "$container" pg_isready -q -h 127.0.0.1 -U postgres; then break; fi
    sleep 1
  done
  client=(docker exec -i "$container" psql -h 127.0.0.1)
fi
psql16() { "${client[@]}" -U postgres -d postgres -X -q -v ON_ERROR_STOP=1 "$@"; }
version=$(psql16 -Atc 'SHOW server_version')
[[ $version == 16.* ]] || { echo "Expected PostgreSQL 16, found $version" >&2; exit 1; }
echo "PostgreSQL $version"
for sql in db/schema.sql tests/postgres/*.sql; do
  echo "Checking $sql"
  psql16 -v ownership_fixture="$fixture" -f - < "$sql"
done
