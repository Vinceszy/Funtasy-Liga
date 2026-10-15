const { BASE, check, section, launch, finish, blockApis, rewriteJson } = require('./common');
// AFTER THE SUBMISSION DEADLINE BUT BEFORE THE FIRST WHISTLE the two squads are shown too.
//
// THE EXCLUDED BUG: during a live round, while not a single match had
// started, the match view only said "A forduló még nem kezdődött el" -
// although the squad is already fixed at that point, the collector has saved
// it, and this is exactly the most exciting question: who the opponent is
// lining up. No secret is revealed either: under the manager's name the
// "Aktuális keret" shows the same anyway.
//
// THE TEST DOES NOT RELY ON THE CALENDAR: we remove the results of an
// ALREADY CLOSED round from the schedule on the fly, which puts it exactly
// into this state (there is a saved squad, there is no result). That way it
// measures even when no such round exists in reality.
const BEFORE = 6;        // there is a keretek/<r>.json for this one
const FUTURE = 20;       // there is no saved squad for this one

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 1200, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  await rewriteJson(p, '**/results.json*', j => {
    (j.schedule[String(BEFORE)] || []).forEach(m => { m[2] = null; m[3] = null; });
    return j;
  });
  // The stored squad must take on the AFTER-DEADLINE, BEFORE-WHISTLE state
  // too: zero points, not played yet, the match in the future. Deleting the
  // result alone is not enough - the real points stand in the squad of the
  // closed round, and then we would not see the state being measured.
  const FUTURE_TIME = new Date(Date.now() + 2 * 864e5).toISOString().replace(/\.\d+Z$/, '+00:00');
  await rewriteJson(p, '**/keretek/' + BEFORE + '.json*', j => {
    for (const name in (j.squads || {}))
      (j.squads[name] || []).forEach(x => {
        x.week = 0; x.played = false; x.vege = false; x.start = FUTURE_TIME;
      });
    return j;
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1200);

  section('Fixed squad, round not started yet');
  const pair = await p.evaluate(r => {
    const m = (SCHEDULE[r] || [])[0];
    return m ? [m[0], m[1]] : null;
  }, BEFORE);
  check(!!pair, 'there is a match in round ' + BEFORE + ' (' + JSON.stringify(pair) + ')');
  await p.evaluate(([h, v, r]) => showMatchRound(h, v, r), [pair[0], pair[1], BEFORE]);
  // .catch: if the squad does NOT appear (that is the old behaviour), the
  // test must not die with an exception - the assertions tell what is missing.
  await p.waitForSelector('#mBody .sqcol', { timeout: 10000 }).catch(() => {});
  const k = await p.evaluate(() => ({
    sub: document.getElementById('mSub').textContent,
    score: (document.querySelector('#mBody .score') || {}).textContent,
    columns: document.querySelectorAll('#mBody .sqcol').length,
    players: document.querySelectorAll('#mBody .sqcol .plr').length,
    liveMarks: document.querySelectorAll('#mBody .elojel').length,
    lineupRows: document.querySelectorAll('#mBody .kezdsor').length,
    points: [...document.querySelectorAll('#mBody .sqcol .plr .pts')].map(x => x.textContent.trim()),
  }));
  check(k.columns === 2, 'BOTH squads are drawn (' + k.columns + ' columns)');
  check(k.players >= 30, 'the two squads together have at least 30 players (' + k.players + ')');
  check(/sem kezdődött el/.test(k.sub),
     'the subtitle says that not a single match has started yet: "' + k.sub + '"');
  // THE ROUND IS ALREADY LIVE AT THIS POINT: the submission deadline has
  // passed, the squad is fixed, and the score is not 0:0 either - the
  // Hungarian rule is already worth points. So the "live" mark is NOT a lie
  // but the exact state. (An earlier version hid it; that was the wrong
  // decision.) The line-up efficiency stays hidden though: it would be 0/0, a
  // number that says nothing.
  check(k.liveMarks > 0, 'the „élő" mark is there (' + k.liveMarks + ')');
  check(k.lineupRows === 0, 'there is no KEZD% row (' + k.lineupRows + ')');
  // The score shows a NUMBER, not a dash: the Hungarian rule applies already.
  check(/\d/.test(k.score || ''),
     'the header shows a number, not 0:0 or a dash — the Hungarian rule is already worth points ('
     + (k.score || '').replace(/\s+/g, ' ').trim() + ')');
  const numeric = k.points.filter(x => /\d/.test(x));
  check(k.points.length > 0 && numeric.length === 0,
     'every player has a dash instead of points (' + k.points.length + ' cells, '
     + numeric.length + ' with a number)');

  section('The home page list shows the score from the squads too');
  // THE EXCLUDED BUG: the "Következő forduló" widget showed "- : -", although
  // the squad was already fixed, and the HUNGARIAN RULE +10 is already worth
  // points. Cause: the home page list takes the score from the MLSZ ranking,
  // and that says 0 before the whistle - while 0-0 is discarded as "not even
  // started". From now on in this case we compute from the SQUAD, with the
  // same function (squadTotal) as the match panel.
  //
  // THIS MUST BE MEASURED ON AN UNTOUCHED PAGE: for the measurement above we
  // removed the results of a round, which makes the "next round" point at a
  // DIFFERENT round, and we would not see what the visitor sees.
  const p2 = await br.newPage({ viewport: { width: 900, height: 900 } });
  const err2 = []; p2.on('pageerror', e => err2.push(e.message));
  await blockApis(p2);
  await p2.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p2.waitForSelector('#mNext .match', { timeout: 20000 });
  await p2.waitForFunction(() => typeof SQUAD_FILE !== 'undefined' && SQUAD_FILE !== null,
                           null, { timeout: 20000 }).catch(() => {});
  // We wait for a STATE, not a fixed time. After the squad file arrives,
  // computing `fillFromSquads()` and redrawing the list are still to come;
  // under parallel load that takes more than 600 ms, and the test measured
  // the INTERMEDIATE state with dashes - not a product bug, but a fixed wait.
  // If the measurable state does not hold (there is no squad for the next
  // round yet), there is nothing to wait for, and the branch below skips the
  // measurement anyway.
  await p2.waitForFunction(() => {
    const r = T.rNext;
    const measurable = !!(r && SQUAD_ROUND === r && SQUAD_FILE
                       && Object.keys(SQUAD_FILE).length
                       && (SCHEDULE[r] || []).length
                       && (SCHEDULE[r] || []).every(m => m[2] == null));
    if (!measurable) return true;
    return [...document.querySelectorAll('#mNext .match .score')]
      .some(x => /\d/.test(x.textContent));
  }, null, { timeout: 20000 }).catch(() => {});
  const w = await p2.evaluate(() => {
    const r = T.rNext;
    return {
      r: r,
      // measurable only if the NEXT round already has a squad but no result
      // yet - that state is exactly the question
      measurable: !!(r && SQUAD_ROUND === r && SQUAD_FILE
                  && Object.keys(SQUAD_FILE).length
                  && (SCHEDULE[r] || []).length
                  && (SCHEDULE[r] || []).every(m => m[2] == null)),
      scores: [...document.querySelectorAll('#mNext .match .score')]
        .map(x => x.textContent.replace(/\s+/g, ' ').trim()),
      live: document.querySelectorAll('#mNext .elojel').length,
    };
  });
  if (w.measurable){
    check(w.scores.length > 0 && w.scores.every(x => /\d/.test(x)),
       'the list shows a NUMBER, not a dash (' + w.scores.join(' | ') + ')');
    check(w.live === w.scores.length,
       'every match gets the „élő" mark (' + w.live + '/' + w.scores.length + ')');
  } else {
    check(true, 'skipped: there is no saved squad for the next round yet (r=' + w.r + ')');
  }
  check(err2.length === 0, 'no JS error on the home page'
     + (err2.length ? ': ' + err2.join(' | ') : ''));
  await p2.close();

  section('The browser\'s live squad fetch knows the rescheduled match too');
  // MEASURED, IN THREE CASES: we fixed the collector, yet the page still said
  // "the club has no match". The LIVE squad fetch rebuilds the records IN THE
  // BROWSER (squadRecord), with its own logic - and that was left out of the
  // fix. The stored data was right, the fresh fetch overwrote it.
  // The input has the shape of the REAL measurement (naplo/mlsz-double-match.txt).
  const kr = await p.evaluate(() => {
    const ETO = [{ start_at: '2026-09-03T19:30:00+02:00', status: 'scheduled', round_number: '3F' },
                 { start_at: '2026-09-06T20:00:00+02:00', status: 'scheduled', round_number: '7F' }];
    const d = g => ({ competition_player: { id: 1, team: { short_name: 'ETO' },
                        countries: [], current_round: { games: g } },
                      position: {}, summary_statistics: {} });
    const out = x => ({ nogame: !!x.nogame, start: x.start, vege: !!x.vege });
    return {
      rescheduled: out(squadRecord(d(ETO), 7)),
      between: out(squadRecord(d([{ ...ETO[0], status: 'completed' }, ETO[1]]), 7)),
      both: out(squadRecord(d([{ ...ETO[0], status: 'completed' },
                              { ...ETO[1], status: 'completed' }]), 7)),
      slippedBack: out(squadRecord(d([{ start_at: '2026-09-20T18:00:00+02:00',
                                     status: 'scheduled', round_number: '9F' }]), 3)),
      empty: out(squadRecord(d([]), 7)),
    };
  });
  check(!kr.rescheduled.nogame && kr.rescheduled.start === '2026-09-03T19:30:00+02:00',
     'because of the rescheduled match there is NO „nincs meccse", and it points to that match ('
     + JSON.stringify(kr.rescheduled) + ')');
  check(kr.between.start === '2026-09-06T20:00:00+02:00' && !kr.between.vege,
     'after the rescheduled one it points to the next match, and it is not „vége" yet ('
     + JSON.stringify(kr.between) + ')');
  check(kr.both.vege, 'only with both played does it become „vége" (' + JSON.stringify(kr.both) + ')');
  check(kr.slippedBack.nogame && kr.empty.nogame,
     'a match that slipped back and an empty list are still „nincs meccse", though');

  section('A real future round keeps the message');
  // There is NO saved squad for this one - we will not make anything up.
  await p.evaluate(() => { const b = document.getElementById('ovClose'); if (b) b.click(); });
  await p.waitForTimeout(250);
  const pair2 = await p.evaluate(r => {
    const m = (SCHEDULE[r] || [])[0];
    return m ? [m[0], m[1]] : null;
  }, FUTURE);
  await p.evaluate(([h, v, r]) => showMatchRound(h, v, r), [pair2[0], pair2[1], FUTURE]);
  await p.waitForTimeout(1500);
  const j = await p.evaluate(() => ({
    columns: document.querySelectorAll('#mBody .sqcol').length,
    text: document.getElementById('mBody').innerText.trim(),
  }));
  check(j.columns === 0 && /nem kezdődött/.test(j.text),
     'a future round has no squad, only the message ("' + j.text.slice(0, 40) + '")');

  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await finish(br);
})();
