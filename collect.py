#!/usr/bin/env python3
"""FunTasy Liga - adatgyujto valodi bongeszovel (Playwright).

Miert kell bongeszo? Az MLSZ a keret-vegpontot adatkozponti IP-krol 403-mal tiltja.
A Playwright valodi Chrome-ot indit, betolti a fantasy.mlsz.hu-t, es onnan
azonos eredetbol (same-origin) keri le az adatokat - igy nincs CORS es nincs tiltas.

Kimenet:
  results.json       - a lejatszott fordulok H2H eredmenyei (archivum)
  squads.json        - az aktualis keretek (az oldal ebbol tolt gyorsan)
  squad_history.json - fordulonkenti keret-pillanatkepek (szezon-osszesitohoz)
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

COMPETITION = 3
MEMBERS = {
    "Katyul": "peterkmrs", "Bence": "Dill Dough", "Sámsi": "samsonp",
    "Vince": "HolVanSalah", "Bazsa": "Hoxha98", "Csongi": "szcsngr",
    "Csendi": "cspeti93", "Ádám": "siuu_1885",
}

JS_FETCH = """
async (url) => {
  const r = await fetch(url, {headers: {'Accept': 'application/json'}});
  if (!r.ok) return {__error: r.status};
  return await r.json();
}
"""


def load(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def deep_name(o, depth=0):
    if not isinstance(o, dict) or depth > 6:
        return None
    f, l = o.get("first_name"), o.get("last_name")
    if f or l:
        return " ".join(x for x in (f, l) if x)
    for k in ("name", "short_name", "display_name"):
        v = o.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for v in o.values():
        if isinstance(v, dict):
            r = deep_name(v, depth + 1)
            if r:
                return r
    return None


def main():
    results = load("results.json", {"updated": None, "schedule": {}})
    history = load("squad_history.json", {"updated": None, "rounds": {}})
    schedule = results["schedule"]

    points, squads = {}, {}
    current_round = None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(
            locale="hu-HU",
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"),
            viewport={"width": 1366, "height": 900},
        )
        page = ctx.new_page()
        page.goto("https://fantasy.mlsz.hu/", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(4000)          # hagyjuk lefutni az esetleges vedelmi ellenorzest

        def api(path):
            url = "https://fantasy-api.mlsz.hu/competitions/%d/%s" % (COMPETITION, path)
            for attempt in range(3):
                try:
                    j = page.evaluate(JS_FETCH, url)
                    if isinstance(j, dict) and "__error" in j:
                        print("  ! HTTP %s <- %s" % (j["__error"], path[:70]), file=sys.stderr)
                    else:
                        return j
                except Exception as e:
                    print("  ! %s <- %s" % (e, path[:70]), file=sys.stderr)
                page.wait_for_timeout(2500)
            return None

        for name, uname in MEMBERS.items():
            from urllib.parse import quote
            j = api("rankings?include=user_team.user.id,summary_statistics,ranking,rounds,"
                    "competition_rank&page=1&per_page=5&filter[search]=" + quote(uname))
            rows = (j or {}).get("data") or []
            row = next((d for d in rows
                        if ((d.get("user_team") or {}).get("user") or {}).get("username") == uname),
                       rows[0] if rows else None)
            if not row:
                print("  ! nincs talalat: %s" % uname, file=sys.stderr)
                continue
            ut = row.get("user_team") or {}
            rs = ut.get("round_statistics") or []
            points[name] = {int(s["round_number"]): s["points"] for s in rs}
            if rs:
                current_round = max(current_round or 0, max(int(s["round_number"]) for s in rs))

            uid = (ut.get("user") or {}).get("id")
            if uid:
                k = api("user-team-players-history?include=competition_player.player,"
                        "competition_player.team&filter[user_id]=%d" % uid)
                data = (k or {}).get("data")
                if isinstance(data, list) and data:
                    squads[name] = [{
                        "name": deep_name(d.get("competition_player") or {}) or
                                ("#%s" % (d.get("competition_player_id") or d.get("id"))),
                        "team": ((d.get("competition_player") or {}).get("team") or {}).get("short_name")
                                or ((d.get("competition_player") or {}).get("team") or {}).get("name") or "",
                        "cap": bool(d.get("is_captain")),
                        "sub": d.get("type") == "substitutes",
                        "week": (d.get("summary_statistics") or {}).get("weekly_points", 0),
                        "total": (d.get("summary_statistics") or {}).get("competition_points", 0),
                    } for d in data]
            print("  %s: fordulok=%s, keret=%d fo" % (name, sorted(points.get(name, {})),
                                                     len(squads.get(name, []))))
        browser.close()

    # --- H2H eredmenyek archivalasa (0-0 = meg nem lezart) ---
    filled = 0
    for rnd, matches in schedule.items():
        r = int(rnd)
        for m in matches:
            if m[2] is not None:
                continue
            hp, vp = points.get(m[0], {}).get(r), points.get(m[1], {}).get(r)
            if hp is None or vp is None or (not hp and not vp):
                continue
            m[2], m[3] = hp, vp
            filled += 1
            print("  + %d. fordulo: %s %s - %s %s" % (r, m[0], hp, vp, m[1]))

    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if filled:
        results["updated"] = stamp
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=0)

    if squads:
        with open("squads.json", "w", encoding="utf-8") as f:
            json.dump({"updated": stamp, "squads": squads}, f, ensure_ascii=False, indent=0)
        if current_round:
            history["rounds"][str(current_round)] = squads      # a legfrissebb allapot felulirja
            history["updated"] = stamp
            with open("squad_history.json", "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=0)
            print("  keret-pillanatkep mentve: %d. fordulo" % current_round)

    print("Kesz: %d uj eredmeny, %d keret." % (filled, len(squads)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
