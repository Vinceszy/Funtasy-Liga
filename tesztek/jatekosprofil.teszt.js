const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// Jatekosprofil. Amit rogzit (NB1 + PL):
//   - a "Szezon jatekosai" sorai megnyitjak a profilt, es viszik a
//     cp-azonositot (enelkul a bontas nem lenne lekerheto);
//   - a fordulo sora az ELLENFELET, az ALLAST es a jatekos SAJAT pontjat
//     mutatja - vagyis a kapitanysag es a pad nelkuli alappontot;
//   - a PADOS ertekbol visszaszamolt alappont NEM csuszik el 0,01-gyel
//     (az API a felezes utan ket tizedesre kerekit: 0,75 -> 0,38; a
//     visszaszorzas 0,76-ot adna) - ez a legkonnyebben elromlo reszlet;
//   - egy forduloban TOBB szakvezeto is szerepelhet (salary cap liga);
//   - akinel senki sem volt, arra kiirjuk, hogy senkinel sem volt;
//   - a sor lenyilasa a game-player-stats bontasat mutatja;
//   - a vissza gomb a "Szezon jatekosai" fulre ter vissza.
//
// Az elofeltetelt a teszt ALLITJA ELO (jsonAtir), nem a repo aktualis
// adatara epit: igy egy fordulo-valtas nem buktatja el.
const CP = 424242;
const JATEKOS = { name: 'Teszt Elek', team: 'PAKS', pos: 'CS', u21: false, hun: true,
                  price: 8, total: 30, id: CP, played: true, vege: true };

