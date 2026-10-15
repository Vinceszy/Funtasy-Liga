const { BASE, check, launch, finish } = require('./common');
// The player's match above the points breakdown in NB1 (from meccsek.json).
//
// What it pins down:
//  - finished match: clubs + result + "vége"
//  - match not yet started: NO made-up 0-0, only the two clubs
//  - a match within the 180-minute time limit: "a meccs zajlik" (state gate)
//  - a match started long ago but without a result: the "vége" label without a result
//  - another club's match does not appear; a club with a double match gets two rows
//  - breakdownHTML puts the match row ABOVE the table; with nogame there is no row
(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await p.route('**fantasy-api.mlsz.hu/**', route => {
    const u = decodeURIComponent(route.request().url());
    if (/game-player-stats/.test(u))
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ data: [
          { value: 1, points: 3, competition_stat_config: { name: 'Győzelem' } },
          { value: 77, points: 0, competition_stat_config: { name: 'Játszott perc' } },
        ] }) });
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{"data":[]}' });
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof gameRowsHTML === 'function', null, { timeout: 20000 });
  // WE STATE THE PRECONDITION: the page loads meccsek.json WITHOUT blocking,
  // and when the response arrives it OVERWRITES GAMES (nb1/index.html:
  // GAMES=null, then the fetch's .then sets it). If the test puts in its own
  // round 7 first, the late response wipes it out - the test then measures
  // empty lists, and all five match assertions fail. It came up under load.
  await p.waitForFunction(() => typeof GAMES !== 'undefined' && GAMES !== null,
                          null, { timeout: 20000 });

  const m = await p.evaluate(async () => {
    const hour = 3600e3, day = 24 * hour;
    const iso = t => new Date(t).toISOString().replace(/\.\d+Z$/, '+00:00');
    GAMES = { 7: [
      { h: 'VASAS', v: 'ETO', hp: 2, vp: 2, vege: true, start: iso(Date.now() - 3 * day) },
      { h: 'PAFC',  v: 'MTK', start: iso(Date.now() + 2 * day) },          // still ahead
      { h: 'ZTE',   v: 'ETO', start: iso(Date.now() - 1 * hour) },         // in progress now
      { h: 'DVSC',  v: 'PAKS', start: iso(Date.now() - 6 * hour) },        // over, no result yet
    ] };
    const rows = html => {
      const d = document.createElement('div');
      d.innerHTML = html;
      return [...d.querySelectorAll('.bontasmeccs')]
        .map(x => [x.children[0].textContent.trim().replace(/\s+/g, ' '),
                   x.children[1].textContent.trim()]);
    };
    // integration: breakdownHTML puts the match row ABOVE the table
    const full = await breakdownHTML({ own: 'X', nm: 'Y', r: '7', cp: '555',
                                      tm: 'VASAS', pl: '1', vg: '1' });
    const d2 = document.createElement('div'); d2.innerHTML = full;
    const nogame = await breakdownHTML({ own: 'X', nm: 'Y', r: '7', cp: '556',
                                      tm: 'VASAS', pl: '0', ng: '1' });
    return {
      finished: rows(gameRowsHTML('VASAS', 7)),
      before: rows(gameRowsHTML('PAFC', 7)),
      running: rows(gameRowsHTML('ZTE', 7)),
      over: rows(gameRowsHTML('DVSC', 7)),
      double: rows(gameRowsHTML('ETO', 7)),
      otherClub: gameRowsHTML('FTC', 7),
      emptyRound: gameRowsHTML('VASAS', 8),
      integOrder: !!d2.firstElementChild && d2.firstElementChild.classList.contains('bontasmeccs')
                   && !!d2.querySelector('.acctable'),
      integMinutes: /Játszott perc/.test(d2.querySelector('.acctable').textContent),
      nogameNone: !/bontasmeccs/.test(nogame || ''),
    };
  });

  console.log('   finished: ' + JSON.stringify(m.finished));
  check(m.finished.length === 1 && m.finished[0][0] === 'VASAS 2–2 ETO' && m.finished[0][1] === 'vége',
     'finished match: clubs + result + „vége"');
  console.log('   before: ' + JSON.stringify(m.before));
  check(m.before.length === 1 && m.before[0][0] === 'PAFC–MTK' && m.before[0][1] === 'még nem kezdődött',
     'a match not yet started has no made-up 0–0');
  check(m.running.length === 1 && m.running[0][1] === 'a meccs zajlik',
     'a match within the time limit: „a meccs zajlik" — ' + JSON.stringify(m.running));
  check(m.over.length === 1 && m.over[0][0] === 'DVSC–PAKS' && m.over[0][1] === 'vége',
     'a match started long ago without a result: „vége", but without a number');
  check(m.double.length === 2, 'a club with two matches gets two rows (' + m.double.length + ')');
  check(m.otherClub === '' && m.emptyRound === '', 'no row for another club or an empty round');
  check(m.integOrder, 'breakdownHTML puts the match row above the table');
  check(m.integMinutes, 'the Játszott perc row is in the table (77 minutes)');
  check(m.nogameNone, 'a nogame player has no match row');
  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr));
  await finish(br);
})();
