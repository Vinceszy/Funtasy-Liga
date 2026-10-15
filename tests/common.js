// Shared part of the browser tests: launch, assertions, data rewriting.
// Every test runs on the REAL repository data (there are no fixture copies
// that would go stale); where a special state is needed, the test produces it
// on the fly.
const PW_PATH = process.env.PLAYWRIGHT_MODULE || '/tmp/node_modules/playwright';
const CHROME  = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const BASE    = process.env.TEST_BASE || 'http://127.0.0.1:8910/';

let chromium;
try { chromium = require(PW_PATH).chromium; }
catch (e) {
  console.error('Playwright not found (' + PW_PATH + ').');
  console.error('Set the PLAYWRIGHT_MODULE environment variable, or skip the browser tests.');
  process.exit(2);
}

const failures = [];
/** One assertion. True -> OK, false -> FAIL (and exit code 1 at the end of the run). */
const check = (cond, label) => {
  console.log((cond ? 'OK   ' : 'FAIL ') + label);
  if (!cond) failures.push(label);
  return !!cond;
};
const section = t => console.log('\n--- ' + t + ' ---');
const launch = () => chromium.launch({ executablePath: CHROME });
const finish = async br => { if (br) await br.close(); process.exit(failures.length ? 1 : 0); };

/** Rewrites JSON coming from the repository on the fly (without fixture files).

    The file is read FROM DISK, not through the local test server: under the
    load of the full suite the server sometimes drops the connection, and then
    the test's PRECONDITION was lost - the test failed at a different assertion
    each time, with a misleading message (the "uzenetek" test failed at three
    different places in three runs). A retrying variant with route.fetch was
    not enough either. The network path remains only for a request that does
    not point to a repository file. */
const fs = require('fs');
const ROOT = require('path').join(__dirname, '..');
async function rewriteJson(page, pattern, transform) {
  await page.route(pattern, async route => {
    let j = null;
    try {
      const urlPath = decodeURIComponent(new URL(route.request().url()).pathname);
      j = JSON.parse(fs.readFileSync(require('path').join(ROOT, '.' + urlPath), 'utf8'));
    } catch (e) { /* not a repository file or not JSON - the network path follows */ }
    if (j == null) {
      const resp = await route.fetch();
      try { j = await resp.json(); } catch (e) { return route.fulfill({ response: resp }); }
    }
    route.fulfill({ status: 200, contentType: 'application/json',
                    body: JSON.stringify(transform(j) || j) });
  });
}

/** Cuts off the live APIs: the page works from the stored data only.

    Google Fonts belongs here too - not because it is an "API", but so that
    the tests do not depend on whether the outside network is reachable. (This
    did NOT improve the run time noticeably: measured, the slowest tests stayed
    the same - they are slow for other reasons. The benefit is independence.)
    The font test puts its own route on them, registered LATER (the later one
    wins), so there the behaviour that test measures still applies. */
async function blockApis(page) {
  // the list follows the fetcher's (funtasy.js) PATH LIST: every proxy host
  // must be here too, otherwise a test would leak to the real network
  for (const m of ['**mlsz.hu/**', '**premierleague.com/**',
                   '**corsproxy.io/**', '**allorigins**',
                   '**proxy.cors.sh/**', '**cors.lol/**', '**workers.dev/**',
                   '**fonts.googleapis.com/**', '**fonts.gstatic.com/**'])
    await page.route(m, r => r.abort());
}

/** Cuts off the STORED breakdown: the page falls back to the LIVE fetch.

    The breakdown of a closed round comes from the repository
    (bontasok/<r>.json), and that is the primary path - which is exactly why
    the LIVE path (proxy chain, error message, the profile's points filled in
    row by row) can no longer be measured by cutting off MLSZ alone: the page
    would never get that far. This imitates the missing file - which is also a
    real case: a round from before stored breakdowns existed, or a player who
    is no longer in the current 385-player roster (there are five such).

    A test that measures the STORED path (taroltbontas.teszt.js) does not call this. */
async function blockStoredBreakdowns(page) {
  // The TRAILING * MUST NOT BE DROPPED: the page requests with a cache buster
  // (bontasok/4.json?t=...), and Playwright matches the glob against the FULL
  // URL - with "*.json" the query-string ending does not match, and the test
  // SILENTLY gets the real file. The same pattern applies on every data path.
  await page.route('**/bontasok/*.json*', r => r.fulfill({ status: 404, body: '' }));
}

module.exports = { BASE, chromium, check, section, failures, launch, finish,
                   rewriteJson, blockApis, blockStoredBreakdowns };
