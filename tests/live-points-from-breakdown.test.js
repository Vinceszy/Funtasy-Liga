const { BASE, check, section, launch, finish, blockApis, rewriteJson } = require('./common');
// A PLAYER'S LIVE POINTS COME FROM THE ITEMISED BREAKDOWN, not from the FPL total.
//
// MEASURED (GW2): the FPL keeps the two values separately, and the total
// got stuck while the explain already gave the real events of the finished
// match. For Calvert-Lewin the row showed 1 point and 9 minutes, but his
// breakdown showed 90 minutes, a goal and bonus (2+4+2 = 8). The OFFICIAL FPL
// APP showed it the same way, so it is the source's fault - but the
// itemisation is the credible one, and we can compute from it.
//
// What it pins:
//  - the row's points and minutes are the sum of the breakdown (not
//    total_points/minutes);
//  - the team total and the live match score come from it too;
//  - if there is no explain (not played yet), stats stays the source.
const SQUAD_SIZE = 15, STARTERS = 11;

// THE LIVE ROUND is the MOST RECENT stored round - not a hard-coded number.
// The test used to pick round 2 fixed, because it had no result then; once
// it closed, the page no longer put it into the live overlay, and the test
// measured nothing. So we STATE the precondition: we remove the round's
// result from the schedule on the fly.
const HIST = require(require('path').join(__dirname, '..', 'draft_history.json'));
const GW = Object.keys(HIST.rounds).map(Number).sort((a, b) => b - a)[0] + '';
const makeLiveRound = p => rewriteJson(p, '**/draft.json*', j => {
  j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
  return j;
});

(async () => {
  const br = await launch();
  section('PL: the live points are built from the breakdown');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  await makeLiveRound(p);

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
          // THE TRAP: stats is STUCK (1 point, 9 minutes), but explain gives
          // the real events (90 minutes + goal + bonus = 8 points).
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

  const one = await p.evaluate(() => {
    const e = Object.keys(LIVEPTS)[0];
    return { points: LIVEPTS[e], minutes: (LIVE_MINUTES[e] || {}).perc };
  });
  check(one.points === 8, 'the player\'s points are the breakdown sum (8), not the stuck total (1) '
     + '— got: ' + one.points);
  check(one.minutes === 90, 'the minutes come from the breakdown too (90), not the stuck 9 — got: ' + one.minutes);

  // the team's live total: 11 starters x 8 = 88 (the bench does not count)
  const score = await p.evaluate(() => [...document.querySelectorAll('.match .score')]
    .map(x => x.textContent.trim()).join(' '));
  check(new RegExp('\\b' + (STARTERS * 8) + '\\b').test(score),
     'the live match score is computed from it too (' + STARTERS * 8 + '): ' + score);
  check(!/\b11\b/.test(score),
     'a score computed from the stuck total (11) does NOT appear: ' + score);
  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr.slice(0, 2)));
  await p.close();

  section('No breakdown: stats stays (not played yet)');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  await blockApis(q);
  await makeLiveRound(q);
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
  const empty = await q.evaluate(() => {
    const e = Object.keys(LIVEPTS)[0];
    return { points: LIVEPTS[e], minutes: (LIVE_MINUTES[e] || {}).perc };
  });
  check(empty.points === 3 && empty.minutes === 45,
     'with an empty breakdown stats stays the source (3 points, 45 minutes) — got: '
     + empty.points + ' points, ' + empty.minutes + ' minutes');
  check(qerr.length === 0, 'no JS error: ' + JSON.stringify(qerr.slice(0, 2)));

  await finish(br);
})();
