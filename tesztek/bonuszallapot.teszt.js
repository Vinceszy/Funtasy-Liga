const { BASE, jo, hibak, inditas, vege } = require('./kozos');
// A bonusz harom allapota a PL-oldalon.
//
// MERVE (2026-08-23): az FPL a bonuszt a meccs alatt is szamolja a
// BPS-tablabol, es az explain-be is beteszi (stat: "bonus"). Harom allapot:
//   megy a meccs                          -> a bonusz percrol percre valtozhat
//   lefujva, de a NAPZARAS meg hatravan   -> rogzult, de meg valtozhat
//   napzaras utan                         -> fix, JELOLETLEN
// A harmadik a FORDULO zarasa. 2026/27-tol a lockdown a fordulo utolso
// meccse UTANI nap 09:00 UK-kor van (korabban egy oraval a lefujas utan),
// hogy az Opta felulvizsgalata meg beleszamithasson - NAPI zaras tehat
// nincs. A jelzes a klasszikus FPL event-status vegpontjabol jon; a Draft
// frontendjenek forrasabol kiolvasva a ket mezo jelentese:
//   points:      "" = ures, l = Live, p = Provisional, r = Confirmed
//   bonus_added: igaz eseten a Bonus Points oszlopban "Added"
// Vegleges tehat a "r" vagy az "Added" - a "p" NEM az, az a kozbenso.
// Az explain szerkezete [[stat-lista, meccs_id]] - a bonusz-sor ezert a
// SAJAT meccsehez, azon at a sajat NAPJAHOZ kotheto.

const GW = 1;
// harom meccs harom allapotban, ket kulonbozo napon
const NYITOTT_NAP = '2026-08-23', ZART_NAP = '2026-08-22';
const MECCSEK = [
  { id: 11, started: true,  finished_provisional: false, finished: false,
    kickoff_time: NYITOTT_NAP + 'T13:00:00Z', team_h: 1, team_a: 2 },
  { id: 12, started: true,  finished_provisional: true,  finished: false,
    kickoff_time: NYITOTT_NAP + 'T15:30:00Z', team_h: 3, team_a: 4 },
  // lefujt meccs egy MAR LEZART napon - a meccs finished mezoje meg hamis,
  // tehat ha azt neznenk, tevesen ideiglenesnek jelolnenk
  { id: 13, started: true,  finished_provisional: true,  finished: false,
    kickoff_time: ZART_NAP + 'T14:00:00Z', team_h: 5, team_a: 6 },
];
// A lezart nap "r" (Confirmed), a masik meg "p" (Provisional). A "p"
// szandekosan a NYITOTT napon all: ha valaki azt megint veglegesnek venne,
// ez a teszt bukik.
const NAPOK = { status: [
  { date: ZART_NAP,     event: GW, bonus_added: false, points: 'r' },
  { date: NYITOTT_NAP,  event: GW, bonus_added: false, points: 'p' },
] };
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

let napokKi = true;   // a napi zaras adata megjon-e (a tartalek-ag teszteléséhez)

(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 1100, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  // FIGYELEM: nem eleg a draft.premierleague.com-ot elfogni - a napi zaras a
  // KLASSZIKUS FPL event-status vegpontjarol jon (fantasy.premierleague.com).
  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MECCSEK);
    if (/event-status/.test(u)) return json(napokKi ? NAPOK : { status: [] });
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
  // A napi zaras kulon, a fo frissitestol fuggetlenul erkezik (szandekosan
  // nem varjuk meg ott) - itt viszont meg kell varni, kulonben a teszt a
  // tartalek-agat merne.
  await p.waitForFunction(() => typeof LIVENAP !== 'undefined' && LIVENAP
    && Object.keys(LIVENAP).length === 2, null, { timeout: 20000 });

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
  jo(/b-ideiglenes/.test(lefujva.cls) && /forduló végéig/.test(lefujva.megj),
    'lefújt meccs, a forduló még nyitva: külön jelölés, és megmondja, mire vár');
  jo(!/b-valtozik|b-ideiglenes/.test(kesz.cls) && kesz.megj === '',
    'a forduló zárása után: semmilyen jelölés (a jelöletlen = fix)');
  jo(/még változhat/.test(lefujva.megj) && kesz.megj === '',
    'a "p" (Provisional) jelölést kap, a "r" (Confirmed) nem');
  jo(fut.cls !== lefujva.cls, 'a két jelölt állapot nem ugyanaz');

  console.log('\n--- a bónusz "Added" önmagában is véglegessé tesz ---');
  const added = await p.evaluate(() => {
    // a nyitott nap "p" marad, de a bonusz mar Added
    LIVENAP[Object.keys(LIVENAP).find(d => !LIVENAP[d].lezart)] = { lezart: true };
    return bontasHTML(202, 1);
  });
  const addedSor = sorok(added)[0];
  console.log('   Added esetén:', JSON.stringify(addedSor));
  jo(addedSor.megj === '' && !/b-/.test(addedSor.cls),
    'ha az FPL szerint a bónusz már Added, nincs jelölés');

  console.log('\n--- dupla forduló: két meccs, két állapot ---');
  const ketto = sorok(ki[204]);
  console.log('   sorok:', JSON.stringify(ketto));
  jo(ketto.length === 2, 'két bónusz sor van (meccsenként egy)');
  jo(ketto.some(x => !/b-/.test(x.cls)) && ketto.some(x => /b-valtozik/.test(x.cls)),
    'a kész meccs sora jelöletlen, a futóé jelölt — nem mossuk össze őket');

  console.log('\n--- tartalék: ha a napi zárás adata nem jön meg ---');
  // Ilyenkor a meccs sajat finished mezojere esunk vissza. A 13-as meccs
  // finished=false, tehat jelolve kell lennie - inkabb jelezzunk feleslegesen,
  // mint hogy fixnek mondjunk valamit, ami meg valtozhat.
  napokKi = false;
  const p2 = await br.newPage();
  await p2.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MECCSEK);
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/live/.test(u)) {
      const el = {};
      for (const [id, parok] of Object.entries(JATEKOSOK))
        el[id] = { stats: { total_points: 10, minutes: 90, bonus: parok[0][1] }, explain: explain(parok) };
      return json({ elements: el });
    }
    return json({});
  });
  await p2.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => typeof LIVEMECCS !== 'undefined' && LIVEMECCS
    && Object.keys(LIVEMECCS).length === 3, null, { timeout: 20000 });
  const tartalek = sorok(await p2.evaluate(GW => bontasHTML(203, GW), GW))[0];
  console.log('   napi adat nélkül, lefújt meccs ->', JSON.stringify(tartalek));
  jo(/b-ideiglenes/.test(tartalek.cls),
    'napi adat nélkül a lefújt meccs jelölt marad (a meccs finished mezője a tartalék)');

  console.log('\n--- a többi sor érintetlen ---');
  jo(!/b-valtozik|b-ideiglenes/.test(ki[201].replace(/Bónuszpontok[\s\S]*?<\/tr>/g, '')),
    'a gól és a percek sora nem kap jelölést');

  console.log('\npageerror:', perr.length ? perr : 'nincs');
  jo(perr.length === 0, 'nincs JS-hiba');
  await vege(br);
})();
