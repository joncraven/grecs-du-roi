#!/usr/bin/env bash
# Read-only diagnostics for the grecs vhost on web01 (t_1bdfa688).
set -euo pipefail
SSH_KEY="${SSH_KEY:-$HOME/.ssh/agent-ed25519}"
WEB01="${WEB01_USER:-root}@${WEB01_HOST:-91.99.62.203}"
ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=12 "$WEB01" bash -s <<'REMOTE'
set -euo pipefail
echo "== local curl (Host: grecs) =="
curl -s -o /tmp/grecs.out -w 'code=%{http_code} size=%{size_download}\n' \
  -H 'Host: grecs.craven.fr' http://127.0.0.1/estienne-john1.html || true
head -c 120 /tmp/grecs.out; echo
echo "== caddy version =="
docker exec web-caddy-1 caddy version 2>/dev/null || docker ps --format '{{.Names}}' | head
echo "== grecs block as live Caddy sees it =="
awk '/grecs-du-roi reader/,/end grecs-du-roi/' /srv/web/Caddyfile
echo "== caddy adapted route (grep grecs) =="
docker exec web-caddy-1 sh -c 'caddy adapt --config /etc/caddy/Caddyfile 2>/dev/null | python3 -m json.tool | grep -n -A6 grecs.craven | head -40' || true
echo "== recent caddy logs =="
docker logs web-caddy-1 --tail 15 2>&1 | grep -i grecs | tail -8 || echo "(no grecs log lines)"
REMOTE
