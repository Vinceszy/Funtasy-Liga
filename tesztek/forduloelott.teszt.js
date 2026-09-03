const { BASE, jo, cim, inditas, vege, apiKi, jsonAtir } = require('./kozos');
// A LEADASI HATARIDO UTAN, DE AZ ELSO SIPSZO ELOTT is latszik a ket keret.
//
// BEJELENTETT: elo fordulo alatt, amig egyetlen meccs sem kezdodott el, a
// meccs-nezet csak annyit irt, hogy "A fordulo meg nem kezdodott el" -
// pedig a keret ilyenkor mar rogzitett, a gyujto le is mentette, es eppen
// ez a legizgalmasabb kerdes: kivel all ki az ellenfel. Titok sem serul: a
// szakvezeto neve alatt az "Aktualis keret" amugy is ugyanezt mutatja.
//
// A TESZT NEM A NAPTARRA TAMASZKODIK: a menetrendbol menet kozben kivesszuk
// egy MAR LEZART fordulo eredmenyet, amitol az pontosan ebbe az allapotba
// kerul (van mentett keret, nincs eredmeny). Igy akkor is mer, amikor eppen
// nincs ilyen fordulo a valosagban.
const ELOTTE = 6;        // ehhez van keretek/<r>.json
const JOVOBELI = 20;     // ehhez nincs mentett keret

(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 1200, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await apiKi(p);
  await jsonAtir(p, '**/results.json*', j => {
    (j.schedule[String(ELOTTE)] || []).forEach(m => { m[2] = null; m[3] = null; });
    return j;
  });
  // A tarolt keret is a HATARIDO UTANI, SIPSZO ELOTTI allapotot vegye fel:
  // nulla pont, meg nem jatszott, a meccs a jovoben. Az eredmeny torlese
  // onmagaban nem eleg - a lezart fordulo kereteben ott allnak a valodi
  // pontok, es akkor nem a mert allapotot latnank.
  const JOVO = new Date(Date.now() + 2 * 864e5).toISOString().replace(/\.\d+Z$/, '+00:00');
  await jsonAtir(p, '**/keretek/' + ELOTTE + '.json*', j => {
    for (const nev in (j.squads || {}))
      (j.squads[nev] || []).forEach(x => {
        x.week = 0; x.played = false; x.vege = false; x.start = JOVO;
      });
    return j;
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1200);

  cim('Rögzített keret, még el nem kezdődött forduló');
  const par = await p.evaluate(r => {
    const m = (SCHEDULE[r] || [])[0];
    return m ? [m[0], m[1]] : null;
  }, ELOTTE);
  jo(!!par, 'van meccs a ' + ELOTTE + '. fordulóban (' + JSON.stringify(par) + ')');
  await p.evaluate(([h, v, r]) => showMatchRound(h, v, r), [par[0], par[1], ELOTTE]);
  // .catch: ha a keret NEM jelenik meg (ez a regi viselkedes), ne kivetellel
  // haljon el a teszt - az allitasok mondjak meg, mi hianyzik.
  await p.waitForSelector('#mBody .sqcol', { timeout: 10000 }).catch(() => {});
  const k = await p.evaluate(() => ({
    sub: document.getElementById('mSub').textContent,
    oszlop: document.querySelectorAll('#mBody .sqcol').length,
    jatekos: document.querySelectorAll('#mBody .sqcol .plr').length,
    elojel: document.querySelectorAll('#mBody .elojel').length,
    kezdsor: document.querySelectorAll('#mBody .kezdsor').length,
    pontok: [...document.querySelectorAll('#mBody .sqcol .plr .pts')].map(x => x.textContent.trim()),
  }));
  jo(k.oszlop === 2, 'MINDKÉT keret kirajzolódik (' + k.oszlop + ' oszlop)');
  jo(k.jatekos >= 30, 'a két keret együtt legalább 30 játékos (' + k.jatekos + ')');
  jo(/nem kezdődött/.test(k.sub), 'az alcím megmondja, hogy a forduló még nem kezdődött el: "' + k.sub + '"');
  // Az "elo" jelzes HAZUGSAG lenne: nem zajlik semmi. A kezdoallitasi
  // hatekonysag pedig 0/0 lenne - szam, ami semmit nem mond.
  jo(k.elojel === 0, 'nincs „élő" jelzés (' + k.elojel + ')');
  jo(k.kezdsor === 0, 'nincs KEZD% sor (' + k.kezdsor + ')');
  const szamos = k.pontok.filter(x => /\d/.test(x));
  jo(k.pontok.length > 0 && szamos.length === 0,
     'minden játékosnál kötőjel áll pont helyett (' + k.pontok.length + ' cella, '
     + szamos.length + ' számmal)');

  cim('Valódi jövőbeli fordulónál marad az üzenet');
  // Ehhez NINCS mentett keret - kitalalni nem fogunk semmit.
  await p.evaluate(() => { const b = document.getElementById('ovClose'); if (b) b.click(); });
  await p.waitForTimeout(250);
  const par2 = await p.evaluate(r => {
    const m = (SCHEDULE[r] || [])[0];
    return m ? [m[0], m[1]] : null;
  }, JOVOBELI);
  await p.evaluate(([h, v, r]) => showMatchRound(h, v, r), [par2[0], par2[1], JOVOBELI]);
  await p.waitForTimeout(1500);
  const j = await p.evaluate(() => ({
    oszlop: document.querySelectorAll('#mBody .sqcol').length,
    szoveg: document.getElementById('mBody').innerText.trim(),
  }));
  jo(j.oszlop === 0 && /nem kezdődött/.test(j.szoveg),
     'jövőbeli fordulónál nincs keret, csak az üzenet ("' + j.szoveg.slice(0, 40) + '")');

  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await vege(br);
})();
