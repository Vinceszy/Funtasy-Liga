const { BASE, jo, cim, inditas, vege, apiKi } = require('./kozos');
// A "mit irjunk a 0 pontos jatekosrol" logika TELJES allapottere.
// Nem talalgatott esetek: minden ertelmes kombinacio lefut, es a kimenetre
// invarianseket ellenorzunk. Ami serti oket, azt kilistazzuk.

(async () => {
  const br = await inditas();
  const p = await br.newPage();
  await p.route('**fantasy-api.mlsz.hu/**', r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof nincsPontUzenet === 'function' && typeof pontCellaHTML === 'function');

  const ki = await p.evaluate(() => {
    LIVE[900] = [];                       // 900 = elo fordulo, 901 = lezart
    const perc = m => new Date(Date.now() - m * 60000).toISOString();
    // Az ejfeles helyorzot KET valtozatban visszuk be: az MLSZ ejfelt ir, ha a
    // kezdes nincs kituzve, es annak a napja el is mulhat. A ket eset mast
    // jelent, tehat mast is kell irni rola. A datumok a MAI naphoz kepest
    // keszulnek - bedrotozva egy nap alatt elavulnanak (meg is tettek).
    const ejfel = nap => new Date(Date.now() + nap * 864e5).toISOString().slice(0, 10)
      + 'T00:00:00+02:00';
    const STARTOK = {
      'nincs':        null,
      'ejfelJovo':    ejfel(2),
      'ejfelLejart':  ejfel(-5),
      'jovo':       new Date(Date.now() + 90 * 60000).toISOString(),
      'fut30':      perc(30),
      'fut110':     perc(110),
      'regi240':    perc(240),
    };
    const BONTASOK = {
      'ures':       [],
      'perc0':      [{ name: 'Játszott perc', value: 0, points: 0 }],
      'perc90':     [{ name: 'Játszott perc', value: 90, points: 0 }],
      'pontos':     [{ name: 'Győzelem', value: 1, points: 3 }],
    };
    const sorok = [];
    for (const nogame of [false, true])
    for (const [sn, start] of Object.entries(STARTOK))
    for (const vege of [undefined, true])
    for (const played of [true, false, undefined])
    for (const [bn, nyers] of Object.entries(BONTASOK))
    for (const elo of [true, false]) {
      const round = elo ? 900 : 901;
      const uzenet = nincsPontUzenet(played, start, nyers, nogame, vege, elo);
      const cella = pontCellaHTML({ week: 0, start, vege, played, nogame }, round);
      const kotojel = cella.indexOf('–') >= 0;
      sorok.push({ nogame, sn, vege: !!vege, played: String(played), bn, elo, uzenet, kotojel,
                   allapot: meccsAllapot(start, vege) });
    }
    return sorok;
  });

  console.log('összes kombináció: ' + ki.length);

  // ---- invariansok ----
  const sertesek = {};
  const sert = (nev, s) => (sertesek[nev] = sertesek[nev] || []).push(s);
  for (const s of ki) {
    const kulcs = `nogame=${s.nogame} start=${s.sn} vege=${s.vege} played=${s.played} bontás=${s.bn} élő=${s.elo}`;
    // I1: elo forduloban futo meccsnel tilos azt allitani, hogy vege
    if (s.elo && !s.nogame && s.allapot === 'fut' && /Lejátszotta|véget ért/.test(s.uzenet))
      sert('I1 — futó meccsre azt írja, hogy vége', kulcs + '  ->  ' + s.uzenet);
    // I2: jovobeli vagy kituzetlen kezdes = meg nem kezdodott
    if (!s.nogame && (s.sn === 'jovo' || s.sn === 'ejfelJovo') && !/még nem kezdődött/.test(s.uzenet))
      sert('I2 — jövőbeli/kitűzetlen kezdésre nem azt írja, hogy még nem kezdődött', kulcs + '  ->  ' + s.uzenet);
    // I2b: a LEJART ejfeles helyorzo mar nem kezdesi idopont - nem szabad
    // tole kezdest igerni, mert a datum a multban van
    if (!s.nogame && s.sn === 'ejfelLejart' && !/elmaradt/.test(s.uzenet))
      sert('I2b — lejárt helyőrzőnél kezdést ígér', kulcs + '  ->  ' + s.uzenet);
    // I3: lezart forduloban nem allithatjuk, hogy zajlik
    if (!s.elo && /A meccs zajlik/.test(s.uzenet))
      sert('I3 — lezárt fordulóban azt írja, hogy zajlik', kulcs + '  ->  ' + s.uzenet);
    // I4: nincs meccse -> mindig azt mondja, hogy a klubnak nincs/nem volt
    // meccse (elo forduloban jelen, lezartban mult idoben)
    if (s.nogame && !/nem játszik|nem volt meccse/.test(s.uzenet))
      sert('I4 — nincs meccse, mégis mást ír', kulcs + '  ->  ' + s.uzenet);
    // I5: a sor kotojele es az uzenet nem mondhat mast. "Nincs adat" minden
    // olyan uzenet, ami NEM allitja, hogy a jatekos pontszama vegleges.
    const uzenetSzerintNincsAdat = /nem játszik|nem volt meccse|még nem kezdődött|elmaradt|A meccs zajlik|nincs rögzített esemény|feldolgozása még tart/.test(s.uzenet);
    if (s.kotojel !== uzenetSzerintNincsAdat) {
      // ELFOGADOTT KIVETEL (N3, Vince dontese): a meccs lement, de az MLSZ meg
      // nem tette be a pontokat -> a sor 0-t mutat, a bontas megmondja az
      // igazat. A sor nem tudhatja, megjott-e mar a bontas, es kideritni csak
      // jatekosonkenti lekeressel lehetne. Barmi MAS elteres viszont hiba.
      // ELFOGADOTT: a sor a tarolt 0-t mutatja, az uzenet meg azt mondja, hogy
      // magarol az esemenyrol nincs adat. Ket kulonbozo dologrol szolnak, es a
      // sor szama ilyenkor is a helyes ertek.
      const n3 = !s.kotojel && !s.nogame &&
                 /nincs rögzített esemény|feldolgozása még tart/.test(s.uzenet);
      if (!n3) sert('I5 — a kötőjel és az üzenet ellentmond', kulcs + '  ->  ' +
        (s.kotojel ? 'KÖTŐJEL' : 'szám') + ' / ' + s.uzenet);
      else (sertesek['(elfogadott N3)'] = sertesek['(elfogadott N3)'] || []).push(kulcs);
    }
  }

  const nevek = Object.keys(sertesek);
  const valodi = nevek.filter(n => n[0] !== '(');
  if (!valodi.length) console.log('\nMinden invariáns teljesül'
    + (sertesek['(elfogadott N3)'] ? ' (az elfogadott N3-kivételen kívül: '
       + sertesek['(elfogadott N3)'].length + ' eset).' : '.'));
  for (const n of valodi) {
    const l = sertesek[n];
    console.log('\n### ' + n + '  (' + l.length + ' eset)');
    // csak a kulonbozo kimeneteket mutatjuk, hogy attekintheto legyen
    const latott = new Set();
    for (const x of l) {
      const v = x.split('->')[1];
      if (latott.has(v)) continue;
      latott.add(v);
      console.log('   ' + x);
    }
  }

  // ---- attekinto tabla: elo forduloban mi jon ki ----
  console.log('\n=== ÉLŐ forduló, nincs pontja, bontás=üres ===');
  ki.filter(s => s.elo && !s.nogame && s.bn === 'ures')
    .forEach(s => console.log(`  start=${s.sn.padEnd(8)} vege=${String(s.vege).padEnd(5)} played=${s.played.padEnd(9)} `
      + `[${s.allapot.padEnd(10)}] ${s.kotojel ? '–' : '0'}  ${s.uzenet}`));

  await br.close();
  process.exit(valodi.length ? 1 : 0);
})();
