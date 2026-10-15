const { BASE, check, launch, finish, rewriteJson } = require('./common');
// AZ NB1 NYUGALMI STATUSZSORA.
//
// Korabban "Naprakesz · ellenorizve <most>" allt itt: a kiirt ido a
// LEKERESE volt, nem az adate. A valogatott szunetben harom hetig ez allt a
// lapon, es nem latszott, hogy a tarolt adat regi-e, vagy csak nem tortent
// semmi. A sor most az utolso lezart forduloval es a tarolt adat utolso
// valtozasanak idejevel all.
//
// A teszt sajat allapotot allit be (nincs ideiglenes fordulo, az MLSZ egy
// pontot sem ad), nem a valos adat pillanatnyi tartalmara epul.
const TAROLT = '2026-08-30T10:00:00Z';

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 800 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  let utolso = null;
  await rewriteJson(p, '**/results.json*', j => {
    j.provisional = [];
    j.updated = TAROLT;
    const lejatszott = Object.keys(j.schedule || {}).map(Number)
      .filter(r => (j.schedule[r] || []).some(m => m[2] != null));
    utolso = Math.max(...lejatszott);
    return j;
  });
  await p.route('**://fantasy-api.mlsz.hu/**', route => {
    const u = route.request().url();
    if (u.includes('rankings')) {
      const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
      return route.fulfill({ json: { data: [{ user_team: { user: { id: 5000, username: uname },
        round_statistics: [] }, summary_statistics: {}, rounds: [] }] } });
    }
    return route.fulfill({ json: { data: [] } });
  });
  await p.route('**corsproxy.io/**', r => r.abort());
  await p.route('**allorigins**', r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => /ellenőrizve|hiba|nem elérhető/.test(
    document.getElementById('status').textContent), null, { timeout: 30000 });
  const szoveg = await p.evaluate(() => document.getElementById('status').textContent.trim());
  console.log('   státusz: ' + JSON.stringify(szoveg));

  check(/^Naprakész/.test(szoveg), 'nyugalomban „Naprakész"');
  check(szoveg.includes('utolsó lezárt: ' + utolso + '. forduló'),
     'kiírja az utolsó lezárt fordulót (' + utolso + '.)');
  check(/rögzítve: aug\. 30/.test(szoveg),
     'kiírja a TÁROLT adat utolsó változását, nem a lekérését');
  check(/ellenőrizve \d{2}:\d{2}$/.test(szoveg), 'és hogy mikor ellenőrizte');
  check(!perr.length, 'nincs JS-hiba: ' + JSON.stringify(perr));
  await finish(br);
})();
