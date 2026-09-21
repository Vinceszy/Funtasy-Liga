#!/usr/bin/env python3
"""A dokumentacio konzisztenciaja - a tesztsor resze.

MIERT LETEZIK: a kodot tesztek orzik, az eles adatfajlokat a push elotti
diff-ellenorzes - a dokumentaciot viszont sokaig semmi. A doksi-szerkesztes
ketszer hasalt el csendben (a szerkeszto script hibaja a tobbparancsos
kimenet kozepen elveszett), es csak kezi atnezes vette eszre. A kezi
ellenorzes terheles alatt csuszik el; ez a teszt azota kenyszeriti ki.

Amit ellenoriz:
  D1: minden tesztfajlnak van sora a tesztek/README.md tablazataban, es
      EGY sora van - a duplan beirt sor eddig eszrevetlen maradt, mert a
      meglet onmagaban teljesult.
  D2: a repo gyokereben minden .json adatfajlnak van sora a fo README
      fajl-tablazataban - egy uj adatfajl dokumentacio nelkul bukik.
  D3: a fo README fajl-tablazata nem hivatkozik nem letezo fajlra.
  D4: a valtozasok.json minden bejegyzese teljes es jol formazott
      (datum, ismert tipus, legalabb egy liga, cim, leiras).
  D4/b: EGY FUNKCIO = EGY BEJEGYZES. Nem darabolunk szet egy uj funkciot
      tobb naplo-bejegyzesre; amit a nezo egy dolognak lat, az egy
      bejegyzes, akar tobb resze is van. A hatart ott huzzuk meg, ahol a
      szetdarabolas mar felreismerhetetlen: harom vagy tobb bejegyzes
      ugyanarra a napra ES ugyanabbol a TIPUSBOL. A napra szamolas
      tevesen jelzett: egy nap kikerult ket kulon uj funkcio meg egy
      javitas - harom valodi, kulonbozo dolog -, es a szabaly ezt
      darabolasnak latta. Ami darabolasra vall, az harom EGYNEMU
      bejegyzes: harom funkcio-sor egy napon szinte biztosan ugyanannak
      az egy dolognak a reszei.
  D4/c: a funtasy.css kapcsos zarojelei kiegyensulyozottak. Egy tobblet
      zaro jel a bongeszot ELDOBATJA a tobbi szabalyt - a lap nem hibazik,
      csak szetesik tole valahol lentebb, es ez semmilyen viselkedes-
      tesztben nem latszik.
  D5: ugyanez a valtozasok-vazlat.json meg nem publikalt bejegyzeseire.
  D6: minden oldal ugyanazt a ?v= verziot hivatkozza, es a verzio.json
      ugyanazt a szamot tartalmazza.
  D7: a README tartalomjegyzeke egyezik a cimekkel.
  D8: amit a gyujto kiir, azt a workflow commitolja is.
  D9: a megjegyzesek es a fejlesztoi doksi a SZABALYT mondjak el, nem a
      fejlesztes tortenetet - nincs bennuk datum, dontes-kontextusu nev,
      sem "bejelentett / megtortent" jellegu naplo-jelzo.
  D12: egy fordulo beharangozoja es osszefoglaloja nem ismetli egymast.
      A nezo egymas utan olvassa a kettot; ami a beharangozoban elhangzott,
      az ott el is fogyott. Ot szonal hosszabb szo szerinti atfedes bukik.
  D11: cikk csak LEZART adatbol keszulhet. Osszefoglalo csak vegleges
      fordulora, beharangozo pedig csak a soron kovetkezore - egy fordulo
      KOZBEN irt szoveg a meg mozgo szamokbol dolgozik, es a fordulo vegere
      valotlant allit (egy beharangozo azt irta, hogy valaki megnyerte azt a
      meccset, amit a vegen elvesztett).
  D13: osszefoglalo csak ROGZITETT szinestablabol keszulhet. A prozai
      forrasok (magyar beszamolok, a PL sajat perces kozvetitese) csak a
      futasi naploba kerulnek, tehat egy meres eredmenye addig letezik, amig
      az azt lekero munkamenet - az 5. Draft-fordulot ezert kellett ketszer
      begyujteni. Ha egy fordulohoz osszefoglalo all a lapon, akkor a
      naplo/<liga>-colour-<fordulo>.json is all mellette, tele sorral, es
      atmegy a naplo/colour-check.py ellenorzesen.
  D14: egy cikk nem pontfelsorolas. Ki hany pontot hozott, azt a nezo ket
      kattintassal megnezi; a szoveg arrol szol, amit a tabla nem mutat.
      A "pont" szo es alakjai cikkenkent legfeljebb negyszer szerepelhetnek
      - efolott a szoveg a tablazatot irja ujra vesszokkel.
  D10: minden munkafolyamat es minden meres dokumentalva van. A D2 csak a
      gyokerbeli adatfajlokat nezte, es a naplo/ ala tizenharom meres kerult
      be ugy, hogy a naplo README tablazata nem tudott roluk - a nyers adat
      igy ott all, de senki nem tudja, mit mert es mire jutott.
"""
import glob, json, os, re, sys

GYOKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hibak = []


# Az allitasok szamat SZAMOLJUK, nem irjuk be a zaro sorba: a "Mind a nyolc"
# ugyanugy elavult, ahogy uj eset kerult be.
allitasok = []


def allit(felt, cimke):
    print(("OK   " if felt else "HIBA ") + cimke)
    allitasok.append(cimke)
    if not felt:
        hibak.append(cimke)


def olvas(ut):
    with open(os.path.join(GYOKER, ut), encoding="utf-8") as f:
        return f.read()


# ---- D1: minden teszt dokumentalva ----
teszt_readme = olvas("tesztek/README.md")
tesztek = sorted(os.path.basename(f) for f in
                 glob.glob(os.path.join(GYOKER, "tesztek", "*.teszt.js"))
                 + glob.glob(os.path.join(GYOKER, "tesztek", "gyujto_*.py")))
hianyzo = [t for t in tesztek if "`%s`" % t not in teszt_readme]
allit(not hianyzo, "D1: minden tesztfajlnak van sora a tesztek/README-ben"
      + ("" if not hianyzo else " - HIANYZIK: %s" % ", ".join(hianyzo)))
# Csak a TABLAZAT sorait szamoljuk (sor eleji "| `nev` |"), mert a fajlnevre
# a szoveg torzseben is lehet hivatkozni.
dupla = [t for t in tesztek
         if sum(1 for l in teszt_readme.splitlines()
                if l.startswith("| `%s` |" % t)) > 1]
allit(not dupla, "D1/b: egy teszthez egy sor tartozik"
      + ("" if not dupla else " - DUPLAN: %s" % ", ".join(dupla)))

# ---- D2: minden gyokerbeli adatfajl dokumentalva ----
readme = olvas("README.md")
adatfajlok = sorted(os.path.basename(f) for f in
                    glob.glob(os.path.join(GYOKER, "*.json")))
hianyzo = [f for f in adatfajlok if "`%s`" % f not in readme]
allit(not hianyzo, "D2: minden adatfajlnak van sora a README fajl-tablazataban"
      + ("" if not hianyzo else " - HIANYZIK: %s" % ", ".join(hianyzo)))

# ---- D3: a fajl-tablazat nem hivatkozik nem letezore ----
# A "## 2. Fajlok" tablazat soraibol az elso oszlop hivatkozasai. A
# fordulonkenti sablon-utakat (keretek/<fordulo>.json) kihagyjuk.
tabla = re.search(r"## 2\. Fájlok(.*?)\n## ", readme, re.S)
rossz = []
if tabla:
    for ut in re.findall(r"^\| `([^`<]+)` \|", tabla.group(1), re.M):
        teljes = os.path.join(GYOKER, ut)
        if not (os.path.exists(teljes) or os.path.isdir(teljes.rstrip("/"))):
            rossz.append(ut)
allit(tabla is not None and not rossz,
      "D3: a README fajl-tablazata csak letezo fajlra hivatkozik"
      + ("" if not rossz else " - NEM LETEZIK: %s" % ", ".join(rossz)))

# ---- D4/D5: a naplo es a vazlat bejegyzesei teljesek ----
def bejegyzes_gondok(bejegyzesek):
    gond = []
    for i, b in enumerate(bejegyzesek or []):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", b.get("datum") or ""):
            gond.append("%d. bejegyzes: rossz datum %r" % (i + 1, b.get("datum")))
        if b.get("tipus") not in ("funkcio", "bugfix"):
            gond.append("%d. bejegyzes: ismeretlen tipus %r" % (i + 1, b.get("tipus")))
        if not b.get("ligak") or not all(isinstance(x, str) and x for x in b["ligak"]):
            gond.append("%d. bejegyzes: hianyzo/rossz ligak" % (i + 1))
        for mezo in ("cim", "leiras"):
            if not (b.get(mezo) or "").strip():
                gond.append("%d. bejegyzes: ures %s" % (i + 1, mezo))
    return gond


