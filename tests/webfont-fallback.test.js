const { BASE, check, section, launch, finish, blockApis } = require('./common');
const fs = require('fs'), path = require('path');
// The font stylesheet must NOT stop the page from appearing.
//
// BECAUSE WE MEASURED IT: with a plain <link rel="stylesheet">, when
// fonts.googleapis.com does not answer, DOMContentLoaded takes 12 640 ms
// instead of 57 ms - until then there is NOTHING on the page. On a phone, on
// a weak network, that is exactly the situation in which one wants to check
// the score. The media="print" + onload trick makes the stylesheet
// asynchronous; because of `display=swap` the first paint happens with the
// fallback font anyway.
//
// The other half: in the CSS EVERY font family must have a fallback.
// Without it the browser default (serif Times) would take its place, with a
// different character width - the table would jump when the web font arrives.
const PAGES = ['', 'nb1/', 'pl/', 'valtozasok/'];
const ROOT = path.join(__dirname, '..');

(async () => {
  const br = await launch();

  section('The shape of the link on every page');
  for (const o of PAGES){
    const h = fs.readFileSync(path.join(ROOT, o, 'index.html'), 'utf8');
    const name = o || '(home page)';
    const sheets = h.match(/<link[^>]*fonts\.googleapis\.com[^>]*>/g) || [];
    const blocking = sheets.filter(x => /rel="stylesheet"/.test(x) && !/media="print"/.test(x));
    // the stylesheet inside <noscript> MAY block: there is no onload there to switch it back
    const inNoscript = (h.match(/<noscript>[\s\S]*?<\/noscript>/g) || []).join('');
    const real = blocking.filter(x => inNoscript.indexOf(x) < 0);
    check(real.length === 0, name + ': no render-blocking font stylesheet'
       + (real.length ? ' — ' + real[0].slice(0, 80) : ''));
    check(/media="print"/.test(h) && /this\.media='all'/.test(h),
       name + ': the stylesheet is asynchronous (media="print" + onload)');
    check(/<noscript>[\s\S]*fonts\.googleapis[\s\S]*<\/noscript>/.test(h),
       name + ': the font arrives without JavaScript too (noscript branch)');
    check(/preconnect[^>]*fonts\.gstatic\.com/.test(h),
       name + ': preconnect to fonts.gstatic.com (the files come from there)');
  }

  section('Every font family has a fallback');
  const css = fs.readFileSync(path.join(ROOT, 'funtasy.css'), 'utf8');
  const literal = (css.match(/font(-family)?:[^;}]*(Inter|JetBrains|Archivo)[^;}]*/g) || [])
    .filter(x => !/var\(--/.test(x) && !/^--/.test(x));
  check(literal.length === 0,
     'the CSS nowhere writes a font name directly, a variable stands everywhere'
     + (literal.length ? ' — e.g. ' + literal[0] : ''));
  for (const [v, needed] of [['--fo', 'sans-serif'], ['--mono', 'monospace'], ['--cim', 'sans-serif']]){
    const line = (css.match(new RegExp(v + ':[^;}]*')) || [''])[0];
    check(line.indexOf(needed) > 0, v + ' fallback list ends with ' + needed + ' — "' + line.slice(0, 70) + '"');
  }

  section('Font service that does not answer');
  // The request NEVER comes back - this is the worst case (not an error, but waiting)
  const p = await br.newPage();
  const err = []; p.on('pageerror', e => err.push(e.message));
  await blockApis(p);
  for (const m of ['**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await p.route(m, async () => { await new Promise(() => {}); });   // pending forever
  const t0 = Date.now();
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 15000 });
  const elapsed = Date.now() - t0;
  check(elapsed < 8000, 'the table is drawn even if the font does not arrive ('
     + elapsed + ' ms)');
  const font = await p.evaluate(() => getComputedStyle(document.body).fontFamily);
  check(/sans-serif|system-ui/.test(font), 'the fallback font family takes effect — "' + font.slice(0, 50) + '"');
  check((await p.evaluate(() => document.body.innerText)).length > 500,
     'the page content is there, not empty');
  check((await p.evaluate(() => document.documentElement.scrollWidth
                            - document.documentElement.clientWidth)) <= 1,
     'no horizontal overflow with the fallback font either');
  check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
  await p.close();
  await finish(br);
})();
