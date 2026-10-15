const { BASE, check, section, launch, finish, blockApis } = require('./common');
// The FULL state space of the "what to write about a player with 0 points" logic.
// No guessed cases: every meaningful combination runs, and invariants are
// checked on the output. Whatever violates them is listed.

(async () => {
  const br = await launch();
  const p = await br.newPage();
  await p.route('**fantasy-api.mlsz.hu/**', r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof noPointsMessage === 'function' && typeof pointsCellHTML === 'function');

  const out = await p.evaluate(() => {
    LIVE[900] = [];                       // 900 = live round, 901 = closed
    const minutesAgo = m => new Date(Date.now() - m * 60000).toISOString();
    // The midnight placeholder goes in in TWO variants: MLSZ writes midnight
    // when the kick-off is not fixed, and that day can also pass. The two
    // cases mean different things, so different things must be written about
    // them. The dates are built relative to TODAY - hard-coded they would go
    // stale within a day (and they did).
    const midnight = day => new Date(Date.now() + day * 864e5).toISOString().slice(0, 10)
      + 'T00:00:00+02:00';
    const STARTS = {
      'none':         null,
      'midnightFut':  midnight(2),
      'midnightPast': midnight(-5),
      'future':     new Date(Date.now() + 90 * 60000).toISOString(),
      'running30':  minutesAgo(30),
      'running110': minutesAgo(110),
      'old240':     minutesAgo(240),
    };
    const BREAKDOWNS = {
      'empty':      [],
      'min0':       [{ name: 'Játszott perc', value: 0, points: 0 }],
      'min90':      [{ name: 'Játszott perc', value: 90, points: 0 }],
      'scoring':    [{ name: 'Győzelem', value: 1, points: 3 }],
    };
    const rows = [];
    for (const nogame of [false, true])
    for (const [sn, start] of Object.entries(STARTS))
    for (const vege of [undefined, true])
    for (const played of [true, false, undefined])
    for (const [bn, raw] of Object.entries(BREAKDOWNS))
    for (const live of [true, false]) {
      const round = live ? 900 : 901;
      const message = noPointsMessage(played, start, raw, nogame, vege, live);
      const cell = pointsCellHTML({ week: 0, start, vege, played, nogame }, round);
      const dash = cell.indexOf('–') >= 0;
      rows.push({ nogame, sn, vege: !!vege, played: String(played), bn, live, message, dash,
                  state: matchState(start, vege) });
    }
    return rows;
  });

  console.log('all combinations: ' + out.length);

  // ---- invariants ----
  const violations = {};
  const violate = (name, s) => (violations[name] = violations[name] || []).push(s);
  for (const s of out) {
    const key = `nogame=${s.nogame} start=${s.sn} vege=${s.vege} played=${s.played} breakdown=${s.bn} live=${s.live}`;
    // I1: in a live round, for a running match it must not claim that it is over
    if (s.live && !s.nogame && s.state === 'fut' && /Lejátszotta|véget ért/.test(s.message))
      violate('I1 — says a running match is over', key + '  ->  ' + s.message);
    // I2: a future or unscheduled kick-off = not started yet
    if (!s.nogame && (s.sn === 'future' || s.sn === 'midnightFut') && !/még nem kezdődött/.test(s.message))
      violate('I2 — for a future/unscheduled kick-off it does not say not started yet', key + '  ->  ' + s.message);
    // I2b: an EXPIRED midnight placeholder is no longer a kick-off time - it
    // must not promise a kick-off, because the date is in the past
    if (!s.nogame && s.sn === 'midnightPast' && !/elmaradt/.test(s.message))
      violate('I2b — promises a kick-off for an expired placeholder', key + '  ->  ' + s.message);
    // I3: in a closed round we cannot claim it is in progress
    if (!s.live && /A meccs zajlik/.test(s.message))
      violate('I3 — says in progress in a closed round', key + '  ->  ' + s.message);
    // I4: no match -> it always says that the club has/had no match
    // (present tense in a live round, past tense in a closed one)
    if (s.nogame && !/nem játszik|nem volt meccse/.test(s.message))
      violate('I4 — no match, yet it writes something else', key + '  ->  ' + s.message);
    // I5: the row's dash and the message must not disagree. "No data" is
    // every message that does NOT claim the player's score is final.
    const noDataByMessage = /nem játszik|nem volt meccse|még nem kezdődött|elmaradt|A meccs zajlik|nincs rögzített esemény|feldolgozása még tart/.test(s.message);
    if (s.dash !== noDataByMessage) {
      // ACCEPTED EXCEPTION (N3): the match is over, but MLSZ has not put in
      // the points yet -> the row shows 0, the breakdown tells the truth. The
      // row cannot know whether the breakdown has arrived yet, and finding
      // out would take a fetch per player. Any OTHER mismatch is an error.
      // ACCEPTED: the row shows the stored 0, while the message says there is
      // no data about the event itself. They speak about two different
      // things, and the row's number is the correct value in this case too.
      const n3 = !s.dash && !s.nogame &&
                 /nincs rögzített esemény|feldolgozása még tart/.test(s.message);
      if (!n3) violate('I5 — the dash and the message contradict each other', key + '  ->  ' +
        (s.dash ? 'DASH' : 'number') + ' / ' + s.message);
      else (violations['(accepted N3)'] = violations['(accepted N3)'] || []).push(key);
    }
  }

  const names = Object.keys(violations);
  const real = names.filter(n => n[0] !== '(');
  if (!real.length) console.log('\nEvery invariant holds'
    + (violations['(accepted N3)'] ? ' (apart from the accepted N3 exception: '
       + violations['(accepted N3)'].length + ' cases).' : '.'));
  for (const n of real) {
    const l = violations[n];
    console.log('\n### ' + n + '  (' + l.length + ' cases)');
    // only the distinct outputs are shown, to keep it readable
    const seen = new Set();
    for (const x of l) {
      const v = x.split('->')[1];
      if (seen.has(v)) continue;
      seen.add(v);
      console.log('   ' + x);
    }
  }

  // ---- overview table: what comes out in a live round ----
  console.log('\n=== LIVE round, no points, breakdown=empty ===');
  out.filter(s => s.live && !s.nogame && s.bn === 'empty')
    .forEach(s => console.log(`  start=${s.sn.padEnd(8)} vege=${String(s.vege).padEnd(5)} played=${s.played.padEnd(9)} `
      + `[${s.state.padEnd(10)}] ${s.dash ? '–' : '0'}  ${s.message}`));

  await br.close();
  process.exit(real.length ? 1 : 0);
})();
