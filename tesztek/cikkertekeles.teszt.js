const { BASE, jo, cim, inditas, vege } = require('./kozos');
// AZ IRAS ERTEKELESE a cikksav aljan.
//
// A funkcio celja nem a pontszam, hanem az INDOK: abbol lesz jobb a
// kovetkezo szoveg. Ezert a ket also fokozat indokot ker, a ket felso pedig
// egyetlen koppintassal atmegy - aki elegedett, ne dolgozzon erte.
//
// Amit rogzit:
//  - a sav csak a KINYITOTT cikkben van ott (amit nem olvastal, ne ertekeld);
//  - harmas-negyes: egy koppintas, semmi kerdes, es a kuldott adat helyes;
//  - egyes-kettes: HELYBEN nyilik az indok-panel (a cikk lathato marad),
//    gyorsvalasztokkal es szovegdobozzal;
//  - a gyorsvalaszto egy koppintas, es a kuldott adatban benne van;
//  - a kiut ("indokolni nem fogok") elmegy, de indok NELKUL - nem hamisit;
//  - a kattintas nem csukja be a cikket;
//  - egy eszkoz egy cikket egyszer ertekel, de at tudja ertekelni;
//  - sikertelen kuldesnel nem vesz el, amit beirtak.
const R = 7, H = 'Bence', V = 'Csendi';
const KULCS = 'nb1|7|summary|' + H + '|' + V;

const nyit = async (p, kertek) => {
  await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [H, V, R]);
  await p.waitForSelector('#mBody .artstrip');
  await p.evaluate(() => { document.querySelector('#mBody .artstrip').open = true; });
  await p.waitForSelector('#mBody .artrate');
};

