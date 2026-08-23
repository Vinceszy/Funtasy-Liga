#!/usr/bin/env python3
"""EGYSZERI felderites: van-e az MLSZ-nek FORDULO-SZINTU lezartsag-jelzese?

Eddig a fordulo lezarasat jatekos-szintu mezobol (is_played) kovetkeztettuk
ki - az viszont csak kozvetett jel, es meccs kozben is igazra vall. Ez a
szkript vegigprobal nehany vegpontot, es kiirja, mit talal a fordulokrol.
Semmit nem ir at; a futas utan a fajl torlendo.
"""
import json, sys, urllib.parse, urllib.request

BASE = "https://fantasy-api.mlsz.hu/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-diag/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}


def get(ut):
    url = BASE + ut
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return getattr(e, "code", None) or str(e), None


def kiir(cimke, ut):
    st, j = get(ut)
    print("\n=== %s" % cimke)
    print("    %s -> HTTP %s" % (ut[:110], st))
    if not isinstance(j, dict):
        return None
    d = j.get("data")
    if isinstance(d, list):
        print("    data: %d elem" % len(d))
        for x in d[:3]:
            if isinstance(x, dict):
                print("      kulcsok: %s" % sorted(x)[:18])
                print("      minta:   %s" % json.dumps(x, ensure_ascii=False)[:400])
    elif isinstance(d, dict):
        print("    data kulcsok: %s" % sorted(d)[:20])
        print("    minta: %s" % json.dumps(d, ensure_ascii=False)[:400])
    else:
        print("    valasz kulcsok: %s" % sorted(j)[:20])
        print("    minta: %s" % json.dumps(j, ensure_ascii=False)[:400])
    return j


# 1) van-e onallo fordulo-vegpont?
kiir("competitions/3/rounds", "competitions/3/rounds")
kiir("rounds", "rounds")

# 2) a ranglista include-jaban szereplo 'rounds' mit ad?
uname = "peterkmrs"
r = kiir("rankings (include=rounds)",
         "competitions/3/rankings?include=rounds,user_team.user.id&page=1&per_page=1"
         "&filter%5Bsearch%5D=" + urllib.parse.quote(uname))
if r:
    try:
        elso = (r.get("data") or [None])[0] or {}
        for kulcs in ("rounds", "round", "competition_rounds"):
            if kulcs in elso:
                print("\n    >>> '%s' a ranglista-elemben: %s"
                      % (kulcs, json.dumps(elso[kulcs], ensure_ascii=False)[:900]))
    except Exception as e:
        print("    (feldolgozasi hiba: %s)" % e)

# 3) az 5. fordulo (round_id = 75 + 2*5 = 85) sajat objektuma
for ut in ("competitions/3/rounds/85", "rounds/85",
           "competitions/3/rounds?filter%5Bid%5D=85"):
    kiir("fordulo-objektum probak", ut)

print("\n--- vege ---")
