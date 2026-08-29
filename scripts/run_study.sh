#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${MODEL_DIR:?set MODEL_DIR to the pinned target snapshot}"
DRAFT="${DRAFT_DIR:?set DRAFT_DIR to the pinned draft snapshot}"
IMAGE="${IMAGE:-sxuff/qwen38-27b-abliterated-dflash2:2026-08-29}"
RUN_ROOT="${RUN_ROOT:-$ROOT/private/primary}"
NAME="${STUDY_CONTAINER_NAME:-qwen38-27b-ara-abliterated-nvfp4-study}"
OWNER=study
RESTORE_UNIT="${RESTORE_UNIT:?set RESTORE_UNIT to the service to restore, or none}"
RESTORE_BASE_URL="${RESTORE_BASE_URL:-}"
RESTORE_API_KEY_FILE="${RESTORE_API_KEY_FILE:-}"
RESTORE_EXPECTED_MODEL="${RESTORE_EXPECTED_MODEL:-}"
RESTORE_CANARY_PROMPT="${RESTORE_CANARY_PROMPT:-}"
RESTORE_CANARY_EXPECTED="${RESTORE_CANARY_EXPECTED:-}"
mkdir -p "$RUN_ROOT" "$ROOT/results"
if [[ "$RESTORE_UNIT" != none ]]; then
  [[ -n "$RESTORE_BASE_URL" && -n "$RESTORE_EXPECTED_MODEL" ]] || {
    echo 'RESTORE_BASE_URL and RESTORE_EXPECTED_MODEL are required when RESTORE_UNIT is not none' >&2
    exit 2
  }
  [[ -z "$RESTORE_API_KEY_FILE" || -r "$RESTORE_API_KEY_FILE" ]] || {
    echo "restore API key file is unreadable: $RESTORE_API_KEY_FILE" >&2
    exit 2
  }
  [[ -n "$RESTORE_CANARY_PROMPT" && -n "$RESTORE_CANARY_EXPECTED" ]] || {
    echo 'RESTORE_CANARY_PROMPT and RESTORE_CANARY_EXPECTED are required for rollback verification' >&2
    exit 2
  }
fi
baseline_swap=$(awk '/SwapTotal:/{t=$2}/SwapFree:/{f=$2}END{print (t-f)*1024}' /proc/meminfo)
restore_was_active=0
if [[ "$RESTORE_UNIT" != none ]] && systemctl --user is-active --quiet "$RESTORE_UNIT"; then
  restore_was_active=1
fi
restore(){
  NAME="$NAME" OWNER="$OWNER" "$ROOT/scripts/stop.sh" >/dev/null 2>&1 || true
  if [[ "$restore_was_active" -eq 1 ]]; then
    systemctl --user start "$RESTORE_UNIT"
    args=(--base-url "$RESTORE_BASE_URL" --expected-model "$RESTORE_EXPECTED_MODEL" --timeout-seconds 720 --canary-prompt "$RESTORE_CANARY_PROMPT" --canary-expected "$RESTORE_CANARY_EXPECTED")
    [[ -z "$RESTORE_API_KEY_FILE" ]] || args+=(--api-key-file "$RESTORE_API_KEY_FILE")
    python3 "$ROOT/scripts/wait_endpoint.py" "${args[@]}" > "$RUN_ROOT/restore-receipt.json"
    systemctl --user is-active --quiet "$RESTORE_UNIT"
  fi
}
on_exit(){
  rc=$?
  trap - EXIT
  if ! restore; then
    echo 'rollback verification failed' >&2
    exit 97
  fi
  exit "$rc"
}
trap on_exit EXIT
if [[ "$restore_was_active" -eq 1 ]]; then
  systemctl --user stop "$RESTORE_UNIT"
fi
python3 "$ROOT/scripts/verify_contract.py"
run_arm(){
  arm=$1
  rm -f "$RUN_ROOT/$arm-stop" "$RUN_ROOT/$arm-incident.json" "$RUN_ROOT/$arm-telemetry.jsonl"
  MODE="$arm" MODEL_DIR="$TARGET" DRAFT_DIR="$DRAFT" IMAGE="$IMAGE" NAME="$NAME" OWNER="$OWNER" STATE_DIR="$RUN_ROOT/$arm-state" "$ROOT/scripts/serve.sh"
  deadline=$((SECONDS+1200))
  while ((SECONDS<deadline)); do
    curl -fsS --max-time 3 http://127.0.0.1:8001/v1/models >/dev/null 2>&1 && break
    docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null | grep -qx true || { docker logs "$NAME" > "$RUN_ROOT/$arm-server.log" 2>&1 || true; return 1; }
    sleep 5
  done
  curl -fsS http://127.0.0.1:8001/v1/models | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["data"][0]["id"]=="qwen38-27b-ara-abliterated-nvfp4-mtp",d'
  python3 "$ROOT/scripts/watchdog.py" --output "$RUN_ROOT/$arm-telemetry.jsonl" --stop "$RUN_ROOT/$arm-stop" --incident "$RUN_ROOT/$arm-incident.json" --container "$NAME" --baseline-swap "$baseline_swap" & watchdog=$!
  set +e
  python3 "$ROOT/scripts/benchmark.py" --arm "$arm" --protocol "$ROOT/protocol.json" --fixtures "$ROOT/fixtures.json" --output "$RUN_ROOT/$arm.json"
  bench_rc=$?
  set -e
  touch "$RUN_ROOT/$arm-stop"
  wait "$watchdog" || watch_rc=$?
  watch_rc=${watch_rc:-0}
  curl -fsS http://127.0.0.1:8001/metrics > "$RUN_ROOT/$arm-metrics.txt" || true
  docker logs "$NAME" > "$RUN_ROOT/$arm-server.log" 2>&1 || true
  docker inspect "$NAME" > "$RUN_ROOT/$arm-container.json"
  NAME="$NAME" OWNER="$OWNER" "$ROOT/scripts/stop.sh"
  [[ $bench_rc -eq 0 && $watch_rc -eq 0 && ! -e "$RUN_ROOT/$arm-incident.json" ]]
}
run_arm no-spec
run_arm dflash2
set +e
python3 "$ROOT/scripts/analyze.py" --root "$RUN_ROOT" --output "$ROOT/results/summary.json" --report "$ROOT/REPORT.md"
analyze_rc=$?
set -e
restore
trap - EXIT
if [[ $analyze_rc -eq 0 ]]; then
  touch "$RUN_ROOT/STUDY_COMPLETE"
else
  touch "$RUN_ROOT/STUDY_FINISHED_NO_GO"
fi
exit "$analyze_rc"
