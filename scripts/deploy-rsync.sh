#!/usr/bin/env bash
# Sync repo to production host over SSH (example). Usage:
#   export DEPLOY_HOST=ubuntu@YOUR_IP
#   export DEPLOY_KEY=/path/to/token.pem
#   export DEPLOY_PATH=~/titan-evolution-os-src
#   ./scripts/deploy-rsync.sh
set -euo pipefail
: "${DEPLOY_HOST:?Set DEPLOY_HOST e.g. ubuntu@43.128.80.35}"
: "${DEPLOY_KEY:?Set DEPLOY_KEY path to SSH private key}"
: "${DEPLOY_PATH:?Set DEPLOY_PATH on server e.g. ~/titan-evolution-os-src}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH=(ssh -i "$DEPLOY_KEY" -o StrictHostKeyChecking=accept-new)
RSYNC=(rsync -avz -e "ssh -i $DEPLOY_KEY -o StrictHostKeyChecking=accept-new")
"${RSYNC[@]}" \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude '.cursor' \
  --exclude 'terminals' \
  --exclude 'token.pem' \
  --exclude '*.pem' \
  "$ROOT/" "$DEPLOY_HOST:$DEPLOY_PATH/"
echo "Synced. On server run: cd $DEPLOY_PATH && docker compose up -d --build"
