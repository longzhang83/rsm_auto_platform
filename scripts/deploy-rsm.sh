#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_HOST="${SSH_HOST:-rsm}"
REMOTE_DIR="${REMOTE_DIR:-/home/louis/code/rsm_auto_platform}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.rsm.yml}"
APP_URL="${APP_URL:-http://127.0.0.1:18080}"
PUBLIC_URL="${PUBLIC_URL:-http://10.31.0.4:18080}"

log() {
    printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_remote() {
    local env_prefix
    printf -v env_prefix 'REMOTE_DIR=%q COMPOSE_FILE=%q APP_URL=%q PUBLIC_URL=%q' \
        "$REMOTE_DIR" "$COMPOSE_FILE" "$APP_URL" "$PUBLIC_URL"
    ssh "$SSH_HOST" "$env_prefix bash -s" "$@"
}

cd "$ROOT_DIR"

log "Deploying rsm_auto_platform to ${SSH_HOST}:${REMOTE_DIR}"

if ! command -v rsync >/dev/null 2>&1; then
    echo "ERROR: rsync is required on the local machine."
    exit 1
fi

if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "$SSH_HOST" "true" >/dev/null 2>&1; then
    echo "ERROR: cannot connect to SSH host '${SSH_HOST}'."
    exit 1
fi

log "Preparing remote directory"
ssh "$SSH_HOST" "mkdir -p '$REMOTE_DIR'"

log "Syncing project files"
rsync -az --delete \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='data/' \
    --exclude='logs/' \
    --exclude='backups/' \
    --exclude='static/' \
    --exclude='frontend/node_modules/' \
    --exclude='frontend/dist/' \
    --exclude='backend/.venv/' \
    --exclude='backend/rsm_auto_platform.db' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "$ROOT_DIR"/ "$SSH_HOST:$REMOTE_DIR"/

log "Building and restarting remote services"
run_remote <<'REMOTE_SCRIPT'
set -Eeuo pipefail

cd "$REMOTE_DIR"

if [ ! -f ".env" ]; then
    echo "ERROR: remote .env does not exist at $REMOTE_DIR/.env"
    echo "Create it from .env.example and fill production secrets before deploying."
    exit 1
fi

if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
fi

if ! $SUDO docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not available or current user cannot access it."
    exit 1
fi

if $SUDO docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="$SUDO docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="$SUDO docker-compose"
else
    echo "ERROR: Docker Compose is not installed."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is required on the remote server to build the frontend."
    exit 1
fi

mkdir -p data logs/nginx backups

DEPLOY_TS="$(date '+%Y%m%d-%H%M%S')"
BACKUP_DIR="backups/deploy-$DEPLOY_TS"
mkdir -p "$BACKUP_DIR"

if [ -f "data/rsm_auto_platform.db" ]; then
    cp -a "data/rsm_auto_platform.db" "$BACKUP_DIR/rsm_auto_platform.db"
fi

if [ -d "static" ]; then
    tar -czf "$BACKUP_DIR/static.tar.gz" static
fi

if ls data/*.xlsx data/*.csv >/dev/null 2>&1; then
    sha256sum data/*.xlsx data/*.csv > "$BACKUP_DIR/data-sha256.txt" || true
fi

echo "Backup directory: $REMOTE_DIR/$BACKUP_DIR"

echo "Installing frontend dependencies..."
cd frontend
if [ -f package-lock.json ]; then
    npm ci --prefer-offline --no-audit
else
    npm install --no-audit
fi

echo "Building frontend..."
npm run build
cd ..

if [ -d "frontend/dist" ]; then
    rm -rf static
    mkdir -p static
    cp -a frontend/dist/. static/
elif [ -f "static/index.html" ]; then
    echo "Frontend build output is already in static/."
else
    echo "ERROR: frontend build output not found."
    exit 1
fi

echo "Starting Docker services..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build --force-recreate

echo "Waiting for health checks..."
for i in $(seq 1 40); do
    if curl -fsS "$APP_URL/health" >/dev/null 2>&1 && \
       curl -fsS "$APP_URL/backend-health" >/dev/null 2>&1; then
        break
    fi

    if [ "$i" -eq 40 ]; then
        echo "ERROR: service health check failed."
        $COMPOSE_CMD -f "$COMPOSE_FILE" ps
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=120 backend
        exit 1
    fi

    sleep 3
done

$COMPOSE_CMD -f "$COMPOSE_FILE" ps

echo
echo "Deployment completed."
echo "Local health: $APP_URL/health"
echo "Public URL:   $PUBLIC_URL/"
REMOTE_SCRIPT

log "Deployment finished"
echo "Open: $PUBLIC_URL/"
