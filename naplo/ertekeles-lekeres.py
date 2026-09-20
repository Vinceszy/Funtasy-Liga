#!/usr/bin/env python3
"""What did the readers say about the pieces?

The rating of an article goes to the Worker, one row per article and device.
This asks for the lot and prints a digest: how many came in, how they are
spread from one to four, which piece drew what, and the reasons as written.

The REASONS go to the run log only, never into the repository. They are the
readers' own words about our writing, given to us and not to an audience; the
log file keeps the counts, which is what a later run needs to compare
against.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

PROXY = os.environ.get("PROXY_URL") or "https://funtasy-liga.swick00.workers.dev"
EREDET = os.environ.get("MERES_EREDET") or "https://vinceszy.github.io"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ertekelesek.txt")


def keres(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "FunTasy-harvest (github.com/Vinceszy/Funtasy-Liga)",
        "Origin": EREDET, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode()


def main():
    sor = ["", "=" * 70,
           "LEKERES: %s UTC | cikk-ertekelesek" % time.strftime("%Y-%m-%d %H:%M")]
    c, b = keres(PROXY + "/ertekelesek")
    if c != 200:
        # 503 = a Workernek NINCS tarolo-kotese, vagyis nem "nulla ertekeles",
        # hanem "minden ertekeles elveszik". A kettot kulon kell latni.
        sor.append("  /ertekelesek: HTTP %s%s" % (
            c, "  <- NINCS TAROLO-KOTES, az ertekelesek elvesznek" if c == 503 else ""))
        print("\n".join(sor))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(sor) + "\n")
        return 1
    try:
        lista = json.loads(b.decode("utf-8", "replace"))
    except Exception:                                        # noqa: BLE001
        sor.append("  a valasz nem JSON (%d bajt)" % len(b))
        print("\n".join(sor))
        return 1

    sor.append("  ertekeles osszesen: %d" % len(lista))
    if not lista:
        sor.append("  meg nem ertekelt senki")
        print("\n".join(sor))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("\n".join(sor) + "\n")
        return 0

    eloszlas = {}
    cikkenkent = {}
    indokosak = 0
    for x in lista:
        p = x.get("pont")
        eloszlas[p] = eloszlas.get(p, 0) + 1
        k = x.get("cikk") or "?"
        cikkenkent.setdefault(k, []).append(p)
        if (x.get("indok") or "").strip():
            indokosak += 1
    sor.append("  eloszlas: " + " | ".join(
        "%s pont: %d" % (p, eloszlas[p]) for p in sorted(eloszlas, key=lambda z: (z is None, z))))
    pontok = [x["pont"] for x in lista if isinstance(x.get("pont"), (int, float))]
    if pontok:
        sor.append("  atlag: %.2f" % (sum(pontok) / len(pontok)))
    sor.append("  indokkal: %d / %d" % (indokosak, len(lista)))
    sor.append("")
    sor.append("  CIKKENKENT")
    for k in sorted(cikkenkent):
        ps = cikkenkent[k]
        sor.append("    %-44s %s (%d db)" % (k[:44], ", ".join(str(p) for p in ps), len(ps)))
    print("\n".join(sor))

    # Az INDOKOK csak a futasi naplóba - a repoba nem kerulnek be.
    print("")
    print("#" * 70)
    print("# INDOKOK - csak a futasi naploban, a repoba nem kerul be")
    print("#" * 70)
    for x in lista:
        indok = (x.get("indok") or "").strip()
        if not indok:
            continue
        print("\n### %s | %s pont | %s" % (x.get("cikk"), x.get("pont"), x.get("ido")))
        print(indok)

    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(sor) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
