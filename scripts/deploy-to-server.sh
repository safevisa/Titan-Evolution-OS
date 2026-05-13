#!/usr/bin/env bash
# Deploy from your laptop to the Ubuntu host (Docker + Compose).
# Usage:
#   export DEPLOY_HOST=your.server.ip
#   export DEPLOY_USER=ubuntu
#   export DEPLOY_SSH_KEY=/path/to/key.pem   # optional, defaults to repo ./token.pem if present
#   ./scripts/deploy-to-server.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${DEPLOY_HOST:?Set DEPLOY_HOST to the server IP or hostname}"
DEPLOY_USER="${DEPLOY_USER:-ubuntu}"
KEY="${DEPLOY_SSH_KEY:-$ROOT/token.pem}"
if [[ ! -f "$KEY" ]]; then
  echo "SSH private key not found at $KEY (set DEPLOY_SSH_KEY)" >&2
  exit 1
fi
chmod 600 "$KEY"
REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"

echo "==> Sync sources to ${REMOTE}:~/titan-evolution-os-src/"
rsync -az --delete \
  --exclude '.git/' \
  --exclude 'node_modules/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '.next/' \
  --exclude 'token.pem' \
  --exclude '.env' \
  --exclude '.env.local' \
  -e "ssh -i \"$KEY\" -o StrictHostKeyChecking=accept-new" \
  "$ROOT/" "${REMOTE}:~/titan-evolution-os-src/"

echo "==> Remote: compose up (install Docker on the host first if needed)"
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$REMOTE" bash << 'EOS'
set -euo pipefail
cd ~/titan-evolution-os-src
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not installed. Install Docker Engine + compose plugin, then re-run." >&2
  exit 1
fi
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — set POSTGRES_PASSWORD, OPENAI_API_KEY, PUBLIC_API_URL, etc."
fi
docker compose down --remove-orphans 2>/dev/null || true
docker compose build
docker compose up -d
docker compose ps
EOS

echo "Done. Point Nginx at 127.0.0.1:3001 (Next) and 127.0.0.1:8000 (API) using deploy/nginx-tokenply.conf"
