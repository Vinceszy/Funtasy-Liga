const { BASE, check, section, launch, finish, blockApis } = require('./common');
// Meccs utani pontigazitas panel (NB1). Amit rogzit:
//   - a panel CSAK akkor latszik, ha van adat (elesben ez ritka esemeny,
//     es egy allandoan ures doboz azt sugallna, hogy valami hianyzik);
//   - a legordulo MINDEN lejatszott fordulot felsorol: ahol nem volt
//     valtozas, ott az a hir, hogy nem volt;
//   - alapbol a LEGUTOLSO fordulon all (akkor is, ha abban nem volt
//     valtozas), es lapozni lehet;
//   - a valtozas iranya latszik (elojel es szin), a jatekos SAJAT pontjaval;
//   - a megjelenites UGYANAZ, mint a PL "Zarasi valtozasok" panelje:
//     szakvezeto szerint csoportositva, kattinthato nevekkel.
const ADAT = { updated: 'x', rounds: {
  '2': { Bazsa: { pont: [
          { n: 'Egyik Elek', cp: 1, pos: 'MF', tm: 'MTK', elott: 5, utan: 6, d: '2026-08-20' }] } },
  // Ismeretlen jatekos: csak a valtozas merteke tudott, a jatekos nem
  '3': { Csendi: { pont: [
          { n: '', cp: null, pos: '', tm: '', elott: null, utan: null, dl: -2.5, d: '2026-08-20', nk: 1 }] } },
  '4': { Bazsa: { pont: [
          { n: 'Teszt Elek', cp: 2, pos: 'DF', tm: 'FTC', elott: 9.25, utan: 6.75, d: '2026-08-24' }] },
         Csendi: { pont: [
          { n: 'Másik Elek', cp: 3, pos: 'FW', tm: 'DVSC', elott: 1, utan: 2, d: '2026-08-24' }] } } } };

