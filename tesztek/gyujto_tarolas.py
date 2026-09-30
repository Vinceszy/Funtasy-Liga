#!/usr/bin/env python3
"""A GYULO FAJLOK BIZTONSAGA: felbevagott iras es serult bemenet.

MIERT: a ket gyujto haromoranként fut, felugyelet nelkul, es ugyanazokat a
fajlokat irja ujra. Ezek egy resze GYULO: a squad_history, a zarasok, az
arnaplo es a draft_pontok azt orzi, ami mar nem kerdezheto vissza az API-tol.

KET HIBA VOLT BENNUK EGYSZERRE, es csak egyutt latszott, mit jelentenek.
Az iras az `open(path, "w")`-vel kezdodott, ami azonnal nullara vagja a
fajlt: ha a futas kozben all le (idokorlat, leallitott munkafolyamat), a
helyen felbevagott JSON marad. A beolvasas pedig `except Exception` alatt
uresre valtott - vagyis a kovetkezo futas a serult fajlt "meg nincs
elozmeny"-kent ertelmezte, osszefesulte az ures alappal, es kiirta. Az addigi
fordulok adata ezzel eltunt volna, csendben.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

GYOKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hibak = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    if not felt:
        hibak.append(cimke)


def modul(nev):
    ut = os.path.join(GYOKER, nev + ".py")
    spec = importlib.util.spec_from_file_location(nev, ut)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


for nev in ("collect", "collect_draft"):
    m = modul(nev)
    print("\n--- %s.py ---" % nev)

    # 1) hianyzo fajl = elso futas
    with tempfile.TemporaryDirectory() as d:
        ut = os.path.join(d, "nincs.json")
        allit(m.tarolt_olvas(ut, {"rounds": {}}) == {"rounds": {}},
              "hiányzó fájlnál az alapértelmezés jön (első futás)")

        # 2) serult fajl NEM ugyanaz: megallunk, nem irunk ures elozmenyt
        ut2 = os.path.join(d, "serult.json")
        with open(ut2, "w", encoding="utf-8") as f:
            f.write('{"rounds": {"1": {"Bence": [')     # felbevagott
        try:
            m.tarolt_olvas(ut2, {"rounds": {}})
            allit(False, "sérült fájlnál megállunk (nem vesszük üresnek)")
        except json.JSONDecodeError:
            allit(True, "sérült fájlnál megállunk (nem vesszük üresnek)")

# 3) az iras atomi: a celfajl soha nem latszik felbevagva
m = modul("collect")
with tempfile.TemporaryDirectory() as d:
    ut = os.path.join(d, "x.json")
    m.kompakt_iras(ut, {"rounds": {"1": {"a": 1}}})
    elso = open(ut, encoding="utf-8").read()
    m.kompakt_iras(ut, {"rounds": {"1": {"a": 1}, "2": {"b": 2}}})
    allit(json.loads(open(ut, encoding="utf-8").read())["rounds"].keys() >= {"1", "2"},
          "az újraírás a teljes tartalmat teszi a helyére")
    allit(not [x for x in os.listdir(d) if x.endswith(".uj")],
          "és nem hagy maga után ideiglenes fájlt")
# 4) A SZABALY, nem csak ez az egy hely: mindket gyujtoben MINDEN irasra
# nyitott fajl neve ideiglenes (".uj"-ra vegzodik), es utana mozgatas jon.
# Igy egy kesobb hozzairt uj mentesi ag sem kerulheti meg a szabalyt.
import re as _re
for nev in ("collect.py", "collect_draft.py"):
    forras = open(os.path.join(GYOKER, nev), encoding="utf-8").read()
    kod = _re.sub(r'(?m)^\s*#.*$', '', _re.sub(r'"""».*?"""', '', forras, flags=_re.S))
    kod = _re.sub(r'(?s)""".*?"""', '', forras)
    kod = _re.sub(r'(?m)^\s*#.*$', '', kod)
    irasok = _re.findall(r'open\(\s*([^,]+?)\s*,\s*"w"', kod)
    rossz = [x for x in irasok if '".uj"' not in x and not x.endswith('.uj"')
             and 'ideiglenes' not in x]
    allit(not rossz, "%s: minden írás ideiglenes fájlba megy (%d írás)%s"
          % (nev, len(irasok), "" if not rossz else " - KÖZVETLEN: " + ", ".join(rossz)))
    allit(kod.count("os.replace(") >= 1, "%s: és mozgatás teszi a helyére" % nev)

print("\n" + ("Minden rendben." if not hibak
              else "%d allitas bukott." % len(hibak)))
sys.exit(1 if hibak else 0)
