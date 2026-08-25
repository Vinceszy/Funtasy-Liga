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

  jo(f('1') && /–/.test(f('1').tul), '1. forduló: rövid jel jelzi, hogy senkinél sem volt');
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
  cim('NB1: csak a lejátszott fordulók');
  // Az MLSZ-nel nincs menetrend-vegpont, tehat a jovobeli sorban se
  // ellenfelet, se idopontot nem tudnank kiirni - ures sorokat pedig nem
  // teszunk ki. (A PL-profil ezzel szemben elore is megy: ott van adat.)
  jo(!f('10') && !f('33'),
     'nincsenek jövőbeli, üres fordulósorok (' + sorok.length + ' sor, az utolsó a '
     + (sorok.length ? sorok[sorok.length - 1].r : '?') + ')');

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

  // ---- fooldali jatekoslista + kereso ----
  cim('NB1: főoldali lista és kereső');
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('.jlsor', { timeout: 20000 });
  const db = await p.$$eval('.jlsor', a => a.length);
  jo(db > 0 && db <= 40, 'a lista a legjobbakat mutatja, nem a teljes mezőnyt (' + db + ' sor)');
  // EKEZET NELKUL is talaljon: a mezony tele van ekezetes es delszlav
  // nevekkel, es senki nem fog kalapos c-t irni a keresobe. Olyan JATEKOS-
  // nevet keresunk a listaban, amiben van ekezet, es az ekezet nelkuli
  // alakjara keresunk ra.
  const cel = await p.$$eval('.jlsor .nm', a => {
    for (const x of a) {
      const nev = x.childNodes[0].textContent.trim();      // a klub kulon span
      const szo = nev.split(/\s+/).filter(w => w.normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') !== w)[0];
      if (szo) return szo;
    }
    return null;
  });
  if (cel){
    const celEk = cel.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    await p.fill('#jlDoboz .kereso', celEk);
    await p.waitForFunction(n => document.querySelectorAll('.jlsor').length < n,
                            db, { timeout: 5000 }).catch(() => {});
    const talalt = await p.$$eval('.jlsor .nm', a => a.map(x => x.textContent));
    jo(celEk !== cel.toLowerCase() && talalt.some(x => x.includes(cel)),
       'ékezet nélkül írva is megtalálja („' + celEk + '” → „' + cel + '”)');
  } else {
    jo(false, 'nem találtam ékezetes nevet a listában — az ékezet-teszt nem futott le');
  }
  // a kereses a TELJES mezonyben fusson, ne csak a kirajzolt sorokban:
  // olyanra keresunk, aki a lista vegen sincs benne
  await p.fill('#jlDoboz .kereso', 'zzzznincsilyen');
  await p.waitForSelector('#jlDoboz .jllista .loading', { timeout: 5000 });
  jo(/Nincs találat/.test(await p.$eval('#jlDoboz .jllista', e => e.innerText)),
     'nem létező névre saját üzenet jön, nem üres doboz');
  await p.fill('#jlDoboz .kereso', '');
  await p.waitForSelector('.jlsor', { timeout: 5000 });

  // A "+N" SOSEM vagodhat le: a nevek rovidulnek helyette. (Elobb egyben
  // volt a ket resz, es a CSS pont a darabszamot nyelte el.)
  cim('NB1: a „kinél van” oszlop');
  const tobbek = await p.$$eval('.jltobb', a => a.map(x => x.textContent));
  jo(!tobbek.length || tobbek.every(x => /^\+\d+$/.test(x)),
     'ahol többen birtokolják, a „+N” külön áll és teljes egészében látszik'
     + (tobbek.length ? ' — pl. ' + tobbek[0] : ' (most nincs ilyen sor)'));
  const levagott = await p.$$eval('.jltobb', a => a.some(x => x.scrollWidth > x.clientWidth + 1));
  jo(!levagott, 'a „+N” nincs elvágva');

  // ---- szurok, rendezes, lapozas ----
  cim('NB1: szűrés, rendezés, lapozás');
  const szurok = await p.$$eval('.jlszuro,.jlszam', a => a.map(x => x.dataset.szuro));
  jo(['poszt','klub','tulaj','kpc','ar','pts'].every(k => szurok.includes(k)),
     'minden oszlopnak van szűrője (' + szurok.join(', ') + ')');

  // "Valakinél": a jeloloerteknek NEM szabad vezerlokaraktert tartalmaznia -
  // a HTML-elemzo kicsereli, es a szuro nemán ures listat adna (igy is volt)
  await p.selectOption('[data-szuro="tulaj"]', { label: 'Valakinél' });
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0,
                          null, { timeout: 5000 }).catch(() => {});
  const gazdatlan = await p.$$eval('.jlsor .jltulaj', a => a.filter(x => /nincs/.test(x.className)).length);
  const gazdas = await p.$$eval('.jlsor', a => a.length);
  jo(gazdas > 0 && gazdatlan === 0,
     '„Valakinél”: csak akiknek van gazdájuk (' + gazdas + ' sor, ' + gazdatlan + ' gazdátlan)');
  await p.selectOption('[data-szuro="tulaj"]', { label: 'Senkinél' });
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0,
                          null, { timeout: 5000 }).catch(() => {});
  jo((await p.$$eval('.jlsor .jltulaj', a => a.every(x => /nincs/.test(x.className)))),
     '„Senkinél”: csak a gazdátlanok');
  await p.click('.jltorol');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 1, null, { timeout: 5000 });

  jo((await p.$$eval('.jlsor .jlkpc', a => a.every(x => /^\d+%$/.test(x.textContent)))),
     'a Keret% oszlop százalékot mutat');

  const lab1 = await p.$eval('.jllab', e => e.textContent);
  jo(/^1–\d+ \/ \d+/.test(lab1), 'a lábléc az aktuális tartományt mutatja (' + lab1 + ')');
  const lapGombok = await p.$$eval('.jllapozo > *', a => a.map(x => x.textContent));
  jo(lapGombok[0] === '‹' && lapGombok[lapGombok.length - 1] === '›'
     && lapGombok.includes('1') && lapGombok.some(x => /^\d+$/.test(x) && +x > 2),
     'a lapozóban OLDALSZÁMOK vannak, nem csak nyilak (' + lapGombok.join(' ') + ')');
  jo(await p.$eval('.jllapozo > button', e => e.disabled),
     'az első oldalon a vissza nyíl tiltott');
  // az UTOLSO oldal mindig elerheto egy kattintassal - tiz oldalt egyesevel
  // vegiglapozni nem hasznalhato
  const utolsoSzam = Math.max(...lapGombok.filter(x => /^\d+$/.test(x)).map(Number));
  await p.click('[data-ugras="' + (utolsoSzam - 1) + '"]');
  await p.waitForFunction(() => /\/ \d+ játékos$/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  jo(await p.$eval('.jllapozo > button:last-child', e => e.disabled),
     'az utolsó oldal egy kattintással elérhető, ott az előre nyíl tiltott');
  // az utolso oldalrol a 2. oldal gombja mar nincs kint (csak a szomszedok
  // es az elso/utolso) - eloszor vissza az elsore, onnan tovabb
  await p.click('[data-ugras="0"]');
  await p.waitForFunction(() => /^1–/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  await p.click('[data-ugras="1"]');
  await p.waitForFunction(() => /^41–/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  jo((await p.$eval('.jlsor .rank', e => e.textContent)) === '41.',
     'a 2. oldal a 41. sorral kezdődik (a sorszám folytatódik, nem nullázódik)');

  // oldalmeret: a "mind" eltunteti a lapozot
  await p.selectOption('.jlmeret', '0');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 100,
                          null, { timeout: 8000 });
  jo((await p.$$eval('.jllapozo > *', a => a.length)) === 0,
     '„mind” oldalméretnél nincs lapozó (nincs mit lapozni)');
  await p.selectOption('.jlmeret', '40');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length === 40,
                          null, { timeout: 8000 });
  // szures/kereses utan NEM maradhatunk egy nem letezo oldalon
  await p.fill('#jlDoboz .kereso', 'a');
  await p.waitForFunction(() => /^1–/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  jo(true, 'keresésre visszaugrik az első oldalra');
  await p.click('.jltorol');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 1, null, { timeout: 5000 });

  cim('NB1: a listából megnyílik a profil');
  await p.click('.jlsor');
  await p.waitForSelector('.proflista', { timeout: 20000 });
  jo(true, 'a lista sorára kattintva megnyílik a profil');
  await p.click('#ovClose');

  // ---- soha nem birtokolt jatekos: a profil nem varhat az API-ra ----
  // BEJELENTETT HIBA (2026-08-25): az ilyen jatekosnal fordulonkent egy
  // proxys keres ment ki, mind EGYSZERRE - a proxy eldobta oket, a profil
  // percekig toltott, a lenyilo bontas elhasalt. A szabaly azota: a profil
  // AZONNAL megjelenik kotojelekkel, a pontok SORBAN potladnak.
  cim('NB1: soha nem birtokolt játékos profilja');
  let egyszerre = 0, csucs = 0;
  await p.route('**game-player-stats**', async route => {
    egyszerre++; csucs = Math.max(csucs, egyszerre);
    await new Promise(r => setTimeout(r, 400));       // lassu proxy
    egyszerre--;
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ data: [{ value: 1, points: 2,
        competition_stat_config: { name: 'Gól' } }] }) });
  });
  await p.selectOption('[data-szuro="tulaj"]', { label: 'Senkinél' });
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0, null, { timeout: 5000 });
  const t0 = Date.now();
  await p.click('.jlsor');
  await p.waitForSelector('.proflista', { timeout: 20000 });
  jo(Date.now() - t0 < 3000,
     'a profil a lassú API bevárása NÉLKÜL megjelenik (' + (Date.now() - t0) + ' ms)');
  // ahol volt meccs, ott kotojel; ahol nem (elmaradt fordulo), ott a sajat
  // felirata - szam viszont meg sehol sem lehet
  jo((await p.$$eval('.profsor .pts', a => a.every(x => !/\d/.test(x.textContent)))),
     'a még le nem kért pontok helyén nem áll szám (kötőjel vagy „nincs meccs”)');
  await p.waitForFunction(() => [...document.querySelectorAll('.profsor .pts')]
    .every(x => x.textContent.trim() !== '—'), null, { timeout: 20000 });
  jo(true, 'a pontok a háttérben pótlódnak');
  jo(csucs === 1, 'a kérések SORBAN mennek, nem egyszerre (csúcs: ' + csucs + ')');
  // az unroute a teszt ELEJEN beallitott mockot is levenne - a kesleltetett
  // valasz marad, a tovabbi szakaszoknak az is jo
  await p.click('#ovClose');
  await p.click('.jltorol');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 1, null, { timeout: 5000 });

  // ---- belepes a pont-bontas aljarol ----
  cim('NB1: belépés a lenyíló aljáról');
  await p.evaluate(() => showSquad(['Katyul']));
  await p.waitForSelector('.plr[data-acc]', { timeout: 20000 });
  await p.click('.plr[data-acc]');
  await p.waitForSelector('.accpanel .profnyito', { timeout: 20000 });
  jo(/Teljes játékosprofil/.test(await p.$eval('.accpanel .profnyito', e => e.innerText)),
     'a bontás alján ott a „Teljes játékosprofil” sor');
  await p.click('.accpanel .profnyito');
  await p.waitForSelector('.proflista', { timeout: 20000 });
  const fej2 = await p.$eval('.proffej', e => e.innerText);
  jo(/[A-ZÁÉÍÓÖŐÚÜŰ]/.test(fej2.split('\n')[0]),
     'a lenyílóból nyitott profil fejléce is kitöltött (a posztot a keret-előzményből pótoljuk)');
  jo(await p.$('.accpanel .profnyito') === null,
     'a profilon BELÜL már nincs „Teljes játékosprofil” sor');

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
    ], fixtures: [
      // hatralevo meccsek: ellenfel-azonositoval es palya-jelzessel
      { event: 3, opponent: 1, is_home: true,  kickoff_time: '2026-09-01T13:00:00Z' },
      { event: 4, opponent: 6, is_home: false, kickoff_time: '2026-09-08T13:00:00Z' }
    ] }) }));

  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(() => typeof showProfil === 'function'
    && Object.keys(HIST).length > 0, null, { timeout: 20000 });

  cim('PL: belépési pont');
  const csapat = await q.evaluate(() => Object.keys(HIST[Object.keys(HIST)[0]])[0]);
  await q.evaluate(id => showTeam(+id, 'jatekosok'), csapat);
  await q.waitForSelector('#mBody [data-prof]', { timeout: 20000 });
  jo(/^\d+$/.test(await q.$eval('#mBody [data-prof]', e => e.dataset.prof)),
     'a "Szezon játékosai" sora viszi a játékos azonosítóját');
  await q.click('#mBody [data-prof]');
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

  cim('PL: előre is felsorolja a fordulókat');
  jo(psorok.length >= 38,
     'a profil MINDEN fordulót felsorol, nem csak a lejátszottakat (' + psorok.length + ')');
  jo(g('3') && /ARS/.test(g('3').nm) && /otthon/.test(g('3').nm),
     'jövőbeli fordulónál is ott az ellenfél (a hátralévő meccsekből)'
     + (g('3') ? ' — kapott: ' + g('3').nm : ''));
  jo(g('3') && !g('3').allas && g('3').pts === '—',
     'jövőbeli fordulónál nincs állás és nincs pont, csak az ellenfél');
  jo(g('3') && !g('3').tul.trim(),
     'jövőbeli fordulónál a tulajdonos ÜRES — nem tudjuk, kinél lesz, tehát '
     + '„szabadügynök”-öt sem írunk oda'
     + (g('3') ? ' — kapott: ' + JSON.stringify(g('3').tul) : ''));
  jo(g('38') && !/nincs meccs/.test(g('38').pts + g('38').nm),
     'a távoli fordulóra nem írunk „nincs meccs”-et (az elmaradást jelentene)');

  cim('PL: tulajdonos');
  jo(g('1') && /kezdő/.test(g('1').tul), '1. forduló: a szakvezető és a szerep látszik');
  // A "szabadugynok" csak akkor allitas, ha TUDJUK, hogy senkinel sem volt -
  // vagyis van keret-elozmenyunk arrol a fordulorol. A kozos retegen merjuk,
  // mert ott allithatjuk be mindket esetet.
  const gazdatlanSor = await q.evaluate(() => {
    const alap = { r: 1, ellenfel: 'ARS', hazai: true, hp: 2, vp: 1, tulajok: [] };
    const rajz = x => FunTasy.profilHTML(
      { liga: 'pl', nev: 'X', senkinel: '–', sorok: [Object.assign({}, alap, x)] });
    return { mult: rajz({ pont: 0 }), jovo: rajz({ jovo: true }) };
  });
  jo(/ptul nincs/.test(gazdatlanSor.mult),
     'lejátszott fordulónál, ahol tudjuk, hogy senkié sem volt: rövid jel áll ott');
  jo(!/ptul nincs/.test(gazdatlanSor.jovo),
     'jövőbeli fordulónál viszont semmi — azt nem tudhatjuk előre');
  jo(await q.$$eval('.parany', a => a.length) === 0,
     'draft ligában nincs arány-blokk a valódi oldalon sem');

  cim('PL: főoldali lista');
  // a szuro-legordulo is monogramot mutasson, mint az oszlop
  await q.waitForSelector('.jlsor', { timeout: 20000 });
  const opciok = await q.$$eval('[data-szuro="tulaj"] option',
    a => a.slice(3).map(x => ({ ertek: x.value, felirat: x.textContent, cim: x.title })));
  jo(opciok.length > 0 && opciok.every(x => x.felirat.length <= 4 && x.cim.length > x.felirat.length),
     'a „Kinél van” szűrő monogramot mutat, a teljes név a title-ben van'
     + (opciok.length ? ' — pl. ' + JSON.stringify(opciok[0]) : ''));
  jo(opciok.every(x => x.ertek === x.cim),
     'a szűrt érték a teljes név marad (az azonosít, nem a monogram)');
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForSelector('.jlsor', { timeout: 20000 });
  jo((await q.$$eval('.jlsor', a => a.length)) > 0, 'a PL-főoldalon is ott a játékoslista');
  jo((await q.$$eval('.jltobb', a => a.length)) === 0,
     'draft ligában sosincs „+N”: egy játékos legfeljebb egy keretben van');
  // A kereses NEVRE ES KLUBRA is talal - "ars" tehat az Arsenal jatekosait
  // ES a nevukben "ars"-t tartalmazokat is hozza. Ez szandekos: a talalat
  // legyen bo, ne kelljen elore tudni, mire keresel.
  await q.fill('#jlDoboz .kereso', 'ars');
  await q.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0, null, { timeout: 5000 });
  const arsSorok = await q.$$eval('.jlsor', a => a.map(x => x.innerText.replace(/\n/g, ' ')));
  jo(arsSorok.length > 0 && arsSorok.every(x => /ars/i.test(x)),
     'klubra keresve minden találat tartalmazza a keresett szót (névben vagy klubban)');
  jo(arsSorok.some(x => /\bARS\b/.test(x)), 'az ARS klub játékosai köztük vannak');
  await q.click('.jlsor');
  await q.waitForSelector('.proflista', { timeout: 20000 });
  jo(true, 'a PL-listából is megnyílik a profil');

  jo(qerr.length === 0, 'nincs JS-hiba a PL-oldalon'
     + (qerr.length ? ': ' + qerr.join(' | ') : ''));

  jo(perr.length === 0, 'nincs JS-hiba' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await vege(br);
})();
