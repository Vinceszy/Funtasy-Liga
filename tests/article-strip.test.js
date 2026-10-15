const { BASE, check, section, launch, finish, rewriteJson, blockApis } = require('./common');

// The round we have a preview for - stated here once, so that the
// precondition (no squad for it) and the opened match cannot drift apart.
const PREVIEW_R = 9;
// The round preview / round summary strip on the match page.
//
// The one thing this strip must never do is get in the way of the numbers.
// It sits above the squad columns, so every assertion here is about that:
// it comes collapsed, it costs one line, the columns stay on screen, and a
// fixture nobody wrote about gets no strip at all.
//
// Also recorded: the text matches articles.json paragraph for paragraph,
// the open state survives a redraw (a live round redraws the body every
// few seconds), and on a round with no squads yet the preview comes open,
// because there it is the only thing on the page.

// a played round with summaries, and a fixture from it
const R = 7, HOME = 'Bence', AWAY = 'Csendi';
// a fixture from the same round that has no article
const EMPTY_R = 4, EH = 'Bazsa', EA = 'Csendi';

(async () => {
  const br = await launch();
  const errors = [];

  for (const [w, h, label] of [[1000, 900, 'DESKTOP'], [390, 844, 'MOBILE']]) {
    const p = await br.newPage({ viewport: { width: w, height: h } });
    p.on('pageerror', e => errors.push(label + ': ' + e.message));
    for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
      await p.route(m, r => r.abort());
    await p.goto(BASE + 'nb1/');
    await p.waitForSelector('#table tr');
    // the strip only renders once articles.json is in - the page loads it
    // beside everything else, so wait for it rather than for a timer
    await p.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                            null, { timeout: 20000 });
    await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [HOME, AWAY, R]);
    await p.waitForSelector('#mBody .plr');
    await p.waitForSelector('#mBody .artstrip');

    section(label);
    const strip = p.locator('#mBody .artstrip');
    const measure = async () => p.evaluate(() => {
      const s = document.querySelector('#mBody .artstrip');
      const q = document.querySelector('#mBody .sqwrap');
      return { strip: s.getBoundingClientRect().height,
               head: s.querySelector('.artstriphead').getBoundingClientRect().height,
               squadTop: q.getBoundingClientRect().top,
               open: s.open };
    });

    const closed = await measure();
    check(closed.open === false, 'closed round: the strip comes COLLAPSED');
    check(closed.head < 48, `the collapsed header is one line (${Math.round(closed.head)} px)`);
    check(closed.strip < 60, `the collapsed strip pushes nothing down (${Math.round(closed.strip)} px)`);
    check(closed.squadTop < h,
       `the squad columns stay on screen (their top ${Math.round(closed.squadTop)} px, ` +
       `window ${h} px)`);
    // The lead must stay ONE line however long it is - that is what keeps
    // the collapsed height fixed. A short lead fits on a wide screen, so
    // the clipping is measured with a lead that cannot possibly fit.
    const clipped = await p.evaluate(() => {
      const l = document.querySelector('#mBody .artstriplead');
      const original = l.textContent, height = l.getBoundingClientRect().height;
      l.textContent = 'sokkal hosszabb felütés '.repeat(40);
      const r = { oneLine: height < 26,
                  longStillOneLine: l.getBoundingClientRect().height < 26,
                  cut: l.scrollWidth > l.clientWidth };
      l.textContent = original;
      return r;
    });
    check(clipped.oneLine, 'the lead runs on a single line');
    check(clipped.longStillOneLine && clipped.cut,
       'a lead of any length stays one line, its end cut off');

    // ---- opening ----
    await strip.locator('.artstriphead').click();
    await p.waitForTimeout(120);
    const opened = await measure();
    check(opened.open === true, 'it opens on click');
    check(opened.strip > closed.strip + 40, `the open strip is taller (${Math.round(closed.strip)} → ` +
       `${Math.round(opened.strip)} px)`);
    check(opened.squadTop > closed.squadTop,
       'the squad columns slide down ONLY when it opens');

    // the text is the file's text, paragraph for paragraph
    const match = await p.evaluate(async ([a, b, r]) => {
      const j = await (await fetch('../articles.json')).json();
      const c = j.leagues.nb1[r].summary[a + '|' + b];
      const ps = [...document.querySelectorAll('#mBody .artstripbody p')].map(x => x.textContent);
      return { count: ps.length, expected: c.text.length,
               first: ps[0] === c.text[0], last: ps[ps.length - 1] === c.text[c.text.length - 1],
               lead: document.querySelector('#mBody .artstriplead').textContent === c.short,
               tag: document.querySelector('#mBody .artstriptag').textContent };
    }, [HOME, AWAY, String(R)]);
    check(match.count === match.expected && match.count > 0,
       `every paragraph is shown (${match.count}/${match.expected})`);
    check(match.first && match.last, 'the text is the file\'s, word for word');
    check(match.lead, 'the collapsed strip shows the short version');
    check(match.tag === 'Összefoglaló', `on a closed round the tag is "Összefoglaló" (${match.tag})`);

    // ---- collapsing: nothing is left behind ----
    await strip.locator('.artstriphead').click();
    await p.waitForTimeout(120);
    const reclosed = await measure();
    check(Math.abs(reclosed.squadTop - closed.squadTop) < 2,
       'after collapsing, the squad columns return to their place');

    // ---- a redraw does not collapse it on the viewer ----
    await strip.locator('.artstriphead').click();
    await p.waitForTimeout(120);
    await p.evaluate(() => matchBody());
    await p.waitForSelector('#mBody .artstrip');
    check(await p.evaluate(() => document.querySelector('#mBody .artstrip').open),
       'it stays open after a redraw (on a live round the body is rebuilt every minute)');

    // ---- match without an article: NO strip ----
    await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [EH, EA, EMPTY_R]);
    await p.waitForSelector('#mBody .plr');
    check(await p.locator('#mBody .artstrip').count() === 0,
       'a match without an article shows no trace of the strip');
    check(await p.evaluate(() => document.querySelector('#mBody').firstElementChild
                              .classList.contains('meccsfej')),
       'then the match header is the first element — the view is unchanged');

    await p.close();
  }

  // ---- preview on a round that has no squad yet ----
  const p = await br.newPage({ viewport: { width: 1000, height: 900 } });
  p.on('pageerror', e => errors.push('PREVIEW: ' + e.message));
  // We use the SHARED blockApis, not a list of our own: our own listed three
  // hosts, but the fetcher's path list has nine - our own Worker (/tarolt)
  // was missing from it, and through it the LIVE score of round 9 came in.
  // That made the page - correctly - switch to the live view, which has no
  // strip, and the test failed while nothing had changed in the product.
  await blockApis(p);
  // WE STATE THE PRECONDITION instead of inheriting it from the repository's
  // current state: this round has NO squad. We cut off the per-round file,
  // but that alone is not enough - the page then falls back to the FULL
  // history (loadHistory). While the squads of round 9 had not arrived yet,
  // the test was green by accident; when the market closed they arrived, and
  // this claim failed, although nothing had changed in the product.
  await p.route('**/keretek/*.json*', r => r.fulfill({ status: 404, body: '' }));
  await rewriteJson(p, '**/squad_history.json*', j => {
    delete (j.rounds || {})[String(PREVIEW_R)];
    return j;
  });
  // WE REMOVE THE MATCHES TOO: preview = the round has not started yet. As
  // soon as the collector wrote in the matches of round 9, one of them was
  // in progress, and the page - correctly - switched to the "match still in
  // progress" message, which has no strip. The test failed from that while
  // nothing had changed in the product: only the unstated precondition (no
  // match for this round yet) had stopped holding.
  await rewriteJson(p, '**/meccsek.json*', j => {
    delete (j.rounds || {})[String(PREVIEW_R)];
    return j;
  });
  // AND squads.json too: this is the THIRD source of the round's squad data
  // (`fillFromSquads` computes a live score from it, without the network).
  // While the squads of round 9 had not arrived, this file held round 8,
  // and the test was green by accident.
  await rewriteJson(p, '**/squads.json*', j => ({ ...j, squads: {} }));
  // AND the RESULT too: a preview is only shown for a round that has no
  // score yet. As soon as the round started, the provisional score appeared
  // in the schedule, and the page - correctly - went to the played branch,
  // which has no strip. The same trick the pre-round test uses.
  await rewriteJson(p, '**/results.json*', j => {
    (j.schedule[String(PREVIEW_R)] || []).forEach(m => { m[2] = null; m[3] = null; });
    return j;
  });
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#table tr');
  await p.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                          null, { timeout: 20000 });
  const [ph, pa] = await p.evaluate(async r => {
    const j = await (await fetch('../articles.json')).json();
    return Object.keys(j.leagues.nb1[r].preview)[0].split('|');
  }, String(PREVIEW_R));
  section('PREVIEW (no squad yet)');
  await p.evaluate(([a, b, r]) => showMatchRound(a, b, +r), [ph, pa, String(PREVIEW_R)]);
  await p.waitForSelector('#mBody .artstrip');
  check(await p.evaluate(() => document.querySelector('#mBody .artstrip').open),
     'on a round without squads the preview comes OPEN (there is nothing for it to cover)');
  check(await p.evaluate(() => document.querySelector('#mBody .artstriptag').textContent)
       === 'Beharangozó', 'the tag is "Beharangozó"');
  check(await p.evaluate(() => !!document.querySelector('#mBody .loading')),
     'the "még nem kezdődött el" (not started yet) message stays beside it');
  // the reader's own click wins over the default
  await p.locator('#mBody .artstriphead').click();
  await p.waitForTimeout(120);
  await p.evaluate(([a, b]) => showMatchRound(a, b, 9), [ph, pa]);
  await p.waitForSelector('#mBody .artstrip');
  check(await p.evaluate(() => !document.querySelector('#mBody .artstrip').open),
     'if the viewer collapsed it, it stays collapsed');

  await p.close();

  // ---- the same strip on the PL page ----
  // There is no written article for PL yet, but the wiring still has to be
  // measured: the two pages call the same FunTasy.matchArticle, only with a
  // different league key and with a name instead of an id. The store is set
  // up on the page - so no fake file has to go into the repository.
  const q = await br.newPage({ viewport: { width: 1000, height: 900 } });
  q.on('pageerror', e => errors.push('PL: ' + e.message));
  for (const m of ['**premierleague.com/**', '**corsproxy.io/**', '**allorigins**'])
    await q.route(m, r => r.abort());
  await q.goto(BASE + 'pl/');
  await q.waitForSelector('#table tr');
  await q.waitForFunction(() => Object.keys(SCHEDULE).length > 0, null, { timeout: 20000 });
  section('PL');
  const plm = await q.evaluate(() => {
    // the last round that has a played match
    const gw = Object.keys(SCHEDULE).map(Number).sort((a, b) => b - a)
                 .find(g => (SCHEDULE[g] || []).some(played));
    const [h, v] = SCHEDULE[gw][0];
    ARTICLES = { updated: null, leagues: { pl: { [gw]: { summary: {
      [teamName(h) + '|' + teamName(v)]: { text: ['Elso bekezdes.', 'Masodik bekezdes.'],
                                 short: 'Egy mondat a sav szamara.', source: 'manual' } } } } } };
    showMatch(h, v, gw, 'root');
    return { gw, h, v };
  });
  await q.waitForSelector('#mBody .artstrip');
  const pl = await q.evaluate(() => {
    const s = document.querySelector('#mBody .artstrip');
    const w = document.querySelector('#mBody .sqwrap');
    return { open: s.open, height: s.getBoundingClientRect().height,
             tag: s.querySelector('.artstriptag').textContent,
             lead: s.querySelector('.artstriplead').textContent,
             squadTop: w ? w.getBoundingClientRect().top : null };
  });
  check(pl.open === false, `PL: the strip comes collapsed (round ${plm.gw})`);
  check(pl.height < 60, `PL: the collapsed strip is one line (${Math.round(pl.height)} px)`);
  check(pl.tag === 'Összefoglaló' && pl.lead === 'Egy mondat a sav szamara.',
     'PL: the tag and the lead come from the store');
  check(pl.squadTop !== null && pl.squadTop < 900,
     `PL: the squad columns stay on screen (${Math.round(pl.squadTop)} px)`);
  await q.locator('#mBody .artstriphead').click();
  await q.waitForTimeout(120);
  check(await q.$$eval('#mBody .artstripbody p', n => n.length) === 2,
     'PL: opened, both paragraphs are shown');
  await q.evaluate(([h, v, gw]) => showMatch(h, v, gw, 'root'), [plm.h, plm.v, plm.gw]);
  await q.waitForSelector('#mBody .artstrip');
  check(await q.evaluate(() => document.querySelector('#mBody .artstrip').open),
     'PL: it stays open after a redraw');

  // ---- on a closed round BOTH texts stay ----
  // The final whistle does not make the preview obsolete: it says what the
  // question was before the match, the summary says what the answer was -
  // the two together, one under the other, are worth more. We look the pair
  // up FROM THE STORE instead of writing it in: so the test does not go
  // stale with which round we wrote what for.
  section('Closed round: both texts');
  const mk = await br.newPage({ viewport: { width: 1000, height: 900 } });
  mk.on('pageerror', e => errors.push('BOTH: ' + e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
    await mk.route(m, r => r.abort());
  await mk.goto(BASE + 'nb1/');
  await mk.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                          null, { timeout: 20000 });
  const pair = await mk.evaluate(async () => {
    const j = await (await fetch('../articles.json')).json();
    const nb1 = (j.leagues || {}).nb1 || {};
    for (const r of Object.keys(nb1).sort((a, b) => b - a)) {
      const k = nb1[r];
      if (!k.summary || !k.preview) continue;
      const p = Object.keys(k.summary).find(x => k.preview[x]);
      if (p) return { r: +r, sides: p.split('|') };
    }
    return null;
  });
  if (!pair) {
    check(false, 'there is no round with both a summary AND a preview');
  } else {
    await mk.evaluate(([h, v, r]) => showMatchRound(h, v, r),
                     [pair.sides[0], pair.sides[1], pair.r]);
    await mk.waitForSelector('#mBody .artstrip');
    const tags = await mk.$$eval('#mBody .artstriptag', n => n.map(x => x.textContent));
    check(JSON.stringify(tags) === JSON.stringify(['Összefoglaló', 'Beharangozó']),
       `on round ${pair.r} both are there, the summary first — ` + tags.join(', '));
    check(await mk.$$eval('#mBody .artstrip', n => n.filter(x => x.open).length) === 0,
       'and both come collapsed, they do not push the squads away');
  }
  await mk.close();

  // ---- the CLOSING GATE: the summary of a round not yet closed does not show ----
  // Until the round is final, the points can still move (NB1: post-match
  // adjustments, Draft: separate finalisation), so an "X won by this much"
  // text could lie. This does not apply to the preview: it is about what is
  // coming. The text is set up on the page, so the repository does not have
  // to hold an article for an unclosed round.
  //
  // No URL parameter opens the gate: not even an old `?draft=1` bookmark
  // can bring up an early summary.
  for (const [path, label] of [['nb1/', 'GATE — NB1'],
                               ['nb1/?draft=1', 'GATE — NB1, ?draft=1'],
                               ['pl/', 'GATE — PL'],
                               ['pl/?draft=1', 'GATE — PL, ?draft=1']]) {
    const g = await br.newPage({ viewport: { width: 1000, height: 900 } });
    g.on('pageerror', e => errors.push(label + ': ' + e.message));
    // The shared blockApis, not a list of our own: our own Worker (/tarolt)
    // was missing from the hand-written four, and through it the stored
    // score was written into LIVE too - so an old round looked "open" during
    // the search, and closed afterwards.
    await blockApis(g);
    await g.goto(BASE + path);
    await g.waitForSelector('#table tr');
    section(label);
    const nb1 = path.startsWith('nb1');
    // WE WAIT FOR THE PRECONDITION instead of relying on the table: the
    // header row is there before loading, so '#table tr' is satisfied even
    // when the round data is not in yet. The search then ran on the empty
    // state, and the test failed with "no such round" - misleadingly, since
    // the gate was not the problem.
    //
    // On NB1 we wait for the SCHEDULE, not for the live round: the gate can
    // be examined on any unclosed round, and THERE IS NOT ALWAYS A LIVE
    // ROUND. When the championship pauses, LIVE stays empty, and the test
    // stopped on that - although the behaviour under test was fine.
    //
    // SCHEDULE on its own is not enough: an old schedule is baked into the
    // page, and results.json overwrites it only afterwards. A search that
    // runs in between sees a long-closed round as open. The page sets
    // STORED_AT when results.json arrives, in the same step in which it
    // overwrites the schedule.
    await g.waitForFunction(nb1 => nb1 ? (typeof SCHEDULE !== 'undefined'
                                          && Object.keys(SCHEDULE).length > 0
                                          && window.STORED_AT !== undefined)
                                       : (typeof HIST !== 'undefined'
                                          && Object.keys(HIST).length > 0),
                            nb1, { timeout: 20000 });
    const opened = await g.evaluate(async nb1 => {
      // BOTH kinds of text exist for the same match: so it also shows that
      // the gate chooses between them, not just hides
      const store = (league, r, h, v) => ({ updated: null, leagues: { [league]: { [r]: {
        summary: { [h + '|' + v]: { text: ['Osszefoglalo bekezdes.'],
                                    short: 'Osszefoglalo.', source: 'manual' } },
        preview: { [h + '|' + v]: { text: ['Beharangozo bekezdes.'],
                                    short: 'Beharangozo.', source: 'manual' } } } } } });
      if (nb1) {
        // the nearest round NOT YET CLOSED - running or still to come
        const r = Object.keys(SCHEDULE).map(Number).sort((a, b) => a - b)
                    .find(x => !roundClosed(x) && (SCHEDULE[x] || []).length);
        if (!r) return null;
        const [h, v] = SCHEDULE[r][0];
        ARTICLES = store('nb1', r, h, v);
        await showMatchRound(h, v, r);
        return { r, closed: roundClosed(r) };
      }
      // We look for the next unclosed round in the FIXTURE LIST, not in the
      // history of the rounds so far: once they have all closed, the history
      // has no open one, and the test would fail on the state of the season.
      const gw = Object.keys(SCHEDULE).map(Number).sort((a, b) => a - b)
                   .find(x => !roundClosed(x) && (SCHEDULE[x] || []).length);
      if (!gw) return null;
      const [h, v] = SCHEDULE[gw][0];
      ARTICLES = store('pl', gw, teamName(h), teamName(v));
      showMatch(h, v, gw, 'root');
      return { r: gw, closed: roundClosed(gw) };
    }, nb1);
    check(!!opened && opened.closed === false,
       `there is an unclosed round with squads (${opened && opened.r}.)`);
    await g.waitForSelector('#mBody .artstrip', { timeout: 15000 });
    const state = await g.evaluate(() => {
      const s = document.querySelector('#mBody .artstrip');
      return { tag: s.querySelector('.artstriptag').textContent,
               count: document.querySelectorAll('#mBody .artstrip').length,
               text: s.querySelector('.artstripbody p').textContent };
    });
    check(state.count === 1 && state.tag === 'Beharangozó'
         && state.text === 'Beharangozo bekezdes.',
       `on an unclosed round ONLY the preview shows (${state.tag}, ${state.count} strip)`);
    await g.close();
  }

  errors.forEach(x => check(false, 'page error: ' + x));
  await finish(br);
})();
