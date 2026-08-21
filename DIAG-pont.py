#!/usr/bin/env python3
"""Egyszeri diagnosztika, 5. kor (IDEIGLENES): honnan jon a pont-BONTAS?

A 4. kor lelete: a felulet jJ() hivasa sima GET a players/{id}-re
(include nelkul), es letezik stat-configs meg stat-leaders vegpont is.
A players/{id} valaszt a hatalmas kep-mezok miatt nem lattuk vegig.

Ez a kor a kep-mezoket kidobja es kiirja:
  A) players/1305 teljes szerkezete
  B) stat-configs (a statisztika-tipusok nevei/pontjai?)
  C) stat-leaders roviden

CSAK OLVAS es nyomtat.
"""
import json, sys, time, urllib.error, urllib.request

M_BASE = "https://fantasy-api.mlsz.hu/competitions/3/"
HDRS = {"Accept": "application/json", "User-Agent": "funtasy-archiver/1.0",
        "Referer": "https://fantasy.mlsz.hu/"}
KEP_KULCSOK = {"profile_picture", "logo", "media", "background", "src", "srcset", "icon"}


def get(url):
    time.sleep(0.2)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, str(e)


def kepek_nelkul(x):
    if isinstance(x, dict):
        return {k: kepek_nelkul(v) for k, v in x.items() if k not in KEP_KULCSOK}
    if isinstance(x, list):
        return [kepek_nelkul(v) for v in x]
    return x


def main():
    print("========== A) players/1305 (kep-mezok nelkul) ==========")
    st, j = get(M_BASE + "players/1305")
    if st == 200:
        print(json.dumps(kepek_nelkul(j), ensure_ascii=False, indent=1)[:9000])
    else:
        print("HTTP %s" % st)

    print("\n========== B) stat-configs ==========")
    st, j = get(M_BASE + "stat-configs")
    if st == 200:
        print(json.dumps(kepek_nelkul(j), ensure_ascii=False)[:6000])
    else:
        print("HTTP %s" % st)

    print("\n========== C) stat-leaders ==========")
    st, j = get(M_BASE + "stat-leaders")
    if st == 200:
        print(json.dumps(kepek_nelkul(j), ensure_ascii=False)[:1200])
    else:
        print("HTTP %s" % st)

    print("\nDiagnosztika vege - semmit nem irt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
