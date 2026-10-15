const { check, section, finish } = require('./common');
// STORAGE OF ARTICLE RATINGS (tartalek/proxy-worker.js: /ertekeles).
//
// WHY IT IS NEEDED: the articles get better by learning WHAT was not liked.
// A bare score is too little for that, so for the bottom two grades the
// page asks for a reason - the Worker's job is to actually store it, and not
// to write in anything it does not recognise.
//
// The Worker cannot be reached FROM HERE, so the logic is measured with a
// fake KV - the same way as for the store (tests/worker-store.test.js).
//
// What it pins down:
//  - a valid rating is stored, the score and the reason together;
//  - THE SAME DEVICE does not pile up on the same article, it overwrites;
//  - another device gets a separate row;
//  - an out-of-range score, an unknown article id and a bad device id get
//    400, and do NOT write;
//  - a reason that is too long is cut off (not even a runaway client may
//    fill it up);
//  - ready-made selectable reasons are NOT stored: the viewer's own words
//    are what we need;
//  - rating with GET is not possible, and without a KV binding it says that
//    it was not saved;
//  - /ertekelesek returns what we got.
const PROXY = 'https://funtasy-liga.swick00.workers.dev';
const ORIGIN = 'https://vinceszy.github.io';
const ARTICLE = 'nb1|7|summary|Bence|Csendi';
// The weekly column has no head-to-head: the last field is the article's
// title. This kind was missing from the Worker's pattern, and every column
// rating was lost because of it.
const COLUMN = 'nb1|9|elemzes|Szegény ember percekkel főz';
const DEVICE = 'k7x2m9q1abcd';

function newKV(){
  const store = new Map();
  return {
    writes: 0, store,
    async get(k){ const v = store.get(k); return v == null ? null : v; },
    async getWithMetadata(k){ const v = store.get(k);
      return { value: v == null ? null : v, metadata: null }; },
    async put(k, v){ this.writes++; store.set(k, v); },
    async list({ prefix, limit }){
      return { keys: [...store.keys()].filter(k => k.startsWith(prefix || ''))
                       .slice(0, limit || 1000).map(name => ({ name })) };
    },
  };
}

