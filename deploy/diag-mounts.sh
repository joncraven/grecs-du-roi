#!/usr/bin/env bash
# Read-only: how does web01's caddy container see static trees?
set -euo pipefail
SSH_KEY="${SSH_KEY:-$HOME/.ssh/agent-ed25519}"
WEB01="${WEB01_USER:-root}@${WEB01_HOST:-91.99.62.203}"
ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=12 "$WEB01" bash -s <<'REMOTE'
set -euo pipefail
echo "== caddy container mounts =="
docker inspect web-caddy-1 --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
echo "== library (latin) block for comparison =="
awk '/latin.craven.fr/{f=1} f&&/root|file_server/{print} /^}/{f=0}' /srv/web/Caddyfile | head
echo "== can container see grecs? =="
docker exec web-caddy-1 sh -c 'ls /srv/grecs/current/ 2>&1 | head -3' || true
docker exec web-caddy-1 sh -c 'ls / 2>/dev/null | head' || true
REMOTE
