const { BASE, check, launch, finish } = require('./common');
// THE BENCH ORDER IS THE FPL SUBSTITUTION ORDER, and it must not be re-sorted.
//
// At the end of the round the FPL puts the first bench player who fits the
// formation in place of a starter who did not play - so the bench order is
// itself the information. The stored squad keeps the FPL's own order (picks
// 12-15). The page used to sort the bench by POSITION too, and threw exactly
// this away.
//
// The starters, however, are STILL sorted by position: there the order has
// no meaning, and the goalkeeper-defender-midfielder-forward build-up is
// easier to read.
(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await p.route('**premierleague.com/**', route => route.fulfill({
    status: 200, contentType: 'application/json', body: '{}' }));
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof sqcolHTML === 'function' && Object.keys(PLAYERS).length > 0,
    null, { timeout: 20000 });

  // We pick real players per position, so that position sorting can be
  // measured; the bench is DELIBERATELY not in position order.
  const pick = await p.evaluate(() => {
    const byPos = {};
    for (const id in PLAYERS){
      const j = PLAYERS[id];
      (byPos[j.p] = byPos[j.p] || []).push(+id);
    }
    return byPos;
  });
  const [GKP, DEF, MID, FWD] = ['GKP', 'DEF', 'MID', 'FWD'].map(k => pick[k] || []);
  check(GKP.length && DEF.length && MID.length && FWD.length, 'all four positions exist in the master data');

  // bench: goalkeeper, forward, defender, midfielder - no position sorting
  // gives back this order, so if it is kept, we really do not sort
  const benchOrder = [GKP[1], FWD[1], DEF[2], MID[2]];
  const starters = [MID[0], FWD[0], GKP[0], DEF[0]];   // deliberately mixed
  const list = [
    ...starters.map(e => ({ e, b: false, pts: 1 })),
    ...benchOrder.map(e => ({ e, b: true, pts: 1 })),
  ];

  // we pass a gw so the rows get a data-e attribute: we compare by id, not
  // by name (next to the name the club's short name is in .nm too).
  const dom = await p.evaluate(([list]) => {
    const d = document.createElement('div');
    d.innerHTML = sqcolHTML('T', list, 'Teszt', 99);
    const sqcol = d.querySelector('.sqcol');
    const benchE = [], starterE = [];
    let onBench = false;
    for (const x of sqcol.children){
      if (x.classList.contains('subhead')) { onBench = true; continue; }
      if (!x.classList.contains('plr') || x.classList.contains('plrfej')) continue;
      (onBench ? benchE : starterE).push(+x.dataset.e);
    }
    return { benchE, starterE };
  }, [list]);

  console.log('   bench input:      ' + JSON.stringify(benchOrder));
  console.log('   bench in the DOM: ' + JSON.stringify(dom.benchE));
  check(dom.benchE.length === benchOrder.length && dom.starterE.length === starters.length,
     'every row was drawn (' + dom.starterE.length + ' starters + ' + dom.benchE.length + ' bench)');
  check(dom.benchE.length === benchOrder.length
     && dom.benchE.every((x, i) => x === benchOrder[i]),
     'the bench stands exactly in the input (FPL) order - no sorting by position');
  // a check of the check: sorted by position a DIFFERENT order would come
  // out, so the claim is not trivially true
  const rank = { GKP: 0, DEF: 1, MID: 2, FWD: 3 };
  const pos = await p.evaluate(([ids]) => ids.map(e => PLAYERS[e].p), [benchOrder]);
  check(pos.some((x, i) => i && rank[pos[i - 1]] > rank[x]),
     'the test\'s bench order really is NOT a position order: ' + JSON.stringify(pos));

  const sPos = await p.evaluate(([ids]) => ids.map(e => PLAYERS[e].p), [dom.starterE]);
  console.log('   starters in the DOM: ' + JSON.stringify(sPos));
  check(sPos.length === starters.length
     && sPos.every((x, i) => !i || rank[sPos[i - 1]] <= rank[x]),
     'but the starters stay sorted by position');

  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr));
  await finish(br);
})();
