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
    allas: (document.querySelector('#mBody .score') || {}).textContent,
    oszlop: document.querySelectorAll('#mBody .sqcol').length,
    jatekos: document.querySelectorAll('#mBody .sqcol .plr').length,
    elojel: document.querySelectorAll('#mBody .elojel').length,
    kezdsor: document.querySelectorAll('#mBody .kezdsor').length,
    pontok: [...document.querySelectorAll('#mBody .sqcol .plr .pts')].map(x => x.textContent.trim()),
  }));
  jo(k.oszlop === 2, 'MINDKÉT keret kirajzolódik (' + k.oszlop + ' oszlop)');
  jo(k.jatekos >= 30, 'a két keret együtt legalább 30 játékos (' + k.jatekos + ')');
  jo(/sem kezdődött el/.test(k.sub),
     'az alcím megmondja, hogy még egy meccs sem kezdődött el: "' + k.sub + '"');
  // A FORDULO ILYENKOR MAR EL: a leadasi hatarido lejart, a keret rogzitett,
  // es az allas sem 0:0 - a magyarszabaly mar pontot er. Az "elo" jelzes
  // tehat NEM hazugsag, hanem a pontos allapot. (Egy korabbi valtozat
  // elrejtette; az volt a teves dontes.) A kezdoallitasi hatekonysag viszont
  // marad rejtve: 0/0 lenne, szam, ami semmit nem mond.
  jo(k.elojel > 0, 'ott a „élő" jelzés (' + k.elojel + ')');
  jo(k.kezdsor === 0, 'nincs KEZD% sor (' + k.kezdsor + ')');
  // Az allasban SZAM all, nem kotojel: a magyarszabaly mar most jar.
  jo(/\d/.test(k.allas || ''),
     'a fejlécben szám áll, nem 0:0 vagy kötőjel — a magyarszabály már pontot ér ('
     + (k.allas || '').replace(/\s+/g, ' ').trim() + ')');
  const szamos = k.pontok.filter(x => /\d/.test(x));
  jo(k.pontok.length > 0 && szamos.length === 0,
     'minden játékosnál kötőjel áll pont helyett (' + k.pontok.length + ' cella, '
     + szamos.length + ' számmal)');

  cim('A főoldali lista is a keretekből mutatja az állást');
  // BEJELENTETT: a "Kovetkezo fordulo" widgetben "- : -" allt, holott a
  // keret mar rogzitett, es a MAGYARSZABALY +10 mar pontot er. Ok: a
  // fooldali lista a MLSZ ranglistajabol veszi az allast, az pedig a
  // sipszo elott 0-t mond - a 0-0-t viszont "el sem kezdodott"-kent
  // dobjuk el. Mostantol ilyenkor a KERETBOL szamolunk, ugyanazzal a
  // fuggvennyel (keretOsszeg), mint a meccs-panel.
  //
  // EZT ERINTETLEN LAPON kell merni: a fenti mereshez kivettuk egy fordulo
  // eredmenyet, attol viszont a "kovetkezo fordulo" MAS fordulora all, es
  // nem azt latnank, amit a nezo.
  const p2 = await br.newPage({ viewport: { width: 900, height: 900 } });
  const err2 = []; p2.on('pageerror', e => err2.push(e.message));
  await apiKi(p2);
  await p2.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p2.waitForSelector('#mNext .match', { timeout: 20000 });
  await p2.waitForFunction(() => typeof SQUAD_FILE !== 'undefined' && SQUAD_FILE !== null,
                           null, { timeout: 20000 }).catch(() => {});
  await p2.waitForTimeout(600);
  const w = await p2.evaluate(() => {
    const r = T.rNext;
    return {
      r: r,
      // csak akkor merheto, ha a KOVETKEZO fordulohoz mar van keret, de meg
      // nincs eredmeny - eppen ez az allapot a kerdes
      merheto: !!(r && SQUAD_ROUND === r && SQUAD_FILE
                  && Object.keys(SQUAD_FILE).length
                  && (SCHEDULE[r] || []).length
                  && (SCHEDULE[r] || []).every(m => m[2] == null)),
      allasok: [...document.querySelectorAll('#mNext .match .score')]
        .map(x => x.textContent.replace(/\s+/g, ' ').trim()),
      elo: document.querySelectorAll('#mNext .elojel').length,
    };
  });
  if (w.merheto){
    jo(w.allasok.length > 0 && w.allasok.every(x => /\d/.test(x)),
       'a listában SZÁM áll, nem kötőjel (' + w.allasok.join(' | ') + ')');
    jo(w.elo === w.allasok.length,
       'mindegyik meccs „élő" jelölést kap (' + w.elo + '/' + w.allasok.length + ')');
  } else {
    jo(true, 'kihagyva: a következő fordulóhoz még nincs mentett keret (r=' + w.r + ')');
  }
  jo(err2.length === 0, 'nincs JS-hiba a főoldalon'
     + (err2.length ? ': ' + err2.join(' | ') : ''));
  await p2.close();

  cim('A böngésző élő keret-lekérése is ismeri a pótolt meccset');
  // MEGTORTENT, HAROMSZOR: a gyujtot javitottuk, a lapon megis az allt, hogy
  // "a klubnak nincs meccse". Az ELO keret-lekeres ugyanis a BONGESZOBEN
  // epiti ujra a rekordokat (keretRekord), sajat logikaval - es az kimaradt
  // a javitasbol. A tarolt adat jo volt, a friss lekeres irta felul.
  // A bemenet a VALODI meres alakja (naplo/mlsz-dupla-meccs.txt).
  const kr = await p.evaluate(() => {
    const ETO = [{ start_at: '2026-09-03T19:30:00+02:00', status: 'scheduled', round_number: '3F' },
                 { start_at: '2026-09-06T20:00:00+02:00', status: 'scheduled', round_number: '7F' }];
    const d = g => ({ competition_player: { id: 1, team: { short_name: 'ETO' },
                        countries: [], current_round: { games: g } },
                      position: {}, summary_statistics: {} });
    const ki = x => ({ nogame: !!x.nogame, start: x.start, vege: !!x.vege });
    return {
      potolt: ki(keretRekord(d(ETO), 7)),
      kozben: ki(keretRekord(d([{ ...ETO[0], status: 'completed' }, ETO[1]]), 7)),
      mind: ki(keretRekord(d([{ ...ETO[0], status: 'completed' },
                              { ...ETO[1], status: 'completed' }]), 7)),
      visszaeso: ki(keretRekord(d([{ start_at: '2026-09-20T18:00:00+02:00',
                                     status: 'scheduled', round_number: '9F' }]), 3)),
      ures: ki(keretRekord(d([]), 7)),
    };
  });
  jo(!kr.potolt.nogame && kr.potolt.start === '2026-09-03T19:30:00+02:00',
     'a pótolt meccs miatt NINCS „nincs meccse", és arra a meccsre mutat ('
     + JSON.stringify(kr.potolt) + ')');
  jo(kr.kozben.start === '2026-09-06T20:00:00+02:00' && !kr.kozben.vege,
     'a pótolt után a következő meccsre mutat, és még nincs „vége" ('
     + JSON.stringify(kr.kozben) + ')');
  jo(kr.mind.vege, 'csak mindkettő lementével lesz „vége" (' + JSON.stringify(kr.mind) + ')');
  jo(kr.visszaeso.nogame && kr.ures.nogame,
     'a visszaeső meccs és az üres lista viszont továbbra is „nincs meccse"');

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
