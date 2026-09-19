const { BASE, jo, cim, inditas, vege } = require('./kozos');
// AZ UTOLSO ISMERT ALLAS MAR AZ ELSO KEPEN OTT VAN (NB1).
//
// A KIZART HIBA: "ha valaki mar lekerdezte, lassam azt -
// ne lassak regebbi adatot, mint a legutobbi lekerdezes". A lap elso kepe
// eddig a repobol jott, amit a gyujto 3 orankent frissit: ha a telefon tiz
// perce mar lekerte a friss allast, a gepen megis a regi latszott, es meg
// is kellett varni, amig a nyolc elo lekeres lefut.
//
// Amit rogzit:
//  - a tarolt allas MAR AZELOTT kirajzolodik, hogy az elo lekeresek
//    befejezodnenek (ez a lenyeg: nem kell megvarni oket);
//  - a statuszsav a LEKERES idejet irja ki, nem a mostanit - vagyis nem
//    allitja magarol, hogy epp most ellenorizte;
//  - amint az elo lekeres beer, az veszi at a helyet;
//  - ures tarolonal semmi nem romlik el, a lap a szokasos uton megy.
const TAROLT_PONT = 77, ELO_PONT = 88;
const ELO_KESES = 1500;                 // az elo lekeres lassu: legyen ido merni
const PERCEKKEL_EZELOTT = 90;

const ketjegy = n => String(n).padStart(2, '0');

function utak(page, tarolo, szamlalo){
  page.route('**corsproxy.io/**', r => r.abort());
  page.route('**allorigins**', r => r.abort());
  page.route('**cors.sh/**', r => r.abort());
  page.route('**cors.lol/**', r => r.abort());
  // A sajat Worker: a /tarolt-ot kiszolgaljuk, a proxy-utat elvagjuk, hogy
  // az elo lekeres a kozvetlen uton (lentebb, keslelteve) menjen.
  page.route('**workers.dev/**', async route => {
    const u = new URL(route.request().url());
    if (u.pathname.replace(/\/+$/, '') !== '/tarolt') return route.abort();
    szamlalo.tarolt++;
    return route.fulfill({ status: 200, contentType: 'application/json',
                           body: JSON.stringify(tarolo(u)) });
  });
  return page.route('**://fantasy-api.mlsz.hu/**', async route => {
    const u = route.request().url();
    if (!u.includes('rankings')) return route.fulfill({ json: { data: [] } });
    const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
    await new Promise(r => setTimeout(r, ELO_KESES));
    szamlalo.elo++;
    return route.fulfill({ json: { data: [valasz(uname, ELO_PONT)] } });
  });
}
const valasz = (uname, pont) => ({
  user_team: { user: { id: 5000, username: uname },
               round_statistics: Array.from({ length: 33 },
                 (_, i) => ({ round_number: i + 1, points: pont })) },
  summary_statistics: {}, rounds: [],
});

(async () => {
  const br = await inditas();

  // ---- 1) a tarolt allas megelozi az elo lekerest ----
  cim('NB1: a tárolt állás már az első képen ott van');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  const sz = { tarolt: 0, elo: 0 };
  const ido = new Date(Date.now() - PERCEKKEL_EZELOTT * 60000);
  await utak(p, u => {
    const ki = {};
    for (const cel of u.searchParams.getAll('url')){
      const uname = decodeURIComponent((cel.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
      ki[cel] = { ido: ido.toISOString(),
                  adat: JSON.stringify({ data: [valasz(uname, TAROLT_PONT)] }) };
    }
    return ki;
  }, sz);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });

  // A LIVE reteget nezzuk, nem a kiirt szoveget: a "88" veletlenul benne van
  // egy archiv eredmenyben is ("71,88"), es a szoveges illesztes hamisan
  // talalt - a teszt zoldet mondott volna arra, hogy az elo lekeres beert.
  const eloErtekek = () => p.evaluate(() => Object.values(LIVE).flat()
    .filter(Boolean).map(x => x[2]));
  await p.waitForFunction(v => Object.values(LIVE).flat().filter(Boolean)
    .some(x => x[2] === v), TAROLT_PONT, { timeout: 20000 });
  const eloKesz = sz.elo;
  jo(eloKesz === 0,
     'a tárolt állás kirajzolódott, mielőtt bármelyik élő lekérés beért volna — '
     + eloKesz + ' élő válasz volt eddig');
  jo(sz.tarolt === 1, 'a tárolt állás EGYETLEN kör-útból jött — ' + sz.tarolt + ' kérés');

  const statusz = await p.evaluate(() => document.getElementById('status').textContent);
  const vartOra = ketjegy(ido.getHours()) + ':' + ketjegy(ido.getMinutes());
  jo(statusz.includes(vartOra),
     'a státuszsáv a LEKÉRÉS idejét írja (' + vartOra + '), nem a mostanit: ' + statusz);

  // ---- 2) az elo lekeres atveszi a helyet ----
  await p.waitForFunction(v => Object.values(LIVE).flat().filter(Boolean)
    .some(x => x[2] === v), ELO_PONT, { timeout: 30000 });
  const vegso = await eloErtekek();
  jo(vegso.length > 0 && vegso.every(x => x === ELO_PONT),
     'az élő lekérés felülírta a tároltat — élő értékek: ' + vegso.join(', '));
  jo(!perr.length, 'nincs JS-hiba: ' + perr.join(' | '));
  await p.close();

  // ---- 3) ures tarolo: minden megy a szokasos uton ----
  cim('NB1: üres tárolónál semmi nem romlik el');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  const sz2 = { tarolt: 0, elo: 0 };
  await utak(q, () => ({}), sz2);
  await q.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(v => Object.values(LIVE).flat().filter(Boolean)
    .some(x => x[2] === v), ELO_PONT, { timeout: 30000 });
  jo(true, 'az élő állás üres tároló mellett is megjelenik');
  jo(!qerr.length, 'nincs JS-hiba: ' + qerr.join(' | '));
  await q.close();

  await vege(br);
})();
