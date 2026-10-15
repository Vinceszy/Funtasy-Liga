const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// A LEZART fordulo teteles bontasa a REPOBOL jon (bontasok/<r>.json), nem az
// MLSZ-tol. MIERT: a bontas eddig kizarolag elo lekeresbol jott, kattintasra
// - ha az MLSZ vagy a kozvetito nem valaszolt, a lenyilo hibat irt. A lezart
// fordulo bontasa viszont mar sosem valtozik.
//
// Amit rogzit:
//   - lezart fordulonal a tarolt fajl az elsodleges, es NINCS elo lekeres;
//   - hianyzo fajlnal csendben visszaesunk az elo utra (regi fordulok);
//   - az ELO fordulo marad az elo uton (ott a bontas meg valtozik).
const TAROLT = { round: 4, bontasok: {
  // a mockolt tarolt bontas felismerheto sora
  '@@CP@@': [{ n: 'Játszott perc', v: 90, p: 0 }, { n: 'TÁROLT GÓL', v: 1, p: 5 }] } };
const ELO = { data: [
  { value: 90, points: 0, competition_stat_config: { name: 'Játszott perc' } },
  { value: 1, points: 7, competition_stat_config: { name: 'ÉLŐ GÓL' } }] };

async function nyit(br, opts){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  const elohivas = [];
  await p.route('**fantasy-api.mlsz.hu/**', r => {
    const u = decodeURIComponent(r.request().url());
    if (!/game-player-stats/.test(u)) return r.abort();
    elohivas.push(u);
    return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ELO) });
  });
  if (opts.provisional)
    await jsonAtir(p, '**/results.json*', j => Object.assign(j, { provisional: opts.provisional }));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1200);
  await p.evaluate(r => showMatchRound('Bazsa', 'Csendi', r), opts.fordulo);
  await p.waitForSelector('#mBody .plr[data-acc]', { timeout: 10000 });
  // a tarolt fajlt a sor SAJAT cp-jere szabjuk, hogy biztosan talaljon
  const cp = await p.$eval('#mBody .plr[data-acc]', e => e.dataset.cp);
  if (opts.tarolt){
    const test = JSON.parse(JSON.stringify(TAROLT).replace('@@CP@@', cp));
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
  const szoveg = await p.evaluate(() => document.querySelector('.accpanel').innerText);
  await p.close();
  return { szoveg, elohivas, err };
}

(async () => {
  const br = await inditas();

  cim('Lezárt forduló: a tárolt bontás jön, élő lekérés nélkül');
  let x = await nyit(br, { fordulo: 4, tarolt: true });
  jo(/TÁROLT GÓL/.test(x.szoveg), 'a tárolt fájlból jön a bontás ('
     + x.szoveg.replace(/\n/g, ' | ').slice(0, 70) + ')');
  jo(x.elohivas.length === 0,
     'NINCS élő MLSZ-lekérés lezárt fordulónál (' + x.elohivas.length + ')');
  jo(x.err.length === 0, 'nincs JS-hiba' + (x.err.length ? ': ' + x.err.join(' | ') : ''));

  cim('Hiányzó fájl: csendes visszaesés az élő útra');
  x = await nyit(br, { fordulo: 4, tarolt: false });
  jo(/ÉLŐ GÓL/.test(x.szoveg), 'a bontás az élő lekérésből jön ('
     + x.szoveg.replace(/\n/g, ' | ').slice(0, 70) + ')');
  jo(x.elohivas.length > 0, 'volt élő lekérés (' + x.elohivas.length + ')');
  jo(x.err.length === 0, 'nincs JS-hiba' + (x.err.length ? ': ' + x.err.join(' | ') : ''));

  cim('Élő forduló: a tárolt fájlt NEM használjuk');
  // az 5. fordulot elore kimondjuk elonek; ott a bontas meg valtozhat,
  // tehat a tarolt (esetleg reg mentett) valtozat felrevezetne
  x = await nyit(br, { fordulo: 5, tarolt: true, provisional: [5] });
  jo(/ÉLŐ GÓL/.test(x.szoveg) && !/TÁROLT/.test(x.szoveg),
     'élő fordulónál az élő lekérés nyer (' + x.szoveg.replace(/\n/g, ' | ').slice(0, 70) + ')');
  jo(x.err.length === 0, 'nincs JS-hiba' + (x.err.length ? ': ' + x.err.join(' | ') : ''));

  await vege(br);
})();
