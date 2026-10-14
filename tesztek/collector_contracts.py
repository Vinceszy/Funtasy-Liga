#!/usr/bin/env python3
"""THE NAMES THE PAGES AND THE COLLECTORS SHARE: pinned, so a rename is deliberate.

WHY: the code is moving to English, file by file. Most names can change
freely, but some are a contract between two sides that do not change in the
same commit:

  * the DATA FILES the pages load - a collector writes them, a page reads
    them, and a stale phone may hold the old page for a day;
  * the TOP-LEVEL KEYS of those files - including the archived rounds
    (keretek/<r>.json, bontasok/<r>.json) that no collector rewrites any more;
  * the browser STORAGE KEYS - a renamed key reads as empty, not as an error,
    so a visitor's saved state would vanish silently.

A rename of any of these is not a translation. It needs both sides in one
commit, a migration for the archive or the stored state, and then this list
updated on purpose. The test fails until all three happen.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PAGES = ["funtasy.js", "index.html", "nb1/index.html", "pl/index.html",
         "nemzethy/index.html", "valtozasok/index.html"]

# The data files the pages load. `<r>` stands for a round number.
DATA_FILES = {
    "arak.json": {"arak", "updated"},
    "articles.json": {"leagues", "updated"},
    "bontasok/<r>.json": {"bontasok", "round"},
    "draft.json": {"entries", "league", "schedule", "standings", "updated"},
    "draft_guardiola.json": {"rounds", "updated"},
    "draft_history.json": {"rounds", "updated", "veglegesek"},
    "draft_keretvaltozasok.json": {"rounds", "updated"},
    "draft_players.json": {"players", "teams", "updated"},
    "draft_squads.json": {"squads", "updated"},
    "guardiola.json": {"rounds", "updated"},
    "hatekonysag.json": {"rounds", "updated"},
    "jatekosok.json": {"players", "updated"},
    "keretek/<r>.json": {"round", "squads"},
    "keretvaltozasok.json": {"rounds", "updated"},
    "meccsek.json": {"rounds", "updated"},
    "results.json": {"provisional", "schedule", "updated"},
    "squad_history.json": {"rounds", "updated"},
    "squads.json": {"round", "squads", "updated"},
    "valtozasok.json": {"bejegyzesek"},
    "verzio.json": {"v"},
    "zarasok.json": {"rounds", "updated"},
    "zarasok_nb1.json": {"rounds", "updated"},
}

# Prefixes of the browser storage keys the pages write.
STORAGE_PREFIXES = {"funtasy-ert:", "funtasy-eszkoz"}

failures = []


def check(ok, text):
    print(("OK   " if ok else "FAIL ") + text)
    if not ok:
        failures.append(text)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


sources = {rel: read(rel) for rel in PAGES}
text = "\n".join(sources.values())

# 1) The set of data files the pages reference is the pinned one.
referenced = set()
for m in re.finditer(r"['`\"/](?:\.\./)?([a-z0-9_]+(?:/\$\{[a-z]+\})?[a-z0-9_]*\.json)", text):
    referenced.add(re.sub(r"\$\{[a-z]+\}", "<r>", m.group(1)))
check(referenced == set(DATA_FILES),
      "the pages load exactly the pinned data files"
      + ("" if referenced == set(DATA_FILES) else
         " - new: %s, gone: %s" % (sorted(referenced - set(DATA_FILES)),
                                   sorted(set(DATA_FILES) - referenced))))

# 2) Every data file in the repository still has the pinned top-level keys -
#    the archived rounds included, all of them.
for name, keys in sorted(DATA_FILES.items()):
    paths = (sorted(glob.glob(os.path.join(ROOT, name.replace("<r>", "*"))))
             if "<r>" in name else [os.path.join(ROOT, name)])
    paths = [p for p in paths if os.path.exists(p)]
    if not paths:
        check(False, "%s exists in the repository" % name)
        continue
    wrong = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or set(data) != keys:
            wrong.append(os.path.relpath(path, ROOT))
    check(not wrong, "%s keeps its top-level keys %s%s" % (
        name, sorted(keys), "" if not wrong else " - differs in: %s" % wrong[:5]))

# 3) The browser storage keys are the pinned ones.
used = set(re.findall(r"localStorage\.(?:get|set|remove)Item\(\s*['`\"]([^'`\"]+)", text))
check(used == STORAGE_PREFIXES,
      "the pages use exactly the pinned storage keys %s (found %s)"
      % (sorted(STORAGE_PREFIXES), sorted(used)))

print("\n" + ("All checks pass." if not failures
              else "%d checks failed." % len(failures)))
sys.exit(1 if failures else 0)
