#!/usr/bin/env python3
"""A letoltott cikkekbol MEGSZAMOLJA, mi ter vissza - halozat nelkul.

MIERT KULON A LEKEROTOL: a lekeres kolteseges es kulso; az elemzest viszont
barmikor ujra kell futtatni, mas kerdessel. Ezert a `tartalek/kele/` alatti
szoveg a bemenet, es minden szam onnan jon.

MIT DONT EL: egy fogas akkor kerul be a hang leirasaba, ha TOBB cikkben all
ott. Egyetlen cikk formaja az adott cikke - a szamozott tezisek, a sablonos
csoportkorkep -, nem a szerzoe. A kimenet ezert cikkszamot ad, nem talalatot.

A LAP KERETEIT LEVAGJA: a letoltott oldal aljan a kiado sajat "legfrissebb"
savja all, tele idegen cimmel. Ha az bent marad, a bekezdeshossz es a
szokincs merese azt meri, amit a lap tesz oda, nem amit a szerzo ir.
"""
import glob
import os
import re
import sys

GYOKER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORRAS = os.path.join(GYOKER, "tartalek", "kele")
# Innentol a kiado sajat ajanlo-sava jon, nem a cikk.
VAG = ("Itt állíthatod be, hogy a Google kereső",
       "Nézd meg a legfrissebb cikkeinket",
       "A teljes cikket előfizetőink olvashatják el")

FOGASOK = [
    ("onkorrekcio a masodik mondatban", r"\bJó, ez (persze )?csúsztatás|\bJó, (ez|de) \w+,? (viszont|de|csak)"),
    ("elso szemelyu felutes (Nezem/Olvasom/Latom)", r"^(Nézem|Olvasom|Látom|Hallgatom)\b"),
    ("kerdes sajat valasszal", r"\?\s+(Mindjárt megmondom|Megmondom|Nem\.|Dehogy|Igen\.|Rejtély)"),
    ("Felreertes ne essek", r"Félreértés ne essék"),
    ("harmas engedmeny (Tudom ...)", r"Tudom(:| azt is)|végképp tudom"),
    ("gondolatjeles beszuras", r"\s[–-]\s[^–-]{3,60}\s[–-]\s"),
    ("zarojeles rovid valasz", r"\((Nem|Igen|Dehogy|Nyilván|Persze)[^)]{0,60}\)"),
    ("szamozott tezis (alcim szammal)", r"(?m)^\s*\d\.\s+[A-ZÁÉÍÓÖŐÚÜŰ][^\n]{20,}$"),
    ("nevszoi, igetlen felutes", r"^[A-ZÁÉÍÓÖŐÚÜŰ][^.!?\n]{5,60},\s+[^.!?\n]{3,60}\.\s"),
    ("ketszavas sajat parbeszed", r"\b(Tény\? Tény|Dehogynem|Dehogy)\b"),
    ("praeteritio (egy szot sem szolok)", r"egy szót sem szólok|ki se nyissuk"),
    ("mitosz/patosz szokincs", r"\b(bálvány|megváltó|átk[ao]|isten|megtérés|aranycsata|prizmá)"),
    ("ritka szo", r"\b(hóbelevanc|parolázik|sorminta|dzsembori|skrupulus|tobzódó|pedigré|"
                  r"ethosz|érdemesültség|posvány|oktrojál|lóhalálában|netalántán|idestova|"
                  r"dagonyáz|kistafíroz|cech|bicskanyitogató|akarnok|apportál)"),
    ("olvaso megszolitasa", r"\b(gondolom kitaláljátok|Mondjam tovább|leszel szíves|"
                            r"tegyük a szívünkre|könyörgöm)\b"),
]


def torzs(ut):
    with open(ut, encoding="utf-8") as f:
        sorok = [x.rstrip("\n") for x in f]
    # Az elso ket sor a fejlec (cim, url), utana egy ures sor.
    sorok = [x for x in sorok[2:] if x.strip()]
    ki = []
    for x in sorok:
        if any(x.startswith(v) or v in x for v in VAG):
            break
        ki.append(x)
    # A cim es a cimkesor megismetlodik a torzs elott.
    return ki[2:] if len(ki) > 3 else ki


def main():
    fajlok = sorted(glob.glob(os.path.join(FORRAS, "*.txt")))
    if not fajlok:
        print("nincs letoltott cikk a %s alatt" % FORRAS)
        return 1
    sajat, tobbi = [], []
    for ut in fajlok:
        with open(ut, encoding="utf-8") as f:
            fej = f.readline()
        # A sajat irasait a lap a nevevel cimzi - de nem mindet: az
        # osztalynaplo es a velemenycikk is ove, csak maskepp cimezve.
        neve = ut.rsplit("/", 1)[-1]
        ove = (fej.startswith("# Kele János:")
               or "osztalynaplo" in neve or "velemenycikk" in neve
               or "kele-janos" in neve)
        (sajat if ove else tobbi).append(ut)

    print("=" * 70)
    print("KELE-KORPUSZ: %d cikk, ebbol sajat cimzesu iras %d"
          % (len(fajlok), len(sajat)))
    print("=" * 70)

    hossz = []
    for ut in sajat:
        b = torzs(ut)
        hossz += [len(x) for x in b]
        print("\n  %s  (%d bekezdes)" % (os.path.basename(ut)[:58], len(b)))
        if b:
            print("    NYIT: %s" % b[0][:150])
            print("    ZAR : %s" % b[-1][:150])

    if hossz:
        hossz.sort()
        print("\n  bekezdeshossz: median %d, also negyed %d, felso negyed %d"
              % (hossz[len(hossz) // 2], hossz[len(hossz) // 4],
                 hossz[3 * len(hossz) // 4]))

    print("\n  FOGASOK - HANY CIKKBEN (a sajat cimzesu %d-bol)" % len(sajat))
    for nev, minta in FOGASOK:
        re_ = re.compile(minta, re.IGNORECASE | re.MULTILINE)
        db = 0
        pelda = ""
        for ut in sajat:
            sz = "\n".join(torzs(ut))
            m = re_.search(sz)
            if m:
                db += 1
                pelda = pelda or sz[max(0, m.start() - 40):m.end() + 60].replace("\n", " ")
        jel = "ALTALANOS" if db >= max(3, len(sajat) // 3) else "egyedi   "
        print("    %s %2d/%2d  %-38s %s"
              % (jel, db, len(sajat), nev, pelda[:70]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
