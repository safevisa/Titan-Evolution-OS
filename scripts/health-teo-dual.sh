#!/usr/bin/env bash
# TEO-DUAL health checks — see docs/development/07-可观测性与排障手册.md
set -euo pipefail
echo "=== Titan backend ==="
curl -sf http://127.0.0.1:8000/docs >/dev/null && echo "OK backend /docs" || echo "FAIL backend"
echo "=== Celery beat (M02 requires) ==="
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q celery_beat; then
  echo "OK celery_beat container"
else
  echo "SKIP/WARN: no celery_beat container (enable in M06 before Context Sync)"
fi
echo "=== Computer Use runner (M03) ==="
if curl -sf http://127.0.0.1:8090/health >/dev/null 2>&1; then
  echo "OK computer-use-runner"
else
  echo "SKIP runner (not deployed yet)"
fi
