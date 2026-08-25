#!/usr/bin/env bash
# Az osszes teszt egy paranccsal:  tesztek/futtat.sh
#
# A bongeszos tesztek PARHUZAMOSAN futnak (alap: 3 munkas), mert egymastol
# fuggetlenek - mind sajat bongeszot indit, sajat mockokkal. Ettol a teljes
# sor ~10 percrol ~4 perc kore esik. Kivetel a ket IDOZITEST MERO teszt
# (frissjelzo, visszateres): azok parhuzamos terheles alatt hamisan
# bukhatnanak, ezert a vegen, egyedul futnak.
#
# A parhuzamossag elofeltetele volt, hogy a jsonAtir lemezrol olvasson
# (tesztek/kozos.js): amig a helyi tesztszerveren at ment, a terheles alatt
# eldobott kapcsolat a tesztek elofelteteleit vesztette el.
#
# Kornyezeti valtozok:
#   PORT              a helyi kiszolgalo portja (alap: 8910)
#   PARHUZAM          bongeszos munkasok szama (alap: 3; 1 = regi soros mod)
#   PLAYWRIGHT_MODUL  a playwright modul utja
#   CHROME_UT         a Chromium binaris utja
set -u
GYOKER="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PORT:-8910}"
PARHUZAM="${PARHUZAM:-3}"
export TESZT_BASE="http://127.0.0.1:${PORT}/"

echo "== Funtasy tesztek =="
echo "   gyoker: $GYOKER"
echo "   kiszolgalo: $TESZT_BASE | parhuzam: $PARHUZAM"

python3 -m http.server "$PORT" --directory "$GYOKER" >/dev/null 2>&1 &
SZERVER=$!
KIMENET="$(mktemp -d)"
trap 'kill $SZERVER 2>/dev/null; rm -rf "$KIMENET"' EXIT
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
mutat() {                       # egy hatterben futott teszt eredmenye
  local cimke="$1"
  printf '\n\033[1m### %s\033[0m\n' "$cimke"
  cat "$KIMENET/$cimke.out"
  if [ "$(cat "$KIMENET/$cimke.exit" 2>/dev/null)" = "0" ]; then
    printf '   \033[32mrendben\033[0m\n'
  else BUKOTT=$((BUKOTT + 1)); printf '   \033[31mBUKOTT\033[0m\n'; fi
}

# ---- 1) gyors python-tesztek, sorban ----
futtat "dokuk.py" python3 "$GYOKER/tesztek/dokuk.py"
for t in "$GYOKER"/tesztek/gyujto_*.py; do
  [ -e "$t" ] || continue
  futtat "$(basename "$t")" python3 "$t"
done

# ---- 2) bongeszos tesztek: parhuzamosan, KIVEVE az idozitest merok ----
IDOERZEKENY=" frissjelzo.teszt.js visszateres.teszt.js "
PARHUZAMOSAK=()
SOROSAK=()
for t in "$GYOKER"/tesztek/*.teszt.js; do
  [ -e "$t" ] || continue
  case "$IDOERZEKENY" in
    *" $(basename "$t") "*) SOROSAK+=("$t");;
    *) PARHUZAMOSAK+=("$t");;
  esac
done

if [ "${#PARHUZAMOSAK[@]}" -gt 0 ]; then
  printf '%s\n' "${PARHUZAMOSAK[@]}" | KIMENET="$KIMENET" xargs -P "$PARHUZAM" -n 1 sh -c '
    b="$(basename "$1")"
    node "$1" > "$KIMENET/$b.out" 2>&1
    echo $? > "$KIMENET/$b.exit"' _
  for t in "${PARHUZAMOSAK[@]}"; do mutat "$(basename "$t")"; done
fi

# ---- 3) idozitest merok a vegen, egyedul ----
for t in "${SOROSAK[@]}"; do
  futtat "$(basename "$t")" node "$t"
done

printf '\n=====================================\n'
if [ "$BUKOTT" -eq 0 ]; then printf '\033[32mMinden teszt rendben.\033[0m\n'
else printf '\033[31m%d teszt bukott.\033[0m\n' "$BUKOTT"; fi
exit "$BUKOTT"
