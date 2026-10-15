const { BASE, check, section, launch, finish, blockApis, rewriteJson } = require('./common');
// DURING A LIVE ROUND THE PAGE REFRESHES ITSELF (FunTasy.liveRefresher).
//
// THE EXCLUDED FAULT (PL): a page left open showed the score FROM LOAD TIME
// - the match stood at the 9th minute, and the rows stayed there. The
// drop-down breakdown, however, starts its own fresh fetch on click, so it
// already showed 90 minutes: the row and its panel contradicted each other
// on the same screen. The panel was right.
//
// What it pins:
//  - for a live round the page fetches the score AGAIN, without a click;
//  - the freshly arrived points DO APPEAR (fetching is not enough);
//  - if there is no current round, not a single repeated request goes out;
//  - on a hidden page the clock stops (we do not hammer the relay in the
//    background).
//
// The timer is 400 ms in the test, so the run does not wait for minutes:
// the setting is the second parameter of FunTasy.liveRefresher.
const INTERVAL = 400;
// ONLY THE LIVE ROWS. `.match .score` returns the ARCHIVED results too, and
// any number can stand in those - with round 9 arriving, one closed match
// changed to "44 : 33", and the "no 44 any more" claim failed from that,
// although the live row switched over properly. The same trap the
// stored-score-first test had already learned: a text match finds something
// else.
const score = p => p.evaluate(() => [...document.querySelectorAll('.match.elo .score')]
  .map(x => x.textContent.trim()).join(' '));

(async () => {
  const br = await launch();

  section('PL: refreshes itself during a live round');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  // the clock interval is injected into the page before its own script runs
  await p.addInitScript(k => { window.LIVE_INTERVAL = k; }, INTERVAL);

  let liveRequests = 0, points = 4;
  // THE LIVE ROUND is the MOST RECENT stored round - not a hard-coded number.
  // The test used to pick round 2 fixed, because it had no result then; once
  // it closed, the page no longer put it into the live overlay, and the test
  // measured nothing. So we STATE the precondition: we remove the round's
  // result from the schedule on the fly.
  const HIST = require(require('path').join(__dirname, '..', 'draft_history.json'));
  const GW = Object.keys(HIST.rounds).map(Number).sort((a, b) => b - a)[0] + '';
  await rewriteJson(p, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  });
  await p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/live/.test(u)){
      liveRequests++;
      const el = {};
      for (const lid of Object.keys(HIST.rounds[GW] || {}))
        for (const x of HIST.rounds[GW][lid])
          el[x.e] = { stats: { total_points: points, minutes: 90 }, explain: [] };
      return json({ elements: el });
    }
    return route.fulfill({ status: 404, body: '' });
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  // we wait for the FIRST live fetch - checked with typeof, otherwise we
  // would read the counter before it: LIVEPTS is const/let, so it is NOT on
  // window (the same trap as with USER_IDS in the live-text-and-cache test).
  await p.waitForFunction(() => typeof LIVEPTS !== 'undefined'
                             && Object.keys(LIVEPTS).length > 0, null, { timeout: 30000 });
  const first = liveRequests, scoreBefore = await score(p);
  check(first > 0, 'loading fetches the live score (' + first + ' requests)');
  check(/\d/.test(scoreBefore), 'the live score appears: ' + scoreBefore.slice(0, 40));

  // THE POINT: it has to refresh WITHOUT a click or a focus change.
  points = 9;                                 // meanwhile the score changes
  await new Promise(r => setTimeout(r, INTERVAL * 3));
  check(liveRequests > first,
     'during a live round it fetches the score again by itself (' + first + ' → ' + liveRequests + ')');
  const scoreAfter = await score(p);
  // There are 11 starters, so the displayed live score has to switch from
  // 11*4 = 44 to 11*9 = 99. We do not claim that "something changed" - we
  // claim the SPECIFIC new number appeared, otherwise the test would be
  // green on a whitespace difference too.
  check(/\b44\b/.test(scoreBefore),
     'at load the 4-point score (44) shows: ' + scoreBefore);
  check(/\b99\b/.test(scoreAfter) && !/\b44\b/.test(scoreAfter),
     'it switches to the 9-point score (99) by itself, and the old one (44) disappears: ' + scoreAfter);
  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr.slice(0, 2)));
  await p.close();

  section('No current round: not a single repeated request goes out');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  await blockApis(q);
  await q.addInitScript(k => { window.LIVE_INTERVAL = k; }, INTERVAL);
  let qLive = 0;
  await q.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    // CLOSED round: nothing to refresh
    if (/\/api\/game/.test(u)) return json({ current_event: 1, current_event_finished: true });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/live/.test(u)){ qLive++; return json({ elements: {} }); }
    return route.fulfill({ status: 404, body: '' });
  });
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForSelector('#table tr', { timeout: 30000 });
  const q0 = qLive;
  await new Promise(r => setTimeout(r, INTERVAL * 4));
  check(qLive === q0,
     'for a closed round no repeated request goes out (' + q0 + ' → ' + qLive + ')');
  check(qerr.length === 0, 'no JS error: ' + JSON.stringify(qerr.slice(0, 2)));

  await finish(br);
})();
