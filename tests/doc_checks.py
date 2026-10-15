#!/usr/bin/env python3
"""Consistency of the documentation - part of the test suite.

WHY IT EXISTS: the code is guarded by tests, the live data files by the diff
check before a push - but for a long time nothing guarded the documentation.
Editing the docs failed silently twice (the error of the editing script got
lost in the middle of a multi-command output), and only a manual review
noticed. A manual check slips under load; this test enforces it instead.

What it checks:
  D1: every test file has a row in the tests/README.md table, and exactly
      ONE row - a duplicated row used to go unnoticed, because its mere
      presence was satisfied.
  D2: every .json data file in the repository root has a row in the main
      README's file table - a new data file without documentation fails.
  D3: the main README's file table does not reference a missing file.
  D4: every entry of valtozasok.json is complete and well formed
      (date, known type, at least one league, title, description).
  D4/b: ONE FEATURE = ONE ENTRY. A new feature is not split into several
      changelog entries; what the viewer sees as one thing is one entry,
      even if it has several parts. The line is drawn where the splitting is
      unmistakable: three or more entries on the same day AND of the same
      TYPE. Counting per day alone flagged wrongly: on one day two separate
      new features and a fix went out - three real, different things -, and
      the rule took that for splitting. What indicates splitting is three
      entries OF THE SAME KIND: three feature rows on one day are almost
      certainly parts of the same one thing.
  D4/c: the curly braces of funtasy.css are balanced. One extra closing brace
      makes the browser DROP the following rules - the page does not error,
      it just falls apart somewhere further down, and no behaviour test
      shows it.
  D5: the same for the unpublished entries of valtozasok-vazlat.json.
  D6: every page references the same ?v= version, and verzio.json holds the
      same number.
  D7: the README's table of contents matches the headings.
  D8: what the collector writes, the workflow also commits.
  D9: the comments and the developer docs state the RULE, not the history
      of the development - no date, no name in a decision context, no
      changelog marker of the "announced / happened" kind.
  D12: a round's preview and summary do not repeat each other. The viewer
      reads the two one after the other; what was said in the preview is
      used up there. A verbatim overlap longer than five words fails.
  D11: an article may only be written from CLOSED data. A summary only for a
      final round, a preview only for the next one - a text written DURING
      a round works from numbers still moving, and by the end of the round
      it claims something untrue (a preview wrote that someone had won the
      match that they lost in the end).
  D13: a summary may only be written from a RECORDED colour table. The prose
      sources (Hungarian match reports, the PL's own minute-by-minute
      coverage) only go into the run's log, so the result of a measurement
      exists only as long as the session that fetched it - that is why Draft
      round 5 had to be collected twice. If a summary stands on the page for
      a round, then naplo/<league>-colour-<round>.json stands next to it,
      full of rows, and passes the naplo/colour-check.py check.
  D14: an article is not a list of points. Who brought how many points the
      viewer can see in two clicks; the text is about what the table does
      not show. The word "pont" and its forms may appear at most seven times
      per article - above that the text rewrites the table with commas.
  D17: every article key passes the Worker's rating pattern - otherwise the
       article is out, but it cannot be rated, and that shows nowhere.
  D15: every PUBLISHED piece has a `kozzetett` timestamp. The magazine sorts
      by it; without a stamp a fresh article lands at the bottom of the list,
      among the oldest - that is, it stays invisible on the day it is
      published.
  D16: every page loads THE SAME font stylesheet. Five HTML files call the
      same Google path; if the family list changes on one of them, the pages
      show different fonts, and no behaviour test shows it.
  D10: every workflow and every measurement is documented. D2 only looked at
      the data files in the root, and thirteen measurements went under
      naplo/ without the naplo README table knowing about them - the raw
      data stands there, but nobody knows what it measured and what it found.
"""
import glob, importlib.util, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
failures = []


# The number of assertions is COUNTED, not written into the closing line:
# "All eight" went stale just as a new case was added.
assertions = []


def check(cond, label):
    print(("OK   " if cond else "FAIL ") + label)
    assertions.append(label)
    if not cond:
        failures.append(label)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


# ---- D1: every test is documented ----
test_readme = read("tests/README.md")
tests = sorted(os.path.basename(f) for f in
               glob.glob(os.path.join(ROOT, "tests", "*.test.js"))
               + glob.glob(os.path.join(ROOT, "tests", "collector_*.py")))
missing = [t for t in tests if "`%s`" % t not in test_readme]
check(not missing, "D1: every test file has a row in tests/README"
      + ("" if not missing else " - MISSING: %s" % ", ".join(missing)))
