const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// A felulvizsgalat utani javitasok tesztje.

(async () => {
  const br = await inditas();

  // ---------- meccsFut ----------
  console.log('--- meccsFut: mikor fut a meccs ---');
  const p = await br.newPage();
  await p.route('**fantasy-api.mlsz.hu/**', r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof meccsFut === 'function');
  const e = await p.evaluate(() => {
    const perc = m => new Date(Date.now() - m * 60000).toISOString();
    const jovo  = m => new Date(Date.now() + m * 60000).toISOString();
    return {
      jovobeli:        meccsFut(jovo(60), undefined),
      fut30:           meccsFut(perc(30), undefined),
      fut30VegeHazug:  meccsFut(perc(30), true),     // 'completed' 30 percnel: NEM hihető
      fut110:          meccsFut(perc(110), undefined),
      veget110:        meccsFut(perc(110), true),    // 110 percnel mar hihető
      lejart200:       meccsFut(perc(200), undefined),
      ejfel:           meccsFut('2026-08-22T00:00:00+02:00', undefined),
      nincsStart:      meccsFut(null, undefined),
    };
  });
  jo(e.jovobeli === false, 'jövőbeli kezdés: még nem fut');
  jo(e.fut30 === true, '30 perce kezdődött: fut');
  jo(e.fut30VegeHazug === true, '30 percnél a "completed" jelzést NEM hisszük el (ez volt a hiba)');
  jo(e.fut110 === true, '110 perce kezdődött, nincs vége-jelzés: még fut');
  jo(e.veget110 === false, '110 percnél a "completed" már hiteles: nem fut');
  jo(e.lejart200 === false, '200 perc után akkor sem fut, ha nincs vége-jelzés');
  jo(e.ejfel === false, 'éjfél (nincs kitűzött kezdés): nem tekintjük futónak');
  jo(e.nincsStart === false, 'kezdés nélkül nem állítunk semmit');

  // ---------- "lejatszotta" csak bizonyitekkal ----------
  console.log('\n--- "lejátszotta" állításhoz bizonyíték kell ---');
  const u = await p.evaluate(() => {
    const perc = m => new Date(Date.now() - m * 60000).toISOString();
    const bontas = [{ name: 'Játszott perc', value: 90, points: 0 }];
    return {
      // elo fordulo, is_played igaz, meccs fut, bontas meg nincs
      futKozben:   nincsPontUzenet(true, perc(30), [], false, false, true),
      // Elo fordulo, is_played igaz, a meccs 4 oraja kezdodott, ures bontas.
      // MEGMERT teny: az MLSZ a 0 pontos jatekosra URES bontast ad (Heitor
      // 0 ponttal ures listat kapott, klubtarsa Ljujic ugyanabbol a meccsbol
      // 1,75-ot). Az ures lista tehat NEM jelent feldolgozatlant.
      regenNincs:  nincsPontUzenet(true, perc(240), [], false, false, true),
      // ugyanaz, de mar megjott a bontas -> van bizonyitek
      regenVan:    nincsPontUzenet(true, perc(240), bontas, false, false, true),
      // lezart fordulo (elo=false): a regi viselkedes marad
      lezart:      nincsPontUzenet(true, perc(240), [], false, true, false),
      // kezdesi ido nelkul, elo forduloban: nem allitunk semmit
      nincsIdo:    nincsPontUzenet(true, null, [], false, false, true),
    };
  });
  Object.entries(u).forEach(([k, v]) => console.log('   ' + k.padEnd(12) + ' -> ' + JSON.stringify(v)));
  jo(/A meccs zajlik/.test(u.futKozben), 'futó meccs + is_played=true -> "zajlik" (a bejelentett hiba)');
  jo(/Lejátszotta/.test(u.regenNincs), 'lement meccs + üres bontás -> lejátszotta, pont nélkül');
  jo(/Lejátszotta/.test(u.regenVan), 'megjött bontással már állítunk (90 perc, pont nélkül -> lejátszotta)');
  jo(/Lejátszotta/.test(u.lezart), 'lezárt fordulóban a régi viselkedés marad');
  jo(/Lejátszotta/.test(u.nincsIdo), 'kezdési idő nélkül is a lejátszotta marad (régi rekord)');

  // ---------- lejart helyorzo datum + masik fordulo meccse ----------
  console.log('\n--- kitűzetlen kezdés, aminek a napja már elmúlt ---');
  const h = await p.evaluate(() => {
    const nap = d => new Date(Date.now() + d * 864e5).toISOString().slice(0, 10) + 'T00:00:00+02:00';
    return {
      // Ez volt a 3. fordulos ETO-eset: az MLSZ helyorzoje aug. 15., a
      // fordulo viszont ket hete lezarult - kezdesi idot igerni hazugsag.
      lejart:  nincsPontUzenet(true, nap(-20), [], false, false, false),
      // ha a helyorzo napja meg hatravan, a datum hasznos informacio
      jovobeli: nincsPontUzenet(true, nap(+7), [], false, false, true),
      // "nincs meccse": elo forduloban jelen ido, lezartban mult
      ngElo:   nincsPontUzenet(true, null, null, true, false, true),
      ngLezart: nincsPontUzenet(true, null, null, true, false, false),
    };
  });
  Object.entries(h).forEach(([k, v]) => console.log('   ' + k.padEnd(9) + ' -> ' + JSON.stringify(v)));
  jo(/elmaradt/.test(h.lejart) && !/kezdés/.test(h.lejart),
    'lejárt helyőrző: nem ígér kezdési időt, hanem elmaradt meccset mond');
  jo(/kezdés/.test(h.jovobeli), 'jövőbeli helyőrzőnél a dátum megmarad');
  jo(/nem játszik/.test(h.ngElo), 'élő fordulóban jelen idő');
  jo(/nem volt meccse/.test(h.ngLezart), 'lezárt fordulóban múlt idő');

  console.log('\n--- a meccs round_number-e árulja el, hogy másik fordulóé ---');
  const k = await p.evaluate(() => {
    const rek = (round_number, status) => keretRekord({
      competition_player: { id: 1, first_name: 'A', last_name: 'B', team: { short_name: 'ETO' },
        current_round: { is_played: true, first_played_at: '2026-08-15T00:00:00+02:00',
          games: [{ start_at: '2026-08-23T17:30:00+02:00', status: status, round_number: round_number }] } },
      summary_statistics: { weekly_points: 0 }, position: {} }, 3);
    return {
      masik: rek('5F', 'completed'),      // a 3. fordulora a klub 5. fordulos meccse jott vissza
      sajat: rek('3F', 'completed'),      // ez tenyleg a 3. fordulo meccse
      futoMasik: rek('5F', 'scheduled'),  // masik fordulo meg nem lement meccse
    };
  });
  console.log('   másik fordulóé ->', JSON.stringify(k.masik.nogame), 'start:', JSON.stringify(k.masik.start),
              '| sajátja ->', JSON.stringify(k.sajat.nogame), 'start:', JSON.stringify(k.sajat.start));
  jo(k.masik.nogame === true, 'másik forduló meccse -> nincs meccse ebben a fordulóban');
  jo(k.masik.start === null, 'másik forduló meccséből nem veszünk át kezdési időt');
  jo(k.masik.vege === undefined, 'másik forduló meccsének állapota sem szivárog át');
  jo(k.futoMasik.nogame === true && k.futoMasik.vege === undefined,
    'a másik fordulóból visszaeső, még le nem ment meccs sem téveszt meg');
  jo(k.sajat.nogame === undefined && k.sajat.start === '2026-08-23T17:30:00+02:00' && k.sajat.vege === true,
    'a fordulóhoz tartozó meccs adatait viszont átvesszük');

  // ---------- PL: lezarult fordulo eldobja az elo reteget ----------
  console.log('\n--- PL: a forduló lezárul, amíg a lap háttérben van ---');
  const p2 = await br.newPage();
  await p2.addInitScript(() => { window.__ora = 0; const e = Date.now; Date.now = () => e() + window.__ora; });
  const hist = require(require('path').join(__dirname,'..','draft_history.json'));
  const GW = Object.keys(hist.rounds)[0];
  const elemek = [...new Set(Object.values(hist.rounds[GW]).flat().map(x => x.e))];
  let kesz = false;
  await p2.route('**draft.premierleague.com/api/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: kesz });
    if (/\/live/.test(u)){
      const el = {}; elemek.forEach(id => { el[id] = { stats: { total_points: 6, minutes: 90 }, explain: [] }; });
      return json({ elements: el });
    }
    if (/\/fixtures/.test(u)) return json([]);
    return route.fulfill({ status: 404, body: '' });
  });
  await p2.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => document.querySelector('.match.elo'), null, { timeout: 40000 });
  const eloElotte = await p2.locator('.match.elo').count();
  console.log('   "élő" jelölésű meccs a lezárás előtt:', eloElotte);

  kesz = true;                                    // kozben veget er a fordulo
  await p2.evaluate(() => { window.__ora = 120000; });
  await p2.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p2.waitForTimeout(1500);
  const eloUtana = await p2.locator('.match.elo').count();
  const statusz = (await p2.locator('#status').innerText()).trim();
  console.log('   "élő" jelölés a lezárás után:', eloUtana, '| státusz:', JSON.stringify(statusz.slice(0, 40)));
  jo(eloElotte > 0, 'a forduló alatt van "élő" jelölés');
  jo(eloUtana === 0, 'a lezárás után egy meccs sem marad "élő" jelölésű');
  jo(/Naprakész/.test(statusz), 'a státuszsáv naprakészt ír');
  await p2.close(); await p.close();
  await br.close();
  process.exit(hibak.length ? 1 : 0);
})();
