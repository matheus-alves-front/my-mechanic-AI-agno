#!/usr/bin/env bash
set -euo pipefail

: "${HOST:=0.0.0.0}"
: "${PORT:=8080}"

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w 2 \
  -b "${HOST}:${PORT}" \
  --timeout 120 \
  "app.main:app"