# Only the TABLE rows are counted (a "| `name` |" at the start of the line),
# because the file name can also be referenced in the body text.
duplicate = [t for t in tests
             if sum(1 for l in test_readme.splitlines()
                    if l.startswith("| `%s` |" % t)) > 1]
check(not duplicate, "D1/b: one row belongs to one test"
      + ("" if not duplicate else " - DUPLICATED: %s" % ", ".join(duplicate)))

# ---- D2: every data file in the root is documented ----
readme = read("README.md")
data_files = sorted(os.path.basename(f) for f in
                    glob.glob(os.path.join(ROOT, "*.json")))
missing = [f for f in data_files if "`%s`" % f not in readme]
check(not missing, "D2: every data file has a row in the README file table"
      + ("" if not missing else " - MISSING: %s" % ", ".join(missing)))

# ---- D3: the file table does not reference anything missing ----
# The references in the first column of the rows of the "## 2. Files"
# table. The per-round template paths (keretek/<round>.json) are skipped.
table = re.search(r"## 2\. Files(.*?)\n## ", readme, re.S)
bad = []
if table:
    for path in re.findall(r"^\| `([^`<]+)` \|", table.group(1), re.M):
        full = os.path.join(ROOT, path)
        if not (os.path.exists(full) or os.path.isdir(full.rstrip("/"))):
            bad.append(path)
check(table is not None and not bad,
      "D3: the README file table only references existing files"
      + ("" if not bad else " - DOES NOT EXIST: %s" % ", ".join(bad)))

# ---- D4/D5: the entries of the changelog and the draft are complete ----
def entry_problems(entries):
    problems = []
    for i, b in enumerate(entries or []):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", b.get("datum") or ""):
            problems.append("entry %d: bad date %r" % (i + 1, b.get("datum")))
        if b.get("tipus") not in ("funkcio", "bugfix"):
            problems.append("entry %d: unknown type %r" % (i + 1, b.get("tipus")))
        if not b.get("ligak") or not all(isinstance(x, str) and x for x in b["ligak"]):
            problems.append("entry %d: missing/bad ligak" % (i + 1))
        for field in ("cim", "leiras"):
            if not (b.get(field) or "").strip():
                problems.append("entry %d: empty %s" % (i + 1, field))
    return problems


changelog = json.loads(read("valtozasok.json"))
problems = entry_problems(changelog.get("bejegyzesek"))
check(not problems, "D4: every changelog entry is complete"
      + ("" if not problems else " - " + "; ".join(problems)))

# ---- D4/b: one feature = one entry ----
# This rule was stated many times and written down nowhere - that is why it
# slipped again and again. A machine cannot tell what "one feature" is, but it
# can tell that three entries on one day are surely a split.
# NOT RETROACTIVE: on earlier days several separate things went out, those
# are not rewritten. The boundary is the day the rule was written down.
CHANGELOG_ONE_ENTRY_FROM = "2026-09-20"
per_day = {}
for b in (changelog.get("bejegyzesek") or []):
    if (b.get("datum") or "") < CHANGELOG_ONE_ENTRY_FROM:
        continue
    key = (b.get("datum"), b.get("tipus"))
    per_day[key] = per_day.get(key, 0) + 1
many = sorted(k for k, n in per_day.items() if n >= 3)
check(not many, "D4/b: one feature is one entry, not split up"
      + ("" if not many else " - entries of the same type on one day: %s"
         % ", ".join("%s %s (%d)" % (d, t, per_day[(d, t)]) for d, t in many)))

# ---- D4/c: the curly braces of the stylesheet match ----
# After an extra closing brace the browser drops the FOLLOWING rules, and the
# page falls apart somewhere further down - at a place that has nothing to do
# with what was just edited. In production a match header layout vanished
# this way.
_css = read("funtasy.css")
_css_t = re.sub(r"/\*.*?\*/", "", _css, flags=re.S)
_depth, _error = 0, None
for _i, _ch in enumerate(_css_t):
    if _ch == "{":
        _depth += 1
    elif _ch == "}":
        _depth -= 1
        if _depth < 0 and _error is None:
            _error = "extra closing brace"
            break
if _error is None and _depth > 0:
    _error = "%d unclosed blocks" % _depth
check(_error is None, "D4/c: the curly braces of funtasy.css are balanced"
      + ("" if _error is None else " - " + _error))

# The draft file keeps the NOT YET PUBLISHED entries (for a feature built in
# several stages the changelog only goes out at the end). The same formal
# requirement applies to it, so that at the end of the finished stage it only
# has to be moved - and so that a half-written draft does not sleep unnoticed
# for years.
try:
    draft = json.loads(read("valtozasok-vazlat.json")).get("bejegyzesek")
