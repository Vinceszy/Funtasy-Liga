const { BASE, check, section, failures, launch, finish, blockApis } = require('./common');
// We recompute the table and the head-to-head matrix INDEPENDENTLY from
// results.json, and compare them with what the page draws. Nothing checked
// this before.
const fs = require('fs');

const res = JSON.parse(fs.readFileSync(require('path').join(__dirname,'..','results.json'), 'utf8'));
const provisional = new Set((res.provisional || []).map(Number));

// per manager: M played, W won, D drawn, L lost, PF points for, PA points against
const T = {}, row = n => (T[n] = T[n] || { M: 0, W: 0, D: 0, L: 0, PF: 0, PA: 0 });
const H2H = {};                                   // "A|B" -> [w, d, l] from A's point of view
const h2h = (a, b) => (H2H[a + '|' + b] = H2H[a + '|' + b] || [0, 0, 0]);
for (const [r, ms] of Object.entries(res.schedule)) {
  if (provisional.has(+r)) continue;
  for (const [h, v, hp, vp] of ms) {
    if (hp == null || vp == null) continue;
    const a = row(h), b = row(v);
    a.M++; b.M++; a.PF += hp; b.PF += vp; a.PA += vp; b.PA += hp;
    const i = hp > vp ? 0 : hp < vp ? 2 : 1;
    if (i === 0) { a.W++; b.L++; } else if (i === 2) { b.W++; a.L++; } else { a.D++; b.D++; }
    h2h(h, v)[i]++; h2h(v, h)[2 - i]++;
  }
}
const round2 = x => Math.round(x * 100) / 100;
const ours = Object.entries(T).map(([n, s]) => ({ n, ...s, P: s.W * 3 + s.D, DIFF: round2(s.PF - s.PA) }))
  .sort((x, y) => y.P - x.P || y.DIFF - x.DIFF || y.PF - x.PF);

