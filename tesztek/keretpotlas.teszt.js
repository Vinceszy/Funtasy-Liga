const path = require('path');
const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// A FOLYO FORDULO KERETEIT A BONGESZO POTOLJA, AMIG A GYUJTO MEG NEM IRTA BE.
//
// MEGTORTENT (2026-09-18, PL 5. fordulo): elo meccs alatt a lap nem frissult.
// A gyujto 3 orankent fut, a fordulo viszont a nevezesi hataridovel indul: a
// 16:43 UTC-s futas MEG a 4. fordulot latta, a kovetkezo 23:47-re volt
// idozitve - kozben elindult az 5., es a repoban egyaltalan nem letezett
// hozza keret. A lap kiment az API-ra, meg is kapta az elo pontokat, csak
// nem volt kire raterite oket: elo allas helyett "Naprakesz" allt a
// statuszsavban egy futo meccs alatt.
//
// Amit rogzit:
//  - hianyzo keretnel a bongeszo lekeri a fordulo kereteit, es lesz elo allas;
//  - a potlas a gyujto adatat NEM irja felul;
//  - RESZLEGES potlasnal (egy csapat lekerese elhasal) az erintett meccs
//    NEM kap hamis 0-t, a tobbi viszont igen.
const HIST = require(path.join(__dirname, '..', 'draft_history.json'));
const DRAFT = require(path.join(__dirname, '..', 'draft.json'));

// AZ ELO FORDULO a legfrissebb tarolt fordulo. Az elofeltetelt kimondjuk:
// menet kozben kivesszuk a menetrendbol az eredmenyet (kulonben a lap
// lezartkent kezelne), a keret-elozmenybol pedig magat a fordulot - EZ a
// vizsgalt helyzet: fut a fordulo, de a gyujto meg nem irt hozza keretet.
const GW = Object.keys(HIST.rounds).map(Number).sort((a, b) => b - a)[0] + '';
const LIDK = Object.keys(HIST.rounds[GW]);
const EID = {};                       // liga_id -> kitalalt FPL entry_id
LIDK.forEach((lid, i) => { EID[lid] = 900001 + i; });

const elofeltetel = p => Promise.all([
  jsonAtir(p, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  }),
  jsonAtir(p, '**/draft_history.json*', j => {
    delete j.rounds[GW];
    j.veglegesek = (j.veglegesek || []).filter(x => +x !== +GW);
    return j;
  }),
]);

// A fordulo osszes jatekosa 1 pontot er, tehat minden csapat elo osszege 11
// (a pad nem szamit). Igy egyetlen szambol latszik, sikerult-e a potlas.
const VART = 11;

function utvonalak(p, bukjon) {       // bukjon: ennek a liga-idnek a kerete nem jon meg
  return p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/league\/\d+\/details/.test(u))
      return json({ league_entries: LIDK.map(lid => ({ id: +lid, entry_id: EID[lid] })) });
    const m = u.match(/\/entry\/(\d+)\/event\/(\d+)/);
    if (m){
      const lid = LIDK.find(x => EID[x] === +m[1]);
      if (!lid || lid === bukjon) return route.fulfill({ status: 404, body: '' });
      // ugyanaz a szerkezet, amit az FPL ad: position 1-11 kezdo, 12-15 pad
      return json({ picks: (HIST.rounds[GW][lid] || [])
        .map((x, i) => ({ element: x.e, position: i + 1 })) });
    }
    if (/\/live/.test(u)){
      const el = {};
      for (const lid of LIDK)
        for (const x of HIST.rounds[GW][lid])
          el[x.e] = { stats: { total_points: 1, minutes: 90, starts: 1 },
                      explain: [[[{ name: 'Minutes played', points: 1, value: 90,
                                    stat: 'minutes' }], 1]] };
      return json({ elements: el });
    }
    return route.fulfill({ status: 404, body: '' });
  });
}

const allasok = p => p.evaluate(() => [...document.querySelectorAll('.match .score')]
  .map(x => x.textContent.trim()));

(async () => {
  const br = await inditas();

  // ---- 1) teljes potlas ----
  cim('PL: a böngésző pótolja a folyó forduló kereteit');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);
  await elofeltetel(p);
  await utvonalak(p, null);
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(g => typeof POTKER !== 'undefined' && !!POTKER[g],
                          GW, { timeout: 30000 });

  const potolt = await p.evaluate(g => Object.keys(POTKER[g] || {}).length, GW);
  jo(potolt === LIDK.length,
     'mind a ' + LIDK.length + ' keretet pótolta — kapott: ' + potolt);

  const nincsHist = await p.evaluate(g => !HIST[g], GW);
  jo(nincsHist, 'a tárolt adatban tényleg nincs keret ehhez a fordulóhoz (az előfeltétel áll)');

  const a1 = await allasok(p);
  jo(a1.some(x => new RegExp('\\b' + VART + '\\b').test(x)),
     'az élő meccsállás megjelenik a pótolt keretből (' + VART + '): ' + a1.join(' | '));

  const statusz = await p.evaluate(() => document.getElementById('status').textContent);
  jo(/él/i.test(statusz), 'a státuszsáv élő fordulót jelez: ' + statusz);
  jo(!perr.length, 'nincs JS-hiba: ' + perr.join(' | '));
  await p.close();

  // ---- 2) reszleges potlas: a hianyzo csapat meccse NEM kap hamis 0-t ----
  cim('PL: részleges pótlásnál nincs hamis állás');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  await apiKi(q);
  await elofeltetel(q);
  const bukott = LIDK[0];
  await utvonalak(q, bukott);
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(g => typeof POTKER !== 'undefined' && !!POTKER[g],
                          GW, { timeout: 30000 });

  const reszleges = await q.evaluate(g => Object.keys(POTKER[g] || {}).length, GW);
  jo(reszleges === LIDK.length - 1,
     'egy keret hiányzik, a többi megvan (' + (LIDK.length - 1) + ') — kapott: ' + reszleges);

  // a bukott csapat meccsen a ket fel egyike sem kap elo szamot
  const ervenyes = await q.evaluate(([g, b]) => {
    const sor = (SCHEDULE[g] || []).findIndex(m => String(m[0]) === b || String(m[1]) === b);
    return { sor, meccsek: (SCHEDULE[g] || []).length,
             elo: (LIVE[g] || [])[sor] || null,
             masik: (LIVE[g] || []).filter(Boolean).length };
  }, [GW, bukott]);
  jo(ervenyes.elo === null,
     'a hiányzó kerethez tartozó meccs NEM kap élő állást (a 0 hamis szám lenne) — kapott: '
     + JSON.stringify(ervenyes.elo));
  jo(ervenyes.masik === ervenyes.meccsek - 1,
     'a többi meccs viszont kap élő állást (' + (ervenyes.meccsek - 1) + ') — kapott: '
     + ervenyes.masik);

  const a2 = await allasok(q);
  jo(a2.some(x => new RegExp('\\b' + VART + '\\b').test(x)),
     'a teljes keretű meccseken ott az élő állás: ' + a2.join(' | '));
  jo(!qerr.length, 'nincs JS-hiba: ' + qerr.join(' | '));
  await q.close();

  await vege(br);
})();