except FileNotFoundError:
    draft = []
problems = entry_problems(draft)
check(not problems, "D5: every changelog draft entry is complete"
      + ("" if not problems else " - " + "; ".join(problems)))

# D6: the ?v=N cache marker is the same on EVERY page.
# GitHub Pages caches for 1-2 minutes; the version number is raised by hand
# with every release. If it is raised on only one page, the other keeps an OLD
# funtasy.js/css - there the user sees old code for weeks, and their bug
# report becomes impossible to interpret. A machine must look at this, not an
# eye.
import json
import re as _re
_versions = {}
# The list is not MANUAL: every HTML page that references the shared layer
# counts. nemzethy/index.html was left out of it, and served the articles two
# versions behind - exactly the page that uses them the most.
_V_PAGES = sorted(
    os.path.relpath(x, ROOT).replace(os.sep, "/")
    for x in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
    if not os.path.relpath(x, ROOT).replace(os.sep, "/").startswith(("tests/", "tartalek/"))
    and _re.search(r"funtasy\.(js|css)\?v=", open(x, encoding="utf-8").read()))
for _f in _V_PAGES:
    for _m in _re.findall(r'(funtasy\.(?:js|css))\?v=(\d+)', read(_f)):
        _versions.setdefault(_m[1], []).append("%s -> %s" % (_f, _m[0]))
check(len(_versions) == 1,
      "D6: every page references the same ?v= version"
      + ("" if len(_versions) == 1
         else " - different versions: " + "; ".join("v=%s (%s)" % (v, ", ".join(h))
                                                    for v, h in sorted(_versions.items()))))

# D6/b: verzio.json holds THE SAME number as ?v=.
# ?v= busts the cache of funtasy.js/css - NOT of the PAGE'S OWN HTML. But the
# pages' HTML holds live logic, and an old HTML runs by the old rule. So the
# page asks verzio.json, and if it is older itself, it reloads ONCE
# (FunTasy.reloadIfStale). If the two numbers drift apart, this protection
# either does not catch, or causes an endless reload - a machine must look at
# this.
try:
    _vj = json.loads(read("verzio.json")).get("v")
except Exception as _e:
    _vj = None
_vhtml = int(list(_versions)[0]) if len(_versions) == 1 else None
check(_vj is not None and _vhtml is not None and int(_vj) == _vhtml,
      "D6/b: verzio.json matches the ?v= number (verzio.json: %s, ?v=: %s)"
      % (_vj, _vhtml))

# D8: what the collector WRITES, the workflow COMMITS too.
# The workflows add MANUALLY LISTED files to the commit - this is deliberate
# (it does not sweep in rubbish), but silent: for a long time
# keretvaltozasok.json was not on the list at all, so the collector computed
# it correctly in every run, and it NEVER got into the repository. The
# "Valtoztatasok" tab therefore said "no points yet" even for the closed
# round 7. Nothing flagged it. A machine must look at this.
_JOBS = (("collect.py", ".github/workflows/archive.yml"),
         ("collect_draft.py", ".github/workflows/draft.yml"))
_missing = []
for _coll, _wf in _JOBS:
    # Either one `git add -A <files>` line, or a loop over the files that
    # adds only the ones that exist (`for f in <files>; do ... git add`).
    _wft = read(_wf)
    _add = (_re.search(r"for f in ([^\n;]*); do\n[^\n]*git add", _wft)
            or _re.search(r"git add -A(?: --)? ([^\n]*?)(?: 2>/dev/null)?\n", _wft))
    _list = [x.strip("'\"") for x in _add.group(1).split()] if _add else []
    for _f in sorted(set(_re.findall(r'(?:write_compact|write_if_changed)\(\s*"([^"]+)"',
                                     read(_coll)))):
        _folder = _f.split("/")[0]
        _covered = any(_f == x or _folder == x or (x.endswith("*.json") and _f.startswith(x[:-6]))
                       for x in _list)
        if not _covered:
            _missing.append("%s -> %s" % (_f, _wf))
check(not _missing,
      "D8: what the collector writes, the workflow commits too"
      + ("" if not _missing else " - MISSING: " + "; ".join(_missing)))

# ---- D11: an article only from closed data ----
# The page's own gate hides the summary of an unclosed round at run time, but
# it does not prevent WRITING it - and the trouble was not even there: the
# preview of the NEXT round refers to the current standings, so written while
# a round is still running, its numbers can turn around by the end of the
# round.
def _final_round():
    results = json.loads(read("results.json"))
    provisional = {int(x) for x in (results.get("provisional") or [])}
    closed = {int(r) for r, ms in (results.get("schedule") or {}).items()
              if int(r) not in provisional
              and any(m[2] is not None for m in ms)}
    return max(closed) if closed else 0, closed


