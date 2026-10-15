const { BASE, check, section, launch, finish } = require('./common');
// THE NEMZETHY SPORT PAGE (nemzethy/): every piece of writing in one place.
//
// On the match sheet the strip answers what happened in THAT match. This
// page is for whoever wants to read the whole thing in one go - and the two
// views could easily drift apart on what may be shown. So the essence here
// is the GATE: the magazine may not show more than the match sheet.
//
// TWO MODES. `?liga=nb1` is the paper of THAT LEAGUE - with its own colours,
// its own name, only its own articles -, without a parameter it is the
// shared edition. From a league page it opens from the top bar, from the
// home page the shared one opens.
//
// What it pins down:
//  - the header is the page name and the slogan;
//  - every published article appears, with its FULL text (not a teaser);
//  - the summary of a round not yet closed is not shown here either, only
//    its preview;
//  - four SEPARATE filters (league, manager, round, type), working together:
//    each offers ONLY the values that actually exist alongside the other
//    filters - it cannot be set to an empty result, and the two can be
//    combined FREELY (one person in ONE league);
//  - managers are listed PER PERSON: whoever plays in both leagues is one
//    row with both names, and filtering on him brings articles from both;
//  - under every article there is the rating strip;
//  - "Másolom" copies THE ARTICLE and the link pointing to it;
//  - the page is reachable from the footer.
(async () => {
  const br = await launch();
  const errors = [];
  const p = await br.newPage({ viewport: { width: 1000, height: 1000 } });
  p.on('pageerror', e => errors.push(e.message));
  for (const m of ['**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await p.route(m, r => r.abort());
  // clipboard outside a secure context too: our own, measurable variant
  await p.addInitScript(() => {
    window.__copied = [];
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
      writeText: t => { window.__copied.push(t); return Promise.resolve(); } } });
  });
  await p.goto(BASE + 'nemzethy/');
  await p.waitForSelector('.magcikk', { timeout: 20000 });

  section('Header');
  check((await p.locator('.magcim').textContent()).trim() === 'Nemzethy Sport', 'the page name');
  check((await p.locator('.magszlogen').textContent()).trim() === 'Heti Funtasy Magazin',
     'and the slogan');

  // ---- full text, not a teaser ----
  section('Full text');
  const expected = await p.evaluate(async () => {
    const j = await (await fetch('../articles.json')).json();
    const out = {};
    for (const [lg, rs] of Object.entries(j.leagues || {}))
      for (const [r, ks] of Object.entries(rs))
        for (const [k, m] of Object.entries(ks))
          for (const [pair, a] of Object.entries(m))
            out[lg + '|' + r + '|' + k + '|' + pair] = { paras: a.text.length, teaser: a.short };
    return out;
  });
  const shownParas = await p.$$eval('.magcikk .magtest p', n => n.length);
  const expectedParas = Object.values(expected).reduce((s, x) => s + x.paras, 0);
  check(await p.locator('.magcikk').count() === Object.keys(expected).length,
     `every article is published (${await p.locator('.magcikk').count()}/${Object.keys(expected).length})`);
  check(shownParas === expectedParas,
     `and with its full text, not a teaser (${shownParas}/${expectedParas} paragraphs)`);

  // ---- the gate: it shows no more than the match sheet ----
  section('The gate is closed here too');
  const gate = await p.evaluate(async () => {
    const [j, res, hist] = await Promise.all([
      (await fetch('../articles.json')).json(),
      (await fetch('../results.json')).json(),
      (await fetch('../draft_history.json')).json()]);
    const provisional = new Set((res.provisional || []).map(Number));
    const closed = { nb1: new Set(), pl: new Set(Object.values(hist.veglegesek || []).map(Number)) };
    for (const r in (res.schedule || {}))
      if (!provisional.has(+r) && res.schedule[r].some(m => m && m[2] != null)) closed.nb1.add(+r);
    // every summary whose round is NOT final
    const forbidden = [];
    for (const [lg, rs] of Object.entries(j.leagues || {}))
      for (const [r, ks] of Object.entries(rs))
        if (ks.summary && !closed[lg].has(+r))
          for (const pair of Object.keys(ks.summary)) forbidden.push(lg + ' ' + r + ' ' + pair);
    return { forbidden, closedNb1: [...closed.nb1], closedPl: [...closed.pl] };
  });
  console.log(`   closed rounds — NB1: ${gate.closedNb1.join(',')} · PL: ${gate.closedPl.join(',')}`);
  console.log(`   summaries that must not be published: ${gate.forbidden.length}`);
  // a summary that may not be published is not published
  const shownIds = await p.$$eval('.magcikk', n => n.map(x => x.id));
  const leaked = gate.forbidden.filter(t => {
    const [lg, r] = t.split(' ');
    return shownIds.some(id => id.startsWith('c-' + lg + '-' + r + '-summary'));
  });
  check(leaked.length === 0,
     'the summary of a round not yet closed is not published here either — ' + JSON.stringify(leaked));

  // ---- filters ----
  section('Filters');
  const all = await p.locator('.magcikk').count();
  const groups = async () => p.$$eval('.magszuro',
                                      n => n.map(x => x.options[0].text));
  check(JSON.stringify(await groups()) ===
       JSON.stringify(['Liga', 'Szakvezető', 'Forduló', 'Típus']),
     'four separate filters — ' + (await groups()).join(', '));
  check(await p.evaluate(() =>
       Math.round(document.querySelector('.magszurok').getBoundingClientRect().height)) < 130,
     'the filter bar does not eat up the page — '
     + await p.evaluate(() =>
         Math.round(document.querySelector('.magszurok').getBoundingClientRect().height)) + ' px');

  // a drop-down, not a row of buttons: on a phone it opens the system's own picker
  const pick = async (filter, value) => {
    await p.selectOption(`.magszuro[data-szuro="${filter}"]`, value);
    await p.waitForTimeout(150);
  };
  await pick('liga', 'nb1');
  const nb1Count = await p.locator('.magcikk').count();
  check(nb1Count > 0 && nb1Count < all, `filtered by league there are fewer (${nb1Count}/${all})`);
  // The list is in PUBLICATION order, so the leagues are mixed: there is no
  // league heading, the league name is in the header of every article.
  check(await p.$$eval('.magcikk .magfordulo',
                    n => n.length > 0 && n.every(x => /^NB1 ·/.test(x.textContent))),
     'the header of every shown article carries the league name');
  await pick('liga', 'pl');
  const plCount = await p.locator('.magcikk').count();
  check(nb1Count + plCount === all, `the two leagues make up the whole (${nb1Count} + ${plCount} = ${all})`);
  await pick('liga', 'mind');

  // ONE PERSON, ONE ROW. The two leagues know the same manager by DIFFERENT
  // NAMES (a nickname in NB1, a team name in PL), and the shared edition
  // offered them twice because of that, as two separate people. What this
  // pins down: whoever plays in both leagues stands in ONE row with both
  // names - and filtering on him brings the articles of BOTH leagues.
  const people = await p.$$eval('.magszuro[data-szuro="ki"] option',
    n => n.filter(x => x.value !== 'mind')
          .map(x => ({ value: x.value, label: x.text })));
  // The names come from the articles themselves (the two text nodes of the
  // pairing), the people from the page's own name->person resolution: this
  // way the test does not repeat the mapping table, it only claims that the
  // names ARE merged.
  const counts = await p.evaluate(() => {
    const names = new Set();
    // Names come only from the heading of the HEAD-TO-HEADS. The weekly
    // column has no opponent, so its title stands in the heading - that is
    // not a manager, and it is not in the filter either; if it counted here,
    // the test would expect more names than there are people.
    document.querySelectorAll('.magcikk .magpar').forEach(h => {
      if (!h.querySelector('.magvs')) return;
      [...h.childNodes].forEach(c => {
        const t = c.nodeType === 3 ? c.textContent.trim() : '';
        if (t) names.add(t);
      });
    });
    return { names: names.size,
             people: new Set([...names].map(n => PERSON(n).key)).size };
  });
  check(people.length === counts.people && counts.people < counts.names,
     `${counts.names} names, but ${people.length} rows in the filter — whoever plays `
     + 'in both leagues appears once');
  const twoLeague = people.filter(x => x.label.includes(' · '));
  check(twoLeague.length === counts.names - counts.people,
     `and shows his two league names together — ${twoLeague.map(x => x.label).join(' | ')}`);

  const chosen = twoLeague[0];
  await pick('ki', chosen.value);
  const rows = await p.$$eval('.magcikk', n => n.map(x => ({
    league: x.id.split('-')[1], pair: x.querySelector('.magpar').textContent })));
  const hisNames = chosen.label.split(' · ');
  check(rows.length > 0 && rows.every(x => hisNames.some(n => x.pair.includes(n))),
     `${chosen.label}: all ${rows.length} articles are about him`);
  check(new Set(rows.map(x => x.league)).size === 2,
     'and from both leagues — one person, one filter');
  // the other filters now offer ONLY the values that belong to him
  const rounds = await p.$$eval('.magszuro[data-szuro="fordulo"] option',
                                n => n.map(x => x.value));
  // The header reads "NB1 · 8. forduló", so the number has to be looked for
  // AFTER the league name - read from the start it would be NaN, and the list
  // would look empty.
  const expectedRounds = await p.$$eval('.magcikk .magfordulo',
    n => [...new Set(n.map(x => Number((x.textContent.match(/(\d+)\.\s*forduló/) || [])[1])))]);
  check(rounds.filter(x => x !== 'mind').length === expectedRounds.length,
     `the list of rounds narrowed with it (${rounds.filter(x => x !== 'mind').join(',')})`);

  // THE TWO FILTERS ARE INDEPENDENT: you can filter by person AND league at
  // once. While they shared one control, the question could not even be asked.
  await pick('liga', 'nb1');
  const together = await p.$$eval('.magcikk', n => n.map(x => x.id.split('-')[1]));
  check(together.length > 0 && together.length < rows.length
     && together.every(x => x === 'nb1'),
     `by person AND league at once (${together.length}/${rows.length} articles, NB1 only)`);
  await pick('liga', 'mind');
  await pick('ki', 'mind');

  await pick('fajta', 'summary');
  const labels2 = await p.$$eval('.magcikk .magrovat', n => n.map(x => x.textContent));
  check(labels2.length > 0 && labels2.every(t => /Összefoglaló/i.test(t)),
     `it filters by type too (${labels2.length} summaries)`);
  check(/\d+ \/ \d+/.test(await p.locator('.magszam').textContent()),
     'it says how many of how many are shown — ' + await p.locator('.magszam').textContent());
  check(await p.locator('.magtorol').count() === 1, 'and the whole filtering can be cleared with one button');
  await p.locator('.magtorol').click();
  await p.waitForTimeout(150);
  check(await p.locator('.magcikk').count() === all, 'clearing gives back the whole');
  check(await p.locator('.magtorol').count() === 0, 'without filtering the clear button disappears');

  // ---- rating and copying ----
  section('Rating and copying');
  check(await p.locator('.magcikk .artrate').count() === all,
     'under every article there is the rating strip');
  const first = p.locator('.magcikk').first();
  const fullText = await first.locator('.magmaso').getAttribute('data-szoveg');
  await first.locator('.magmaso').click();
  await p.waitForFunction(() => window.__copied && window.__copied.length, null, { timeout: 5000 });
  const copied = (await p.evaluate(() => window.__copied[0])) || '';
  // The ARTICLE goes to the clipboard, not the teaser: whoever copies takes the text.
  check(copied.startsWith(fullText) && fullText.indexOf('\n\n') > 0,
     `the full article went to the clipboard (${fullText.split('\n\n').length} paragraphs)`);
  check(/\/nemzethy\/#c-/.test(copied),
     'and at the end the link pointing to the article — ' + copied.split('\n').pop());
  check(/Kimásolva/.test(await first.locator('.magmaso').textContent()), 'the button gives feedback too');

  // ---- reachable from the footer ----
  section('Reachability');
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#lablec a');
  check(await p.locator('#lablec a[href$="nemzethy/"]').count() === 1,
     'reachable from the footer of the league page too');

  // ---- league mode ----
  for (const lg of ['nb1', 'pl']){
    section('League paper — ' + lg);
    await p.goto(BASE + 'nemzethy/?liga=' + lg);
    await p.waitForSelector('.magcikk', { timeout: 20000 });
    const a = await p.evaluate(() => ({
      theme: document.body.className,
      tag: (document.querySelector('.magcim .tag') || {}).textContent,
      slogan: document.querySelector('.magszlogen').textContent,
      articles: document.querySelectorAll('.magcikk').length,
      leagueFilter: document.querySelectorAll('.magszuro[data-szuro="liga"]').length,
      filterGroups: document.querySelectorAll('.magszuro').length,
      leagueHeading: document.querySelectorAll('.magliga').length,
      other: document.getElementById('magMasik').style.display !== 'none',
      height: document.scrollingElement.scrollHeight,
      overflow: document.scrollingElement.scrollWidth - document.documentElement.clientWidth,
    }));
    check(a.theme === 'liga-' + lg, `${lg}: the page takes on the league's colours (${a.theme})`);
    check((a.tag || '').trim().toLowerCase() === lg, `the league name is in the header (${a.tag})`);
    check(a.articles > 0 && a.articles < all, `only this league's articles (${a.articles}/${all})`);
    check(a.leagueFilter === 0 && a.leagueHeading === 0,
       'no league filter and no league heading — this is already its own paper');
    check(a.filterGroups === 3,
       `the three filters are there though: manager, round, type (${a.filterGroups})`);
    check(a.other, 'and there is a way across to the shared edition');
    check(a.overflow === 0, `on a phone nothing sticks out sideways (${a.overflow} px)`);
    console.log(`   page height on a phone: ${a.height} px`);
  }

  // ---- entry points ----
  section('Entry points');
  for (const [path, expectedHref] of [['nb1/', '../nemzethy/?liga=nb1'],
                                      ['pl/', '../nemzethy/?liga=pl']]){
    await p.goto(BASE + path);
    await p.waitForSelector('.liganav .ujsaglink', { timeout: 20000 });
    const g = p.locator('.liganav .ujsaglink');
    check(await g.getAttribute('href') === expectedHref,
       `the top bar of /${path} opens its OWN paper (${await g.getAttribute('href')})`);
    check((await g.textContent()).includes('Nemzethy Sport'), 'and its name is there too');
  }
  await p.goto(BASE);
  await p.waitForSelector('.ujdonsagsor');
  check(await p.locator('.ujdonsagsor[href="nemzethy/"]').count() === 1,
     'from the home page the SHARED edition opens, on a highlighted row');
  // THE TWO LEVELS. The leagues are alternatives to each other; the paper is
  // PART OF the given league. So everywhere EXACTLY ONE item lights up - the
  // one where you are -, and the paper's button does not disappear while you
  // are on it. Earlier it disappeared, and the way back was the league's own
  // dot, which did not look like a way back.
  section('The two levels of the top bar');
  for (const [path, expectedActive, expectedLeagueLink] of [
        ['nb1/', 'NB1', null],
        ['nemzethy/?liga=nb1', 'Nemzethy Sport NB1', '../nb1/'],
        ['nemzethy/', 'Nemzethy Sport', null]]) {
    await p.goto(BASE + path);
    await p.waitForSelector('.liganav a', { timeout: 20000 });
    const a = await p.evaluate(() => ({
      active: [...document.querySelectorAll('.liganav a.on')]
                 .map(x => x.textContent.trim()),
      paper: !!document.querySelector('.liganav .ujsaglink'),
      nb1href: (document.querySelector('.liganav .ligalink') || {}).getAttribute
                 ? document.querySelector('.liganav .ligalink').getAttribute('href') : null,
      nb1active: (document.querySelector('.liganav .ligalink') || {}).className || '',
    }));
    check(a.active.length === 1 && a.active[0] === expectedActive,
       `/${path || ''}: exactly one item lights up, the one where you are — ${JSON.stringify(a.active)}`);
    check(a.paper, `/${path || ''}: the paper's button is there (it does not disappear)`);
    if (expectedLeagueLink)
      check(!a.nb1active.includes('on') && a.nb1href === expectedLeagueLink,
         `from the paper the league's dot leads back to the league page (${a.nb1href})`);
  }

  errors.forEach(x => check(false, 'page error: ' + x));
  await finish(br);
})();
