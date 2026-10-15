const { BASE, check, launch, finish } = require('./common');
// The player's MATCH above the points breakdown: "ARS 2-1 BRE - 70. perc".
//
// The score comes from the fixtures answer - from the same request we send
// for the live round anyway. For a closed round a separate fixtures fetch
// goes out (cached per round); breakdownHTML is asynchronous anyway, so no
// fill-in afterwards is needed.
//
// What it pins: on a running match the match clock, once finished "vége"
// (over), no score for a match that has not started, two rows in a double
// gameweek, and that the header stands ABOVE the table.
const GW = 1, OLD = 7;
const MATCH = (id, t) => ({ id, minutes: 0, ...t });
const LIVE = [
  // running match, has a score
  MATCH(11, { started: true,  finished_provisional: false, finished: false,
              kickoff_time: '2026-08-24T19:00:00Z', team_h: 1, team_a: 4,
              team_h_score: 2, team_a_score: 1 }),
  // finished
  MATCH(12, { started: true,  finished_provisional: true,  finished: false,
              kickoff_time: '2026-08-24T16:00:00Z', team_h: 2, team_a: 5,
              team_h_score: 0, team_a_score: 3 }),
  // not started yet: no score
  MATCH(13, { started: false, finished_provisional: false, finished: false,
              kickoff_time: '2026-08-25T19:00:00Z', team_h: 3, team_a: 6,
              team_h_score: null, team_a_score: null }),
  // club 1's SECOND match in the same round (double gameweek)
  MATCH(14, { started: false, finished_provisional: false, finished: false,
              kickoff_time: '2026-08-26T19:00:00Z', team_h: 7, team_a: 1,
              team_h_score: null, team_a_score: null }),
];
const CLOSED = [
  MATCH(71, { started: true, finished_provisional: true, finished: true,
              kickoff_time: '2026-08-01T14:00:00Z', team_h: 1, team_a: 2,
              team_h_score: 4, team_a_score: 0 }),
];

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  const data = require(require('path').join(__dirname, '..', 'draft_players.json'));
  const club = { one: data.teams['1'], two: data.teams['2'], three: data.teams['3'] };
  const player = {};
  for (const [k, short] of Object.entries(club))
    player[k] = Object.entries(data.players).filter(([, v]) => v.t === short).map(([x]) => +x)[0];

  let fxRequests = 0;
  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) {
      fxRequests++;
      return json(/event\/7\//.test(u) ? CLOSED : LIVE);
    }
    if (/\/live/.test(u)) {
      const el = {};
      for (const id of Object.values(player))
        el[id] = { stats: { total_points: 5, minutes: 70, starts: 1 },
                   explain: [[[{ stat: 'minutes', value: 70, points: 2 }], 11]] };
      return json({ elements: el });
    }
    return json({});
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof LIVE_MATCHES !== 'undefined' && LIVE_MATCHES
    && Object.keys(LIVE_MATCHES).length > 0, null, { timeout: 20000 });

  // the header rows come back as text: [left, right] pairs
  const headers = (e, gw) => p.evaluate(async ([e, gw]) => {
    const h = await breakdownHTML(e, gw);
    const d = document.createElement('div');
    d.innerHTML = h || '';
    const rows = [...d.querySelectorAll('.bontasmeccs')]
      .map(x => [x.children[0].textContent.trim().replace(/\s+/g, ' '),
                 x.children[1].textContent.trim()]);
    // does the header stand ABOVE the table?
    const first = d.firstElementChild;
    const table = d.querySelector('table, .acctable, .loading');
    return { rows, onTop: !!first && first.classList.contains('bontasmeccs'),
             hasTable: !!table };
  }, [e, gw]);

  console.log('--- live round ---');
  const running = await headers(player.one, GW);
  console.log('   ' + JSON.stringify(running.rows));
  check(running.rows.length === 2, 'in a double gameweek both matches get a row (' + running.rows.length + ')');
  check(running.rows[0][0] === club.one + ' 2–1 ' + data.teams['4'],
     'the running match\'s score in home–away order: ' + running.rows[0][0]);
  check(running.rows[0][1] === '70. perc', 'the match clock from the players\' minutes: ' + running.rows[0][1]);
  check(running.rows[1][0] === data.teams['7'] + '–' + club.one && running.rows[1][1] === 'még nem kezdődött',
     'a match that has not started has no score, only the two clubs');
  check(running.onTop, 'the match header stands ABOVE the points breakdown');
  check(running.hasTable, 'the points breakdown itself is there below it');

  const finished = await headers(player.two, GW);
  console.log('   ' + JSON.stringify(finished.rows));
  check(finished.rows.length === 1 && finished.rows[0][1] === 'vége',
     'a finished match shows "vége" in place of the clock');
  check(finished.rows[0][0] === club.two + ' 0–3 ' + data.teams['5'],
     'the finished match\'s final score is there too: ' + finished.rows[0][0]);

  const before = await headers(player.three, GW);
  console.log('   ' + JSON.stringify(before.rows));
  check(before.rows.length === 1 && !/\d–\d/.test(before.rows[0][0]),
     'for a match that has not started we do not show 0–0');

  console.log('\n--- closed round ---');
  const countBefore = fxRequests;
  const old = await headers(player.one, OLD);
  console.log('   ' + JSON.stringify(old.rows));
  check(old.rows.length === 1 && old.rows[0][0] === club.one + ' 4–0 ' + club.two,
     'in a closed round the final score comes from that round\'s own fixtures');
  check(old.rows[0][1] === 'vége', '"vége" in a closed round');
  const firstFetch = fxRequests - countBefore;
  await headers(player.two, OLD);
  const second = fxRequests - countBefore - firstFetch;
  console.log('   fixtures requests: ' + firstFetch + ' on the first opening, ' + second + ' on the second');
  check(firstFetch === 1 && second === 0,
     'the closed round\'s match list is downloaded ONCE per round');

  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr));
  await finish(br);
})();
