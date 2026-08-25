const { BASE, jo, inditas, vege, jsonAtir } = require('./kozos');
// A ZARAS ES A GYUJTES KOZOTTI RES (PL).
//
// Az FPL a fordulot a "lockdown"-kor zarja (merve: 2026-08-25 08:03 es 08:23
// UTC kozott billent at minden), a gyujtonk viszont 3 orankent fut. A ket
// idopont kozott a game vegpont mar azt mondja, hogy current_event_finished,
// de a tarolt draft.json-ban meg nincs benne a fordulo eredmenye.
//
// Ez a res korabban "Naprakesz · ellenorizve <most>"-ot irt ki: a kiirt ido a
// LEKERESE volt, nem az adate - vagyis pont akkor allitotta magarol, hogy
// naprakesz, amikor bizonyithatoan nem volt az. Most megmondja, mi hianyzik.
//
// A teszt mindket allapotot KIMONDJA (nem a valos adatra tamaszkodik), mert
// a gyujto barmikor behozhatja az eredmenyt.
const GW = 1;

async function statuszSzoveg(br, eredmenyVan){
  const p = await br.newPage({ viewport: { width: 900, height: 800 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  // a fordulo mar lezarult az FPL szerint
  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: true });
    if (/event-status/.test(u)) return json({ status: [] });
    return json({});
  });
  // a tarolt adatban VAN vagy NINCS eredmeny erre a fordulora
  await jsonAtir(p, '**/draft.json*', j => {
    const s = (j.schedule && j.schedule[GW]) || [];
    j.schedule[GW] = s.map(m => eredmenyVan ? [m[0], m[1], 20, 30] : [m[0], m[1], null, null]);
    j.updated = '2026-08-25T05:47:00Z';
    return j;
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => {
    const el = document.getElementById('status');
    return el && el.textContent && !/lekérése/.test(el.textContent);
  }, null, { timeout: 20000 });
  const st = await p.evaluate(() => ({
    szoveg: document.getElementById('status').textContent.trim(),
    osztaly: document.getElementById('status').className,
  }));
  await p.close();
  return { ...st, perr };
}

(async () => {
  const br = await inditas();

  const hianyzik = await statuszSzoveg(br, false);
  console.log('   eredmény nélkül: ' + JSON.stringify(hianyzik.szoveg) + '  [' + hianyzik.osztaly + ']');
  jo(!/Naprakész/.test(hianyzik.szoveg),
     'lezárt forduló + hiányzó eredmény: NEM ír „Naprakész"-t');
  jo(/lezárult/.test(hianyzik.szoveg) && /adatfrissítéssel/.test(hianyzik.szoveg),
     'megmondja, mi hiányzik és mikor pótlódik');
  jo(/tárolt állás/.test(hianyzik.szoveg) && /aug\./.test(hianyzik.szoveg),
     'kiírja a TÁROLT állás idejét, nem a lekérését: ' + JSON.stringify(hianyzik.szoveg));
  jo(hianyzik.osztaly === 'varakozik',
     'saját jelölést kap (nem „ok", nem hiba): ' + JSON.stringify(hianyzik.osztaly));

  const megvan = await statuszSzoveg(br, true);
  console.log('   eredménnyel:     ' + JSON.stringify(megvan.szoveg) + '  [' + megvan.osztaly + ']');
  jo(/Naprakész/.test(megvan.szoveg) && megvan.osztaly === 'ok',
     'ha az eredmény már a tárolt adatban van, újra „Naprakész"');

  jo(!hianyzik.perr.length && !megvan.perr.length,
     'nincs JS-hiba: ' + JSON.stringify([...hianyzik.perr, ...megvan.perr]));
  await vege(br);
})();
