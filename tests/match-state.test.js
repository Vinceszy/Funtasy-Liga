const { BASE, check, section, failures, launch, finish, blockApis, rewriteJson } = require('./common');
// Test of the fixes made after the review: when a match counts as running,
// what may be claimed about a player without points, and what happens when
// a round closes while the page is in the background.

(async () => {
  const br = await launch();

  // ---------- isMatchRunning ----------
  console.log('--- isMatchRunning: when the match is running ---');
  const p = await br.newPage();
  await p.route('**fantasy-api.mlsz.hu/**', r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof isMatchRunning === 'function');
  const e = await p.evaluate(() => {
    const ago = m => new Date(Date.now() - m * 60000).toISOString();
    const ahead = m => new Date(Date.now() + m * 60000).toISOString();
    return {
      future:           isMatchRunning(ahead(60), undefined),
      running30:        isMatchRunning(ago(30), undefined),
      running30LyingEnd: isMatchRunning(ago(30), true),     // 'completed' at 30 minutes: NOT believable
      running110:       isMatchRunning(ago(110), undefined),
      ended110:         isMatchRunning(ago(110), true),     // at 110 minutes it is believable
      expired200:       isMatchRunning(ago(200), undefined),
      midnight:         isMatchRunning('2026-08-22T00:00:00+02:00', undefined),
      noStart:          isMatchRunning(null, undefined),
    };
  });
  check(e.future === false, 'kick-off in the future: not running yet');
  check(e.running30 === true, 'kicked off 30 minutes ago: running');
  check(e.running30LyingEnd === true, 'at 30 minutes we do NOT believe the "completed" flag (this was the bug)');
  check(e.running110 === true, 'kicked off 110 minutes ago, no end flag: still running');
  check(e.ended110 === false, 'at 110 minutes "completed" is credible: not running');
  check(e.expired200 === false, 'after 200 minutes it is not running even without an end flag');
  check(e.midnight === false, 'midnight (no kick-off set): we do not treat it as running');
  check(e.noStart === false, 'without a kick-off we claim nothing');

  // ---------- "played it" only with evidence ----------
  console.log('\n--- the "played it" claim needs evidence ---');
  const u = await p.evaluate(() => {
    const ago = m => new Date(Date.now() - m * 60000).toISOString();
    const breakdown = [{ name: 'Játszott perc', value: 90, points: 0 }];
    return {
      // live round, is_played true, match running, no breakdown yet
      duringMatch:  noPointsMessage(true, ago(30), [], false, false, true),
      // Live round, is_played true, the match kicked off 4 hours ago, empty
      // breakdown. MEASURED fact: the MLSZ gives an EMPTY breakdown for a
      // player with 0 points (Heitor got an empty list with 0 points, his
      // clubmate Ljujic got 1.75 from the same match). So an empty list does
      // NOT mean unprocessed.
      longAgoNone:  noPointsMessage(true, ago(240), [], false, false, true),
      // the same, but the breakdown has arrived -> there is evidence
      longAgoSome:  noPointsMessage(true, ago(240), breakdown, false, false, true),
      // closed round (live=false): the old behaviour stays
      closed:       noPointsMessage(true, ago(240), [], false, true, false),
      // without a kick-off time, in a live round: we claim nothing
      noTime:       noPointsMessage(true, null, [], false, false, true),
    };
  });
  Object.entries(u).forEach(([k, v]) => console.log('   ' + k.padEnd(12) + ' -> ' + JSON.stringify(v)));
  check(/A meccs zajlik/.test(u.duringMatch), 'running match + is_played=true -> "zajlik" (the reported bug)');
  check(/Lejátszotta/.test(u.longAgoNone), 'finished match + empty breakdown -> played it, without points');
  check(/Lejátszotta/.test(u.longAgoSome), 'with an arrived breakdown we do claim it (90 minutes, no points -> played it)');
  check(/Lejátszotta/.test(u.closed), 'in a closed round the old behaviour stays');
  check(/Lejátszotta/.test(u.noTime), 'without a kick-off time "played it" stays too (old record)');

  // ---------- expired placeholder date + another round's match ----------
  console.log('\n--- unscheduled kick-off whose day has already passed ---');
  const h = await p.evaluate(() => {
    const day = d => new Date(Date.now() + d * 864e5).toISOString().slice(0, 10) + 'T00:00:00+02:00';
    return {
      // This was the round-3 ETO case: the MLSZ placeholder is Aug 15, but
      // the round closed two weeks ago - promising a kick-off time is a lie.
      expired:  noPointsMessage(true, day(-20), [], false, false, false),
      // if the placeholder's day is still ahead, the date is useful information
      future:   noPointsMessage(true, day(+7), [], false, false, true),
      // "no match": present tense in a live round, past tense in a closed one
      ngLive:   noPointsMessage(true, null, null, true, false, true),
      ngClosed: noPointsMessage(true, null, null, true, false, false),
    };
  });
  Object.entries(h).forEach(([k, v]) => console.log('   ' + k.padEnd(9) + ' -> ' + JSON.stringify(v)));
  check(/elmaradt/.test(h.expired) && !/kezdés/.test(h.expired),
    'expired placeholder: promises no kick-off time, says the match was postponed');
  check(/kezdés/.test(h.future), 'with a future placeholder the date stays');
  check(/nem játszik/.test(h.ngLive), 'present tense in a live round');
  check(/nem volt meccse/.test(h.ngClosed), 'past tense in a closed round');

  console.log('\n--- the match\'s round_number reveals that it belongs to another round ---');
  const k = await p.evaluate(() => {
    const rec = (round_number, status) => squadRecord({
      competition_player: { id: 1, first_name: 'A', last_name: 'B', team: { short_name: 'ETO' },
        current_round: { is_played: true, first_played_at: '2026-08-15T00:00:00+02:00',
          games: [{ start_at: '2026-08-23T17:30:00+02:00', status: status, round_number: round_number }] } },
      summary_statistics: { weekly_points: 0 }, position: {} }, 3);
    return {
      other: rec('5F', 'completed'),        // for round 3 the club's round-5 match came back
      own: rec('3F', 'completed'),          // this really is the round-3 match
      otherRunning: rec('5F', 'scheduled'), // another round's match not yet played
    };
  });
  console.log('   other round\'s ->', JSON.stringify(k.other.nogame), 'start:', JSON.stringify(k.other.start),
              '| own ->', JSON.stringify(k.own.nogame), 'start:', JSON.stringify(k.own.start));
  check(k.other.nogame === true, 'another round\'s match -> no match in this round');
  check(k.other.start === null, 'no kick-off time is taken from another round\'s match');
  check(k.other.vege === undefined, 'nor does another round\'s match state leak through');
  check(k.otherRunning.nogame === true && k.otherRunning.vege === undefined,
    'a not-yet-played match falling back from another round does not mislead either');
  check(k.own.nogame === undefined && k.own.start === '2026-08-23T17:30:00+02:00' && k.own.vege === true,
    'but the data of the match belonging to the round is taken over');

  // ---------- PL: a closed round drops the live layer ----------
  console.log('\n--- PL: the round closes while the page is in the background ---');
  const p2 = await br.newPage();
  await p2.addInitScript(() => { window.__clock = 0; const e = Date.now; Date.now = () => e() + window.__clock; });
  // The round's result is NOT yet in the STORED data - we state this (we do
  // not build on the repository's current state: the collector may bring in
  // the result at any time, and then this scenario would fall apart by
  // itself). So the expectation after closing is not "Naprakesz" (up to
  // date): the collection is still to come, and the status line says so
  // (see closing-gap.test.js - the other branch is there too).
  const hist = require(require('path').join(__dirname,'..','draft_history.json'));
  // The MOST RECENT stored round, not the first: the home page lists the
  // latest round, so the "live" mark only shows on its matches.
  const GW = Object.keys(hist.rounds).map(Number).sort((a, b) => b - a)[0] + '';
  const elements = [...new Set(Object.values(hist.rounds[GW]).flat().map(x => x.e))];
  let finished = false;
  await rewriteJson(p2, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  });
  await p2.route('**premierleague.com/api/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    // the daily points closing (classic FPL) - the PL page fetches this too
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: finished });
    if (/\/live/.test(u)){
      const el = {}; elements.forEach(id => { el[id] = { stats: { total_points: 6, minutes: 90 }, explain: [] }; });
      return json({ elements: el });
    }
    if (/\/fixtures/.test(u)) return json([]);
    return route.fulfill({ status: 404, body: '' });
  });
  await p2.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => document.querySelector('.match.elo'), null, { timeout: 40000 });
  const liveBefore = await p2.locator('.match.elo').count();
  console.log('   matches marked "live" before closing:', liveBefore);

  finished = true;                                // meanwhile the round ends
  await p2.evaluate(() => { window.__clock = 120000; });
  await p2.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p2.waitForTimeout(1500);
  const liveAfter = await p2.locator('.match.elo').count();
  const status = (await p2.locator('#status').innerText()).trim();
  console.log('   "live" marks after closing:', liveAfter, '| status:', JSON.stringify(status.slice(0, 40)));
  check(liveBefore > 0, 'during the round there is a "live" mark');
  check(liveAfter === 0, 'after closing no match keeps the "live" mark');
  check(/lezárult/.test(status) && !/Naprakész/.test(status),
     'the status bar says the result is still missing — it does not say "naprakész"');
  await p2.close(); await p.close();
  await br.close();
  process.exit(failures.length ? 1 : 0);
})();
