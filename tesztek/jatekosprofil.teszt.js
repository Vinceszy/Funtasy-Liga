const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// Jatekosprofil (NB1). Amit rogzit:
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
    tul: (x.querySelector('.ptulajok') || {}).innerText || ''
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

  jo(perr.length === 0, 'nincs JS-hiba' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await vege(br);
})();
