#!/usr/bin/env python3
"""The player roster and the price log (collect.py) - 12 assertions.

WHY: the roster is the source of the home page list and search, and the
price log is the ONLY way to follow price changes - it was measured that MLSZ
gives no price history anywhere (naplo/mlsz-player-list.txt, round 6: it
silently swallows every include, the separate endpoints are 404). What the
log does not write down today cannot be filled in retroactively - that is
why it deserves its own test.
"""
import importlib.util, json, os, sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
failures = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


# ---------------- 1) mapping the roster ----------------
RESPONSE = {"data": [
    {"id": 915, "first_name": "Áron", "last_name": "Alaxai", "is_u21": False,
     "position": {"monogram": "H", "name": "Hátvéd"},
     "team": {"short_name": "NYÍREGY", "name": "Nyíregyháza"},
     "current_round": {"market_price": 4.2},
     "summary_statistics": {"competition_points": 12.5}},
    # incomplete row: no monogram, no short_name, no price
    {"id": 916, "first_name": "", "last_name": "Teszt", "is_u21": True,
     "position": {"name": "Csatár"}, "team": {"name": "MTK"},
     "current_round": {}, "summary_statistics": {}},
    {"first_name": "Nincs", "last_name": "Azonosító"},          # without an id: left out
]}
requested = {}
c.api_get = lambda url, retries=3: (requested.setdefault("url", url), (200, RESPONSE))[1]
t = c.player_roster()

check(t is not None and len(t) == 2, "the row without an id is left out (%s rows)" % (len(t) if t else None))
check("per_page=500" in requested["url"], "one request, with a large page size (per_page=500)")
check(t["915"] == {"n": "Alaxai Áron", "t": "NYÍREGY", "p": "H", "u21": False,
                   "pts": 12.5, "ar": 4.2},
      "every field of the complete row lands in place, the name in HUNGARIAN order (%s)"
      % t["915"]["n"])

# the recognisable part of a long name is the surname - it must come first
check(c.player_name("Gleofilo Sabrino Rudewald Hasselbaink", "Vlijter")
      == "Vlijter Gleofilo Sabrino Rudewald Hasselbaink",
      "with a long name too the surname comes first (that is what is on the shirt)")
check(c.player_name(None, None, "#42") == "#42", "without a name the id is the fallback")
check(t["916"]["p"] == "Csatár" and t["916"]["t"] == "MTK",
      "without a monogram/short name the full name is the fallback")
check(t["916"]["pts"] == 0 and t["916"]["ar"] is None,
      "missing points -> 0, missing price -> None (not 0: that would look like a price change)")

c.api_get = lambda url, retries=3: (500, None)
check(c.player_roster() is None, "on a failed response None comes back (the file stays unchanged)")

# ---------------- 2) the price log ----------------
# The log reads arak.json FROM THE WORKING DIRECTORY. It runs in a temporary
# directory, with its own history: this way the test does not depend on the
# repository's current data, and the module's `open` does not have to be
# shadowed either (that would not catch a read moved into the shared module
# anyway - such a trick would silently have measured something else).
import tempfile

WORKDIR = tempfile.mkdtemp()
os.chdir(WORKDIR)


def log_step(roster, today, previous=None):
    """One step of the price log with the given history (None = no file yet)."""
    if previous is None:
        if os.path.exists("arak.json"):
            os.remove("arak.json")
    else:
        with open("arak.json", "w", encoding="utf-8") as f:
            json.dump({"arak": previous}, f)
    return c.update_price_log(roster, today)


T1 = {"1": {"ar": 5.0}, "2": {"ar": 8.0}}
n, count = log_step(T1, "2026-08-25")
check(count == 2 and n == {"1": [["2026-08-25", 5.0]], "2": [["2026-08-25", 8.0]]},
      "first run: every price is recorded")

# unchanged price -> NO new row is written (we run every 3 hours, it would grow otherwise)
n2, count2 = log_step(T1, "2026-08-26", previous=n)
check(count2 == 0 and n2 == n, "no new entry is made for an unchanged price")

# change -> a new row only for the affected player, the old one STAYS
n3, count3 = log_step({"1": {"ar": 5.5}, "2": {"ar": 8.0}}, "2026-08-27", previous=n)
check(count3 == 1 and n3["1"] == [["2026-08-25", 5.0], ["2026-08-27", 5.5]]
      and n3["2"] == [["2026-08-25", 8.0]],
      "on a change a new row is added, the earlier value stays")

# a missing/zero price does NOT count as a change - otherwise an API error
# would write a false "dropped to 0" entry that cannot be told apart later
n4, count4 = log_step({"1": {"ar": None}, "2": {"ar": 0}}, "2026-08-28", previous=n)
check(count4 == 0 and n4 == n,
      "a missing or zero price is not recorded (an API error does not write a false price crash)")

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % 12)
