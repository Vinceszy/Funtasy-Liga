const { BASE, jo, inditas, vege } = require('./kozos');
// A jatekos meccse a pont-bontas folott az NB1-en (meccsek.json-bol).
//
// Amit rogzit:
//  - lezart meccs: klubok + eredmeny + "vege"
//  - el nem kezdodott meccs: NINCS kitalalt 0-0, csak a ket klub
//  - a 180 perces idokorlaton beluli meccs: "a meccs zajlik" (allapot-kapu)
//  - reg elkezdodott, de eredmeny nelkuli meccs: "vege" cimke eredmeny nelkul
//  - masik klub meccse nem jelenik meg; dupla meccsu klubnal ket sor
//  - a bontasHTML a meccs-sort a tablazat FOLE teszi; nogame-nel nincs sor
(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await p.route('**fantasy-api.mlsz.hu/**', route => {
    const u = decodeURIComponent(route.request().url());
    if (/game-player-stats/.test(u))
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ data: [
          { value: 1, points: 3, competition_stat_config: { name: 'Győzelem' } },
          { value: 77, points: 0, competition_stat_config: { name: 'Játszott perc' } },
        ] }) });
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{"data":[]}' });
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof meccsSorokHTML === 'function', null, { timeout: 20000 });

  const m = await p.evaluate(async () => {
    const ora = 3600e3, nap = 24 * ora;
    const iso = t => new Date(t).toISOString().replace(/\.\d+Z$/, '+00:00');
    MECCSEK = { 7: [
      { h: 'VASAS', v: 'ETO', hp: 2, vp: 2, vege: true, start: iso(Date.now() - 3 * nap) },
      { h: 'PAFC',  v: 'MTK', start: iso(Date.now() + 2 * nap) },          // meg elotte
      { h: 'ZTE',   v: 'ETO', start: iso(Date.now() - 1 * ora) },          // most zajlik
      { h: 'DVSC',  v: 'PAKS', start: iso(Date.now() - 6 * ora) },         // lement, eredmeny meg nincs
    ] };
    const sorok = html => {
      const d = document.createElement('div');
      d.innerHTML = html;
      return [...d.querySelectorAll('.bontasmeccs')]
        .map(x => [x.children[0].textContent.trim().replace(/\s+/g, ' '),
                   x.children[1].textContent.trim()]);
    };
    // integracio: a bontasHTML a meccs-sort a tablazat FOLE teszi
    const teljes = await bontasHTML({ own: 'X', nm: 'Y', r: '7', cp: '555',
                                      tm: 'VASAS', pl: '1', vg: '1' });
    const d2 = document.createElement('div'); d2.innerHTML = teljes;
    const nogame = await bontasHTML({ own: 'X', nm: 'Y', r: '7', cp: '556',
                                      tm: 'VASAS', pl: '0', ng: '1' });
    return {
      lezart: sorok(meccsSorokHTML('VASAS', 7)),
      elotte: sorok(meccsSorokHTML('PAFC', 7)),
      zajlik: sorok(meccsSorokHTML('ZTE', 7)),
      lement: sorok(meccsSorokHTML('DVSC', 7)),
      dupla:  sorok(meccsSorokHTML('ETO', 7)),
      idegen: meccsSorokHTML('FTC', 7),
      uresen: meccsSorokHTML('VASAS', 8),
      integHelyes: !!d2.firstElementChild && d2.firstElementChild.classList.contains('bontasmeccs')
                   && !!d2.querySelector('.acctable'),
      integPerc: /Játszott perc/.test(d2.querySelector('.acctable').textContent),
      nogameNincs: !/bontasmeccs/.test(nogame || ''),
    };
  });

  console.log('   lezárt: ' + JSON.stringify(m.lezart));
  jo(m.lezart.length === 1 && m.lezart[0][0] === 'VASAS 2–2 ETO' && m.lezart[0][1] === 'vége',
     'lezárt meccs: klubok + eredmény + „vége"');
  console.log('   előtte: ' + JSON.stringify(m.elotte));
  jo(m.elotte.length === 1 && m.elotte[0][0] === 'PAFC–MTK' && m.elotte[0][1] === 'még nem kezdődött',
     'el nem kezdődött meccsnél nincs kitalált 0–0');
  jo(m.zajlik.length === 1 && m.zajlik[0][1] === 'a meccs zajlik',
     'az időkorláton belüli meccs: „a meccs zajlik" — ' + JSON.stringify(m.zajlik));
  jo(m.lement.length === 1 && m.lement[0][0] === 'DVSC–PAKS' && m.lement[0][1] === 'vége',
     'rég elkezdődött meccs eredmény nélkül: „vége", de szám nélkül');
  jo(m.dupla.length === 2, 'két meccses klubnál két sor (' + m.dupla.length + ')');
  jo(m.idegen === '' && m.uresen === '', 'idegen klubra és üres fordulóra nincs sor');
  jo(m.integHelyes, 'a bontasHTML a meccs-sort a táblázat fölé teszi');
  jo(m.integPerc, 'a Játszott perc sor a táblázatban van (77 perc)');
  jo(m.nogameNincs, 'nogame játékosnál nincs meccs-sor');
  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr));
  await vege(br);
})();