naplo = json.loads(olvas("valtozasok.json"))
gond = bejegyzes_gondok(naplo.get("bejegyzesek"))
allit(not gond, "D4: a valtozasnaplo minden bejegyzese teljes"
      + ("" if not gond else " - " + "; ".join(gond)))

# ---- D4/b: egy funkcio = egy bejegyzes ----
# Ez a szabaly sokszor elhangzott, es sehol nem allt leirva - ezert csuszott
# el ujra meg ujra. A gepi forma nem tudja megmondani, mi "egy funkcio", de
# azt igen, hogy harom bejegyzes egy napon mar biztosan szetdarabolas.
# NEM VISSZAMENOLEGES: a korabbi napokon tobb kulon dolog is kikerult, azokat
# nem irjuk at. A hatar az a nap, amikor a szabaly leirasra kerult.
NAPLO_EGYBEN_TOL = "2026-09-20"
naponta = {}
for b in (naplo.get("bejegyzesek") or []):
    if (b.get("datum") or "") < NAPLO_EGYBEN_TOL:
        continue
    kulcs = (b.get("datum"), b.get("tipus"))
    naponta[kulcs] = naponta.get(kulcs, 0) + 1
sok = sorted(k for k, n in naponta.items() if n >= 3)
allit(not sok, "D4/b: egy funkcio egy bejegyzes, nincs szetdarabolva"
      + ("" if not sok else " - egy napra eso azonos tipusu bejegyzesek: %s"
         % ", ".join("%s %s (%d)" % (d, t, naponta[(d, t)]) for d, t in sok)))

# ---- D4/c: a stiluslap kapcsos zarojelei stimmelnek ----
# Egy tobblet zaro jel utan a bongeszo a KOVETKEZO szabalyokat dobja el, es
# a lap valahol lentebb esik szet - olyan helyen, aminek semmi koze ahhoz,
# amit epp szerkesztettunk. Elesben igy tunt el egy meccs-fejlec elrendezese.
_css = olvas("funtasy.css")
_css_t = re.sub(r"/\*.*?\*/", "", _css, flags=re.S)
_m, _hiba = 0, None
for _i, _ch in enumerate(_css_t):
    if _ch == "{":
        _m += 1
    elif _ch == "}":
        _m -= 1
        if _m < 0 and _hiba is None:
            _hiba = "tobblet zaro jel"
            break
if _hiba is None and _m > 0:
    _hiba = "%d lezaratlan blokk" % _m
allit(_hiba is None, "D4/c: a funtasy.css kapcsos zarojelei kiegyensulyozottak"
      + ("" if _hiba is None else " - " + _hiba))

# A vazlat-fajl a MEG NEM PUBLIKALT bejegyzeseket orzi (tobb szakaszban
# keszulo funkcional a naplo csak a vegen megy ki). Ugyanaz az alaki
# elvaras all ra, hogy a kesz szakasz vegen csak at kelljen mozgatni - es
# hogy egy felig megirt vazlat ne aludjon el evekig eszrevetlenul.
try:
    vazlat = json.loads(olvas("valtozasok-vazlat.json")).get("bejegyzesek")
except FileNotFoundError:
    vazlat = []
gond = bejegyzes_gondok(vazlat)
allit(not gond, "D5: a valtozasnaplo-vazlat minden bejegyzese teljes"
      + ("" if not gond else " - " + "; ".join(gond)))

# D6: a ?v=N gyorsitotar-jelzo MINDEN oldalon ugyanaz.
# A GitHub Pages 1-2 percig gyorsitataroz; a verzioszamot kezzel emeljuk
# minden kiadasnal. Ha csak az egyik oldalon emelkedik, az a masikon REGI
# funtasy.js/css-t hagy - ott a felhasznalo hetekig regi kodot lat, es a
# hibajelentese ertelmezhetetlen lesz. Ezt gepnek kell nezni, nem szemnek.
import json
import re as _re
_verziok = {}
# A lista nem KEZI: minden HTML-lap szamit, ami a kozos reteget hivatkozza.
# A nemzethy/index.html kimaradt belole, es ket verzioval lemaradva szolgalta
# ki a cikkeket - eppen az a lap, amelyik a legtobbet hasznal beloluk.
_V_OLDALAK = sorted(
    os.path.relpath(x, GYOKER).replace(os.sep, "/")
    for x in glob.glob(os.path.join(GYOKER, "**", "*.html"), recursive=True)
    if not os.path.relpath(x, GYOKER).replace(os.sep, "/").startswith(("tesztek/", "tartalek/"))
    and _re.search(r"funtasy\.(js|css)\?v=", open(x, encoding="utf-8").read()))
