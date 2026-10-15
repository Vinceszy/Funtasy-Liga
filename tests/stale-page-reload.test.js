const { BASE, check, section, launch, finish, blockApis } = require('./common');
// A STALE PAGE RELOADS ITSELF.
//
// WHY: `?v=` busts the cache of funtasy.js/css - but NOT the page's OWN
// HTML. The pages' HTML, however, holds live logic (pairing of shared
// players, building the live squad records, the match state), and an old
// HTML runs these by the OLD rule. Twice in one day the fix was out, yet the
// viewer still saw the old behaviour - and nothing signalled it.
//
// So the page asks verzio.json. Three claims:
//   V1: same version -> NO reload (otherwise every page would load twice)
//   V2: newer version -> reloads ONCE
//   V3: if it is still old after the reload, it does NOT try again - it
//       rather stays silent than reload back and forth (loop protection)
//
// SIDE EFFECT OF THE LOOP-PROTECTION RULE: `location.reload()` does not
// bypass the HTTP cache, so the page may get the same old HTML back - and
// then the protection makes it stick there. So before reloading, the
// document is fetched fresh (`cache: 'reload'`); this does not change the
// number of navigations, which is what V2 and V3 measure.
async function measure(br, v, path){
  const p = await br.newPage();
  let nav = 0;
  p.on('framenavigated', f => { if (f === p.mainFrame()) nav++; });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  await p.route('**/verzio.json*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify({ v: v }) }));
  await p.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2500);
  await p.close();
  return { nav: nav, err: err };
}

(async () => {
  const br = await launch();
  const own = +require('fs').readFileSync(
    require('path').join(__dirname, '..', 'verzio.json'), 'utf8').match(/\d+/)[0];

  section('V1: no reload with the same version');
  const a = await measure(br, own, 'nb1/');
  check(a.nav === 1, 'a single load (' + a.nav + ')');
  check(a.err.length === 0, 'no JS error' + (a.err.length ? ': ' + a.err.join(' | ') : ''));

  section('V2: with a newer version it reloads ONCE');
  const b = await measure(br, own + 20, 'nb1/');
  check(b.nav === 2, 'exactly one reload (' + b.nav + ' navigations)');
  check(b.err.length === 0, 'no JS error' + (b.err.length ? ': ' + b.err.join(' | ') : ''));

  section('V3: the PL page checks too');
  const c = await measure(br, own + 20, 'pl/');
  check(c.nav === 2, 'the PL page reloads too (' + c.nav + ' navigations)');

  section('V4: verzio.json matches the pages\' ?v= number');
  // If they drifted apart, the protection would either not catch it or cause
  // ENDLESS reloading. doc_checks.py D6/b looks at it too; here we check it
  // on the RUNNING page.
  const p = await br.newPage();
  await blockApis(p);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  const pageV = await p.evaluate(() => {
    const sc = document.querySelector('script[src*="funtasy.js?v="]');
    return sc ? +sc.getAttribute('src').split('v=')[1] : null;
  });
  check(pageV === own, 'the page\'s ?v=' + pageV + ' and verzio.json\'s v=' + own + ' match');
  await p.close();
  await finish(br);
})();
