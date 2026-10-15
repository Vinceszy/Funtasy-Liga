const { BASE, check, section, launch, finish } = require('./common');
// THE NB1 LIVE FETCH DOES NOT GO ONE AFTER ANOTHER.
//
// The live score is assembled from one separate MLSZ request per manager
// (8 people = 8 requests), and this runs again every minute. Earlier all
// eight went ONE AFTER ANOTHER, each waited for: eight round trips in a row -
// for data that changes 2-4 times a day in NB1 (MLSZ gives no points
// during a match).
//
// Now the FIRST request goes alone - the fetcher learns from it which proxy
// path works -, and the remaining seven go at once. Two round trips out of
// eight.
//
// What it pins down:
//  - the data of all eight managers arrives (the speed-up lost nobody);
//  - the first request FINISHES before the second starts (path learning);
//  - the remaining seven start AT ONCE (not one after another);
//  - the total time is enough for two rounds, not eight;
//  - if someone from the parallel round fails, we retry one by one, and his
//    score still gets in.
const DELAY = 250;          // artificial response time per request (ms)
const MEMBERS = 8;

function stub(page, log, failFor){
  const failed = new Set();
  // The other paths are cut off at once, so that the proxy order does not
  // disturb the measurement: this way every request takes exactly one DELAY.
  page.route('**workers.dev/**', r => r.abort());
  page.route('**corsproxy.io/**', r => r.abort());
  page.route('**allorigins**', r => r.abort());
  page.route('**cors.sh/**', r => r.abort());
  page.route('**cors.lol/**', r => r.abort());
  return page.route('**://fantasy-api.mlsz.hu/**', async route => {
    const u = route.request().url();
    if (!u.includes('rankings'))
      return route.fulfill({ json: { data: [] } });
    const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
    const t0 = Date.now();
    await new Promise(r => setTimeout(r, DELAY));
    log.push({ uname, t0, t1: Date.now() });
    // the FIRST request of the "failFor" manager fails, the second succeeds
    if (uname === failFor && !failed.has(uname)){
      failed.add(uname);
      return route.fulfill({ status: 500, body: '' });
    }
    return route.fulfill({ json: { data: [{
      user_team: { user: { id: 5000, username: uname },
                   round_statistics: Array.from({ length: 33 },
                     (_, i) => ({ round_number: i + 1, points: 40 + i })) },
      summary_statistics: {}, rounds: [] }] } });
  });
}

const waitDone = p => p.waitForFunction(() => {
  const s = document.getElementById('status');
  return s && s.textContent && !/lekérése/.test(s.textContent);
}, null, { timeout: 40000 });

(async () => {
  const br = await launch();

  // ---- 1) order and time ----
  section('NB1: the live fetch goes in two rounds, not eight');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  const log = [];
  await stub(p, log, null);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await waitDone(p);

  check(log.length === MEMBERS,
     'the data of all ' + MEMBERS + ' managers was fetched — got: ' + log.length);

  const order = [...log].sort((a, b) => a.t0 - b.t0);
  const first = order[0], rest = order.slice(1);
  check(first.t1 <= rest[0].t0 + 5,
     'the first request finishes before the second starts (path learning) — '
     + (rest[0].t0 - first.t1) + ' ms difference');

  const spread = rest[rest.length - 1].t0 - rest[0].t0;
  check(spread < DELAY,
     'the remaining ' + rest.length + ' start at once (their starts within ' + spread
     + ' ms, one request is ' + DELAY + ' ms)');

  const total = Math.max(...log.map(x => x.t1)) - Math.min(...log.map(x => x.t0));
  check(total < 4 * DELAY,
     'the whole fetch takes two rounds (' + total + ' ms), not eight (~'
     + MEMBERS * DELAY + ' ms)');

  const score = await p.evaluate(() => {
    const r = Object.keys(LIVE).map(Number).sort((a, b) => a - b)[0];
    return { r, rows: (LIVE[r] || []).filter(Boolean).length };
  });
  check(score.rows > 0,
     'the live score was filled in too (round ' + score.r + ', ' + score.rows + ' matches)');
  check(!perr.length, 'no JS error: ' + perr.join(' | '));
  await p.close();

  // ---- 2) a failed request is retried one by one ----
  section('NB1: whoever drops out of the parallel round is requested again');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  const log2 = [];
  const FAILING = 'Hoxha98';                    // Bazsa - not the first in line
  await stub(q, log2, FAILING);
  await q.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await waitDone(q);

  const count = log2.filter(x => x.uname === FAILING).length;
  check(count === 2, 'the failed manager is requested again exactly once — '
     + count + ' requests went out for him');

  const present = await q.evaluate(() => !!(USER_IDS['Bazsa']));
  check(present, 'after the retry his data got in too');
  check(!qerr.length, 'no JS error: ' + qerr.join(' | '));
  await q.close();

  await finish(br);
})();
