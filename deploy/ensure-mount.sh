#!/usr/bin/env bash
# One-time (idempotent): mount /srv/grecs into the caddy container on web01.
# Mirrors how /srv/library, /srv/prosite, /srv/turtle are mounted.
# Backs up the compose file, edits the grecs volume line in, brings the
# caddy service up, verifies the mount, restores on failure.
set -euo pipefail
SSH_KEY="${SSH_KEY:-$HOME/.ssh/agent-ed25519}"
WEB01="${WEB01_USER:-root}@${WEB01_HOST:-91.99.62.203}"
ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=12 "$WEB01" bash -s <<'REMOTE'
set -euo pipefail
cd /srv/web
compose=$(ls docker-compose.yml docker-compose.yaml compose.yml compose.yaml 2>/dev/null | head -1 || true)
[ -n "$compose" ] || { echo "no compose file in /srv/web"; exit 1; }
echo "compose file: $compose"
if docker inspect web-caddy-1 --format '{{range .Mounts}}{{.Source}}{{"\n"}}{{end}}' | grep -qx /srv/grecs; then
  echo "mount already active"; exit 0
fi
ts=$(date -u +%Y%m%d%H%M%S)
bak="$compose.grecs.bak.$ts"
cp -a "$compose" "$bak"
python3 - "$compose" <<'PY'
import sys, re
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text()
if "/srv/grecs" in text:
    print("compose already references grecs")
    raise SystemExit(0)
# insert the volume line next to an existing static mount
m = re.search(r"^(\s*)- /srv/turtle:/srv/turtle(:ro)?$", text, re.M)
if not m:
    m = re.search(r"^(\s*)- /srv/library:/srv/library(:ro)?$", text, re.M)
assert m, "no known static mount line to anchor against"
indent = m.group(1)
text = text[:m.end()] + f"\n{indent}- /srv/grecs:/srv/grecs:ro" + text[m.end():]
p.write_text(text)
print("added /srv/grecs mount line")
PY
if ! docker compose -f "$compose" config >/dev/null 2>&1; then
  cp -a "$bak" "$compose"; echo "compose config invalid; restored $bak"; exit 1
fi
docker compose -f "$compose" up -d caddy
sleep 3
docker inspect web-caddy-1 --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' | grep grecs \
  || { cp -a "$bak" "$compose"; echo "mount missing after up; restored $bak (container keeps running with old config)"; exit 1; }
docker exec web-caddy-1 sh -c 'ls /srv/grecs/current | head -3'
echo "MOUNT OK"
REMOTE
