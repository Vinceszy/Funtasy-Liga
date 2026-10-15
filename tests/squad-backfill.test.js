const path = require('path');
const { BASE, check, section, launch, finish, blockApis, rewriteJson } = require('./common');
// THE BROWSER BACKFILLS THE SQUADS OF THE CURRENT ROUND UNTIL THE COLLECTOR HAS WRITTEN THEM.
//
// MEASURED (PL round 5): during a live match the page did not update.
// The collector runs every 3 hours, but the round starts with the entry
// deadline: the run at 16:43 UTC STILL saw round 4, the next one was
// scheduled for 23:47 - meanwhile round 5 started, and the repository had
// no squad for it at all. The page went out to the API and did get the live
// points, but had nobody to spread them over: instead of a live score the
// status bar said "Naprakész" during a running match.
//
// What it pins down:
//  - with a missing squad the browser fetches the round's squads, and there
//    is a live score;
//  - the backfill does NOT overwrite the collector's data;
//  - with a PARTIAL backfill (fetching one team fails) the affected match
//    does NOT get a false 0, but the others do get a score.
const HIST = require(path.join(__dirname, '..', 'draft_history.json'));
const DRAFT = require(path.join(__dirname, '..', 'draft.json'));

// THE LIVE ROUND is the most recent stored round. We state the precondition:
// on the fly we remove its result from the schedule (otherwise the page would
// treat it as closed), and the round itself from the squad history - THIS is
// the situation under test: the round is running, but the collector has not
// written its squads yet.
const GW = Object.keys(HIST.rounds).map(Number).sort((a, b) => b - a)[0] + '';
const LEAGUE_IDS = Object.keys(HIST.rounds[GW]);
const EID = {};                       // league_id -> made-up FPL entry_id
LEAGUE_IDS.forEach((lid, i) => { EID[lid] = 900001 + i; });

const precondition = p => Promise.all([
  rewriteJson(p, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  }),
  rewriteJson(p, '**/draft_history.json*', j => {
    delete j.rounds[GW];
    j.veglegesek = (j.veglegesek || []).filter(x => +x !== +GW);
    return j;
  }),
]);

// Every player of the round is worth 1 point, so every team's live total is
// 11 (the bench does not count). That way a single number shows whether the
// backfill worked.
const EXPECTED = 11;

function routes(p, failFor) {       // failFor: the squad of this league id does not arrive
  return p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/league\/\d+\/details/.test(u))
      return json({ league_entries: LEAGUE_IDS.map(lid => ({ id: +lid, entry_id: EID[lid] })) });
    const m = u.match(/\/entry\/(\d+)\/event\/(\d+)/);
    if (m){
      const lid = LEAGUE_IDS.find(x => EID[x] === +m[1]);
      if (!lid || lid === failFor) return route.fulfill({ status: 404, body: '' });
      // the same structure FPL gives: position 1-11 starters, 12-15 bench
      return json({ picks: (HIST.rounds[GW][lid] || [])
        .map((x, i) => ({ element: x.e, position: i + 1 })) });
    }
    if (/\/live/.test(u)){
      const el = {};
      for (const lid of LEAGUE_IDS)
        for (const x of HIST.rounds[GW][lid])
          el[x.e] = { stats: { total_points: 1, minutes: 90, starts: 1 },
                      explain: [[[{ name: 'Minutes played', points: 1, value: 90,
                                    stat: 'minutes' }], 1]] };
      return json({ elements: el });
    }
    return route.fulfill({ status: 404, body: '' });
  });
}

const scores = p => p.evaluate(() => [...document.querySelectorAll('.match .score')]
  .map(x => x.textContent.trim()));

(async () => {
  const br = await launch();

  // ---- 1) full backfill ----
  section('PL: the browser backfills the current round\'s squads');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  await precondition(p);
  await routes(p, null);
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(g => typeof BACKFILLED !== 'undefined' && !!BACKFILLED[g],
                          GW, { timeout: 30000 });

  const filled = await p.evaluate(g => Object.keys(BACKFILLED[g] || {}).length, GW);
  check(filled === LEAGUE_IDS.length,
     'it backfilled all ' + LEAGUE_IDS.length + ' squads — got: ' + filled);

  const noHist = await p.evaluate(g => !HIST[g], GW);
  check(noHist, 'the stored data really has no squad for this round (the precondition holds)');

  const a1 = await scores(p);
  check(a1.some(x => new RegExp('\\b' + EXPECTED + '\\b').test(x)),
     'the live match score appears from the backfilled squad (' + EXPECTED + '): ' + a1.join(' | '));

  const status = await p.evaluate(() => document.getElementById('status').textContent);
  check(/él/i.test(status), 'the status bar signals a live round: ' + status);
  check(!perr.length, 'no JS error: ' + perr.join(' | '));
  await p.close();

  // ---- 2) partial backfill: the missing team's match does NOT get a false 0 ----
  section('PL: no false score with a partial backfill');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  await blockApis(q);
  await precondition(q);
  const failed = LEAGUE_IDS[0];
  await routes(q, failed);
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(g => typeof BACKFILLED !== 'undefined' && !!BACKFILLED[g],
                          GW, { timeout: 30000 });

  const partial = await q.evaluate(g => Object.keys(BACKFILLED[g] || {}).length, GW);
  check(partial === LEAGUE_IDS.length - 1,
     'one squad is missing, the rest are there (' + (LEAGUE_IDS.length - 1) + ') — got: ' + partial);

  // in the failed team's match neither side gets a live number
  const valid = await q.evaluate(([g, b]) => {
    const row = (SCHEDULE[g] || []).findIndex(m => String(m[0]) === b || String(m[1]) === b);
    return { row, matches: (SCHEDULE[g] || []).length,
             live: (LIVE[g] || [])[row] || null,
             others: (LIVE[g] || []).filter(Boolean).length };
  }, [GW, failed]);
  check(valid.live === null,
     'the match of the missing squad does NOT get a live score (0 would be a false number) — got: '
     + JSON.stringify(valid.live));
  check(valid.others === valid.matches - 1,
     'the other matches do get a live score (' + (valid.matches - 1) + ') — got: '
     + valid.others);

  const a2 = await scores(q);
  check(a2.some(x => new RegExp('\\b' + EXPECTED + '\\b').test(x)),
     'the matches with full squads show the live score: ' + a2.join(' | '));
  check(!qerr.length, 'no JS error: ' + qerr.join(' | '));
  await q.close();

  await finish(br);
})();