for _f in _V_OLDALAK:
    for _m in _re.findall(r'(funtasy\.(?:js|css))\?v=(\d+)', olvas(_f)):
        _verziok.setdefault(_m[1], []).append("%s -> %s" % (_f, _m[0]))
allit(len(_verziok) == 1,
      "D6: minden oldal ugyanazt a ?v= verziot hivatkozza"
      + ("" if len(_verziok) == 1
         else " - eltero verziok: " + "; ".join("v=%s (%s)" % (v, ", ".join(h))
                                                for v, h in sorted(_verziok.items()))))

# D6/b: a verzio.json UGYANAZT a szamot tartalmazza, mint a ?v=.
# A ?v= a funtasy.js/css gyorsitotarat tori - a LAP SAJAT HTML-jet NEM. Az
# oldalak HTML-jeben viszont eles logika van, es egy regi HTML a regi szabaly
# szerint fut. Ezert a lap megkerdezi a verzio.json-t, es ha o regebbi,
# EGYSZER ujratolt (FunTasy.verzioOr). Ha a ket szam elcsuszik, ez a vedelem
# vagy nem fog, vagy vegtelen ujratoltest okozna - gepnek kell nezni.
try:
    _vj = json.loads(olvas("verzio.json")).get("v")
except Exception as _e:
    _vj = None
_vhtml = int(list(_verziok)[0]) if len(_verziok) == 1 else None
allit(_vj is not None and _vhtml is not None and int(_vj) == _vhtml,
      "D6/b: a verzio.json egyezik a ?v= szammal (verzio.json: %s, ?v=: %s)"
      % (_vj, _vhtml))

# D8: amit a gyujto KIIR, azt a workflow COMMITOLJA is.
# A workflow-k KEZZEL FELSOROLT fajlokat adnak a committhoz - ez szandekos
# (nem sopor be szemetet), de nema: sokaig a keretvaltozasok.json
# egyaltalan nem volt a listan, tehat a gyujto minden korben helyesen
# kiszamolta, es a repoba SOSEM kerult be. A "Valtoztatasok" fulon ezert
# allt a lezart 7. fordulonal is, hogy "meg nincs pontszam". Semmi nem
# jelezte. Ezt gepnek kell nezni.
_MUNKAK = (("collect.py", ".github/workflows/archive.yml"),
           ("collect_draft.py", ".github/workflows/draft.yml"))
_hianyzo = []
for _coll, _wf in _MUNKAK:
    _add = _re.search(r"git add -A(?: --)? ([^\n]*?)(?: 2>/dev/null)?\n", olvas(_wf))
    _lista = [x.strip("'\"") for x in _add.group(1).split()] if _add else []
    for _f in sorted(set(_re.findall(r'(?:kompakt_iras|kiir_ha_valtozott)\(\s*"([^"]+)"',
                                     olvas(_coll)))):
        _mappa = _f.split("/")[0]
        _fed = any(_f == x or _mappa == x or (x.endswith("*.json") and _f.startswith(x[:-6]))
                   for x in _lista)
        if not _fed:
            _hianyzo.append("%s -> %s" % (_f, _wf))
allit(not _hianyzo,
      "D8: amit a gyujto kiir, azt a workflow commitolja is"
      + ("" if not _hianyzo else " - HIANYZIK: " + "; ".join(_hianyzo)))

# ---- D11: cikk csak lezart adatbol ----
# A lap sajat kapuja futasidoben elrejti a le nem zart fordulo osszefoglalojat,
# de az MEGIRNI nem akadalyozza meg - es a baj nem is ott volt: a KOVETKEZO
# fordulo beharangozoja hivatkozik a mostani allasra, tehat egy meg futo
# fordulo kozben irva a szamai a fordulo vegere megfordulhatnak.
def _vegso_fordulo():
    eredmeny = json.loads(olvas("results.json"))
    ideiglenes = {int(x) for x in (eredmeny.get("provisional") or [])}
    zart = {int(r) for r, ms in (eredmeny.get("schedule") or {}).items()
            if int(r) not in ideiglenes
            and any(m[2] is not None for m in ms)}
    return max(zart) if zart else 0, zart


_utolso, _zart_nb1 = _vegso_fordulo()
_pl_zart = {int(x) for x in
            (json.loads(olvas("draft_history.json")).get("veglegesek") or [])}
