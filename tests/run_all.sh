#!/usr/bin/env bash
# Every test with one command:  tests/run_all.sh
#
# The browser tests run IN PARALLEL (default: 3 workers), because they are
# independent of each other - each launches its own browser with its own
# mocks. This brings the full suite down from ~10 minutes to about 4. The
# exception is the two TIMING-SENSITIVE tests (frissjelzo, visszateres): under
# parallel load they could fail falsely, so they run at the end, alone.
#
# Parallel runs depend on rewriteJson reading from disk (tests/common.js):
# while it went through the local test server, a connection dropped under
# load lost the tests' preconditions.
#
# Environment variables:
#   PORT               port of the local server (default: 8910)
#   WORKERS            number of browser workers (default: 3; 1 = serial mode)
#   PLAYWRIGHT_MODULE  path of the playwright module
#   CHROME_PATH        path of the Chromium binary
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8910}"
WORKERS="${WORKERS:-3}"
export TEST_BASE="http://127.0.0.1:${PORT}/"

echo "== Funtasy tests =="
echo "   root: $ROOT"
echo "   server: $TEST_BASE | workers: $WORKERS"

python3 -m http.server "$PORT" --directory "$ROOT" >/dev/null 2>&1 &
SERVER=$!
OUTDIR="$(mktemp -d)"
trap 'kill $SERVER 2>/dev/null; rm -rf "$OUTDIR"' EXIT
for _ in $(seq 1 40); do
  curl -sf -o /dev/null "$TEST_BASE" && break
  sleep 0.25
done

FAILED=0
run() {                         # run <label> <command...>
  local label="$1"; shift
  printf '\n\033[1m### %s\033[0m\n' "$label"
  if "$@"; then printf '   \033[32mpassed\033[0m\n'
  else FAILED=$((FAILED + 1)); printf '   \033[31mFAILED\033[0m\n'; fi
}
report() {                      # the result of a test that ran in the background
  local label="$1"
  printf '\n\033[1m### %s\033[0m\n' "$label"
  cat "$OUTDIR/$label.out"
  if [ "$(cat "$OUTDIR/$label.exit" 2>/dev/null)" = "0" ]; then
    printf '   \033[32mpassed\033[0m\n'
  else FAILED=$((FAILED + 1)); printf '   \033[31mFAILED\033[0m\n'; fi
}

# ---- 1) fast Python tests, one after the other ----
run "doc_checks.py" python3 "$ROOT/tests/doc_checks.py"
run "data_consistency.py" python3 "$ROOT/tests/data_consistency.py"
for t in "$ROOT"/tests/collector_*.py; do
  [ -e "$t" ] || continue
  run "$(basename "$t")" python3 "$t"
done

# ---- 2) browser tests: in parallel, EXCEPT the timing-sensitive ones ----
TIMING_SENSITIVE=" frissjelzo.teszt.js visszateres.teszt.js "
PARALLEL=()
SERIAL=()
for t in "$ROOT"/tests/*.teszt.js "$ROOT"/tests/*.test.js; do
  [ -e "$t" ] || continue
  case "$TIMING_SENSITIVE" in
    *" $(basename "$t") "*) SERIAL+=("$t");;
    *) PARALLEL+=("$t");;
  esac
done

if [ "${#PARALLEL[@]}" -gt 0 ]; then
  printf '%s\n' "${PARALLEL[@]}" | OUTDIR="$OUTDIR" xargs -P "$WORKERS" -n 1 sh -c '
    b="$(basename "$1")"
    node "$1" > "$OUTDIR/$b.out" 2>&1
    echo $? > "$OUTDIR/$b.exit"' _
  for t in "${PARALLEL[@]}"; do report "$(basename "$t")"; done
fi

# ---- 3) the timing-sensitive tests at the end, alone ----
for t in "${SERIAL[@]}"; do
  run "$(basename "$t")" node "$t"
done

printf '\n=====================================\n'
if [ "$FAILED" -eq 0 ]; then printf '\033[32mAll tests passed.\033[0m\n'
else printf '\033[31m%d tests failed.\033[0m\n' "$FAILED"; fi
exit "$FAILED"
