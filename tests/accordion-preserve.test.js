const { BASE, check, section, launch, finish, blockApis, blockStoredBreakdowns } = require('./common');
// An OPEN points breakdown must not disappear because of a refresh arriving
// in the background.
//
// THE EXCLUDED BUG: "if I open a player's points breakdown in the match,
// after 'bontás betöltése' the accordion closes again, I have to reopen it".
// It was not the breakdown itself that closed it: the view is redrawn
// afterwards (the up-to-the-minute squad arrives, the minutes played, the
// live points), and the whole #mBody is rebuilt - the panel vanished from
// under the user. From now on every such redraw goes through
// FunTasy.accPreserve, which puts back both the row AND the panel content.
const BREAKDOWN = { data: [
  { value: 90, points: 2, competition_stat_config: { name: 'Játszott perc' } },
  { value: 1,  points: 5, competition_stat_config: { name: 'Gól' } } ] };

(async () => {
  const br = await launch();

  section('NB1: redrawing the match view');
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  // We measure the preservation that follows a FETCH: the panel goes through
  // the "bontás betöltése" state to the finished content. The stored
  // breakdown skips that (it is there at once from the repository), so here
  // it is deliberately not served - the mocked MLSZ response has to apply.
  await blockStoredBreakdowns(p);
  await p.route('**fantasy-api.mlsz.hu/**', r => /game-player-stats/.test(decodeURIComponent(r.request().url()))
    ? r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(BREAKDOWN) })
    : r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1200);
  await p.evaluate(() => showMatchRound('Bazsa', 'Csendi', 4));
  await p.waitForSelector('#mBody .plr[data-acc]', { timeout: 10000 });
  await p.$eval('#mBody .plr[data-acc]', e => e.click());
  await p.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && !/betöltése/i.test(a.textContent);
  }, null, { timeout: 10000 });
  const before = await p.evaluate(() => document.querySelector('.accpanel').innerText);
  check(/Gól/.test(before), 'the breakdown has loaded (' + before.slice(0, 40).replace(/\n/g, ' ') + ')');

  await p.evaluate(() => matchBody());          // the live refresh calls this too
  await p.waitForTimeout(300);
  const after = await p.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return { present: !!a, text: a ? a.innerText : '', open: !!document.querySelector('.plr.open') };
  });
  check(after.present, 'the breakdown is still open after the redraw');
  check(after.open, 'the row looks open too (the arrow does not turn back)');
  check(after.text === before, 'the panel CONTENT is the same too — no flash, no new request');

  section('NB1: redrawing the squad view');
  await p.evaluate(() => { const b = document.getElementById('ovClose'); if (b) b.click(); });
  await p.waitForTimeout(200);
  await p.evaluate(() => showSquad(['Katyul']));
  await p.waitForSelector('#mBody .plr[data-acc]', { timeout: 10000 });
  await p.$eval('#mBody .plr[data-acc]', e => e.click());
  await p.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && !/betöltése/i.test(a.textContent);
  }, null, { timeout: 10000 });
  const k1 = await p.evaluate(() => document.querySelector('.accpanel').innerText);
  // the same redraw that the live squad fetch triggers
  await p.evaluate(() => {
    const test = document.getElementById('mBody').innerHTML;
    FunTasy.accPreserve(() => { document.getElementById('mBody').innerHTML = test; });
  });
  await p.waitForTimeout(250);
  const k2 = await p.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return a ? a.innerText : null;
  });
  check(k2 === k1, 'the open breakdown is kept in the squad view too');

  section('A failed load is NOT preserved (the preservation itself caused an error)');
  // MEASURED: the preservation put back the ERROR MESSAGE too, and left the
  // row open - a transient network error got stuck this way, and the next
  // click closed the row instead of retrying. The breakdown came back only
  // after two clicks. Now: a failed panel is not preserved, so ONE click
  // retries.
  await p.close();
  var p2 = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err2 = []; p2.on('pageerror', e => err2.push(e.message));
  await blockApis(p2);
  await blockStoredBreakdowns(p2);   // we measure a FAILED load - a stored breakdown would not fail
  // The fetcher tries SEVERAL paths (direct + proxies), and the proxied URL
  // contains the target URL too - so "the first request" is not one URL but
  // a whole ROUND OF ATTEMPTS. We control it with a switch: first EVERY path
  // fails, flipping the switch lets the successful retry through.
  let serve = false;
  await p2.route('**fantasy-api.mlsz.hu/**', r => {
    if (!/game-player-stats/.test(decodeURIComponent(r.request().url()))) return r.abort();
    return serve
      ? r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(BREAKDOWN) })
      : r.abort();
  });
  await p2.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p2.waitForSelector('#table tr', { timeout: 20000 });
  await p2.waitForTimeout(1200);
  await p2.evaluate(() => showMatchRound('Bazsa', 'Csendi', 4));
  await p2.waitForSelector('#mBody .plr[data-acc]', { timeout: 10000 });
  await p2.$eval('#mBody .plr[data-acc]', e => e.click());
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'hiba';
  }, null, { timeout: 10000 });
  check(true, 'the first fetch failed, the panel shows an error');
  // The REASON is there too: which path failed and why. Without it neither
  // the user nor the developer can tell whether it is the network, a proxy,
  // or a change in the API.
  check(await p2.$$eval('.accpanel .accmiert', a => a.length) === 1,
     'next to the error message the REASON stands too (which path failed with what)');
  await p2.evaluate(() => matchBody());
  await p2.waitForTimeout(300);
  check((await p2.$$eval('.accpanel', a => a.length)) === 0,
     'the redraw does NOT preserve the error message (the row closes)');
  check((await p2.$$eval('.plr.open', a => a.length)) === 0,
     'the row does not stay marked as open either — otherwise the click would only close it');
  serve = true;                       // from now on the fetch may succeed
  await p2.$eval('#mBody .plr[data-acc]', e => e.click());
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'kesz';
  }, null, { timeout: 10000 });
  check(/Gól/.test(await p2.evaluate(() => document.querySelector('.accpanel').innerText)),
     'ONE click retries, and this time it succeeds');

  section('A redraw during loading restarts the fetch');
  // If the redraw catches the "Bontás betöltése..." state, the old request
  // completes onto the stale row - the panel would have stayed stuck on the
  // loading indicator forever. In that case it must be restarted.
  await p2.evaluate(() => { const s = document.querySelector('.plr.open'); if (s) s.click(); });
  await p2.waitForTimeout(200);
  // ANOTHER row: the previous player's breakdown is already in the cache, so
  // there we would never see a "loading" state.
  await p2.unroute('**fantasy-api.mlsz.hu/**');
  await p2.route('**fantasy-api.mlsz.hu/**', async r => {
    if (!/game-player-stats/.test(decodeURIComponent(r.request().url()))) return r.abort();
    await new Promise(x => setTimeout(x, 700));         // slow response
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(BREAKDOWN) });
  });
  await p2.$$eval('#mBody .plr[data-acc]', a => a[1].click());
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'tolt';
  }, null, { timeout: 5000 });
  await p2.evaluate(() => matchBody());                   // RIGHT during the load
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'kesz';
  }, null, { timeout: 10000 }).catch(() => {});
  const t = await p2.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return a ? { state: a.dataset.allapot, text: a.innerText } : null;
  });
  check(t && t.state === 'kesz' && /Gól/.test(t.text) && !/betöltése/i.test(t.text),
     'after a redraw during loading the breakdown still arrives — it does not get stuck on the indicator ('
     + JSON.stringify(t && { state: t.state, text: t.text.slice(0, 40) }) + ')');

  section('No side effect in the closed state');
  await p2.evaluate(() => { const s = document.querySelector('.plr.open'); if (s) s.click(); });
  await p2.waitForTimeout(200);
  await p2.evaluate(() => {
    const test = document.getElementById('mBody').innerHTML;
    FunTasy.accPreserve(() => { document.getElementById('mBody').innerHTML = test; });
  });
  await p2.waitForTimeout(200);
  check((await p2.$$eval('.accpanel', a => a.length)) === 0,
     'if nothing was open, the redraw opens nothing');
  check(err.length === 0 && err2.length === 0, 'no JS error'
     + (err.concat(err2).length ? ': ' + err.concat(err2).join(' | ') : ''));
  await p2.close();
  await finish(br);
})();