(async () => {
  const br = await launch();

  // ---- nincs adat: a panel rejtve marad ----
  section('Adat nélkül nincs panel');
  const ures = await br.newPage();
  await blockApis(ures);
  await ures.route('**/zarasok_nb1.json*', r => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ updated: 'x', rounds: {} }) }));
  await ures.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await ures.waitForSelector('#table tr', { timeout: 20000 });
  check(await ures.locator('#znPanel').isVisible() === false,
     'üres adatnál a panel nem jelenik meg');
  await ures.close();

  // ---- hianyzo fajl sem torhet el semmit ----
  const nincs = await br.newPage();
  const nerr = []; nincs.on('pageerror', e => nerr.push(e.message));
  await blockApis(nincs);
  await nincs.route('**/zarasok_nb1.json*', r => r.fulfill({ status: 404, body: '' }));
  await nincs.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await nincs.waitForSelector('#table tr', { timeout: 20000 });
  check(await nincs.locator('#znPanel').isVisible() === false && nerr.length === 0,
     'hiányzó fájlnál sincs panel és nincs JS-hiba' + (nerr.length ? ': ' + nerr.join(' | ') : ''));
  await nincs.close();

  // ---- adattal ----
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  await p.route('**/zarasok_nb1.json*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(ADAT) }));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#znPanel:not([style*="none"])', { timeout: 20000 });

  section('Tartalom');
  // AZ ELVART FORDULOT AZ ADATBOL SZAMOLJUK, nem beegetve. Korabban itt "5"
  // allt - az volt akkor az utolso lejatszott fordulo -, es a 6. lezarasaval
  // a teszt bukni kezdett, holott a termekkel semmi baj nem volt. A
  // naptartol fuggo allando elobb-utobb mindig elavul.
  const utolso = await p.evaluate(() => T.lastPlayedRound());
  // Az utolso lejatszott forduloban NINCS valtozas a mockolt adatban: a
  // lapozo akkor is ott all, mert az is hir, hogy nem tortent semmi.
  check((await p.$eval('#selZaras', e => e.value)) === String(utolso),
     'alapból az utolsó fordulón áll a lapozó (' + utolso + '.)');
  check(/Nem történt változás/.test(await p.$eval('#znBody', e => e.innerText)),
     'változás nélküli fordulónál ezt meg is mondja');
  await p.selectOption('#selZaras', '4'); await p.waitForTimeout(200);
  const fejek = await p.$$eval('#znBody .zcsapat h3', a => a.map(x => x.textContent.trim()));
  check(JSON.stringify(fejek) === JSON.stringify(['Bazsa', 'Csendi']),
     'szakvezető szerint csoportosít, névsorban (' + fejek.join(', ') + ')');
  const sorok = await p.$$eval('#znBody .zsor', a => a.map(x => x.innerText.replace(/\n/g, ' ')));
  check(sorok.length === 2, 'a forduló minden változása látszik (' + sorok.length + ')');
  check(/Teszt Elek/.test(sorok[0]) && /FTC/.test(sorok[0]),
     'a konkrét játékos neve és klubja ott van (' + sorok[0] + ')');
  check(/9,25\s*→\s*6,75/.test(sorok[0]) && /-2,5/.test(sorok[0]),
     'a régi és az új érték, valamint az előjeles különbség is ott van (' + sorok[0] + ')');
  check((await p.$$eval('#znBody .zdiff.neg', a => a.length)) === 1
     && (await p.$$eval('#znBody .zdiff.pos', a => a.length)) === 1,
     'a csökkenés és a növekedés külön színt kap');
  check((await p.$$eval('#znBody .ppos', a => a.map(x => x.textContent.trim()))).length === 2,
     'minden sor elején ott a poszt-címke');

  section('Kattintható nevek');
  // A jatekos neve profilt nyit, a szakvezeto neve a keretet - ugyanugy,
  // mint a PL panelen (ott data-team, itt data-member).
  check((await p.$eval('#znBody .zsor .znev', e => e.dataset.prof)) === 'Teszt Elek'
     && (await p.$eval('#znBody .zsor .znev', e => e.dataset.pcp)) === '2',
     'a játékos neve a profilra mutat');
  check((await p.$eval('#znBody .zcsapat h3', e => e.dataset.member)) === 'Bazsa',
     'a szakvezető neve a keretre mutat');
  await p.click('#znBody .zsor .znev');
  await p.waitForSelector('#ov.open', { timeout: 5000 });
  check(/Teszt Elek/.test(await p.$eval('#mTitle', e => e.textContent)),
     'a játékos nevére kattintva a profilja nyílik');
  await p.click('#ovClose'); await p.waitForTimeout(200);

  section('Lapozás');
  const fordulok = await p.$$eval('#selZaras option', a => a.map(o => +o.value));
  // Ugyanaz: a VART lista is az oldal sajat adatabol jon - minden olyan
  // fordulo, aminek mar van eredmenye.
  const vart = await p.evaluate(() => ROUNDS.filter(r => (SCHEDULE[r] || []).some(m => m[2] != null)));
  check(JSON.stringify(fordulok) === JSON.stringify(vart),
     'minden lejátszott forduló ott van a legördülőben (' + fordulok.join(', ')
     + (JSON.stringify(fordulok) === JSON.stringify(vart) ? '' : ' — várt: ' + vart.join(', ')) + ')');
  await p.selectOption('#selZaras', '3'); await p.waitForTimeout(200);
  await p.click('[data-znav="-1"]');
  await p.waitForFunction(() => document.querySelector('#selZaras').value === '2',
                          null, { timeout: 5000 });
  check(/Egyik Elek/.test(await p.$eval('#znBody', e => e.innerText)),
     'a nyíllal a korábbi fordulóra lehet lépni');
  // az 1. az elso fordulo: onnan a visszalepes nem vihet sehova
  await p.selectOption('#selZaras', '1'); await p.waitForTimeout(200);
  await p.click('[data-znav="-1"]');
  check((await p.$eval('#selZaras', e => e.value)) === '1',
     'az első fordulónál a visszalépés nem visz sehova (nem esik ki a listából)');

  section('Ismeretlen játékos');
  // Ahol csak a valtozas MERTEKE ismert: nincs "elotte -> utana", a nev nem
  // kattinthato, es kiirt magyarazat all alatta.
  await p.selectOption('#selZaras', '3'); await p.waitForTimeout(200);
  const isor = await p.$eval('#znBody .zsor', e => e.innerText.replace(/\n/g, ' '));
  check(/Ismeretlen játékos/.test(isor) && /-2,5/.test(isor) && !/→/.test(isor),
     'csak a változás mértéke áll ott, nincs előtte → utána (' + isor + ')');
  check((await p.$$eval('#znBody .zsor .znev.kattint', a => a.length)) === 0,
     'az ismeretlen játékos neve nem kattintható');
  check(/nem gyűjtött játékos-szintű adatot/.test(await p.$eval('#znBody', e => e.innerText)),
     'kiírt magyarázat áll alatta');

  check(perr.length === 0, 'nincs JS-hiba' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await finish(br);
})();
