#!/usr/bin/env bash
# One-command publish of the Grecs du Roi reader + specimen (grecs.craven.fr)
# to web01. Same static pipeline family as library-site (latin.craven.fr):
# publish ONLY from main → rsync src/ to /srv/grecs/<sha>/ → atomic
# current symlink flip → insert marked Caddy block → validate + reload →
# smoke. Never copies a repo Caddyfile over live /srv/web/Caddyfile; edits
# only the marked grecs block (backup first, restore on validate failure).
#
#   ./deploy/deploy.sh              # ship + smoke
#   DRY_RUN=1 ./deploy/deploy.sh    # local staging only, no network
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"   # grecs-du-roi/
WEB01_HOST="${WEB01_HOST:-91.99.62.203}"
WEB01_USER="${WEB01_USER:-root}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/agent-ed25519}"
SITE_HOST="${SITE_HOST:-greek.craven.fr}"
REMOTE_ROOT="${REMOTE_ROOT:-/srv/grecs}"

[ -f "$SSH_KEY" ] || { echo "missing ssh key $SSH_KEY"; exit 1; }

# Ship rule (project memory, same as latin.craven.fr): from main only.
branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)"
[ "$branch" = "main" ] || { echo "refusing to deploy from branch '$branch' (main only)"; exit 1; }
git -C "$ROOT" diff --quiet || { echo "uncommitted changes; commit first"; exit 1; }
SHA="$(git -C "$ROOT" rev-parse --short HEAD)"

STAGE="$(mktemp -d /tmp/grecs-stage.XXXX)"
trap 'rm -rf "$STAGE"' EXIT

echo "[1/5] stage static tree from src/ + bounded qa-evidence"
rsync -a --exclude '.DS_Store' "$ROOT/src/" "$STAGE/"
mkdir -p "$STAGE/qa-evidence"
for f in estienne-scan.jpg estienne-chromium-full.png estienne-compare-harness.png \
         reader-mode-roi.png reader-mode-modern.png; do
  [ -f "$ROOT/qa-evidence/$f" ] && cp "$ROOT/qa-evidence/$f" "$STAGE/qa-evidence/$f"
done

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "[dry-run] staged tree:"; find "$STAGE" -type f | wc -l; exit 0
fi

SSH=(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=12 "$WEB01_USER@$WEB01_HOST")
RSYNC_SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new -o BatchMode=yes"

echo "[2/5] rsync → web01:$REMOTE_ROOT/$SHA/"
"${SSH[@]}" "mkdir -p $REMOTE_ROOT/$SHA"
rsync -az --delete -e "$RSYNC_SSH" "$STAGE/" "$WEB01_USER@$WEB01_HOST:$REMOTE_ROOT/$SHA/"

echo "[3/5] atomic current symlink flip → $SHA"
"${SSH[@]}" "ln -sfn $REMOTE_ROOT/$SHA $REMOTE_ROOT/current.tmp && mv -Tf $REMOTE_ROOT/current.tmp $REMOTE_ROOT/current"

echo "[4/5] insert marked Caddy block for $SITE_HOST"
scp -i "$SSH_KEY" -o BatchMode=yes \
  "$ROOT/deploy/Caddyfile.http.snippet" \
  "$WEB01_USER@$WEB01_HOST:/tmp/grecs.caddy.http.snippet"
"${SSH[@]}" "bash -s" <<'REMOTE'
set -euo pipefail
ts=$(date -u +%Y%m%d%H%M%S)
bak="/srv/web/Caddyfile.grecs.bak.$ts"
cp -a /srv/web/Caddyfile "$bak"
python3 - <<'PY'
from pathlib import Path
p = Path("/srv/web/Caddyfile")
text = p.read_text()
snip = Path("/tmp/grecs.caddy.http.snippet").read_text()
start = "# --- grecs-du-roi reader"  # prefix match: old grecs.* and new greek.* blocks
end = "# --- end grecs-du-roi reader ---"
if start in text and end in text:
    block = text[text.index(start):text.index(end) + len(end)]
    if "\n\troot * /srv/grecs/current" in block or "root * /srv/grecs/current" in block.split("\n", 1)[-1]:
        # block already serves /srv/grecs/current (e.g. the TLS variant from
        # enable-tls.sh) — content is live via the symlink flip; do NOT
        # downgrade TLS to the http:// snippet (KO 2026-11-12: it did).
        print("existing grecs block serves /srv/grecs/current; leaving Caddyfile untouched")
    else:
        pre = text[:text.index(start)]
        post = text[text.index(end) + len(end):]
        p.write_text(pre.rstrip() + "\n" + snip + post)
        print("replaced marked grecs block")
elif "grecs.craven.fr" in text or "greek.craven.fr" in text:
    print("unmarked grecs reference exists; refusing to edit")
    raise SystemExit(1)
else:
    p.write_text(text.rstrip() + "\n" + snip)
    print("appended grecs block")
PY
cd /srv/web
if ! docker compose run --rm -T caddy caddy validate --config /etc/caddy/Caddyfile </dev/null; then
  cp -a "$bak" /srv/web/Caddyfile
  echo "caddy validate failed; restored $bak"
  exit 1
fi
docker compose restart caddy
REMOTE

echo "[5/5] smoke"
ok=1
for path in / /index.html /estienne-john1.html /fonts/grecs-roi-greek-cursive.woff2 \
            /fonts/cardo-polytonic.woff2 /fonts/LICENSES.json \
            /qa-evidence/estienne-scan.jpg; do
  read -r code size < <(curl -s -o /dev/null -w '%{http_code} %{size_download}' \
    --resolve "$SITE_HOST:80:$WEB01_HOST" "http://$SITE_HOST$path" || echo "000 0")
  echo "  http://$SITE_HOST$path → $code ($size B)"
  # content-type check: a 200 that serves 0 bytes is a misconfigured vhost
  { [ "$code" = "200" ] && [ "$size" -gt 0 ]; } || ok=0
done
[ "$ok" = "1" ] && echo "DEPLOY OK ($SHA)" || { echo "SMOKE FAILED"; exit 1; }
