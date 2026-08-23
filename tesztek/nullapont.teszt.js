const { BASE, jo, cim, hibak, inditas, vege } = require('./kozos');
// A negy "0 pont" allapot es a kattinthatosag-jelzes tesztje mindket oldalon.
const REPO = require('path').join(__dirname, '..');

const cfg = n => ({ competition_stat_config: { name: n } });
// cp 101/102: nincs egyetlen sor sem (nincs meg statisztika)
// cp 103: sorok vannak, de 0 perc -> nem lepett palyara
// cp 104: sorok vannak, 90 perc, de egyik sem er pontot
// cp 105: van pontot ero sor -> rendes tablazat
const BONTAS = {
  101: [], 102: [],
  103: [{ value: 0, points: 0, ...cfg('Játszott perc') }, { value: 0, points: 0, ...cfg('Gólok') }],
  104: [{ value: 90, points: 0, ...cfg('Játszott perc') }, { value: 0, points: 0, ...cfg('Gólok') }],
  105: [{ value: 1, points: 3, ...cfg('Győzelem') }, { value: 90, points: 2, ...cfg('Percek a pályán (több, mint 60 perc)') },
        { value: 90, points: 0, ...cfg('Játszott perc') }],
};

const panelSzoveg = async page => {
  await page.waitForFunction(() => {
    const p = document.querySelector('.accpanel');
    return p && !p.textContent.includes('betöltése');
  }, null, { timeout: 15000 });
  return (await page.locator('.accpanel').innerText()).trim();
};
const ell = (cimke, kapott, vart) =>
  console.log((kapott.startsWith(vart) ? 'OK   ' : 'HIBA ') + cimke + ' -> ' + JSON.stringify(kapott.slice(0, 70)));

