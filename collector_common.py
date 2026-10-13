#!/usr/bin/env python3
"""What the two collectors (collect.py, collect_draft.py) do identically.

Not a drawer for "shared things": exactly THREE functions live here, and all
three are about one thing - that the ACCUMULATING files (price log, squad
history, results, matches, closing substitutions) survive an interrupted run.

Those files hold what a run cannot recompute: the past. The price log is the
sharpest case - the MLSZ serves no price history at all
(naplo/mlsz-arelozmeny.txt), so whatever the log loses is lost for good.

WHY IN ONE PLACE: the two collectors run from separate workflows, and for a
long time each wrote this out on its own. While there are two copies, one of
them can forget the guarantee, and the fault only shows AFTER an interrupted
run - when there is nothing left to restore. One copy cannot drift apart.
"""
import json, os, time


def stamp():
    """The `updated` field of the output files - UTC, to the second."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_compact(path, obj):
    """The bookmarklet's compact JSON format - written ATOMICALLY.

    `open(path, "w")` truncates the file first and writes afterwards. If the
    run stops in between (time limit, cancelled workflow), a CUT-OFF JSON is
    left in its place. We write to a temporary file and MOVE it into place;
    the move is atomic, so the target is either the old or the complete new
    content - never half of it.
    """
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


def read_stored(path, default):
    """Read an ACCUMULATING file: missing and damaged are NOT the same.

    Missing (FileNotFoundError): this is the first run, and the default is
    the right answer. EVERY OTHER exception - above all JSON that does not
    parse - is raised.
    Present but unreadable: something broke. Carrying on is the worst thing
    to do - the caller would merge it with the empty default and write it
    back, and the earlier rounds would be gone. We stop instead.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
