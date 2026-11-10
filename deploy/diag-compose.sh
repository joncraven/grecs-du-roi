#!/usr/bin/env bash
set -euo pipefail
SSH_KEY="${SSH_KEY:-$HOME/.ssh/agent-ed25519}"
ssh -i "$SSH_KEY" -o BatchMode=yes root@91.99.62.203 "grep -n -B2 -A8 'volumes:' /srv/web/docker-compose.yml | head -40"
