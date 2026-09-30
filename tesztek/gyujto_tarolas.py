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

A harom fuggveny (stamp, kompakt_iras, tarolt_olvas) azota a gyujto_kozos.py-ban
all, EGY masolatban. A teszt ezt is allitja: ket masolat kozul az egyik
elfelejtheti a garanciat, es az csak egy felbeszakadt futas UTAN latszana.
"""
import importlib.util
import json
import os
import sys
import tempfile

GYOKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(GYOKER))
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
print("\n--- az atomi iras ---")
m = modul("collect")
with tempfile.TemporaryDirectory() as d:
    ut = os.path.join(d, "x.json")
    m.kompakt_iras(ut, {"rounds": {"1": {"a": 1}}})
    m.kompakt_iras(ut, {"rounds": {"1": {"a": 1}, "2": {"b": 2}}})
    allit(json.loads(open(ut, encoding="utf-8").read())["rounds"].keys() >= {"1", "2"},
          "az újraírás a teljes tartalmat teszi a helyére")
    allit(not [x for x in os.listdir(d) if x.endswith(".uj")],
          "és nem hagy maga után ideiglenes fájlt")
# 4) A SZABALY, nem csak ez az egy hely: sehol a ket gyujtoben es a kozos
# modulban nem nyilhat kozvetlenul IRASRA egy celfajl - a nev mindig
# ideiglenes (".uj"), es mozgatas teszi a helyere. Igy egy kesobb hozzairt uj
# mentesi ag sem kerulheti meg a szabalyt.
import re as _re

FORRASOK = ("collect.py", "collect_draft.py", "gyujto_kozos.py")
print("\n--- a forraskod szabalya ---")
osszes = 0
for nev in FORRASOK:
    forras = open(os.path.join(GYOKER, nev), encoding="utf-8").read()
    kod = _re.sub(r'(?s)""".*?"""', "", forras)          # dokumentacio nelkul
    kod = _re.sub(r"(?m)^\s*#.*$", "", kod)              # megjegyzes nelkul
    irasok = _re.findall(r'open\(\s*([^,]+?)\s*,\s*"w"', kod)
    osszes += len(irasok)
    rossz = [x for x in irasok if '.uj"' not in x and "ideiglenes" not in x]
    allit(not rossz, "%s: nincs kozvetlen iras a celfajlba (%d iras)%s"
          % (nev, len(irasok), "" if not rossz else " - KOZVETLEN: " + ", ".join(rossz)))

# A mozgatas a KOZOS modulban van, egy helyen - ezert itt kell megkovetelni.
kozos = open(os.path.join(GYOKER, "gyujto_kozos.py"), encoding="utf-8").read()
allit("os.replace(" in kozos,
      "a kozos modul mozgatassal teszi a helyere (nem masolassal)")
allit(osszes >= 2, "van mit ellenorizni (%d iras osszesen)" % osszes)

# 5) A KET GYUJTO UGYANAZT A HAROM FUGGVENYT HASZNALJA - egy masolatbol.
# Amig ket kulon masolat volt, az egyik elfelejthette a garanciat, es az csak
# egy felbeszakadt futas UTAN latszott volna, amikor mar nincs mit visszaallitani.
import gyujto_kozos  # noqa: E402  (a GYOKER mar a sys.path-on van)
for nev in ("collect", "collect_draft"):
    m = modul(nev)
    allit(m.kompakt_iras is gyujto_kozos.kompakt_iras
          and m.tarolt_olvas is gyujto_kozos.tarolt_olvas
          and m.stamp is gyujto_kozos.stamp,
          "%s.py a kozos modul fuggvenyeit hasznalja, nem sajat masolatot" % nev)

print("\n" + ("Minden rendben." if not hibak
              else "%d allitas bukott." % len(hibak)))
sys.exit(1 if hibak else 0)
