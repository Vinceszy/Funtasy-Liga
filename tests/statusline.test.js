const { BASE, check, launch, finish, rewriteJson } = require('./common');
// THE NB1 IDLE STATUS LINE.
//
// It used to say "Naprakesz · ellenorizve <now>" (up to date · checked
// <now>): the time shown was that of the FETCH, not of the data. During the
// international break this stood on the page for three weeks, and one could
// not tell whether the stored data was old or simply nothing had happened.
// The line now shows the last closed round and when the stored data last
// changed.
//
// The test sets up its own state (no provisional round, the MLSZ gives no
// points at all), it does not build on the current content of the real data.
const STORED = '2026-08-30T10:00:00Z';

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 800 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  let last = null;
  await rewriteJson(p, '**/results.json*', j => {
    j.provisional = [];
    j.updated = STORED;
    const played = Object.keys(j.schedule || {}).map(Number)
      .filter(r => (j.schedule[r] || []).some(m => m[2] != null));
    last = Math.max(...played);
    return j;
  });
  await p.route('**://fantasy-api.mlsz.hu/**', route => {
    const u = route.request().url();
    if (u.includes('rankings')) {
      const uname = decodeURIComponent((u.match(/filter%5Bsearch%5D=([^&]*)/) || [])[1] || '');
      return route.fulfill({ json: { data: [{ user_team: { user: { id: 5000, username: uname },
        round_statistics: [] }, summary_statistics: {}, rounds: [] }] } });
    }
    return route.fulfill({ json: { data: [] } });
  });
  await p.route('**corsproxy.io/**', r => r.abort());
  await p.route('**allorigins**', r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => /ellenőrizve|hiba|nem elérhető/.test(
    document.getElementById('status').textContent), null, { timeout: 30000 });
  const text = await p.evaluate(() => document.getElementById('status').textContent.trim());
  console.log('   status: ' + JSON.stringify(text));

  check(/^Naprakész/.test(text), 'at rest it says "Naprakész"');
  check(text.includes('utolsó lezárt: ' + last + '. forduló'),
     'it shows the last closed round (' + last + '.)');
  check(/rögzítve: aug\. 30/.test(text),
     'it shows the last change of the STORED data, not the time of the fetch');
  check(/ellenőrizve \d{2}:\d{2}$/.test(text), 'and when it checked');
  check(!perr.length, 'no JS error: ' + JSON.stringify(perr));
  await finish(br);
})();
