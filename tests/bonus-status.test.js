const { BASE, check, failures, launch, finish } = require('./common');
// The three states of the bonus on the PL page.
//
// MEASURED: FPL computes the bonus during the match too, from the BPS table,
// and puts it into the explain as well (stat: "bonus"). Three states:
//   the match is running                  -> the bonus may change minute by minute
//   full time, but the DAY CLOSE is ahead -> settled, but may still change
//   after the day close                   -> fixed, UNMARKED
// The third is the ROUND close. From 2026/27 the lockdown is at 09:00 UK on
// the day AFTER the round's last match (earlier one hour after full time),
// so that Opta's review can still count - so there is NO daily close. The
// signal comes from the classic FPL event-status endpoint; read from the
// source of the Draft frontend, the meaning of the two fields:
//   points:      "" = empty, l = Live, p = Provisional, r = Confirmed
//   bonus_added: when true, "Added" in the Bonus Points column
// So final means "r" or "Added" - "p" is NOT final, it is the in-between.
// The explain has the shape [[stat list, match_id]] - so a bonus row can be
// tied to ITS OWN match, and through that to its own DAY.

const GW = 1;
// three matches in three states, on two different days
const OPEN_DAY = '2026-08-23', CLOSED_DAY = '2026-08-22';
const MATCHES = [
  { id: 11, started: true,  finished_provisional: false, finished: false,
    kickoff_time: OPEN_DAY + 'T13:00:00Z', team_h: 1, team_a: 2 },
  { id: 12, started: true,  finished_provisional: true,  finished: false,
    kickoff_time: OPEN_DAY + 'T15:30:00Z', team_h: 3, team_a: 4 },
  // a finished match on an ALREADY CLOSED day - the match's finished field is
  // still false, so if we looked at that, we would wrongly mark it provisional
  { id: 13, started: true,  finished_provisional: true,  finished: false,
    kickoff_time: CLOSED_DAY + 'T14:00:00Z', team_h: 5, team_a: 6 },
];
// The closed day is "r" (Confirmed), the other still "p" (Provisional). The
// "p" deliberately stands on the OPEN day: if anyone took it as final again,
// this test fails.
const DAYS = { status: [
  { date: CLOSED_DAY, event: GW, bonus_added: false, points: 'r' },
  { date: OPEN_DAY,   event: GW, bonus_added: false, points: 'p' },
] };
// per player: which match(es) he appears in and how much bonus he got
const PLAYERS = {
  201: [[11, 3]],            // his match is running
  202: [[12, 2]],            // full time, not official yet
  203: [[13, 1]],            // official
  204: [[13, 1], [11, 2]],   // double gameweek: one finished + one running match
};
const explain = pairs => pairs.map(([mid, bonus]) => [[
  { name: 'Minutes played', points: 2, value: 90, stat: 'minutes' },
  { name: 'Goals scored',   points: 5, value: 1,  stat: 'goals_scored' },
  { name: 'Bonus',          points: bonus, value: bonus, stat: 'bonus' },
], mid]);

