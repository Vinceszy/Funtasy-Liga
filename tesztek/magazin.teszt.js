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
//  - negy szuro (liga, szakvezeto, fordulo, tipus), egymassal osszjatekban:
//    mindegyik CSAK azokat az ertekeket kinalja, amik a tobbi szuro mellett
//    tenylegesen leteznek - ures talalatra nem lehet kattintani;
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

  // ---- szurok ----
  cim('Szűrők');
  const mind = await p.locator('.magcikk').count();
  const csoportok = async () => p.$$eval('.magszuro',
                                         n => n.map(x => x.options[0].text));
  jo(JSON.stringify(await csoportok()) ===
       JSON.stringify(['Liga vagy szakvezető', 'Forduló', 'Típus']),
     'a liga és a szakvezető EGY vezérlő — ' + (await csoportok()).join(', '));
  jo(JSON.stringify(await p.$$eval('.magszuro[data-szuro="ligaki"] optgroup',
                                   n => n.map(x => x.label)))
       === JSON.stringify(['Liga', 'Szakvezető']),
     'elöl a két liga, alatta a szakvezetők');
  jo(await p.evaluate(() =>
       Math.round(document.querySelector('.magszurok').getBoundingClientRect().height)) < 130,
     'a szűrősáv nem eszi meg a lapot — '
     + await p.evaluate(() =>
         Math.round(document.querySelector('.magszurok').getBoundingClientRect().height)) + ' px');

  // legordulo, nem gombsor: a rendszer sajat valasztojat nyitja telefonon
  const valaszt = async (szuro, ertek) => {
    await p.selectOption(`.magszuro[data-szuro="${szuro}"]`, ertek);
    await p.waitForTimeout(150);
  };
  await valaszt('ligaki', 'liga:nb1');
  const nb1db = await p.locator('.magcikk').count();
  jo(nb1db > 0 && nb1db < mind, `ligára szűrve kevesebb (${nb1db}/${mind})`);
  jo(await p.$$eval('.magliga', n => n.length) === 1, 'egyetlen liga-cím maradt');
  await valaszt('ligaki', 'liga:pl');
  const pldb = await p.locator('.magcikk').count();
  jo(nb1db + pldb === mind, `a két liga kiadja az egészet (${nb1db} + ${pldb} = ${mind})`);
  await valaszt('ligaki', 'mind');

  // EGY EMBER, EGY SOR. A ket liga MAS NEVEN ismeri ugyanazt a szakvezetot
  // (az NB1-ben becenev, a PL-ben csapatnev), es a kozos kiadas ettol
  // ketszer kinalta oket, ket kulon emberkent. Amit ez rogzit: aki mindket
  // ligaban jatszik, EGY sorban all a ket nevevel - es rea szurve MINDKET
  // liga irasai eljonnek.
  const nep = await p.$$eval(
    '.magszuro[data-szuro="ligaki"] optgroup[label="Szakvezető"] option',
    n => n.map(x => ({ ertek: x.value, felirat: x.text })));
  // A nevek magukbol a cikkekbol jonnek (a parositas ket szoveges csomopontja),
  // az emberek pedig a lap sajat nev->ember feloldasabol: igy a teszt nem
  // ismetli meg a csatolotablat, csak azt allitja, hogy ossze VAN vonva.
  const szam = await p.evaluate(() => {
    const nevek = new Set();
    document.querySelectorAll('.magcikk .magpar').forEach(h =>
      [...h.childNodes].forEach(c => {
        const t = c.nodeType === 3 ? c.textContent.trim() : '';
        if (t) nevek.add(t);
      }));
    return { nevek: nevek.size,
             emberek: new Set([...nevek].map(n => SZEMELY(n).kulcs)).size };
  });
  jo(nep.length === szam.emberek && szam.emberek < szam.nevek,
     `${szam.nevek} név, de ${nep.length} sor a szűrőben — aki mindkét ligában `
     + 'játszik, egyszer szerepel');
  const ketligas = nep.filter(x => x.felirat.includes(' · '));
  jo(ketligas.length === szam.nevek - szam.emberek,
     `és a két liganevét egyben mutatja — ${ketligas.map(x => x.felirat).join(' | ')}`);

  const valasztott = ketligas[0];
  await valaszt('ligaki', valasztott.ertek);
  const sorok = await p.$$eval('.magcikk', n => n.map(x => ({
    liga: x.id.split('-')[1], par: x.querySelector('.magpar').textContent })));
  const nevei = valasztott.felirat.split(' · ');
  jo(sorok.length > 0 && sorok.every(x => nevei.some(n => x.par.includes(n))),
     `${valasztott.felirat}: mind a ${sorok.length} írás róla szól`);
  jo(new Set(sorok.map(x => x.liga)).size === 2,
     'és mindkét ligából — egy ember, egy szűrés');
  // a tobbi szuro MAR CSAK a hozza tartozo ertekeket kinalja
  const fordulok = await p.$$eval('.magszuro[data-szuro="fordulo"] option',
                                  n => n.map(x => x.value));
  const vartFordulok = await p.$$eval('.magcikk .magfordulo',
                                      n => [...new Set(n.map(x => parseInt(x.textContent)))]);
  jo(fordulok.filter(x => x !== 'mind').length === vartFordulok.length,
     `a fordulók listája vele szűkült (${fordulok.filter(x => x !== 'mind').join(',')})`);

  await valaszt('fajta', 'summary');
  const cimkek2 = await p.$$eval('.magcikk .magrovat', n => n.map(x => x.textContent));
  jo(cimkek2.length > 0 && cimkek2.every(t => /Összefoglaló/i.test(t)),
     `típusra is szűr (${cimkek2.length} összefoglaló)`);
  jo(/\d+ \/ \d+/.test(await p.locator('.magszam').textContent()),
     'ott áll, hányból hány látszik — ' + await p.locator('.magszam').textContent());
  jo(await p.locator('.magtorol').count() === 1, 'és egy gombbal törölhető az egész szűrés');
  await p.locator('.magtorol').click();
  await p.waitForTimeout(150);
  jo(await p.locator('.magcikk').count() === mind, 'a törlés visszaadja az egészet');
  jo(await p.locator('.magtorol').count() === 0, 'szűrés nélkül a törlés el is tűnik');

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
      ligaszuro: document.querySelectorAll('.magszuro[data-szuro="ligaki"]').length,
      szurocsoport: document.querySelectorAll('.magszuro').length,
      ligacim: document.querySelectorAll('.magliga').length,
      masik: document.getElementById('magMasik').style.display !== 'none',
      magassag: document.scrollingElement.scrollHeight,
      tullogas: document.scrollingElement.scrollWidth - document.documentElement.clientWidth,
    }));
    jo(a.tema === 'liga-' + lg, `${lg}: a lap átveszi a liga színeit (${a.tema})`);
    jo((a.cimke || '').trim().toLowerCase() === lg, `a fejlécben a liga neve (${a.cimke})`);
    jo(a.cikkek > 0 && a.cikkek < mind, `csak ennek a ligának az írásai (${a.cikkek}/${mind})`);
    jo(a.ligaszuro === 0 && a.ligacim === 0,
       'nincs liga-szűrő és nincs liga-cím — ez már eleve az ő újságja');
    jo(a.szurocsoport === 3,
       `a három szűrő viszont megvan: szakvezető, forduló, típus (${a.szurocsoport})`);
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
  // A KET SZINT. A ligak egymas alternativai; az ujsag AZ ADOTT LIGA resze.
  // Ezert mindenhol PONTOSAN EGY elem vilagit - az, ahol vagy -, es az
  // ujsag gombja nem tunik el, amikor rajta allsz. Korabban eltunt, es a
  // visszaut maga a liga pottye volt, ami nem nezett ki visszautnak.
  cim('A felső sáv két szintje');
  for (const [ut, vartAktiv, vartLigaLink] of [
        ['nb1/', 'NB1', null],
        ['nemzethy/?liga=nb1', 'Nemzethy Sport NB1', '../nb1/'],
        ['nemzethy/', 'Nemzethy Sport', null]]) {
    await p.goto(BASE + ut);
    await p.waitForSelector('.liganav a', { timeout: 20000 });
    const a = await p.evaluate(() => ({
      aktivak: [...document.querySelectorAll('.liganav a.on')]
                 .map(x => x.textContent.trim()),
      ujsag: !!document.querySelector('.liganav .ujsaglink'),
      nb1href: (document.querySelector('.liganav .ligalink') || {}).getAttribute
                 ? document.querySelector('.liganav .ligalink').getAttribute('href') : null,
      nb1aktiv: (document.querySelector('.liganav .ligalink') || {}).className || '',
    }));
    jo(a.aktivak.length === 1 && a.aktivak[0] === vartAktiv,
       `/${ut || ''}: pontosan egy elem világít, az, ahol vagy — ${JSON.stringify(a.aktivak)}`);
    jo(a.ujsag, `/${ut || ''}: az újság gombja ott van (nem tűnik el)`);
    if (vartLigaLink)
      jo(!a.nb1aktiv.includes('on') && a.nb1href === vartLigaLink,
         `az újságból a liga pöttye a liga oldalára visz vissza (${a.nb1href})`);
  }

  hibak.forEach(x => jo(false, 'oldalhiba: ' + x));
  await vege(br);
})();
