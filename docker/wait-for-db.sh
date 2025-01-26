#!/bin/bash
set -e

host="$1"
shift

until pg_isready -h "$host" -p 5432 -q; do
  >&2 echo "Ожидание db Postgres"
  sleep 1
done

>&2 echo "Postgres is up - выполнение команды"
exec "$@"