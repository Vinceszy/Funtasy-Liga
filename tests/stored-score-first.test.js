const { BASE, check, section, launch, finish } = require('./common');
// THE LAST KNOWN SCORE IS ALREADY ON THE FIRST PAINT (NB1).
//
// THE EXCLUDED FAULT: "if someone has already fetched it, I want to see that
// - I must not see older data than the latest fetch". The page's first paint
// used to come from the repository, which the collector refreshes every 3
// hours: if the phone had fetched the fresh score ten minutes earlier, the
// computer still showed the old one, and one had to wait until the eight
// live fetches had run.
//
// What it pins:
//  - the stored score is drawn BEFORE the live fetches finish (this is the
//    point: there is no need to wait for them);
//  - the status bar shows the time of the FETCH, not the current time - that
//    is, it does not claim it has just checked;
//  - as soon as the live fetch arrives, it takes over;
//  - with an empty store nothing breaks, the page goes the usual way.
const STORED_POINTS = 77, LIVE_POINTS = 88;
const LIVE_DELAY = 1500;                // the live fetch is slow: leave time to measure
const MINUTES_AGO = 90;

const twoDigit = n => String(n).padStart(2, '0');

function routes(page, store, counter){
  page.route('**corsproxy.io/**', r => r.abort());
  page.route('**allorigins**', r => r.abort());
  page.route('**cors.sh/**', r => r.abort());
  page.route('**cors.lol/**', r => r.abort());
  // Our own Worker: /tarolt is served, the proxy path is cut, so that the
  // live fetch goes the direct way (below, delayed).
  page.route('**workers.dev/**', async route => {
    const u = new URL(route.request().url());
    if (u.pathname.replace(/\/+$/, '') !== '/tarolt') return route.abort();
    counter.stored++;
    return route.fulfill({ status: 200, contentType: 'application/json',
                           body: JSON.stringify(store(u)) });
  });
  return page.route('**://fantasy-api.mlsz.hu/**', async route => {
    const u = route.request().url();
    if (!u.includes('rankings')) return route.fulfill({ json: { data: [] } });
    const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
    await new Promise(r => setTimeout(r, LIVE_DELAY));
    counter.live++;
    return route.fulfill({ json: { data: [answer(uname, LIVE_POINTS)] } });
  });
}
const answer = (uname, points) => ({
  user_team: { user: { id: 5000, username: uname },
               round_statistics: Array.from({ length: 33 },
                 (_, i) => ({ round_number: i + 1, points: points })) },
  summary_statistics: {}, rounds: [],
});

(async () => {
  const br = await launch();

  // ---- 1) the stored score comes before the live fetch ----
  section('NB1: the stored score is already on the first paint');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  const cnt = { stored: 0, live: 0 };
  const when = new Date(Date.now() - MINUTES_AGO * 60000);
  await routes(p, u => {
    const out = {};
    for (const target of u.searchParams.getAll('url')){
      const uname = decodeURIComponent((target.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
      out[target] = { ido: when.toISOString(),
                      adat: JSON.stringify({ data: [answer(uname, STORED_POINTS)] }) };
    }
    return out;
  }, cnt);
  // We collect the status bar's texts ALL ALONG instead of reading them once.
  // What the test claims - that the time of the FETCH stands next to the
  // stored score - is a STATE, not a moment: the next live fetch overwrites
  // the bar itself. So a single read under load already saw the next state,
  // and the test failed misleadingly.
  await p.addInitScript(() => {
    window.__statuses = [];
    const run = () => {
      const el = document.getElementById('status');
      if (!el) return setTimeout(run, 10);
      const note = () => {
        const t = el.textContent;
        if (t && window.__statuses[window.__statuses.length - 1] !== t)
          window.__statuses.push(t);
      };
      note();
      new MutationObserver(note).observe(el, { childList: true, characterData: true,
                                               subtree: true });
    };
    run();
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });

  // We look at the LIVE layer, not the displayed text: the "88" also happens
  // to be in an archived result ("71,88"), and the text match found it
  // falsely - the test would have said green to the live fetch having arrived.
  const liveValues = () => p.evaluate(() => Object.values(LIVE).flat()
    .filter(Boolean).map(x => x[2]));
  await p.waitForFunction(v => Object.values(LIVE).flat().filter(Boolean)
    .some(x => x[2] === v), STORED_POINTS, { timeout: 20000 });
  const liveDone = cnt.live;
  check(liveDone === 0,
     'the stored score was drawn before any live fetch arrived — '
     + liveDone + ' live answers so far');
  check(cnt.stored === 1, 'the stored score came from a SINGLE round trip — ' + cnt.stored + ' requests');

  const statuses = await p.evaluate(() => window.__statuses || []);
  const expectedTime = twoDigit(when.getHours()) + ':' + twoDigit(when.getMinutes());
  const nowTime = twoDigit(new Date().getHours()) + ':' + twoDigit(new Date().getMinutes());
  check(statuses.some(t => t.includes(expectedTime)),
     'the status bar showed the time of the FETCH (' + expectedTime + '), not the current one ('
     + nowTime + '): ' + JSON.stringify(statuses));

  // ---- 2) the live fetch takes over ----
  await p.waitForFunction(v => Object.values(LIVE).flat().filter(Boolean)
    .some(x => x[2] === v), LIVE_POINTS, { timeout: 30000 });
  const final = await liveValues();
  check(final.length > 0 && final.every(x => x === LIVE_POINTS),
     'the live fetch overwrote the stored one — live values: ' + final.join(', '));
  check(!perr.length, 'no JS error: ' + perr.join(' | '));
  await p.close();

  // ---- 3) empty store: everything goes the usual way ----
  section('NB1: with an empty store nothing breaks');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  const cnt2 = { stored: 0, live: 0 };
  await routes(q, () => ({}), cnt2);
  await q.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(v => Object.values(LIVE).flat().filter(Boolean)
    .some(x => x[2] === v), LIVE_POINTS, { timeout: 30000 });
  check(true, 'the live score shows with an empty store too');
  check(!qerr.length, 'no JS error: ' + qerr.join(' | '));
  await q.close();

  await finish(br);
})();
