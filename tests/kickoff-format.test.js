const { check, section, failures, launch, finish, BASE } = require('./common');
// KICK-OFF TIME, ONE FORMATTER FOR BOTH LEAGUES (funtasy.js formatKickoff).
//
// There used to be two separate versions of it, and the second one behaved
// wrongly at the edges: for an empty or invalid value it put "Invalid Date"
// on the page, and for null an invented date ("jan. 1. 00:00"). A raw
// timestamp is awkward, but an invented date is a lie - so what we do not
// understand we return unchanged.
//
// MIDNIGHT is a league question: the MLSZ uses it to mark an unscheduled
// kick-off, while the FPL gives no time at all in that case. If the nb1 rule
// leaked over to pl, a real midnight kick-off would show as "nincs kituzve"
// (not scheduled).
(async () => {
  const br = await launch();
  const p = await br.newPage();
  const err = []; p.on('pageerror', e => err.push(e.message));
  for (const m of ['**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/');
  await p.waitForFunction(() => window.FunTasy && FunTasy.formatKickoff, null, { timeout: 20000 });

  const f = (s, lg) => p.evaluate(([s, lg]) => FunTasy.formatKickoff(s, lg), [s, lg]);

  section('Ordinary time');
  check(await f('2026-09-27T17:30:00Z', 'nb1') === await f('2026-09-27T17:30:00Z', 'pl'),
     'the two leagues give the same for a real time');
  check(/17:30|19:30/.test(await f('2026-09-27T17:30:00Z', 'nb1')),
     'and it contains the hour too — ' + await f('2026-09-27T17:30:00Z', 'nb1'));

  section('Midnight: the league decides');
  const midNb1 = await f('2026-09-27T00:00:00Z', 'nb1');
  const midPl  = await f('2026-09-27T00:00:00Z', 'pl');
  check(/nincs kitűzve/.test(midNb1), 'on NB1 midnight = not scheduled yet — ' + midNb1);
  check(!/nincs kitűzve/.test(midPl), 'but on PL a real hour stays — ' + midPl);

  section('Edge values: we never invent a date');
  for (const [input, what] of [[null, 'null'], ['', 'empty'], ['nincs', 'not a date'],
                               ['2026-09-27', 'date without a time']]) {
    for (const lg of ['nb1', 'pl']) {
      const k = await f(input, lg);
      check(!/Invalid Date/.test(k) && !/jan\. 1\./.test(k),
         `${what} (${lg}): no invented date — ${JSON.stringify(k)}`);
    }
  }
  check(await f('nincs', 'nb1') === 'nincs', 'what we do not understand we return unchanged');
  check(await f(null, 'pl') === '', 'null becomes empty, not a date');

  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await finish(br);
})();
