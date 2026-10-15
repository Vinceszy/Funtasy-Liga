const { BASE, check, section, launch, finish, blockApis, rewriteJson } = require('./common');
// The itemised breakdown of a CLOSED round comes from the REPOSITORY
// (bontasok/<r>.json), not from the MLSZ. WHY: the breakdown used to come
// exclusively from a live fetch, on click - if the MLSZ or the relay did not
// answer, the drop-down showed an error. But the breakdown of a closed round
// never changes any more.
//
// What it pins:
//   - for a closed round the stored file is primary, and there is NO live fetch;
//   - with a missing file we fall back silently to the live path (old rounds);
//   - the LIVE round stays on the live path (there the breakdown still changes).
const STORED = { round: 4, bontasok: {
  // a recognisable row of the mocked stored breakdown
  '@@CP@@': [{ n: 'Játszott perc', v: 90, p: 0 }, { n: 'TÁROLT GÓL', v: 1, p: 5 }] } };
const LIVE = { data: [
  { value: 90, points: 0, competition_stat_config: { name: 'Játszott perc' } },
  { value: 1, points: 7, competition_stat_config: { name: 'ÉLŐ GÓL' } }] };

async function open(br, opts){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  const liveCalls = [];
  await p.route('**fantasy-api.mlsz.hu/**', r => {
    const u = decodeURIComponent(r.request().url());
    if (!/game-player-stats/.test(u)) return r.abort();
    liveCalls.push(u);
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(LIVE) });
  });
  if (opts.provisional)
    await rewriteJson(p, '**/results.json*', j => Object.assign(j, { provisional: opts.provisional }));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1200);
  await p.evaluate(r => showMatchRound('Bazsa', 'Csendi', r), opts.round);
  await p.waitForSelector('#mBody .plr[data-acc]', { timeout: 10000 });
  // the stored file is tailored to the row's OWN cp, so it is sure to match
  const cp = await p.$eval('#mBody .plr[data-acc]', e => e.dataset.cp);
  if (opts.stored){
    const test = JSON.parse(JSON.stringify(STORED).replace('@@CP@@', cp));
    await p.route('**/bontasok/*.json*', r => r.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify(test) }));
  } else {
    await p.route('**/bontasok/*.json*', r => r.fulfill({ status: 404, body: '' }));
  }
  await p.$eval('#mBody .plr[data-acc]', e => e.click());
  await p.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot && a.dataset.allapot !== 'tolt';
  }, null, { timeout: 15000 });
  const text = await p.evaluate(() => document.querySelector('.accpanel').innerText);
  await p.close();
  return { text, liveCalls, err };
}

(async () => {
  const br = await launch();

  section('Closed round: the stored breakdown comes, without a live fetch');
  let x = await open(br, { round: 4, stored: true });
  check(/TÁROLT GÓL/.test(x.text), 'the breakdown comes from the stored file ('
     + x.text.replace(/\n/g, ' | ').slice(0, 70) + ')');
  check(x.liveCalls.length === 0,
     'NO live MLSZ fetch for a closed round (' + x.liveCalls.length + ')');
  check(x.err.length === 0, 'no JS error' + (x.err.length ? ': ' + x.err.join(' | ') : ''));

  section('Missing file: silent fallback to the live path');
  x = await open(br, { round: 4, stored: false });
  check(/ÉLŐ GÓL/.test(x.text), 'the breakdown comes from the live fetch ('
     + x.text.replace(/\n/g, ' | ').slice(0, 70) + ')');
  check(x.liveCalls.length > 0, 'there was a live fetch (' + x.liveCalls.length + ')');
  check(x.err.length === 0, 'no JS error' + (x.err.length ? ': ' + x.err.join(' | ') : ''));

  section('Live round: the stored file is NOT used');
  // round 5 is declared live up front; there the breakdown can still change,
  // so the stored (possibly long-saved) version would mislead
  x = await open(br, { round: 5, stored: true, provisional: [5] });
  check(/ÉLŐ GÓL/.test(x.text) && !/TÁROLT/.test(x.text),
     'for a live round the live fetch wins (' + x.text.replace(/\n/g, ' | ').slice(0, 70) + ')');
  check(x.err.length === 0, 'no JS error' + (x.err.length ? ': ' + x.err.join(' | ') : ''));

  await finish(br);
})();
