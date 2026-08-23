const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// A magyarszabaly (+10) elhelyezese a kulonbseg-nezetben.
// Ket eset: ha mindket keret ugyanannyit kap, kozos tetel; ha nem, akkor
// mindket oldalon az eltero csoportba kerul (a masiknal 0-val).
const szam = t => parseFloat(String(t).replace(/[^\d,.-]/g, '').replace(/\.(?=\d{3}\b)/g, '').replace(',', '.'));

(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 1100, height: 1000 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#table tr');
  const HIST = await p.evaluate(async () => (await (await fetch('../squad_history.json')).json()).rounds || {});

  // Csak azokat a parositasokat nezzuk, amelyekhez van tarolt keret. A
  // "kozos-e a szabaly" kerdes eldontheto rendereles nelkul is: a
  // magyarBonus a ket kezdo tizenegybol szamol.
  const jeloltek = await p.evaluate((HIST) => {
    const ki = { kozos: null, kulon: null };
    for (const [r, ms] of Object.entries(SCHEDULE)) {
      const keretek = HIST[r];
      if (!keretek) continue;
      for (const [h, v] of ms) {
        const A = keretek[h], B = keretek[v];
        if (!A || !B) continue;
        const mb = l => magyarBonus(l.filter(x => !x.sub)).pts;
        const kulcs = mb(A) === mb(B) ? 'kozos' : 'kulon';
        if (!ki[kulcs]) ki[kulcs] = [h, v, +r];
      }
      if (ki.kozos && ki.kulon) break;
    }
    return ki;
  }, HIST);
  console.log('jelöltek:', JSON.stringify(jeloltek));

  let szintetikus = false;
  for (const kulcs of ['kozos', 'kulon']) {
    let cel = jeloltek[kulcs];
    if (!cel) {
      // A valos adatokban minden keret teljesiti a szabalyt, ezert a "csak az
      // egyik oldalon jar" esetet szandekosan eloallitjuk: az egyik szakvezeto
      // keretebol kivesszuk a magyar jelolest.
      const alap = jeloltek.kozos;
      if (!alap) { console.log('\n(nincs vizsgalhato meccs)'); continue; }
      const [h0, v0, r0] = alap;
      // A HIST mar be van toltve az elozo meccs megnyitasakor: kozvetlenul
      // atirjuk, majd ujrarajzoltatjuk a meccset.
      await p.evaluate(([r0, h0]) => {
        HIST[String(r0)][h0].forEach(x => { x.hun = false; x.u21 = false; });
      }, [r0, h0]);
      szintetikus = true;
      jeloltek.kulon = alap;
      console.log(`\n(szintetikus eset: ${h0} keretebol kivettuk a magyar jelolest)`);
    }
    const cel2 = jeloltek[kulcs];
    if (!cel2) continue;
    const [h, v, r] = cel2;
    await p.evaluate(([h, v, r]) => showMatchRound(h, v, r), cel2);
    await p.waitForSelector('.sqcol .plr', { timeout: 15000 });
    if ((await p.$$('.szakasz')).length === 0) { await p.click('#elteresGomb'); await p.waitForTimeout(300); }

    const kozosBan = await p.locator('.sqcol .kozosresz .szabalysor').count();
    const eltBan = await p.locator('.sqcol > .szabalysor').count();
    const mobil = await p.locator('.mobilkozos .szabalysor').count();
    console.log(`\n--- ${kulcs === 'kozos' ? 'KÖZÖS szabály' : 'CSAK AZ EGYIK OLDALON'}: ${h} vs ${v}, ${r}. forduló ---`);
    console.log('   szabálysor — közös részben:', kozosBan, '| eltérők közt:', eltBan, '| mobil blokkban:', mobil);
    if (kulcs === 'kozos') {
      jo(kozosBan === 2 && eltBan === 0, 'közös szabály: mindkét oszlop közös részében, az eltérők közt sehol');
      jo(mobil === 1, 'a mobil közös blokkban egyszer szerepel');
    } else {
      jo(kozosBan === 0 && eltBan === 2, 'eltérő szabály: mindkét oszlopban az eltérők közt, saját sorként');
      jo(mobil === 0, 'a mobil közös blokkban nem szerepel');
    }

    const szamlak = await p.$$eval('.sqcol', cols => cols.map(c => ({
      fejlec: (c.querySelector('h3 span') || {}).textContent,
      sorok: [...c.querySelectorAll('.osszesito')].map(o =>
        [o.querySelector('span').textContent.trim(), o.querySelector('b').textContent.trim()]),
    })));
    szamlak.forEach((c, i) => {
      const kozos = szam(c.sorok[0][1]), elt = szam(c.sorok[1][1]), ossz = szam(c.sorok[2][1]);
      // A szintetikus esetben az elso oszlopbol szandekosan kivettuk a +10-et,
      // a hivatalos pontszam viszont meg tartalmazza - ott ennyi a kulonbseg.
      const varhato = (szintetikus && i === 0) ? ossz - 10 : ossz;
      jo(Math.abs(kozos + elt - varhato) < 0.005,
        `${i + 1}. oszlop számlája: ${kozos} + ${elt} = ${varhato}`
        + (varhato !== ossz ? ` (+10 hivatalos, a szintetikus keretben nem jár)` : ''));
      jo(Math.abs(ossz - szam(c.fejlec)) < 0.005, `${i + 1}. oszlop végösszege = a fejléc pontja (${c.fejlec})`);
    });
    await p.click('.mclose');
    await p.waitForTimeout(150);
  }

  console.log('\npageerror:', perr.length ? perr : 'nincs');
  await br.close();
  process.exit(hibak.length ? 1 : 0);
})();
