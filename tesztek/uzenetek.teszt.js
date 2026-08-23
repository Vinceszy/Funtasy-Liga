const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// A negy bejelentett hiba tesztje.
//  1-2) gyorsitotar: minden elo lekeres MAS URL-re megy es no-store-ral
//  3)   meccs kozben nem szabad azt irni, hogy "lejatszotta pont nelkul"
//  4)   NB1-en a szoveg nem igerhet elo pontot (eloPontok ligatulajdonsag)

// ---- mockolt MLSZ-keret: egy jatekos, allithato jelzokkel
function keret(opts){
  return { data: [{
    id: 1, is_captain: false, type: 'starter', position: { monogram: 'CS' },
    summary_statistics: { weekly_points: 0, competition_points: 0 },
    competition_player: { id: 1249, first_name: 'Zalán Márk', last_name: 'Kerezsi',
      is_u21: false, team: { short_name: 'MTK' }, countries: [{ code: 'HUN' }],
      current_round: Object.assign({ is_played: true, market_price: 8.5,
        first_played_at: opts.start }, opts.games ? { games: opts.games } : {}) } }] };
}

(async () => {
  const br = await inditas();

  // =============== 3-4) NB1 uzenet meccs kozben ===============
  console.log('--- NB1: mit ír meccs közben ---');
  // A kezdes ota eltelt ido szamit: egy meccs 60 perccel a kezdes utan meg
  // nem erhetett veget, ezert ott a 'completed' jelzest nem hisszuk el.
  const esetek = [
    { nev: 'meccs zajlik (is_played MAR igaz)', status: 'scheduled', ora: 1, vart: /A meccs zajlik/ },
    { nev: 'meccs közben hazug "completed"',    status: 'completed', ora: 0.5, vart: /A meccs zajlik/ },
    { nev: 'meccs véget ért, pont nélkül',      status: 'completed', ora: 2.2, vart: /Lejátszotta a meccset/ },
  ];
  for (const eset of esetek){
    const p = await br.newPage();
    const perr = []; p.on('pageerror', x => perr.push(x.message));
    // a meccs 1 oraja tart (mult ideju kezdes)
    const start = new Date(Date.now() - eset.ora * 3600000).toISOString().replace('Z', '+00:00');
    await p.route('**fantasy-api.mlsz.hu/**', route => {
      const u = decodeURIComponent(route.request().url());
      const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
      // Meccs alatt az MLSZ meg nem ad adatot; a lement meccsnel viszont mar igen
      if (/game-player-stats/.test(u)) return json({ data: eset.ora > 2
        ? [{ value: 90, points: 0, competition_stat_config: { name: 'Játszott perc' } }] : [] });
      if (/user-team-players-history/.test(u))
        return json(keret({ start, games: [{ start_at: start, status: eset.status }] }));
      const m = /filter\[search\]=([^&]+)/.exec(u);
      return json({ data: [{ user_team: { user: { id: 1, username: m ? m[1] : '' },
        round_statistics: [{ round_number: 5, points: 30 }] } }] });
    });
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 20000 });
    // elo meccs megnyitasa az 5. (ideiglenes) fordulora
    await p.evaluate(() => showLiveMatch('Bazsa', 'Vince', 5));
    await p.waitForSelector('.plr[data-acc]', { timeout: 20000 });
    await p.click('.plr[data-acc]');
    await p.waitForFunction(() => {
      const el = document.querySelector('.accpanel');
      return el && !/betöltése/i.test(el.textContent);
    }, null, { timeout: 20000 });
    const szoveg = (await p.locator('.accpanel').innerText()).trim();
    console.log('   ' + eset.nev + ' -> ' + JSON.stringify(szoveg.slice(0, 70)));
    jo(eset.vart.test(szoveg), eset.nev);
    if (/zajlik/.test(szoveg))
      jo(!/eddig nincs pontot érő/.test(szoveg) && /MLSZ a pontokat a meccs végén/.test(szoveg),
        'a "zajlik" szöveg nem ígér élő pontot, hanem megmondja, mikor jön');
    jo(perr.length === 0, 'nincs JS-hiba (' + eset.nev + ')');
    await p.close();
  }

  // =============== 1-2) gyorsitotar-tores ===============
  console.log('\n--- Gyorsítótár: minden lekérés friss URL-re megy ---');
  for (const [liga, minta] of [['nb1', '**fantasy-api.mlsz.hu/**'], ['pl', '**draft.premierleague.com/**']]){
    const p = await br.newPage();
    const urlek = [], cacheMod = new Set();
    await p.route(minta, route => {
      const req = route.request();
      urlek.push(req.url());
      const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
      const u = decodeURIComponent(req.url());
      if (liga === 'pl'){
        if (/\/api\/game/.test(u)) return json({ current_event: 1, current_event_finished: false });
        if (/\/live/.test(u)) return json({ elements: {} });
        if (/\/fixtures/.test(u)) return json([]);
        return route.fulfill({ status: 404, body: '' });
      }
      const m = /filter\[search\]=([^&]+)/.exec(u);
      return json({ data: [{ user_team: { user: { id: 1, username: m ? m[1] : '' }, round_statistics: [] } }] });
    });
    // a no-store-t a Request objektumbol olvassuk ki
    p.on('request', r => { if (r.url().match(/mlsz|premierleague|corsproxy|allorigins/)) cacheMod.add(r.resourceType()); });
    await p.addInitScript(() => {
      window.__cacheMod = [];
      const eredeti = window.fetch;
      window.fetch = function (u, o) { window.__cacheMod.push((o || {}).cache || 'default'); return eredeti.apply(this, arguments); };
    });
    await p.goto(BASE + liga + '/', { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 150 && urlek.length === 0; i++) await p.waitForTimeout(100);
    await p.waitForTimeout(1200);
    const modok = await p.evaluate(() => window.__cacheMod.filter((_, i) => i > 0));
    const eloModok = await p.evaluate(() => window.__cacheMod);
    console.log('   ' + liga + ': ' + urlek.length + ' API-kérés, cache-módok: ' +
      JSON.stringify([...new Set(eloModok)]));
    jo(urlek.length > 0, liga + ': van API-kérés');
    if (liga === 'pl'){
      // az FPL belso URL-jere is kerul idobelyeg
      jo(urlek.every(u => /fpl_=\d+/.test(decodeURIComponent(u))),
        'PL: minden FPL-kérés kap időbélyeget');
      const egyedi = new Set(urlek.map(u => decodeURIComponent(u)));
      jo(egyedi.size === urlek.length, 'PL: nincs két azonos URL (' + egyedi.size + '/' + urlek.length + ')');
    }
    jo(eloModok.filter(m => m === 'no-store').length > 0, liga + ': no-store van a lekéréseken');
    await p.close();
  }

  // proxy-utvonal: idobelyeg a proxy URL-jen (a direkt utvonal elrontasaval kenyszeritjuk)
  console.log('\n--- Proxy-útvonal: a proxy URL-je is friss ---');
  {
    const p = await br.newPage();
    const proxyUrlek = [];
    await p.route('**fantasy-api.mlsz.hu/**', r => r.abort());            // direkt utvonal bukik
    await p.route('**corsproxy.io/**', route => {
      proxyUrlek.push(route.request().url());
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ data: [{ user_team: { user: { id: 1, username: 'x' }, round_statistics: [] } }] }) });
    });
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    for (let i = 0; i < 150 && proxyUrlek.length < 2; i++) await p.waitForTimeout(100);
    console.log('   corsproxy-kérések: ' + proxyUrlek.length);
    jo(proxyUrlek.length > 0 && proxyUrlek.every(u => /&_=\d+/.test(u)),
      'NB1: a corsproxy URL-je kap időbélyeget');
    jo(new Set(proxyUrlek).size === proxyUrlek.length,
      'NB1: nincs két azonos proxy-URL (' + new Set(proxyUrlek).size + '/' + proxyUrlek.length + ')');
    await p.close();
  }

  await br.close();
  process.exit(hibak.length ? 1 : 0);
})();
