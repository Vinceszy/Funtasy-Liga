const { BASE, jo, inditas, vege } = require('./kozos');
// A jatekos MECCSE a pont-bontas folott: "ARS 2-1 BRE - 70. perc".
//
// Az allas a fixtures valaszabol jon - ugyanabbol a keresbol, amit az elo
// fordulohoz amugy is elkuldunk. Lezart fordulora egy kulon (fordulonkent
// gyorsitotarazott) fixtures-lekeres megy; a bontasHTML amugy is aszinkron,
// ezert nem kell utantoltes.
//
// Amit rogzit: futo meccsen a meccsora, lefujva "vege", el nem kezdodott
// meccsnel nincs allas, dupla forduloban ket sor, es hogy a fejlec a
// tablazat FOLOTT all.
const GW = 1, REGI = 7;
const MECCS = (id, t) => ({ id, minutes: 0, ...t });
const ELO = [
  // futo meccs, van allas
  MECCS(11, { started: true,  finished_provisional: false, finished: false,
              kickoff_time: '2026-08-24T19:00:00Z', team_h: 1, team_a: 4,
              team_h_score: 2, team_a_score: 1 }),
  // lefujva
  MECCS(12, { started: true,  finished_provisional: true,  finished: false,
              kickoff_time: '2026-08-24T16:00:00Z', team_h: 2, team_a: 5,
              team_h_score: 0, team_a_score: 3 }),
  // meg nem kezdodott: nincs allas
  MECCS(13, { started: false, finished_provisional: false, finished: false,
              kickoff_time: '2026-08-25T19:00:00Z', team_h: 3, team_a: 6,
              team_h_score: null, team_a_score: null }),
  // az 1-es klub MASODIK meccse ugyanebben a forduloban (dupla fordulo)
  MECCS(14, { started: false, finished_provisional: false, finished: false,
              kickoff_time: '2026-08-26T19:00:00Z', team_h: 7, team_a: 1,
              team_h_score: null, team_a_score: null }),
];
const LEZART = [
  MECCS(71, { started: true, finished_provisional: true, finished: true,
              kickoff_time: '2026-08-01T14:00:00Z', team_h: 1, team_a: 2,
              team_h_score: 4, team_a_score: 0 }),
];

(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  const adat = require(require('path').join(__dirname, '..', 'draft_players.json'));
  const klub = { egy: adat.teams['1'], ketto: adat.teams['2'], harom: adat.teams['3'] };
  const jatekos = {};
  for (const [k, rov] of Object.entries(klub))
    jatekos[k] = Object.entries(adat.players).filter(([, v]) => v.t === rov).map(([x]) => +x)[0];

  let fxKeresek = 0;
  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) {
      fxKeresek++;
      return json(/event\/7\//.test(u) ? LEZART : ELO);
    }
    if (/\/live/.test(u)) {
      const el = {};
      for (const id of Object.values(jatekos))
        el[id] = { stats: { total_points: 5, minutes: 70, starts: 1 },
                   explain: [[[{ stat: 'minutes', value: 70, points: 2 }], 11]] };
      return json({ elements: el });
    }
    return json({});
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof LIVEMECCS !== 'undefined' && LIVEMECCS
    && Object.keys(LIVEMECCS).length > 0, null, { timeout: 20000 });

  // a fejlecsorokat szoveggé alakitva kerjuk vissza: [bal, jobb] paronkent
  const fejek = (e, gw) => p.evaluate(async ([e, gw]) => {
    const h = await bontasHTML(e, gw);
    const d = document.createElement('div');
    d.innerHTML = h || '';
    const sorok = [...d.querySelectorAll('.bontasmeccs')]
      .map(x => [x.children[0].textContent.trim().replace(/\s+/g, ' '),
                 x.children[1].textContent.trim()]);
    // a fejlec a tablazat FOLOTT all-e?
    const elso = d.firstElementChild;
    const tabla = d.querySelector('table, .acctable, .loading');
    return { sorok, felul: !!elso && elso.classList.contains('bontasmeccs'),
             vanTabla: !!tabla };
  }, [e, gw]);

  console.log('--- élő forduló ---');
  const futo = await fejek(jatekos.egy, GW);
  console.log('   ' + JSON.stringify(futo.sorok));
  jo(futo.sorok.length === 2, 'dupla fordulóban mindkét meccs sort kap (' + futo.sorok.length + ')');
  jo(futo.sorok[0][0] === klub.egy + ' 2–1 ' + adat.teams['4'],
     'a futó meccs állása a hazai–vendég sorrendben: ' + futo.sorok[0][0]);
  jo(futo.sorok[0][1] === '70. perc', 'a meccsóra a játékosok perceiből: ' + futo.sorok[0][1]);
  jo(futo.sorok[1][0] === adat.teams['7'] + '–' + klub.egy && futo.sorok[1][1] === 'még nem kezdődött',
     'az el nem kezdődött meccsnél nincs állás, csak a két klub');
  jo(futo.felul, 'a meccsfejléc a pont-bontás FÖLÖTT áll');
  jo(futo.vanTabla, 'a pont-bontás maga is ott van alatta');

  const lefujt = await fejek(jatekos.ketto, GW);
  console.log('   ' + JSON.stringify(lefujt.sorok));
  jo(lefujt.sorok.length === 1 && lefujt.sorok[0][1] === 'vége',
     'lefújt meccsnél "vége" áll az óra helyén');
  jo(lefujt.sorok[0][0] === klub.ketto + ' 0–3 ' + adat.teams['5'],
     'a lefújt meccs végeredménye is ott van: ' + lefujt.sorok[0][0]);

  const elotte = await fejek(jatekos.harom, GW);
  console.log('   ' + JSON.stringify(elotte.sorok));
  jo(elotte.sorok.length === 1 && !/\d–\d/.test(elotte.sorok[0][0]),
     'el nem kezdődött meccsnél nem írunk ki 0–0-t');

  console.log('\n--- lezárt forduló ---');
  const elotteDb = fxKeresek;
  const regi = await fejek(jatekos.egy, REGI);
  console.log('   ' + JSON.stringify(regi.sorok));
  jo(regi.sorok.length === 1 && regi.sorok[0][0] === klub.egy + ' 4–0 ' + klub.ketto,
     'lezárt fordulóban a végeredmény jön a saját fordulója fixtures-éből');
  jo(regi.sorok[0][1] === 'vége', 'lezárt fordulóban "vége"');
  const egyKeres = fxKeresek - elotteDb;
  await fejek(jatekos.ketto, REGI);
  const masodik = fxKeresek - elotteDb - egyKeres;
  console.log('   fixtures-kérés: első megnyitásra ' + egyKeres + ', másodikra ' + masodik);
  jo(egyKeres === 1 && masodik === 0,
     'a lezárt forduló meccslistája fordulónként EGYSZER töltődik le');

  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr));
  await vege(br);
})();
