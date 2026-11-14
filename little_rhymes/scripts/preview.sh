#!/usr/bin/env bash
set -euo pipefail
preview_port=${PORT:-3000}
while [ "$#" -gt 0 ]; do
  case "$1" in
    --port) preview_port=$2; shift 2 ;;
    --host) shift 2 ;;
    *) shift ;;
  esac
done
if [ -x .venv/bin/python ]; then
  runtime_python=.venv/bin/python
elif [ -x ../.venv/bin/python ]; then
  runtime_python=../.venv/bin/python
else
  runtime_python=python
fi
exec "$runtime_python" manage.py runserver "0.0.0.0:${preview_port}" --noreload
