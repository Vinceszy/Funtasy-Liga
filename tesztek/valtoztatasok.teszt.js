const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// A "Valtoztatasok" ful. A ful egesz ertelme, hogy a tabellaban allo GUARD
// szam LEVEZETHETO legyen - ezert a fo allitas nem az, hogy latszik a lista,
// hanem hogy MINDEN SZAM EGYEZIK MINDENNEL:
//
//   a blokk soraiban allo kulonbsegek osszege
//     = a blokk "Osszesen" sora
//     = a blokk fejleceben allo GUARD
//     = a Fordulok fulon allo GUARD ugyanarra a fordulora
//   es mindezek fordulonkenti osszege
//     = a tabella GUA oszlopa.
//
// Ha barhol elcsuszik, a ful mast mond, mint a tabella - es akkor a ful
// rosszabb a semminel.
const sz = t => {                       // "+25,5" / "-4,12" / "0" -> szam
  const s = String(t).replace(/\s/g, '').replace(',', '.');
  return s === '' || s === '—' || s === '–' ? null : parseFloat(s);
};

// A ket liga UGYANAZT a fulet kapja, ezert ugyanaz a teszt fut mindkettore -
// csak az azonosito-jelzo, a ful kulcsa es a megnyito fuggveny mas.
const LIGAK = [
  { ut: 'nb1/', jelzo: 'member', tab: 'changes',
    nyit: '(n, t) => showSquad([n], t, "replace")',
    fulek: 'Aktuális keret|Fordulók|Szezon játékosai|Változtatások' },
  { ut: 'pl/', jelzo: 'team', tab: 'valtoztatasok',
    nyit: '(n, t) => showTeam(+n, t, "replace")',
    fulek: 'Aktuális keret|Fordulók|Szezon játékosai|Változtatások' },
];

