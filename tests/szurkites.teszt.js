const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// A kozos jatekosok szurkitesenek ellenorzese gepen es mobilon.

async function meccsNyit(page) {
  await page.waitForSelector('.score', { timeout: 20000 });
  // olyan meccset keresunk, ahol van kozos jatekos
  const cellak = await page.$$('.score');
  for (const c of cellak) {
    await c.click();
    await page.waitForTimeout(700);
    const van = await page.$('.szurogomb');
    if (!van) { await page.click('.mclose'); await page.waitForTimeout(200); continue; }
    // szuro bekapcsolasa, ha meg nincs
    if ((await page.$$('.szakasz')).length === 0) {
      await page.click('.szurogomb');
      await page.waitForTimeout(500);
    }
    const kozosSor = await page.$('.kozosresz .plr[data-acc]:not(.szabalysor)');
    if (kozosSor) return true;
    await page.click('.mclose'); await page.waitForTimeout(200);
  }
  return false;
}

const szin = (h) => h.evaluate(e => getComputedStyle(e).color);

(async () => {
  const b = await inditas();

  // ---- asztali ----
  let p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto(BASE + 'nb1/', { waitUntil: 'networkidle' });
  const van = await meccsNyit(p);
  jo(van, 'talaltunk kozos jatekost tartalmazo meccset');
  if (van) {
    const kozos = await p.$('.kozosresz .plr[data-acc]:not(.szabalysor) .nm');
    const elt = await p.$('.sqcol > .plr[data-acc] .nm');
    const dim = await p.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--dim').trim());
    const kSzin = await szin(kozos), eSzin = await szin(elt);
    console.log('   kozos szin:', kSzin, '| eltero szin:', eSzin, '| --dim:', dim);
    jo(kSzin !== eSzin, 'a kozos jatekos neve halvanyabb, mint az elteroe');
    // a kozos pontszam is halvany
    const kPts = await szin(await p.$('.kozosresz .plr[data-acc]:not(.szabalysor) .pts'));
    jo(kPts === kSzin, 'a kozos jatekos pontszama is halvany (' + kPts + ')');
    // az osszesito sor NEM halvany
    const oSzin = await szin(await p.$('.kozosresz .osszesito b'));
    jo(oSzin !== kSzin, 'az osszesito sor nem halvany (' + oSzin + ')');
    // a kattinthatosag megmaradt
    await p.click('.kozosresz .plr[data-acc]:not(.szabalysor)');
    await p.waitForTimeout(900);
    jo((await p.$$('.accpanel')).length > 0, 'a halvany kozos sor tovabbra is nyithato');
    await p.screenshot({ path: '/tmp/claude-0/-home-user-Funtasy-Liga/89995d2a-d2a0-5d00-83f9-d1d8d2a45519/scratchpad/kep-szurke.png', fullPage: true });
  }
  await p.close();

  // ---- mobil ----
  p = await b.newPage({ viewport: { width: 390, height: 844 } });
  await p.goto(BASE + 'nb1/', { waitUntil: 'networkidle' });
  const van2 = await meccsNyit(p);
  if (van2) {
    const mk = await p.$('.mobilkozos .plr[data-acc]:not(.szabalysor) .nm');
    jo(!!mk, 'mobilon lathato a kozos blokk');
    if (mk) {
      const lath = await p.$$eval('.mobilkozos', els => els.map(e => getComputedStyle(e).display));
      jo(lath[0] === 'block', 'mobilon a .mobilkozos lathato (' + lath[0] + ')');
      const rejt = await p.$$eval('.sqcol .kozosresz', els => els.map(e => getComputedStyle(e).display));
      jo(rejt.every(d => d === 'none'), 'mobilon az oszlopokban nincs kozos resz');
      console.log('   mobil kozos szin:', await szin(mk));
    }
    await p.screenshot({ path: '/tmp/claude-0/-home-user-Funtasy-Liga/89995d2a-d2a0-5d00-83f9-d1d8d2a45519/scratchpad/kep-szurke-mobil.png', fullPage: true });
  } else {
    jo(false, 'mobilon nem talaltunk kozos jatekost');
  }
  await p.close();
  await b.close();
  process.exit(hibak.length ? 1 : 0);
})();
