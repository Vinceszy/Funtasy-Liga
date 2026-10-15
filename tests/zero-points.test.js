const { BASE, check, section, failures, launch, finish, rewriteJson } = require('./common');
// Test of the four "0 points" states and of the clickability hint, on both sites.
const REPO = require('path').join(__dirname, '..');

const cfg = n => ({ competition_stat_config: { name: n } });
// cp 101/102: not a single row (no statistics yet)
// cp 103: there are rows, but 0 minutes -> did not come on
// cp 104: there are rows, 90 minutes, but none is worth points
// cp 105: there is a row worth points -> a normal table
const BREAKDOWN = {
  101: [], 102: [],
  103: [{ value: 0, points: 0, ...cfg('Játszott perc') }, { value: 0, points: 0, ...cfg('Gólok') }],
  104: [{ value: 90, points: 0, ...cfg('Játszott perc') }, { value: 0, points: 0, ...cfg('Gólok') }],
  105: [{ value: 1, points: 3, ...cfg('Győzelem') }, { value: 90, points: 2, ...cfg('Percek a pályán (több, mint 60 perc)') },
        { value: 90, points: 0, ...cfg('Játszott perc') }],
};

// The panel text WITHOUT THE MATCH HEADER: this test is about the messages,
// the header (score + match clock) is measured by
// breakdown-match-header.test.js. That way the match can stay strict
// (startsWith) instead of weakening to "contains".
const panelText = async page => {
  await page.waitForFunction(() => {
    const p = document.querySelector('.accpanel');
    return p && !p.textContent.includes('betöltése');
  }, null, { timeout: 15000 });
  return page.evaluate(() => {
    const p = document.querySelector('.accpanel').cloneNode(true);
    p.querySelectorAll('.bontasmeccs').forEach(x => x.remove());
    document.body.appendChild(p);
    const t = p.innerText.trim();
    p.remove();
    return t;
  });
};
const expectStart = (label, got, expected) =>
  check(got.startsWith(expected), label + ' -> ' + JSON.stringify(got.slice(0, 70)));

