#!/usr/bin/env bash
# Flip grecs.craven.fr from the HTTP-only vhost to Let's Encrypt TLS.
# Gate: the OVH A record must already equal web01's IPv4, otherwise ACME
# fails and burns rate limits (latin/mahjong gotcha).
#
#   ./deploy/enable-tls.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB01_HOST="${WEB01_HOST:-91.99.62.203}"
WEB01_USER="${WEB01_USER:-root}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/agent-ed25519}"
SITE_HOST="${SITE_HOST:-grecs.craven.fr}"
SSH=(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o BatchMode=yes "$WEB01_USER@$WEB01_HOST")

ip="$(dig +short A "$SITE_HOST" | tail -1)"
[ "$ip" = "$WEB01_HOST" ] || {
  echo "DNS not ready: $SITE_HOST -> ${ip:-none} (want $WEB01_HOST)"
  echo "Add the OVH A record, wait for TTL, then re-run."
  exit 1
}

scp -i "$SSH_KEY" -o BatchMode=yes \
  "$ROOT/deploy/Caddyfile.tls.snippet" \
  "$WEB01_USER@$WEB01_HOST:/tmp/grecs.caddy.tls.snippet"

"${SSH[@]}" "bash -s" <<'REMOTE'
set -euo pipefail
ts=$(date -u +%Y%m%d%H%M%S)
bak="/srv/web/Caddyfile.grecs-tls.bak.$ts"
cp -a /srv/web/Caddyfile "$bak"
python3 - <<'PY'
from pathlib import Path
p = Path("/srv/web/Caddyfile")
text = p.read_text()
tls = Path("/tmp/grecs.caddy.tls.snippet").read_text()
start = "# --- grecs-du-roi reader grecs.craven.fr"
end = "# --- end grecs-du-roi reader ---"
if start in text and end in text:
    pre = text[:text.index(start)]
    post = text[text.index(end) + len(end):]
    p.write_text(pre.rstrip() + "\n" + tls + post)
    print("replaced grecs block with TLS variant")
else:
    print("marked grecs block not found; run deploy.sh first")
    raise SystemExit(1)
PY
cd /srv/web
if ! docker compose run --rm -T caddy caddy validate --config /etc/caddy/Caddyfile </dev/null; then
  cp -a "$bak" /srv/web/Caddyfile
  echo "caddy validate failed; restored $bak"
  exit 1
fi
docker compose restart caddy
REMOTE

echo "TLS block applied. First ACME issuance may take ~30s."
for i in $(seq 1 12); do
  sleep 5
  if curl -sfL "https://$SITE_HOST/" -o /dev/null; then
    echo "OK: https://$SITE_HOST/ serves 200"; exit 0
  fi
done
echo "https not answering after 60s — check: ssh web01 'docker logs web-caddy-1 --tail 50'"
