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

  cim('Hibás betöltést NEM őrzünk meg (a megőrzés maga okozott hibát)');
  // MEGTORTENT: az orzes a HIBAUZENETET is visszatette, es a sort nyitva
  // hagyta - egy atmeneti halozati hiba igy beragadt, es a kovetkezo
  // kattintas becsukta a sort ahelyett, hogy ujraprobalta volna. A bontas
  // ket kattintasra jott csak vissza. Most: hibas panel nem orzodik meg,
  // tehat EGY kattintas ujraprobal.
  await p.close();
  var p2 = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err2 = []; p2.on('pageerror', e => err2.push(e.message));
  await apiKi(p2);
  let hivas = 0;
  await p2.route('**fantasy-api.mlsz.hu/**', r => {
    if (!/game-player-stats/.test(decodeURIComponent(r.request().url()))) return r.abort();
    hivas++;
    return hivas === 1 ? r.abort()      // az ELSO keres elhasal
      : r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(BONTAS) });
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
  jo(true, 'az első lekérés elhasalt, a panel hibát mutat');
  // Az OK is ott van: melyik ut miert nem ment. Enelkul se a felhasznalo, se
  // a fejleszto nem tudja eldonteni, halozat-e, proxy-e vagy az API valtozott.
  jo(await p2.$$eval('.accpanel .accmiert', a => a.length) === 1,
     'a hibaüzenet mellett ott áll az OK is (melyik út mivel bukott)');
  await p2.evaluate(() => meccsTest());
  await p2.waitForTimeout(300);
  jo((await p2.$$eval('.accpanel', a => a.length)) === 0,
     'az újrarajzolás NEM őrzi meg a hibaüzenetet (a sor bezár)');
  jo((await p2.$$eval('.plr.open', a => a.length)) === 0,
     'a sor sem marad nyitottnak jelölve — különben a kattintás csak becsukná');
  await p2.$eval('#mBody .plr[data-acc]', e => e.click());
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'kesz';
  }, null, { timeout: 10000 });
  jo(/Gól/.test(await p2.evaluate(() => document.querySelector('.accpanel').innerText)),
     'EGY kattintás újrapróbálja, és most sikerül');

  cim('Betöltés közbeni újrarajzolás újraindítja a lekérést');
  // Ha az ujrarajzolas a "Bontas betoltese..." allapotot kapja el, a regi
  // keres mar az elavult sorra fut ki - a panel orokre a betoltes-jelzesen
  // ragadt volna. Ilyenkor ujra kell inditani.
  await p2.evaluate(() => { const s = document.querySelector('.plr.open'); if (s) s.click(); });
  await p2.waitForTimeout(200);
  // MASIK sor: az elozo jatekos bontasa mar a gyorsitotarban van, tehat ott
  // sosem latnank "toltes" allapotot.
  await p2.unroute('**fantasy-api.mlsz.hu/**');
  await p2.route('**fantasy-api.mlsz.hu/**', async r => {
    if (!/game-player-stats/.test(decodeURIComponent(r.request().url()))) return r.abort();
    await new Promise(x => setTimeout(x, 700));         // lassu valasz
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(BONTAS) });
  });
  await p2.$$eval('#mBody .plr[data-acc]', a => a[1].click());
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'tolt';
  }, null, { timeout: 5000 });
  await p2.evaluate(() => meccsTest());                   // EPP a betoltes kozben
  await p2.waitForFunction(() => {
    const a = document.querySelector('.accpanel');
    return a && a.dataset.allapot === 'kesz';
  }, null, { timeout: 10000 }).catch(() => {});
  const t = await p2.evaluate(() => {
    const a = document.querySelector('.accpanel');
    return a ? { allapot: a.dataset.allapot, szoveg: a.innerText } : null;
  });
  jo(t && t.allapot === 'kesz' && /Gól/.test(t.szoveg) && !/betöltése/i.test(t.szoveg),
     'betöltés közbeni újrarajzolás után is megjön a bontás — nem ragad be a jelzésen ('
     + JSON.stringify(t && { allapot: t.allapot, szoveg: t.szoveg.slice(0, 40) }) + ')');

  cim('Zárt állapotban nincs mellékhatás');
  await p2.evaluate(() => { const s = document.querySelector('.plr.open'); if (s) s.click(); });
  await p2.waitForTimeout(200);
  await p2.evaluate(() => {
    const test = document.getElementById('mBody').innerHTML;
    FunTasy.accOrzo(() => { document.getElementById('mBody').innerHTML = test; });
  });
  await p2.waitForTimeout(200);
  jo((await p2.$$eval('.accpanel', a => a.length)) === 0,
     'ha semmi nem volt nyitva, az újrarajzolás nem nyit meg semmit');
  jo(err.length === 0 && err2.length === 0, 'nincs JS-hiba'
     + (err.concat(err2).length ? ': ' + err.concat(err2).join(' | ') : ''));
  await p2.close();
  await vege(br);
})();