_last, _closed_nb1 = _final_round()
_pl_closed = {int(x) for x in
              (json.loads(read("draft_history.json")).get("veglegesek") or [])}
_CLOSED = {"nb1": _closed_nb1, "pl": _pl_closed}
_trouble = []
for _file in ("articles.json",):
    _articles = json.loads(read(_file))
    for _league, _rounds in (_articles.get("leagues") or {}).items():
        _last_league = max(_CLOSED.get(_league) or {0})
        for _r, _kinds in _rounds.items():
            if "summary" in _kinds and int(_r) not in (_CLOSED.get(_league) or set()):
                _trouble.append("%s: %s %s. summary, although the round is not final"
                                % (_file, _league, _r))
            # The preview of a closed round is an ARCHIVE, that is fine: a
            # round first gets a preview, then a summary. The error is a
            # preview running AHEAD: the round after the next would have to be
            # written from the current standings, and those still move.
            # The weekly column keeps the same limit: it may look ahead, but
            # only to the next round - beyond that its own numbers would move.
            if ("preview" in _kinds or "elemzes" in _kinds) and int(_r) > _last_league + 1:
                _trouble.append("%s: %s %s. preview, although the next one is round %d "
                                "- its numbers still change"
                                % (_file, _league, _r, _last_league + 1))
check(not _trouble, "D11: articles were written only from closed data"
      + ("" if not _trouble else " - " + "; ".join(_trouble)))

# ---- D12: the preview and the summary do not repeat each other ----
# After two manual rewrites this is left to the machine: the eye skims over a
# recurring sentence, especially its own.
def _words(article, names=()):
    text = " ".join(article.get("text") or []) + " " + (article.get("short") or "")
    t = _re.findall(r"\w+", text.lower(), _re.UNICODE)
    # A TEAM NAME is not a repetition: "One More Last Ride" is four words, and
    # any mention of it looked like a six-word overlap together with the
    # article and its suffix. A single marker replaces the name, so only the
    # text around it counts.
    for name in sorted(names, key=len, reverse=True):
        n = _re.findall(r"\w+", name.lower(), _re.UNICODE)
        if not n:
            continue
        out, i = [], 0
        while i < len(t):
            if t[i:i + len(n)] == n:
                out.append("«csapat»")
                i += len(n)
            else:
                out.append(t[i])
                i += 1
        t = out
    return t


_overlap = []
for _file in ("articles.json",):
    _articles = json.loads(read(_file))
    for _league, _rounds in (_articles.get("leagues") or {}).items():
        for _r, _kinds in _rounds.items():
            _pre, _sum = _kinds.get("preview") or {}, _kinds.get("summary") or {}
            for _pair in set(_pre) & set(_sum):
                _names = tuple(_pair.split("|"))
                _a, _b = _words(_pre[_pair], _names), _words(_sum[_pair], _names)
                _sixes = {tuple(_a[i:i + 6]) for i in range(len(_a) - 5)}
                _shared = [" ".join(t) for i in range(len(_b) - 5)
                           for t in [tuple(_b[i:i + 6])] if t in _sixes]
                if _shared:
                    _overlap.append("%s %s. %s: \"%s\"" % (_league, _r, _pair, _shared[0]))
check(not _overlap, "D12: the preview and the summary do not repeat each other"
      + ("" if not _overlap else " - OVERLAP: " + "; ".join(_overlap[:3])))

# ---- D13: a summary only from a recorded colour table ----
# The prose source lives in the run's log and nowhere else. If the rows do not
# go into the table, the next session collects the same again - or, worse,
# writes from memory.
import subprocess as _sp

# The rounds written before the rule: their prose was then only in the run's
# log, and collecting it again would be exactly the second run the rule
# forbids. They are exempt by name, not by date - this way the list is
# visible and shrinks.
_D13_EXEMPT = {("nb1", "7"), ("pl", "4")}

