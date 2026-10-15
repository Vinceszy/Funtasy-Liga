const { check, section, finish } = require('./common');
// THE WORKER'S "LAST KNOWN SCORE" STORE (tartalek/proxy-worker.js).
//
// WHY IT IS NEEDED: the cache expires and drops - whoever arrives after the
// expiry has to wait for the full fetch again, and meanwhile sees the
// repository data that refreshes every 3 hours. The wanted behaviour is "I
// must not see anything older than what anybody fetched last".
//
// The Worker CANNOT be reached from here (the work environment does not
// allow going out to workers.dev), so the logic is measured here, with a
// fake KV and a fake network. The end-to-end measurement runs separately,
// from GitHub Actions.
//
// What it pins:
//  - a storable answer passes through unchanged, and is stored once;
//  - an UNCHANGED answer does not write again (critical because of the
//    1000 KV writes a day);
//  - on a change it writes;
//  - it does NOT store the fast-changing PL live points;
//  - the cache-busting stamp (fpl_) does not create a new key;
//  - the /tarolt endpoint does not start a SINGLE upstream request;
//  - without the binding the Worker works exactly as before.
const PROXY = 'https://funtasy-liga.swick00.workers.dev';
const ORIGIN = 'https://vinceszy.github.io';
const NB1 = uname => 'https://fantasy-api.mlsz.hu/competitions/3/rankings'
  + '?include=user_team.user.id&page=1&per_page=5&filter%5Bsearch%5D=' + uname;
const PL_LIVE  = 'https://draft.premierleague.com/api/event/5/live';
const PL_SQUAD = 'https://draft.premierleague.com/api/entry/900001/event/5';

function newKV(){
  const store = new Map();
  return {
    writes: 0, reads: 0, store,
    async get(k){ this.reads++; const v = store.get(k); return v ? v.value : null; },
    async getWithMetadata(k){
      this.reads++; const v = store.get(k);
      return v ? { value: v.value, metadata: v.meta } : { value: null, metadata: null };
    },
    async put(k, v, o){ this.writes++; store.set(k, { value: v, meta: (o || {}).metadata }); },
  };
}

(async () => {
  const mod = await import('file://' + require('path').join(__dirname, '..',
                                              'tartalek', 'proxy-worker.js'));
  const worker = mod.default;

  // fake network: the test sets the answer, and we count the calls
  let answerBody = '{"data":[1]}', upstream = 0, lastTarget = null;
  globalThis.fetch = async (u) => {
    upstream++; lastTarget = String(u);
    return new Response(answerBody, { status: 200,
      headers: { 'Content-Type': 'application/json' } });
  };

  const pending = [];
  const ctx = { waitUntil: p => pending.push(p) };
  const call = async (path, env) => {
    const r = await worker.fetch(
      new Request(path, { headers: { Origin: ORIGIN } }), env, ctx);
    await Promise.all(pending.splice(0));      // finish the waitUntil calls
    return r;
  };
  const via = target => PROXY + '/?url=' + encodeURIComponent(target);

  // ---- 1) storable answer: passes through and is stored ----
  section('Worker: remembers the rarely changing answer');
  const kv = newKV();
  const env = { TAROLT: kv };
  let r = await call(via(NB1('HolVanSalah')), env);
  check(r.status === 200, 'the answer passes through (HTTP ' + r.status + ')');
  check((await r.text()) === answerBody, 'the body is unchanged');
  check(upstream === 1, 'one request went upstream — ' + upstream);
  check(kv.writes === 1, 'stored once — ' + kv.writes + ' writes');
  const key = [...kv.store.keys()][0];
  check(!!(kv.store.get(key).meta || {}).ido, 'the timestamp was saved too');

  // ---- 2) unchanged answer: does NOT write again ----
  section('Worker: does not write on an unchanged answer');
  await call(via(NB1('HolVanSalah')), env);
  check(kv.writes === 1, 'still 1 write — ' + kv.writes
     + ' (this is the point, because of the 1000-a-day limit)');

  // ---- 3) change: writes ----
  section('Worker: writes on a change');
  answerBody = '{"data":[2]}';
  await call(via(NB1('HolVanSalah')), env);
  check(kv.writes === 2, 'now 2 writes — ' + kv.writes);
  check(kv.store.size === 1, 'the same key was updated, no new one was created — '
     + kv.store.size + ' keys');

  // ---- 4) the cache-busting stamp does not create a new key ----
  section('Worker: the fpl_ stamp does not scatter keys');
  const kv2 = newKV(), env2 = { TAROLT: kv2 };
  await call(via(PL_SQUAD + '?fpl_=111'), env2);
  await call(via(PL_SQUAD + '?fpl_=222'), env2);
  check(kv2.store.size === 1, 'a single key — ' + kv2.store.size);
  check(kv2.writes === 1, 'the second one did not write again (same data) — ' + kv2.writes);

  // ---- 5) the fast-changing PL live points are not stored ----
  section('Worker: does not store the PL live points that change every minute');
  const kv3 = newKV(), env3 = { TAROLT: kv3 };
  const r3 = await call(via(PL_LIVE), env3);
  check(r3.status === 200, 'the answer passes through just the same');
  check(kv3.writes === 0, 'not a single write — ' + kv3.writes);

  // ---- 6) /tarolt: immediate answer, nothing upstream ----
  section('Worker: /tarolt does not go out to the network');
  const before = upstream;
  const t = await call(PROXY + '/tarolt?url=' + encodeURIComponent(NB1('HolVanSalah'))
                       + '&url=' + encodeURIComponent(NB1('Hoxha98')), env);
  check(upstream === before, 'not a single request went upstream — ' + (upstream - before));
  const j = await t.json();
  check(!!j[NB1('HolVanSalah')], 'the stored score arrived');
  check(j[NB1('HolVanSalah')].adat === '{"data":[2]}',
     'the data of the LATEST fetch came, not the earlier one');
  check(!!j[NB1('HolVanSalah')].ido, 'together with its timestamp');
  check(!(NB1('Hoxha98') in j), 'what nobody has fetched yet has no entry');

  // ---- 7) without the binding everything stays as before ----
  section('Worker: without the KV binding, the old behaviour');
  const before2 = upstream;
  const r4 = await call(via(NB1('samsonp')), {});
  check(r4.status === 200 && (await r4.text()) === answerBody,
     'the proxy serves just the same');
  check(upstream === before2 + 1, 'the fetch happened');
  const t4 = await call(PROXY + '/tarolt?url=' + encodeURIComponent(NB1('samsonp')), {});
  check((await t4.text()) === '{}', '/tarolt gives an empty answer, not an error');

  // ---- 8) the origin check applies to /tarolt too ----
  section('Worker: /tarolt does not serve a foreign origin either');
  const r5 = await worker.fetch(
    new Request(PROXY + '/tarolt?url=' + encodeURIComponent(NB1('HolVanSalah')),
                { headers: { Origin: 'https://valaki.mas' } }), env, ctx);
  check(r5.status === 403, 'foreign origin rejected (HTTP ' + r5.status + ')');

  await finish();
})();