_ZART = {"nb1": _zart_nb1, "pl": _pl_zart}
_baj = []
for _fajl in ("articles.json", "articles-draft.json"):
    _cikkek = json.loads(olvas(_fajl))
    for _liga, _fordulok in (_cikkek.get("leagues") or {}).items():
        _utolso_liga = max(_ZART.get(_liga) or {0})
        for _r, _fajtak in _fordulok.items():
            if "summary" in _fajtak and int(_r) not in (_ZART.get(_liga) or set()):
                _baj.append("%s: %s %s. osszefoglalo, pedig a fordulo nem vegleges"
                            % (_fajl, _liga, _r))
            # Lezart fordulo beharangozoja ARCHIVUM, az rendben van: egy
            # fordulo eloszor beharangozot kap, aztan osszefoglalot. Az a
            # hiba, ha a beharangozo ELORE szalad: a kovetkezo utani fordulot
            # a mostani allasbol kellene megirni, az pedig meg mozog.
            # A heti rovat ugyanezt a hatart tartja: elore nezhet, de csak a
            # soron kovetkezo fordulora - azon tul a sajat szamai mozognanak.
            if ("preview" in _fajtak or "elemzes" in _fajtak) and int(_r) > _utolso_liga + 1:
                _baj.append("%s: %s %s. beharangozo, pedig a soron kovetkezo a %d. "
                            "- a szamai meg valtoznak"
                            % (_fajl, _liga, _r, _utolso_liga + 1))
allit(not _baj, "D11: cikk csak lezart adatbol keszult"
      + ("" if not _baj else " - " + "; ".join(_baj)))

# ---- D12: a beharangozo es az osszefoglalo nem ismetli egymast ----
# Ket kezi atiras utan gepre bizzuk: a szem atsiklik egy visszakoszono
# mondaton, kulonosen a sajat mondatan.
def _szavak(cikk, nevek=()):
    szoveg = " ".join(cikk.get("text") or []) + " " + (cikk.get("short") or "")
    t = _re.findall(r"\w+", szoveg.lower(), _re.UNICODE)
    # A CSAPATNEV nem szoismetles: a "One More Last Ride" negy szo, es barmelyik
    # emlitese hatos atfedesnek latszott a nevelovel meg a ragjaval egyutt. A nev
    # helyere egyetlen jelzo kerul, igy csak az korulotte levo szoveg szamit.
    for nev in sorted(nevek, key=len, reverse=True):
        n = _re.findall(r"\w+", nev.lower(), _re.UNICODE)
        if not n:
            continue
        ki, i = [], 0
        while i < len(t):
            if t[i:i + len(n)] == n:
                ki.append("\u00abcsapat\u00bb")
                i += len(n)
            else:
                ki.append(t[i])
                i += 1
        t = ki
    return t


_atfedes = []
for _fajl in ("articles.json", "articles-draft.json"):
    _cikkek = json.loads(olvas(_fajl))
    for _liga, _fordulok in (_cikkek.get("leagues") or {}).items():
        for _r, _fajtak in _fordulok.items():
            _be, _ossz = _fajtak.get("preview") or {}, _fajtak.get("summary") or {}
            for _par in set(_be) & set(_ossz):
                _nevek = tuple(_par.split("|"))
                _a, _b = _szavak(_be[_par], _nevek), _szavak(_ossz[_par], _nevek)
                _hatos = {tuple(_a[i:i + 6]) for i in range(len(_a) - 5)}
                _kozos = [" ".join(t) for i in range(len(_b) - 5)
                          for t in [tuple(_b[i:i + 6])] if t in _hatos]
                if _kozos:
                    _atfedes.append("%s %s. %s: \"%s\"" % (_liga, _r, _par, _kozos[0]))
allit(not _atfedes, "D12: a beharangozo es az osszefoglalo nem ismetli egymast"
      + ("" if not _atfedes else " - ATFEDES: " + "; ".join(_atfedes[:3])))

# ---- D13: osszefoglalo csak rogzitett szinestablabol ----
# A prozai forras a futasi naploban el es sehol masutt. Ha a sorok nem
# kerulnek be a tablaba, a kovetkezo munkamenet ujra begyujti ugyanazt -
# vagy ami rosszabb, emlekezetbol ir.
import subprocess as _sp