_colour = []
for _file in ("articles.json",):
    _articles = json.loads(read(_file))
    for _league, _rounds in (_articles.get("leagues") or {}).items():
        for _r, _kinds in _rounds.items():
            if not (_kinds.get("summary") or {}) or (_league, _r) in _D13_EXEMPT:
                continue
            _path = os.path.join(ROOT, "naplo", "%s-colour-%s.json" % (_league, _r))
            if not os.path.exists(_path):
                _colour.append("%s %s.: no colour table" % (_league, _r))
                continue
            _t = json.loads(open(_path, encoding="utf-8").read())
            _rows = [x for x in (_t.get("claims") or [])
                     if x.get("anchor") != "statement"]
            if not _rows:
                _colour.append("%s %s.: empty colour table" % (_league, _r))
                continue
            _res = _sp.run([sys.executable, os.path.join(ROOT, "naplo", "colour-check.py"),
                            _league, _r], capture_output=True, text=True)
            if _res.returncode:
                _colour.append("%s %s.: %s" % (_league, _r,
                                               (_res.stdout or _res.stderr).strip().splitlines()[-1]))
check(not _colour, "D13: summaries were written only from a recorded colour table"
      + ("" if not _colour else " - " + "; ".join(_colour[:3])))

# ---- D14: an article is not a list of points ----
# The trouble is not with the numbers, but with them standing in place of the
# text. "pontos", "pontosan", "pontjan" do not belong here: they mean
# something else.
#
# THE LIMIT DOES NOT ASK TO DROP THE WORD. Pulled down to four, this was the
# consequence: the numbers stayed, the unit vanished from next to them - "the
# ten he did not get", "half of it came in for five", "a quarter unit". The
# article passed the check, and became unreadable. A barefoot number is worse
# than the word. So the limit is as many as the APPROVED articles actually
# used (3-7 in the summaries of rounds 7-8, 7 in the longest); what is above
# that really is a table. The goal is fewer NUMBERS, not fewer WORDS.
_POINTS = _re.compile(
    r"\bpont(ok|ot|okat|ja|jai|jat|jaik|tal|ttal|nyi|ig|ba|ban|ra|rol|hoz|szam\w*)?\b",
    _re.IGNORECASE | _re.UNICODE)
_POINTS_MAX = 7

# The rounds written before the rule. These texts passed the approval, and
# they are not rewritten after the fact: the list is by name and shrinks.
_D14_EXEMPT = {
    ("nb1", "7", "summary"), ("nb1", "8", "preview"), ("nb1", "8", "summary"),
    ("nb1", "9", "preview"), ("pl", "4", "summary"), ("pl", "5", "preview"),
}

_dense = []
for _file in ("articles.json",):
    _articles = json.loads(read(_file))
    for _league, _rounds in (_articles.get("leagues") or {}).items():
        for _r, _kinds in _rounds.items():
            for _kind, _pairs in _kinds.items():
                if (_league, _r, _kind) in _D14_EXEMPT:
                    continue
                for _pair, _article in (_pairs or {}).items():
                    _txt = " ".join(_article.get("text") or []) + " " + (_article.get("short") or "")
                    _count = len(_POINTS.findall(_txt))
                    if _count > _POINTS_MAX:
                        _dense.append("%s %s. %s (%s): %dx" % (_league, _r, _pair, _kind, _count))
check(not _dense, "D14: the articles are not lists of points"
      + ("" if not _dense else " - TOO DENSE: " + "; ".join(_dense[:3])))

# ---- D15: every published piece has a publication timestamp ----
# The magazine sorts by time. What goes out without a stamp falls to the
# bottom of the list - invisible exactly on the day it was published.
_unstamped = []
for _league, _rounds in (json.loads(read("articles.json")).get("leagues") or {}).items():
    for _r, _kinds in _rounds.items():
        for _kind, _pairs in _kinds.items():
            for _pair, _article in (_pairs or {}).items():
                if not (_article.get("kozzetett") or "").strip():
                    _unstamped.append("%s %s. %s %s" % (_league, _r, _kind, _pair))
check(not _unstamped, "D15: every published piece has a publication time"
      + ("" if not _unstamped else " - MISSING: " + "; ".join(_unstamped[:3])))

# ---- D17: every article key passes the Worker's rating filters ----
# The rating key is EXACTLY the string FunTasy.articleList gives
# (league|round|kind|pair), and the Worker's own pattern decides whether it is
# accepted. If a title does not match, the rating fails with 400 - the article
# is out, but no opinion can be given on it, and that shows nowhere. It
# happened once: `elemzes` was missing from the pattern, and every rating of
# the column was lost. The pattern comes from the worker's source, not copied
# here - otherwise this assertion would drift silently.
_wsrc = read(os.path.join("tartalek", "proxy-worker.js"))
_m = re.search(r"export const ARTICLE_KEY_PATTERN\s*=\s*/(.+?)/;", _wsrc, re.S)
check(bool(_m), "D17: the Worker's article pattern is found in the source")
if _m:
    _pattern = re.compile(_m.group(1).strip())
    _bad = []
    for _league, _rounds in (json.loads(read("articles.json")).get("leagues") or {}).items():
        for _r, _kinds in _rounds.items():
            for _kind, _pairs in _kinds.items():
                for _pair in (_pairs or {}):
                    _key = "%s|%s|%s|%s" % (_league, _r, _kind, _pair)
                    if not _pattern.match(_key):
                        _bad.append(_key)
    check(not _bad, "D17: every article key can be rated (by the Worker's pattern)"
          + ("" if not _bad else " - REJECTED: " + "; ".join(_bad[:3])))

