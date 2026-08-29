#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py'
python3 -m py_compile "$ROOT"/scripts/*.py "$ROOT"/deploy/*.py
for f in "$ROOT"/scripts/*.sh "$ROOT"/deploy/*.sh; do bash -n "$f"; done
for f in "$ROOT/protocol.json" "$ROOT/fixtures.json" "$ROOT/manifests/target.json" "$ROOT/manifests/draft.json" "$ROOT/runtime-manifest.json" "$ROOT/preregistration.json" "$ROOT/results/summary.json" "$ROOT/evidence/quality-failures.json" "$ROOT/evidence/baseline-ladder.json" "$ROOT/evidence/promotion.json" "$ROOT/evidence/qualification.json"; do
  python3 -m json.tool "$f" >/dev/null
done
python3 "$ROOT/scripts/verify_seal.py" >/dev/null
python3 "$ROOT/scripts/verify_contract.py" >/dev/null
if git -C "$ROOT" status --short | grep -E '(^|/)(private|runs|\.state)/' >/dev/null; then
  echo 'private artifacts are visible to git' >&2
  exit 1
fi
echo REPOSITORY_CHECKS_OK
