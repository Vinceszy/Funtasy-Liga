const { BASE, jo, cim, inditas, vege, apiKi } = require('./kozos');
// A lekero (FunTasy.lekero) tartalek-utjai. MIERT LETEZIK: 2026-08-27-en a
// ket akkori proxy (corsproxy.io, allorigins) egyszerre halt meg - a
// corsproxy 401-re valtott, az allorigins tulterhelt volt -, es ezzel
// MINDKET liga minden elo lekerese (pont-bontas, elo pontok) leallt. A
// meres (naplo/proxy-meres.txt) alapjan az ut-lista kibovult; ez a teszt
// azt rogziti, hogy a lanc TENYLEG vegigesik a kovetkezo utig, es a
// csomagolt allorigins-valaszt is erti.
const BONTAS = { data: [
  { value: 90, points: 2, competition_stat_config: { name: 'Játszott perc' } },
  { value: 1,  points: 5, competition_stat_config: { name: 'Gól' } } ] };
const JSONV = b => ({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });

async function lap(br, utak){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);   // minden kulso ut zarva; az egyes esetek nyitjak, amit akarnak
  // FONTOS a sorrend: a '**fantasy-api.mlsz.hu/**' minta a PROXYS URL-ekre is
  // illeszkedik (cors.sh: .../proxy.cors.sh/https://fantasy-api.mlsz.hu/...),
  // de a kesobb regisztralt utvonal nyer - ezert a proxy-utak UTANA jonnek.
  for (const [minta, valasz] of utak) await p.route(minta, valasz);
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
    return { allapot: a.dataset.allapot, szoveg: a.innerText.replace(/\n/g, ' | ') };
  });
  return { p, err, panel };
}

(async () => {
  const br = await inditas();

  cim('corsproxy 401 + allorigins néma → a cors.sh úton megjön a bontás');
  // Pontosan a 2026-08-27-i hibakep: direkt CORS-hiba, corsproxy 401,
  // allorigins nem valaszol. A cors.sh-nak kell kiszolgalnia.
  let { p, err, panel } = await lap(br, [
    ['**fantasy-api.mlsz.hu/**', r => r.abort('failed')],          // direkt: CORS
    ['**corsproxy.io/**', r => r.fulfill({ status: 401, body: '' })],
    ['**proxy.cors.sh/**', r => r.fulfill(JSONV(BONTAS))],         // kesobb: ez nyer
  ]);
  jo(panel.allapot === 'kesz' && /Gól/.test(panel.szoveg),
     'a bontás a cors.sh úton megjött (' + panel.szoveg.slice(0, 60) + ')');
  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();

  cim('a csomagolt allorigins-válasz (get?url=) kibontása');
  // A meresben pont a /get ut ment, amikor a /raw nem: a valasz ott
  // {contents: "<json szovegkent>"} alaku - ezt kell kibontani.
  ({ p, err, panel } = await lap(br, [
    ['**fantasy-api.mlsz.hu/**', r => r.abort('failed')],
    ['**corsproxy.io/**', r => r.fulfill({ status: 401, body: '' })],
    ['**proxy.cors.sh/**', r => r.fulfill({ status: 500, body: '' })],
    ['**allorigins.win/raw**', r => r.abort('failed')],
    ['**allorigins.win/get**', r => r.fulfill(JSONV({ contents: JSON.stringify(BONTAS) }))],
  ]));
  jo(panel.allapot === 'kesz' && /Gól/.test(panel.szoveg),
     'a csomagolt válasz kibontva megjelenik (' + panel.szoveg.slice(0, 60) + ')');
  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();

  cim('ha minden út elhasal, a hibaüzenet felsorolja őket');
  ({ p, err, panel } = await lap(br, []));   // az apiKi mindent elvag
  jo(panel.allapot === 'hiba', 'a panel hibát mutat');
  for (const ut of ['sajat', 'direkt', 'cors.sh', 'allorigins', 'cors.lol', 'corsproxy'])
    jo(panel.szoveg.indexOf(ut) >= 0, 'a hibaüzenetben ott a(z) ' + ut + ' út');
  await p.close();
  await vege(br);
})();