(async () => {
  const mod = await import('file://' + require('path').join(__dirname, '..',
                                              'tartalek', 'proxy-worker.js'));
  const worker = mod.default;
  const pending = [];
  const ctx = { waitUntil: p => pending.push(p) };
  globalThis.fetch = async () => new Response('{}', { status: 200 });

  const send = async (body, env, method) => {
    const r = await worker.fetch(new Request(PROXY + '/ertekeles', {
      method: method || 'POST', headers: { Origin: ORIGIN, 'Content-Type': 'application/json' },
      ...(method === 'GET' ? {} : { body: JSON.stringify(body) }),
    }), env, ctx);
    await Promise.all(pending.splice(0));
    return r;
  };

  // ---- 1) a valid rating ----
  section('Rating: the score and the reason are stored');
  const kv = newKV(), env = { TAROLT: kv };
  let r = await send({ cikk: ARTICLE, eszkoz: DEVICE, pont: 2,
                       indok: 'Semmi nem derült ki belőle.' }, env);
  check(r.status === 200, 'HTTP 200 — ' + r.status);
  check((await r.json()).ok === true, 'the response acknowledges');
  check(kv.writes === 1, 'one write — ' + kv.writes);
  const key = [...kv.store.keys()][0];
  check(key === 'ert/' + ARTICLE + '/' + DEVICE, 'the key holds the article AND the device — ' + key);
  const saved = JSON.parse(kv.store.get(key));
  check(saved.pont === 2, 'the score was saved — ' + saved.pont);
  check(saved.indok === 'Semmi nem derült ki belőle.', 'the viewer\'s own words too');
  check(!('okok' in saved),
     'ready-made selectable reasons are not stored — our categories teach us nothing');
  check(!!saved.ido, 'with a timestamp');

  // ---- 1/b) rating the WEEKLY COLUMN ----
  // It has no head-to-head, the last field is the title. This kind was
  // missing from the Worker's pattern for a long time, so every column rating
  // fell with 400, and the log looked as if nobody had rated anything.
  section('Rating: the weekly column can be rated too');
  const kvC = newKV();
  const rC = await send({ cikk: COLUMN, eszkoz: DEVICE, pont: 4 }, { TAROLT: kvC });
  check(rC.status === 200, 'a rating of the column goes through — HTTP ' + rC.status);
  check([...kvC.store.keys()][0] === 'ert/' + COLUMN + '/' + DEVICE,
     'and the title goes into the key — ' + [...kvC.store.keys()][0]);

  // The Worker's pattern and the page's article kinds change TOGETHER. If a
  // new kind is added to the page but not here, its ratings are silently lost.
  const kindsSrc = (require('fs').readFileSync(
    require('path').join(__dirname, '..', 'funtasy.js'), 'utf8')
      .match(/var ARTICLE_LABEL = \{([^}]*)\}/) || [])[1] || '';
  const pageKinds = [...kindsSrc.matchAll(/(\w+):/g)].map(m => m[1]).sort();
  const pattern = (require('fs').readFileSync(
    require('path').join(__dirname, '..', 'tartalek', 'proxy-worker.js'), 'utf8')
      .match(/ARTICLE_KEY_PATTERN\s*=\s*\n?\s*\/\^\(nb1\|pl\)[^;]*?\(([a-z|]+)\)/) || [])[1] || '';
  const workerKinds = pattern.split('|').sort();
  check(JSON.stringify(pageKinds) === JSON.stringify(workerKinds),
     'the Worker accepts every article kind that exists on the page — page: ['
     + pageKinds + '] worker: [' + workerKinds + ']');

  // ---- 2) the same device does not pile up ----
  section('Rating: the same device overwrites, it does not pile up');
  await send({ cikk: ARTICLE, eszkoz: DEVICE, pont: 4 }, env);
  check(kv.store.size === 1, 'still one row — ' + kv.store.size);
  check(JSON.parse(kv.store.get(key)).pont === 4, 'the new score took the place of the old one');
  await send({ cikk: ARTICLE, eszkoz: 'masikeszkoz99', pont: 1, indok: 'Unalmas.' }, env);
  check(kv.store.size === 2, 'another device gets a separate row — ' + kv.store.size);

  // ---- 3) what we do not recognise, we do not write ----
  section('Rating: a bad request does not write');
  const bad = [
    ['out-of-range score',   { cikk: ARTICLE, eszkoz: DEVICE, pont: 7 }],
    ['zero score',           { cikk: ARTICLE, eszkoz: DEVICE, pont: 0 }],
    ['fractional score',     { cikk: ARTICLE, eszkoz: DEVICE, pont: 2.5 }],
    ['unknown league',       { cikk: 'xx|7|summary|A|B', eszkoz: DEVICE, pont: 3 }],
    ['unknown kind',         { cikk: 'nb1|7|vicc|A|B', eszkoz: DEVICE, pont: 3 }],
    ['slash in the article', { cikk: 'nb1|7|summary|A/B', eszkoz: DEVICE, pont: 3 }],
    ['bad device id',        { cikk: ARTICLE, eszkoz: 'RÖVID', pont: 3 }],
    ['missing article',      { eszkoz: DEVICE, pont: 3 }],
  ];
  for (const [label, body] of bad) {
    const before = kv.writes;
    const v = await send(body, env);
    check(v.status === 400 && kv.writes === before, label + ' -> HTTP ' + v.status
       + ', writes: ' + (kv.writes - before));
  }

  // ---- 4) a reason that is too long is cut off ----
  section('Rating: a reason that is too long is cut off');
  const kv2 = newKV(), env2 = { TAROLT: kv2 };
  await send({ cikk: ARTICLE, eszkoz: DEVICE, pont: 1, indok: 'x'.repeat(5000),
               okok: new Array(50).fill('y'.repeat(200)) }, env2);
  const m2 = JSON.parse(kv2.store.get('ert/' + ARTICLE + '/' + DEVICE));
  check(m2.indok.length === mod.MAX_REASON, 'the reason is ' + m2.indok.length + ' characters');
  check(!('okok' in m2), 'reasons sent from outside are not even stored');

  // ---- 5) rating with GET is not possible, and without a binding it says so ----
  section('Rating: GET does not work, without a binding it says so');
  const g = await send(null, env, 'GET');
  check(g.status === 400, 'on GET it does not write but errors — HTTP ' + g.status);
  const n = await send({ cikk: ARTICLE, eszkoz: DEVICE, pont: 3 }, {});
  check(n.status === 503, 'without a binding HTTP 503 — ' + n.status
     + ' (we do not lie that it was saved)');

  // ---- 6) no writing without an Origin ----
  // The GETs are protected by going only to the two known APIs; the rating,
  // however, writes into OUR store, and the device id is supplied by the
  // caller. Without an Origin (curl, a script) an unlimited number of keys
  // could be created in it from anywhere.
  section('Rating: no writing without an Origin');
  const kv3 = newKV(), env3 = { TAROLT: kv3 };
  const raw = await worker.fetch(new Request(PROXY + '/ertekeles',
    { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cikk: ARTICLE, eszkoz: DEVICE, pont: 4 }) }), env3, ctx);
  check(raw.status === 403, 'a POST without an Origin gets HTTP 403 — ' + raw.status);
  check(kv3.writes === 0, 'and it did not write to the store either — ' + kv3.writes + ' writes');

  // ---- 7) the list returns it ----
  section('Rating: the list returns what we got');
  const l = await worker.fetch(new Request(PROXY + '/ertekelesek',
    { headers: { Origin: ORIGIN } }), env, ctx);
  const list = await l.json();
  check(Array.isArray(list) && list.length === 2, 'two ratings came — ' + list.length);
  check(list.every(x => x.cikk === ARTICLE), 'both belong to the article');
  check(list.some(x => x.indok === 'Unalmas.'), 'the reason is in it too');

  // "Nobody has rated yet" and "there is no store" are two different states.
  // If both returned an empty list, a broken binding would look like zero
  // ratings - that is, we would stay silent exactly when we should speak up.
  const noBinding = await worker.fetch(new Request(PROXY + '/ertekelesek',
    { headers: { Origin: ORIGIN } }), {}, ctx);
  check(noBinding.status === 503, 'without a binding the list gives 503 too — '
     + noBinding.status + ' (an empty list must not lie zero)');
  const emptyKv = await worker.fetch(new Request(PROXY + '/ertekelesek',
    { headers: { Origin: ORIGIN } }), { TAROLT: newKV() }, ctx);
  check(emptyKv.status === 200 && (await emptyKv.json()).length === 0,
     'with an empty store, though, 200 and an empty list — there really are no ratings there');

  await finish(null);
})();