(async () => {
  const br = await launch();
  const p = await br.newPage();
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr td', { timeout: 30000 });
  // The table is drawn in steps (an earlier state first, then the full
  // results), so wait for the STATE: every expected match counted and the
  // head-to-head matrix drawn - not for the first row.
  const matches = ours.reduce((sum, v) => sum + v.M, 0);
  await p.waitForFunction((expected) => {
    const rows = [...document.querySelectorAll('#table tr')].filter((tr) => tr.querySelector('td'));
    const played = rows.reduce((sum, tr) => sum + (parseFloat(tr.children[2]?.textContent) || 0), 0);
    return played === expected && document.querySelectorAll('#matrix tr').length > 1;
  }, matches, { timeout: 30000 }).catch(() => { /* the checks below report what is missing */ });

  // only the data rows (the header consists of THs)
  const page = await p.$$eval('#table tr', trs => trs
    .filter(tr => tr.querySelector('td'))
    .map(tr => [...tr.children].map(c => c.textContent.trim())));
  const num = t => parseFloat(String(t).replace(/\s/g, '').replace(',', '.'));

  console.log('--- table ---');
  check(page.length === ours.length, `number of rows (page ${page.length}, computed ${ours.length})`);
  ours.forEach((v, i) => {
    const o = page[i] || [];
    check((o[1] || '').startsWith(v.n), `place ${i + 1} ${v.n} (on the page: "${(o[1] || '').split(' ')[0]}")`);
    const expected = [v.M, v.W, v.D, v.L, round2(v.PF), round2(v.PA), v.DIFF, v.P];
    const got = [2, 3, 4, 5, 6, 7, 8, 9].map(j => num(o[j]));
    const ok = expected.every((x, j) => Math.abs(x - got[j]) < 0.005);
    if (!ok) console.log(`      expected: ${expected.join(' | ')}\n      got:      ${got.join(' | ')}`);
    check(ok, `   ${v.n} numbers (M/GY/D/V/SP/KP/KÜL/Pont)`);
  });

  console.log('\n--- head-to-head matrix ---');
  const mx = await p.evaluate(() => {
    const t = document.getElementById('matrix');
    const rows = [...t.querySelectorAll('tr')];
    const head = [...rows[0].children].map(c => c.textContent.trim());
    return rows.slice(1).map(tr => ({
      name: tr.children[0].textContent.trim(),
      cells: [...tr.children].slice(1).map((c, i) => ({ column: head[i + 1], value: c.textContent.trim() })),
    }));
  });
  const full = n => ours.find(x => x.n === n).n;
  let count = 0, mismatches = 0;
  for (const r of mx) {
    const a = ours.find(x => x.n === r.name);
    if (!a) { check(false, 'unknown matrix row: ' + r.name); continue; }
    for (const c of r.cells) {
      const b = ours.find(x => x.n.toLowerCase().startsWith(c.column.toLowerCase()));
      if (!b) { check(false, 'unknown matrix column: ' + c.column); continue; }
      if (a.n === b.n) { if (c.value !== '—') { mismatches++; console.log(`   diagonal ${a.n}: "${c.value}"`); } continue; }
      const m = H2H[a.n + '|' + b.n];
      const expected = m ? m.join('/') : '·';
      count++;
      if (c.value.replace(/\s/g, '') !== expected) {
        mismatches++; console.log(`   ${a.n} vs ${b.n}: page="${c.value}" computed="${expected}"`);
      }
    }
  }
  check(mismatches === 0, `matrix cells (${count} checked, ${mismatches} mismatches)`);

  section('On horizontal scroll both the place AND the name stay put');
  // THE EXCLUDED FAULT (iPhone): on scrolling the manager header stayed put,
  // but the names slid under the numbers. Cause: `td.name` itself was the
  // flex container, and a flex cell drops out of the table layout - Safari
  // does not stick it there. The header (`th`) has no flex, so it stayed.
  //
  // WE CANNOT RUN SAFARI HERE, so we do not measure the look of sticking but
  // the CAUSE: the cell must stay a real table cell, and the flex must be on
  // the .nevsor inside it. If someone puts the flex back on the cell, this
  // test fails - even without the phone.
  const mob = await br.newPage({ viewport: { width: 390, height: 800 } });
  await blockApis(mob);
  await mob.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await mob.waitForSelector('#table td.name', { timeout: 20000 });
  const st = await mob.evaluate(() => {
    const tr = document.querySelectorAll('#table tr')[1];
    const cs = e => e && getComputedStyle(e);
    const name = tr.querySelector('td.name'), rank = tr.querySelector('td.rank');
    const th = document.querySelectorAll('#table tr:first-child th')[1];
    return {
      nameDisplay: cs(name).display, namePos: cs(name).position,
      rankPos: cs(rank).position, thPos: cs(th).position,
      nameRow: !!name.querySelector('.nevsor'),
      nameRowDisplay: cs(name.querySelector('.nevsor')) && cs(name.querySelector('.nevsor')).display,
      borderCollapse: cs(document.getElementById('table')).borderCollapse,
    };
  });
  check(st.nameDisplay === 'table-cell',
     'the name cell stays a REAL table cell (display: ' + st.nameDisplay + ')');
  check(st.nameRow && st.nameRowDisplay === 'flex',
     'the flex is INSIDE the cell, on .nevsor (' + st.nameRowDisplay + ')');
  check(st.namePos === 'sticky' && st.rankPos === 'sticky' && st.thPos === 'sticky',
     'the place, the name and the header all stick (' + st.rankPos + ' / ' + st.namePos
     + ' / ' + st.thPos + ')');
  // WebKit (on iPhone EVERY browser, Chrome too) does not reliably stick
  // table cells with `collapse`. Measured: `separate` changes nothing in the
  // rendering.
  check(st.borderCollapse === 'separate',
     'the sticky-cell table\'s border-collapse is separate (' + st.borderCollapse + ')');
  await mob.close();

  await br.close();
  process.exit(failures.length ? 1 : 0);
})();
