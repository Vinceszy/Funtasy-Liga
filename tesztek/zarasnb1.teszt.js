const { BASE, jo, cim, inditas, vege, apiKi } = require('./kozos');
// Meccs utani pontigazitas panel (NB1). Amit rogzit:
//   - a panel CSAK akkor latszik, ha van adat (elesben ez ritka esemeny,
//     es egy allandoan ures doboz azt sugallna, hogy valami hianyzik);
//   - a legutolso ilyen fordulot mutatja alapbol, es lapozni lehet;
//   - a valtozas iranya latszik (elojel es szin), a jatekos SAJAT pontjaval;
//   - a megjelenites UGYANAZ, mint a PL "Zarasi valtozasok" panelje:
//     szakvezeto szerint csoportositva, kattinthato nevekkel.
const ADAT = { updated: 'x', rounds: {
  '4': { Bazsa: { pont: [
          { n: 'Egyik Elek', cp: 1, pos: 'MF', tm: 'MTK', elott: 5, utan: 6, d: '2026-08-20' }] } },
  '5': { Bazsa: { pont: [
          { n: 'Teszt Elek', cp: 2, pos: 'DF', tm: 'FTC', elott: 9.25, utan: 6.75, d: '2026-08-24' }] },
         Csendi: { pont: [
          { n: 'Másik Elek', cp: 3, pos: 'FW', tm: 'DVSC', elott: 1, utan: 2, d: '2026-08-24' }] } } } };

(async () => {
  const br = await inditas();

  // ---- nincs adat: a panel rejtve marad ----
  cim('Adat nélkül nincs panel');
  const ures = await br.newPage();
  await apiKi(ures);
  await ures.route('**/zarasok_nb1.json*', r => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ updated: 'x', rounds: {} }) }));
  await ures.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await ures.waitForSelector('#table tr', { timeout: 20000 });
  jo(await ures.locator('#znPanel').isVisible() === false,
     'üres adatnál a panel nem jelenik meg');
  await ures.close();

  // ---- hianyzo fajl sem torhet el semmit ----
  const nincs = await br.newPage();
  const nerr = []; nincs.on('pageerror', e => nerr.push(e.message));
  await apiKi(nincs);
  await nincs.route('**/zarasok_nb1.json*', r => r.fulfill({ status: 404, body: '' }));
  await nincs.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await nincs.waitForSelector('#table tr', { timeout: 20000 });
  jo(await nincs.locator('#znPanel').isVisible() === false && nerr.length === 0,
     'hiányzó fájlnál sincs panel és nincs JS-hiba' + (nerr.length ? ': ' + nerr.join(' | ') : ''));
  await nincs.close();

  // ---- adattal ----
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);
  await p.route('**/zarasok_nb1.json*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(ADAT) }));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#znPanel:not([style*="none"])', { timeout: 20000 });

  cim('Tartalom');
  jo((await p.$eval('#selZaras', e => e.value)) === '5',
     'alapból a legutolsó ilyen fordulót mutatja');
  const fejek = await p.$$eval('#znBody .zcsapat h3', a => a.map(x => x.textContent.trim()));
  jo(JSON.stringify(fejek) === JSON.stringify(['Bazsa', 'Csendi']),
     'szakvezető szerint csoportosít, névsorban (' + fejek.join(', ') + ')');
  const sorok = await p.$$eval('#znBody .zsor', a => a.map(x => x.innerText.replace(/\n/g, ' ')));
  jo(sorok.length === 2, 'a forduló minden változása látszik (' + sorok.length + ')');
  jo(/Teszt Elek/.test(sorok[0]) && /FTC/.test(sorok[0]),
     'a konkrét játékos neve és klubja ott van (' + sorok[0] + ')');
  jo(/9,25\s*→\s*6,75/.test(sorok[0]) && /-2,5/.test(sorok[0]),
     'a régi és az új érték, valamint az előjeles különbség is ott van (' + sorok[0] + ')');
  jo((await p.$$eval('#znBody .zdiff.neg', a => a.length)) === 1
     && (await p.$$eval('#znBody .zdiff.pos', a => a.length)) === 1,
     'a csökkenés és a növekedés külön színt kap');
  jo((await p.$$eval('#znBody .ppos', a => a.map(x => x.textContent.trim()))).length === 2,
     'minden sor elején ott a poszt-címke');

  cim('Kattintható nevek');
  // A jatekos neve profilt nyit, a szakvezeto neve a keretet - ugyanugy,
  // mint a PL panelen (ott data-team, itt data-member).
  jo((await p.$eval('#znBody .zsor .znev', e => e.dataset.prof)) === 'Teszt Elek'
     && (await p.$eval('#znBody .zsor .znev', e => e.dataset.pcp)) === '2',
     'a játékos neve a profilra mutat');
  jo((await p.$eval('#znBody .zcsapat h3', e => e.dataset.member)) === 'Bazsa',
     'a szakvezető neve a keretre mutat');
  await p.click('#znBody .zsor .znev');
  await p.waitForSelector('#ov.open', { timeout: 5000 });
  jo(/Teszt Elek/.test(await p.$eval('#mTitle', e => e.textContent)),
     'a játékos nevére kattintva a profilja nyílik');
  await p.click('#ovClose'); await p.waitForTimeout(200);

  cim('Lapozás');
  await p.click('[data-znav="-1"]');
  await p.waitForFunction(() => document.querySelector('#selZaras').value === '4',
                          null, { timeout: 5000 });
  jo(/Egyik Elek/.test(await p.$eval('#znBody', e => e.innerText)),
     'a nyíllal a korábbi fordulóra lehet lépni');
  // a 4. az elso ilyen fordulo: onnan a visszalepes nem vihet sehova
  await p.click('[data-znav="-1"]');
  jo((await p.$eval('#selZaras', e => e.value)) === '4',
     'az első fordulónál a visszalépés nem visz sehova (nem esik ki a listából)');

  jo(perr.length === 0, 'nincs JS-hiba' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await vege(br);
})();
