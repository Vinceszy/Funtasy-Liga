#!/usr/bin/env python3
"""GOMB-forras.js  ->  GOMB-bookmarklet.txt

A konyvjelzo forraskodjat a GOMB-forras.js-ben kell szerkeszteni, majd ezt
a szkriptet lefuttatni. A szkript osszefuzi a sorokat, szazalekjelesen
kodolja, es kiirja a bongeszobe illesztheto egysoros valtozatot.

    python3 GOMB-epites.py

A bongeszoben levo konyvjelzot ezutan kezzel kell frissiteni: az onnan fut,
nem a repobol.
"""
import re, sys, urllib.parse

SRC, DST, MARKER = "GOMB-forras.js", "GOMB-bookmarklet.txt", "// ==BOOKMARKLET-START=="

# Ezeket a karaktereket hagyjuk kodolatlanul (igy all elo bitre az eddigi fajl).
# Ami nincs a listan, az %XX formaban kerul be - uj karakter eseten is helyes marad.
SAFE = set(' "-.0123456789<>ABCDEFGHIJKLMNOPRSTUVW_abcdefghijklmnopqrstuvwxyz'
           '·Ááéíóöüő–—…✔')


def encode(s):
    return "".join(c if c in SAFE else "".join("%%%02X" % b for b in c.encode("utf-8"))
                   for c in s)


def main():
    src = open(SRC, encoding="utf-8").read()
    if MARKER not in src:
        sys.exit("HIBA: nincs meg a '%s' jelolo a %s fajlban." % (MARKER, SRC))
    body = src.split(MARKER, 1)[1]

    # Biztonsagi fek: valodi token soha ne kerulhessen a kimenetbe.
    leak = re.search(r"gh[pousr]_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}", body)
    if leak:
        sys.exit("HIBA: valodi tokennek tuno szoveg a forrasban (%s...). "
                 "Csereld vissza IDE_A_TOKEN-re." % leak.group(0)[:12])

    code = " ".join(l.strip() for l in body.strip().splitlines() if l.strip())
    out = "javascript:" + encode(code) + "\n"
    open(DST, "w", encoding="utf-8").write(out)

    back = urllib.parse.unquote(out.strip()[len("javascript:"):])
    print("Kesz: %s (%d karakter)" % (DST, len(out.strip())))
    print("Ellenorzes: a visszafejtett kod %d karakter, %d utasitas."
          % (len(back), back.count(";")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
