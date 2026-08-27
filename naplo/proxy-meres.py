#!/usr/bin/env python3
"""CORS-proxy meres (2026-08-27, bejelentett hiba).

MIERT: az oldal elo lekeresei (pont-bontas, elo pontok, elo keret) a
bongeszobol mennek, es az MLSZ/FPL API-t kozvetlenul nem lehet mas oldalrol
lekerni (nincs CORS-fejlec) - ezert kozbeiktatott proxy kell. 2026-08-27-en
mindket hasznalt proxy elhasalt egyszerre:
  corsproxy.io  -> HTTP 401 (a szolgaltatas regisztraciohoz kotott lett)
  allorigins    -> nem valaszol / CORS-hiba
Ez a meres azt mondja meg, MELYIK proxy mukodik MOST mindket cel-API-val -
nem talalgatunk, hanem vegigprobaljuk oket. A bongeszonek az szamit, hogy a
valaszban ott van-e az Access-Control-Allow-Origin (ACAO) fejlec.
"""
import json, time, urllib.request, urllib.parse

MLSZ = ('https://fantasy-api.mlsz.hu/game-player-stats?include=competition_stat_config'
        '&filter%5Bcompetition_player_id%5D=1249&filter%5Bround_id%5D=85')
FPL = 'https://draft.premierleague.com/api/game'
ORIGIN = 'https://vinceszy.github.io'


def enc(u):
    return urllib.parse.quote(u, safe='')


TS = str(int(time.time() * 1000))
PROXYK = [
    # a ket eddigi ut - a hibakep igazolasara
    ('corsproxy', lambda u: 'https://corsproxy.io/?url=' + enc(u) + '&_=' + TS),
    ('corsproxy-ts-nelkul', lambda u: 'https://corsproxy.io/?url=' + enc(u)),
    ('allorigins-raw', lambda u: 'https://api.allorigins.win/raw?url=' + enc(u)),
    ('allorigins-get', lambda u: 'https://api.allorigins.win/get?url=' + enc(u)),
    # jeloltek
    ('codetabs', lambda u: 'https://api.codetabs.com/v1/proxy?quest=' + enc(u)),
    ('cors.lol', lambda u: 'https://api.cors.lol/?url=' + enc(u)),
    ('thingproxy', lambda u: 'https://thingproxy.freeboard.io/fetch/' + u),
    ('workers-demo', lambda u: 'https://test.cors.workers.dev/?' + u),
    ('cors.sh', lambda u: 'https://proxy.cors.sh/' + u),
]


def keres(url, origin=True):
    t0 = time.time()
    fej = {'Accept': 'application/json',
           'User-Agent': 'Mozilla/5.0 (FunTasy proxy-meres; github.com/Vinceszy/Funtasy-Liga)'}
    if origin:
        fej['Origin'] = ORIGIN
    req = urllib.request.Request(url, headers=fej)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            test = r.read(150000)
            acao = r.headers.get('access-control-allow-origin')
            try:
                j = json.loads(test)
                # MLSZ: {"data": [...]}; FPL: {"current_event": ...};
                # allorigins-get: {"contents": "..."} (csomagolt valasz)
                ok = isinstance(j, dict) and bool(
                    j.get('data') is not None or 'current_event' in j or j.get('contents'))
            except Exception:
                ok = False
            return r.status, acao, len(test), ok, round((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('access-control-allow-origin'), 0, False, \
            round((time.time() - t0) * 1000)
    except Exception as e:
        return type(e).__name__ + ':' + str(e)[:48], None, 0, False, \
            round((time.time() - t0) * 1000)


sorok = []


def rogzit(s):
    print(s, flush=True)
    sorok.append(s)


rogzit('CORS-proxy meres · %s · Origin: %s'
       % (time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), ORIGIN))
rogzit('A bongeszos hibakep, ami miatt a meres keszult:')
rogzit('  direkt:CORS · corsproxy:HTTP 401 · allorigins:CORS  (NB1 es PL egyszerre)')
for cel_nev, cel in (('MLSZ', MLSZ), ('FPL', FPL)):
    rogzit('')
    rogzit('=== %s · %s' % (cel_nev, cel))
    st, acao, n, ok, ms = keres(cel)
    rogzit('  %-20s status=%-6s ACAO=%-24s %6d byte  json-ok:%-5s %5d ms'
           % ('direkt', st, str(acao), n, ok, ms))
    for nev, f in PROXYK:
        st, acao, n, ok, ms = keres(f(cel))
        rogzit('  %-20s status=%-6s ACAO=%-24s %6d byte  json-ok:%-5s %5d ms'
               % (nev, st, str(acao), n, ok, ms))
        time.sleep(1.2)

# Egy proxy csak akkor hasznalhato a bongeszobol, ha ACAO-t is ad. A vegso
# itelet ezert: status 200 + ACAO ('*' vagy az Origin) + ertelmes JSON.
rogzit('')
rogzit('Ertekeles: az a proxy jo, ahol status=200 ES van ACAO ES json-ok:True.')
with open('naplo/proxy-meres.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorok) + '\n')
