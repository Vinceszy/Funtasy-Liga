const { BASE, jo, cim, hibak, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// A "frissítés…" jelzes: lassu lekeresnel latszik, gyorsnal nem villan fel.

// Megjelenik-e a jelzes a megadott idon belul? (A vegallapotot nezni keves
// volna: a jelzes a lekeres vegen eltunik.)
async function jelzesreVar(p, ms){
  try {
    const el = await p.waitForSelector('.frissjel', { timeout: ms, state: 'attached' });
    await p.waitForTimeout(350);                   // hadd ketyegjen egy kicsit
    return (await el.textContent()) || '';
  } catch (e) { return null; }
}

async function plMeccs(br, keses){
  const p = await br.newPage();
  const perr = []; p.on('pageerror', x => perr.push(x.message));
  // A sajat proxy (workers.dev) a tesztkornyezetbol nem erheto el, es a
  // valodi halozati probalkozasa ~300 ms - ennyi kesessel a LIVEGW valasz
  // MAR A KATTINTAS UTAN erne be, es a nem-elo ag futna le, jelzes nelkul.
  // (Elesben a sajat ut a leggyorsabb, ott nincs ilyen kesleltetes.)
  await p.route('**workers.dev/**', r => r.abort());
  const hist = require(require('path').join(__dirname,'..','draft_history.json'));
  const GW = Object.keys(hist.rounds)[0];
  const elemek = [...new Set(Object.values(hist.rounds[GW]).flat().map(x => x.e))];
  let elsoKesz = false;
  await p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    // a napi pontzaras (klasszikus FPL) - a PL-oldal ezt is lekeri
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/live/.test(u)){
      // a betoltesi lekerest nem lassitjuk, csak a modalbol indulot
      if (keses && elsoKesz) await new Promise(r => setTimeout(r, keses));
      elsoKesz = true;
      const el = {};
      elemek.forEach(id => { el[id] = { stats: { total_points: 4, minutes: 90 }, explain: [] }; });
      return json({ elements: el });
    }
    if (/\/fixtures/.test(u)) return json([]);
    return route.fulfill({ status: 404, body: '' });
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => document.querySelector('.match .score') &&
    /\d/.test(document.querySelector('.match .score').textContent), null, { timeout: 40000 });
  await p.locator('.match').first().click();
  // A LASSU agon bokezuen varunk: a jelzes a lekeres INDULASA utan 500
  // ms-mal jelenik meg, de elotte a lap meg betolti a fordulo keretet a
  // helyi szerverrol - a teljes tesztsor parhuzamos terhelese alatt ez
  // onmagaban tullephette a 2,5 mp-et, es a teszt "nincs jelzes"-t mert.
  // (A GYORS ag rovid marad: ott a jelzes HIANYAT allitjuk.)
  const szoveg = await jelzesreVar(p, keses ? 8000 : 1500);
  await p.waitForTimeout((keses || 0) + 800);
  const maradt = await p.locator('.frissjel').count();
  await p.close();
  return { szoveg, maradt, perr };
}

(async () => {
  const br = await inditas();

  console.log('--- PL: lassú lekérés (3 mp) ---');
  const lassu = await plMeccs(br, 3000);
  console.log('   jelzés szövege:', JSON.stringify(lassu.szoveg));
  jo(lassu.szoveg !== null, 'lassú lekérésnél megjelenik a jelzés');
  jo(/^frissítés… \d+,\d mp$/.test(lassu.szoveg || ''), 'a jelzés kiírja az eltelt időt');
  jo(lassu.maradt === 0, 'a lekérés végén eltűnik');
  jo(lassu.perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(lassu.perr.slice(0, 2)));

  console.log('\n--- PL: gyors lekérés ---');
  const gyors = await plMeccs(br, 0);
  console.log('   jelzés szövege:', JSON.stringify(gyors.szoveg));
  jo(gyors.szoveg === null, 'gyors lekérésnél nem villan fel (nincs zaj)');

  // ---------------- NB1 ----------------
  console.log('\n--- NB1: lassú élő keret-lekérés (3 mp) ---');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', x => perr.push(x.message));
  await p.route('**workers.dev/**', r => r.abort());   // lasd fent: plMeccs
  // Az elofeltetelt KIMONDJUK, nem a betoltesi frissitestol remeljuk: az 5.
  // fordulo elo volta eddig azon mult, hogy a mockolt ranglista-valaszok a
  // kattintas ELOTT beertek-e - ha nem, az elo keret-lekeres el se indult,
  // es a teszt jelzes nelkul, felrevezeto hibaval bukott (flake, kb. minden
  // harmadik futas). Ugyanigy rogzit a uzenetek.teszt.js is.
  await jsonAtir(p, '**/results.json*', j => Object.assign(j, { provisional: [5] }));
  const start = new Date(Date.now() - 1800000).toISOString();
  await p.route('**fantasy-api.mlsz.hu/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/game-player-stats/.test(u)) return json({ data: [] });
    if (/user-team-players-history/.test(u)){
      await new Promise(r => setTimeout(r, 3000));
      return json({ data: [{ id: 1, is_captain: false, type: 'starter', position: { monogram: 'CS' },
        summary_statistics: { weekly_points: 0, competition_points: 0 },
        competition_player: { id: 1249, first_name: 'Teszt', last_name: 'Jatekos', is_u21: false,
          team: { short_name: 'MTK' }, countries: [{ code: 'HUN' }],
          current_round: { is_played: true, market_price: 5, first_played_at: start,
            games: [{ start_at: start, status: 'scheduled' }] } } }] });
    }
    const m = /filter\[search\]=([^&]+)/.exec(u);
    return json({ data: [{ user_team: { user: { id: 1, username: m ? m[1] : '' },
      round_statistics: [{ round_number: 5, points: 30 }] } }] });
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 30000 });
  // NEM varjuk meg: a showLiveMatch async, es ha az egesz lefutasat
  // megvarnank, a jelzest mar le is vette volna magarol
  await p.evaluate(() => { showLiveMatch('Bazsa', 'Vince', 5); });
  const nb1Szoveg = await jelzesreVar(p, 8000);   // lasd fent: terheles alatt kevés volt
  console.log('   jelzés szövege:', JSON.stringify(nb1Szoveg));
  jo(nb1Szoveg !== null, 'NB1: lassú élő keret-lekérésnél is megjelenik');
  await p.waitForTimeout(4000);
  jo(await p.locator('.frissjel').count() === 0, 'NB1: a végén eltűnik');
  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr.slice(0, 2)));
  await p.close();

  await br.close();
  process.exit(hibak.length ? 1 : 0);
})();
