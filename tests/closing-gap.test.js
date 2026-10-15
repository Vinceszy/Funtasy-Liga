const { BASE, check, launch, finish, rewriteJson } = require('./common');
// THE GAP BETWEEN CLOSING AND COLLECTION (PL).
//
// The FPL closes the round at "lockdown" (measured: everything flips between
// 08:03 and 08:23 UTC), but our collector runs every 3 hours. Between the
// two moments the game endpoint already says current_event_finished, but the
// stored draft.json does not yet contain the round's result.
//
// This gap used to show "Naprakesz · ellenorizve <now>": the time shown was
// that of the FETCH, not of the data - so it claimed to be up to date
// exactly when it provably was not. Now it says what is missing.
//
// The test STATES both states (it does not rely on the real data), because
// the collector may bring in the result at any time.
const GW = 1;

async function statusText(br, hasResult){
  const p = await br.newPage({ viewport: { width: 900, height: 800 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  // the round has already closed according to the FPL
  await p.route('**premierleague.com/**', route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/\/api\/game/.test(u)) return json({ current_event: GW, current_event_finished: true });
    if (/event-status/.test(u)) return json({ status: [] });
    return json({});
  });
  // the stored data HAS or HAS NO result for this round
  await rewriteJson(p, '**/draft.json*', j => {
    const s = (j.schedule && j.schedule[GW]) || [];
    j.schedule[GW] = s.map(m => hasResult ? [m[0], m[1], 20, 30] : [m[0], m[1], null, null]);
    j.updated = '2026-08-25T05:47:00Z';
    return j;
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => {
    const el = document.getElementById('status');
    return el && el.textContent && !/lekérése/.test(el.textContent);
  }, null, { timeout: 20000 });
  const st = await p.evaluate(() => ({
    text: document.getElementById('status').textContent.trim(),
    cls: document.getElementById('status').className,
  }));
  await p.close();
  return { ...st, perr };
}

(async () => {
  const br = await launch();

  const missing = await statusText(br, false);
  console.log('   without result: ' + JSON.stringify(missing.text) + '  [' + missing.cls + ']');
  check(!/Naprakész/.test(missing.text),
     'closed round + missing result: does NOT say "Naprakész"');
  check(/lezárult/.test(missing.text) && /adatfrissítéssel/.test(missing.text),
     'it says what is missing and when it will be filled in');
  check(/tárolt állás/.test(missing.text) && /aug\./.test(missing.text),
     'it shows the time of the STORED score, not of the fetch: ' + JSON.stringify(missing.text));
  check(missing.cls === 'varakozik',
     'it gets its own mark (not "ok", not an error): ' + JSON.stringify(missing.cls));

  const present = await statusText(br, true);
  console.log('   with result:    ' + JSON.stringify(present.text) + '  [' + present.cls + ']');
  check(/Naprakész/.test(present.text) && present.cls === 'ok',
     'once the result is in the stored data, "Naprakész" again');
  check(new RegExp('utolsó lezárt: ' + GW + '\\. forduló \\(rögzítve: ').test(present.text),
     'the idle line states the last closed round and when it was recorded: '
     + JSON.stringify(present.text));

  check(!missing.perr.length && !present.perr.length,
     'no JS error: ' + JSON.stringify([...missing.perr, ...present.perr]));
  await finish(br);
})();
