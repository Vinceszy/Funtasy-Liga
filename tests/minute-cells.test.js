const { BASE, check, failures, launch, finish } = require('./common');
// A player's three numbers in the live round: minutes played, match clock,
// whether he started.
//
// We show raw values and do not interpret them for the viewer ("subbed
// off") - that would need a tolerance, and a one-minute slip between the two
// endpoints would produce a false claim. From the two numbers the viewer
// sees for himself whether the player is on the pitch.
// The match clock stops at 45 and 90, so a finished match says "vége" (over).

const GW = 1;
const CLUBS = { running: 1, done: 2, before: 3 };   // team id -> state
// "minutes" is deliberately 0 everywhere: MEASURED, FPL never fills it in.
// The match clock has to be computed from the players' minutes - if someone
// put the match's own field back, this test fails.
const MATCHES = [
  { id: 11, started: true,  finished_provisional: false, finished: false,
    minutes: 0, kickoff_time: '2026-08-24T19:00:00Z', team_h: 1, team_a: 4 },
  { id: 12, started: true,  finished_provisional: true,  finished: false,
    minutes: 0, kickoff_time: '2026-08-24T16:00:00Z', team_h: 2, team_a: 5 },
  { id: 13, started: false, finished_provisional: false, finished: false,
    minutes: 0, kickoff_time: '2026-08-25T19:00:00Z', team_h: 3, team_a: 6 },
];
// player -> {minutes, starter}; the club comes from draft_players.json, so
// real player ids have to be used: we pick them at run time.
(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  const data = require(require('path').join(__dirname, '..', 'draft_players.json'));
  const teamId = Object.fromEntries(Object.entries(data.teams).map(([k, v]) => [v, +k]));
  // pick real players from each of the three clubs
  const clubName = { running: data.teams['1'], done: data.teams['2'], before: data.teams['3'] };
  const player = {};
  for (const [state, short] of Object.entries(clubName))
    player[state] = Object.entries(data.players)
      .filter(([, v]) => v.t === short).map(([k]) => +k);

  // minutes: on the running match starter / subbed off / subbed on / unused, full match on the finished one
  const P = {
    [player.running[0]]: { minutes: 70, starts: 1 },   // on the pitch, starter
    [player.running[1]]: { minutes: 62, starts: 1 },   // subbed off
    [player.running[2]]: { minutes: 12, starts: 0 },   // subbed on
    [player.running[3]]: { minutes: 0,  starts: 0 },   // did not come on
    [player.done[0]]:    { minutes: 90, starts: 1 },   // finished match
    [player.before[0]]:  { minutes: 0,  starts: 0 },   // not started yet
  };

  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MATCHES);
    if (/\/live/.test(u)) {
      const el = {};
      for (const [id, st] of Object.entries(P))
        el[id] = { stats: { total_points: 5, ...st }, explain: [] };
      return json({ elements: el });
    }
    return json({});
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof LIVE_MINUTES !== 'undefined' && Object.keys(LIVE_MINUTES).length > 0,
    null, { timeout: 20000 });

  const cells = async e => p.evaluate(([e, GW]) => {
    const d = document.createElement('div');
    d.innerHTML = minuteCellsHTML(e, GW);
    return [...d.children].map(x => x.textContent);
  }, [e, GW]);

  console.log('--- running match (70th minute) ---');
  const onPitch = await cells(player.running[0]);
  const off = await cells(player.running[1]);
  const on = await cells(player.running[2]);
  const zero = await cells(player.running[3]);
  [['on pitch, starter', onPitch], ['subbed off', off], ['subbed on', on], ['0 minutes', zero]]
    .forEach(([n, c]) => console.log('   ' + n.padEnd(18) + JSON.stringify(c)));
  check(JSON.stringify(onPitch) === JSON.stringify(["70'", "70'", 'K']), 'starter on the pitch: 70/70/K');
  check(JSON.stringify(off) === JSON.stringify(["62'", "70'", 'K']), 'subbed off: 62/70/K — the viewer sees he is not on the pitch');
  check(JSON.stringify(on) === JSON.stringify(["12'", "70'", '–']), 'subbed on: 12/70/–');
  check(JSON.stringify(zero) === JSON.stringify(["0'", "70'", '–']), 'did not come on: 0/70/–');

  console.log('\n--- finished match ---');
  const done = await cells(player.done[0]);
  console.log('   ' + JSON.stringify(done));
  check(done[1] === 'vége', 'on a finished match the clock says "vége" — 90 on its own would be ambiguous');
  check(done[0] === "90'" && done[2] === 'K', 'the player\'s minutes and the starter mark remain');

  console.log('\n--- not started yet ---');
  const before = await cells(player.before[0]);
  console.log('   ' + JSON.stringify(before));
  check(before.length === 0, 'a match that has not started has no cells');

  console.log('\n--- the match clock comes from the PLAYERS\' minutes ---');
  const clock = await p.evaluate(() => LIVE_MATCHES[11].perc);
  console.log('   clock of match 11: ' + clock + " (the fixtures' minutes field was 0)");
  check(clock === 70, 'the match clock is the minutes of the starters on the pitch, not the fixtures field');

  console.log('\n--- column names ---');
  // Three unlabelled numbers are a mystery at first, so a header row goes
  // above the minute columns. Each label has to fall EXACTLY above its own
  // column - we measure this by comparing the centres, not by eye.
  const squad = [
    { e: player.running[0], b: false, pts: 5 }, { e: player.running[1], b: false, pts: 5 },
    { e: player.running[2], b: false, pts: 5 }, { e: player.done[0], b: false, pts: 5 },
    { e: player.running[3], b: true,  pts: 0 }, { e: player.before[0], b: true, pts: 0 },
  ];
  const m = await p.evaluate(([list, GW, old]) => {
    const measure = (html, width) => {
      const d = document.createElement('div');
      d.className = 'sqwrap one'; d.style.width = width + 'px';
      d.innerHTML = html; document.body.appendChild(d);
      const mid = el => { const r = el.getBoundingClientRect(); return Math.round(r.left + r.width / 2); };
      const heads = [...d.querySelectorAll('.plrfej')];
      const first = heads[0];
      const row = d.querySelector('.plr:not(.plrfej)');
      const out = {
        headCount: heads.length,
        labels: first ? [...first.children].map(x => x.textContent.trim()).filter(Boolean) : [],
        headMid: first ? [...first.querySelectorAll('.perc,.kezd,.pts')].map(mid) : [],
        rowMid: row ? [...row.querySelectorAll('.perc,.kezd,.pts')].map(mid) : [],
        overflow: row ? row.scrollWidth > row.clientWidth + 1 : false,
      };
      d.remove();
      return out;
    };
    return {
      desktop: measure(sqcolHTML('T', list, 'Teszt', GW), 420),
      mobile: measure(sqcolHTML('T', list, 'Teszt', GW), 320),
      closed: measure(sqcolHTML('T', list, 'Teszt', old), 420),
    };
  }, [squad, GW, 99]);
  console.log('   labels: ' + JSON.stringify(m.desktop.labels));
  console.log('   header centres: ' + JSON.stringify(m.desktop.headMid) + '  row centres: ' + JSON.stringify(m.desktop.rowMid));
  check(JSON.stringify(m.desktop.labels) === JSON.stringify(['perc', 'meccs', 'kezdő', 'pont']),
     'the four columns have names: perc / meccs / kezdő / pont');
  check(m.desktop.headCount === 2, 'the header is above both the starters and the bench (' + m.desktop.headCount + ')');
  check(m.desktop.headMid.length === 4 && m.desktop.rowMid.length === 4
     && m.desktop.headMid.every((x, i) => Math.abs(x - m.desktop.rowMid[i]) <= 1),
     'every label stands above its own column');
  check(m.mobile.headMid.every((x, i) => Math.abs(x - m.mobile.rowMid[i]) <= 1),
     'it lines up at mobile width too');
  check(!m.desktop.overflow && !m.mobile.overflow, 'the row does not overflow (the name is shortened)');
  check(m.closed.headCount === 0, 'a closed round not loaded yet has no header — and no minute column either');

  console.log('\n--- closed round ---');
  // A closed round gets the minutes and the "kezdo" (starter) mark too, but
  // not the match clock: there every match is over, so everybody would show
  // "vege". The data does not come from the live fetch but from the round's
  // own /live answer - until that has arrived, there are no cells.
  const before2 = await p.evaluate(e => minuteCellsHTML(e, 99), player.running[0]);
  check(before2 === '', 'before loading there are no cells for the closed round');
  const loaded = await p.evaluate(() => loadPastMinutes(99));
  check(loaded === true, 'the minutes of the closed round can be loaded');
  const closedCells = await p.evaluate(e => {
    const d = document.createElement('div');
    d.innerHTML = minuteCellsHTML(e, 99);
    return [...d.children].map(x => x.textContent);
  }, player.running[1]);
  console.log('   closed round cells: ' + JSON.stringify(closedCells));
  check(JSON.stringify(closedCells) === JSON.stringify(["62'", 'K']),
     'a closed round has two cells: minutes and starter — no match clock');
  const closedHead = await p.evaluate(([list]) => {
    const d = document.createElement('div');
    d.innerHTML = sqcolHTML('T', list, 'Teszt', 99);
    const f = d.querySelector('.plrfej');
    return f ? [...f.children].map(x => x.textContent.trim()).filter(Boolean) : null;
  }, [squad]);
  console.log('   closed round header: ' + JSON.stringify(closedHead));
  check(JSON.stringify(closedHead) === JSON.stringify(['perc', 'kezdő', 'pont']),
     'the match column is left out of the header too');
  const closedFit = await p.evaluate(([list]) => {
    const d = document.createElement('div');
    d.className = 'sqwrap one'; d.style.width = '420px';
    d.innerHTML = sqcolHTML('T', list, 'Teszt', 99);
    document.body.appendChild(d);
    const mid = el => { const r = el.getBoundingClientRect(); return Math.round(r.left + r.width / 2); };
    const f = [...d.querySelector('.plrfej').querySelectorAll('.perc,.kezd,.pts')].map(mid);
    const row = [...d.querySelector('.plr:not(.plrfej)').querySelectorAll('.perc,.kezd,.pts')].map(mid);
    d.remove();
    return { f, row };
  }, [squad]);
  check(closedFit.f.length === 3 && closedFit.f.every((x, i) => Math.abs(x - closedFit.row[i]) <= 1),
     'the three columns line up in a closed round too');
  console.log('\n--- closed round opened (filled in afterwards) ---');
  // End to end: the modal comes up first without minute columns, and when
  // the round's /live answer arrives, it redraws itself.
  const e2e = await p.evaluate(async () => {
    LIVEGW = 99;                                  // this makes round 1 "closed"
    for (const k in PAST_MINUTES) delete PAST_MINUTES[k];
    GW_ELEMENTS.clear();
    const gw = Object.keys(HIST).map(Number).sort((a, b) => a - b)[0];
    const teams = Object.keys(HIST[gw] || {}).map(Number);
    if (teams.length < 2) return { skip: true };
    showMatch(teams[0], teams[1], gw);
    const immediately = document.querySelectorAll('#mBody .plrfej').length;
    for (let i = 0; i < 60 && !document.querySelector('#mBody .plrfej'); i++)
      await new Promise(r => setTimeout(r, 100));
    const head = document.querySelector('#mBody .plrfej');
    return { skip: false, immediately,
             labels: head ? [...head.children].map(x => x.textContent.trim()).filter(Boolean) : null,
             cells: document.querySelectorAll('#mBody .plr:not(.plrfej) .perc').length };
  });
  if (e2e.skip) console.log('   (no two teams in the first round — skipped)');
  else {
    console.log('   header at once: ' + e2e.immediately + ' · afterwards: ' + JSON.stringify(e2e.labels));
    check(e2e.immediately === 0, 'the modal comes up before the minutes — it does not keep the viewer waiting');
    check(JSON.stringify(e2e.labels) === JSON.stringify(['perc', 'kezdő', 'pont']),
       'when the data arrives it redraws itself, without the match clock');
    check(e2e.cells > 0, 'the player rows get the minute cell too (' + e2e.cells + ')');
  }

  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr));
  await finish(br);
})();