# A szabaly elott irt fordulok: a prozajuk akkor csak a futasi naploban volt,
# es ujra begyujteni oket eppen az a masodik futas lenne, amit a szabaly tilt.
# Nem datum alol mentesulnek, hanem nevre - igy a lista latszik es fogy.
_D13_KIVETEL = {("nb1", "7"), ("pl", "4")}

_szin = []
for _fajl in ("articles.json", "articles-draft.json"):
    _cikkek = json.loads(olvas(_fajl))
    for _liga, _fordulok in (_cikkek.get("leagues") or {}).items():
        for _r, _fajtak in _fordulok.items():
            if not (_fajtak.get("summary") or {}) or (_liga, _r) in _D13_KIVETEL:
                continue
            _ut = os.path.join(GYOKER, "naplo", "%s-colour-%s.json" % (_liga, _r))
            if not os.path.exists(_ut):
                _szin.append("%s %s.: nincs szinestabla" % (_liga, _r))
                continue
            _t = json.loads(open(_ut, encoding="utf-8").read())
            _sorok = [x for x in (_t.get("allitasok") or [])
                      if x.get("horgony") != "nyilatkozat"]
            if not _sorok:
                _szin.append("%s %s.: ures szinestabla" % (_liga, _r))
                continue
            _f = _sp.run([sys.executable, os.path.join(GYOKER, "naplo", "colour-check.py"),
                          _liga, _r], capture_output=True, text=True)
            if _f.returncode:
                _szin.append("%s %s.: %s" % (_liga, _r,
                                             (_f.stdout or _f.stderr).strip().splitlines()[-1]))
allit(not _szin, "D13: osszefoglalo csak rogzitett szinestablabol keszult"
      + ("" if not _szin else " - " + "; ".join(_szin[:3])))

# ---- D14: a cikk nem pontfelsorolas ----
# Nem a szamokkal van baj, hanem azzal, amikor a szoveg helyett allnak ott.
# A "pontos", "pontosan", "pontjan" nem ide tartozik: azok mast jelentenek.
_PONT = _re.compile(
    r"\bpont(ok|ot|okat|ja|jai|jat|jaik|tal|ttal|nyi|ig|ba|ban|ra|rol|hoz|szam\w*)?\b",
    _re.IGNORECASE | _re.UNICODE)
_PONT_MAX = 4

# A szabaly elott irt fordulok. Ezek a szovegek atmentek a jovahagyason, es
# nem irjuk at oket utolag a hatunk mogott: a lista nevre szol es fogy.
_D14_KIVETEL = {
    ("nb1", "7", "summary"), ("nb1", "8", "preview"), ("nb1", "8", "summary"),
    ("nb1", "9", "preview"), ("pl", "4", "summary"), ("pl", "5", "preview"),
}

_suru = []
for _fajl in ("articles.json", "articles-draft.json"):
    _cikkek = json.loads(olvas(_fajl))
    for _liga, _fordulok in (_cikkek.get("leagues") or {}).items():
        for _r, _fajtak in _fordulok.items():
            for _fajta, _parok in _fajtak.items():
                if (_liga, _r, _fajta) in _D14_KIVETEL:
                    continue
                for _par, _cikk in (_parok or {}).items():
                    _sz = " ".join(_cikk.get("text") or []) + " " + (_cikk.get("short") or "")
                    _db = len(_PONT.findall(_sz))
                    if _db > _PONT_MAX:
                        _suru.append("%s %s. %s (%s): %dx" % (_liga, _r, _par, _fajta, _db))
allit(not _suru, "D14: a cikkek nem pontfelsorolasok"
      + ("" if not _suru else " - TULSURU: " + "; ".join(_suru[:3])))

# ---- D10: minden munkafolyamat es minden meres dokumentalva ----
# Ket helyen szokott elmaradni: egy uj workflow a fo README fajl-tablazatabol,
# egy uj meres pedig a naplo sajat tablazatabol. Mindketto csendes: a fajl ott
# van, fut is, csak senki nem tudja, mi az.
_naplo_readme = olvas("naplo/README.md")
_hianyzo = [os.path.basename(f) for f in
            sorted(glob.glob(os.path.join(GYOKER, ".github", "workflows", "*.yml")))
            if "`.github/workflows/%s`" % os.path.basename(f) not in readme]
_hianyzo += [os.path.basename(f) for f in
             sorted(glob.glob(os.path.join(GYOKER, "naplo", "*.py"))
                    + glob.glob(os.path.join(GYOKER, "naplo", "*.txt")))
             if "`%s`" % os.path.basename(f) not in _naplo_readme]
