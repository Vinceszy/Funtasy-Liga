const { BASE, check, section, launch, finish, rewriteJson } = require('./common');
// SMALL PAGE GUARANTEES, each one a fault that once went unnoticed.
//
//  * The magazine's rating buttons answer a click (the listener used to be
//    started only by the match page's strip, so on /nemzethy/ they did
//    nothing).
//  * A subpage finds verzio.json next to funtasy.js (a 404 resolves, so a
//    fallback chained on rejection never ran, and an outdated subpage was
//    never reloaded).
//  * On a phone the home page's league cards keep their large title (a
//    later narrow-screen .panel rule used to win).
//  * While results.json loads, the NB1 table shows no numbers at all - the
//    page used to show an embedded four-round table as if it were current.
const CUT = ['**mlsz.hu/**', '**premierleague.com/**', '**corsproxy.io/**', '**allorigins**',
             '**workers.dev/**', '**fonts.googleapis.com/**', '**fonts.gstatic.com/**'];

async function page(br, viewport) {
  const p = await br.newPage({ viewport: viewport || { width: 390, height: 844 } });
  for (const m of CUT) await p.route(m, r => r.abort());
  return p;
}

(async () => {
  const br = await launch();

  section('magazine: the rating buttons answer');
  {
    const p = await page(br);
    await p.goto(BASE + 'nemzethy/', { waitUntil: 'domcontentloaded' });
    const gomb = p.locator('.artrate button[data-pont="2"]').first();
    await gomb.waitFor({ timeout: 15000 }).catch(() => {});
    const van = await gomb.count();
    check(van > 0, 'there is a rating bar on the magazine');
    if (van) {
      await gomb.click({ force: true });
      const doboz = await p.waitForSelector('.artreasont', { timeout: 5000 }).catch(() => null);
      check(!!doboz, 'a 2 opens the reason box');
    }
    await p.close();
  }

  section('subpage: verzio.json is found next to funtasy.js');
  {
    const p = await page(br);
    const kert = [];
    p.on('response', r => { if (r.url().includes('verzio.json')) kert.push([r.url(), r.status()]); });
    await p.goto(BASE + 'nb1/', { waitUntil: 'load' });
    await p.waitForTimeout(800);
    check(kert.length > 0 && kert.every(([, st]) => st === 200),
       'every verzio.json request answered 200: ' + JSON.stringify(kert));
    await p.close();
  }

  section('home: the league card titles keep their size on a phone');
  {
    const p = await page(br);
    await p.goto(BASE, { waitUntil: 'load' });
    await p.waitForSelector('.ligakartya h2', { timeout: 10000 });
    const meret = await p.$$eval('.ligakartya h2', hs => hs.map(h => getComputedStyle(h).fontSize));
    check(meret.length && meret.every(m => m === '22px'), 'every card title is 22px: ' + JSON.stringify(meret));
    await p.close();
  }

  section('NB1: no numbers in the table before results.json arrives');
  {
    const p = await page(br);
    await rewriteJson(p, '**/results.json*', j => j);
    let engedd;
    const kapu = new Promise(r => { engedd = r; });
    await p.route('**/results.json*', async route => { await kapu; route.fallback(); });
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 10000 });
    const elotte = await p.$$eval('#table tr', trs => trs.slice(1).map(tr => tr.className + '|' +
      [...tr.cells].slice(2).map(c => c.textContent.trim()).join('')));
    check(elotte.length === 8 && elotte.every(s => s.startsWith('placeholder|') && !/\d/.test(s.split('|')[1])),
       'eight placeholder rows, no digits: ' + JSON.stringify(elotte.slice(0, 2)));
    engedd();
    await p.waitForFunction(() => document.querySelectorAll('#table tr.placeholder').length === 0,
                            null, { timeout: 15000 }).catch(() => {});
    const utana = await p.$$eval('#table tr', trs => trs.length - 1);
    check(utana === 8, 'after the results: eight real rows (' + utana + ')');
    await p.close();
  }

  await finish(br);
})();
