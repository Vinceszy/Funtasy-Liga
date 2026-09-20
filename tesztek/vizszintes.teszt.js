const { BASE, jo, cim, inditas, vege } = require('./kozos');
// EGYETLEN OLDAL SEM LOG KI OLDALRA.
//
// Korabban ezt egy `html,body{overflow-x:hidden}` szabaly "oldotta meg":
// ami kilogott, azt egyszeruen levagta. Csakhogy az iOS Safari a html-re
// tett vizszintes vagastol sajat gorgeto-dobozza teszi az elemet, es a
// lendulettel valo gorgetes elromlik - a lap nem indul el, megremeg,
// elindul, majd visszaszalad. A vagas tehat nem ingyenes.
//
// Ezert a vagas helyett MERJUK, amit vedeni akart. Ez a teszt az igazi
// allitas: a tartalom elfer. Ha egy uj elem kilog, itt derul ki, nem pedig
// ugy, hogy csendben le van vagva a szeleAllitas.
const SZELESSEGEK = [320, 360, 390, 412];

(async () => {
  const br = await inditas();
  const hibak = [];
  for (const w of SZELESSEGEK) {
    const ctx = await br.newContext({ viewport: { width: w, height: 820 },
                                      deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const p = await ctx.newPage();
    p.on('pageerror', e => hibak.push(`${w}px: ${e.message}`));
    for (const m of ['**mlsz.hu/**', '**premierleague.com/**', '**corsproxy.io/**',
                     '**allorigins**', '**workers.dev/**', '**fonts.googleapis.com/**',
                     '**fonts.gstatic.com/**'])
      await p.route(m, r => r.abort());
    cim(w + ' pixel');

    // A hibauzenet NEVEZZE MEG a bunost: "kilog 12 pixellel" onmagaban nem
    // mondja meg, mit kell megjavitani.
    const mer = async cimke => {
      const r = await p.evaluate(() => {
        const d = document.documentElement;
        const tul = d.scrollWidth - d.clientWidth;
        const bunos = tul > 0 ? [...document.querySelectorAll('*')]
          .filter(e => e.getBoundingClientRect().right > d.clientWidth + 1)
          .slice(0, 3).map(e => e.tagName.toLowerCase()
            + (e.className ? '.' + String(e.className).split(/\s+/)[0] : '')) : [];
        return { tul, bunos };
      });
      jo(r.tul === 0, `${cimke}: nem lóg ki oldalra`
         + (r.tul ? ` — ${r.tul} px, okozza: ${r.bunos.join(', ')}` : ''));
    };

    for (const [ut, cimke] of [['', 'kezdőlap'], ['valtozasok/', 'változásnapló'],
                               ['nemzethy/', 'magazin (közös)'],
                               ['nemzethy/?liga=nb1', 'magazin (NB1)'],
                               ['nemzethy/?liga=pl', 'magazin (PL)']]) {
      await p.goto(BASE + ut);
      await p.waitForTimeout(700);
      await mer(cimke);
    }

    // A liga-oldalak a NYITOTT nezetekkel egyutt: ott all a szeles tartalom
    // (keret-oszlopok, tablazat), tehat ott a legkonnyebb kilogni.
    await p.goto(BASE + 'nb1/');
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await mer('NB1 főoldal');
    await p.evaluate(() => showMatchRound('Bence', 'Csendi', 7));
    await p.waitForSelector('#mBody .plr', { timeout: 20000 });
    await mer('NB1 meccs-adatlap');
    if (await p.locator('#elteresGomb').count()) {
      await p.click('#elteresGomb');
      await p.waitForTimeout(250);
      await mer('NB1 különbségek');
    }

    await p.goto(BASE + 'pl/');
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await p.waitForFunction(() => typeof HIST !== 'undefined' && Object.keys(HIST).length > 0,
                            null, { timeout: 20000 });
    await mer('PL főoldal');
    await p.evaluate(() => {
      const gw = Math.max(...Object.keys(SCHEDULE).map(Number)
        .filter(g => (SCHEDULE[g] || []).some(m => m[2] != null)));
      const [h, v] = SCHEDULE[gw][0];
      showMatch(h, v, gw, 'root');
    });
    await p.waitForSelector('#mBody .plr', { timeout: 20000 });
    await mer('PL meccs-adatlap');
    await ctx.close();
  }
  hibak.forEach(x => jo(false, 'oldalhiba: ' + x));
  await vege(br);
})();