# ---- D18: the bookmarklet is what is built from its source ----
# tartalek/bookmarklet.txt is GENERATED: it is built from bookmarklet-source.js
# with bookmarklet-build.py. Two copies of the same code, and the generated one
# is what has to be pasted into the browser. Whoever fixes the source but
# forgets to rebuild leaves an OLD bookmarklet in the repository - and that
# shows nowhere, because both files are there, both make sense.
_bdir = os.path.join(ROOT, "tartalek")
_bspec = importlib.util.spec_from_file_location(
    "bookmarklet_build", os.path.join(_bdir, "bookmarklet-build.py"))
_build = importlib.util.module_from_spec(_bspec)
_bspec.loader.exec_module(_build)               # main() only runs as __main__
_bsrc = read(os.path.join("tartalek", "bookmarklet-source.js"))
_bexpected = "javascript:" + _build.encode(
    " ".join(l.strip() for l in _bsrc.split(_build.MARKER, 1)[1].strip().splitlines()
             if l.strip())) + "\n"
_bactual = read(os.path.join("tartalek", "bookmarklet.txt"))
check(_bexpected == _bactual,
      "D18: the bookmarklet is freshly built from its source (run: cd tartalek && "
      "python3 bookmarklet-build.py)" if _bexpected != _bactual
      else "D18: the bookmarklet is freshly built from its source (%d characters)"
      % len(_bactual.strip()))

# ---- D16: every page loads the same fonts ----
# Five separate HTML files hold the same Google path. If the family list
# changes on one of them, that page comes with a different font - and nothing
# would notice.
_font = _re.compile(r'''fonts\.googleapis\.com/css2\?([^"']+)''')
_sheets = {}
for _path in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
    _rel = os.path.relpath(_path, ROOT).replace(os.sep, "/")
    if _rel.startswith((".git/", "tartalek/")):
        continue
    _t = {m.group(1) for m in _font.finditer(open(_path, encoding="utf-8").read())}
    if _t:
        _sheets[_rel] = _t
_differ = sorted(f for f, t in _sheets.items() if t != next(iter(_sheets.values())))
check(len(_sheets) > 1 and not _differ,
      "D16: every page loads the same font stylesheet (%d pages)" % len(_sheets)
      + ("" if not _differ else " - DIFFERS: " + ", ".join(_differ)))

# ---- D10: every workflow and every measurement is documented ----
# It tends to be left out in two places: a new workflow from the main README's
# file table, and a new measurement from naplo's own table. Both are silent:
# the file is there, it even runs, only nobody knows what it is.
_naplo_readme = read("naplo/README.md")
_missing = [os.path.basename(f) for f in
            sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))
            if "`.github/workflows/%s`" % os.path.basename(f) not in readme]
_missing += [os.path.basename(f) for f in
             sorted(glob.glob(os.path.join(ROOT, "naplo", "*.py"))
                    + glob.glob(os.path.join(ROOT, "naplo", "*.txt")))
             if "`%s`" % os.path.basename(f) not in _naplo_readme]
check(not _missing, "D10: every workflow and measurement is documented"
      + ("" if not _missing else " - MISSING: %s" % ", ".join(_missing)))

# D7: the README's table of contents matches the actual headings.
# The file has 1500+ lines; without a table of contents it cannot be searched,
# with a stale one it is misleading. So the table is NOT manual work: it is
# rebuilt here from the headings, and if it differs, the test prints the
# correct text - it can be pasted in.
_MARKER = "<!-- table of contents: maintained by tests/doc_checks.py, do not edit by hand -->"


def _slug(title):
    t = title.strip().lower()
    for x in ("„", '"', "”"):
        t = t.replace(x, "")
    t = re.sub(r"[^\w\sÀ-ɏ-]", "", t, flags=re.UNICODE)
    return t.replace(" ", "-")


def _headings(text):
    out, in_code = [], False
    for l in text.split("\n"):
        if l.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if l.startswith("## "):
            out.append((2, l[3:].strip()))
        elif l.startswith("### "):
            out.append((3, l[4:].strip()))
    return out


