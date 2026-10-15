const { BASE, check, section, failures, launch, finish, blockApis, rewriteJson } = require('./common');
// Refresh when the page becomes visible again (FunTasy.onVisibleAgain).
// 1) unit test of the helper, 2) e2e on the PL page with a mocked FPL API:
//    does the home page really fetch the live points again on return.

(async () => {
  const br = await launch();

  // ---------------- 1. unit test ----------------
  let p = await br.newPage();
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => window.FunTasy && FunTasy.onVisibleAgain);

  const e = await p.evaluate(async () => {
    const wait = ms => new Promise(r => setTimeout(r, ms));
    const out = {};
    const bfPageshow = () => {
      const ps = new Event('pageshow');
      Object.defineProperty(ps, 'persisted', { value: true });
      window.dispatchEvent(ps);
    };

    // a) all three event kinds trigger (minGap=0, we wait for the run between them)
    let n = 0;
    FunTasy.onVisibleAgain(() => { n++; }, 0);
    document.dispatchEvent(new Event('visibilitychange')); await wait(40);
    window.dispatchEvent(new Event('focus'));              await wait(40);
    bfPageshow();                                          await wait(40);
    out.three = n;

    // b) a plain (non-bfcache) pageshow does not trigger - that is a fresh load
    let n2 = 0;
    FunTasy.onVisibleAgain(() => { n2++; }, 0);
    window.dispatchEvent(new Event('pageshow')); await wait(40);
    out.plainPageshow = n2;

    // c) within the window after loading it does not fetch again (we just fetched)
    let n3 = 0;
    FunTasy.onVisibleAgain(() => { n3++; }, 30000);
    document.dispatchEvent(new Event('visibilitychange')); await wait(40);
    out.freshlyLoaded = n3;

    // d) no second refresh starts while one is running
    let started = 0;
    FunTasy.onVisibleAgain(() => { started++; return wait(300); }, 0);
    document.dispatchEvent(new Event('visibilitychange')); await wait(50);
    document.dispatchEvent(new Event('visibilitychange')); await wait(400);
    out.parallel = started;

    // e) a refresh that runs into an error does not block the next one
    let n5 = 0;
    FunTasy.onVisibleAgain(() => { n5++; throw new Error('test'); }, 0);
    document.dispatchEvent(new Event('visibilitychange')); await wait(40);
    document.dispatchEvent(new Event('visibilitychange')); await wait(40);
    out.afterError = n5;
    return out;
  });

  console.log('--- unit test ---');
  check(e.three === 3, 'all three events trigger (visibilitychange, focus, bfcache pageshow): ' + e.three);
  check(e.plainPageshow === 0, 'a plain (non-bfcache) pageshow does not trigger: ' + e.plainPageshow);
  check(e.freshlyLoaded === 0, 'a freshly loaded page does not fetch again: ' + e.freshlyLoaded);
  check(e.parallel === 1, 'no second refresh starts while one is running: ' + e.parallel);
  check(e.afterError === 2, 'after a refresh that ran into an error the next one starts: ' + e.afterError);
  await p.close();

  // ---------------- 2. e2e on the PL page, with a mocked FPL API ----------------
  console.log('\n--- e2e: PL home page ---');
  p = await br.newPage();
  await p.addInitScript(() => {                 // a clock we can wind, because of the throttling
    window.__clock = 0;
    const original = Date.now;
    Date.now = () => original() + window.__clock;
  });

  // The player points change on every fetch: that shows whether the fresh ones got through.
  let liveCalls = 0, points = 5;
  const hist = require(require('path').join(__dirname,'..','draft_history.json'));
  // The MOST RECENT stored round, not the first: the home page lists the
  // latest round, so the live overlay only shows on its matches. While there
  // was only one round, the two were the same; with round 2 closed they
  // split, and the test picked the round 1 that DOES NOT SHOW.
  const GW = Object.keys(hist.rounds).map(Number).sort((a, b) => b - a)[0] + '';
  const elements = [...new Set(Object.values(hist.rounds[GW]).flat().map(x => x.e))];
  // The scenario's precondition is that the round's result is NOT YET in the
  // stored data - we state it rather than inherit it from the repository's
  // current state (the collector may write the result in at any time, and
  // then the live layer would - correctly - overwrite nothing any more).
  await rewriteJson(p, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  });
  await p.route('**premierleague.com/api/**', route => {
    const u = route.request().url();
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    // the daily points closing (classic FPL) - the PL page fetches this too
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/live/.test(u)){
      liveCalls++; points++;
      const el = {};
      elements.forEach(id => { el[id] = { stats: { total_points: points, minutes: 90 }, explain: [] }; });
      return json({ elements: el });
    }
    if (/\/fixtures/.test(u)) return json([]);
    return route.fulfill({ status: 404, body: '' });
  });
  const perr = []; p.on('pageerror', x => perr.push(x.message));

  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  // The status bar's "fetching" message also contains the word "Elo allas",
  // so we do not wait for that but for the fetch itself - and the drawing
  // that follows it.
  for (let i = 0; i < 200 && liveCalls === 0; i++) await p.waitForTimeout(100);
  await p.waitForTimeout(600);
  const atLoad = liveCalls;
  const score1 = await p.$$eval('.match .score', ns => ns.map(n => n.textContent.trim()).join(' | '));
  console.log('   /live fetches at load:', atLoad);
  console.log('   score at load:', score1.slice(0, 90));
  check(atLoad > 0, 'it fetches the live points at load');

  // returning to the page
  await p.evaluate(() => { window.__clock = 120000; });
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(1200);
  const score2 = await p.$$eval('.match .score', ns => ns.map(n => n.textContent.trim()).join(' | '));
  console.log('   /live fetches after return:', liveCalls);
  console.log('   score after return:', score2.slice(0, 90));
  check(liveCalls > atLoad, 'on return it fetches the live points again');
  check(score1 !== score2, 'the score in the home page match list really updates (does not freeze)');

  // throttling: an immediate second return must not start another one
  const prev = liveCalls;
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(800);
  check(liveCalls === prev, 'right after that it does not fetch again (throttling): ' + liveCalls);

  // there is deliberately NO timed refresh
  await p.evaluate(() => { window.__clock = 900000; });
  await p.waitForTimeout(2000);
  check(liveCalls === prev, 'a page left open does not fetch by itself: ' + liveCalls);

  // Second return: both scores are filled in by now, so this is what really
  // shows that an ALREADY DISPLAYED score can follow the change too (without
  // it the home page would stay at 39 while the score is already 38).
  await p.evaluate(() => { window.__clock = 1800000; });
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(1200);
  const score3 = await p.$$eval('.match .score', ns => ns.map(n => n.textContent.trim()).join(' | '));
  console.log('   /live fetches after the 2nd return:', liveCalls);
  console.log('   score after the 2nd return:', score3.slice(0, 90));
  check(liveCalls === prev + 1, 'the second return fetches too: ' + liveCalls);
  check(score2 !== score3 && /\d/.test(score2) && /\d/.test(score3),
    'an already displayed score follows the change too (' + score2.slice(0, 12) + ' -> ' + score3.slice(0, 12) + ')');

  console.log('   pageerror:', perr.length ? perr : 'none');
  check(perr.length === 0, 'no JS error on the PL page');
  await p.close();

  // ---------------- 3. e2e on the NB1 page ----------------
  // There the rankings endpoint is the live source; it has to be fetched again on return just the same.
  console.log('\n--- e2e: NB1 home page ---');
  p = await br.newPage();
  await p.addInitScript(() => {
    window.__clock = 0;
    const original = Date.now;
    Date.now = () => original() + window.__clock;
  });
  // One NB1 refresh fetches 8 managers one after another, so it issues many
  // requests. The NUMBER of refreshes is measured by the first manager's
  // fetch (it occurs exactly once per round), not by the raw request count.
  let rankCalls = 0, firstUname = null;
  await p.route('**fantasy-api.mlsz.hu/**', route => {
    const u = decodeURIComponent(route.request().url());
    const m = /filter\[search\]=([^&]+)/.exec(u);
    const uname = m ? m[1] : '';
    if (firstUname === null) firstUname = uname;
    if (uname === firstUname) rankCalls++;
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      data: [{ user_team: { user: { id: 1, username: uname }, round_statistics: [] } }] }) });
  });
  const perr2 = []; p.on('pageerror', x => perr2.push(x.message));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  for (let i = 0; i < 200 && rankCalls === 0; i++) await p.waitForTimeout(100);
  await p.waitForTimeout(1500);
  const nb1AtLoad = rankCalls;
  console.log('   rankings fetches at load:', nb1AtLoad);
  check(nb1AtLoad > 0, 'it fetches the rankings at load');

  await p.evaluate(() => { window.__clock = 120000; });
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(1500);
  console.log('   rankings fetches after return:', rankCalls);
  check(rankCalls > nb1AtLoad, 'on return the NB1 page fetches again too');

  const nb1Prev = rankCalls;
  await p.evaluate(() => { window.__clock = 900000; });
  await p.waitForTimeout(2000);
  check(rankCalls === nb1Prev, 'an NB1 page left open does not fetch by itself: ' + rankCalls);
  console.log('   pageerror:', perr2.length ? perr2 : 'none');
  check(perr2.length === 0, 'no JS error on the NB1 page');
  await p.close();

  await br.close();
  process.exit(failures.length ? 1 : 0);
})();
