#!/usr/bin/env python3
"""EGYSZERI meres: ad-e a jatekos-adatlap FORDULONKENTI arat, es milyen alakban?

MIERT: az oldal fordulonkenti arat mutat a profilon. A listas torzs csak a
MOSTANI arat adja, a sajat arnaplonk (arak.json) pedig a sajat inditasa ota
gyul - a szezon elso forduloira tehat nincs benne semmi. A README szerint a
jatekos-adatlap `rounds` tombje visszamenoleg is adja, de a MEZONEVEKET nem
merte meg senki, es a fordulo azonositoja (round_id = 75 + 2 x fordulo) nem
ugyanaz, mint a sor sajat `id`-je - a ketto osszekeverese csendben rossz
forduloba tenne minden arat.

Amit eldont: van-e `rounds`, mi all egy soraban, melyik mezo a fordulo, es
egyezik-e a legutolso fordulo ara azzal, amit a torzs mostani arkent ad.

Csak olvas. Halozat kell hozza, tehat Actionsbol megy.
"""
import json
import os
import sys
import urllib.request

API = "https://fantasy-api.mlsz.hu/"
FEJ = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 funtasy-armeres/1.0"}
NAPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlsz-arelozmeny.txt")


def hoz(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=FEJ), timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:                                    # noqa: BLE001
        return {"__hiba": "%s: %s" % (type(e).__name__, e)}


def main():
    sorok = []

    def ki(s=""):
        print(s)
        sorok.append(s)

    cp = os.environ.get("AR_CP")
    if not cp:
        # Barmelyik jatekos megteszi: a lista elso sora.
        lista = hoz(API + "competitions/3/players?page%5Bsize%5D=1")
        adat = (lista or {}).get("data") or []
        cp = str(adat[0].get("id")) if adat else ""
        ki("lista elso jatekosa: %s" % (cp or "NEM JOTT"))
    if not cp:
        ki("nincs mivel merni - megallunk")
        return 1

    j = hoz(API + "competitions/3/players/" + cp)
    if j.get("__hiba"):
        ki("adatlap: %s" % j["__hiba"])
        return 1
    ki("adatlap gyoker-kulcsai: %s" % sorted(j.keys()))
    r = j.get("rounds")
    ki("rounds tipusa: %s, hossza: %s" % (type(r).__name__, len(r) if isinstance(r, list) else "-"))
    if not isinstance(r, list) or not r:
        ki("NINCS fordulonkenti sor - az arelozmeny innen nem potolhato")
        return 0

    ki("egy sor kulcsai: %s" % sorted(r[0].keys()))
    ki("")
    ki("%-10s %-10s %-8s %-10s" % ("id", "round_id", "ar", "jatszott"))
    for x in r:
        ki("%-10s %-10s %-8s %-10s" % (x.get("id"), x.get("round_id"),
                                       x.get("market_price"), x.get("is_played")))
    ki("")
    # A dontes, ami miatt a meres keszult: melyik mezobol jon a fordulo szama?
    for mezo in ("round_id", "id"):
        ertekek = [x.get(mezo) for x in r if isinstance(x.get(mezo), int)]
        szamok = sorted((e - 75) / 2 for e in ertekek)
        rendben = all(float(n).is_integer() and 1 <= n <= 38 for n in szamok)
        ki("%s-bol (id-75)/2: %s -> %s" % (mezo, szamok[:8],
                                           "ERVENYES fordulo-szamok" if rendben else "nem fordulo"))
    torzs_ar = ((j.get("current_round") or {}).get("market_price"))
    ki("")
    ki("a torzs MOSTANI ara: %s | az utolso sor ara: %s"
       % (torzs_ar, r[-1].get("market_price")))
    return 0


if __name__ == "__main__":
    import io as _io
    import contextlib
    puffer = _io.StringIO()
    with contextlib.redirect_stdout(puffer):
        kod = main()
    szoveg = puffer.getvalue()
    sys.stdout.write(szoveg)
    with open(NAPLO, "w", encoding="utf-8") as f:
        f.write(szoveg)
    sys.exit(kod)
