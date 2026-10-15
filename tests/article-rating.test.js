const { BASE, check, section, launch, finish } = require('./common');
// RATING THE WRITING at the bottom of the article strip.
//
// The point of the feature is not the score but the REASON: that is what
// makes the next text better. So the two lower grades ask for a reason, and
// the two upper ones go through with a single tap - whoever is satisfied
// should not have to work for it.
//
// What it pins:
//  - the bar is only there in an OPENED article (what you did not read, you
//    should not rate);
//  - three or four: one tap, no question, and the data sent is correct;
//  - one or two: the reason panel opens IN PLACE (the article stays visible),
//    and it asks for the viewer's OWN WORDS - there are no ready-made reasons;
//  - "Elkuldom" (send) expects a reason: with an empty text box it does not
//    even offer itself;
//  - the way out ("indokolni nem fogok", I won't give a reason) sends, but
//    WITHOUT a reason - it does not forge one;
//  - the click does not collapse the article;
//  - a device rates an article once, but can re-rate it;
//  - on a failed send what was typed is not lost.
const R = 7, H = 'Bence', V = 'Csendi';
const KEY = 'nb1|7|summary|' + H + '|' + V;

const open = async (p, requests) => {
  await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [H, V, R]);
  await p.waitForSelector('#mBody .artstrip');
  await p.evaluate(() => { document.querySelector('#mBody .artstrip').open = true; });
  await p.waitForSelector('#mBody .artrate');
};

