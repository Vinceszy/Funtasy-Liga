const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// A JATEKOS ELO PONTJA A TETELES BONTASBOL JON, nem az FPL osszesitojebol.
//
// MEGTORTENT (2026-08-30, GW2): az FPL a ket erteket kulon tartja, es az
// osszesito beragadt, mikozben az explain mar a lement meccs valos
// esemenyeit adta. Calvert-Lewinnel a sor 1 pontot es 9 percet mutatott,
// a bontasa viszont 90 percet, golt es bonuszt (2+4+2 = 8). Ugyanez a
// HIVATALOS FPL-APPBAN is igy latszott, tehat a forras hibaja - de a
// reszletezes a hiteles, es mi abbol tudunk szamolni.
//
// Amit rogzit:
//  - a sor pontja es perce a bontas osszege (nem a total_points/minutes);
//  - a csapat osszege es az elo meccsallas is ebbol jon;
//  - ha nincs explain (meg nem jatszott), a stats marad a forras.
const CSAPAT_MERET = 15, KEZDOK = 11;

// AZ ELO FORDULO a LEGFRISSEBB tarolt fordulo - nem egy beirt szam. A teszt
// fixen a 2.-at tette elove, mert akkor annak meg nem volt eredmenye; a
// lezarasaval a lap mar nem az elo overlaybe tette, es a teszt semmit nem
// mert. Az elofeltetelt ezert KIMONDJUK: a menetrendbol menet kozben
// kivesszuk a fordulo eredmenyet.
const HIST = require(require('path').join(__dirname, '..', 'draft_history.json'));
const GW = Object.keys(HIST.rounds).map(Number).sort((a, b) => b - a)[0] + '';
const eloFordulova = p => jsonAtir(p, '**/draft.json*', j => {
  j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
  return j;
});

(async () => {
  const br = await inditas();
  cim('PL: az élő pont a bontásból áll össze');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);
  await eloFordulova(p);

  await p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/live/.test(u)){
      const el = {};
      for (const lid of Object.keys(HIST.rounds[GW] || {}))
        for (const x of HIST.rounds[GW][lid])
          // A CSAPDA: a stats BERAGADT (1 pont, 9 perc), az explain viszont
          // a valos esemenyeket adja (90 perc + gol + bonusz = 8 pont).
          el[x.e] = {
            stats: { total_points: 1, minutes: 9, starts: 1 },
            explain: [[[
              { name: 'Minutes played', points: 2, value: 90, stat: 'minutes' },
              { name: 'Goals scored',   points: 4, value: 1,  stat: 'goals_scored' },
              { name: 'Bonus',          points: 2, value: 2,  stat: 'bonus' },
            ], 1]],
          };
      return json({ elements: el });
    }
    return route.fulfill({ status: 404, body: '' });
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof LIVEPTS !== 'undefined'
                             && Object.keys(LIVEPTS).length > 0, null, { timeout: 30000 });

  const egy = await p.evaluate(() => {
    const e = Object.keys(LIVEPTS)[0];
    return { pont: LIVEPTS[e], perc: (LIVEPERC[e] || {}).perc };
  });
  jo(egy.pont === 8, 'a játékos pontja a bontás összege (8), nem a beragadt összesítő (1) '
     + '— kapott: ' + egy.pont);
  jo(egy.perc === 90, 'a perc is a bontásból jön (90), nem a beragadt 9 — kapott: ' + egy.perc);

  // a csapat elo osszege: 11 kezdo x 8 = 88 (a pad nem szamit)
  const allas = await p.evaluate(() => [...document.querySelectorAll('.match .score')]
    .map(x => x.textContent.trim()).join(' '));
  jo(new RegExp('\\b' + (KEZDOK * 8) + '\\b').test(allas),
     'az élő meccsállás is ebből számol (' + KEZDOK * 8 + '): ' + allas);
  jo(!/\b11\b/.test(allas),
     'a beragadt összesítőből számolt állás (11) NEM jelenik meg: ' + allas);
  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr.slice(0, 2)));
  await p.close();

  cim('Nincs bontás: marad a stats (még nem játszott)');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  await apiKi(q);
  await eloFordulova(q);
  await q.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/live/.test(u)){
      const el = {};
      for (const lid of Object.keys(HIST.rounds[GW] || {}))
        for (const x of HIST.rounds[GW][lid])
          el[x.e] = { stats: { total_points: 3, minutes: 45, starts: 1 }, explain: [] };
      return json({ elements: el });
    }
    return route.fulfill({ status: 404, body: '' });
  });
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(() => typeof LIVEPTS !== 'undefined'
                             && Object.keys(LIVEPTS).length > 0, null, { timeout: 30000 });
  const ures = await q.evaluate(() => {
    const e = Object.keys(LIVEPTS)[0];
    return { pont: LIVEPTS[e], perc: (LIVEPERC[e] || {}).perc };
  });
  jo(ures.pont === 3 && ures.perc === 45,
     'üres bontásnál a stats marad a forrás (3 pont, 45 perc) — kapott: '
     + ures.pont + ' pont, ' + ures.perc + ' perc');
  jo(qerr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(qerr.slice(0, 2)));

  await vege(br);
})();
