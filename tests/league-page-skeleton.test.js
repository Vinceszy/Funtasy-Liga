const { BASE, check, section, launch, finish, blockApis } = require('./common');
const fs = require('fs'), path = require('path');
// THE SKELETON OF THE TWO LEAGUE PAGES IS THE SAME.
//
// WHY IT EXISTS: the two pages are separate files (no build, no template),
// so the shared part is written out twice by hand - and it can drift apart.
// It did: the closing-changes panel stood on one page with a different
// title, in a different column and with a different layout than on the
// other. What has to be rewritten in two places at once has to be guarded
// by a machine.
//
// What it does NOT check: the content of the panels. The data of the two
// leagues differs (draft vs salary cap), but the FRAME has to be the same.
const PAGES = ['index.html', 'nb1/index.html', 'pl/index.html', 'valtozasok/index.html'];
const ROOT = path.join(__dirname, '..');

// For comparing the <head>: the relative path prefix and the title differ
// per league, everything else has to be identical.
const headNorm = h => h.slice(0, h.indexOf('</head>'))
  .replace(/<title>[\s\S]*?<\/title>/, '<title/>')
  .replace(/\.\.\//g, '')
  .replace(/\s+/g, ' ').trim();

(async () => {
  const br = await launch();

  section('The <head> is the same on every page');
  const heads = PAGES.map(f => [f, headNorm(fs.readFileSync(path.join(ROOT, f), 'utf8'))]);
  const base = heads[0][1];
  for (const [f, h] of heads.slice(1)){
    if (h === base) { check(true, f + ': identical to the home page'); continue; }
    // where does it first differ?
    let i = 0; while (i < h.length && h[i] === base[i]) i++;
    check(false, f + ': the <head> differs — "…' + h.slice(Math.max(0, i - 40), i + 40)
       + '" instead of "…' + base.slice(Math.max(0, i - 40), i + 40) + '"');
  }

  section('Without JavaScript it says what is missing');
  for (const f of PAGES){
    const h = fs.readFileSync(path.join(ROOT, f), 'utf8');
    check(/<noscript><div class="note nojs">/.test(h) && /JavaScript<\/b> kell/.test(h),
       f + ': there is a <noscript> warning (otherwise only an empty skeleton shows)');
  }

  const page = async (league, w, h) => {
    const p = await br.newPage({ viewport: { width: w, height: h } });
    const err = []; p.on('pageerror', e => err.push(e.message));
    await blockApis(p);
    await p.goto(BASE + league + '/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await p.waitForTimeout(2200);
    return { p, err };
  };

  for (const [w, h, label] of [[1400, 1100, 'DESKTOP'], [390, 844, 'MOBILE']]){
    section(label + ': the panels stand in the same order and column');
    const out = {};
    for (const league of ['nb1', 'pl']){
      const { p, err } = await page(league, w, h);
      out[league] = await p.$$eval('.panel', a => a.filter(x => x.offsetParent !== null).map(x => {
        const c = x.querySelector('h2'), r = x.getBoundingClientRect();
        return { title: (c ? c.childNodes[0].textContent : '(no title)').trim(),
                 column: r.x < 400 ? 'left' : 'right', y: Math.round(r.y) };
      }));
      check(err.length === 0, league + ': no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
      await p.close();
    }
    const order = x => x.map(o => o.title).join(' → ');
    out.nb1.sort((a, b) => a.y - b.y); out.pl.sort((a, b) => a.y - b.y);
    check(order(out.nb1) === order(out.pl),
       label + ': the same panels, in the same order\n     NB1: '
       + order(out.nb1) + '\n     PL : ' + order(out.pl));
    if (label === 'DESKTOP'){
      const cols = x => x.map(o => o.title + '=' + o.column).join(', ');
      check(cols(out.nb1) === cols(out.pl),
         'DESKTOP: every panel in the same column\n     NB1: ' + cols(out.nb1)
         + '\n     PL : ' + cols(out.pl));
    }
  }

  section('The table header is the same (except for the first cell)');
  const head = {};
  for (const league of ['nb1', 'pl']){
    const { p } = await page(league, 1400, 1100);
    head[league] = await p.$$eval('#table tr:first-child th, #table tr:first-child td',
                                  a => a.map(x => x.textContent.trim()));
    await p.close();
  }
  // the first two cells: rank (empty) and the name of the participant
  check(head.nb1[1] !== head.pl[1],
     'the participant column has a different name per league (' + head.nb1[1] + ' / ' + head.pl[1] + ')');
  check(head.nb1.slice(2).join('|') === head.pl.slice(2).join('|'),
     'the headers of the other columns are identical\n     NB1: ' + head.nb1.slice(2).join(' | ')
     + '\n     PL : ' + head.pl.slice(2).join(' | '));

  await finish(br);
})();
