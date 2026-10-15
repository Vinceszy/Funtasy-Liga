const { BASE, jo, cim, inditas, vege } = require('./kozos');
// AZ NB1 ELO LEKERES NEM MEGY EGYMAS UTAN.
//
// Az elo allas szakvezetonkent egy kulon MLSZ-lekeresbol all ossze (8 ember
// = 8 keres), es ez percenkent ujra lefut. Korabban mind a nyolc EGYMAS
// UTAN ment, egyenkent megvarva: nyolc kor-ut sorban - olyan adatert, ami
// az NB1-en naponta 2-4-szer valtozik (az MLSZ meccs kozben nem ad pontot).
//
// Most az ELSO keres megy egyedul - a lekero abbol tanulja meg, melyik
// proxy-ut mukodik -, a maradek het pedig egyszerre. Nyolc kor-utbol ketto.
//
// Amit rogzit:
//  - mind a nyolc szakvezeto adata megjon (a gyorsitas nem vesztett el senkit);
//  - az elso keres BEFEJEZODIK, mielott a masodik elindul (ut-tanulas);
//  - a maradek het EGYSZERRE indul (nem egymas utan);
//  - a teljes ido ket korre eleg, nem nyolcra;
//  - ha a parhuzamos korbol valaki elhasal, egyesevel ujraprobaljuk, es az
//    allasa megis bekerul.
const KESES = 250;          // mesterseges valaszido kersenkent (ms)
const TAGOK = 8;

function stub(page, naplo, bukjon){
  const bukott = new Set();
  // A tobbi utat azonnal elvagjuk, hogy a merest ne a proxy-sorrend zavarja:
  // igy minden keres ideje pontosan egy KESES.
  page.route('**workers.dev/**', r => r.abort());
  page.route('**corsproxy.io/**', r => r.abort());
  page.route('**allorigins**', r => r.abort());
  page.route('**cors.sh/**', r => r.abort());
  page.route('**cors.lol/**', r => r.abort());
  return page.route('**://fantasy-api.mlsz.hu/**', async route => {
    const u = route.request().url();
    if (!u.includes('rankings'))
      return route.fulfill({ json: { data: [] } });
    const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
    const t0 = Date.now();
    await new Promise(r => setTimeout(r, KESES));
    naplo.push({ uname, t0, t1: Date.now() });
    // a "bukjon" szakvezeto ELSO kerese elhasal, a masodik mar sikerul
    if (uname === bukjon && !bukott.has(uname)){
      bukott.add(uname);
      return route.fulfill({ status: 500, body: '' });
    }
    return route.fulfill({ json: { data: [{
      user_team: { user: { id: 5000, username: uname },
                   round_statistics: Array.from({ length: 33 },
                     (_, i) => ({ round_number: i + 1, points: 40 + i })) },
      summary_statistics: {}, rounds: [] }] } });
  });
}

const keszVar = p => p.waitForFunction(() => {
  const s = document.getElementById('status');
  return s && s.textContent && !/lekérése/.test(s.textContent);
}, null, { timeout: 40000 });

(async () => {
  const br = await inditas();

  // ---- 1) sorrend es ido ----
  cim('NB1: az élő lekérés két körben megy, nem nyolcban');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  const naplo = [];
  await stub(p, naplo, null);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await keszVar(p);

  jo(naplo.length === TAGOK,
     'mind a ' + TAGOK + ' szakvezető adata lekérődött — kapott: ' + naplo.length);

  const sorrend = [...naplo].sort((a, b) => a.t0 - b.t0);
  const elso = sorrend[0], tobbi = sorrend.slice(1);
  jo(elso.t1 <= tobbi[0].t0 + 5,
     'az első kérés befejeződik, mielőtt a második elindul (út-tanulás) — '
     + (tobbi[0].t0 - elso.t1) + ' ms különbség');

  const szoras = tobbi[tobbi.length - 1].t0 - tobbi[0].t0;
  jo(szoras < KESES,
     'a maradék ' + tobbi.length + ' egyszerre indul (indulásaik ' + szoras
     + ' ms-en belül, egy kérés ' + KESES + ' ms)');

  const teljes = Math.max(...naplo.map(x => x.t1)) - Math.min(...naplo.map(x => x.t0));
  jo(teljes < 4 * KESES,
     'a teljes lekérés két kör ideje (' + teljes + ' ms), nem nyolcé (~'
     + TAGOK * KESES + ' ms)');

  const allas = await p.evaluate(() => {
    const r = Object.keys(LIVE).map(Number).sort((a, b) => a - b)[0];
    return { r, sorok: (LIVE[r] || []).filter(Boolean).length };
  });
  jo(allas.sorok > 0,
     'az élő állás ki is töltődött (' + allas.r + '. forduló, ' + allas.sorok + ' meccs)');
  jo(!perr.length, 'nincs JS-hiba: ' + perr.join(' | '));
  await p.close();

  // ---- 2) az elhasalt keresst egyesevel ujraprobaljuk ----
  cim('NB1: aki a párhuzamos körből kiesik, azt újrakérjük');
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', e => qerr.push(e.message));
  const naplo2 = [];
  const BUKO = 'Hoxha98';                       // Bazsa - nem az elso a sorban
  await stub(q, naplo2, BUKO);
  await q.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await keszVar(q);

  const hany = naplo2.filter(x => x.uname === BUKO).length;
  jo(hany === 2, 'a bukott szakvezetőt pontosan egyszer kérjük újra — '
     + hany + ' kérés ment ki rá');

  const megvan = await q.evaluate(() => !!(USER_IDS['Bazsa']));
  jo(megvan, 'az újrakérés után az ő adata is bekerült');
  jo(!qerr.length, 'nincs JS-hiba: ' + qerr.join(' | '));
  await q.close();

  await vege(br);
})();
