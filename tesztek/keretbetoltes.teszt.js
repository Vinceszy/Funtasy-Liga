const { BASE, jo, cim, hibak, inditas, vege } = require('./kozos');
// A meccs megnyitasa a FORDULONKENTI keret-fajlt toltse le, ne a teljes
// elozmenyt - es ha a fordulonkenti fajl hianyzik, essen vissza rá.

(async () => {
  const br = await inditas();

  // ---------- 1. normal eset: fordulonkenti fajl ----------
  cim('Meccs megnyitasa: melyik fajlt tolti le?');
  let p = await br.newPage();
  const kert = [];
  p.on('request', r => {
    const u = r.url();
    if (/keretek\/\d+\.json/.test(u)) kert.push('keretek/' + u.match(/keretek\/(\d+)\.json/)[1]);
    if (/squad_history\.json/.test(u)) kert.push('squad_history');
  });
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr td', { timeout: 30000 });
  await p.evaluate(() => showMatchRound('Bazsa', 'Katyul', 1));
  await p.waitForSelector('.sqcol .plr', { timeout: 20000 });
  const jatekosok = await p.locator('.sqcol .plr').count();
  console.log('   lekért fájlok: ' + JSON.stringify(kert) + ' | játékos-sor: ' + jatekosok);
  jo(kert.includes('keretek/1'), 'az 1. forduló saját fájlját kéri le');
  jo(!kert.includes('squad_history'), 'a teljes előzményt NEM tölti le');
  jo(jatekosok >= 20, 'a keretek meg is jelennek (' + jatekosok + ' sor)');
  await p.close();

  // ---------- 2. visszaeses: nincs fordulonkenti fajl ----------
  cim('Ha a fordulonkenti fajl hianyzik, a teljes elozmeny a tartalek');
  p = await br.newPage();
  const kert2 = [];
  p.on('request', r => { if (/squad_history\.json/.test(r.url())) kert2.push('squad_history'); });
  await p.route('**/keretek/*.json*', r => r.fulfill({ status: 404, body: '' }));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr td', { timeout: 30000 });
  await p.evaluate(() => showMatchRound('Bazsa', 'Katyul', 1));
  await p.waitForSelector('.sqcol .plr', { timeout: 20000 });
  const jatekosok2 = await p.locator('.sqcol .plr').count();
  console.log('   tartalék lekérés: ' + JSON.stringify(kert2) + ' | játékos-sor: ' + jatekosok2);
  jo(kert2.includes('squad_history'), 'visszaesik a teljes előzményre');
  jo(jatekosok2 >= 20, 'a keretek így is megjelennek (' + jatekosok2 + ' sor)');
  await p.close();

  // ---------- 3. a ket forras ugyanazt adja ----------
  cim('A fordulonkenti fajl es a teljes elozmeny egyezik');
  const fs = require('fs'), path = require('path');
  const teljes = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'squad_history.json'), 'utf8')).rounds;
  let elteres = 0;
  for (const r of Object.keys(teljes)) {
    const f = path.join(__dirname, '..', 'keretek', r + '.json');
    if (!fs.existsSync(f)) { elteres++; console.log('   hiányzik: keretek/' + r + '.json'); continue; }
    const egy = JSON.parse(fs.readFileSync(f, 'utf8')).squads;
    if (JSON.stringify(egy) !== JSON.stringify(teljes[r])) { elteres++; console.log('   eltér: ' + r); }
  }
  jo(elteres === 0, 'mind a ' + Object.keys(teljes).length + ' forduló fájlja egyezik az előzménnyel');

  await vege(br);
})();