(async () => {
  const br = await inditas();
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);

  // ---- elofeltetel: egy kitalalt jatekos ismert szerepekkel ----
  //  1. f: senkinel sem volt
  //  2. f: Katyul PADJAN, week=0,38  -> alappont 0,75 (nem 0,76!)
  //  3. f: Katyul KAPITANYA (week=19) es Bence kezdoje (week=9,5) -> 9,5
  await jsonAtir(p, '**/squad_history.json*', j => {
    const R = j.rounds;
    for (const r of Object.keys(R))
      for (const mgr of Object.keys(R[r]))
        R[r][mgr] = R[r][mgr].filter(x => x.id !== CP);
    R['2'].Katyul.push(Object.assign({}, JATEKOS, { cap: false, sub: true,  week: 0.38 }));
    R['3'].Katyul.push(Object.assign({}, JATEKOS, { cap: true,  sub: false, week: 19 }));
    R['3'].Bence .push(Object.assign({}, JATEKOS, { cap: false, sub: false, week: 9.5 }));
    return j;
  });
  // a PAKS meccsei, hogy az ellenfel es az allas determinisztikus legyen
  await jsonAtir(p, '**/meccsek.json*', j => {
    j.rounds['1'] = [{ id: 1, h: 'PAKS', v: 'FTC', hp: 1, vp: 3, vege: true }];
    j.rounds['2'] = [{ id: 2, h: 'ZTE',  v: 'PAKS', hp: 0, vp: 2, vege: true }];
    j.rounds['3'] = [{ id: 3, h: 'PAKS', v: 'DVSC', hp: 2, vp: 2, vege: true }];
    return j;
  });
  // a bontas-vegpont: az apiKi utan allitjuk be, ezert ez nyer
  await p.route('**game-player-stats**', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ data: [
      { value: 1,  points: 6, competition_stat_config: { name: 'Gól' } },
      { value: 78, points: 0, competition_stat_config: { name: 'Játszott perc' } },
      { value: 1,  points: 3, competition_stat_config: { name: 'Győzelem' } }] }) }));

  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof showProfil === 'function', null, { timeout: 20000 });

  // ---- a belepesi pont: "Szezon jatekosai" ----
  cim('Belépési pont');
  await p.evaluate(() => showSquad(['Katyul'], 'players'));
  await p.waitForSelector('[data-prof]', { timeout: 20000 });
  const sor = await p.$(`[data-prof="Teszt Elek"]`);
  jo(!!sor, 'a kitalált játékos sora ott van a "Szezon játékosai" listában');
  jo(await p.$eval(`[data-prof="Teszt Elek"]`, e => e.dataset.pcp) === String(CP),
     'a sor viszi a cp-azonosítót (enélkül nem lenne lekérhető a bontás)');

  await sor.click();
  await p.waitForSelector('.proflista', { timeout: 20000 });

  // ---- fejlec ----
  cim('Fejléc');
  const fej = await p.$eval('.proffej', e => e.innerText);
  jo(/Teszt Elek/.test(fej) && /PAKS/.test(fej), 'a fejléc a nevet és a klubot mutatja');
  jo(await p.$$eval('.proffej .flag', a => a.length) === 1,
     'a magyar játékost zászló jelzi (nem kék címke)');

  // ---- a fordulo-sorok ----
  cim('Fordulónkénti sorok');
  const sorok = await p.$$eval('.profsor', a => a.map(x => ({
    r: x.querySelector('.ppos').textContent.trim(),
    nm: x.querySelector('.nm').textContent.trim(),
    allas: (x.querySelector('.pallas') || {}).textContent || '',
    pts: x.querySelector('.pts').textContent.trim(),
    tul: (x.querySelector('.ptulajok') || {}).innerText || '',
    ar: (x.querySelector('.parany') || {}).textContent || ''
  })));
  const f = n => sorok.find(s => s.r === n + '.');

  jo(f('1') && /senkinél/.test(f('1').tul), '1. forduló: kiírja, hogy senkinél sem volt');
  jo(f('1') && /FTC/.test(f('1').nm) && /idegenben|otthon/.test(f('1').nm),
     '1. forduló: az ellenfél és a pálya látszik');
  jo(f('1') && f('1').allas.replace(/\s/g, '') === '1–3',
     '1. forduló: az állás hazai–vendég sorrendben (1–3), nem megforgatva');

  jo(f('2') && f('2').pts === '0,75',
     'PAD: a 0,38-as heti értékből 0,75 alappont lesz — nem 0,76 '
     + '(a felezés utáni kerekítést a negyedre kerekítés hozza vissza)'
     + (f('2') ? ' — kapott: ' + f('2').pts : ''));
  jo(f('2') && /Katyul/.test(f('2').tul) && /pad/.test(f('2').tul),
     '2. forduló: Katyul padján volt');

  jo(f('3') && f('3').pts === '9,5',
     'KAPITÁNY: a 19-es heti értékből 9,5 alappont lesz (a duplázás nélkül)');
  jo(f('3') && /Katyul/.test(f('3').tul) && /kapitány/.test(f('3').tul)
            && /Bence/.test(f('3').tul) && /kezdő/.test(f('3').tul),
     '3. forduló: MINDKÉT szakvezető szerepel, a saját szerepével');

  // ---- a ligara vetitett aranyok ----
  // A liga 8 kerete a nevezo. A 2. forduloban egyedul Katyul padjan volt
  // (1/8 = 13%, kezdo 0), a 3.-ban Katyul kapitanya ES Bence kezdoje
  // (2/8 = 25%) - ez utobbi rogziti, hogy a KAPITANY IS KEZDONEK szamit,
  // kulonben itt 13% jonne ki.
  cim('A ligára vetített arányok');
  jo(f('2') && /keret\s*13%/.test(f('2').ar) && /kezdő\s*0%/.test(f('2').ar)
            && /kapitány\s*0%/.test(f('2').ar),
     '2. forduló: 1 keret a 8-ból, padon — keret 13%, kezdő 0%, kapitány 0%'
     + (f('2') ? ' — kapott: ' + f('2').ar : ''));
  jo(f('3') && /keret\s*25%/.test(f('3').ar) && /kezdő\s*25%/.test(f('3').ar)
            && /kapitány\s*13%/.test(f('3').ar),
     '3. forduló: a kapitány is kezdő — keret 25%, kezdő 25%, kapitány 13%'
     + (f('3') ? ' — kapott: ' + f('3').ar : ''));
  jo(f('1') && !f('1').ar, '1. forduló: akinél senki sem volt, ott nincs arány-blokk');

  // ---- lenyilo bontas ----
  cim('Lenyíló bontás');
  await p.click('.profsor[data-pr="3"]');
  await p.waitForSelector('.accpanel .acctable', { timeout: 20000 });
  const acc = await p.$eval('.accpanel', e => e.innerText);
  jo(/Gól/.test(acc) && /Győzelem/.test(acc), 'a bontás a pontot érő eseményeket mutatja');
  jo(/Játszott perc/.test(acc), 'a játszott perc a 0 pont ellenére is látszik');
  jo(/PAKS/.test(acc) && /DVSC/.test(acc), 'a bontás fölött ott a klub meccse');

  // ---- vissza ----
  cim('Visszalépés');
  await p.click('#ovBack');
  await p.waitForSelector('[data-prof]', { timeout: 20000 });
  jo(await p.$('.proflista') === null, 'a vissza gomb a "Szezon játékosai" listára tér vissza');

  // ---- draft liga: ott az arany ertelmetlen ----
  // Nem az NB1/PL kulonbsegen mulik, hanem a liga TIPUSAN: draftban egy
  // jatekos pontosan egy szakvezetonel lehet, tehat a "keret %" mindig 1/N
  // vagy 0 lenne. Ugyanazt az adatot rajzoltatjuk ki ketfele ligaval.
  cim('Draft liga: nincs arány');
  const ketfele = await p.evaluate(() => {
    const sor = { r: 1, ellenfel: 'ARS', hazai: true, hp: 2, vp: 1, pont: 7,
                  keretszam: 8,
                  tulajok: [{ nev: 'A', kezdo: true, kapitany: true },
                            { nev: 'B', kezdo: false, kapitany: false }] };
    const rajz = l => FunTasy.profilHTML({ liga: l, nev: 'X', sorok: [sor] });
    return { nb1: rajz('nb1'), pl: rajz('pl') };
  });
  jo(/class="parany"/.test(ketfele.nb1), 'salary cap ligában ott az arány-blokk');
  jo(!/class="parany"/.test(ketfele.pl), 'DRAFT ligában nincs arány-blokk (mindig 1 vagy 0 keret)');
  jo(/kapitány/.test(ketfele.pl) && /pad/.test(ketfele.pl),
     'a szerep neve draft ligában is látszik (csak az arány marad el)');

  await p.close();

  // ================= PL (draft liga) =================
  // Az element-summary valaszat mi adjuk: a konteneres gepbol az FPL nem
  // erheto el, es a teszt igy determinisztikus is. A KESOBB regisztralt
  // route nyer, ezert eloszor vagunk el mindent, utana jon a celzott mock.
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', x => qerr.push(x.message));
  for (const m of ['**mlsz.hu/**', '**premierleague.com/**',
                   '**corsproxy.io/**', '**allorigins**']) await q.route(m, r => r.abort());
  await q.route('**element-summary**', r => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ history: [
      { event: 1, total_points: 17, detail: 'AVL (H) 4-0', minutes: 77 },
      // DUPLA FORDULO: ugyanaz a fordulo ket meccsel
      { event: 2, total_points: 3,  detail: 'FUL (A) 2-3', minutes: 90 },
      { event: 2, total_points: 6,  detail: 'BRE (H) 1-0', minutes: 90 }
    ], fixtures: [] }) }));

  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(() => typeof showProfil === 'function'
    && Object.keys(HIST).length > 0, null, { timeout: 20000 });

  cim('PL: belépési pont');
  const csapat = await q.evaluate(() => Object.keys(HIST[Object.keys(HIST)[0]])[0]);
  await q.evaluate(id => showTeam(+id, 'jatekosok'), csapat);
  await q.waitForSelector('[data-prof]', { timeout: 20000 });
  jo(/^\d+$/.test(await q.$eval('[data-prof]', e => e.dataset.prof)),
     'a "Szezon játékosai" sora viszi a játékos azonosítóját');
  await q.click('[data-prof]');
  await q.waitForSelector('.proflista', { timeout: 20000 });

  const psorok = await q.$$eval('.profsor', a => a.map(x => ({
    r: x.querySelector('.ppos').textContent.trim(),
    nm: x.querySelector('.nm').textContent.trim(),
    allas: (x.querySelector('.pallas') || {}).textContent || '',
    pts: x.querySelector('.pts').textContent.trim(),
    tul: (x.querySelector('.ptulajok') || {}).innerText || ''
  })));
  const g = n => psorok.find(x => x.r === n + '.');

  cim('PL: az eredmény sorrendje');
  // A `detail` allasa HAZAI-VENDEG sorrendben all (kimerve: naplo/fpl-profil.txt,
  // 25 idegenbeli meccsbol 25). Idegenbeli meccsen valik el a ket olvasat:
  // "FUL (A) 2-3" annyit tesz, hogy a HAZAI FUL 2, a jatekos csapata 3 -
  // ha megforditva ertelmeznenk, itt 3-2 allna.
  jo(g('2') && /FUL \(i\) 2–3/.test(g('2').nm),
     'idegenbeli meccs: "FUL (A) 2-3" -> FUL (i) 2–3, nem megfordítva'
     + (g('2') ? ' — kapott: ' + g('2').nm : ''));
  jo(g('1') && /AVL/.test(g('1').nm) && /otthon/.test(g('1').nm)
            && g('1').allas.replace(/\s/g, '') === '4–0',
     'egy meccsnél az állás a saját oszlopában áll (4–0)');

  cim('PL: dupla forduló');
  jo(g('2') && /FUL/.test(g('2').nm) && /BRE/.test(g('2').nm),
     'dupla fordulóban MINDKÉT meccs látszik (a második nem tűnik el)');
  jo(g('2') && g('2').pts === '9',
     'dupla fordulóban a pontok összeadódnak (3 + 6 = 9)'
     + (g('2') ? ' — kapott: ' + g('2').pts : ''));
  jo(g('2') && !g('2').allas,
     'dupla fordulóban az állás-oszlop üres (az állások a meccsek mellett állnak)');

  cim('PL: tulajdonos');
  jo(g('1') && /kezdő/.test(g('1').tul), '1. forduló: a szakvezető és a szerep látszik');
  jo(g('2') && /szabadügynök/.test(g('2').tul),
     'akinél senki sem volt: "szabadügynök" (nem "senkinél sem volt")');
  jo(await q.$$eval('.parany', a => a.length) === 0,
     'draft ligában nincs arány-blokk a valódi oldalon sem');

  jo(qerr.length === 0, 'nincs JS-hiba a PL-oldalon'
     + (qerr.length ? ': ' + qerr.join(' | ') : ''));

  jo(perr.length === 0, 'nincs JS-hiba' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await vege(br);
})();