let serveDays = true;   // whether the daily close data arrives (for testing the fallback branch)

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 1100, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  // NOTE: catching draft.premierleague.com is not enough - the daily close
  // comes from the CLASSIC FPL event-status endpoint (fantasy.premierleague.com).
  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MATCHES);
    if (/event-status/.test(u)) return json(serveDays ? DAYS : { status: [] });
    if (/\/live/.test(u)) {
      const el = {};
      for (const [id, pairs] of Object.entries(PLAYERS))
        el[id] = { stats: { total_points: 10, minutes: 90, bonus: pairs[0][1] }, explain: explain(pairs) };
      return json({ elements: el });
    }
    return json({});
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  // LIVEGW/LIVE_MATCHES are top-level `let`s, so they are NOT on window - they
  // have to be referred to by name (the body of waitForFunction runs in the
  // global scope).
  await p.waitForFunction(() => typeof LIVEGW !== 'undefined' && LIVEGW === 1,
    null, { timeout: 20000 });
  await p.waitForFunction(() => typeof LIVE_MATCHES !== 'undefined' && LIVE_MATCHES
    && Object.keys(LIVE_MATCHES).length === 3, null, { timeout: 20000 });
  // The daily close arrives separately, independently of the main refresh
  // (deliberately not waited for there) - here, though, it must be waited
  // for, otherwise the test would measure the fallback branch.
  await p.waitForFunction(() => typeof LIVE_DAYS !== 'undefined' && LIVE_DAYS
    && Object.keys(LIVE_DAYS).length === 2, null, { timeout: 20000 });

  const html = await p.evaluate(async (GW) => {
    const r = {};
    for (const id of [201, 202, 203, 204]) r[id] = await breakdownHTML(+id, GW);
    return r;
  }, GW);

  const bonusRows = h => {
    // the bonus rows: text of the name cell + class of the points cell
    const out = [];
    const re = /<td class="ev">Bónuszpontok([\s\S]*?)<\/td>[\s\S]*?<td class="([^"]*)">/g;
    let m; while ((m = re.exec(h))) out.push({ note: m[1].replace(/<[^>]*>/g, '').trim(), cls: m[2] });
    return out;
  };

  console.log('--- single-match cases ---');
  const running = bonusRows(html[201])[0], fullTime = bonusRows(html[202])[0], done = bonusRows(html[203])[0];
  console.log('   running match   ->', JSON.stringify(running));
  console.log('   full time       ->', JSON.stringify(fullTime));
  console.log('   official        ->', JSON.stringify(done));
  check(/b-valtozik/.test(running.cls) && /változik/.test(running.note),
    'running match: the bonus row is marked, and says that it is still changing');
  check(/b-ideiglenes/.test(fullTime.cls) && /forduló végéig/.test(fullTime.note),
    'finished match, round still open: a separate mark, and it says what it is waiting for');
  check(!/b-valtozik|b-ideiglenes/.test(done.cls) && done.note === '',
    'after the round close: no mark at all (unmarked = fixed)');
  check(/még változhat/.test(fullTime.note) && done.note === '',
    '"p" (Provisional) gets a mark, "r" (Confirmed) does not');
  check(running.cls !== fullTime.cls, 'the two marked states are not the same');

  console.log('\n--- the bonus "Added" makes it final on its own ---');
  const added = await p.evaluate(() => {
    // the open day stays "p", but the bonus is already Added
    LIVE_DAYS[Object.keys(LIVE_DAYS).find(d => !LIVE_DAYS[d].lezart)] = { lezart: true };
    return breakdownHTML(202, 1);
  });
  const addedRow = bonusRows(added)[0];
  console.log('   with Added:', JSON.stringify(addedRow));
  check(addedRow.note === '' && !/b-/.test(addedRow.cls),
    'if according to FPL the bonus is already Added, there is no mark');

  console.log('\n--- double gameweek: two matches, two states ---');
  const two = bonusRows(html[204]);
  console.log('   rows:', JSON.stringify(two));
  check(two.length === 2, 'there are two bonus rows (one per match)');
  check(two.some(x => !/b-/.test(x.cls)) && two.some(x => /b-valtozik/.test(x.cls)),
    'the finished match\'s row is unmarked, the running one\'s is marked — we do not blur them together');

  console.log('\n--- fallback: if the daily close data does not arrive ---');
  // In that case we fall back on the match's own finished field. Match 13
  // has finished=false, so it must be marked - better to flag needlessly than
  // to call something fixed that may still change.
  serveDays = false;
  const p2 = await br.newPage();
  await p2.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MATCHES);
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/live/.test(u)) {
      const el = {};
      for (const [id, pairs] of Object.entries(PLAYERS))
        el[id] = { stats: { total_points: 10, minutes: 90, bonus: pairs[0][1] }, explain: explain(pairs) };
      return json({ elements: el });
    }
    return json({});
  });
  await p2.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => typeof LIVE_MATCHES !== 'undefined' && LIVE_MATCHES
    && Object.keys(LIVE_MATCHES).length === 3, null, { timeout: 20000 });
  const fallback = bonusRows(await p2.evaluate(GW => breakdownHTML(203, GW), GW))[0];
  console.log('   without day data, finished match ->', JSON.stringify(fallback));
  check(/b-ideiglenes/.test(fallback.cls),
    'without day data a finished match stays marked (the match\'s finished field is the fallback)');

  console.log('\n--- the other rows are untouched ---');
  check(!/b-valtozik|b-ideiglenes/.test(html[201].replace(/Bónuszpontok[\s\S]*?<\/tr>/g, '')),
    'the goal and minutes rows get no mark');

  console.log('\npageerror:', perr.length ? perr : 'none');
  check(perr.length === 0, 'no JS error');
  await finish(br);
})();
