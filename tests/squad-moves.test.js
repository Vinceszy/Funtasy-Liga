const { BASE, check, section, launch, finish, blockApis, rewriteJson } = require('./common');
// The "Valtoztatasok" (squad moves) tab. The whole point of the tab is that
// the GUARD number in the table can be DERIVED - so the main claim is not
// that the list shows, but that EVERY NUMBER AGREES WITH EVERY OTHER:
//
//   the sum of the differences in a block's rows
//     = the block's "Osszesen" (total) row
//     = the GUARD in the block's header
//     = the GUARD on the Fordulok (rounds) tab for the same round
//   and the per-round sum of all of these
//     = the GUA column of the table.
//
// If it slips anywhere, the tab says something different from the table -
// and then the tab is worse than nothing.
const num = t => {                      // "+25,5" / "-4,12" / "0" -> number
  const s = String(t).replace(/\s/g, '').replace(',', '.');
  return s === '' || s === '—' || s === '–' ? null : parseFloat(s);
};

// The two leagues get THE SAME tab, so the same test runs on both - only the
// id attribute, the tab's key and the opener function differ.
const LEAGUES = [
  { path: 'nb1/', idAttr: 'member', tab: 'changes',
    open: '(n, t) => showSquad([n], t, "replace")',
    tabs: 'Aktuális keret|Fordulók|Szezon játékosai|Változtatások' },
  { path: 'pl/', idAttr: 'team', tab: 'valtoztatasok',
    open: '(n, t) => showTeam(+n, t, "replace")',
    tabs: 'Aktuális keret|Fordulók|Szezon játékosai|Változtatások' },
];

