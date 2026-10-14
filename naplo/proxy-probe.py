#!/usr/bin/env python3
"""CORS proxy probe (2026-08-27).

WHY: the site's live requests (points breakdown, live points, live squad)
are made from the browser, and the MLSZ/FPL APIs cannot be requested directly
from another site (no CORS header) - so a proxy in between is needed. On
2026-08-27 both proxies in use failed at once:
  corsproxy.io  -> HTTP 401 (the service became registration-only)
  allorigins    -> no answer / CORS error
This probe tells WHICH proxy works NOW with both target APIs - not by
guessing, but by trying them all. What matters to the browser is whether the
response carries the Access-Control-Allow-Origin (ACAO) header.
"""
import json, time, urllib.request, urllib.parse

MLSZ = ('https://fantasy-api.mlsz.hu/game-player-stats?include=competition_stat_config'
        '&filter%5Bcompetition_player_id%5D=1249&filter%5Bround_id%5D=85')
FPL = 'https://draft.premierleague.com/api/game'
ORIGIN = 'https://vinceszy.github.io'


def enc(u):
    return urllib.parse.quote(u, safe='')


TS = str(int(time.time() * 1000))
PROXIES = [
    # the two routes used so far - to confirm the fault
    ('corsproxy', lambda u: 'https://corsproxy.io/?url=' + enc(u) + '&_=' + TS),
    ('corsproxy-no-ts', lambda u: 'https://corsproxy.io/?url=' + enc(u)),
    ('allorigins-raw', lambda u: 'https://api.allorigins.win/raw?url=' + enc(u)),
    ('allorigins-get', lambda u: 'https://api.allorigins.win/get?url=' + enc(u)),
    # candidates
    ('codetabs', lambda u: 'https://api.codetabs.com/v1/proxy?quest=' + enc(u)),
    ('cors.lol', lambda u: 'https://api.cors.lol/?url=' + enc(u)),
    ('thingproxy', lambda u: 'https://thingproxy.freeboard.io/fetch/' + u),
    ('workers-demo', lambda u: 'https://test.cors.workers.dev/?' + u),
    ('cors.sh', lambda u: 'https://proxy.cors.sh/' + u),
]


def fetch(url, origin=True):
    t0 = time.time()
    headers = {'Accept': 'application/json',
               'User-Agent': 'Mozilla/5.0 (FunTasy proxy-meres; github.com/Vinceszy/Funtasy-Liga)'}
    if origin:
        headers['Origin'] = ORIGIN
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            test = r.read(150000)
            acao = r.headers.get('access-control-allow-origin')
            try:
                j = json.loads(test)
                # MLSZ: {"data": [...]}; FPL: {"current_event": ...};
                # allorigins-get: {"contents": "..."} (wrapped response)
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


lines = []


def record(s):
    print(s, flush=True)
    lines.append(s)


record('CORS proxy probe · %s · Origin: %s'
       % (time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()), ORIGIN))
record('The fault seen in the browser that the probe was made for:')
record('  direct:CORS · corsproxy:HTTP 401 · allorigins:CORS  (NB1 and PL at once)')
for target_name, target in (('MLSZ', MLSZ), ('FPL', FPL)):
    record('')
    record('=== %s · %s' % (target_name, target))
    st, acao, n, ok, ms = fetch(target)
    record('  %-20s status=%-6s ACAO=%-24s %6d byte  json-ok:%-5s %5d ms'
           % ('direct', st, str(acao), n, ok, ms))
    for name, f in PROXIES:
        st, acao, n, ok, ms = fetch(f(target))
        record('  %-20s status=%-6s ACAO=%-24s %6d byte  json-ok:%-5s %5d ms'
               % (name, st, str(acao), n, ok, ms))
        time.sleep(1.2)

# A proxy can be used from the browser only if it also gives ACAO. The final
# verdict is therefore: status 200 + ACAO ('*' or the Origin) + sensible JSON.
record('')
record('Verdict: a proxy is good where status=200 AND there is ACAO AND json-ok:True.')
with open('naplo/proxy-probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
