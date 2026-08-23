#!/usr/bin/env bash
# Az osszes teszt egy paranccsal:  tesztek/futtat.sh
# Egyetlen helyi kiszolgalot inditunk a repo gyokerere, es minden teszt azon
# a VALODI adaton fut. Kornyezeti valtozok:
#   PORT              a helyi kiszolgalo portja (alap: 8910)
#   PLAYWRIGHT_MODUL  a playwright modul utja
#   CHROME_UT         a Chromium binaris utja
set -u
GYOKER="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8910}"
export TESZT_BASE="http://127.0.0.1:${PORT}/"

echo "== Funtasy tesztek =="
echo "   gyoker: $GYOKER"
echo "   kiszolgalo: $TESZT_BASE"

python3 -m http.server "$PORT" --directory "$GYOKER" >/dev/null 2>&1 &
SZERVER=$!
trap 'kill $SZERVER 2>/dev/null' EXIT
for _ in $(seq 1 40); do
  curl -sf -o /dev/null "$TESZT_BASE" && break
  sleep 0.25
done

BUKOTT=0
futtat() {                      # futtat <cimke> <parancs...>
  local cimke="$1"; shift
  printf '\n\033[1m### %s\033[0m\n' "$cimke"
  if "$@"; then printf '   \033[32mrendben\033[0m\n'
  else BUKOTT=$((BUKOTT + 1)); printf '   \033[31mBUKOTT\033[0m\n'; fi
}

for t in "$GYOKER"/tesztek/gyujto_*.py; do
  [ -e "$t" ] || continue
  futtat "$(basename "$t")" python3 "$t"
done
for t in "$GYOKER"/tesztek/*.teszt.js; do
  [ -e "$t" ] || continue
  futtat "$(basename "$t")" node "$t"
done

printf '\n=====================================\n'
if [ "$BUKOTT" -eq 0 ]; then printf '\033[32mMinden teszt rendben.\033[0m\n'
else printf '\033[31m%d teszt bukott.\033[0m\n' "$BUKOTT"; fi
exit "$BUKOTT"
