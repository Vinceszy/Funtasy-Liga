const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// A tabellat es a matrixot FUGGETLENUL ujraszamoljuk a results.json-bol, es
// osszevetjuk azzal, amit az oldal kirajzol. Eddig ezt semmi nem ellenorizte.
const fs = require('fs');

const res = JSON.parse(fs.readFileSync(require('path').join(__dirname,'..','results.json'), 'utf8'));
const ideiglenes = new Set((res.provisional || []).map(Number));

const T = {}, be = n => (T[n] = T[n] || { M: 0, GY: 0, D: 0, V: 0, SP: 0, KP: 0 });
const H2H = {};                                   // "A|B" -> [gy, d, v] A szemszogebol
const h2h = (a, b) => (H2H[a + '|' + b] = H2H[a + '|' + b] || [0, 0, 0]);
for (const [r, ms] of Object.entries(res.schedule)) {
  if (ideiglenes.has(+r)) continue;
  for (const [h, v, hp, vp] of ms) {
    if (hp == null || vp == null) continue;
    const a = be(h), b = be(v);
    a.M++; b.M++; a.SP += hp; b.SP += vp; a.KP += vp; b.KP += hp;
    const i = hp > vp ? 0 : hp < vp ? 2 : 1;
    if (i === 0) { a.GY++; b.V++; } else if (i === 2) { b.GY++; a.V++; } else { a.D++; b.D++; }
    h2h(h, v)[i]++; h2h(v, h)[2 - i]++;
  }
}
const ker = x => Math.round(x * 100) / 100;
const enyem = Object.entries(T).map(([n, s]) => ({ n, ...s, P: s.GY * 3 + s.D, KUL: ker(s.SP - s.KP) }))
  .sort((x, y) => y.P - x.P || y.KUL - x.KUL || y.SP - x.SP);

