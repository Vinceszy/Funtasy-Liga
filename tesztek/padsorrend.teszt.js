const { BASE, jo, inditas, vege } = require('./kozos');
// A PAD SORRENDJE AZ FPL CSERE-SORRENDJE, es nem rendezheto at.
//
// A fordulo vegen az FPL az elso olyan padost allitja be a nem jatszo kezdo
// helyere, aki formaciolag befer - tehat a pad sorrendje maga az informacio.
// A tarolt keret az FPL sajat sorrendjet orzi (picks 12-15). Az oldal
// korabban POSZT szerint rendezte a padot is, es ezzel pont ezt dobta el.
//
// A kezdoket viszont TOVABBRA IS poszt szerint rendezzuk: ott a sorrendnek
// nincs jelentese, es a kapus-vedo-kozeppalyas-csatar felepites olvashatobb.
(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await p.route('**premierleague.com/**', route => route.fulfill({
    status: 200, contentType: 'application/json', body: '{}' }));
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof sqcolHTML === 'function' && Object.keys(PLAYERS).length > 0,
    null, { timeout: 20000 });

  // Valodi jatekosokat valasztunk posztonkent, hogy a poszt-rendezes merheto
  // legyen; a pad SZANDEKOSAN nem poszt-sorrendben all.
  const valasztas = await p.evaluate(() => {
    const poszt = {};
    for (const id in PLAYERS){
      const j = PLAYERS[id];
      (poszt[j.p] = poszt[j.p] || []).push(+id);
    }
    return poszt;
  });
  const [GKP, DEF, MID, FWD] = ['GKP', 'DEF', 'MID', 'FWD'].map(k => valasztas[k] || []);
  jo(GKP.length && DEF.length && MID.length && FWD.length, 'van mind a négy poszt a törzsadatban');

  // pad: kapus, csatar, vedo, kozeppalyas - egyetlen poszt-rendezes sem adja
  // vissza ezt a sorrendet, tehat ha megmarad, akkor tenyleg nem rendezunk
  const padSorrend = [GKP[1], FWD[1], DEF[2], MID[2]];
  const kezdok = [MID[0], FWD[0], GKP[0], DEF[0]];   // szandekosan kevert
  const lista = [
    ...kezdok.map(e => ({ e, b: false, pts: 1 })),
    ...padSorrend.map(e => ({ e, b: true, pts: 1 })),
  ];

  // gw-t adunk at, hogy a sorok data-e attributumot kapjanak: azonosito
  // szerint hasonlitunk, nem nev szerint (a nev mellett a klub rovidneve is
  // ott van a .nm-ben).
  const dom = await p.evaluate(([lista]) => {
    const d = document.createElement('div');
    d.innerHTML = sqcolHTML('T', lista, 'Teszt', 99);
    const sqcol = d.querySelector('.sqcol');
    const padE = [], kezdoE = [];
    let padban = false;
    for (const x of sqcol.children){
      if (x.classList.contains('subhead')) { padban = true; continue; }
      if (!x.classList.contains('plr') || x.classList.contains('plrfej')) continue;
      (padban ? padE : kezdoE).push(+x.dataset.e);
    }
    return { padE, kezdoE };
  }, [lista]);

  console.log('   pad bemenet:   ' + JSON.stringify(padSorrend));
  console.log('   pad a DOM-ban: ' + JSON.stringify(dom.padE));
  jo(dom.padE.length === padSorrend.length && dom.kezdoE.length === kezdok.length,
     'minden sor kirajzolodott (' + dom.kezdoE.length + ' kezdo + ' + dom.padE.length + ' pad)');
  jo(dom.padE.length === padSorrend.length
     && dom.padE.every((x, i) => x === padSorrend[i]),
     'a pad pontosan a bemeneti (FPL-) sorrendben all - nincs poszt szerinti rendezes');
  // ellenorzes az ellenorzesre: poszt szerint rendezve MAS sorrend jonne ki,
  // tehat az allitas nem trivialisan igaz
  const rang = { GKP: 0, DEF: 1, MID: 2, FWD: 3 };
  const poszt = await p.evaluate(([ids]) => ids.map(e => PLAYERS[e].p), [padSorrend]);
  jo(poszt.some((x, i) => i && rang[poszt[i - 1]] > rang[x]),
     'a teszt pad-sorrendje tenyleg NEM poszt-sorrend: ' + JSON.stringify(poszt));

  const kPoszt = await p.evaluate(([ids]) => ids.map(e => PLAYERS[e].p), [dom.kezdoE]);
  console.log('   kezdok a DOM-ban: ' + JSON.stringify(kPoszt));
  jo(kPoszt.length === kezdok.length
     && kPoszt.every((x, i) => !i || rang[kPoszt[i - 1]] <= rang[x]),
     'a kezdok viszont poszt szerint rendezve maradnak');

  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr));
  await vege(br);
})();