async function liga(br, L){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  await p.goto(BASE + L.ut, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForFunction(() => document.querySelector('#table td.guard'), null, { timeout: 20000 });

  cim('A fül ott van a többi mellett');
  // A Playwright evaluate EGY argumentumot vesz at, ezert a megnyito
  // fuggveny szovegkent utazik, es a lapon belul all ossze.
  const nyit = (n, t) => p.evaluate(a => eval(a.f)(a.n, a.t), { f: L.nyit, n: n, t: t });
  const nevek = await p.$$eval('#table tr [data-' + L.jelzo + ']',
                               (a, j) => a.map(x => x.dataset[j]), L.jelzo);
  jo(nevek.length >= 2, 'van legalább két szakvezető a tabellában (' + nevek.length + ')');
  await nyit(nevek[0], null);
  await p.waitForSelector('#mTabs .tab', { timeout: 10000 });
  const fulek = await p.$$eval('#mTabs .tab', a => a.map(x => x.textContent.trim()));
  jo(fulek.join('|') === L.fulek,
     'a négy fül a várt sorrendben: ' + fulek.join(' | '));

  cim('Minden szám egyezik mindennel');
  // A tabellabol vett kumulalt ertek szakvezetonkent - ehhez kell a vegen
  // stimmelnie a fordulonkenti osszegnek.
  const tabella = await p.$$eval('#table tr', (trs, j) => {
    const ki = {};
    trs.forEach(tr => {
      const n = tr.querySelector('[data-' + j + ']'), g = tr.querySelector('td.guard');
      if (n && g) ki[n.dataset[j]] = g.textContent.trim();
    });
    return ki;
  }, L.jelzo);
  let bajok = [], lattunkBlokkot = false;
  for (const nev of nevek) {
    // 1) a Fordulok ful GUARD oszlopa fordulonkent
    await nyit(nev, L.ut === 'pl/' ? 'fordulok' : 'season');
    await p.waitForSelector('#mBody table tr', { timeout: 10000 });
    const fordulok = await p.$$eval('#mBody table tr', trs => {
      const fej = [...trs[0].children].map(x => x.textContent.trim());
      const gi = fej.indexOf('GUARD'), ki = {};
      trs.slice(1).forEach(tr => {
        const c = tr.children;
        ki[parseInt(c[0].textContent)] = c[gi].textContent.trim();
      });
      return ki;
    });
    // 2) a Valtoztatasok ful blokkjai
    await nyit(nev, L.tab);
    await p.waitForFunction(() => {
      const b = document.getElementById('mBody');
      return b && (b.querySelector('.valtlista') || /nincs elmentett|Nincs adat/i.test(b.innerText));
    }, null, { timeout: 10000 });
    // LEZART FORDULO NELKUL nincs lista - es ez a helyes allapot, nem hiba:
    // ilyenkor a Fordulok fulon es a tabellaban sem allhat szam.
    if (!(await p.$('#mBody .valtlista'))){
      const vanFordulo = Object.values(fordulok).some(x => sz(x) != null);
      if (vanFordulo)
        bajok.push(nev + ': a Fordulók fülön van GUARD, a Változtatások fülön nincs lista');
      if (sz(tabella[nev]) != null)
        bajok.push(nev + ': a tabellában ' + tabella[nev] + ', a Változtatások fülön nincs lista');
      continue;
    }
    const blokkok = await p.$$eval('#mBody .vakor', bs => bs.map(b => ({
      cim: b.querySelector('.vafej span').textContent.trim(),
      fejGuard: (b.querySelector('.vafej .guardjel') || {}).textContent,
      sorok: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz) .zdiff')].map(x => x.textContent.trim()),
      jatekos: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz):not(.vagep) .zdiff')].map(x => x.textContent.trim()),
      reszossz: (b.querySelector('.vareszossz .zdiff') || {}).textContent,
      ures: !!b.querySelector('.vaures'),
      ossz: (b.querySelector('.vaossz .zdiff') || {}).textContent,
    })));
    jo(blokkok.length > 0, nev + ': van legalább egy forduló-blokk (' + blokkok.length + ')');
    lattunkBlokkot = true;
    // NOVEKVO SORRENDBEN, mint mindenutt maskor. Az elso valtozat a
    // legfrissebbel kezdett, es az szembement a Fordulok fullel.
    const sorrend = blokkok.map(b => parseInt(b.cim));
    if (sorrend.some((r, i) => i && r < sorrend[i - 1]))
      bajok.push(nev + ': a fordulók nem növekvő sorrendben állnak (' + sorrend.join(', ') + ')');
    let kum = 0;
    for (const b of blokkok) {
      const r = parseInt(b.cim);
      const fej = sz(b.fejGuard);
      kum += fej;
      // a) sorok osszege = fejlec (ures blokknal nincs sor, es a fejlec 0)
      const sorOssz = Math.round(b.sorok.reduce((s, x) => s + sz(x), 0) * 100) / 100;
      if (b.ures) {
        if (fej !== 0) bajok.push(nev + ' ' + r + '.: nincs változtatás, de a GUARD ' + fej);
      } else if (Math.abs(sorOssz - fej) > 0.005)
        bajok.push(nev + ' ' + r + '.: a sorok összege ' + sorOssz + ', a fejléc ' + fej);
      // b) "Osszesen" sor = fejlec
      if (!b.ures && Math.abs(sz(b.ossz) - fej) > 0.005)
        bajok.push(nev + ' ' + r + '.: az Összesen ' + sz(b.ossz) + ', a fejléc ' + fej);
      // b2) a PL-en kulon all, amit az EMBER csinalt - annak a jatekos-sorok
      //     osszegevel kell egyeznie, kulonben a szetvalasztas hamis
      if (b.reszossz != null){
        const jo_ = Math.round(b.jatekos.reduce((s2, x) => s2 + sz(x), 0) * 100) / 100;
        if (Math.abs(sz(b.reszossz) - jo_) > 0.005)
          bajok.push(nev + ' ' + r + '.: "A te döntéseid" ' + sz(b.reszossz)
                     + ', a játékos-sorok összege ' + jo_);
      }
      // c) fejlec = a Fordulok fulon allo GUARD
      const f = sz(fordulok[r]);
      if (f == null || Math.abs(f - fej) > 0.005)
        bajok.push(nev + ' ' + r + '.: a Fordulók fülön ' + fordulok[r] + ', itt ' + fej);
    }
    // d) a fordulonkenti osszeg = a tabella GUA cellaja
    kum = Math.round(kum * 100) / 100;
    const t = sz(tabella[nev]);
    if (t == null || Math.abs(t - kum) > 0.005)
      bajok.push(nev + ': a tabellában ' + tabella[nev] + ', a fülek összege ' + kum);
  }
  jo(bajok.length === 0, 'minden szám egyezik minden szakvezetőnél és fordulónál'
     + (bajok.length ? ' — ELTÉRÉS: ' + bajok.join(' ; ') : '')
     + (lattunkBlokkot ? '' : ' (ebben a ligában még nincs lezárt forduló mutatóval)'));

  cim('A változtatás nélküli forduló is kilátszik');
  // AZ ADATBOL DERUL KI, hogy VAN-E ilyen fordulo - nem feltetelezzuk.
  // A PL-en peldaul a GW2-ben minden csapat valtoztatott, tehat ott nincs
  // mit kilatszania; ha ilyenkor is "kell egy ures blokk"-ot allitanank, a
  // teszt a VALOSAGOT hibaztatna. Ha viszont az adatban VAN valtozatlan
  // szakvezeto-fordulo, a fulnek MUTATNIA KELL.
  const vanAdatban = await p.evaluate(async ut => {
    try {
      const r = await fetch(ut + '?t=' + Date.now());
      if (!r.ok) return false;
      const j = (await r.json()).rounds || {};
      return Object.values(j).some(f => Object.values(f).some(
        v => !v.ki.length && !v.be.length && !v.szerep.length && !v.bonusz));
    } catch (e) { return false; }
  }, L.ut === 'pl/' ? '../draft_keretvaltozasok.json' : '../keretvaltozasok.json');
  // Ez nem diszites: ha kihagynank, a nezo azt hinne, hogy hianyzik az adat -
  // pedig eppen az a valasz, hogy a szakvezeto hozza sem nyult a kerethez.
  let vanUres = false;
  for (const nev of nevek) {
    await nyit(nev, L.tab);
    // FIX VARAKOZAS NEM JO: a lista a keretvaltozasok.json beerkezese utan
    // rajzolodik ki, es ahogy no az adat, ugy csuszik ki egy 120 ms-os
    // ablakbol - a teszt ilyenkor "nincs ilyen fordulo"-t mer, holott van.
    // Az ALLAPOTRA varunk: kesz a lista, vagy kimondtuk, hogy nincs adat.
    await p.waitForFunction(() => {
      const b = document.getElementById('mBody');
      return b && (b.querySelector('.valtlista') || /nincs elmentett|Nincs adat/i.test(b.innerText));
    }, null, { timeout: 10000 }).catch(() => {});
    if (await p.$('#mBody .vaures')) { vanUres = true; break; }
  }
  jo(vanUres || !vanAdatban || !lattunkBlokkot,
     !vanAdatban
       ? 'az adatban most nincs változtatás nélküli forduló — nincs mit kilátszania'
       : 'van olyan forduló, ahol "Nem változtatott a keretén." áll'
         + (lattunkBlokkot ? '' : ' (ebben a ligában még nincs lezárt forduló mutatóval)'));

  cim('A nevek kattinthatók');
  await nyit(nevek[0], L.tab);
  if (!lattunkBlokkot){
    jo(true, 'kihagyva: ebben a ligában még nincs lezárt forduló mutatóval');
    jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
    await p.close();
    return;
  }
  await p.waitForSelector('#mBody .valtlista .vanev.kattint', { timeout: 10000 });
  const nev0 = await p.$eval('#mBody .valtlista .vanev.kattint', e => e.textContent.trim());
  await p.$eval('#mBody .valtlista .vanev.kattint', e => e.click());
  await p.waitForTimeout(600);
  const cimSor = await p.$eval('#mTitle', e => e.textContent.trim());
  jo(nev0.indexOf(cimSor) === 0 || cimSor.length > 0 && nev0.indexOf(cimSor.split(' ')[0]) >= 0,
     'a névre kattintva a játékos profilja nyílik (' + cimSor + ')');

  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

