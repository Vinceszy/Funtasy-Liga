const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// Frissites, amikor a lap ismet lathatova valik (FunTasy.ujraLathatokor).
// 1) egysegteszt a segitore, 2) e2e a PL-oldalon mockolt FPL-API-val:
//    a fooldal tenyleg ujra lekeri-e az elo pontokat visszatereskor.

(async () => {
  const br = await inditas();

  // ---------------- 1. egysegteszt ----------------
  let p = await br.newPage();
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => window.FunTasy && FunTasy.ujraLathatokor);

  const e = await p.evaluate(async () => {
    const var_ = ms => new Promise(r => setTimeout(r, ms));
    const ki = {};
    const bfPageshow = () => {
      const ps = new Event('pageshow');
      Object.defineProperty(ps, 'persisted', { value: true });
      window.dispatchEvent(ps);
    };

    // a) mindharom esemenyfajta indit (minKoz=0, kozottuk megvarjuk a futast)
    let n = 0;
    FunTasy.ujraLathatokor(() => { n++; }, 0);
    document.dispatchEvent(new Event('visibilitychange')); await var_(40);
    window.dispatchEvent(new Event('focus'));              await var_(40);
    bfPageshow();                                          await var_(40);
    ki.harom = n;

    // b) a sima (nem bfcache-es) pageshow nem indit - az friss betoltes
    let n2 = 0;
    FunTasy.ujraLathatokor(() => { n2++; }, 0);
    window.dispatchEvent(new Event('pageshow')); await var_(40);
    ki.simaPageshow = n2;

    // c) a betoltes utani ablakban nem ker le ujra (akkor eppen most kertunk)
    let n3 = 0;
    FunTasy.ujraLathatokor(() => { n3++; }, 30000);
    document.dispatchEvent(new Event('visibilitychange')); await var_(40);
    ki.frissenBetoltve = n3;

    // d) futo frissites alatt nem indul masik
    let indult = 0;
    FunTasy.ujraLathatokor(() => { indult++; return var_(300); }, 0);
    document.dispatchEvent(new Event('visibilitychange')); await var_(50);
    document.dispatchEvent(new Event('visibilitychange')); await var_(400);
    ki.parhuzamos = indult;

    // e) hibaba futo frissites nem akasztja meg a kovetkezot
    let n5 = 0;
    FunTasy.ujraLathatokor(() => { n5++; throw new Error('teszt'); }, 0);
    document.dispatchEvent(new Event('visibilitychange')); await var_(40);
    document.dispatchEvent(new Event('visibilitychange')); await var_(40);
    ki.hibaUtan = n5;
    return ki;
  });

  console.log('--- egységteszt ---');
  jo(e.harom === 3, 'mindhárom esemény indít (visibilitychange, focus, bfcache-es pageshow): ' + e.harom);
  jo(e.simaPageshow === 0, 'a sima (nem bfcache-es) pageshow nem indít: ' + e.simaPageshow);
  jo(e.frissenBetoltve === 0, 'frissen betöltött lapon nem kér le újra: ' + e.frissenBetoltve);
  jo(e.parhuzamos === 1, 'futó frissítés alatt nem indul másik: ' + e.parhuzamos);
  jo(e.hibaUtan === 2, 'hibába futó frissítés után a következő elindul: ' + e.hibaUtan);
  await p.close();

  // ---------------- 2. e2e a PL-oldalon, mockolt FPL-API-val ----------------
  console.log('\n--- e2e: PL főoldal ---');
  p = await br.newPage();
  await p.addInitScript(() => {                 // tekerheto ora a fojtas miatt
    window.__ora = 0;
    const eredeti = Date.now;
    Date.now = () => eredeti() + window.__ora;
  });

  // A jatekos-pontok minden lekeresnel valtoznak: igy latszik, atjott-e a friss.
  let liveHivas = 0, pont = 5;
  const hist = require(require('path').join(__dirname,'..','draft_history.json'));
  const GW = Object.keys(hist.rounds)[0];
  const elemek = [...new Set(Object.values(hist.rounds[GW]).flat().map(x => x.e))];
  await p.route('**draft.premierleague.com/api/**', route => {
    const u = route.request().url();
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/live/.test(u)){
      liveHivas++; pont++;
      const el = {};
      elemek.forEach(id => { el[id] = { stats: { total_points: pont, minutes: 90 }, explain: [] }; });
      return json({ elements: el });
    }
    if (/\/fixtures/.test(u)) return json([]);
    return route.fulfill({ status: 404, body: '' });
  });
  const perr = []; p.on('pageerror', x => perr.push(x.message));

  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  // A statuszsav "lekeres" uzenete is tartalmazza az "Elo allas" szot, ezert
  // nem arra varunk, hanem magara a lekeresre - es az azt koveto rajzolasra.
  for (let i = 0; i < 200 && liveHivas === 0; i++) await p.waitForTimeout(100);
  await p.waitForTimeout(600);
  const betolteskor = liveHivas;
  const allas1 = await p.$$eval('.match .score', ns => ns.map(n => n.textContent.trim()).join(' | '));
  console.log('   /live lekérés betöltéskor:', betolteskor);
  console.log('   állás betöltéskor:', allas1.slice(0, 90));
  jo(betolteskor > 0, 'betöltéskor lekéri az élő pontokat');

  // visszateres a laphoz
  await p.evaluate(() => { window.__ora = 120000; });
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(1200);
  const allas2 = await p.$$eval('.match .score', ns => ns.map(n => n.textContent.trim()).join(' | '));
  console.log('   /live lekérés visszatérés után:', liveHivas);
  console.log('   állás visszatérés után:', allas2.slice(0, 90));
  jo(liveHivas > betolteskor, 'visszatéréskor újra lekéri az élő pontokat');
  jo(allas1 !== allas2, 'a főoldali meccslista állása tényleg frissül (nem fagy be)');

  // fojtas: azonnali masodik visszateres ne inditson ujabbat
  const elozo = liveHivas;
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(800);
  jo(liveHivas === elozo, 'közvetlenül utána nem kér le újra (fojtás): ' + liveHivas);

  // idozitett frissites szandekosan NINCS
  await p.evaluate(() => { window.__ora = 900000; });
  await p.waitForTimeout(2000);
  jo(liveHivas === elozo, 'nyitva hagyott lapon magától nem kér le: ' + liveHivas);

  // Masodik visszateres: mar mindket allas ki van toltve, tehat ez mutatja
  // igazan, hogy a MAR KIIRT pontszam is kovetni tudja a valtozast (ez volt
  // a bejelentett hiba: a fooldalon 39 maradt, mikozben mar 38 volt).
  await p.evaluate(() => { window.__ora = 1800000; });
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(1200);
  const allas3 = await p.$$eval('.match .score', ns => ns.map(n => n.textContent.trim()).join(' | '));
  console.log('   /live lekérés 2. visszatérés után:', liveHivas);
  console.log('   állás 2. visszatérés után:', allas3.slice(0, 90));
  jo(liveHivas === elozo + 1, 'a második visszatérés is lekér: ' + liveHivas);
  jo(allas2 !== allas3 && /\d/.test(allas2) && /\d/.test(allas3),
    'a már kiírt pontszám is követi a változást (' + allas2.slice(0, 12) + ' -> ' + allas3.slice(0, 12) + ')');

  console.log('   pageerror:', perr.length ? perr : 'nincs');
  jo(perr.length === 0, 'nincs JS-hiba a PL-oldalon');
  await p.close();

  // ---------------- 3. e2e az NB1-oldalon ----------------
  // Ott a ranglista-vegpont az elo forras; ugyanugy visszatereskor kell ujra.
  console.log('\n--- e2e: NB1 főoldal ---');
  p = await br.newPage();
  await p.addInitScript(() => {
    window.__ora = 0;
    const eredeti = Date.now;
    Date.now = () => eredeti() + window.__ora;
  });
  // Egy NB1-frissites 8 szakvezetot ker le egymas utan, tehat sok kerest ad
  // ki. A frissitesek SZAMAT az elso szakvezeto lekerese meri (fordulonkent
  // pontosan egyszer szerepel), nem a nyers keresszam.
  let rankHivas = 0, elsoUname = null;
  await p.route('**fantasy-api.mlsz.hu/**', route => {
    const u = decodeURIComponent(route.request().url());
    const m = /filter\[search\]=([^&]+)/.exec(u);
    const uname = m ? m[1] : '';
    if (elsoUname === null) elsoUname = uname;
    if (uname === elsoUname) rankHivas++;
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      data: [{ user_team: { user: { id: 1, username: uname }, round_statistics: [] } }] }) });
  });
  const perr2 = []; p.on('pageerror', x => perr2.push(x.message));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  for (let i = 0; i < 200 && rankHivas === 0; i++) await p.waitForTimeout(100);
  await p.waitForTimeout(1500);
  const nb1Betoltes = rankHivas;
  console.log('   ranglista-lekérés betöltéskor:', nb1Betoltes);
  jo(nb1Betoltes > 0, 'betöltéskor lekéri a ranglistát');

  await p.evaluate(() => { window.__ora = 120000; });
  await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForTimeout(1500);
  console.log('   ranglista-lekérés visszatérés után:', rankHivas);
  jo(rankHivas > nb1Betoltes, 'visszatéréskor az NB1-oldal is újra lekér');

  const nb1Elozo = rankHivas;
  await p.evaluate(() => { window.__ora = 900000; });
  await p.waitForTimeout(2000);
  jo(rankHivas === nb1Elozo, 'nyitva hagyott NB1-lapon magától nem kér le: ' + rankHivas);
  console.log('   pageerror:', perr2.length ? perr2 : 'nincs');
  jo(perr2.length === 0, 'nincs JS-hiba az NB1-oldalon');
  await p.close();

  await br.close();
  process.exit(hibak.length ? 1 : 0);
})();
