const { BASE, check, section, failures, launch, finish, blockApis } = require('./common');
const os = require('os');
const path = require('path');
// Checks the dimming of the shared players on desktop and on mobile.

async function openMatch(page) {
  await page.waitForSelector('.score', { timeout: 20000 });
  // we look for a match that has a shared player
  const cells = await page.$$('.score');
  for (const c of cells) {
    await c.click();
    await page.waitForTimeout(700);
    const hasFilter = await page.$('.szurogomb');
    if (!hasFilter) { await page.click('.mclose'); await page.waitForTimeout(200); continue; }
    // switch the filter on, if it is not on yet
    if ((await page.$$('.szakasz')).length === 0) {
      await page.click('.szurogomb');
      await page.waitForTimeout(500);
    }
    const sharedRow = await page.$('.kozosresz .plr[data-acc]:not(.szabalysor)');
    if (sharedRow) return true;
    await page.click('.mclose'); await page.waitForTimeout(200);
  }
  return false;
}

const colour = (h) => h.evaluate(e => getComputedStyle(e).color);

(async () => {
  const b = await launch();

  // ---- desktop ----
  let p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  await p.goto(BASE + 'nb1/', { waitUntil: 'networkidle' });
  const found = await openMatch(p);
  check(found, 'found a match that contains a shared player');
  if (found) {
    const shared = await p.$('.kozosresz .plr[data-acc]:not(.szabalysor) .nm');
    const diff = await p.$('.sqcol > .plr[data-acc] .nm');
    const dim = await p.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--dim').trim());
    const sharedColour = await colour(shared), diffColour = await colour(diff);
    console.log('   shared colour:', sharedColour, '| differing colour:', diffColour, '| --dim:', dim);
    check(sharedColour !== diffColour, 'the shared player\'s name is dimmer than the differing one\'s');
    // the shared points are dim too
    const sharedPts = await colour(await p.$('.kozosresz .plr[data-acc]:not(.szabalysor) .pts'));
    check(sharedPts === sharedColour, 'the shared player\'s points are dim too (' + sharedPts + ')');
    // the totals row is NOT dim
    const totalColour = await colour(await p.$('.kozosresz .osszesito b'));
    check(totalColour !== sharedColour, 'the totals row is not dim (' + totalColour + ')');
    // clickability is kept
    await p.click('.kozosresz .plr[data-acc]:not(.szabalysor)');
    await p.waitForTimeout(900);
    check((await p.$$('.accpanel')).length > 0, 'the dimmed shared row can still be opened');
    await p.screenshot({ path: path.join(os.tmpdir(), 'shared-players-dimmed.png'), fullPage: true });
  }
  await p.close();

  // ---- mobile ----
  p = await b.newPage({ viewport: { width: 390, height: 844 } });
  await p.goto(BASE + 'nb1/', { waitUntil: 'networkidle' });
  const found2 = await openMatch(p);
  if (found2) {
    const mk = await p.$('.mobilkozos .plr[data-acc]:not(.szabalysor) .nm');
    check(!!mk, 'on mobile the shared block is visible');
    if (mk) {
      const shown = await p.$$eval('.mobilkozos', els => els.map(e => getComputedStyle(e).display));
      check(shown[0] === 'block', 'on mobile .mobilkozos is visible (' + shown[0] + ')');
      const hidden = await p.$$eval('.sqcol .kozosresz', els => els.map(e => getComputedStyle(e).display));
      check(hidden.every(d => d === 'none'), 'on mobile the columns have no shared part');
      console.log('   mobile shared colour:', await colour(mk));
    }
    await p.screenshot({ path: path.join(os.tmpdir(), 'shared-players-dimmed-mobile.png'), fullPage: true });
  } else {
    check(false, 'found no shared player on mobile');
  }
  await p.close();
  await b.close();
  process.exit(failures.length ? 1 : 0);
})();