allit(not _hianyzo, "D10: minden munkafolyamat es meres dokumentalva van"
      + ("" if not _hianyzo else " - HIANYZIK: %s" % ", ".join(_hianyzo)))

# D7: a README tartalomjegyzeke egyezik a tenyleges cimekkel.
# A fajl 1500+ soros; jegyzek nelkul kereshetetlen, elavult jegyzekkel meg
# felrevezeto. Ezert a jegyzek NEM kezi munka: itt keszul ujra a cimekbol, es
# ha eltert, a teszt kiirja a helyes szoveget - be lehet masolni.
_JELOLES = "<!-- tartalomjegyzek: a tesztek/dokuk.py tartja karban, kezzel ne szerkeszd -->"


def _slug(cim):
    t = cim.strip().lower()
    for x in ("\u201e", '"', "\u201d"):
        t = t.replace(x, "")
    t = re.sub(r"[^\w\s\u00c0-\u024f-]", "", t, flags=re.UNICODE)
    return t.replace(" ", "-")


def _cimek(szoveg):
    ki, kod = [], False
    for l in szoveg.split("\n"):
        if l.startswith("```"):
            kod = not kod
            continue
        if kod:
            continue
        if l.startswith("## "):
            ki.append((2, l[3:].strip()))
        elif l.startswith("### "):
            ki.append((3, l[4:].strip()))
    return ki


def _jegyzek(szoveg):
    sorok = [_JELOLES, "<details>", "<summary><b>Tartalom</b></summary>", ""]
    for sz, c in _cimek(szoveg):
        sorok.append("%s- [%s](#%s)" % ("  " * (sz - 2), c, _slug(c)))
    return "\n".join(sorok + ["", "</details>"])


_readme = olvas("README.md")
if _JELOLES not in _readme:
    allit(False, "D7: a README-ben nincs tartalomjegyzek (a jelolo hianyzik)")
else:
    _eleje = _readme.index(_JELOLES)
    _vege = _readme.index("</details>", _eleje) + len("</details>")
    _mostani = _readme[_eleje:_vege]
    _kell = _jegyzek(_readme)
    # "python3 tesztek/dokuk.py --javit" ujrairja a jegyzeket. Igy egy uj
    # cim utan nem kell kezzel masolgatni - es nem is fog elmaradni.
    if _mostani != _kell and "--javit" in sys.argv:
        with open(os.path.join(GYOKER, "README.md"), "w", encoding="utf-8") as _f:
            _f.write(_readme[:_eleje] + _kell + _readme[_vege:])
        print("  . README tartalomjegyzek ujrairva (--javit)")
        _mostani = _kell
    allit(_mostani == _kell,
          "D7: a README tartalomjegyzeke egyezik a cimekkel"
          + ("" if _mostani == _kell else
             " - futtasd: python3 tesztek/dokuk.py --javit"))

# ---- D9: a repo a kode, nem a fejlesztes naploja ----
# A kodmegjegyzes es a dokumentacio a SZABALYT es annak okat mondja el, nem a
# tortenetet: ki kerte, ki dontotte el, mikor, es mi derult ki elesben. Ezt
# emlekezetre bizni nem lehet - ez az allitas orzi.
#
# Csak MEGJEGYZESEKET es dokumentacio-prozat vizsgal: a kodban es az
# adatfajlokban allo datum lehet valodi ertek (teszt-fixtura kezdesi ido,
# changelog-datum, wrangler compatibility_date), azt nem szabad bantani.
# A naplo/ konyvtar kivetel: ott a mereseknek IDEJUK van, az az adat resze.
TILTOTT = [
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "datum"),
    (re.compile(r"\b\d{4}\.\s*(janu|febru|marci|april|maju|juni|juli|augusz|"
                r"szeptem|oktob|novem|decem)", re.I), "datum"),
    # A resztvevok neve LIGA-ADAT, az szerepelhet (peldaban, kodban is).
    # Amit tiltunk, az a dontes-kontextus: ki kerte, ki dontotte el.
    (re.compile(r"Vince\s+(k[eé]r|d[oö]nt|fogalmaz|szerint)", re.I), "nev"),
    (re.compile(r"BEJELENTETT|BEJELENTVE|MEGTORTENT|MEGTÖRTÉNT"), "naplo-jelzo"),
    (re.compile(r"kiderült|kiderult", re.I), "naplo-jelzo"),
]
KIVETEL_MAPPA = ("tartalek/",)
# A naplo/ alatt a MERESEK kimenete all, azoknak van idejuk - de a modszer es
# a hang leirasa ugyanaz a dokumentacio, mint barmi mas: a szabalyt mondja el
# es az okat, nem azt, hanyadik nekifutasra lett ilyen.
# A meresnek IDEJE van: mikor kerdeztuk meg a forrast, az maga az adat. Ezert
# a naplo/ alatt a datum megengedett - a fejlesztes tortenete viszont nem.
NAPLO_MENTES = ("datum",)


