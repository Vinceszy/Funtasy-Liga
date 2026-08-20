#!/usr/bin/env python3
"""Egyszeri diagnosztika (IDEIGLENES fajl): az FPL Draft keret-vegpontjai.

A draft.html kattinthato funkcioihoz (keret, szezon jatekosai, meccs-reszletek)
jatekos-szintu adat kell. Ez a futas kideriti, mit adnak a szoba joheto
vegpontok a GitHub futojarol. CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.request

B = "https://draft.premierleague.com/api/"
HDRS = {"Accept": "application/json",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")}


def get(p):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(B + p, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return r.status, json.loads(raw), len(raw)
    except urllib.error.HTTPError as e:
        return e.code, None, 0
    except Exception as e:
        return None, str(e), 0


def kulcsok(x, n=14):
    if isinstance(x, dict):
        return ", ".join(sorted(x.keys())[:n])
    return type(x).__name__


def main():
    print("FPL Draft keret-vegpontok diagnosztikaja")

    # --- referencia: a liga, es egy entry_id kinyerese ---
    st, j, meret = get("league/48093/details")
    print("\n1. league/48093/details: HTTP %s (%d byte)" % (st, meret))
    entry_id = None
    if st == 200:
        for e in j.get("league_entries") or []:
            if e.get("id") == 268988:              # HolVanSalah?!
                entry_id = e.get("entry_id")
        print("   teszt-entry (HolVanSalah?!): entry_id=%s" % entry_id)

    # --- jatekos-torzsadat ---
    st, j, meret = get("bootstrap-static")
    print("\n2. bootstrap-static: HTTP %s (%d byte)" % (st, meret))
    if st == 200:
        print("   gyoker-kulcsok: %s" % kulcsok(j))
        el = (j.get("elements") or [])
        print("   elements: %d jatekos" % len(el))
        if el:
            print("   egy jatekos mezoi: %s" % ", ".join(sorted(el[0].keys())))
            m = el[0]
            print("   pelda: id=%s web_name=%s team=%s element_type=%s"
                  % (m.get("id"), m.get("web_name"), m.get("team"), m.get("element_type")))
        print("   teams[0]: %s" % json.dumps((j.get("teams") or [{}])[0], ensure_ascii=False)[:200])
        print("   element_types: %s" % json.dumps(
            [{k: t.get(k) for k in ("id", "singular_name_short")} for t in (j.get("element_types") or [])],
            ensure_ascii=False))
        ev = j.get("events") or {}
        print("   events kulcsok: %s" % kulcsok(ev))
        if isinstance(ev, dict):
            print("   events.current=%s next=%s" % (ev.get("current"), ev.get("next")))

    # --- heti keret egy csapatra ---
    if entry_id:
        for gw in (1,):
            st, j, meret = get("entry/%d/event/%d" % (entry_id, gw))
            print("\n3. entry/%d/event/%d: HTTP %s (%d byte)" % (entry_id, gw, st, meret))
            if st == 200:
                print("   gyoker-kulcsok: %s" % kulcsok(j))
                picks = j.get("picks") or []
                print("   picks: %d elem; elso: %s"
                      % (len(picks), json.dumps(picks[0], ensure_ascii=False) if picks else "-"))
                print("   entry_history/subs kulcsok: %s | %s"
                      % (kulcsok(j.get("entry_history") or {}), len(j.get("subs") or [])))

    # --- heti elo pontok ---
    st, j, meret = get("event/1/live")
    print("\n4. event/1/live: HTTP %s (%d byte)" % (st, meret))
    if st == 200:
        print("   gyoker-kulcsok: %s" % kulcsok(j))
        el = j.get("elements")
        if isinstance(el, dict) and el:
            k = next(iter(el))
            print("   elements: %d jatekos (szotarkent); egy elem kulcsai: %s"
                  % (len(el), kulcsok(el[k])))
            print("   pelda stats: %s" % json.dumps((el[k] or {}).get("stats"), ensure_ascii=False)[:250])
        elif isinstance(el, list):
            print("   elements: %d jatekos (listakent); elso: %s"
                  % (len(el), json.dumps(el[0], ensure_ascii=False)[:250] if el else "-"))

    # --- jatek-allapot (aktualis fordulo) ---
    st, j, meret = get("game")
    print("\n5. game: HTTP %s (%d byte)" % (st, meret))
    if st == 200:
        print("   %s" % json.dumps(j, ensure_ascii=False)[:400])

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