/* A PL-en ma meg EGYETLEN lezart fordulo sincs mutatoval (a GW1-re
   fogalmilag nincs, a GW2 pedig meg nem zart le), tehat a fenti sor ott
   csak az URES allapotot meri. A ful mukodeset viszont MOST kell
   bizonyitani, nem majd - ezert a menetrendbe menet kozben beirjuk a GW2
   eredmenyet, es ugyanazt a levezetest ellenorizzuk. */
async function plLezartan(br){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  await jsonAtir(p, '**/draft.json*', j => {
    (j.schedule['2'] || []).forEach(m => { if (m[2] == null){ m[2] = 40; m[3] = 30; } });
    return j;
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForFunction(() => document.querySelector('#table td.guard'), null, { timeout: 20000 });
  const idk = await p.$$eval('#table tr [data-team]', a => a.map(x => x.dataset.team));
  const bajok = [];
  for (const id of idk){
    await p.evaluate(i => showTeam(+i, 'fordulok', 'replace'), id);
    await p.waitForSelector('#mBody table tr', { timeout: 10000 });
    const fGuard = await p.$$eval('#mBody table tr', trs => {
      const fej = [...trs[0].children].map(x => x.textContent.trim());
      const gi = fej.indexOf('GUARD'), ki = {};
      trs.slice(1).forEach(tr => { ki[parseInt(tr.children[0].textContent)] = tr.children[gi].textContent.trim(); });
      return ki;
    });
    await p.evaluate(i => showTeam(+i, 'valtoztatasok', 'replace'), id);
    await p.waitForSelector('#mBody .valtlista', { timeout: 10000 });
    const b = await p.$eval('#mBody .vakor', b => ({
      cim: b.querySelector('.vafej span').textContent.trim(),
      fej: (b.querySelector('.vafej .guardjel') || {}).textContent,
      sorok: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz) .zdiff')].map(x => x.textContent.trim()),
      jatekos: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz):not(.vagep) .zdiff')].map(x => x.textContent.trim()),
      reszossz: (b.querySelector('.vareszossz .zdiff') || {}).textContent,
      gep: (b.querySelector('.vagep .zdiff') || {}).textContent,
      ures: !!b.querySelector('.vaures'),
      ossz: (b.querySelector('.vaossz .zdiff') || {}).textContent,
    }));
    const r = parseInt(b.cim), fej = sz(b.fej);
    const sorOssz = Math.round(b.sorok.reduce((s, x) => s + sz(x), 0) * 100) / 100;
    if (!b.ures && Math.abs(sorOssz - fej) > 0.005)
      bajok.push(id + ': a sorok összege ' + sorOssz + ', a fejléc ' + fej);
    if (!b.ures && Math.abs(sz(b.ossz) - fej) > 0.005)
      bajok.push(id + ': az Összesen ' + sz(b.ossz) + ', a fejléc ' + fej);
    if (Math.abs(sz(fGuard[r]) - fej) > 0.005)
      bajok.push(id + ': a Fordulók fülön ' + fGuard[r] + ', itt ' + fej);
    // AMIT AZ EMBER CSINALT + AMIT A GEP: a ketto egyutt a mutato, es a
    // sajat resz a jatekos-sorok osszege. Ha ez elcsuszik, a ful azt
    // sugallna, hogy a szakvezeto tette, amit a zarasi automatikus csere.
    const jo_ = Math.round(b.jatekos.reduce((s2, x) => s2 + sz(x), 0) * 100) / 100;
    if (b.reszossz == null || Math.abs(sz(b.reszossz) - jo_) > 0.005)
      bajok.push(id + ': "A te döntéseid" ' + b.reszossz + ', a játékos-sorok összege ' + jo_);
    if (b.gep == null)
      bajok.push(id + ': hiányzik az automatikus csere sora');
    else if (Math.abs(jo_ + sz(b.gep) - fej) > 0.005)
      bajok.push(id + ': ember ' + jo_ + ' + gép ' + sz(b.gep) + ' ≠ ' + fej);
  }
  jo(idk.length > 0 && bajok.length === 0,
     'lezárt fordulóval a PL-en is minden szám egyezik (' + idk.length + ' csapat)'
     + (bajok.length ? ' — ELTÉRÉS: ' + bajok.join(' ; ') : ''));
  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

/* MEGTORTENT: a `?v=` csak a funtasy.js/css gyorsitotarat tori, az
   nb1/index.html-et NEM - es a kiszolgalo a regi ?v=-es kerésre is a MOSTANI
   funtasy.js-t adja. Igy a bongeszo REGI lapja (ami meg egyben, cimkezetlen
   `sorok`-kent adta at a teteleket) az UJ megjelenitovel talalkozott: a
   fordulo fejleceben ott allt a GUARD, alatta viszont "Nem valtoztatott a
   kereten." - holott harom jatekost cserelt. A megjelenito azota MINDKET
   alakot erti; ez a teszt ezt tartja eletben. */
async function regiAlak(br){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  const k = await p.evaluate(() => {
    document.getElementById('mBody').innerHTML = FunTasy.valtoztatasLista(
      [{ nev: '2. forduló', guard: 2,
         sorok: [{ poszt: 'ST', nev: 'X', klub: 'K', cimke: 'kapitány', dl: -6 },
                 { poszt: 'MID', nev: 'Y', klub: 'K', ert: 8, dl: 8 }] }], 'nincs');
    const b = document.querySelector('#mBody .vakor');
    return { sorok: b.querySelectorAll('.vasor:not(.vaossz):not(.vaures)').length,
             ures: !!b.querySelector('.vaures'),
             ossz: (b.querySelector('.vaossz .zdiff') || {}).textContent };
  });
  jo(k.sorok === 2 && !k.ures,
     'a címkézetlen `sorok` alakból is kirajzolódnak a tételek (' + JSON.stringify(k) + ')');
  jo(k.ossz && k.ossz.replace(',', '.').indexOf('2') >= 0,
     'és az Összesen sor is ott van (' + k.ossz + ')');
  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

(async () => {
  const br = await inditas();
  for (const L of LIGAK){
    cim('=== ' + L.ut.replace('/', '').toUpperCase() + ' ===');
    await liga(br, L);
  }
  cim('=== PL, lezárt fordulóval (a menetrend menet közben kiegészítve) ===');
  await plLezartan(br);
  cim('=== A régi, címkézetlen adatalak is megjelenik ===');
  await regiAlak(br);
  await vege(br);
})();
