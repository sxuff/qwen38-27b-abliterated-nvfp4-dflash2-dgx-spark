#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY_FILE="${QWEN38_PROXY_KEY_FILE:-$HOME/.config/qwen38/proxy.key}"
[[ -s "$KEY_FILE" ]] || { echo "create a non-empty API key file first: $KEY_FILE" >&2; exit 2; }
mode=$(stat -c '%a' "$KEY_FILE")
[[ "$mode" == 600 || "$mode" == 400 ]] || { echo "API key file must be mode 600 or 400, got $mode" >&2; exit 2; }
install -Dm0755 "$ROOT/deploy/qwen38-abliterated-dflash2-service.sh" "$HOME/.local/bin/qwen38-abliterated-dflash2-service.sh"
install -Dm0755 "$ROOT/deploy/qwen38-auth-proxy-service.sh" "$HOME/.local/bin/qwen38-auth-proxy-service.sh"
install -Dm0755 "$ROOT/deploy/qwen38-auth-proxy.py" "$HOME/.local/bin/qwen38-auth-proxy.py"
install -Dm0644 "$ROOT/deploy/qwen38-abliterated-dflash2.service" "$HOME/.config/systemd/user/qwen38-abliterated-dflash2.service"
install -Dm0644 "$ROOT/deploy/qwen38-abliterated-dflash2-proxy.service" "$HOME/.config/systemd/user/qwen38-abliterated-dflash2-proxy.service"
systemctl --user daemon-reload
printf '%s\n' \
  'Installed the model and authenticated proxy user services without starting them.' \
  "API key file: $KEY_FILE" \
  'Start explicitly with:' \
  'systemctl --user enable --now qwen38-abliterated-dflash2.service qwen38-abliterated-dflash2-proxy.service'
