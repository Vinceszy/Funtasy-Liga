const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// ELO FORDULO ALATT A LAP MAGATOL FRISSUL (FunTasy.eloFrissito).
//
// BEJELENTETT HIBA (2026-08-30, PL): a nyitva hagyott lap a BETOLTESKORI
// allast mutatta - a meccs a 9. percnel allt, es a sorok ott is maradtak.
// A lenyilo bontas viszont kattintaskor sajat, friss lekerest indit, ezert
// az mar 90 percet mutatott: ugyanazon a kepernyon mondott ellent egymasnak
// a sor es a panelje. A panel volt a helyes.
//
// Amit rogzit:
//  - elo fordulonal a lap UJRA lekeri az allast, kattintas nelkul;
//  - a frissen erkezo pont MEG IS JELENIK (nem eleg lekerni);
//  - ha nincs folyo fordulo, egyetlen ismetelt keres sem megy ki;
//  - rejtett lapon all az ora (nem verjuk a kozvetitot a hatterben).
//
// Az idozito a tesztben 400 ms, hogy a sor ne varjon perceket: a keszlet a
// FunTasy.eloFrissito masodik parametere.
const KOZ = 400;
const allas = p => p.evaluate(() => [...document.querySelectorAll('.match .score')]
  .map(x => x.textContent.trim()).join(' '));

(async () => {
  const br = await inditas();

  cim('PL: élő fordulónál magától frissül');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);
  // az ora kozet a lapba injektaljuk, mielott a sajat szkript lefutna
  await p.addInitScript(k => { window.ELO_ORA_KOZ = k; }, KOZ);

  let liveKeres = 0, pont = 4;
  // AZ ELO FORDULO a LEGFRISSEBB tarolt fordulo - nem egy beirt szam. A
  // teszt korabban fixen a 2.-at tette elove, mert akkor annak meg nem volt
  // eredmenye; a lezarasaval a lap mar nem az elo overlaybe tette, es a
  // teszt semmit nem mert. Az elofeltetelt ezert KIMONDJUK: a menetrendbol
  // menet kozben kivesszuk a fordulo eredmenyet.
  const HIST = require(require('path').join(__dirname, '..', 'draft_history.json'));
  const GW = Object.keys(HIST.rounds).map(Number).sort((a, b) => b - a)[0] + '';
  await jsonAtir(p, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  });
  await p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/live/.test(u)){
      liveKeres++;
      const el = {};
      for (const lid of Object.keys(HIST.rounds[GW] || {}))
        for (const x of HIST.rounds[GW][lid])
          el[x.e] = { stats: { total_points: pont, minutes: 90 }, explain: [] };
      return json({ elements: el });
    }
    return route.fulfill({ status: 404, body: '' });
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  // az ELSO elo lekerest megvarjuk - enelkul a szamlalot azelott olvasnank ki
  // typeof-fal: a LIVEPTS const/let, tehat NINCS a window-on (ugyanaz a
  // csapda, mint a USER_IDS-nel az uzenetek-tesztben).
  await p.waitForFunction(() => typeof LIVEPTS !== 'undefined'
                             && Object.keys(LIVEPTS).length > 0, null, { timeout: 30000 });
  const elso = liveKeres, allasElotte = await allas(p);
  jo(elso > 0, 'a betöltés lekéri az élő állást (' + elso + ' kérés)');
  jo(/\d/.test(allasElotte), 'az élő állás megjelenik: ' + allasElotte.slice(0, 40));

  // A LENYEG: kattintas es fokuszvaltas NELKUL is frissulnie kell.
  pont = 9;                                   // kozben valtozik az allas
  await new Promise(r => setTimeout(r, KOZ * 3));
  jo(liveKeres > elso,
     'élő fordulónál magától újra lekéri az állást (' + elso + ' → ' + liveKeres + ')');
  const allasUtana = await allas(p);
  // A kezdok szama 11, tehat a kiirt elo allasnak 11*4 = 44-rol 11*9 = 99-re
  // kell valtania. Nem azt allitjuk, hogy "valtozott valami" - azt, hogy a
  // KONKRET uj szam megjelent, kulonben a teszt egy szokoz-elteresre is zold.
  jo(/\b44\b/.test(allasElotte),
     'betöltéskor a 4 pontos állás (44) látszik: ' + allasElotte);
  jo(/\b99\b/.test(allasUtana) && !/\b44\b/.test(allasUtana),
     'magától átvált a 9 pontos állásra (99), és a régi (44) eltűnik: ' + allasUtana);
  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr.slice(0, 2)));
  await p.close();

  cim('Nincs folyó forduló: egyetlen ismételt kérés sem megy ki');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  await apiKi(q);
  await q.addInitScript(k => { window.ELO_ORA_KOZ = k; }, KOZ);
  let qLive = 0;
  await q.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json',
                                      body: JSON.stringify(b) });
    if (/event-status/.test(u)) return json({ status: [] });
    // LEZART fordulo: nincs mit frissiteni
    if (/\/api\/game/.test(u)) return json({ current_event: 1, current_event_finished: true });
    if (/\/fixtures/.test(u)) return json([]);
    if (/\/live/.test(u)){ qLive++; return json({ elements: {} }); }
    return route.fulfill({ status: 404, body: '' });
  });
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForSelector('#table tr', { timeout: 30000 });
  const q0 = qLive;
  await new Promise(r => setTimeout(r, KOZ * 4));
  jo(qLive === q0,
     'lezárt fordulónál nem megy ki ismételt kérés (' + q0 + ' → ' + qLive + ')');
  jo(qerr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(qerr.slice(0, 2)));

  await vege(br);
})();
