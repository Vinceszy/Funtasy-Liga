#!/usr/bin/env python3
"""THE SAFETY OF THE ACCUMULATING FILES: a cut-off write and a damaged input.

WHY: the two collectors run unattended and rewrite the same files every
time. Some of them ACCUMULATE: squad_history, the closing substitutions, the
price log and draft_pontok keep what the API can no longer be asked for.

They had two faults at once, and only together did it show what they meant.
Writing started with `open(path, "w")`, which truncates the file at once: if
the run stopped in between (time limit, cancelled workflow), a cut-off JSON
was left behind. Reading fell back to empty under `except Exception` - so the
next run took the damaged file for "no history yet", merged it with the empty
default and wrote it out. Every earlier round would have vanished, silently.

The three functions (stamp, write_compact, read_stored) now live in
collector_common.py, in ONE copy. The test asserts that too: of two copies,
one can forget the guarantee, and that would only show AFTER an interrupted
run.
"""
import importlib.util
import json
import os
import re
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(ROOT))
failures = []


def check(condition, label):
    print(("OK   " if condition else "FAIL ") + label)
    if not condition:
        failures.append(label)


def load(name):
    path = os.path.join(ROOT, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


for name in ("collect", "collect_draft"):
    m = load(name)
    print("\n--- %s.py ---" % name)

    # 1) a missing file means the first run
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "missing.json")
        check(m.read_stored(path, {"rounds": {}}) == {"rounds": {}},
              "a missing file returns the default (first run)")

        # 2) a damaged file is NOT the same: stop, never write an empty history
        damaged = os.path.join(d, "damaged.json")
        with open(damaged, "w", encoding="utf-8") as f:
            f.write('{"rounds": {"1": {"Bence": [')     # cut off
        try:
            m.read_stored(damaged, {"rounds": {}})
            check(False, "a damaged file stops the run (it is not taken as empty)")
        except json.JSONDecodeError:
            check(True, "a damaged file stops the run (it is not taken as empty)")

# 3) the write is atomic: the target is never seen cut off
print("\n--- the atomic write ---")
m = load("collect")
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "x.json")
    m.write_compact(path, {"rounds": {"1": {"a": 1}}})
    m.write_compact(path, {"rounds": {"1": {"a": 1}, "2": {"b": 2}}})
    check(json.loads(open(path, encoding="utf-8").read())["rounds"].keys() >= {"1", "2"},
          "a rewrite puts the complete content in place")
    check(not [x for x in os.listdir(d) if x.endswith(".tmp")],
          "and leaves no temporary file behind")

# 4) THE RULE, not only this one place: nowhere in the two collectors and the
# shared module may a target be opened for WRITING directly - the name is
# always a temporary one, moved into place. A save branch added later cannot
# get round the rule either.
SOURCES = ("collect.py", "collect_draft.py", "collector_common.py")
print("\n--- the rule in the source ---")
total = 0
for name in SOURCES:
    source = open(os.path.join(ROOT, name), encoding="utf-8").read()
    code = re.sub(r'(?s)""".*?"""', "", source)          # without docstrings
    code = re.sub(r"(?m)^\s*#.*$", "", code)             # without comments
    writes = re.findall(r'open\(\s*([^,]+?)\s*,\s*"w"', code)
    total += len(writes)
    direct = [x for x in writes
              if not any(t in x for t in ('.uj"', '.tmp"', "temporary"))]
    check(not direct, "%s: no direct write to a target (%d writes)%s"
          % (name, len(writes), "" if not direct else " - DIRECT: " + ", ".join(direct)))

# The move is in the SHARED module, in one place - so it is required there.
shared = open(os.path.join(ROOT, "collector_common.py"), encoding="utf-8").read()
check("os.replace(" in shared, "the shared module moves the file into place (no copy)")
check(total >= 2, "there is something to check (%d writes in all)" % total)

# 5) BOTH COLLECTORS USE THE SAME THREE FUNCTIONS - from one copy.
import collector_common  # noqa: E402  (ROOT is already on sys.path)
for name in ("collect", "collect_draft"):
    m = load(name)
    check(m.write_compact is collector_common.write_compact
          and m.read_stored is collector_common.read_stored
          and m.stamp is collector_common.stamp,
          "%s.py uses the shared module's functions, not a copy of its own" % name)

print("\n" + ("All checks pass." if not failures
              else "%d checks failed." % len(failures)))
sys.exit(1 if failures else 0)
