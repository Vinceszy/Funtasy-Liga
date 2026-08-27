const { BASE, jo, cim, inditas, vege, apiKi } = require('./kozos');
// A NYITOTT pont-bontas nem tunhet el a hatterben beero frissitestol.
//
// BEJELENTETT HIBA: "ha megnyitom a jatekos pontreszletezeset a meccsben, a
// 'bontas betoltese' utan visszazar az accordion, ujra meg kell nyitni".
// Nem maga a bontas zarta be: a nezet utolag ujrarajzolodik (beer a percre
// friss keret, a jatszott percek, az elo pontok), es a teljes #mBody
// ujraepul - a panel a felhasznalo ala tunt el. Mostantol minden ilyen
// ujrarajzolas a FunTasy.accOrzo-n megy at, ami a sort ES a panel tartalmat
// is visszateszi.
const BONTAS = { data: [
  { value: 90, points: 2, competition_stat_config: { name: 'Játszott perc' } },
  { value: 1,  points: 5, competition_stat_config: { name: 'Gól' } } ] };

(async () => {
  const br = await inditas();

  cim('NB1: a meccs-nézet újrarajzolása');
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  await p.route('**fantasy-api.mlsz.hu/**', r => /game-player-stats/.test(decodeURIComponent(r.request().url()))
    ? r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(BONTAS) })
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
  const elotte = await p.evaluate(() => document.querySelector('.accpanel').innerText);
  jo(/Gól/.test(elotte), 'a bontás betöltődött (' + elotte.slice(0, 40).replace(/\n/g, ' ') + ')');

  await p.evaluate(() => meccsTest());          // ezt hivja az élő frissítés is
  await p.waitForTimeout(300);
  const utana = await p.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return { van: !!a, szoveg: a ? a.innerText : '', nyilt: !!document.querySelector('.plr.open') };
  });
  jo(utana.van, 'az újrarajzolás után is nyitva van a bontás');
  jo(utana.nyilt, 'a sor is nyitottnak látszik (a nyíl nem fordul vissza)');
  jo(utana.szoveg === elotte, 'a panel TARTALMA is ugyanaz — nincs villanás, nincs újabb lekérés');

  cim('NB1: a keret-nézet újrarajzolása');
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
  // ugyanaz a ujrarajzolas, mint amit az elo keret-lekeres valt ki
  await p.evaluate(() => {
    const test = document.getElementById('mBody').innerHTML;
    FunTasy.accOrzo(() => { document.getElementById('mBody').innerHTML = test; });
  });
  await p.waitForTimeout(250);
  const k2 = await p.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return a ? a.innerText : null;
  });
  jo(k2 === k1, 'a keret-nézetben is megmarad a nyitott bontás');

  cim('Zárt állapotban nincs mellékhatás');
  await p.evaluate(() => { const s = document.querySelector('.plr.open'); if (s) s.click(); });
  await p.waitForTimeout(200);
  await p.evaluate(() => {
    const test = document.getElementById('mBody').innerHTML;
    FunTasy.accOrzo(() => { document.getElementById('mBody').innerHTML = test; });
  });
  await p.waitForTimeout(200);
  jo((await p.$$eval('.accpanel', a => a.length)) === 0,
     'ha semmi nem volt nyitva, az újrarajzolás nem nyit meg semmit');
  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await vege(br);
})();