def _c_megjegyzesek(szoveg):
    """JS/CSS/HTML megjegyzesei, a sztringliteralokat atugorva.

    Sajat palyagep kell hozza: egy egyszeru regex a sztringben allo `//`-t is
    megjegyzesnek latna, a megjegyzesben allo idezojel pedig sztringet
    nyitna. Mindketto hamis talalatot adna eles kod felett."""
    ki, i, sor, n = [], 0, 1, len(szoveg)
    while i < n:
        c = szoveg[i]
        if c == "\n":
            sor += 1
            i += 1
        elif c in "\"'`":
            zaro, i = c, i + 1
            while i < n and szoveg[i] != zaro:
                if szoveg[i] == "\\":
                    i += 1
                elif szoveg[i] == "\n":
                    sor += 1
                i += 1
            i += 1
        elif szoveg.startswith("//", i):
            v = szoveg.find("\n", i)
            v = n if v < 0 else v
            ki.append((sor, szoveg[i:v]))
            i = v
        elif szoveg.startswith("/*", i):
            v = szoveg.find("*/", i + 2)
            v = n if v < 0 else v + 2
            ki.append((sor, szoveg[i:v]))
            sor += szoveg.count("\n", i, v)
            i = v
        elif szoveg.startswith("<!--", i):
            v = szoveg.find("-->", i + 4)
            v = n if v < 0 else v + 3
            ki.append((sor, szoveg[i:v]))
            sor += szoveg.count("\n", i, v)
            i = v
        else:
            i += 1
    return ki


def _py_megjegyzesek(szoveg):
    """Python megjegyzesek es dokumentacios sztringek (tokenize-zal)."""
    import io as _io
    import tokenize
    ki = []
    try:
        for t in tokenize.generate_tokens(_io.StringIO(szoveg).readline):
            if t.type == tokenize.COMMENT:
                ki.append((t.start[0], t.string))
            elif t.type == tokenize.STRING and t.string[:3] in ('"""', "'''"):
                ki.append((t.start[0], t.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return ki


def _md_proza(szoveg):
    """Markdown-proza: a koddal keritett blokkok nelkul."""
    ki, kodban = [], False
    for sz, sor in enumerate(szoveg.split("\n"), 1):
        if sor.lstrip().startswith("```"):
            kodban = not kodban
            continue
        if not kodban:
            ki.append((sz, sor))
    return ki


def _yml_megjegyzesek(szoveg):
    return [(sz, sor) for sz, sor in enumerate(szoveg.split("\n"), 1)
            if sor.lstrip().startswith("#")]


_D9_MINTAK = (("*.js", _c_megjegyzesek), ("*.css", _c_megjegyzesek),
              ("*.html", _c_megjegyzesek), ("*.py", _py_megjegyzesek),
              ("*.md", _md_proza), ("*.yml", _yml_megjegyzesek))
_d9 = []
for _minta, _bonto in _D9_MINTAK:
    for _ut in glob.glob(os.path.join(GYOKER, "**", _minta), recursive=True):
        _rel = os.path.relpath(_ut, GYOKER).replace(os.sep, "/")
        if _rel.startswith(".git/") or _rel.startswith(KIVETEL_MAPPA):
            continue
        _naploban = _rel.startswith("naplo/")
        with open(_ut, encoding="utf-8") as _f:
            _szoveg = _f.read()
        for _sor, _reszlet in _bonto(_szoveg):
            for _re, _mi in TILTOTT:
                if _naploban and _mi in NAPLO_MENTES:
                    continue
                _t = _re.search(_reszlet)
                if _t:
                    _d9.append("%s:%d (%s) %s" % (_rel, _sor, _mi, _t.group(0)))
                    break
allit(not _d9, "D9: a megjegyzesek es a doksi nem naplozzak a fejlesztest"
      + ("" if not _d9 else " - %d talalat" % len(_d9)))
if _d9 and "--d9" in sys.argv:
    print("\n".join("  . " + x for x in _d9))

if hibak:
    print("\n%d allitas bukott." % len(hibak))
    sys.exit(1)
print("\nMind a %d allitas rendben." % len(allitasok))