(async () => {
  const br = await launch();
  const errors = [];
  const p = await br.newPage({ viewport: { width: 1000, height: 1000 } });
  p.on('pageerror', e => errors.push(e.message));
  for (const m of ['**mlsz.hu/**', '**corsproxy.io/**', '**allorigins**'])
    await p.route(m, r => r.abort());

  // We do not go out to the Worker: we catch the request and look at WHAT it
  // would have sent. The test sets the answer, so the failing branch can be
  // measured too.
  let requests = [], answer = { status: 200, body: '{"ok":true}' };
  await p.route('**/ertekeles', async route => {
    requests.push({ method: route.request().method(),
                    body: JSON.parse(route.request().postData() || '{}') });
    await route.fulfill({ status: answer.status, contentType: 'application/json',
                          body: answer.body,
                          headers: { 'Access-Control-Allow-Origin': '*' } });
  });
  await p.goto(BASE + 'nb1/');
  await p.waitForSelector('#table tr');
  await p.waitForFunction(() => typeof ARTICLES !== 'undefined' && ARTICLES !== null,
                          null, { timeout: 20000 });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });

  // ---- where the bar is ----
  section('Where the bar is');
  await p.evaluate(([a, b, r]) => showMatchRound(a, b, r), [H, V, R]);
  await p.waitForSelector('#mBody .artstrip');
  check(await p.locator('#mBody .artrate').isVisible() === false,
     'not visible on a collapsed article — what you did not read, you should not rate');
  await p.evaluate(() => { document.querySelector('#mBody .artstrip').open = true; });
  await p.waitForSelector('#mBody .artrate');
  check(await p.locator('#mBody .artrate').isVisible(), 'opened, it is there');
  check(await p.locator('#mBody .artrateg').count() === 4, 'four grades');

  // ---- four: one tap ----
  section('Four: one tap');
  requests = [];
  await p.locator('#mBody .artrateg[data-pont="4"]').click();
  await p.waitForFunction(() => /Köszi/.test(document.querySelector('#mBody .artrate').textContent),
                          null, { timeout: 5000 });
  check(requests.length === 1 && requests[0].method === 'POST', 'one POST went out');
  const t4 = requests[0].body;
  check(t4.pont === 4 && t4.cikk === KEY, 'the score and the article id are correct — '
     + t4.pont + ' / ' + t4.cikk);
  check(/^[a-z0-9]{8,32}$/.test(t4.eszkoz || ''), 'with a device id — ' + t4.eszkoz);
  check((t4.okok || []).length === 0 && !t4.indok, 'we did not ask for a reason');
  check(await p.locator('#mBody .artreason').count() === 0, 'no reason panel opened');
  check(await p.evaluate(() => document.querySelector('#mBody .artstrip').open),
     'the article stayed open — the click did not collapse it');

  // ---- it remembers, but can be re-rated ----
  section('It remembers, but can be re-rated');
  await p.evaluate(() => showMatchRound('Bazsa', 'Ádám', 7));
  await p.waitForSelector('#mBody .plr');
  await open(p);
  check(/Köszi/.test(await p.locator('#mBody .artrate').innerText()),
     'on return it remembers: ' + (await p.locator('#mBody .artrate').innerText()).trim());
  await p.locator('#mBody .artrateagain').click();
  await p.waitForSelector('#mBody .artrateg');
  check(await p.locator('#mBody .artrateg').count() === 4, 'on re-rating the four grades are back');

  // ---- two: the reason panel opens in place ----
  section('Two: asks for a reason in place');
  const beforeY = await p.evaluate(() =>
    document.querySelector('#mBody .artstripbody p').getBoundingClientRect().top);
  requests = [];
  await p.locator('#mBody .artrateg[data-pont="2"]').click();
  await p.waitForSelector('#mBody .artreason');
  check(requests.length === 0, 'nothing sent yet — the reason comes first');
  check(await p.locator('#mBody .artchip').count() === 0,
     'no ready-made reason to choose — we ask for the viewer\'s own words');
  check(await p.locator('#mBody .artreasont').isVisible(), 'free text');
  check(await p.locator('#mBody .artsend').isVisible()
     && await p.locator('#mBody .artskip').isVisible(), 'two buttons: send and way out');
  check(await p.locator('#mBody .artsend').isDisabled(),
     '"Elküldöm" does not offer itself with an empty box');
  check(await p.locator('#mBody .artskip').isEnabled(), 'but the way out is available all along');
  const afterY = await p.evaluate(() =>
    document.querySelector('#mBody .artstripbody p').getBoundingClientRect().top);
  check(Math.abs(afterY - beforeY) < 2,
     'the article text stayed in place — it does not cover what we ask an opinion about');

  // ---- quick choice + text ----
  section('Two: the viewer\'s own words are sent');
  await p.locator('#mBody .artreasont').fill('Nem derült ki belőle, mi döntött.');
  check(await p.locator('#mBody .artsend').isEnabled(),
     'as soon as there is something to send, the button arms');
  await p.locator('#mBody .artsend').click();
  await p.waitForFunction(() => /Köszi/.test(document.querySelector('#mBody .artrate').textContent),
                          null, { timeout: 5000 });
  check(requests.length === 1, 'one POST went out');
  const t2 = requests[0].body;
  check(t2.pont === 2, 'the score is two — ' + t2.pont);
  check(t2.indok === 'Nem derült ki belőle, mi döntött.', 'the typed sentence was sent');
  check(!('okok' in t2), 'no ready-made category is sent with it');

  // ---- the way out: sends, but without a reason ----
  section('The way out sends without a reason — it does not forge one');
  await p.locator('#mBody .artrateagain').click();
  await p.waitForSelector('#mBody .artrateg');
  requests = [];
  await p.locator('#mBody .artrateg[data-pont="1"]').click();
  await p.waitForSelector('#mBody .artreason');
  await p.locator('#mBody .artreasont').fill('Ezt mégsem küldöm el.');
  await p.locator('#mBody .artskip').click();
  await p.waitForFunction(() => /Köszi/.test(document.querySelector('#mBody .artrate').textContent),
                          null, { timeout: 5000 });
  const t1 = requests[0].body;
  check(t1.pont === 1, 'the one was sent — ' + t1.pont);
  check(!t1.indok,
     'but without a reason: what was typed before changing one\'s mind is not sent behind one\'s back — '
     + JSON.stringify({ indok: t1.indok }));

  // ---- failed send: what was typed is not lost ----
  section('On a failed send what was typed is not lost');
  await p.locator('#mBody .artrateagain').click();
  await p.waitForSelector('#mBody .artrateg');
  answer = { status: 500, body: '{"ok":false}' };
  await p.locator('#mBody .artrateg[data-pont="1"]').click();
  await p.waitForSelector('#mBody .artreason');
  await p.locator('#mBody .artreasont').fill('Ez maradjon meg.');
  await p.locator('#mBody .artsend').click();
  await p.waitForFunction(() => /Nem sikerült/.test(
    document.querySelector('#mBody .artreasonq').textContent), null, { timeout: 5000 });
  check(await p.locator('#mBody .artreasont').inputValue() === 'Ez maradjon meg.',
     'the typed text stayed');
  check(await p.locator('#mBody .artsend').isEnabled(), 'and it can be retried');

  errors.forEach(x => check(false, 'page error: ' + x));
  await finish(br);
})();
