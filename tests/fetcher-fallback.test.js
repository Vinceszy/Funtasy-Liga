const { BASE, check, section, launch, finish, blockApis, blockStoredBreakdowns } = require('./common');
// The fallback paths of the fetcher (FunTasy.makeFetcher). WHY IT EXISTS: once
// the two proxies of the time (corsproxy.io, allorigins) died at the same
// time - corsproxy switched to 401, allorigins was overloaded -, and with
// that EVERY live fetch of BOTH leagues (points breakdown, live points)
// stopped. Based on the measurement (naplo/proxy-probe.txt) the path list
// was extended; this test pins down that the chain REALLY falls through to
// the next path, and that it understands the wrapped allorigins response too.
const BREAKDOWN = { data: [
  { value: 90, points: 2, competition_stat_config: { name: 'Játszott perc' } },
  { value: 1,  points: 5, competition_stat_config: { name: 'Gól' } } ] };
const JSONV = b => ({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });

async function openPage(br, paths){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);   // every outside path closed; each case opens what it wants
  // This test measures THE FETCHER'S PATH CHAIN (which proxy comes into play,
  // what the error message says). The breakdown of a closed round, however,
  // now comes from the repository, so it is there without a fetch - we would
  // never even reach the chain. So the stored breakdown is deliberately not
  // served here.
  await blockStoredBreakdowns(p);
  // The ORDER matters: the '**fantasy-api.mlsz.hu/**' pattern also matches
  // the PROXIED URLs (cors.sh: .../proxy.cors.sh/https://fantasy-api.mlsz.hu/...),
  // but the route registered later wins - so the proxy paths come AFTER it.
  for (const [pattern, response] of paths) await p.route(pattern, response);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1200);
  await p.evaluate(() => showMatchRound('Bazsa', 'Csendi', 4));
  await p.waitForSelector('#mBody .plr[data-acc]', { timeout: 10000 });
  await p.$eval('#mBody .plr[data-acc]', e => e.click());
  await p.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot && a.dataset.allapot !== 'tolt';
  }, null, { timeout: 25000 });
  const panel = await p.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return { state: a.dataset.allapot, text: a.innerText.replace(/\n/g, ' | ') };
  });
  return { p, err, panel };
}

(async () => {
  const br = await launch();

  section('corsproxy 401 + allorigins silent → the breakdown arrives via cors.sh');
  // Exactly the failure pattern that happened: a direct CORS error,
  // corsproxy 401, allorigins does not answer. cors.sh has to serve it.
  let { p, err, panel } = await openPage(br, [
    ['**fantasy-api.mlsz.hu/**', r => r.abort('failed')],          // direct: CORS
    ['**corsproxy.io/**', r => r.fulfill({ status: 401, body: '' })],
    ['**proxy.cors.sh/**', r => r.fulfill(JSONV(BREAKDOWN))],      // later: this one wins
  ]);
  check(panel.state === 'kesz' && /Gól/.test(panel.text),
     'the breakdown arrived via cors.sh (' + panel.text.slice(0, 60) + ')');
  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();

  section('unwrapping the wrapped allorigins response (get?url=)');
  // In the measurement exactly the /get path worked when /raw did not: there
  // the response has the shape {contents: "<json as text>"} - that has to be
  // unwrapped.
  ({ p, err, panel } = await openPage(br, [
    ['**fantasy-api.mlsz.hu/**', r => r.abort('failed')],
    ['**corsproxy.io/**', r => r.fulfill({ status: 401, body: '' })],
    ['**proxy.cors.sh/**', r => r.fulfill({ status: 500, body: '' })],
    ['**allorigins.win/raw**', r => r.abort('failed')],
    ['**allorigins.win/get**', r => r.fulfill(JSONV({ contents: JSON.stringify(BREAKDOWN) }))],
  ]));
  check(panel.state === 'kesz' && /Gól/.test(panel.text),
     'the wrapped response is unwrapped and shown (' + panel.text.slice(0, 60) + ')');
  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();

  section('if every path fails, the error message lists them');
  ({ p, err, panel } = await openPage(br, []));   // blockApis cuts everything
  check(panel.state === 'hiba', 'the panel shows an error');
  for (const path of ['sajat', 'direkt', 'cors.sh', 'allorigins', 'cors.lol', 'corsproxy'])
    check(panel.text.indexOf(path) >= 0, 'the error message names the ' + path + ' path');
  await p.close();
  await finish(br);
})();
