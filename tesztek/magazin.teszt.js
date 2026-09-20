const { BASE, jo, cim, inditas, vege } = require('./kozos');
// A NEMZETHY SPORT OLDAL (nemzethy/): egy helyen az osszes iras.
//
// A meccs adatlapjan a sav arra valaszol, mi tortent AZON a meccsen. Ide az
// jon, aki egyben olvasna vegig az egeszet - es ez a ket nezet konnyen
// elcsuszhatna abban, mit szabad mutatni. Ezert a lenyeg itt a KAPU: a
// magazin nem mutathat tobbet, mint a meccs adatlapja.
//
// KET UZEMMOD. `?liga=nb1` az ADOTT LIGA ujsagja - sajat szinekkel, sajat
// nevvel, csak az o irasaival -, parameter nelkul a kozos kiadas. A liga
// oldalarol a felso savbol nyilik, a kezdolaprol a kozos.
//
// Amit rogzit:
//  - a fejlec a lap neve es a szlogen;
//  - minden kint levo iras megjelenik, TELJES szoveggel (nem felutessel);
//  - le nem zart fordulo osszefoglaloja itt sem latszik, csak a beharangozoja;
//  - a liga-szuro mukodik, es a ligankenti cim vele mozog;
//  - minden cikk alatt ott az ertekelo sav;
//  - a "Masolom" a ROVID valtozatot es a cikkre mutato hivatkozast adja;
//  - a lablecbol elerheto az oldal.
(async () => {
  const br = await inditas();
  const hibak = [];
  const p = await br.newPage({ viewport: { width: 1000, height: 1000 } });
  p.on('pageerror', e => hibak.push(e.message));
  for (const m of ['**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await p.route(m, r => r.abort());
  // vagolap a biztonsagos kontextuson kivul is: sajat, merheto valtozat
  await p.addInitScript(() => {
    window.__masolt = [];
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
      writeText: t => { window.__masolt.push(t); return Promise.resolve(); } } });
  });
  await p.goto(BASE + 'nemzethy/');
  await p.waitForSelector('.magcikk', { timeout: 20000 });

  cim('Fejléc');
  jo((await p.locator('.magcim').textContent()).trim() === 'Nemzethy Sport', 'a lap neve');
  jo((await p.locator('.magszlogen').textContent()).trim() === 'Heti Funtasy Magazin',
     'és a szlogen');

  // ---- teljes szoveg, nem felutes ----
  cim('Teljes szöveg');
  const varat = await p.evaluate(async () => {
    const j = await (await fetch('../articles.json')).json();
    const out = {};
    for (const [lg, rs] of Object.entries(j.leagues || {}))
      for (const [r, ks] of Object.entries(rs))
        for (const [k, m] of Object.entries(ks))
          for (const [par, a] of Object.entries(m))
            out[lg + '|' + r + '|' + k + '|' + par] = { bek: a.text.length, rovid: a.short };
    return out;
  });
  const elsoBek = await p.$$eval('.magcikk .magtest p', n => n.length);
  const varhatoBek = Object.values(varat).reduce((s, x) => s + x.bek, 0);
  jo(await p.locator('.magcikk').count() === Object.keys(varat).length,
     `minden írás kint van (${await p.locator('.magcikk').count()}/${Object.keys(varat).length})`);
  jo(elsoBek === varhatoBek,
     `és teljes szöveggel, nem felütéssel (${elsoBek}/${varhatoBek} bekezdés)`);

  // ---- a kapu: nem mutat tobbet, mint a meccs adatlapja ----
  cim('A kapu itt is zár');
  const kapu = await p.evaluate(async () => {
    const [j, res, hist] = await Promise.all([
      (await fetch('../articles.json')).json(),
      (await fetch('../results.json')).json(),
      (await fetch('../draft_history.json')).json()]);
    const ideig = new Set((res.provisional || []).map(Number));
    const zart = { nb1: new Set(), pl: new Set(Object.values(hist.veglegesek || []).map(Number)) };
    for (const r in (res.schedule || {}))
      if (!ideig.has(+r) && res.schedule[r].some(m => m && m[2] != null)) zart.nb1.add(+r);
    // minden osszefoglalo, aminek a forduloja NEM vegleges
    const tiltott = [];
    for (const [lg, rs] of Object.entries(j.leagues || {}))
      for (const [r, ks] of Object.entries(rs))
        if (ks.summary && !zart[lg].has(+r))
          for (const par of Object.keys(ks.summary)) tiltott.push(lg + ' ' + r + ' ' + par);
    return { tiltott, zartNb1: [...zart.nb1], zartPl: [...zart.pl] };
  });
  console.log(`   lezárt fordulók — NB1: ${kapu.zartNb1.join(',')} · PL: ${kapu.zartPl.join(',')}`);
  console.log(`   olyan összefoglaló, aminek nem szabadna kint lennie: ${kapu.tiltott.length}`);
  // amelyik osszefoglalo nem lehetne kint, az nincs is kint
  const kintiKulcsok = await p.$$eval('.magcikk', n => n.map(x => x.id));
  const bennmaradt = kapu.tiltott.filter(t => {
    const [lg, r] = t.split(' ');
    return kintiKulcsok.some(id => id.startsWith('c-' + lg + '-' + r + '-summary'));
  });
  jo(bennmaradt.length === 0,
     'le nem zárt forduló összefoglalója itt sincs kint — ' + JSON.stringify(bennmaradt));

  // ---- szuro ----
  cim('Liga-szűrő');
  const mind = await p.locator('.magcikk').count();
  await p.locator('#magSzuro .vlt-chip', { hasText: 'NB1' }).click();
  await p.waitForTimeout(150);
  const nb1db = await p.locator('.magcikk').count();
  jo(nb1db > 0 && nb1db < mind, `NB1-re szűrve kevesebb (${nb1db}/${mind})`);
  jo(await p.$$eval('.magliga', n => n.length) === 1, 'egyetlen liga-cím maradt');
  await p.locator('#magSzuro .vlt-chip', { hasText: 'PL' }).click();
  await p.waitForTimeout(150);
  const pldb = await p.locator('.magcikk').count();
  jo(nb1db + pldb === mind, `a két liga kiadja az egészet (${nb1db} + ${pldb} = ${mind})`);
  await p.locator('#magSzuro .vlt-chip', { hasText: 'Mind' }).click();
  await p.waitForTimeout(150);

  // ---- ertekeles es masolas ----
  cim('Értékelés és másolás');
  jo(await p.locator('.magcikk .artrate').count() === mind,
     'minden írás alatt ott az értékelő sáv');
  const elso = p.locator('.magcikk').first();
  const rovid = await elso.locator('.magmaso').getAttribute('data-rovid');
  await elso.locator('.magmaso').click();
  await p.waitForFunction(() => window.__masolt && window.__masolt.length, null, { timeout: 5000 });
  const masolt = (await p.evaluate(() => window.__masolt[0])) || '';
  jo(masolt.startsWith(rovid), 'a rövid változat került a vágólapra');
  jo(/\/nemzethy\/#c-/.test(masolt), 'és egy a cikkre mutató hivatkozás — ' + masolt.split('\n')[1]);
  jo(/Kimásolva/.test(await elso.locator('.magmaso').textContent()), 'a gomb vissza is jelez');

  // ---- elerheto a lablecbol ----
  cim('Elérhetőség');
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#lablec a');
  jo(await p.locator('#lablec a[href$="nemzethy/"]').count() === 1,
     'a láblécből elérhető a liga-oldalról is');

  // ---- liga-uzemmod ----
  for (const lg of ['nb1', 'pl']){
    cim('Liga-újság — ' + lg);
    await p.goto(BASE + 'nemzethy/?liga=' + lg);
    await p.waitForSelector('.magcikk', { timeout: 20000 });
    const a = await p.evaluate(() => ({
      tema: document.body.className,
      cimke: (document.querySelector('.magcim .tag') || {}).textContent,
      szlogen: document.querySelector('.magszlogen').textContent,
      cikkek: document.querySelectorAll('.magcikk').length,
      szuro: getComputedStyle(document.getElementById('magSzuroSav')).display,
      ligacim: document.querySelectorAll('.magliga').length,
      masik: document.getElementById('magMasik').style.display !== 'none',
      magassag: document.scrollingElement.scrollHeight,
      tullogas: document.scrollingElement.scrollWidth - document.documentElement.clientWidth,
    }));
    jo(a.tema === 'liga-' + lg, `${lg}: a lap átveszi a liga színeit (${a.tema})`);
    jo((a.cimke || '').trim().toLowerCase() === lg, `a fejlécben a liga neve (${a.cimke})`);
    jo(a.cikkek > 0 && a.cikkek < mind, `csak ennek a ligának az írásai (${a.cikkek}/${mind})`);
    jo(a.szuro === 'none' && a.ligacim === 0,
       'nincs liga-szűrő és nincs liga-cím — ez már eleve az ő újságja');
    jo(a.masik, 'és van átjárás a közös kiadásra');
    jo(a.tullogas === 0, `telefonon nem lóg ki oldalra (${a.tullogas} px)`);
    console.log(`   lap magassága telefonon: ${a.magassag} px`);
  }

  // ---- belepesi pontok ----
  cim('Belépési pontok');
  for (const [ut, varthref] of [['nb1/', '../nemzethy/?liga=nb1'],
                                ['pl/', '../nemzethy/?liga=pl']]){
    await p.goto(BASE + ut);
    await p.waitForSelector('.liganav .ujsaglink', { timeout: 20000 });
    const g = p.locator('.liganav .ujsaglink');
    jo(await g.getAttribute('href') === varthref,
       `/${ut} felső sávjából a SAJÁT újságja nyílik (${await g.getAttribute('href')})`);
    jo((await g.textContent()).includes('Nemzethy Sport'), 'és a neve is ott áll');
  }
  await p.goto(BASE);
  await p.waitForSelector('.ujdonsagsor');
  jo(await p.locator('.ujdonsagsor[href="nemzethy/"]').count() === 1,
     'a kezdőlapról a KÖZÖS kiadás nyílik, kiemelt soron');
  await p.goto(BASE + 'nemzethy/');
  await p.waitForSelector('.magcikk');
  jo(await p.locator('.liganav .ujsaglink').count() === 0,
     'az újság saját lapján nincs önmagára mutató gomb');

  hibak.forEach(x => jo(false, 'oldalhiba: ' + x));
  await vege(br);
})();
