const { BASE, check, section, launch, finish, blockApis } = require('./common');
const fs = require('fs'), path = require('path');
// A betukeszlet-iv NEM allithatja meg a lap megjeleneset.
//
// MERT MEGMERTUK: sima <link rel="stylesheet">-tel, amikor a
// fonts.googleapis.com nem valaszol, a DOMContentLoaded 57 ms helyett
// 12 640 ms - addig a lapon SEMMI nincs. Mobilon, gyenge halon ez pont az a
// helyzet, amikor az ember megnezne az allast. A media="print" + onload
// trukk aszinkronna teszi az ivet; a `display=swap` miatt az elso festes
// ugyis a tartalek betuvel tortenik.
//
// A masik fele: a CSS-ben MINDEN betucsaladnak legyen tartaleka. Enelkul a
// bongeszo alapertelmezese (talpas Times) allna a helyere, mas
// betuszelesseggel - a tablazat ugrana egyet a webfont megerkezesekor.
const OLDALAK = ['', 'nb1/', 'pl/', 'valtozasok/'];
const GYOKER = path.join(__dirname, '..');

(async () => {
  const br = await launch();

  section('A hivatkozas alakja minden oldalon');
  for (const o of OLDALAK){
    const h = fs.readFileSync(path.join(GYOKER, o, 'index.html'), 'utf8');
    const nev = o || '(főoldal)';
    const ivek = h.match(/<link[^>]*fonts\.googleapis\.com[^>]*>/g) || [];
    const blokkolo = ivek.filter(x => /rel="stylesheet"/.test(x) && !/media="print"/.test(x));
    // a <noscript>-beli iv blokkolo LEHET: ott nincs onload, ami visszakapcsolna
    const noscriptben = (h.match(/<noscript>[\s\S]*?<\/noscript>/g) || []).join('');
    const igazi = blokkolo.filter(x => noscriptben.indexOf(x) < 0);
    check(igazi.length === 0, nev + ': nincs renderelést blokkoló betűkészlet-ív'
       + (igazi.length ? ' — ' + igazi[0].slice(0, 80) : ''));
    check(/media="print"/.test(h) && /this\.media='all'/.test(h),
       nev + ': az ív aszinkron (media="print" + onload)');
    check(/<noscript>[\s\S]*fonts\.googleapis[\s\S]*<\/noscript>/.test(h),
       nev + ': JavaScript nélkül is megjön a betűkészlet (noscript-ág)');
    check(/preconnect[^>]*fonts\.gstatic\.com/.test(h),
       nev + ': preconnect a fonts.gstatic.com-ra (onnan jönnek a fájlok)');
  }

  section('Minden betűcsaládnak van tartaléka');
  const css = fs.readFileSync(path.join(GYOKER, 'funtasy.css'), 'utf8');
  const beirt = (css.match(/font(-family)?:[^;}]*(Inter|JetBrains|Archivo)[^;}]*/g) || [])
    .filter(x => !/var\(--/.test(x) && !/^--/.test(x));
  check(beirt.length === 0,
     'a CSS sehol nem ír be betűnevet közvetlenül, mindenhol változó áll'
     + (beirt.length ? ' — pl. ' + beirt[0] : ''));
  for (const [v, kell] of [['--fo', 'sans-serif'], ['--mono', 'monospace'], ['--cim', 'sans-serif']]){
    const sor = (css.match(new RegExp(v + ':[^;}]*')) || [''])[0];
    check(sor.indexOf(kell) > 0, v + ' tartalék-sora ' + kell + '-fel zárul — „' + sor.slice(0, 70) + '”');
  }

  section('Nem válaszoló betűkészlet-szolgáltatás');
  // A keres SOSEM jon vissza - ez a legrosszabb eset (nem hiba, hanem varakozas)
  const p = await br.newPage();
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  for (const m of ['**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await p.route(m, async () => { await new Promise(() => {}); });   // orokre fuggoben
  const t0 = Date.now();
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 15000 });
  const eltelt = Date.now() - t0;
  check(eltelt < 8000, 'a tabella kirajzolódik akkor is, ha a betűkészlet nem jön meg ('
     + eltelt + ' ms)');
  const font = await p.evaluate(() => getComputedStyle(document.body).fontFamily);
  check(/sans-serif|system-ui/.test(font), 'a tartalék betűcsalád lép életbe — „' + font.slice(0, 50) + '”');
  check((await p.evaluate(() => document.body.innerText)).length > 500,
     'a lap tartalma ott van, nem üres');
  check((await p.evaluate(() => document.documentElement.scrollWidth
                            - document.documentElement.clientWidth)) <= 1,
     'tartalék betűvel sincs vízszintes túlcsordulás');
  check(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await finish(br);
})();
