#!/usr/bin/env python3
"""Computing the line-up efficiency (collect.py efficiency) - 7 assertions.

The rule: the bench is mandatorily 1 goalkeeper + 1 defender + 1 midfielder
+ 1 forward, so the optimum benches the weakest player of each position;
the captain is the best of the starters. The stored week is already a FINAL
value (captain x2, bench x0.5) - the raw points have to be worked back from
the cap/sub flags.
"""
import importlib.util, os, sys

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'collect.py')
spec = importlib.util.spec_from_file_location('collect', SOURCE)
c = importlib.util.module_from_spec(spec); sys.modules['collect'] = c
spec.loader.exec_module(c)
failures = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


def pl(pos, week, cap=False, sub=False):
    return {"pos": pos, "week": week, "cap": cap, "sub": sub}


# --- perfect line-up: the efficiency is exactly 100% ---
# raw points: K 6/1, H 5/4/3/1, KP 7/6/5/4/2, CS 9/3/2/1
# optimal bench (minimum per position): K1, H1, KP2, CS1 -> x0.5 = 2.5
# raw sum of the starters: (6)+(5+4+3)+(7+6+5+4)+(9+3+2) = 54; captain is the 9
# possible = 54 + 2.5 + 9 = 65.5
PERFECT = ([pl("K", 6), pl("K", 0.5, sub=True)]
           + [pl("H", 5), pl("H", 4), pl("H", 3), pl("H", 0.5, sub=True)]
           + [pl("KP", 7), pl("KP", 6), pl("KP", 5), pl("KP", 4), pl("KP", 1, sub=True)]
           + [pl("CS", 18, cap=True), pl("CS", 3), pl("CS", 2), pl("CS", 0.5, sub=True)])
v = c.efficiency(PERFECT)
check(v is not None and abs(v[1] - 65.5) < 1e-9,
      "possible: minimum per position on the bench, best starter is captain (%.2f)" % (v[1] if v else -1))
check(v is not None and abs(v[0] - v[1]) < 1e-9,
      "the perfect line-up is 100%%: scored == possible (%.2f == %.2f)" % (v or (0, 0)))

# --- bad line-up: the forward with 9 raw points sits on the BENCH (week 4.5),
#     and the armband is on the 5-point defender (week 10) ---
BAD = ([pl("K", 6), pl("K", 0.5, sub=True)]
       + [pl("H", 10, cap=True), pl("H", 4), pl("H", 3), pl("H", 0.5, sub=True)]
       + [pl("KP", 7), pl("KP", 6), pl("KP", 5), pl("KP", 4), pl("KP", 1, sub=True)]
       + [pl("CS", 4.5, sub=True), pl("CS", 3), pl("CS", 2), pl("CS", 1)])
v2 = c.efficiency(BAD)
check(v2 is not None and abs(v2[1] - 65.5) < 1e-9,
      "the possible does NOT depend on the actual line-up (%.2f)" % (v2[1] if v2 else -1))
check(v2 is not None and v2[0] < v2[1],
      "the bad line-up scores less than the possible (%.2f < %.2f)" % (v2 or (0, 0)))
check(v2 is not None and abs(v2[0] - sum(p["week"] for p in BAD)) < 1e-9,
      "the scored value is the sum of the weeks (the official round points)")

# --- incomplete data: not a 15-player squad or a missing position -> None ---
check(c.efficiency(PERFECT[:14]) is None, "no value for a 14-player squad")
check(c.efficiency([pl("K", 1)] * 15) is None, "no value for a single-position (broken) squad")

if failures:
    print("\n%d assertions failed." % len(failures)); sys.exit(1)
print("\nAll seven assertions passed.")