(async () => {
  const br = await inditas();
  const p = await br.newPage();
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr td', { timeout: 30000 });

  // csak az adatsorok (a fejlec TH-kbol all)
  const oldal = await p.$$eval('#table tr', trs => trs
    .filter(tr => tr.querySelector('td'))
    .map(tr => [...tr.children].map(c => c.textContent.trim())));
  const sz = t => parseFloat(String(t).replace(/\s/g, '').replace(',', '.'));

  console.log('--- tabella ---');
  jo(oldal.length === enyem.length, `sorok száma (oldal ${oldal.length}, számolt ${enyem.length})`);
  enyem.forEach((v, i) => {
    const o = oldal[i] || [];
    jo((o[1] || '').startsWith(v.n), `${i + 1}. hely ${v.n} (oldalon: "${(o[1] || '').split(' ')[0]}")`);
    const vart = [v.M, v.GY, v.D, v.V, ker(v.SP), ker(v.KP), v.KUL, v.P];
    const kap = [2, 3, 4, 5, 6, 7, 8, 9].map(j => sz(o[j]));
    const ok = vart.every((x, j) => Math.abs(x - kap[j]) < 0.005);
    if (!ok) console.log(`      várt:   ${vart.join(' | ')}\n      kapott: ${kap.join(' | ')}`);
    jo(ok, `   ${v.n} számai (M/GY/D/V/SP/KP/KÜL/Pont)`);
  });

  console.log('\n--- egymás elleni mátrix ---');
  const mx = await p.evaluate(() => {
    const t = document.getElementById('matrix');
    const sorok = [...t.querySelectorAll('tr')];
    const fej = [...sorok[0].children].map(c => c.textContent.trim());
    return sorok.slice(1).map(tr => ({
      nev: tr.children[0].textContent.trim(),
      cellak: [...tr.children].slice(1).map((c, i) => ({ oszlop: fej[i + 1], ertek: c.textContent.trim() })),
    }));
  });
  const teljes = n => enyem.find(x => x.n === n).n;
  let db = 0, elteres = 0;
  for (const sor of mx) {
    const a = enyem.find(x => x.n === sor.nev);
    if (!a) { jo(false, 'ismeretlen mátrix-sor: ' + sor.nev); continue; }
    for (const c of sor.cellak) {
      const b = enyem.find(x => x.n.toLowerCase().startsWith(c.oszlop.toLowerCase()));
      if (!b) { jo(false, 'ismeretlen mátrix-oszlop: ' + c.oszlop); continue; }
      if (a.n === b.n) { if (c.ertek !== '—') { elteres++; console.log(`   átló ${a.n}: "${c.ertek}"`); } continue; }
      const m = H2H[a.n + '|' + b.n];
      const vart = m ? m.join('/') : '·';
      db++;
      if (c.ertek.replace(/\s/g, '') !== vart) {
        elteres++; console.log(`   ${a.n} vs ${b.n}: oldal="${c.ertek}" számolt="${vart}"`);
      }
    }
  }
  jo(elteres === 0, `mátrix cellái (${db} ellenőrizve, ${elteres} eltérés)`);

  cim('Vízszintes görgetésnél a helyezés ÉS a név is áll');
  // BEJELENTETT (iPhone): gorgetesnel a SZAKVEZETO fejlec allva maradt, a
  // nevek viszont elcsusztak a szamok ala. Ok: a `td.name` maga volt a flex
  // kontener, es a flexes cella kikerul a tablazat-elrendezesbol - Safari
  // ott nem ragasztja. A fejlecen (`th`) nincs flex, ezert az allt.
  //
  // A SAFARI-T ITT NEM TUDJUK FUTTATNI, ezert nem a ragadas latszatat
  // merjuk, hanem az OKOT: a cella maradjon valodi tablazat-cella, es a
  // flex a benne levo .nevsor-on legyen. Ha valaki visszateszi a flexet a
  // cellara, ez a teszt bukik - a telefon nelkul is.
  const mob = await br.newPage({ viewport: { width: 390, height: 800 } });
  await apiKi(mob);
  await mob.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await mob.waitForSelector('#table td.name', { timeout: 20000 });
  const st = await mob.evaluate(() => {
    const tr = document.querySelectorAll('#table tr')[1];
    const cs = e => e && getComputedStyle(e);
    const nev = tr.querySelector('td.name'), rang = tr.querySelector('td.rank');
    const th = document.querySelectorAll('#table tr:first-child th')[1];
    return {
      nevDisplay: cs(nev).display, nevPos: cs(nev).position,
      rangPos: cs(rang).position, thPos: cs(th).position,
      nevsor: !!nev.querySelector('.nevsor'),
      nevsorDisplay: cs(nev.querySelector('.nevsor')) && cs(nev.querySelector('.nevsor')).display,
      borderCollapse: cs(document.getElementById('table')).borderCollapse,
    };
  });
  jo(st.nevDisplay === 'table-cell',
     'a névcella VALÓDI táblázat-cella marad (display: ' + st.nevDisplay + ')');
  jo(st.nevsor && st.nevsorDisplay === 'flex',
     'a flex a cellán BELÜL, a .nevsor-on van (' + st.nevsorDisplay + ')');
  jo(st.nevPos === 'sticky' && st.rangPos === 'sticky' && st.thPos === 'sticky',
     'a helyezés, a név és a fejléc mind ragad (' + st.rangPos + ' / ' + st.nevPos
     + ' / ' + st.thPos + ')');
  // A WebKit (iPhone-on MINDEN bongeszo, a Chrome is) `collapse` mellett nem
  // ragasztja megbizhatoan a tablazat-cellakat. Megmerve: a `separate` a
  // rajzolaton semmit nem valtoztat.
  jo(st.borderCollapse === 'separate',
     'a ragadó cellás tábla border-collapse-e separate (' + st.borderCollapse + ')');
  await mob.close();

  await br.close();
  process.exit(hibak.length ? 1 : 0);
})();