(async () => {
  const browser = await inditas();
  const hibak = [];

  // ---------------- NB1 ----------------
  const page = await browser.newPage();
  page.on('pageerror', e => hibak.push('NB1 pageerror: ' + e.message));
  await page.route('**://fantasy-api.mlsz.hu/**', route => {
    const u = route.request().url();
    if (u.includes('game-player-stats')) {
      const cp = +(u.match(/competition_player_id%5D=(\d+)/) || [])[1];
      return route.fulfill({ json: { data: BONTAS[cp] || [] } });
    }
    if (u.includes('user-team-players-history')) return route.fulfill({ json: { data: [] } });
    if (u.includes('rankings')){
      const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
      return route.fulfill({ json: { data: [{ user_team: { user: { id: 5000, username: uname } }, summary_statistics: {}, rounds: [] }] } });
    }
    return route.fulfill({ status: 404, json: {} });
  });
  await page.route('**corsproxy.io/**', r => r.abort());
  await page.route('**allorigins**', r => r.abort());
  // A fixtura abszolut idopontokat tarol, amik idokozben elavulnak (egy
  // "meg nem kezdodott" meccs holnapra mar lejatszott). Ezert a kezdeseket
  // MOSTHOZ kepest allitjuk be, kulonben a teszt naponta mast mer.
  // A teszt SAJAT allapotokat allit be, nem a valos adat pillanatnyi
  // tartalmara epul: az elso szakvezeto keretet lecsereljuk hat, pontosan
  // meghatarozott allapotu jatekosra. Igy a teszt akkor is ugyanazt meri, ha
  // kozben valtozik a szezon allasa.
  const ora = h => new Date(Date.now() + h * 3600000).toISOString();
  const JATEKOS = (nev, id, tobbi) => Object.assign({
    name: nev, team: 'MTK', pos: 'CS', u21: false, hun: true, price: 5,
    cap: false, sub: false, week: 0, total: 0, id: id }, tobbi);
  const TESZTKERET = [
    // nev,                       cp-id (a bontas-mockhoz), allapot
    JATEKOS('Meg Nem Kezdodott', 101, { played: false, start: ora(3) }),
    JATEKOS('Eppen Fut',         102, { played: false, start: ora(-0.5) }),
    JATEKOS('Nem Lepett Palyara',103, { played: true,  start: ora(-4), vege: true }),
    JATEKOS('Lejatszotta Nullat',104, { played: true,  start: ora(-4), vege: true }),
    JATEKOS('Pontot Szerzett',   105, { played: true,  start: ora(-4), vege: true, week: 5 }),
    JATEKOS('Nincs Meccse',      106, { played: false, start: null, nogame: true }),
    // Kituzetlen kezdes: az MLSZ ejfelt ir, ha az idopont meg nincs meg
    JATEKOS('Ejfeli Placeholder',107, { played: false, start: '2026-12-24T00:00:00+01:00' }),
    // A BEJELENTETT HIBA esete: az MLSZ az is_played-et mar a meccs KOZBEN
    // igazra billenti. Ilyenkor sem szabad azt irni, hogy "lejatszotta".
    JATEKOS('Futó Meccsű Tesztjátékos', 104, { played: true, start: ora(-0.5), sub: true }),
  ];
  await page.route('**/squads.json*', async route => {
    const j = await (await route.fetch()).json();
    j.squads[Object.keys(j.squads)[0]] = TESZTKERET;
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(j) });
  });
  await page.goto(BASE + 'nb1/');
  await page.waitForSelector('#table tr');
  await page.click('[data-member="Katyul"]');
  await page.waitForSelector('.plr[data-acc]');

  console.log('--- NB1 ---');
  console.log('sugosor:', await page.locator('.acchint').count() === 1 ? 'OK' : 'HIBA');
  console.log('nyil minden soron:',
    (await page.locator('.plr[data-acc]').count()) === (await page.locator('.plr[data-acc] .accarr').count()) ? 'OK' : 'HIBA');

  const kattints = async nev => {
    const sor = page.locator('.plr', { hasText: nev }).first();
    await sor.click();
    return panelSzoveg(page);
  };
  ell('meg nem kezdodott', await kattints('Meg Nem Kezdodott'), 'A meccs még nem kezdődött el — kezdés:');
  console.log('nyitott sor jelolve:', await page.locator('.plr.open .accarr').count() === 1 ? 'OK' : 'HIBA');
  ell('zajlik           ', await kattints('Eppen Fut'), 'A meccs zajlik');
  ell('nem lepett palyara', await kattints('Nem Lepett Palyara'), 'Nem lépett pályára');
  ell('lejatszotta, 0    ', await kattints('Lejatszotta Nullat'), 'Lejátszotta a meccset');
  ell('nincs meccse      ', await kattints('Nincs Meccse'), 'Ebben a fordulóban nem játszik');
  // A bejelentett hiba regresszio-tesztje: is_played=true, de a meccs meg fut.
  // Meccs kozben a 0 helyen kotojel all (az MLSZ meg nem ad pontot), de aki
  // mar szerzett pontot, annal a szam latszik.
  const futPont = await page.locator('.plr', { hasText: 'Futó Meccsű' }).first()
    .locator('.pts').innerText();
  const futCim = await page.locator('.plr', { hasText: 'Futó Meccsű' }).first()
    .locator('.pts').getAttribute('title');
  console.log((futPont.trim() === '–' ? 'OK   ' : 'HIBA ')
    + 'futó meccs, 0 pont -> kötőjel (' + JSON.stringify(futPont.trim()) + ')');
  console.log((/meccs zajlik/.test(futCim || '') ? 'OK   ' : 'HIBA ')
    + 'a kötőjel magyarázata: ' + JSON.stringify(futCim));
  const lementPont = await page.locator('.plr', { hasText: 'Lejatszotta Nullat' }).first()
    .locator('.pts').innerText();
  console.log((lementPont.trim() !== '–' ? 'OK   ' : 'HIBA ')
    + 'lement meccs, 0 pont -> szám marad (' + JSON.stringify(lementPont.trim()) + ')');
  const futSzoveg = await kattints('Futó Meccsű');   // ujrakattintas zarna a panelt
  ell('fut, de is_played ', futSzoveg, 'A meccs zajlik');
  console.log((/az MLSZ a pontokat a meccs végén rögzíti/.test(futSzoveg) ? 'OK   ' : 'HIBA ')
    + 'NB1: a "zajlik" nem ígér élő pontot');
  ell('ejfel = nincs ido  ', await kattints('Ejfeli Placeholder'), 'A meccs még nem kezdődött el — kezdés: dec. 24. (időpont még nincs kitűzve)');
  const kj = await page.$$eval('.plr', ns => ns.filter(n => n.dataset.ng === '1')
    .map(n => (n.querySelector('.pts')||{}).textContent));
  console.log((kj.length === 1 && kj[0] === '–' ? 'OK   ' : 'HIBA ') + 'nincs meccse -> kotojel: ' + JSON.stringify(kj));
  const t = await kattints('Pontot Szerzett');
  console.log((/Győzelem/.test(t) && /Percek a pályán/.test(t) && !/Játszott perc\b/.test(t) ? 'OK   ' : 'HIBA ')
    + 'pontot ero bontas -> ' + JSON.stringify(t.replace(/\n/g, ' | ').slice(0, 80)));

  // ---------------- PL ----------------
  const pl = require(REPO + '/draft_players.json');
  const hist = require(REPO + '/draft_history.json');
  const csapat = Object.keys(hist.rounds['1'])[0];
  const elemek = hist.rounds['1'][csapat].map(x => x.e);
  const rov2id = {}; Object.entries(pl.teams).forEach(([id, r]) => rov2id[r] = +id);
  const klub = e => pl.players[String(e)].t;
  // negy teszt-jatekos negy allapotra - KULON klubbol, mert az allapot
  // klubhoz kotodik (egy klub minden jatekosa ugyanabban a meccsben van)
  const latott = new Set(), valasztott = [];
  for (const e of elemek){ const k = klub(e); if (!latott.has(k)){ latott.add(k); valasztott.push(e); } }
  const [A, B, C, D] = valasztott;
  const elems = {};
  elemek.forEach(e => { elems[e] = { stats: { total_points: 0, minutes: 0 },
    explain: [[[{ name: 'Minutes played', points: 0, value: 0, stat: 'minutes' }], 1]] }; });
  elems[D] = { stats: { total_points: 0, minutes: 90 },
    explain: [[[{ name: 'Minutes played', points: 0, value: 90, stat: 'minutes' }], 1]] };
  const most = Date.now();
  const fixtures = [
    { started: false, finished: false, kickoff_time: new Date(most + 20 * 3600e3).toISOString(), team_h: rov2id[klub(A)], team_a: 0 },
    { started: true,  finished: false, kickoff_time: new Date(most - 3600e3).toISOString(),      team_h: rov2id[klub(B)], team_a: 0 },
    { started: true,  finished: false, finished_provisional: true, kickoff_time: new Date(most - 7200e3).toISOString(),      team_h: rov2id[klub(C)], team_a: rov2id[klub(D)] },
  ];
  const page2 = await browser.newPage();
  page2.on('pageerror', e => hibak.push('PL pageerror: ' + e.message));
  await page2.route('**://draft.premierleague.com/**', route => {
    const u = route.request().url();
    // a lekeresek gyorsitotar-toro parametert kapnak, tehat nem lehet a
    // vegzodesre illeszteni ("/game" helyett "/game?fpl_=...")
    if (/\/game(\?|$)/.test(u)) return route.fulfill({ json: { current_event: 1, current_event_finished: false } });
    if (u.includes('/event/1/live')) return route.fulfill({ json: { elements: elems } });
    if (u.includes('/event/1/fixtures')) return route.fulfill({ json: fixtures });
    return route.fulfill({ status: 404, json: {} });
  });
  await page2.goto(BASE + 'pl/');
  await page2.waitForSelector('#table tr');
  await page2.waitForFunction(() => document.getElementById('status').textContent.includes('Élő'));
  await page2.click(`[data-team="${csapat}"]`);
  await page2.waitForSelector('.plr[data-acc]');

  console.log('--- PL ---');
  console.log('sugosor:', await page2.locator('.acchint').count() === 1 ? 'OK' : 'HIBA');
  console.log('nyil minden soron:',
    (await page2.locator('.plr[data-acc]').count()) === (await page2.locator('.plr[data-acc] .accarr').count()) ? 'OK' : 'HIBA');
  const kattints2 = async e => {
    const sor = page2.locator(`.plr[data-e="${e}"]`).first();
    await sor.click();
    return panelSzoveg(page2);
  };
  ell('meg nem kezdodott', await kattints2(A), 'A meccs még nem kezdődött el — kezdés:');
  ell('zajlik           ', await kattints2(B), 'A meccs zajlik');
  ell('nem lepett palyara', await kattints2(C), 'Nem lépett pályára');
  ell('lejatszotta, 0    ', await kattints2(D), 'Lejátszotta a meccset');
  const [, , , , E] = valasztott;   // otodik klub: nincs meccse a forduloban
  if (E){
    ell('PL ures fordulo   ', await kattints2(E), 'Ebben a fordulóban nem játszik');
    const j = (await page2.locator(`.plr[data-e="${E}"] .pts`).textContent()).trim();
    console.log((j === '–' ? 'OK   ' : 'HIBA ') + 'PL ures fordulo -> kotojel: ' + JSON.stringify(j));
  } else console.log('(nincs otodik klub a teszt-kerethez)');
  // kotojel csak a meg nem kezdodott meccs jatekosainal
  const jelA = (await page2.locator(`.plr[data-e="${A}"] .pts`).textContent()).trim();
  const jelD = (await page2.locator(`.plr[data-e="${D}"] .pts`).textContent()).trim();
  console.log((jelA === '–' && jelD === '0' ? 'OK   ' : 'HIBA ') + `kotojel/0: nem kezdodott="${jelA}" lejatszott="${jelD}"`);

  console.log('pageerror-ok:', hibak.length ? hibak : 'nincs');
  await browser.close();
  process.exit(hibak.length ? 1 : 0);
})();
