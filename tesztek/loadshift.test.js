const { BASE, jo, cim, inditas, vege, jsonAtir } = require('./kozos');
// THE PAGE MUST NOT JUMP WHILE IT LOADS.
//
// A page that loads in steps moves what the reader is looking at with each
// step: the league bar drawn by script, the status line going from empty to
// one line to two, the table going from a bare header to its rows. On a
// phone each of these pushes everything below it down.
//
// The test loads both league pages at phone width with the data delayed
// (so the empty first paint is long enough to see), samples the position
// of the table panel and of the note under the table every 50 ms, and
// requires them to stay put from the first paint to the end. Live APIs are
// cut: the test is about layout, not about which state the data is in.
const PHONE = { width: 390, height: 844 };
const MAX_SHIFT = 3; // px: sub-pixel rounding and font hinting, nothing more

async function measure(br, path, dataFile) {
  const p = await br.newPage({ viewport: PHONE, deviceScaleFactor: 2 });
  const errors = []; p.on('pageerror', e => errors.push(e.message));
  for (const m of ['**mlsz.hu/**', '**premierleague.com/**', '**corsproxy.io/**',
                   '**allorigins**', '**workers.dev/**', '**fonts.googleapis.com/**',
                   '**fonts.gstatic.com/**'])
    await p.route(m, r => r.abort());
  // Hold the league data back, so the empty first paint lasts long enough.
  await jsonAtir(p, '**/' + dataFile + '*', j => j);
  await p.route('**/' + dataFile + '*', async route => {
    await new Promise(r => setTimeout(r, 700));
    route.fallback();
  });
  // From DOMContentLoaded on: before it the stylesheet may not be applied
  // yet, the browser does not paint, and a measurement there is not a frame
  // anybody sees. Everything the recording showed happens after it.
  await p.goto(BASE + path, { waitUntil: 'domcontentloaded' });
  const samples = [];
  const end = Date.now() + 3000;
  while (Date.now() < end) {
    const s = await p.evaluate(() => {
      const panel = document.querySelector('.grid .panel');
      const note = panel && panel.querySelector('.note');
      const rows = document.querySelectorAll('#table tr').length;
      return panel && note ? { panel: panel.getBoundingClientRect().top,
                               note: note.getBoundingClientRect().top, rows } : null;
    }).catch(() => null);
    if (s) samples.push(s);
    await p.waitForTimeout(50);
  }
  await p.close();
  return { samples, errors };
}

(async () => {
  const br = await inditas();
  for (const [name, path, dataFile] of [['PL', 'pl/', 'draft.json'], ['NB1', 'nb1/', 'results.json']]) {
    cim(name + ': the page holds still while it loads');
    const { samples, errors } = await measure(br, path, dataFile);
    jo(samples.length > 20, 'enough samples (' + samples.length + ')');
    const range = k => Math.max(...samples.map(s => s[k])) - Math.min(...samples.map(s => s[k]));
    const filled = samples.filter(s => s.rows > 1);
    jo(filled.length > 0, 'the table filled during the window');
    jo(range('panel') <= MAX_SHIFT,
       'the table panel stays put (moved ' + range('panel').toFixed(1) + ' px)');
    jo(range('note') <= MAX_SHIFT,
       'the note under the table stays put (moved ' + range('note').toFixed(1) + ' px)');
    jo(!errors.length, 'no JS error: ' + JSON.stringify(errors));
  }
  await vege(br);
})();
