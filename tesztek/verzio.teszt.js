const { BASE, jo, cim, inditas, vege, apiKi } = require('./kozos');
// AZ ELAVULT LAP MAGATOL UJRATOLT.
//
// MIERT: a `?v=` a funtasy.js/css gyorsitotarat tori - a lap SAJAT HTML-jet
// NEM. Az oldalak HTML-jeben viszont eles logika el (kozos jatekosok
// parositasa, az elo keret-rekordok epitese, a meccsallapot), es egy regi
// HTML ezeket a REGI szabaly szerint futtatja. Egy nap alatt ketszer allt
// elo, hogy a javitas kint volt, a nezo megis a regi viselkedest latta - es
// semmi nem jelezte.
//
// A lap ezert megkerdezi a verzio.json-t. Harom allitas:
//   V1: azonos verzio -> NEM tolt ujra (kulonben minden lap kettot toltene)
//   V2: ujabb verzio  -> EGYSZER ujratolt
//   V3: ha az ujratoltes utan is regi marad, TOBBSZOR NEM probalja - inkabb
//       csendben marad, mint hogy oda-vissza toltson (hurok-vedelem)
async function meres(br, v, ut){
  const p = await br.newPage();
  let nav = 0;
  p.on('framenavigated', f => { if (f === p.mainFrame()) nav++; });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  await p.route('**/verzio.json*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify({ v: v }) }));
  await p.goto(BASE + ut, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(2500);
  await p.close();
  return { nav: nav, err: err };
}

(async () => {
  const br = await inditas();
  const sajat = +require('fs').readFileSync(
    require('path').join(__dirname, '..', 'verzio.json'), 'utf8').match(/\d+/)[0];

  cim('V1: azonos verziónál nincs újratöltés');
  const a = await meres(br, sajat, 'nb1/');
  jo(a.nav === 1, 'egyetlen betöltés (' + a.nav + ')');
  jo(a.err.length === 0, 'nincs JS-hiba' + (a.err.length ? ': ' + a.err.join(' | ') : ''));

  cim('V2: újabb verziónál EGYSZER újratölt');
  const b = await meres(br, sajat + 20, 'nb1/');
  jo(b.nav === 2, 'pontosan egy újratöltés (' + b.nav + ' navigáció)');
  jo(b.err.length === 0, 'nincs JS-hiba' + (b.err.length ? ': ' + b.err.join(' | ') : ''));

  cim('V3: a PL-oldal is ellenőrzi');
  const c = await meres(br, sajat + 20, 'pl/');
  jo(c.nav === 2, 'a PL-oldal is újratölt (' + c.nav + ' navigáció)');

  cim('V4: a verzio.json egyezik a lapok ?v= számával');
  // Ha elcsuszna, a vedelem vagy nem fogna, vagy VEGTELEN ujratoltest
  // okozna. A dokuk.py D6/b is nezi; itt a FUTO lapon ellenorizzuk.
  const p = await br.newPage();
  await apiKi(p);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  const lapV = await p.evaluate(() => {
    const sc = document.querySelector('script[src*="funtasy.js?v="]');
    return sc ? +sc.getAttribute('src').split('v=')[1] : null;
  });
  jo(lapV === sajat, 'a lap ?v=' + lapV + ' és a verzio.json v=' + sajat + ' egyezik');
  await p.close();
  await vege(br);
})();