(async () => {
  const browser = await launch();
  // Only the page's JS errors are collected here; EVERY assertion goes through
  // the shared check(), otherwise the runner sees a failed test as green too
  // (that is what happened).
  const pageErrors = [];

  // ---------------- NB1 ----------------
  const page = await browser.newPage();
  page.on('pageerror', e => pageErrors.push('NB1 pageerror: ' + e.message));
  await page.route('**://fantasy-api.mlsz.hu/**', route => {
    const u = route.request().url();
    if (u.includes('game-player-stats')) {
      const cp = +(u.match(/competition_player_id%5D=(\d+)/) || [])[1];
      return route.fulfill({ json: { data: BREAKDOWN[cp] || [] } });
    }
    if (u.includes('user-team-players-history')) return route.fulfill({ json: { data: [] } });
    if (u.includes('rankings')){
      const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
      return route.fulfill({ json: { data: [{ user_team: { user: { id: 5000, username: uname } }, summary_statistics: {}, rounds: [] }] } });
    }
    return route.fulfill({ status: 404, json: {} });
  });
  await page.route('**corsproxy.io/**', r => r.abort());
  await page.route('**allorigins**', r => r.abort());
  // A PRECONDITION the test sets up itself: the round shown must be LIVE.
  // Without it the real results.json decides, and as soon as the collector
  // closes the round, the test would measure the "in progress" states in a
  // closed round - where, however, "the match is over, the points are being
  // processed" is the correct answer.
  const squadsR = require(REPO + '/squads.json').round;
  await rewriteJson(page, '**/results.json*', j => Object.assign(j, { provisional: [squadsR] }));
  // The fixture stores absolute times, which go stale in the meantime (a
  // match "not started yet" is already played by tomorrow). So the kick-offs
  // are set RELATIVE TO NOW, otherwise the test would measure something
  // different every day.
  // The test sets up ITS OWN states instead of relying on the momentary
  // content of the real data: the first manager's squad is replaced by
  // players in precisely defined states. That way the test measures the same
  // thing even if the state of the season changes meanwhile.
  // A kick-off whose text reads T00:00 is the NB1 "time not set yet" marker
  // (midnightPlaceholder), so a relative time landing in the 00:00 minute is
  // moved two minutes earlier - otherwise the test fails for one minute a day.
  const hours = h => {
    let t = Date.now() + h * 3600000;
    if (new Date(t).toISOString().slice(11, 16) === '00:00') t -= 120000;
    return new Date(t).toISOString();
  };
  const PLAYER = (name, id, rest) => Object.assign({
    name: name, team: 'MTK', pos: 'CS', u21: false, hun: true, price: 5,
    cap: false, sub: false, week: 0, total: 0, id: id }, rest);
  const TEST_SQUAD = [
    // name,                      cp id (for the breakdown mock), state
    PLAYER('Meg Nem Kezdodott', 101, { played: false, start: hours(3) }),
    PLAYER('Eppen Fut',         102, { played: false, start: hours(-0.5) }),
    PLAYER('Nem Lepett Palyara',103, { played: true,  start: hours(-4), vege: true }),
    PLAYER('Lejatszotta Nullat',104, { played: true,  start: hours(-4), vege: true }),
    PLAYER('Pontot Szerzett',   105, { played: true,  start: hours(-4), vege: true, week: 5 }),
    PLAYER('Nincs Meccse',      106, { played: false, start: null, nogame: true }),
    // Kick-off not yet fixed: MLSZ writes midnight while the time is not known
    PLAYER('Ejfeli Placeholder',107, { played: false, start: '2026-12-24T00:00:00+01:00' }),
    // The case of THE EXCLUDED BUG: MLSZ flips is_played to true already
    // DURING the match. Even then we must not write "played it".
    PLAYER('Futó Meccsű Tesztjátékos', 104, { played: true, start: hours(-0.5), sub: true }),
  ];
  await page.route('**/squads.json*', async route => {
    const j = await (await route.fetch()).json();
    j.squads[Object.keys(j.squads)[0]] = TEST_SQUAD;
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(j) });
  });
  await page.goto(BASE + 'nb1/');
  await page.waitForSelector('#table tr');
  await page.click('[data-member="Katyul"]');
  await page.waitForSelector('.plr[data-acc]');

  console.log('--- NB1 ---');
  check(await page.locator('.acchint').count() === 1, 'hint line');
  check((await page.locator('.plr[data-acc]').count()) === (await page.locator('.plr[data-acc] .accarr').count()),
     'arrow on every row');

  const clickRow = async name => {
    const row = page.locator('.plr', { hasText: name }).first();
    await row.click();
    return panelText(page);
  };
  expectStart('not started yet   ', await clickRow('Meg Nem Kezdodott'), 'A meccs még nem kezdődött el — kezdés:');
  check(await page.locator('.plr.open .accarr').count() === 1, 'open row is marked');
  expectStart('in progress       ', await clickRow('Eppen Fut'), 'A meccs zajlik');
  expectStart('did not come on   ', await clickRow('Nem Lepett Palyara'), 'Nem lépett pályára');
  // For someone who played the match without an event worth points, the
  // "Játszott perc" row stands (it says more than the old text message) - but
  // ONLY for a finished match: on a running match the state gate's message
  // comes (see below).
  const played = await clickRow('Lejatszotta Nullat');
  check(/Játszott perc\t90/.test(played) && !/Lejátszotta a meccset/.test(played),
     'played it, 0 -> the Játszott perc row stands, not a message: ' + JSON.stringify(played.slice(0, 60)));
  expectStart('no match          ', await clickRow('Nincs Meccse'), 'Ebben a fordulóban nem játszik');
  // Regression test of the reported bug: is_played=true, but the match is
  // still running. During the match a dash stands in place of 0 (MLSZ does
  // not give points yet), but for someone who has already scored points the
  // number is shown.
  const runningPts = await page.locator('.plr', { hasText: 'Futó Meccsű' }).first()
    .locator('.pts').innerText();
  const runningTitle = await page.locator('.plr', { hasText: 'Futó Meccsű' }).first()
    .locator('.pts').getAttribute('title');
  check(runningPts.trim() === '–', 'running match, 0 points -> dash (' + JSON.stringify(runningPts.trim()) + ')');
  check(/meccs zajlik/.test(runningTitle || ''), 'the dash is explained: ' + JSON.stringify(runningTitle));
  const finishedPts = await page.locator('.plr', { hasText: 'Lejatszotta Nullat' }).first()
    .locator('.pts').innerText();
  check(finishedPts.trim() !== '–', 'finished match, 0 points -> the number stays (' + JSON.stringify(finishedPts.trim()) + ')');
  const runningText = await clickRow('Futó Meccsű');   // clicking again would close the panel
  expectStart('running, is_played', runningText, 'A meccs zajlik');
  check(/a pontok csak a meccs végén kerülnek be/.test(runningText),
     'NB1: "zajlik" does not promise live points');
  expectStart('midnight = no time ', await clickRow('Ejfeli Placeholder'), 'A meccs még nem kezdődött el — kezdés: dec. 24. (időpont még nincs kitűzve)');
  const dashes = await page.$$eval('.plr', ns => ns.filter(n => n.dataset.ng === '1')
    .map(n => (n.querySelector('.pts')||{}).textContent));
  check(dashes.length === 1 && dashes[0] === '–', 'no match -> dash: ' + JSON.stringify(dashes));
  const t = await clickRow('Pontot Szerzett');
  check(/Győzelem/.test(t) && /Percek a pályán/.test(t),
     'breakdown worth points -> ' + JSON.stringify(t.replace(/\n/g, ' | ').slice(0, 80)));
  check(/ESEMÉNY\tÉRTÉK\tPONT\nJátszott perc\t90/.test(t),
     'Játszott perc is the first row in a breakdown worth points too');

  // ---------------- PL ----------------
  const pl = require(REPO + '/draft_players.json');
  const hist = require(REPO + '/draft_history.json');
  const team = Object.keys(hist.rounds['1'])[0];
  const elements = hist.rounds['1'][team].map(x => x.e);
  const shortToId = {}; Object.entries(pl.teams).forEach(([id, r]) => shortToId[r] = +id);
  const club = e => pl.players[String(e)].t;
  // four test players for four states - from SEPARATE clubs, because the
  // state is tied to the club (every player of a club is in the same match)
  const seen = new Set(), chosen = [];
  for (const e of elements){ const k = club(e); if (!seen.has(k)){ seen.add(k); chosen.push(e); } }
  const [A, B, C, D] = chosen;
  const elems = {};
  elements.forEach(e => { elems[e] = { stats: { total_points: 0, minutes: 0 },
    explain: [[[{ name: 'Minutes played', points: 0, value: 0, stat: 'minutes' }], 1]] }; });
  elems[D] = { stats: { total_points: 0, minutes: 90 },
    explain: [[[{ name: 'Minutes played', points: 0, value: 90, stat: 'minutes' }], 1]] };
  const now = Date.now();
  // The "id" may NOT be left out: the page keeps the state per match
  // (LIVE_MATCHES), so without an id all three would be written to the same key,
  // and the mock would silently merge into a single match.
  const fixtures = [
    { id: 1, started: false, finished: false, kickoff_time: new Date(now + 20 * 3600e3).toISOString(), team_h: shortToId[club(A)], team_a: 0 },
    { id: 2, started: true,  finished: false, kickoff_time: new Date(now - 3600e3).toISOString(),      team_h: shortToId[club(B)], team_a: 0 },
    { id: 3, started: true,  finished: false, finished_provisional: true, kickoff_time: new Date(now - 7200e3).toISOString(),      team_h: shortToId[club(C)], team_a: shortToId[club(D)] },
  ];
  const page2 = await browser.newPage();
  page2.on('pageerror', e => pageErrors.push('PL pageerror: ' + e.message));
  // The daily points close comes from CLASSIC FPL (fantasy.premierleague.com),
  // so catching the draft host is not enough.
  await page2.route('**://*.premierleague.com/**', route => {
    const u = route.request().url();
    if (u.includes('event-status')) return route.fulfill({ json: { status: [] } });
    // the requests get a cache-buster parameter, so the ending cannot be
    // matched ("/game?fpl_=..." instead of "/game")
    if (/\/game(\?|$)/.test(u)) return route.fulfill({ json: { current_event: 1, current_event_finished: false } });
    if (u.includes('/event/1/live')) return route.fulfill({ json: { elements: elems } });
    if (u.includes('/event/1/fixtures')) return route.fulfill({ json: fixtures });
    return route.fulfill({ status: 404, json: {} });
  });
  await page2.goto(BASE + 'pl/');
  await page2.waitForSelector('#table tr');
  // We do NOT wait for the status bar text. Two different messages contain
  // the word "Élő" - the START of the fetch ("Élő állás lekérése…") and its
  // END ("Élő állás — 1. forduló · frissítve …") -, so watching for the
  // substring let us through during the fetch as well. Whoever clicked then
  // got the "current squad" branch in the squad view (it has no data-acc),
  // and the test failed with a misleading message - in measurements, every
  // second run. So we wait for what the view DEPENDS ON: the current round
  // is set, and the live points have arrived.
  await page2.waitForFunction(() => typeof LIVEGW !== 'undefined' && LIVEGW
                                    && Object.keys(LIVEPTS).length > 0);
  await page2.click(`[data-team="${team}"]`);
  await page2.waitForSelector('.plr[data-acc]');

  console.log('--- PL ---');
  check(await page2.locator('.acchint').count() === 1, 'hint line');
  check((await page2.locator('.plr[data-acc]').count()) === (await page2.locator('.plr[data-acc] .accarr').count()),
     'arrow on every row');
  const clickRow2 = async e => {
    const row = page2.locator(`.plr[data-e="${e}"]`).first();
    await row.click();
    return panelText(page2);
  };
  expectStart('not started yet   ', await clickRow2(A), 'A meccs még nem kezdődött el — kezdés:');
  expectStart('in progress       ', await clickRow2(B), 'A meccs zajlik');
  expectStart('did not come on   ', await clickRow2(C), 'Nem lépett pályára');
  expectStart('played it, 0      ', await clickRow2(D), 'Lejátszotta a meccset');
  const [, , , , E] = chosen;   // fifth club: no match in the round
  if (E){
    expectStart('PL empty round    ', await clickRow2(E), 'Ebben a fordulóban nem játszik');
    const j = (await page2.locator(`.plr[data-e="${E}"] .pts`).textContent()).trim();
    check(j === '–', 'PL empty round -> dash: ' + JSON.stringify(j));
  } else console.log('(no fifth club for the test squad)');
  // a dash only for the players of a match not yet started
  const markA = (await page2.locator(`.plr[data-e="${A}"] .pts`).textContent()).trim();
  const markD = (await page2.locator(`.plr[data-e="${D}"] .pts`).textContent()).trim();
  check(markA === '–' && markD === '0', `dash/0: not started="${markA}" played="${markD}"`);

  check(pageErrors.length === 0, 'no JS error on the pages: ' + JSON.stringify(pageErrors));
  await finish(browser);
})();
