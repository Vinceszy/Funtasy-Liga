const { BASE, jo, hibak, inditas, vege } = require('./kozos');
// A jatekos harom szama az elo forduloban: jatszott perc, meccsora, kezdo-e.
//
// Nyers ertekeket mutatunk, nem ertelmezunk helyette ("lecserelve") - ahhoz
// tureshatar kellene, es egy egyperces csuszas a ket vegpont kozott hamis
// allitast szulne. A ket szambol a nezo maga latja, palyan van-e.
// A meccsora 45-nel es 90-nel megall, ezert a lefujt meccs "vege"-t ir.

const GW = 1;
const KLUB = { fut: 1, kesz: 2, elotte: 3 };   // csapat-id -> allapot
// A "minutes" szandekosan 0 mindenhol: MERVE, hogy az FPL sosem tolti ki.
// A meccsorat a jatekosok perceibol kell szamolni - ha valaki visszatenne a
// meccs sajat mezojet, ez a teszt bukik.
const MECCSEK = [
  { id: 11, started: true,  finished_provisional: false, finished: false,
    minutes: 0, kickoff_time: '2026-08-24T19:00:00Z', team_h: 1, team_a: 4 },
  { id: 12, started: true,  finished_provisional: true,  finished: false,
    minutes: 0, kickoff_time: '2026-08-24T16:00:00Z', team_h: 2, team_a: 5 },
  { id: 13, started: false, finished_provisional: false, finished: false,
    minutes: 0, kickoff_time: '2026-08-25T19:00:00Z', team_h: 3, team_a: 6 },
];
// jatekos -> {perc, kezdo}; a klubot a draft_players.json adja, ezert valodi
// jatekos-azonositokat kell hasznalni: futas kozben valasztunk hozzajuk.
(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  const adat = require(require('path').join(__dirname, '..', 'draft_players.json'));
  const csapatId = Object.fromEntries(Object.entries(adat.teams).map(([k, v]) => [v, +k]));
  // valasszunk ki egy-egy valodi jatekost a harom klubbol
  const klubNev = { fut: adat.teams['1'], kesz: adat.teams['2'], elotte: adat.teams['3'] };
  const jatekos = {};
  for (const [allapot, rov] of Object.entries(klubNev))
    jatekos[allapot] = Object.entries(adat.players)
      .filter(([, v]) => v.t === rov).map(([k]) => +k);

  // percek: futo meccsen kezdo/lecserelt/becserelt/be nem allt, kesz meccsen vegig
  const P = {
    [jatekos.fut[0]]:    { minutes: 70, starts: 1 },   // palyan, kezdo
    [jatekos.fut[1]]:    { minutes: 62, starts: 1 },   // lecserelve
    [jatekos.fut[2]]:    { minutes: 12, starts: 0 },   // becserelve
    [jatekos.fut[3]]:    { minutes: 0,  starts: 0 },   // nem lepett palyara
    [jatekos.kesz[0]]:   { minutes: 90, starts: 1 },   // lement meccs
    [jatekos.elotte[0]]: { minutes: 0,  starts: 0 },   // meg nem kezdodott
  };

  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json(MECCSEK);
    if (/\/live/.test(u)) {
      const el = {};
      for (const [id, st] of Object.entries(P))
        el[id] = { stats: { total_points: 5, ...st }, explain: [] };
      return json({ elements: el });
    }
    return json({});
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof LIVEPERC !== 'undefined' && Object.keys(LIVEPERC).length > 0,
    null, { timeout: 20000 });

  const cellak = async e => p.evaluate(([e, GW]) => {
    const d = document.createElement('div');
    d.innerHTML = percCellakHTML(e, GW);
    return [...d.children].map(x => x.textContent);
  }, [e, GW]);

  console.log('--- futó meccs (70. perc) ---');
  const palyan = await cellak(jatekos.fut[0]);
  const le = await cellak(jatekos.fut[1]);
  const be = await cellak(jatekos.fut[2]);
  const nulla = await cellak(jatekos.fut[3]);
  [['pályán, kezdő', palyan], ['lecserélve', le], ['becserélve', be], ['0 perc', nulla]]
    .forEach(([n, c]) => console.log('   ' + n.padEnd(15) + JSON.stringify(c)));
  jo(JSON.stringify(palyan) === JSON.stringify(["70'", "70'", 'K']), 'pályán lévő kezdő: 70/70/K');
  jo(JSON.stringify(le) === JSON.stringify(["62'", "70'", 'K']), 'lecserélt: 62/70/K — a néző látja, hogy nincs a pályán');
  jo(JSON.stringify(be) === JSON.stringify(["12'", "70'", '–']), 'becserélt: 12/70/–');
  jo(JSON.stringify(nulla) === JSON.stringify(["0'", "70'", '–']), 'nem lépett pályára: 0/70/–');

  console.log('\n--- lement meccs ---');
  const kesz = await cellak(jatekos.kesz[0]);
  console.log('   ' + JSON.stringify(kesz));
  jo(kesz[1] === 'vége', 'lefújt meccsnél a meccsóra "vége" — a 90 önmagában kétértelmű lenne');
  jo(kesz[0] === "90'" && kesz[2] === 'K', 'a játékos percei és a kezdő jelzés megmaradnak');

  console.log('\n--- még nem kezdődött el ---');
  const elotte = await cellak(jatekos.elotte[0]);
  console.log('   ' + JSON.stringify(elotte));
  jo(elotte.length === 0, 'el nem kezdődött meccsnél nincs cella');

  console.log('\n--- a meccsóra a JÁTÉKOSOK perceiből jön ---');
  const ora = await p.evaluate(() => LIVEMECCS[11].perc);
  console.log('   a 11-es meccs órája: ' + ora + " (a fixtures minutes mezoje 0 volt)");
  jo(ora === 70, 'a meccsóra a pályán lévő kezdők percszáma, nem a fixtures mezője');

  console.log('\n--- lezárt forduló ---');
  const regi = await p.evaluate(e => percCellakHTML(e, 99), jatekos.fut[0]);
  jo(regi === '', 'nem az élő fordulóban nincs cella');
  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr));
  await vege(br);
})();
