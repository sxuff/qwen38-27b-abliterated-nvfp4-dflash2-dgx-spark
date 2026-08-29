#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${QWEN38_RECIPE_ROOT:-$HOME/qwen38-27b-abliterated-nvfp4-dflash2-dgx-spark}"
MODEL_DIR="${QWEN38_MODEL_DIR:-$HOME/models/Qwen3.8-27B-ARA-abliterated-NVFP4-MTP-16b43988bddf/snapshot}"
DRAFT_DIR="${QWEN38_DRAFT_DIR:-$HOME/.cache/qwen38-spec-drafts/hub/models--z-lab--Qwen3.8-27B-DFlash2/snapshots/50307d4c4cde6860d4eee73e2547cd786fe8e8a4}"
NAME=qwen38-27b-ara-abliterated-nvfp4
OWNER=systemd:qwen38-abliterated-dflash2
cleanup() {
  NAME="$NAME" OWNER="$OWNER" "$ROOT/scripts/stop.sh" >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 0' TERM INT
MODE=dflash2 \
MODEL_DIR="$MODEL_DIR" \
DRAFT_DIR="$DRAFT_DIR" \
NAME="$NAME" \
OWNER="$OWNER" \
STATE_DIR="$HOME/.local/state/qwen38-abliterated-dflash2" \
HOST=127.0.0.1 \
PORT=8002 \
MEM_FRACTION_STATIC=0.70 \
"$ROOT/scripts/serve.sh"
status="$(docker wait "$NAME")"
exit "$status"