async function league(br, L){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  await p.goto(BASE + L.path, { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForFunction(() => document.querySelector('#table td.guard'), null, { timeout: 20000 });

  section('The tab is there next to the others');
  // Playwright's evaluate takes ONE argument, so the opener function travels
  // as text and is assembled inside the page.
  const open = (n, t) => p.evaluate(a => eval(a.f)(a.n, a.t), { f: L.open, n: n, t: t });
  const names = await p.$$eval('#table tr [data-' + L.idAttr + ']',
                               (a, j) => a.map(x => x.dataset[j]), L.idAttr);
  check(names.length >= 2, 'there are at least two managers in the table (' + names.length + ')');
  await open(names[0], null);
  await p.waitForSelector('#mTabs .tab', { timeout: 10000 });
  const tabs = await p.$$eval('#mTabs .tab', a => a.map(x => x.textContent.trim()));
  check(tabs.join('|') === L.tabs,
     'the four tabs in the expected order: ' + tabs.join(' | '));

  section('Every number agrees with every other');
  // The cumulative value per manager taken from the table - the per-round
  // sum has to match this at the end.
  const table = await p.$$eval('#table tr', (trs, j) => {
    const out = {};
    trs.forEach(tr => {
      const n = tr.querySelector('[data-' + j + ']'), g = tr.querySelector('td.guard');
      if (n && g) out[n.dataset[j]] = g.textContent.trim();
    });
    return out;
  }, L.idAttr);
  let problems = [], sawBlock = false;
  for (const name of names) {
    // 1) the GUARD column of the Fordulok tab, per round
    await open(name, L.path === 'pl/' ? 'fordulok' : 'season');
    await p.waitForSelector('#mBody table tr', { timeout: 10000 });
    const rounds = await p.$$eval('#mBody table tr', trs => {
      const head = [...trs[0].children].map(x => x.textContent.trim());
      const gi = head.indexOf('GUARD'), out = {};
      trs.slice(1).forEach(tr => {
        const c = tr.children;
        out[parseInt(c[0].textContent)] = c[gi].textContent.trim();
      });
      return out;
    });
    // 2) the blocks of the Valtoztatasok tab
    await open(name, L.tab);
    await p.waitForFunction(() => {
      const b = document.getElementById('mBody');
      return b && (b.querySelector('.valtlista') || /nincs elmentett|Nincs adat/i.test(b.innerText));
    }, null, { timeout: 10000 });
    // WITHOUT A CLOSED ROUND there is no list - and that is the correct
    // state, not an error: then neither the Fordulok tab nor the table may
    // show a number.
    if (!(await p.$('#mBody .valtlista'))){
      const hasRound = Object.values(rounds).some(x => num(x) != null);
      if (hasRound)
        problems.push(name + ': GUARD on the Fordulók tab, but no list on the Változtatások tab');
      if (num(table[name]) != null)
        problems.push(name + ': ' + table[name] + ' in the table, but no list on the Változtatások tab');
      continue;
    }
    const blocks = await p.$$eval('#mBody .vakor', bs => bs.map(b => ({
      title: b.querySelector('.vafej span').textContent.trim(),
      headGuard: b.querySelector('.vafej .guardjel')
        ? b.querySelector('.vafej .guardjel').textContent : null,
      note: (b.querySelector('.vafej .vamegj') || {}).textContent,
      emptyDiff: [...b.querySelectorAll('.zdiff')].every(x => !x.textContent.trim()),
      rows: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz) .zdiff')].map(x => x.textContent.trim()),
      playerRows: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz):not(.vagep) .zdiff')].map(x => x.textContent.trim()),
      subtotal: (b.querySelector('.vareszossz .zdiff') || {}).textContent,
      empty: !!b.querySelector('.vaures'),
      total: (b.querySelector('.vaossz .zdiff') || {}).textContent,
    })));
    check(blocks.length > 0, name + ': there is at least one round block (' + blocks.length + ')');
    sawBlock = true;
    // In ASCENDING ORDER, as everywhere else. The first version started with
    // the most recent one, and that ran against the Fordulok tab.
    const order = blocks.map(b => parseInt(b.title));
    if (order.some((r, i) => i && r < order[i - 1]))
      problems.push(name + ': the rounds are not in ascending order (' + order.join(', ') + ')');
    let cum = 0;
    for (const b of blocks) {
      const r = parseInt(b.title);
      // A block WITHOUT POINTS (not yet closed) is left out of the
      // comparison: it deliberately has no number. A separate claim below
      // measures it.
      if (b.headGuard == null){
        if (num(rounds[r]) != null)
          problems.push(name + ' ' + r + '.: GUARD on the Fordulók tab, "még nincs pontszám" here');
        continue;
      }
      const head = num(b.headGuard);
      cum += head;
      // a) sum of the rows = header (an empty block has no rows, and its header is 0)
      const rowSum = Math.round(b.rows.reduce((s, x) => s + num(x), 0) * 100) / 100;
      if (b.empty) {
        if (head !== 0) problems.push(name + ' ' + r + '.: no change, but GUARD is ' + head);
      } else if (Math.abs(rowSum - head) > 0.005)
        problems.push(name + ' ' + r + '.: row sum ' + rowSum + ', header ' + head);
      // b) "Osszesen" row = header
      if (!b.empty && Math.abs(num(b.total) - head) > 0.005)
        problems.push(name + ' ' + r + '.: Összesen ' + num(b.total) + ', header ' + head);
      // b2) on PL what the HUMAN did stands separately - it must equal the
      //     sum of the player rows, otherwise the split is false
      if (b.subtotal != null){
        const playerSum = Math.round(b.playerRows.reduce((s2, x) => s2 + num(x), 0) * 100) / 100;
        if (Math.abs(num(b.subtotal) - playerSum) > 0.005)
          problems.push(name + ' ' + r + '.: "A te döntéseid" ' + num(b.subtotal)
                     + ', sum of the player rows ' + playerSum);
      }
      // c) header = the GUARD on the Fordulok tab
      const f = num(rounds[r]);
      if (f == null || Math.abs(f - head) > 0.005)
        problems.push(name + ' ' + r + '.: ' + rounds[r] + ' on the Fordulók tab, ' + head + ' here');
    }
    // d) the per-round sum = the table's GUA cell
    cum = Math.round(cum * 100) / 100;
    const t = num(table[name]);
    if (t == null || Math.abs(t - cum) > 0.005)
      problems.push(name + ': ' + table[name] + ' in the table, sum of the tabs ' + cum);
  }
  check(problems.length === 0, 'every number agrees for every manager and round'
     + (problems.length ? ' — MISMATCH: ' + problems.join(' ; ') : '')
     + (sawBlock ? '' : ' (this league has no closed round with a GUARD yet)'));

  section('A round without changes shows too');
  // THE DATA DECIDES whether such a round EXISTS - we do not assume it.
  // On PL, for example, every team made changes in GW2, so there is nothing
  // to show there; if we claimed "there must be an empty block" then too,
  // the test would blame REALITY. But if the data DOES have an unchanged
  // manager-round, the tab MUST SHOW it.
  const inData = await p.evaluate(async url => {
    try {
      const r = await fetch(url + '?t=' + Date.now());
      if (!r.ok) return false;
      const j = (await r.json()).rounds || {};
      return Object.values(j).some(f => Object.values(f).some(
        v => !v.ki.length && !v.be.length && !v.szerep.length && !v.bonusz));
    } catch (e) { return false; }
  }, L.path === 'pl/' ? '../draft_keretvaltozasok.json' : '../keretvaltozasok.json');
  // This is not decoration: if it were left out, the viewer would think the
  // data is missing - when the answer is exactly that the manager did not
  // touch the squad at all.
  let hasEmpty = false;
  for (const name of names) {
    await open(name, L.tab);
    // A FIXED WAIT DOES NOT WORK: the list is drawn after keretvaltozasok.json
    // arrives, and as the data grows it slips out of a 120 ms window - the
    // test then measures "no such round" when there is one. We wait for the
    // STATE: the list is ready, or we said there is no data.
    await p.waitForFunction(() => {
      const b = document.getElementById('mBody');
      return b && (b.querySelector('.valtlista') || /nincs elmentett|Nincs adat/i.test(b.innerText));
    }, null, { timeout: 10000 }).catch(() => {});
    if (await p.$('#mBody .vaures')) { hasEmpty = true; break; }
  }
  check(hasEmpty || !inData || !sawBlock,
     !inData
       ? 'the data has no round without changes right now — nothing to show'
       : 'there is a round that says "Nem változtatott a keretén."'
         + (sawBlock ? '' : ' (this league has no closed round with a GUARD yet)'));

  section('The round in progress is there without points');
  // The squad is locked after the deadline, so the change is already known
  // - its points are not. Then the block is there, but contains NO number at
  // all: neither in the rows nor in the total. A "0" would be a lie.
  //
  // THE DATA DECIDES WHOM WE OPEN. The earlier version examined the FIRST
  // manager who had a block without points, and required it to have rows -
  // although someone who did not touch the squad correctly has NO rows. As
  // soon as the first one in order happened to have no change, the test
  // blamed reality. Now the data says who MUST show rows and who must show
  // "Nem valtoztatott".
  const current = await p.evaluate(async url => {
    try {
      const r = await fetch(url + '?t=' + Date.now());
      if (!r.ok) return null;
      const j = (await r.json()).rounds || {};
      // the round in progress: there the GUARD is null for EVERYONE
      const keys = Object.keys(j).map(Number).sort((a, b) => b - a);
      for (const r2 of keys){
        const f = j[r2], values = Object.values(f);
        if (!values.length || !values.every(v => v.guard == null)) continue;
        const changed = x => !!((x.ki || []).length || (x.be || []).length
                             || (x.szerep || []).length);
        return {
          r: r2,
          changed:   Object.keys(f).find(k => changed(f[k])) || null,
          unchanged: Object.keys(f).find(k => !changed(f[k])) || null,
        };
      }
      return null;
    } catch (e) { return null; }
  }, L.path === 'pl/' ? '../draft_keretvaltozasok.json' : '../keretvaltozasok.json');

  // The state of the block without points for ONE opened manager.
  const blockWithoutPoints = async name => {
    await open(name, L.tab);
    await p.waitForFunction(() => {
      const b = document.getElementById('mBody');
      return b && (b.querySelector('.valtlista') || /nincs elmentett|Nincs adat/i.test(b.innerText));
    }, null, { timeout: 10000 }).catch(() => {});
    return p.$$eval('#mBody .vakor', bs => {
      const b = bs.find(x => x.querySelector('.vafej .vamegj'));
      return b ? { title: b.querySelector('.vafej span').textContent.trim(),
                   note: b.querySelector('.vafej .vamegj').textContent.trim(),
                   guardMark: !!b.querySelector('.vafej .guardjel'),
                   total: !!b.querySelector('.vaossz'),
                   rows: b.querySelectorAll('.vasor:not(.vaures)').length,
                   empty: !!b.querySelector('.vaures'),
                   emptyDiff: [...b.querySelectorAll('.zdiff')].every(x => !x.textContent.trim()),
                   emptyValue: [...b.querySelectorAll('.vaert')].every(x => !x.textContent.trim()) } : null;
    });
  };

  if (!current){
    check(true, 'skipped: there is no round right now whose squad is locked but has no points yet');
  } else {
    if (current.changed){
      const t = await blockWithoutPoints(current.changed);
      check(!!t, 'whoever made changes (' + current.changed + ') has the block without points');
      if (t){
        check(t.title.includes(current.r), 'the block belongs to the current round (' + t.title + ')');
        check(/nincs pontszám/.test(t.note),
           'the header says there are no points yet ("' + t.note + '")');
        check(!t.guardMark && !t.total, 'no GUARD in the header and no "Összesen" row');
        check(t.rows > 0, 'but the change itself shows (' + t.rows + ' rows)');
        check(t.emptyDiff && t.emptyValue, 'not a single number in the rows — a "0" would be a lie');
      }
    } else {
      check(true, 'skipped: nobody made changes in the current round');
    }
    // The OTHER case, which used to cause a false failure: someone who did
    // not touch the squad gets the "Nem valtoztatott" message, not rows.
    if (current.unchanged){
      const u = await blockWithoutPoints(current.unchanged);
      check(!!u, 'whoever made no changes (' + current.unchanged + ') has the block too');
      if (u){
        check(/nincs pontszám/.test(u.note), 'it also says "még nincs pontszám"');
        check(u.rows === 0 && u.empty,
           'instead of rows the "Nem változtatott a keretén." message stands');
      }
    } else {
      check(true, 'skipped: everybody made changes in the current round');
    }
  }

  section('The names are clickable');
  await open(names[0], L.tab);
  if (!sawBlock){
    check(true, 'skipped: this league has no closed round with a GUARD yet');
    check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
    await p.close();
    return;
  }
  await p.waitForSelector('#mBody .valtlista .vanev.kattint', { timeout: 10000 });
  const name0 = await p.$eval('#mBody .valtlista .vanev.kattint', e => e.textContent.trim());
  await p.$eval('#mBody .valtlista .vanev.kattint', e => e.click());
  await p.waitForTimeout(600);
  const titleLine = await p.$eval('#mTitle', e => e.textContent.trim());
  check(name0.indexOf(titleLine) === 0 || titleLine.length > 0 && name0.indexOf(titleLine.split(' ')[0]) >= 0,
     'clicking the name opens the player profile (' + titleLine + ')');

  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

/* On PL there is not yet a SINGLE closed round with a GUARD (GW1 by
   definition has none, and GW2 has not closed yet), so the run above only
   measures the EMPTY state there. But the tab's behaviour has to be proven
   NOW, not later - so we write the GW2 result into the schedule on the fly
   and check the same derivation. */
async function plClosed(br){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  await rewriteJson(p, '**/draft.json*', j => {
    (j.schedule['2'] || []).forEach(m => { if (m[2] == null){ m[2] = 40; m[3] = 30; } });
    return j;
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForFunction(() => document.querySelector('#table td.guard'), null, { timeout: 20000 });
  const ids = await p.$$eval('#table tr [data-team]', a => a.map(x => x.dataset.team));
  const problems = [];
  for (const id of ids){
    await p.evaluate(i => showTeam(+i, 'fordulok', 'replace'), id);
    await p.waitForSelector('#mBody table tr', { timeout: 10000 });
    const roundGuard = await p.$$eval('#mBody table tr', trs => {
      const head = [...trs[0].children].map(x => x.textContent.trim());
      const gi = head.indexOf('GUARD'), out = {};
      trs.slice(1).forEach(tr => { out[parseInt(tr.children[0].textContent)] = tr.children[gi].textContent.trim(); });
      return out;
    });
    await p.evaluate(i => showTeam(+i, 'valtoztatasok', 'replace'), id);
    await p.waitForSelector('#mBody .valtlista', { timeout: 10000 });
    const b = await p.$eval('#mBody .vakor', b => ({
      title: b.querySelector('.vafej span').textContent.trim(),
      head: (b.querySelector('.vafej .guardjel') || {}).textContent,
      rows: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz) .zdiff')].map(x => x.textContent.trim()),
      playerRows: [...b.querySelectorAll('.vasor:not(.vaossz):not(.vaures):not(.vareszossz):not(.vagep) .zdiff')].map(x => x.textContent.trim()),
      subtotal: (b.querySelector('.vareszossz .zdiff') || {}).textContent,
      auto: (b.querySelector('.vagep .zdiff') || {}).textContent,
      empty: !!b.querySelector('.vaures'),
      total: (b.querySelector('.vaossz .zdiff') || {}).textContent,
    }));
    const r = parseInt(b.title), head = num(b.head);
    const rowSum = Math.round(b.rows.reduce((s, x) => s + num(x), 0) * 100) / 100;
    if (!b.empty && Math.abs(rowSum - head) > 0.005)
      problems.push(id + ': row sum ' + rowSum + ', header ' + head);
    if (!b.empty && Math.abs(num(b.total) - head) > 0.005)
      problems.push(id + ': Összesen ' + num(b.total) + ', header ' + head);
    if (Math.abs(num(roundGuard[r]) - head) > 0.005)
      problems.push(id + ': ' + roundGuard[r] + ' on the Fordulók tab, ' + head + ' here');
    // WHAT THE HUMAN DID + WHAT THE MACHINE DID: the two together are the
    // GUARD, and the human's part is the sum of the player rows. If this
    // slips, the tab would suggest the manager did what the automatic
    // substitution at closing did.
    const playerSum = Math.round(b.playerRows.reduce((s2, x) => s2 + num(x), 0) * 100) / 100;
    if (b.subtotal == null || Math.abs(num(b.subtotal) - playerSum) > 0.005)
      problems.push(id + ': line-up rework row ' + b.subtotal + ', sum of the player rows ' + playerSum);
    if (b.auto == null)
      problems.push(id + ': the automatic substitution row is missing');
    else if (Math.abs(playerSum + num(b.auto) - head) > 0.005)
      problems.push(id + ': human ' + playerSum + ' + machine ' + num(b.auto) + ' ≠ ' + head);
  }
  check(ids.length > 0 && problems.length === 0,
     'with a closed round every number agrees on PL too (' + ids.length + ' teams)'
     + (problems.length ? ' — MISMATCH: ' + problems.join(' ; ') : ''));
  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

/* MEASURED: `?v=` only busts the cache of funtasy.js/css, NOT of
   nb1/index.html - and the server answers the old ?v= request with the
   CURRENT funtasy.js too. So the browser's OLD page (which still passed the
   items in one piece, as unlabelled `sorok`) met the NEW renderer: the round
   header showed the GUARD, but under it "Nem valtoztatott a kereten." - even
   though three players had been swapped. The renderer has understood BOTH
   shapes since; this test keeps that alive. */
async function oldShape(br){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  const k = await p.evaluate(() => {
    document.getElementById('mBody').innerHTML = FunTasy.changesList(
      [{ nev: '2. forduló', guard: 2,
         sorok: [{ poszt: 'ST', nev: 'X', klub: 'K', cimke: 'kapitány', dl: -6 },
                 { poszt: 'MID', nev: 'Y', klub: 'K', ert: 8, dl: 8 }] }], 'nincs');
    const b = document.querySelector('#mBody .vakor');
    return { rows: b.querySelectorAll('.vasor:not(.vaossz):not(.vaures)').length,
             empty: !!b.querySelector('.vaures'),
             total: (b.querySelector('.vaossz .zdiff') || {}).textContent };
  });
  check(k.rows === 2 && !k.empty,
     'the items are drawn from the unlabelled `sorok` shape too (' + JSON.stringify(k) + ')');
  check(k.total && k.total.replace(',', '.').indexOf('2') >= 0,
     'and the Összesen row is there too (' + k.total + ')');
  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

/* On PL there is currently NO round whose squad is locked but has no points
   yet - so the run above skips that measurement there. But the behaviour has
   to be proven NOW: we remove the latest round's results from the schedule,
   which makes the page treat it as "not yet closed". */
async function plWithoutPoints(br){
  const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  const GW = await new Promise(r => {
    const j = require(require('path').join(__dirname, '..', 'draft_keretvaltozasok.json'));
    r(Object.keys(j.rounds).map(Number).sort((a, b) => b - a)[0] + '');
  });
  await rewriteJson(p, '**/draft.json*', j => {
    j.schedule[GW] = (j.schedule[GW] || []).map(m => [m[0], m[1], null, null]);
    return j;
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 20000 });
  await p.waitForTimeout(1500);
  const id = await p.$eval('#table tr [data-team]', e => e.dataset.team);
  await p.evaluate(i => showTeam(+i, 'valtoztatasok', 'replace'), id);
  await p.waitForSelector('#mBody .valtlista', { timeout: 10000 });
  // We look the block up BY ROUND NUMBER instead of taking the first one: the
  // rounds stand in ASCENDING order, so as soon as there were several closed
  // rounds, the first block was no longer the round under test (without points).
  const t = await p.$$eval('#mBody .vakor', (bs, gw) => {
    const b = bs.find(x => parseInt(x.querySelector('.vafej span').textContent) === +gw);
    if (!b) return null;
    return ({
    note: (b.querySelector('.vafej .vamegj') || {}).textContent,
    guardMark: !!b.querySelector('.vafej .guardjel'),
    total: !!b.querySelector('.vaossz'),
    auto: !!b.querySelector('.vagep'),
    rows: b.querySelectorAll('.vasor:not(.vaures)').length,
    emptyDiff: [...b.querySelectorAll('.zdiff')].every(x => !x.textContent.trim()),
  });
  }, GW);
  check(!!t, 'the block of round ' + GW + ' is there');
  if (!t){ await p.close(); return; }
  check(/nincs pontszám/.test(t.note || ''),
     'PL: the header says there are no points yet ("' + t.note + '")');
  check(!t.guardMark && !t.total, 'PL: no GUARD and no "Összesen" row');
  check(!t.auto, 'PL: no automatic-substitution row either — the automatic substitution has not happened yet');
  check(t.rows > 0 && t.emptyDiff,
     'PL: the change shows (' + t.rows + ' rows), without numbers');
  // THE TAB IS NOT ABOUT THE VIEWER. The same tab can be opened on any
  // manager's page, so a caption like "a kezdod atalakitasa" (your line-up's
  // rework) points at a different person than the one the viewer is reading
  // about. The error is silent: every number is right, only the sentence lies.
  // We look at the CAPTIONS, not the whole text of the rows: in a row the
  // position mark and the name run together ("kezdo" + "DEF"), and that gives
  // a false match.
  const e2 = await p.$$eval('#mBody .vakor .vanev, #mBody .vakor .vacimke, #mBody .note',
    n => n.map(x => x.textContent.trim())
          .join(' | ')
          .match(/(kereted|kezdőd|csapatod|neked|nálad|döntésed|általad)\w{0,8}/gi) || []);
  check(e2.length === 0,
     'the tab does not address the viewer (second person singular)'
     + (e2.length ? ' — ' + [...new Set(e2)].join(', ') : ''));
  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
}

(async () => {
  const br = await launch();
  for (const L of LEAGUES){
    section('=== ' + L.path.replace('/', '').toUpperCase() + ' ===');
    await league(br, L);
  }
  section('=== PL, with a closed round (schedule completed on the fly) ===');
  await plClosed(br);
  section('=== PL, round without points (not yet closed) ===');
  await plWithoutPoints(br);
  section('=== The old, unlabelled data shape renders too ===');
  await oldShape(br);
  await finish(br);
})();
