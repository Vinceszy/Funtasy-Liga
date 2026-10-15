const { BASE, check, section, failures, launch, finish } = require('./common');
// Opening a match must download the PER-ROUND squad file, not the whole
// history - and if the per-round file is missing, it must fall back on it.

(async () => {
  const br = await launch();

  // ---------- 1. normal case: per-round file ----------
  section('Opening a match: which file does it download?');
  let p = await br.newPage();
  const requested = [];
  p.on('request', r => {
    const u = r.url();
    if (/keretek\/\d+\.json/.test(u)) requested.push('keretek/' + u.match(/keretek\/(\d+)\.json/)[1]);
    if (/squad_history\.json/.test(u)) requested.push('squad_history');
  });
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr td', { timeout: 30000 });
  await p.evaluate(() => showMatchRound('Bazsa', 'Katyul', 1));
  await p.waitForSelector('.sqcol .plr', { timeout: 20000 });
  const players = await p.locator('.sqcol .plr').count();
  console.log('   files requested: ' + JSON.stringify(requested) + ' | player rows: ' + players);
  check(requested.includes('keretek/1'), 'it requests round 1\'s own file');
  check(!requested.includes('squad_history'), 'it does NOT download the whole history');
  check(players >= 20, 'the squads do appear (' + players + ' rows)');
  await p.close();

  // ---------- 2. fallback: no per-round file ----------
  section('If the per-round file is missing, the whole history is the fallback');
  p = await br.newPage();
  const requested2 = [];
  p.on('request', r => { if (/squad_history\.json/.test(r.url())) requested2.push('squad_history'); });
  await p.route('**/keretek/*.json*', r => r.fulfill({ status: 404, body: '' }));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**']) await p.route(m, r => r.abort());
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr td', { timeout: 30000 });
  await p.evaluate(() => showMatchRound('Bazsa', 'Katyul', 1));
  await p.waitForSelector('.sqcol .plr', { timeout: 20000 });
  const players2 = await p.locator('.sqcol .plr').count();
  console.log('   fallback request: ' + JSON.stringify(requested2) + ' | player rows: ' + players2);
  check(requested2.includes('squad_history'), 'it falls back on the whole history');
  check(players2 >= 20, 'the squads appear this way too (' + players2 + ' rows)');
  await p.close();

  // ---------- 3. the two sources give the same ----------
  section('The per-round files and the whole history match');
  const fs = require('fs'), path = require('path');
  const full = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'squad_history.json'), 'utf8')).rounds;
  let mismatches = 0;
  for (const r of Object.keys(full)) {
    const f = path.join(__dirname, '..', 'keretek', r + '.json');
    if (!fs.existsSync(f)) { mismatches++; console.log('   missing: keretek/' + r + '.json'); continue; }
    const one = JSON.parse(fs.readFileSync(f, 'utf8')).squads;
    if (JSON.stringify(one) !== JSON.stringify(full[r])) { mismatches++; console.log('   differs: ' + r); }
  }
  check(mismatches === 0, 'the files of all ' + Object.keys(full).length + ' rounds match the history');

  await finish(br);
})();
