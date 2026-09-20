const { BASE, jo, cim, inditas, vege } = require('./kozos');
// The round preview / round summary strip on the match page.
//
// The one thing this strip must never do is get in the way of the numbers.
// It sits above the squad columns, so every assertion here is about that:
// it comes collapsed, it costs one line, the columns stay on screen, and a
// fixture nobody wrote about gets no strip at all.
//
// Also recorded: the text matches articles.json paragraph for paragraph,
// the open state survives a redraw (a live round redraws the body every
// few seconds), and on a round with no squads yet the preview comes open,
// because there it is the only thing on the page.

// a played round with summaries, and a fixture from it
const R = 7, HAZAI = 'Bence', VENDEG = 'Csendi';
// a fixture from the same round that has no article
const URES_R = 4, UH = 'Bazsa', UV = 'Csendi';

(async () => {
  const br = await inditas();
  const hibak = [];

  for (const [w, h, cimke] of [[1000, 900, 'GÉP'], [390, 844, 'MOBIL']]) {
    const p = await br.newPage({ viewport: { width: w, height: h } });
    p.on('pageerror', e => hibak.push(cimke + ': ' + e.message));
    for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
      await p.route(m, r => r.abort());
    await p.goto(BASE + 'nb1/');
    await p.waitForSelector('#table tr');
    // the strip only renders once articles.json is in - the page loads it
    // beside everything else, so wait for it rather than for a timer
    await p.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                            null, { timeout: 20000 });
    await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [HAZAI, VENDEG, R]);
    await p.waitForSelector('#mBody .plr');
    await p.waitForSelector('#mBody .artstrip');

    cim(cimke);
    const sav = p.locator('#mBody .artstrip');
    const meret = async () => p.evaluate(() => {
      const s = document.querySelector('#mBody .artstrip');
      const q = document.querySelector('#mBody .sqwrap');
      return { sav: s.getBoundingClientRect().height,
               fej: s.querySelector('.artstriphead').getBoundingClientRect().height,
               keretTeteje: q.getBoundingClientRect().top,
               nyitva: s.open };
    });

    const zart = await meret();
    jo(zart.nyitva === false, 'lezárt forduló: a sáv CSUKVA jön');
    jo(zart.fej < 48, `a csukott fejléc egy sor (${Math.round(zart.fej)} px)`);
    jo(zart.sav < 60, `a csukott sáv nem nyom le semmit (${Math.round(zart.sav)} px)`);
    jo(zart.keretTeteje < h,
       `a keret-oszlopok a képernyőn maradnak (tetejük ${Math.round(zart.keretTeteje)} px, ` +
       `ablak ${h} px)`);
    // The lead must stay ONE line however long it is - that is what keeps
    // the collapsed height fixed. A short lead fits on a wide screen, so
    // the clipping is measured with a lead that cannot possibly fit.
    const csonkolt = await p.evaluate(() => {
      const l = document.querySelector('#mBody .artstriplead');
      const eredeti = l.textContent, magas = l.getBoundingClientRect().height;
      l.textContent = 'sokkal hosszabb felütés '.repeat(40);
      const r = { egySor: magas < 26,
                  hosszanIsEgySor: l.getBoundingClientRect().height < 26,
                  csonk: l.scrollWidth > l.clientWidth };
      l.textContent = eredeti;
      return r;
    });
    jo(csonkolt.egySor, 'a felütés egyetlen sorban fut');
    jo(csonkolt.hosszanIsEgySor && csonkolt.csonk,
       'a bármilyen hosszú felütés is egy sor marad, a vége levágva');

    // ---- kinyitás ----
    await sav.locator('.artstriphead').click();
    await p.waitForTimeout(120);
    const nyitott = await meret();
    jo(nyitott.nyitva === true, 'kattintásra kinyílik');
    jo(nyitott.sav > zart.sav + 40, `a nyitott sáv nagyobb (${Math.round(zart.sav)} → ` +
       `${Math.round(nyitott.sav)} px)`);
    jo(nyitott.keretTeteje > zart.keretTeteje,
       'a keret-oszlopok CSAK nyitáskor csúsznak lejjebb');

    // the text is the file's text, paragraph for paragraph
    const egyezik = await p.evaluate(async ([a, b, r]) => {
      const j = await (await fetch('../articles.json')).json();
      const c = j.leagues.nb1[r].summary[a + '|' + b];
      const pk = [...document.querySelectorAll('#mBody .artstripbody p')].map(x => x.textContent);
      return { db: pk.length, vart: c.text.length,
               elso: pk[0] === c.text[0], utolso: pk[pk.length - 1] === c.text[c.text.length - 1],
               felutes: document.querySelector('#mBody .artstriplead').textContent === c.short,
               cimke: document.querySelector('#mBody .artstriptag').textContent };
    }, [HAZAI, VENDEG, String(R)]);
    jo(egyezik.db === egyezik.vart && egyezik.db > 0,
       `minden bekezdés kint van (${egyezik.db}/${egyezik.vart})`);
    jo(egyezik.elso && egyezik.utolso, 'a szöveg szó szerint a fájlé');
    jo(egyezik.felutes, 'a csukott sávban a rövid változat áll');
    jo(egyezik.cimke === 'Összefoglaló', `lezárt fordulón „Összefoglaló" a címke (${egyezik.cimke})`);

    // ---- becsukás: nem marad utána semmi ----
    await sav.locator('.artstriphead').click();
    await p.waitForTimeout(120);
    const ujraZart = await meret();
    jo(Math.abs(ujraZart.keretTeteje - zart.keretTeteje) < 2,
       'becsukás után a keret-oszlopok visszaállnak a helyükre');

    // ---- az újrarajzolás nem csukja be a nézőre ----
    await sav.locator('.artstriphead').click();
    await p.waitForTimeout(120);
    await p.evaluate(() => meccsTest());
    await p.waitForSelector('#mBody .artstrip');
    jo(await p.evaluate(() => document.querySelector('#mBody .artstrip').open),
       'újrarajzolás után is nyitva marad (élő fordulón percenként újraépül a test)');

    // ---- cikk nélküli meccs: NINCS sáv ----
    await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [UH, UV, URES_R]);
    await p.waitForSelector('#mBody .plr');
    jo(await p.locator('#mBody .artstrip').count() === 0,
       'cikk nélküli meccsen nyoma sincs a sávnak');
    jo(await p.evaluate(() => document.querySelector('#mBody').firstElementChild
                              .classList.contains('meccsfej')),
       'ilyenkor a meccsfej az első elem — a nézet változatlan');

    await p.close();
  }

  // ---- beharangozó olyan fordulón, ahol még nincs keret ----
  const p = await br.newPage({ viewport: { width: 1000, height: 900 } });
  p.on('pageerror', e => hibak.push('BEHARANGOZÓ: ' + e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
    await p.route(m, r => r.abort());
  // a round the collector has not archived: there is no squad file for it
  await p.route('**/keretek/*.json*', r => r.fulfill({ status: 404, body: '' }));
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#table tr');
  await p.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                          null, { timeout: 20000 });
  const [bh, bv] = await p.evaluate(async () => {
    const j = await (await fetch('../articles.json')).json();
    return Object.keys(j.leagues.nb1['9'].preview)[0].split('|');
  });
  cim('BEHARANGOZÓ (nincs még keret)');
  await p.evaluate(([a, b]) => showMatchRound(a, b, 9), [bh, bv]);
  await p.waitForSelector('#mBody .artstrip');
  jo(await p.evaluate(() => document.querySelector('#mBody .artstrip').open),
     'keret nélküli fordulón a beharangozó NYITVA jön (nincs mit eltakarnia)');
  jo(await p.evaluate(() => document.querySelector('#mBody .artstriptag').textContent)
       === 'Beharangozó', 'a címke „Beharangozó"');
  jo(await p.evaluate(() => !!document.querySelector('#mBody .loading')),
     'a „még nem kezdődött el" üzenet mellette marad');
  // the reader's own click wins over the default
  await p.locator('#mBody .artstriphead').click();
  await p.waitForTimeout(120);
  await p.evaluate(([a, b]) => showMatchRound(a, b, 9), [bh, bv]);
  await p.waitForSelector('#mBody .artstrip');
  jo(await p.evaluate(() => !document.querySelector('#mBody .artstrip').open),
     'ha a néző becsukta, becsukva is marad');

  await p.close();

  // ---- ugyanaz a sav a PL-oldalon ----
  // A PL-hez meg nincs irott cikk, a bekotest megis meg kell merni: a
  // ket oldal ugyanazt a FunTasy.matchArticle-t hivja, csak masik
  // liga-kulccsal es azonosito helyett nevvel. A tarolot a lapon
  // allitjuk be - igy nem kell hamis fajlt tenni a repoba.
  const q = await br.newPage({ viewport: { width: 1000, height: 900 } });
  q.on('pageerror', e => hibak.push('PL: ' + e.message));
  for (const m of ['**premierleague.com/**', '**corsproxy.io/**', '**allorigins**'])
    await q.route(m, r => r.abort());
  await q.goto(BASE + 'pl/');
  await q.waitForSelector('#table tr');
  await q.waitForFunction(() => Object.keys(SCHEDULE).length > 0, null, { timeout: 20000 });
  cim('PL');
  const plm = await q.evaluate(() => {
    // az utolso olyan fordulo, aminek van lejatszott meccse
    const gw = Object.keys(SCHEDULE).map(Number).sort((a, b) => b - a)
                 .find(g => (SCHEDULE[g] || []).some(played));
    const [h, v] = SCHEDULE[gw][0];
    ARTICLES = { updated: null, leagues: { pl: { [gw]: { summary: {
      [nev(h) + '|' + nev(v)]: { text: ['Elso bekezdes.', 'Masodik bekezdes.'],
                                 short: 'Egy mondat a sav szamara.', source: 'manual' } } } } } };
    showMatch(h, v, gw, 'root');
    return { gw, h, v };
  });
  await q.waitForSelector('#mBody .artstrip');
  const pl = await q.evaluate(() => {
    const s = document.querySelector('#mBody .artstrip');
    const w = document.querySelector('#mBody .sqwrap');
    return { nyitva: s.open, magas: s.getBoundingClientRect().height,
             cimke: s.querySelector('.artstriptag').textContent,
             felutes: s.querySelector('.artstriplead').textContent,
             keretTeteje: w ? w.getBoundingClientRect().top : null };
  });
  jo(pl.nyitva === false, `PL: a sáv csukva jön (${plm.gw}. forduló)`);
  jo(pl.magas < 60, `PL: a csukott sáv egy sor (${Math.round(pl.magas)} px)`);
  jo(pl.cimke === 'Összefoglaló' && pl.felutes === 'Egy mondat a sav szamara.',
     'PL: a címke és a felütés a tárolóból jön');
  jo(pl.keretTeteje !== null && pl.keretTeteje < 900,
     `PL: a keret-oszlopok a képernyőn maradnak (${Math.round(pl.keretTeteje)} px)`);
  await q.locator('#mBody .artstriphead').click();
  await q.waitForTimeout(120);
  jo(await q.$$eval('#mBody .artstripbody p', n => n.length) === 2,
     'PL: kinyitva mindkét bekezdés kint van');
  await q.evaluate(([h, v, gw]) => showMatch(h, v, gw, 'root'), [plm.h, plm.v, plm.gw]);
  await q.waitForSelector('#mBody .artstrip');
  jo(await q.evaluate(() => document.querySelector('#mBody .artstrip').open),
     'PL: újrarajzolás után is nyitva marad');

  // ---- a lezart fordulon MINDKET szoveg kint marad ----
  // A lefujas nem avultatja el a beharangozot: az mondja meg, mi volt a kerdes
  // a meccs elott, az osszefoglalo meg azt, mi lett a valasz - egymas alatt a
  // ketto tobbet er. A parost a TAROLOBOL keressuk ki, nem beirjuk: igy a
  // teszt nem avul el azzal, hogy melyik fordulohoz mit irtunk.
  cim('Lezárt forduló: mindkét szöveg');
  const mk = await br.newPage({ viewport: { width: 1000, height: 900 } });
  mk.on('pageerror', e => hibak.push('MINDKETTO: ' + e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
    await mk.route(m, r => r.abort());
  await mk.goto(BASE + 'nb1/');
  await mk.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                          null, { timeout: 20000 });
  const par = await mk.evaluate(async () => {
    const j = await (await fetch('../articles.json')).json();
    const nb1 = (j.leagues || {}).nb1 || {};
    for (const r of Object.keys(nb1).sort((a, b) => b - a)) {
      const k = nb1[r];
      if (!k.summary || !k.preview) continue;
      const p = Object.keys(k.summary).find(x => k.preview[x]);
      if (p) return { r: +r, felek: p.split('|') };
    }
    return null;
  });
  if (!par) {
    jo(false, 'nincs olyan forduló, amihez összefoglaló ÉS beharangozó is van');
  } else {
    await mk.evaluate(([h, v, r]) => showMatchRound(h, v, r),
                     [par.felek[0], par.felek[1], par.r]);
    await mk.waitForSelector('#mBody .artstrip');
    const cimkek = await mk.$$eval('#mBody .artstriptag', n => n.map(x => x.textContent));
    jo(JSON.stringify(cimkek) === JSON.stringify(['Összefoglaló', 'Beharangozó']),
       `a ${par.r}. fordulón mindkettő ott van, az összefoglaló elöl — ` + cimkek.join(', '));
    jo(await mk.$$eval('#mBody .artstrip', n => n.filter(x => x.open).length) === 0,
       'és mindkettő csukva jön, nem tolja el a kereteket');
  }
  await mk.close();

  // ---- a ZARAS-KAPU: le nem zart fordulo osszefoglaloja nem latszik ----
  // Amig a fordulo nem vegleges, a pontok meg elmozdulhatnak (NB1: meccs
  // utani igazitasok, Draft: kulon veglegesites), tehat egy "X nyert
  // ennyivel" szoveg hazudhat. A beharangozora ez nem all: az arrol szol,
  // ami jon. A szoveget a lapon allitjuk be, hogy a repoban ne kelljen
  // hozza le nem zart fordulos cikket tartani.
  for (const [ut, cimke, vazlat] of [['nb1/', 'KAPU — NB1', false],
                                     ['nb1/?draft=1', 'KAPU — NB1, ?draft=1', true],
                                     ['pl/', 'KAPU — PL', false],
                                     ['pl/?draft=1', 'KAPU — PL, ?draft=1', true]]) {
    const g = await br.newPage({ viewport: { width: 1000, height: 900 } });
    g.on('pageerror', e => hibak.push(cimke + ': ' + e.message));
    for (const m of ['**mlsz.hu/**', '**premierleague.com/**',
                     '**corsproxy.io/**', '**allorigins**'])
      await g.route(m, r => r.abort());
    await g.goto(BASE + ut);
    await g.waitForSelector('#table tr');
    cim(cimke);
    const nb1 = ut.startsWith('nb1');
    // AZ ELOFELTETELT KIVARJUK, nem a tablazatra hagyatkozunk: a fejlec-sor
    // mar a betoltes elott ott all, tehat a '#table tr' akkor is teljesul,
    // amikor a fordulo-adat meg nincs meg. Igy a kereses ures allapotban
    // futott le, es a teszt "nincs ilyen fordulo"-val bukott - felrevezetoen,
    // mert nem a kapuval volt baj.
    //
    // Az NB1-en a MENETRENDRE varunk, nem az elo fordulora: a kapu barmelyik
    // le nem zart fordulon vizsgalhato, es ELO FORDULO NINCS MINDIG. Amikor a
    // bajnokseg szunetel, a LIVE ures marad, es a teszt ettol allt meg -
    // holott a vizsgalt viselkedessel semmi baj nem volt.
    await g.waitForFunction(nb1 => nb1 ? (typeof SCHEDULE !== 'undefined'
                                          && Object.keys(SCHEDULE).length > 0)
                                       : (typeof HIST !== 'undefined'
                                          && Object.keys(HIST).length > 0),
                            nb1, { timeout: 20000 });
    const nyitott = await g.evaluate(async nb1 => {
      // ugyanarra a meccsre MINDKET fajta szoveg megvan: igy az is latszik,
      // hogy a kapu valaszt kozuluk, nem csak elrejt
      const tarol = (liga, r, h, v) => ({ updated: null, leagues: { [liga]: { [r]: {
        summary: { [h + '|' + v]: { text: ['Osszefoglalo bekezdes.'],
                                    short: 'Osszefoglalo.', source: 'manual' } },
        preview: { [h + '|' + v]: { text: ['Beharangozo bekezdes.'],
                                    short: 'Beharangozo.', source: 'manual' } } } } } });
      if (nb1) {
        // a legkozelebbi MEG NEM LEZART fordulo - fut vagy csak ezutan jon
        const r = Object.keys(SCHEDULE).map(Number).sort((a, b) => a - b)
                    .find(x => !roundClosed(x) && (SCHEDULE[x] || []).length);
        if (!r) return null;
        const [h, v] = SCHEDULE[r][0];
        ARTICLES = tarol('nb1', r, h, v);
        await showMatchRound(h, v, r);
        return { r, zart: roundClosed(r) };
      }
      const gw = Object.keys(HIST).map(Number).sort((a, b) => b - a)
                   .find(x => !roundClosed(x) && (SCHEDULE[x] || []).length);
      if (!gw) return null;
      const [h, v] = SCHEDULE[gw][0];
      ARTICLES = tarol('pl', gw, nev(h), nev(v));
      showMatch(h, v, gw, 'root');
      return { r: gw, zart: roundClosed(gw) };
    }, nb1);
    jo(!!nyitott && nyitott.zart === false,
       `van le nem zárt forduló keretekkel (${nyitott && nyitott.r}.)`);
    await g.waitForSelector('#mBody .artstrip', { timeout: 15000 });
    const allapot = await g.evaluate(() => {
      const s = document.querySelector('#mBody .artstrip');
      return { cimke: s.querySelector('.artstriptag').textContent,
               vazlat: s.classList.contains('draft'),
               szoveg: s.querySelector('.artstripbody p').textContent };
    });
    if (!vazlat) {
      jo(allapot.cimke === 'Beharangozó' && allapot.szoveg === 'Beharangozo bekezdes.',
         `le nem zárt fordulón CSAK a beharangozó látszik (${allapot.cimke})`);
      jo(allapot.vazlat === false, 'publikált szövegen nincs vázlat-jelzés');
    } else {
      jo(allapot.cimke === 'Összefoglaló · vázlat' && allapot.szoveg === 'Osszefoglalo bekezdes.',
         `?draft=1 felengedi a kaput, és vázlatnak jelöli (${allapot.cimke})`);
      jo(allapot.vazlat === true, 'a vázlat kap saját jelzést (szaggatott keret)');
    }
    await g.close();
  }

  // ---- A vazlat-fajl: ?draft=1 NELKUL a lap le sem keri ----
  // A meg nem publikalt szoveg kulon fajlban all. Az allitas nem fugghet
  // attol, hogy epp van-e benne valami: a merest sajat, HAMIS vazlat-fajllal
  // vegezzuk, olyan meccsre, amirol a kint levo fajlban nincs szo.
  const VR = 6, VH = 'Bazsa', VV = 'Sámsi';        // lezart fordulo, nincs rola cikk
  for (const [mod, cimke, varunk] of [['nb1/', 'VÁZLAT-FÁJL — zárva', false],
                                      ['nb1/?draft=1', 'VÁZLAT-FÁJL — ?draft=1', true]]) {
    const g = await br.newPage({ viewport: { width: 1000, height: 900 } });
    g.on('pageerror', e => hibak.push(cimke + ': ' + e.message));
    for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
      await g.route(m, r => r.abort());
    let kertek = 0;
    await g.route('**/articles-draft.json*', r => {
      kertek++;
      return r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ updated: null, leagues: { nb1: { [VR]: { summary: {
          [VH + '|' + VV]: { text: ['Vazlat bekezdes.'], short: 'Vazlat.',
                             source: 'manual' } } } } } }) });
    });
    await g.goto(BASE + mod);
    await g.waitForSelector('#table tr');
    await g.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                            null, { timeout: 20000 });
    cim(cimke);
    jo(kertek === (varunk ? 1 : 0),
       `a lap ${varunk ? 'lekéri' : 'LE SEM KÉRI'} a vázlat-fájlt (${kertek} kérés)`);
    await g.evaluate(([a, b, r]) => showMatchRound(a, b, r), [VH, VV, VR]);
    await g.waitForSelector('#mBody .plr', { timeout: 20000 });
    const van = await g.locator('#mBody .artstrip').count() > 0;
    jo(van === varunk, `a vázlatos meccsen ${varunk ? 'ott a sáv' : 'NINCS sáv'}`);
    if (varunk)
      jo(await g.evaluate(() => document.querySelector('#mBody .artstripbody p').textContent)
           === 'Vazlat bekezdes.', 'a vázlat szövege jön elő');
    // a kint lévő cikk ettől függetlenül látszik: a vázlat ráolvad, nem kicseréli
    await g.evaluate(() => showMatchRound('Bence', 'Csendi', 7));
    await g.waitForSelector('#mBody .plr', { timeout: 20000 });
    jo(await g.locator('#mBody .artstrip').count() === 1,
       'a publikált cikk mindkét módban ott van');
    await g.close();
  }

  hibak.forEach(x => jo(false, 'oldalhiba: ' + x));
  await vege(br);
})();