(async () => {
  const br = await inditas();
  const hibak = [];
  const p = await br.newPage({ viewport: { width: 1000, height: 1000 } });
  p.on('pageerror', e => hibak.push(e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
    await p.route(m, r => r.abort());

  // A Workerhez nem megyunk ki: elkapjuk a kerest, es megnezzuk, MIT kuldott
  // volna. A valaszt a teszt allitja be, igy a hibas ag is merheto.
  let kertek = [], valasz = { status: 200, body: '{"ok":true}' };
  await p.route('**/ertekeles', async route => {
    kertek.push({ mod: route.request().method(),
                  torzs: JSON.parse(route.request().postData() || '{}') });
    await route.fulfill({ status: valasz.status, contentType: 'application/json',
                          body: valasz.body,
                          headers: { 'Access-Control-Allow-Origin': '*' } });
  });
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#table tr');
  await p.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                          null, { timeout: 20000 });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });

  // ---- a sav helye ----
  cim('Hol van a sáv');
  await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [H, V, R]);
  await p.waitForSelector('#mBody .artstrip');
  jo(await p.locator('#mBody .artrate').isVisible() === false,
     'becsukott cikknél nem látszik — amit nem olvastál, ne értékeld');
  await p.evaluate(() => { document.querySelector('#mBody .artstrip').open = true; });
  await p.waitForSelector('#mBody .artrate');
  jo(await p.locator('#mBody .artrate').isVisible(), 'kinyitva ott van');
  jo(await p.locator('#mBody .artrateg').count() === 4, 'négy fokozat');

  // ---- negyes: egy koppintas ----
  cim('Négyes: egy koppintás');
  kertek = [];
  await p.locator('#mBody .artrateg[data-pont="4"]').click();
  await p.waitForFunction(() => /Köszi/.test(document.querySelector('#mBody .artrate').textContent),
                          null, { timeout: 5000 });
  jo(kertek.length === 1 && kertek[0].mod === 'POST', 'egy POST ment ki');
  const t4 = kertek[0].torzs;
  jo(t4.pont === 4 && t4.cikk === KULCS, 'a pont és a cikk azonosítója helyes — '
     + t4.pont + ' / ' + t4.cikk);
  jo(/^[a-z0-9]{8,32}$/.test(t4.eszkoz || ''), 'eszközazonosítóval — ' + t4.eszkoz);
  jo((t4.okok || []).length === 0 && !t4.indok, 'indokot nem kértünk tőle');
  jo(await p.locator('#mBody .artreason').count() === 0, 'nem nyílt indok-panel');
  jo(await p.evaluate(() => document.querySelector('#mBody .artstrip').open),
     'a cikk nyitva maradt — a kattintás nem csukta be');

  // ---- emlekszik ra, de at lehet ertekelni ----
  cim('Emlékszik, de átértékelhető');
  await p.evaluate(() => showMatchRound('Bazsa', 'Ádám', 7));
  await p.waitForSelector('#mBody .plr');
  await nyit(p);
  jo(/Köszi/.test(await p.locator('#mBody .artrate').innerText()),
     'visszatérve emlékszik rá: ' + (await p.locator('#mBody .artrate').innerText()).trim());
  await p.locator('#mBody .artrateagain').click();
  await p.waitForSelector('#mBody .artrateg');
  jo(await p.locator('#mBody .artrateg').count() === 4, 'átértékeléskor újra ott a négy fokozat');

  // ---- kettes: helyben nyilo indok-panel ----
  cim('Kettes: helyben kér indokot');
  const elotteY = await p.evaluate(() =>
    document.querySelector('#mBody .artstripbody p').getBoundingClientRect().top);
  kertek = [];
  await p.locator('#mBody .artrateg[data-pont="2"]').click();
  await p.waitForSelector('#mBody .artreason');
  jo(kertek.length === 0, 'még nem küldött semmit — előbb az indok');
  jo(await p.locator('#mBody .artchip').count() >= 5, 'gyorsválasztók: '
     + await p.locator('#mBody .artchip').count());
  jo(await p.locator('#mBody .artreasont').isVisible(), 'szabad szöveg is');
  jo(await p.locator('#mBody .artsend').isVisible()
     && await p.locator('#mBody .artskip').isVisible(), 'két gomb: küldés és kiút');
  const utanaY = await p.evaluate(() =>
    document.querySelector('#mBody .artstripbody p').getBoundingClientRect().top);
  jo(Math.abs(utanaY - elotteY) < 2,
     'a cikk szövege a helyén maradt — nem takarja el, amiről véleményt kérünk');

  // ---- gyorsvalaszto + szoveg ----
  cim('Kettes: a gyorsválasztó és a szöveg is elmegy');
  await p.locator('#mBody .artchip').first().click();
  await p.locator('#mBody .artreasont').fill('Nem derült ki belőle, mi döntött.');
  await p.locator('#mBody .artsend').click();
  await p.waitForFunction(() => /Köszi/.test(document.querySelector('#mBody .artrate').textContent),
                          null, { timeout: 5000 });
  jo(kertek.length === 1, 'egy POST ment ki');
  const t2 = kertek[0].torzs;
  jo(t2.pont === 2, 'a pont kettes — ' + t2.pont);
  jo((t2.okok || []).length === 1, 'a kiválasztott ok is elment — ' + JSON.stringify(t2.okok));
  jo(t2.indok === 'Nem derült ki belőle, mi döntött.', 'és a szöveg is');

  // ---- a kiut: elmegy, de indok nelkul ----
  cim('A kiút indok nélkül küld — nem hamisít');
  await p.locator('#mBody .artrateagain').click();
  await p.waitForSelector('#mBody .artrateg');
  kertek = [];
  await p.locator('#mBody .artrateg[data-pont="1"]').click();
  await p.waitForSelector('#mBody .artreason');
  await p.locator('#mBody .artchip').first().click();
  await p.locator('#mBody .artreasont').fill('Ezt mégsem küldöm el.');
  await p.locator('#mBody .artskip').click();
  await p.waitForFunction(() => /Köszi/.test(document.querySelector('#mBody .artrate').textContent),
                          null, { timeout: 5000 });
  const t1 = kertek[0].torzs;
  jo(t1.pont === 1, 'az egyes elment — ' + t1.pont);
  jo(!t1.indok && (t1.okok || []).length === 0,
     'de indok nélkül: amit a kiúttal küldött, azt nem írjuk mellé — '
     + JSON.stringify({ okok: t1.okok, indok: t1.indok }));

  // ---- sikertelen kuldes: nem vesz el, amit beirtak ----
  cim('Hibás küldésnél nem vész el, amit beírtak');
  await p.locator('#mBody .artrateagain').click();
  await p.waitForSelector('#mBody .artrateg');
  valasz = { status: 500, body: '{"ok":false}' };
  await p.locator('#mBody .artrateg[data-pont="1"]').click();
  await p.waitForSelector('#mBody .artreason');
  await p.locator('#mBody .artreasont').fill('Ez maradjon meg.');
  await p.locator('#mBody .artsend').click();
  await p.waitForFunction(() => /Nem sikerült/.test(
    document.querySelector('#mBody .artreasonq').textContent), null, { timeout: 5000 });
  jo(await p.locator('#mBody .artreasont').inputValue() === 'Ez maradjon meg.',
     'a beírt szöveg ott maradt');
  jo(await p.locator('#mBody .artsend').isEnabled(), 'és újra lehet próbálni');

  hibak.forEach(x => jo(false, 'oldalhiba: ' + x));
  await vege(br);
})();
