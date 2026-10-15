#!/usr/bin/env python3
"""bookmarklet-source.js  ->  bookmarklet.txt

The bookmarklet's source code is edited in bookmarklet-source.js, and then this
script is run. It joins the lines, percent-encodes them, and writes the
one-line version that can be pasted into the browser.

    python3 bookmarklet-build.py

The bookmark in the browser then has to be updated by hand: it runs from
there, not from the repository.
"""
import re, sys, urllib.parse

SRC, DST, MARKER = "bookmarklet-source.js", "bookmarklet.txt", "// ==BOOKMARKLET-START=="

# These characters are left unencoded (this reproduces the existing file bit
# for bit). Anything not on the list goes in as %XX - so a new character is
# still encoded correctly.
SAFE = set(' "-.0123456789<>ABCDEFGHIJKLMNOPRSTUVW_abcdefghijklmnopqrstuvwxyz'
           '·Ááéíóöüő–—…✔')


def encode(s):
    return "".join(c if c in SAFE else "".join("%%%02X" % b for b in c.encode("utf-8"))
                   for c in s)


def main():
    src = open(SRC, encoding="utf-8").read()
    if MARKER not in src:
        sys.exit("ERROR: the '%s' marker is missing from %s." % (MARKER, SRC))
    body = src.split(MARKER, 1)[1]

    # Safety brake: a real token must never get into the output.
    leak = re.search(r"gh[pousr]_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}", body)
    if leak:
        sys.exit("ERROR: text that looks like a real token in the source (%s...). "
                 "Put IDE_A_TOKEN back in its place." % leak.group(0)[:12])

    code = " ".join(l.strip() for l in body.strip().splitlines() if l.strip())
    out = "javascript:" + encode(code) + "\n"
    open(DST, "w", encoding="utf-8").write(out)

    back = urllib.parse.unquote(out.strip()[len("javascript:"):])
    print("Done: %s (%d characters)" % (DST, len(out.strip())))
    print("Check: the decoded code is %d characters, %d statements."
          % (len(back), back.count(";")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