def _toc(text):
    lines = [_MARKER, "<details>", "<summary><b>Contents</b></summary>", ""]
    for level, h in _headings(text):
        lines.append("%s- [%s](#%s)" % ("  " * (level - 2), h, _slug(h)))
    return "\n".join(lines + ["", "</details>"])


_readme = read("README.md")
if _MARKER not in _readme:
    check(False, "D7: the README has no table of contents (the marker is missing)")
else:
    _start = _readme.index(_MARKER)
    _end = _readme.index("</details>", _start) + len("</details>")
    _current = _readme[_start:_end]
    _wanted = _toc(_readme)
    # "python3 tests/doc_checks.py --fix" rewrites the table of contents. This
    # way after a new heading nothing has to be copied by hand - and it will
    # not be left out either.
    if _current != _wanted and "--fix" in sys.argv:
        with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as _f:
            _f.write(_readme[:_start] + _wanted + _readme[_end:])
        print("  . README table of contents rewritten (--fix)")
        _current = _wanted
    check(_current == _wanted,
          "D7: the README's table of contents matches the headings"
          + ("" if _current == _wanted else
             " - run: python3 tests/doc_checks.py --fix"))

# ---- D9: the repository is the code, not the log of the development ----
# The code comments and the documentation state the RULE and its reason, not
# the history: who asked for it, who decided it, when, and what turned up in
# production. This cannot be left to memory - this assertion guards it.
#
# It only examines COMMENTS and documentation prose: a date in code and in the
# data files can be a real value (a test fixture's kick-off time, a changelog
# date, wrangler's compatibility_date), that must not be touched.
# The naplo/ directory is an exception: there the measurements have a TIME,
# which is part of the data.
# The comments and the docs are English; the Hungarian patterns stay too,
# because a note pasted from a Hungarian conversation is the likeliest leak.
FORBIDDEN = [
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "date"),
    (re.compile(r"\b\d{4}\.\s*(janu|febru|marci|april|maju|juni|juli|augusz|"
                r"szeptem|oktob|novem|decem)", re.I), "date"),
    # The participants' names are LEAGUE DATA, they may appear (in an example,
    # in code too). What is forbidden is the decision context: who asked, who
    # decided.
    (re.compile(r"Vince\s+(k[eé]r|d[oö]nt|fogalmaz|szerint)", re.I), "name"),
    (re.compile(r"BEJELENTETT|BEJELENTVE|MEGTORTENT|MEGTÖRTÉNT"), "log-marker"),
    (re.compile(r"kiderült|kiderult", re.I), "log-marker"),
    (re.compile(r"\b(January|February|March|April|May|June|July|August|September|"
                r"October|November|December)\s+\d{1,2},?\s+\d{4}\b"), "date"),
    (re.compile(r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|"
                r"September|October|November|December)\s+\d{4}\b"), "date"),
    (re.compile(r"Vince\s+(asked|wanted|decided|said|requested|prefers)|"
                r"Vince's\s+(request|decision|idea)", re.I), "name"),
    (re.compile(r"\b(it\s+turned\s+out|we\s+found\s+out|we\s+discovered|"
                r"we\s+(?:used\s+to\s+)?thought|we\s+decided|"
                r"(?:was|were)\s+reported\s+(?:by|in)|reported\s+bug)\b", re.I),
     "log-marker"),
]
EXEMPT_FOLDER = ("tartalek/",)
# Under naplo/ stands the OUTPUT of the measurements, those have a time - but
# the description of the method and the voice is the same documentation as
# anything else: it states the rule and its reason, not at which attempt it
# became like this.
# A measurement HAS a time: when the source was asked is the data itself. So
# under naplo/ a date is allowed - the history of the development is not.
NAPLO_EXEMPT = ("date",)


def _c_comments(text):
    """The comments of JS/CSS/HTML, skipping string literals.

    It needs its own scanner: a simple regex would also take a `//` inside a
    string for a comment, and a quote inside a comment would open a string.
    Both would give false hits over live code."""
    out, i, line, n = [], 0, 1, len(text)
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
        elif c in "\"'`":
            closing, i = c, i + 1
            while i < n and text[i] != closing:
                if text[i] == "\\":
                    i += 1
                elif text[i] == "\n":
                    line += 1
                i += 1
            i += 1
        elif text.startswith("//", i):
            e = text.find("\n", i)
            e = n if e < 0 else e
            out.append((line, text[i:e]))
            i = e
        elif text.startswith("/*", i):
            e = text.find("*/", i + 2)
            e = n if e < 0 else e + 2
            out.append((line, text[i:e]))
            line += text.count("\n", i, e)
            i = e
        elif text.startswith("<!--", i):
            e = text.find("-->", i + 4)
            e = n if e < 0 else e + 3
            out.append((line, text[i:e]))
            line += text.count("\n", i, e)
            i = e
        else:
            i += 1
    return out


