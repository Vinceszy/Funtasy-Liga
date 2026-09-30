const { jo, cim, hibak, inditas, vege, BASE } = require('./kozos');
// KEZDESI IDOPONT, KET LIGARA EGY FORMAZOVAL (funtasy.js idoFmt).
//
// Ket kulon valtozat volt ra, es a masodik a szelen hibasan viselkedett:
// ures vagy hibas ertekre "Invalid Date"-et, null-ra pedig egy kitalalt
// datumot ("jan. 1. 00:00") irt a lapra. Egy nyers idobelyeg kellemetlen,
// egy kitalalt datum viszont hazugsag - ezert amit nem ertunk, azt
// valtozatlanul adjuk vissza.
//
// Az EJFEL liga-kerdes: az MLSZ ezzel jeloli a ki nem tuzott kezdest, az
// FPL ilyenkor egyaltalan nem ad idopontot. Ha az nb1-es szabaly a pl-re is
// atszivarogna, egy valodi ejfeli kezdes "nincs kituzve"-kent latszana.
(async () => {
  const br = await inditas();
  const p = await br.newPage();
  const err = []; p.on('pageerror', e => err.push(e.message));
  for (const m of ['**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/');
  await p.waitForFunction(() => window.FunTasy && FunTasy.idoFmt, null, { timeout: 20000 });

  const f = (s, lg) => p.evaluate(([s, lg]) => FunTasy.idoFmt(s, lg), [s, lg]);

  cim('Rendes időpont');
  jo(await f('2026-09-27T17:30:00Z', 'nb1') === await f('2026-09-27T17:30:00Z', 'pl'),
     'a két liga ugyanazt adja egy valódi időpontra');
  jo(/17:30|19:30/.test(await f('2026-09-27T17:30:00Z', 'nb1')),
     'és óra is van benne — ' + await f('2026-09-27T17:30:00Z', 'nb1'));

  cim('Éjfél: liga dönti el');
  const ejNb1 = await f('2026-09-27T00:00:00Z', 'nb1');
  const ejPl  = await f('2026-09-27T00:00:00Z', 'pl');
  jo(/nincs kitűzve/.test(ejNb1), 'NB1-en az éjfél = még nincs kitűzve — ' + ejNb1);
  jo(!/nincs kitűzve/.test(ejPl), 'PL-en viszont valódi óra marad — ' + ejPl);

  cim('Szélső értékek: soha nem találunk ki dátumot');
  for (const [be, mit] of [[null, 'null'], ['', 'üres'], ['nincs', 'nem dátum'],
                           ['2026-09-27', 'óra nélküli dátum']]) {
    for (const lg of ['nb1', 'pl']) {
      const k = await f(be, lg);
      jo(!/Invalid Date/.test(k) && !/jan\. 1\./.test(k),
         `${mit} (${lg}): nincs kitalált dátum — ${JSON.stringify(k)}`);
    }
  }
  jo(await f('nincs', 'nb1') === 'nincs', 'amit nem értünk, azt változatlanul adjuk vissza');
  jo(await f(null, 'pl') === '', 'null-ból üres lesz, nem dátum');

  jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await vege(br);
})();
