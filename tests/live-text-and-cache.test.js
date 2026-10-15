const { BASE, check, section, failures, launch, finish, blockApis, rewriteJson } = require('./common');
// Test of the four reported bugs.
//  1-2) cache: every live fetch goes to a DIFFERENT URL and with no-store
//  3)   during a match the page must not say "played it without points"
//  4)   on NB1 the text must not promise live points (the league's livePoints property)

// ---- mocked MLSZ squad: one player, with adjustable flags
function squad(opts){
  return { data: [{
    id: 1, is_captain: false, type: 'starter', position: { monogram: 'CS' },
    summary_statistics: { weekly_points: 0, competition_points: 0 },
    competition_player: { id: 1249, first_name: 'Zalán Márk', last_name: 'Kerezsi',
      is_u21: false, team: { short_name: 'MTK' }, countries: [{ code: 'HUN' }],
      current_round: Object.assign({ is_played: true, market_price: 8.5,
        first_played_at: opts.start }, opts.games ? { games: opts.games } : {}) } }] };
}

(async () => {
  const br = await launch();

  // =============== 3-4) NB1 message during a match ===============
  console.log('--- NB1: what it says during a match ---');
  // The time elapsed since kick-off counts: a match cannot have ended 60
  // minutes after kick-off, so there we do not believe the 'completed' flag.
  const cases = [
    { name: 'match in progress (is_played ALREADY true)', status: 'scheduled', hours: 1, expected: /A meccs zajlik/ },
    { name: 'lying "completed" during the match',         status: 'completed', hours: 0.5, expected: /A meccs zajlik/ },
    // For a finished match the "Jatszott perc" (minutes played) row stands
    // instead of the "played it without points" message (it says more) - but
    // that is the privilege of the finished match ONLY, the two cases above
    // still expect a text message (state gate).
    { name: 'match over, without points',                 status: 'completed', hours: 2.2, expected: /Játszott perc\s*90/ },
  ];
  for (const c of cases){
    const p = await br.newPage();
    const perr = []; p.on('pageerror', x => perr.push(x.message));
    // The test's precondition is that round 5 is LIVE. We state it rather
    // than hope for it: it used to rely on the real results.json's
    // provisional list, and the test failed because the collector closed
    // round 5 in the meantime.
    await rewriteJson(p, '**/results.json*', j => Object.assign(j, { provisional: [5] }));
    // the match has been on for the given hours (kick-off in the past)
    const start = new Date(Date.now() - c.hours * 3600000).toISOString().replace('Z', '+00:00');
    await p.route('**fantasy-api.mlsz.hu/**', route => {
      const u = decodeURIComponent(route.request().url());
      const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
      // During the match the MLSZ gives no data yet; for the finished match it does
      if (/game-player-stats/.test(u)) return json({ data: c.hours > 2
        ? [{ value: 90, points: 0, competition_stat_config: { name: 'Játszott perc' } }] : [] });
      if (/user-team-players-history/.test(u))
        return json(squad({ start, games: [{ start_at: start, status: c.status }] }));
      const m = /filter\[search\]=([^&]+)/.exec(u);
      return json({ data: [{ user_team: { user: { id: 1, username: m ? m[1] : '' },
        round_statistics: [{ round_number: 5, points: 30 }] } }] });
    });
    // our own proxy (workers.dev) is not reachable from the test environment
    // - its real network attempt would only delay the first mock answer
    await p.route('**workers.dev/**', r => r.abort());
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 20000 });
    // WE STATE THE PRECONDITION: liveSquad works from USER_IDS, which the
    // refresh at load fills from the rankings answers. If the click comes
    // before that, the live squad fetch never starts, and the test measures
    // the STORED squad (it happened: the detour through our own proxy, ~300
    // ms, added just enough delay, and the test failed deterministically).
    await p.waitForFunction(() => typeof USER_IDS !== 'undefined'
      && USER_IDS['Bazsa'] && USER_IDS['Vince'], null, { timeout: 20000 });
    // open the live match for round 5 (provisional)
    await p.evaluate(() => showLiveMatch('Bazsa', 'Vince', 5));
    // The test's precondition is the MOCKED live squad. Under load it
    // happened that the live fetch did not get here, and the page drew from
    // the STORED squad - then the row carried a kick-off time weeks earlier,
    // and the test measured an entirely different state (failing with a
    // misleading message). So we do not click the first row but wait for the
    // one that came with the CURRENT kick-off - if there is none, the wait
    // fails, and that at least says the precondition was lost.
    // The row is tied to the FULL kick-off timestamp, not just its day: the
    // real round 5's matches are on the same day as the mocked kick-off, so
    // on a MATCHDAY a day match lets the stored row through too - and then
    // the test measures the message of a match kicking off weeks later.
    // (In a live run the second case failed with this.)
    await p.waitForFunction(st => [...document.querySelectorAll('.plr[data-acc]')]
      .some(x => x.dataset.st === st), start, { timeout: 20000 });
    const clicked = await p.evaluate(st => {
      const row = [...document.querySelectorAll('.plr[data-acc]')]
        .find(x => x.dataset.st === st);
      row.click();
      return { ...row.dataset };
    }, start);
    await p.waitForFunction(() => {
      const el = document.querySelector('.accpanel');
      return el && !/betöltése/i.test(el.textContent);
    }, null, { timeout: 20000 });
    const text = (await p.locator('.accpanel').innerText()).trim();
    console.log('   ' + c.name + ' -> ' + JSON.stringify(text.slice(0, 70)));
    if (!c.expected.test(text))
      // if it fails, say WHY: what the page saw of its own precondition
      console.log('   DIAG clicked row: ' + JSON.stringify(clicked)),
      console.log('   DIAG: ' + JSON.stringify(await p.evaluate(() => ({
        prov: window.PROVISIONAL, live: Object.keys(LIVE),
        live5: isLiveRound(5),
        row: { ...(document.querySelector('.plr[data-acc]') || { dataset: {} }).dataset },
      }))));
    check(c.expected.test(text), c.name);
    if (/zajlik/.test(text))
      check(!/eddig nincs pontot érő/.test(text)
         && /a pontok csak a meccs végén kerülnek be/.test(text),
        'the "zajlik" (in progress) text promises no live points, it says when they come');
    check(perr.length === 0, 'no JS error (' + c.name + ')');
    await p.close();
  }

  // =============== 1-2) cache busting ===============
  console.log('\n--- Cache: every fetch goes to a fresh URL ---');
  for (const [league, pattern] of [['nb1', '**fantasy-api.mlsz.hu/**'], ['pl', '**premierleague.com/**']]){
    const p = await br.newPage();
    const urls = [], cacheMode = new Set();
    await p.route(pattern, route => {
      const req = route.request();
      urls.push(req.url());
      const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
      const u = decodeURIComponent(req.url());
      if (league === 'pl'){
        if (/event-status/.test(u)) return json({ status: [] });
        if (/\/api\/game/.test(u)) return json({ current_event: 1, current_event_finished: false });
        if (/\/live/.test(u)) return json({ elements: {} });
        if (/\/fixtures/.test(u)) return json([]);
        return route.fulfill({ status: 404, body: '' });
      }
      const m = /filter\[search\]=([^&]+)/.exec(u);
      return json({ data: [{ user_team: { user: { id: 1, username: m ? m[1] : '' }, round_statistics: [] } }] });
    });
    // no-store is read from the Request object
    p.on('request', r => { if (r.url().match(/mlsz|premierleague|corsproxy|allorigins/)) cacheMode.add(r.resourceType()); });
    await p.addInitScript(() => {
      window.__cacheMode = [];
      const original = window.fetch;
      window.fetch = function (u, o) { window.__cacheMode.push((o || {}).cache || 'default'); return original.apply(this, arguments); };
    });
    await p.goto(BASE + league + '/', { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 150 && urls.length === 0; i++) await p.waitForTimeout(100);
    await p.waitForTimeout(1200);
    const modes = await p.evaluate(() => window.__cacheMode.filter((_, i) => i > 0));
    const allModes = await p.evaluate(() => window.__cacheMode);
    console.log('   ' + league + ': ' + urls.length + ' API requests, cache modes: ' +
      JSON.stringify([...new Set(allModes)]));
    check(urls.length > 0, league + ': there are API requests');
    if (league === 'pl'){
      // the FPL's inner URL gets a timestamp too
      check(urls.every(u => /fpl_=\d+/.test(decodeURIComponent(u))),
        'PL: every FPL request gets a timestamp');
      const unique = new Set(urls.map(u => decodeURIComponent(u)));
      check(unique.size === urls.length, 'PL: no two identical URLs (' + unique.size + '/' + urls.length + ')');
    }
    check(allModes.filter(m => m === 'no-store').length > 0, league + ': the fetches carry no-store');
    await p.close();
  }

  // proxy path: timestamp on the proxy URL (forced by breaking the direct path)
  console.log('\n--- Proxy path: the proxy URL is fresh too ---');
  {
    const p = await br.newPage();
    const proxyUrls = [];
    await p.route('**fantasy-api.mlsz.hu/**', r => r.abort());            // the direct path fails
    await p.route('**corsproxy.io/**', route => {
      proxyUrls.push(route.request().url());
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ data: [{ user_team: { user: { id: 1, username: 'x' }, round_statistics: [] } }] }) });
    });
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 150 && proxyUrls.length < 2; i++) await p.waitForTimeout(100);
    console.log('   corsproxy requests: ' + proxyUrls.length);
    check(proxyUrls.length > 0 && proxyUrls.every(u => /&_=\d+/.test(u)),
      'NB1: the corsproxy URL gets a timestamp');
    check(new Set(proxyUrls).size === proxyUrls.length,
      'NB1: no two identical proxy URLs (' + new Set(proxyUrls).size + '/' + proxyUrls.length + ')');
    await p.close();
  }

  await br.close();
  process.exit(failures.length ? 1 : 0);
})();
