const { BASE, jo, cim, inditas, vege, apiKi } = require('./kozos');
const fs = require('fs'), path = require('path');
// A KET LIGA-OLDAL VAZA UGYANAZ.
//
// MIERT LETEZIK: a ket oldal kulon fajl (nincs build, nincs sablon), tehat a
// kozos resz kezzel van ketszer leirva - es szet tud csuszni. Meg is tortent:
// a zarasi valtozasok panelje az egyik oldalon mas cimmel, mas oszlopban es
// mas elrendezessel allt, mint a masikon. Amit ket helyen kell egyszerre
// atirni, azt gepnek kell orizni.
//
// Amit NEM ellenoriz: a panelek tartalmat. A ket liga adata mas (draft vs
// salary cap), a KERET azonban ugyanaz kell legyen.
const OLDALAK = ['index.html', 'nb1/index.html', 'pl/index.html', 'valtozasok/index.html'];
const GYOKER = path.join(__dirname, '..');

// A <head> osszehasonlitasahoz: a relativ utvonal-elotag es a cim ligankent
// mas, minden mas azonos kell legyen.
const fejNorm = h => h.slice(0, h.indexOf('</head>'))
  .replace(/<title>[\s\S]*?<\/title>/, '<title/>')
  .replace(/\.\.\//g, '')
  .replace(/\s+/g, ' ').trim();

(async () => {
  const br = await inditas();

  cim('A <head> minden oldalon ugyanaz');
  const fejek = OLDALAK.map(f => [f, fejNorm(fs.readFileSync(path.join(GYOKER, f), 'utf8'))]);
  const alap = fejek[0][1];
  for (const [f, h] of fejek.slice(1)){
    if (h === alap) { jo(true, f + ': azonos a főoldaléval'); continue; }
    // hol ter el eloszor?
    let i = 0; while (i < h.length && h[i] === alap[i]) i++;
    jo(false, f + ': eltér a <head> — „…' + alap.slice(Math.max(0, i - 40), i + 40)
       + '” helyett „…' + h.slice(Math.max(0, i - 40), i + 40) + '”');
  }

  cim('JavaScript nélkül is megmondja, mi hiányzik');
  for (const f of OLDALAK){
    const h = fs.readFileSync(path.join(GYOKER, f), 'utf8');
    jo(/<noscript><div class="note nojs">/.test(h) && /JavaScript<\/b> kell/.test(h),
       f + ': van <noscript> figyelmeztetés (különben csak üres váz látszik)');
  }

  const oldal = async (liga, w, h) => {
    const p = await br.newPage({ viewport: { width: w, height: h } });
    const err = []; p.on('pageerror', e => err.push(e.message));
    await apiKi(p);
    await p.goto(BASE + liga + '/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await p.waitForTimeout(2200);
    return { p, err };
  };

  for (const [w, h, cimke] of [[1400, 1100, 'GÉP'], [390, 844, 'MOBIL']]){
    cim(cimke + ': a panelek ugyanabban a sorrendben és oszlopban állnak');
    const ki = {};
    for (const liga of ['nb1', 'pl']){
      const { p, err } = await oldal(liga, w, h);
      ki[liga] = await p.$$eval('.panel', a => a.filter(x => x.offsetParent !== null).map(x => {
        const c = x.querySelector('h2'), r = x.getBoundingClientRect();
        return { cim: (c ? c.childNodes[0].textContent : '(nincs cím)').trim(),
                 oszlop: r.x < 400 ? 'bal' : 'jobb', y: Math.round(r.y) };
      }));
      jo(err.length === 0, liga + ': nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
      await p.close();
    }
    const sor = x => x.map(o => o.cim).join(' → ');
    ki.nb1.sort((a, b) => a.y - b.y); ki.pl.sort((a, b) => a.y - b.y);
    jo(sor(ki.nb1) === sor(ki.pl),
       cimke + ': ugyanazok a panelek, ugyanabban a sorrendben\n     NB1: '
       + sor(ki.nb1) + '\n     PL : ' + sor(ki.pl));
    if (cimke === 'GÉP'){
      const oszl = x => x.map(o => o.cim + '=' + o.oszlop).join(', ');
      jo(oszl(ki.nb1) === oszl(ki.pl),
         'GÉP: minden panel ugyanabban az oszlopban\n     NB1: ' + oszl(ki.nb1)
         + '\n     PL : ' + oszl(ki.pl));
    }
  }

  cim('A tabella fejléce ugyanaz (az első cella kivételével)');
  const fej = {};
  for (const liga of ['nb1', 'pl']){
    const { p } = await oldal(liga, 1400, 1100);
    fej[liga] = await p.$$eval('#table tr:first-child th, #table tr:first-child td',
                               a => a.map(x => x.textContent.trim()));
    await p.close();
  }
  // az elso ket cella: sorszam (ures) es a resztvevo megnevezese
  jo(fej.nb1[1] !== fej.pl[1],
     'a résztvevő oszlopa ligánként más néven fut (' + fej.nb1[1] + ' / ' + fej.pl[1] + ')');
  jo(fej.nb1.slice(2).join('|') === fej.pl.slice(2).join('|'),
     'a többi oszlop fejléce azonos\n     NB1: ' + fej.nb1.slice(2).join(' | ')
     + '\n     PL : ' + fej.pl.slice(2).join(' | '));

  await vege(br);
})();
