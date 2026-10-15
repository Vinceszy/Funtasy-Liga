const { BASE, check, section, launch, finish } = require('./common');
// NO PAGE STICKS OUT SIDEWAYS.
//
// Earlier this was "solved" by an `html,body{overflow-x:hidden}` rule:
// whatever stuck out was simply cut off. But iOS Safari turns an element
// into its own scroll box when it is clipped horizontally on html, and
// momentum scrolling breaks - the page does not start, it shudders, starts,
// then runs back. So the clipping is not free.
//
// So instead of clipping, we MEASURE what it was meant to protect. This test
// is the real claim: the content fits. If a new element sticks out, it shows
// up here, not by having its edge silently cut off.
const WIDTHS = [320, 360, 390, 412];

(async () => {
  const br = await launch();
  const errors = [];
  for (const w of WIDTHS) {
    const ctx = await br.newContext({ viewport: { width: w, height: 820 },
                                      deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const p = await ctx.newPage();
    p.on('pageerror', e => errors.push(`${w}px: ${e.message}`));
    for (const m of ['**mlsz.hu/**', '**premierleague.com/**', '**corsproxy.io/**',
                     '**allorigins**', '**workers.dev/**', '**fonts.googleapis.com/**',
                     '**fonts.gstatic.com/**'])
      await p.route(m, r => r.abort());
    section(w + ' pixels');

    // The error message must NAME the culprit: "sticks out by 12 pixels" on
    // its own does not tell what has to be fixed.
    const measure = async label => {
      const r = await p.evaluate(() => {
        const d = document.documentElement;
        const overflow = d.scrollWidth - d.clientWidth;
        const culprits = overflow > 0 ? [...document.querySelectorAll('*')]
          .filter(e => e.getBoundingClientRect().right > d.clientWidth + 1)
          .slice(0, 3).map(e => e.tagName.toLowerCase()
            + (e.className ? '.' + String(e.className).split(/\s+/)[0] : '')) : [];
        return { overflow, culprits };
      });
      check(r.overflow === 0, `${label}: does not stick out sideways`
         + (r.overflow ? ` — ${r.overflow} px, caused by: ${r.culprits.join(', ')}` : ''));
    };

    for (const [path, label] of [['', 'home page'], ['valtozasok/', 'change log'],
                                 ['nemzethy/', 'magazine (shared)'],
                                 ['nemzethy/?liga=nb1', 'magazine (NB1)'],
                                 ['nemzethy/?liga=pl', 'magazine (PL)']]) {
      await p.goto(BASE + path);
      await p.waitForTimeout(700);
      await measure(label);
    }

    // The league pages together with the OPEN views: that is where the wide
    // content is (squad columns, table), so that is where sticking out is
    // easiest.
    await p.goto(BASE + 'nb1/');
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await measure('NB1 home page');
    await p.evaluate(() => showMatchRound('Bence', 'Csendi', 7));
    await p.waitForSelector('#mBody .plr', { timeout: 20000 });
    await measure('NB1 match sheet');
    if (await p.locator('#elteresGomb').count()) {
      await p.click('#elteresGomb');
      await p.waitForTimeout(250);
      await measure('NB1 differences');
    }

    await p.goto(BASE + 'pl/');
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await p.waitForFunction(() => typeof HIST !== 'undefined' && Object.keys(HIST).length > 0,
                            null, { timeout: 20000 });
    await measure('PL home page');
    await p.evaluate(() => {
      const gw = Math.max(...Object.keys(SCHEDULE).map(Number)
        .filter(g => (SCHEDULE[g] || []).some(m => m[2] != null)));
      const [h, v] = SCHEDULE[gw][0];
      showMatch(h, v, gw, 'root');
    });
    await p.waitForSelector('#mBody .plr', { timeout: 20000 });
    await measure('PL match sheet');
    await ctx.close();
  }
  errors.forEach(x => check(false, 'page error: ' + x));
  await finish(br);
})();
