const { BASE, check, section, failures, launch, finish, blockApis } = require('./common');
// Placement of the Hungarian rule (+10) in the difference view.
// Two cases: if both squads get the same amount, it is a shared item; if
// not, it goes into the differing group on both sides (with 0 on the other).
const num = t => parseFloat(String(t).replace(/[^\d,.-]/g, '').replace(/\.(?=\d{3}\b)/g, '').replace(',', '.'));

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 1100, height: 1000 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#table tr');
  const HIST = await p.evaluate(async () => (await (await fetch('../squad_history.json')).json()).rounds || {});

  // We only look at the fixtures that have a stored squad. Whether the rule
  // is shared can be decided without rendering: hungarianBonus computes from
  // the two starting elevens.
  const candidates = await p.evaluate((HIST) => {
    const out = { shared: null, separate: null };
    for (const [r, ms] of Object.entries(SCHEDULE)) {
      const squads = HIST[r];
      if (!squads) continue;
      for (const [h, v] of ms) {
        const A = squads[h], B = squads[v];
        if (!A || !B) continue;
        const mb = l => hungarianBonus(l.filter(x => !x.sub)).pts;
        const key = mb(A) === mb(B) ? 'shared' : 'separate';
        if (!out[key]) out[key] = [h, v, +r];
      }
      if (out.shared && out.separate) break;
    }
    return out;
  }, HIST);
  console.log('candidates:', JSON.stringify(candidates));

  let synthetic = false;
  for (const key of ['shared', 'separate']) {
    let target = candidates[key];
    if (!target) {
      // In the real data every squad meets the rule, so the "only on one
      // side" case is produced deliberately: we remove the Hungarian flag
      // from one manager's squad.
      const base = candidates.shared;
      if (!base) { console.log('\n(no match to examine)'); continue; }
      const [h0, v0, r0] = base;
      // The match view reads the PER-ROUND squad file, so that is what we
      // intercept and rewrite (patching HIST would have no effect any more).
      await p.route('**/keretek/*.json*', async route => {
        const j = await (await route.fetch()).json();
        (j.squads[h0] || []).forEach(x => { x.hun = false; x.u21 = false; });
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(j) });
      });
      await p.goto(BASE + 'nb1/');
      await p.waitForSelector('#table tr td', { timeout: 20000 });
      synthetic = true;
      candidates.separate = base;
      console.log(`\n(synthetic case: removed the Hungarian flag from ${h0}'s squad)`);
    }
    const target2 = candidates[key];
    if (!target2) continue;
    const [h, v, r] = target2;
    await p.evaluate(([h, v, r]) => showMatchRound(h, v, r), target2);
    await p.waitForSelector('.sqcol .plr', { timeout: 15000 });
    if ((await p.$$('.szakasz')).length === 0) { await p.click('#elteresGomb'); await p.waitForTimeout(300); }

    const inShared = await p.locator('.sqcol .kozosresz .szabalysor').count();
    const inDiffering = await p.locator('.sqcol > .szabalysor').count();
    const mobile = await p.locator('.mobilkozos .szabalysor').count();
    console.log(`\n--- ${key === 'shared' ? 'SHARED rule' : 'ONLY ON ONE SIDE'}: ${h} vs ${v}, round ${r} ---`);
    console.log('   rule row — in the shared part:', inShared, '| among the differing:', inDiffering, '| in the mobile block:', mobile);
    if (key === 'shared') {
      check(inShared === 2 && inDiffering === 0, 'shared rule: in the shared part of both columns, nowhere among the differing items');
      check(mobile === 1, 'it appears once in the mobile shared block');
    } else {
      check(inShared === 0 && inDiffering === 2, 'differing rule: among the differing items in both columns, as a row of its own');
      check(mobile === 0, 'it does not appear in the mobile shared block');
    }

    const tallies = await p.$$eval('.sqcol', cols => cols.map(c => ({
      header: (c.querySelector('h3 span') || {}).textContent,
      rows: [...c.querySelectorAll('.osszesito')].map(o =>
        [o.querySelector('span').textContent.trim(), o.querySelector('b').textContent.trim()]),
    })));
    tallies.forEach((c, i) => {
      const shared = num(c.rows[0][1]), diff = num(c.rows[1][1]), total = num(c.rows[2][1]);
      // In the synthetic case the +10 was deliberately removed from the first
      // column, but the official score still contains it - that is the
      // difference there.
      const expected = (synthetic && i === 0) ? total - 10 : total;
      check(Math.abs(shared + diff - expected) < 0.005,
        `column ${i + 1} tally: ${shared} + ${diff} = ${expected}`
        + (expected !== total ? ` (+10 official, not due in the synthetic squad)` : ''));
      check(Math.abs(total - num(c.header)) < 0.005, `column ${i + 1} total = the header's points (${c.header})`);
    });
    await p.click('.mclose');
    await p.waitForTimeout(150);
  }

  console.log('\npageerror:', perr.length ? perr : 'none');
  await br.close();
  process.exit(failures.length ? 1 : 0);
})();
