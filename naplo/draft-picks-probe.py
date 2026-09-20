#!/usr/bin/env python3
"""What does the Draft league remember about the draft itself?

A draft league has a fact the salary-cap side cannot have: every player was
CHOSEN, by somebody, at a known moment. "A first-round pick sitting on the
bench" and "the man nobody wanted until the fourteenth round" are the kind
of sentence a summary is worth reading for - but only if the data is really
there and really joins to the squads we already store.

Probed here:
  draft/<league>/choices       who picked whom, in which round, at which pick
  draft/<league>/transactions  the waiver and free-agent moves behind them
  draft/<league>/trades        offers between managers

For each: the status, the keys, and - the part that decides whether it is
usable - whether the ids JOIN to the element and entry ids we already have.
An endpoint that answers 200 with ids we cannot match is worth nothing.

Reads only; writes the log file. No article or personal text is stored: the
Draft API returns real names, so the probe reports SHAPES and counts, and
the few sample rows it prints carry ids, not names.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

B = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json", "Accept-Language": "en-GB,en;q=0.9",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")}
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "draft-picks.txt")
LEAGUE = os.environ.get("LEAGUE_ID") or "48093"


def keres(path):
    t = time.time()
    try:
        req = urllib.request.Request(B + path, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), int((time.time() - t) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300], int((time.time() - t) * 1000)
    except Exception as e:                                   # noqa: BLE001
        return 0, ("%s: %s" % (type(e).__name__, e)).encode(), int((time.time() - t) * 1000)


def sajat():
    """A mar tarolt azonositok: ezekhez kell illeszkednie a valasznak."""
    gyoker = os.path.dirname(HERE)
    be = lambda n: json.load(open(os.path.join(gyoker, n), encoding="utf-8"))
    d = be("draft.json")
    hist = be("draft_history.json")
    entryk = {str(e["id"]) for e in d.get("entries", [])}
    elemek = set()
    for sq in hist.get("rounds", {}).values():
        for lista in sq.values():
            for x in lista:
                elemek.add(str(x["e"]))
    return entryk, elemek


def main():
    entryk, elemek = sajat()
    ki = ["", "=" * 70,
          "PROBE: %s UTC | draft choices / transactions (liga %s)"
          % (time.strftime("%Y-%m-%d %H:%M"), LEAGUE),
          "  sajat azonositoink: %d csapat, %d jatekos" % (len(entryk), len(elemek))]

    for nev, path in (("choices", "draft/%s/choices" % LEAGUE),
                      ("transactions", "draft/%s/transactions" % LEAGUE),
                      ("trades", "draft/%s/trades" % LEAGUE),
                      ("league details (mar hasznaljuk)", "league/%s/details" % LEAGUE)):
        code, torzs, ms = keres(path)
        ki.append("")
        ki.append("--- %s ---" % nev)
        ki.append("  %s: HTTP %s, %d kb, %d ms" % (path, code, len(torzs) // 1024, ms))
        if code != 200:
            ki.append("  valasz: %s" % torzs[:160].decode("utf-8", "replace"))
            continue
        try:
            j = json.loads(torzs)
        except Exception:                                    # noqa: BLE001
            ki.append("  nem json")
            continue
        if isinstance(j, dict):
            ki.append("  felso kulcsok: %s" % ", ".join(sorted(j.keys())))
            lista = None
            for k in ("choices", "transactions", "trades"):
                if isinstance(j.get(k), list):
                    lista = j[k]
                    ki.append("  '%s' lista: %d elem" % (k, len(lista)))
                    break
        else:
            lista = j if isinstance(j, list) else None
            ki.append("  lista: %d elem" % (len(lista) if lista else 0))
        if not lista:
            continue
        ki.append("  elem-kulcsok: %s" % ", ".join(sorted(lista[0].keys())))
        # A LENYEG: illeszkednek-e az azonositok ahhoz, amink mar van?
        for mezo, halmaz, cimke in (("element", elemek, "jatekos"),
                                    ("entry", entryk, "csapat")):
            ertekek = [str(x.get(mezo)) for x in lista if x.get(mezo) is not None]
            if not ertekek:
                ki.append("  %-8s mezo: nincs a valaszban" % mezo)
                continue
            talalt = sum(1 for v in ertekek if v in halmaz)
            ki.append("  %-8s mezo: %d ertek, ebbol a sajat %s-azonositoinkkal egyezik: %d"
                      % (mezo, len(ertekek), cimke, talalt))
        # mintasorok: CSAK azonositok es szamok, nev nelkul
        biztos = ("element", "entry", "round", "pick", "index", "event", "kind",
                  "result", "added", "removed", "entry_in", "entry_out",
                  "element_in", "element_out", "offered_entry", "received_entry")
        print("\n  == %s mintasorok (nev nelkul) ==" % nev)
        for x in lista[:5]:
            print("     | %s" % json.dumps({k: x.get(k) for k in biztos if k in x},
                                           ensure_ascii=False))
        print("     (osszes mezo: %s)" % ", ".join(sorted(lista[0].keys())))

    szoveg = "\n".join(ki) + "\n"
    print(szoveg)
    fej = ("A Draft-liga sajat draftjarol es tranzakcioirol szolo meres.\n"
           "A fajlt a naplo/draft-picks-probe.py irja. Nevet NEM tarol:\n"
           "csak alakot, darabszamot es azonosito-illeszkedest.\n")
    regi = open(LOG, encoding="utf-8").read() if os.path.exists(LOG) else fej
    open(LOG, "w", encoding="utf-8").write(regi.rstrip("\n") + "\n" + szoveg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