def _py_comments(text):
    """Python comments and docstrings (with tokenize)."""
    import io as _io
    import tokenize
    out = []
    try:
        for t in tokenize.generate_tokens(_io.StringIO(text).readline):
            if t.type == tokenize.COMMENT:
                out.append((t.start[0], t.string))
            elif t.type == tokenize.STRING and t.string[:3] in ('"""', "'''"):
                out.append((t.start[0], t.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return out


def _md_prose(text):
    """Markdown prose: without the fenced code blocks."""
    out, in_code = [], False
    for no, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            out.append((no, line))
    return out


def _yml_comments(text):
    return [(no, line) for no, line in enumerate(text.split("\n"), 1)
            if line.lstrip().startswith("#")]


_D9_PATTERNS = (("*.js", _c_comments), ("*.css", _c_comments),
                ("*.html", _c_comments), ("*.py", _py_comments),
                ("*.md", _md_prose), ("*.yml", _yml_comments))
_d9 = []
for _glob, _splitter in _D9_PATTERNS:
    for _path in glob.glob(os.path.join(ROOT, "**", _glob), recursive=True):
        _rel = os.path.relpath(_path, ROOT).replace(os.sep, "/")
        if _rel.startswith(".git/") or _rel.startswith(EXEMPT_FOLDER):
            continue
        _in_naplo = _rel.startswith("naplo/")
        with open(_path, encoding="utf-8") as _f:
            _text = _f.read()
        for _line, _part in _splitter(_text):
            for _pat, _what in FORBIDDEN:
                if _in_naplo and _what in NAPLO_EXEMPT:
                    continue
                _hit = _pat.search(_part)
                if _hit:
                    _d9.append("%s:%d (%s) %s" % (_rel, _line, _what, _hit.group(0)))
                    break
check(not _d9, "D9: the comments and the docs do not log the development"
      + ("" if not _d9 else " - %d hits" % len(_d9)))
if _d9 and "--d9" in sys.argv:
    print("\n".join("  . " + x for x in _d9))

# ---- D20: new code is named in English ----
# Code - identifiers, file names, comments - is written in English. Files
# named in Hungarian before that are listed in tests/legacy-hungarian-names.txt;
# the list may only shrink. A new file whose name carries a Hungarian word
# fails here, and so does a listed path that is gone (renamed or deleted)
# but still on the list. The check looks at names only: it is the cheapest
# place where the slip shows, and the one that kept recurring.
_HU_WORDS = ['gyujt', 'kozos', 'tarol', 'meres', 'fordulo', 'parosit', 'atigazol', 'elott', 'cikk', 'keret', 'zaras', 'teszt', 'adat', 'naplo', 'valtoz', 'szin', 'beszamolo', 'ertekel', 'esemeny', 'forras', 'hang', 'kispad', 'karszalag', 'jatekos', 'merkozes', 'dupla', 'arelozmeny', 'perc', 'csere', 'figyelo', 'allapot', 'eloora', 'frissjelzo', 'visszateres', 'betukeszlet', 'kezdo', 'tabla', 'eredmeny', 'meccs', 'hatekonysag', 'ujdonsag', 'csapat', 'kozvetit', 'epites', 'kulonbseg', 'lekeres', 'mentes', 'uzenet', 'ellenor', 'lezar', 'osszeg', 'pont']
_legacy = {l.strip() for l in read("tests/legacy-hungarian-names.txt").splitlines()
           if l.strip() and not l.startswith("#")}
import subprocess as _sp
_tracked = _sp.run(["git", "-C", ROOT, "ls-files"], capture_output=True,
                   text=True).stdout.split()
_named = [f for f in _tracked if not f.startswith("tartalek/")
          and re.search(r"\.(py|js|sh|yml|md|txt)$", f)
          and any(w in os.path.basename(f).lower() for w in _HU_WORDS)]
_new_hu = sorted(set(_named) - _legacy)
_gone = sorted(p for p in _legacy if p not in _tracked)
check(not _new_hu and not _gone, "D20: new code files are named in English"
      + ("" if not _new_hu else " - HUNGARIAN NAME: " + ", ".join(_new_hu[:5]))
      + ("" if not _gone else " - NO LONGER EXISTS, remove from the list: " + ", ".join(_gone[:5])))

if failures:
    print("\n%d assertions failed." % len(failures))
    sys.exit(1)
print("\nAll %d assertions passed." % len(assertions))
