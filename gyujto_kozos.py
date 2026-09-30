#!/usr/bin/env python3
"""Amit a ket gyujto (collect.py, collect_draft.py) egyformán csinál.

Nem gyujtemeny a "kozos dolgoknak": pontosan HAROM fuggveny all itt, es
mindharom ugyanarrol szol - hogy a GYULO fajlok (arnaplo, keret-elozmeny,
eredmenyek, meccsek, zarasi igazitasok) tulelnek egy felbeszakadt futast.

Ezek a fajlok azt tartalmazzak, amit a futas nem tud ujraszamolni: a multat.
Az ArNAPLO a legelesebb pelda - kimertuk, hogy az MLSZ semmilyen
ar-elozmenyt nem ad (naplo/mlsz-arelozmeny.txt), tehat amit a naplo elveszit,
az visszamenoleg potolhatatlan.

MIERT EGY HELYEN: a ket gyujto kulon munkafolyamatbol fut, es sokaig
kulon-kulon irta le ugyanezt. Amig ket masolat van, az egyik elfelejtheti a
garanciat, es a hiba csak egy felbeszakadt futas UTAN latszik - amikor mar
nincs mit visszaallitani. Egy masolat nem tud szetcsuszni.
"""
import json, os, time


def stamp():
    """A kimeneti fajlok `updated` mezoje - UTC, masodperc-pontossaggal."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def kompakt_iras(path, obj):
    """A konyvjelzoevel azonos, kompakt JSON-formatum - ATOMIKUSAN.

    Az `open(path, "w")` azonnal nullara vagja a fajlt, es csak utana ir. Ha
    a futas kozben all le (idokorlat, leallitott munkafolyamat), a helyen egy
    FELBEVAGOTT JSON marad. Ideiglenes fajlba irunk, es a helyere MOZGATJUK;
    a mozgatas atomi, tehat a celfajl vagy a regi, vagy a teljes uj tartalom
    - felkesz soha.
    """
    ideiglenes = path + ".uj"
    with open(ideiglenes, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.flush()
        os.fsync(f.fileno())
    os.replace(ideiglenes, path)


def tarolt_olvas(path, alap):
    """Egy GYULO fajl beolvasasa: a hianyzo es a serult NEM ugyanaz.

    Hianyzik (FileNotFoundError): ez az elso futas, az alapertelmezes a
    helyes valasz. MINDEN MAS kivetel - elsosorban a nem ertelmezheto JSON -
    tovabbmegy.
    Letezik, de nem olvashato: valami elromlott. Ilyenkor tovabbmenni a
    legrosszabb, amit tehetunk - a hivo osszefesulne az ures alappal, es
    kiirna; a korabbi fordulok adata ezzel eltunne. Inkabb megallunk.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return alap
