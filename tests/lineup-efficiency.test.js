const { BASE, check, launch, finish, blockApis, rewriteJson } = require('./common');
// Line-up efficiency: how much the chosen starting line-up brought out of
// what could have been brought out of the squad.
//
// PL: the browser computes it (plEfficiency) - the best VALID formation
// (1 goalkeeper, 3-5 defenders, 1-3 forwards) out of the 15. The test sets
// up a hand-computed squad, and pins that an invalid formation (6
// defenders) does not count as possible.
// NB1: the collector computes it (tested by collector_efficiency.py); here
// we measure that the table column is filled from hatekonysag.json, and the
// percentage is the total over the closed rounds.
(async () => {
  const br = await launch();

  // ---------------- PL: the computation itself ----------------
  console.log('--- PL: plEfficiency ---');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof plEfficiency === 'function'
    && Object.keys(PLAYERS).length > 0, null, { timeout: 20000 });

  const compute = (composition) => p.evaluate(([composition]) => {
    // real players by position, in a deterministic order
    const byPos = { GKP: [], DEF: [], MID: [], FWD: [] };
    Object.keys(PLAYERS).map(Number).sort((a, b) => a - b)
      .forEach(e => { const pz = PLAYERS[e].p; if (byPos[pz]) byPos[pz].push(e); });
    const sq = [];
    for (const [pz, count, pts, bench] of composition)
      for (let i = 0; i < count; i++)
        sq.push({ e: byPos[pz][sq.filter(x => PLAYERS[x.e].p === pz).length],
                  b: bench, pts: pts[i] });
    return plEfficiency(sq);
  }, [composition]);

  // 2 GKP (8,2), 5 DEF (6,5,4,1,0), 5 MID (9,7,3,2,0), 3 FWD (10,4,1)
  // best formation: 1-3-4-3? DEF top3=15, MID top4=21, FWD top3=15, GKP 8
  //   3-4-3: 8+15+21+15 = 59;  3-5-2: 8+15+21+14=58;  4-4-2: 8+16+21+14=59;
  //   4-3-3: 8+16+19+15 = 58;  5-3-2: 8+16+19+14=57;  4-5-1: 8+16+21+10=55;
  //   5-4-1: 8+16+21+10=55 -> the maximum is 59
  const v = await compute([
    ['GKP', 1, [8], false], ['GKP', 1, [2], true],
    ['DEF', 4, [6, 5, 4, 1], false], ['DEF', 1, [0], true],
    ['MID', 4, [9, 7, 3, 2], false], ['MID', 1, [0], true],
    ['FWD', 2, [10, 4], false], ['FWD', 1, [1], true],
  ]);
  console.log('   scored/possible: ' + JSON.stringify(v));
  check(v && v.le === 59, 'the possible is the best VALID formation (59): ' + (v && v.le));
  check(v && v.sz === 8 + 16 + 21 + 14, 'the scored is the sum of the starters (' + (v && v.sz) + ')');

  // an invalid formation does not count as possible: a 6-defender "best" is forbidden
  const v2 = await compute([
    ['GKP', 1, [8], false], ['GKP', 1, [0], true],
    ['DEF', 6, [9, 9, 9, 9, 9, 9], false],
    ['MID', 4, [1, 1, 0, 0], false], ['MID', 1, [0], true],
    ['FWD', 1, [1], false], ['FWD', 1, [0], true],
  ]);
  check(v2 && v2.le === 8 + 45 + 2 + 1,
     'at most 5 defenders count, a midfielder takes the sixth one\'s place: ' + (v2 && v2.le));

  // the table column on real data: every row has a % or a dash
  const column = await p.evaluate(() => {
    T.renderTable();
    return { head: !!document.querySelector('#table th[title*="Kezdőállítási"]'),
             cells: [...document.querySelectorAll('#table td.kezdpc')].map(x => x.textContent) };
  });
  console.log('   table: ' + JSON.stringify(column.cells));
  check(column.head, 'the PL table has a KEZD% column (with a title)');
  check(column.cells.length === 10 && column.cells.every(x => /^\d+%$|^–$/.test(x)),
     'every row shows a percentage (or a dash)');
  // The name row is FLEX (to protect the monogram) - in a flex container
  // the space between the TEXT and the span IS LOST, so the gap provides the
  // distance. Without it "WhiteARS" stood instead of "White ARS"; it was a
  // regression of the monogram fix, caught on a screenshot. The row of the
  // Szezon jatekosai (season's players) list is exactly like this:
  // [position chip][name text][club chip].
  //
  // The flex container is now INSIDE the cell (.nevsor): on a flex table
  // cell position:sticky does not work on iPhone, and the names slid under
  // the numbers. So the measurement looks for the text node in .nevsor -
  // accepting the old shape too, if it still stands that way somewhere.
  const gap = await p.evaluate(([id]) => {
    const d = document.createElement('div');
    d.innerHTML = playersHTML(+id);
    document.body.appendChild(d);
    const cell = d.querySelector('td.name .nevsor') || d.querySelector('td.name');
    const text = [...cell.childNodes].find(n => n.nodeType === 3 && n.textContent.trim());
    const club = cell.querySelector('.tm');
    let res = null;
    if (text && club) {
      const r = document.createRange(); r.selectNode(text);
      res = Math.round(club.getBoundingClientRect().left - r.getBoundingClientRect().right);
    }
    const found = { text: !!text, club: !!club, res };
    d.remove();
    return found;
  }, [Object.keys(require === undefined ? {} : {})[0] || (await p.evaluate(() => Object.keys(ENTRIES)[0]))]);
  console.log('   gap between name and club tag: ' + JSON.stringify(gap));
  check(gap.text && gap.club, 'the measurement found a name text AND a club tag (it does not pass on empty)');
  check(gap.res != null && gap.res >= 3,
     'there is a gap between the name and the club tag (not "WhiteARS"): ' + gap.res + 'px');

  check(perr.length === 0, 'no JS error on the PL page: ' + JSON.stringify(perr));
  await p.close();

  // ---------------- NB1: the column filled from json ----------------
  console.log('--- NB1: table from hatekonysag.json ---');
  const p2 = await br.newPage();
  const perr2 = []; p2.on('pageerror', e => perr2.push(e.message));
  await blockApis(p2);
  // our own data, so the expected percentage can be computed by hand:
  // round 1 (closed): sz=40 le=50; round 2 (closed): sz=50 le=50
  // -> in total 90/100 = 90%. The PROVISIONAL round 5 (sz=0 le=100) is
  // DELIBERATELY left out; rounds 3-4 are closed but have no line-up value
  // -> they are left out too (they do not count as 0).
  // The scenario follows REALITY: we mark as provisional a round that has
  // no result yet - in the page's baked-in SCHEDULE round 5 is null-null,
  // so it does not count as played.
  let names;
  await p2.route('**/hatekonysag.json*', async route => {
    const r = await fetch(BASE + 'results.json');
    const j = await r.json();
    names = [...new Set(j.schedule['1'].flat().filter(x => typeof x === 'string'))];
    const row = (sz, le) => Object.fromEntries(names.map(n => [n, { sz, le }]));
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ rounds: { 1: row(40, 50), 2: row(50, 50), 5: row(0, 100) } }) });
  });
  // From disk, not through the test server (common.rewriteJson): a network
  // fetch inside the route outlived the page under the full suite's load.
  await rewriteJson(p2, '**/results.json*', j => {
    j.provisional = [5];             // round 5 is provisional...
    j.schedule['5'] = (j.schedule['5'] || []).map(m => [m[0], m[1], null, null]);
    return j;
  });
  await p2.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => document.querySelector('#table td.kezdpc'), null, { timeout: 20000 });
  const nb1 = await p2.evaluate(() => ({
    cells: [...document.querySelectorAll('#table td.kezdpc')].map(x => x.textContent),
    title: (document.querySelector('#table td.kezdpc') || {}).title,
  }));
  console.log('   cells: ' + JSON.stringify(nb1.cells) + ' | title: ' + JSON.stringify(nb1.title));
  check(nb1.cells.length > 0 && nb1.cells.every(x => x === '90%'),
     'the total is computed from the CLOSED rounds (40+50)/(50+50)=90% — the provisional one is left out');
  check(/40|90/.test(nb1.title || ''), 'the cell title shows the points pair: ' + JSON.stringify(nb1.title));

  // the Fordulok tab comes from the SHARED renderer (T.roundsHTML) - NB1 has
  // the KEZD% column there too, per round (1.: 40/50=80%, 2.: 50/50=100%)
  const rounds = await p2.evaluate(([name]) => {
    const d = document.createElement('div');
    d.innerHTML = T.roundsHTML(name);
    return { head: !!d.querySelector('th[title*="Kezdőállítási"]'),
             cells: [...d.querySelectorAll('td.kezdpc')].map(x => x.textContent).slice(0, 4) };
  }, [names[0]]);
  console.log('   NB1 Fordulók tab: ' + JSON.stringify(rounds.cells));
  check(rounds.head, 'the NB1 Fordulók tab has a KEZD% column too (shared renderer)');
  check(rounds.cells[0] === '80%' && rounds.cells[1] === '100%',
     'per-round values: 1.=80%, 2.=100% — ' + JSON.stringify(rounds.cells));

  // the match header row aligns to BOTH SIDES: the left value to the left
  // edge, the right one to the right - like every other datum in the header
  const align = await p2.evaluate(() => {
    const d = document.createElement('div');
    d.style.cssText = 'width:400px';
    d.innerHTML = FunTasy.lineupPairHTML({ sz: 40, le: 50 }, { sz: 45, le: 50 }, false);
    document.body.appendChild(d);
    const k = d.querySelector('.kezdsor').getBoundingClientRect();
    const left = d.querySelector('.kezdbal').getBoundingClientRect();
    const right = d.querySelector('.kezdjobb').getBoundingClientRect();
    const label = d.querySelector('.kezdcim').textContent.trim();
    d.remove();
    return { leftOK: Math.abs(left.left - k.left) <= 1, rightOK: Math.abs(right.right - k.right) <= 1, label };
  });
  check(align.leftOK && align.rightOK,
     'the two values align to their own half (left on the left edge, right on the right)');
  check(/kezdőállítás/.test(align.label), 'the label is in the middle: ' + JSON.stringify(align.label));

  check(perr2.length === 0, 'no JS error on the NB1 page: ' + JSON.stringify(perr2));
  await finish(br);
})();
