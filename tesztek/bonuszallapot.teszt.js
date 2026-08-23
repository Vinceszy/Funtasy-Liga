const { BASE, jo, hibak, inditas, vege } = require('./kozos');
// A bonusz harom allapota a PL-oldalon.
//
// MERVE (2026-08-23, draft.premierleague.com): az FPL a bonuszt a meccs
// alatt is szamolja a BPS-tablabol, es az explain-be is beteszi
// (stat: "bonus"). Harom allapot van, a meccs jelzoibol:
//   started, meg nem finished_provisional   -> a meccs alatt meg valtozik
//   finished_provisional, meg nem finished  -> lefujva, meg nem hivatalos
//   finished                                -> hivatalos, JELOLETLEN
// Az explain szerkezete [[stat-lista, meccs_id]] - a bonusz-sor ezert a
// SAJAT meccsehez kotheto; dupla fordulonal a ket sor kulon allapotban lehet.

const GW = 1;
// harom meccs, harom allapotban; a negyedik a dupla fordulo masodik meccse
const MECCSEK = [
  { id: 11, started: true,  finished_provisional: false, finished: false, team_h: 1, team_a: 2 },
  { id: 12, started: true,  finished_provisional: true,  finished: false, team_h: 3, team_a: 4 },
  { id: 13, started: true,  finished_provisional: true,  finished: true,  team_h: 5, team_a: 6 },
];
// jatekosonkent: melyik meccs(ek)ben szerepel es mennyi bonuszt kapott
const JATEKOSOK = {
  201: [[11, 3]],            // fut a meccse
  202: [[12, 2]],            // lefujva, meg nem hivatalos
  203: [[13, 1]],            // hivatalos
  204: [[13, 1], [11, 2]],   // dupla fordulo: egy kesz + egy futo meccs
};
const explain = parok => parok.map(([mid, bonusz]) => [[
  { name: 'Minutes played', points: 2, value: 90, stat: 'minutes' },
  { name: 'Goals scored',   points: 5, value: 1,  stat: 'goals_scored' },
  { name: 'Bonus',          points: bonusz, value: bonusz, stat: 'bonus' },
], mid]);

(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 1100, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  await p.route('**draft.premierleague.com/api/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MECCSEK);
    if (/\/live/.test(u)) {
      const el = {};
      for (const [id, parok] of Object.entries(JATEKOSOK))
        el[id] = { stats: { total_points: 10, minutes: 90, bonus: parok[0][1] }, explain: explain(parok) };
      return json({ elements: el });
    }
    return json({});
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  // A LIVEGW/LIVEMECCS top-level `let`, tehat NINCS a window-on - nevvel kell
  // hivatkozni rajuk (a waitForFunction torzse global hatokorben fut).
  await p.waitForFunction(() => typeof LIVEGW !== 'undefined' && LIVEGW === 1,
    null, { timeout: 20000 });
  await p.waitForFunction(() => typeof LIVEMECCS !== 'undefined' && LIVEMECCS
    && Object.keys(LIVEMECCS).length === 3, null, { timeout: 20000 });

  const ki = await p.evaluate(async (GW) => {
    const r = {};
    for (const id of [201, 202, 203, 204]) r[id] = await bontasHTML(+id, GW);
    return r;
  }, GW);

  const sorok = html => {
    // a bonusz sorai: nev-cella szovege + a pont-cella osztalya
    const ki = [];
    const re = /<td class="ev">Bónuszpontok([\s\S]*?)<\/td>[\s\S]*?<td class="([^"]*)">/g;
    let m; while ((m = re.exec(html))) ki.push({ megj: m[1].replace(/<[^>]*>/g, '').trim(), cls: m[2] });
    return ki;
  };

  console.log('--- egy meccses esetek ---');
  const fut = sorok(ki[201])[0], lefujva = sorok(ki[202])[0], kesz = sorok(ki[203])[0];
  console.log('   futó meccs      ->', JSON.stringify(fut));
  console.log('   lefújva         ->', JSON.stringify(lefujva));
  console.log('   hivatalos       ->', JSON.stringify(kesz));
  jo(/b-valtozik/.test(fut.cls) && /változik/.test(fut.megj),
    'futó meccs: a bónusz sor jelölt, és megmondja, hogy még változik');
  jo(/b-ideiglenes/.test(lefujva.cls) && /nem hivatalos/.test(lefujva.megj),
    'lefújt meccs: külön jelölés, "még nem hivatalos"');
  jo(!/b-valtozik|b-ideiglenes/.test(kesz.cls) && kesz.megj === '',
    'hivatalos bónusz: semmilyen jelölés (a jelöletlen = végleges)');
  jo(fut.cls !== lefujva.cls, 'a két jelölt állapot nem ugyanaz');

  console.log('\n--- dupla forduló: két meccs, két állapot ---');
  const ketto = sorok(ki[204]);
  console.log('   sorok:', JSON.stringify(ketto));
  jo(ketto.length === 2, 'két bónusz sor van (meccsenként egy)');
  jo(ketto.some(x => !/b-/.test(x.cls)) && ketto.some(x => /b-valtozik/.test(x.cls)),
    'a kész meccs sora jelöletlen, a futóé jelölt — nem mossuk össze őket');

  console.log('\n--- a többi sor érintetlen ---');
  jo(!/b-valtozik|b-ideiglenes/.test(ki[201].replace(/Bónuszpontok[\s\S]*?<\/tr>/g, '')),
    'a gól és a percek sora nem kap jelölést');

  console.log('\npageerror:', perr.length ? perr : 'nincs');
  jo(perr.length === 0, 'nincs JS-hiba');
  await vege(br);
})();
