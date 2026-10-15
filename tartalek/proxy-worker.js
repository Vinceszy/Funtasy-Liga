/* FunTasy's own CORS proxy - a Cloudflare Worker.

   WHY IT EXISTS: the browser cannot reach the MLSZ/FPL API directly
   (their responses carry no CORS header - measured: naplo/proxy-probe.txt),
   so every live fetch goes through an intermediary. The two free proxies
   once failed at the same time (quota/overload) - the live part of both
   leagues stopped. Our own Worker runs under our own account, nobody
   switches it off, and the free allowance (100,000 requests/day) is a
   multiple of our traffic.

   DEPLOYMENT: the worker is built tied to the REPOSITORY (Cloudflare
   "connect to git"), the settings come from wrangler.toml in the root -
   Cloudflare redeploys it after every push to main. No code has to be
   copied by hand; the worker's URL is in the OWN_PROXY constant of
   funtasy.js.

   WHAT IT DOES: for a GET request of the form ?url=<encoded target URL> it
   fetches the target and returns the response with a CORS header. It only
   serves the two known APIs, and only for our own site - it is not a
   proxy for anyone else, it cannot be abused.

   EDGE CACHE: MLSZ responses are kept for 60 seconds by Cloudflare's edge
   network, so if eight people watch the same match, ONE request a minute
   goes out to the MLSZ, not eight. The FPL live fetches deliberately skip
   this through the page's own fpl_= stamp (they have to be minute-fresh).
   Towards the browser no-store is sent - so the browser/proxy caching that
   caused the "stuck score" error cannot come back here either.

   LAST KNOWN SCORE (the `TAROLT` KV binding): a cache is not enough for
   what the page needs. A cache EXPIRES and discards; arriving after the
   expiry, you have to wait for the full fetch again - and meanwhile you
   see the repository data, refreshed by the collectors at best hourly and
   every 3 hours at other times. The WANTED BEHAVIOUR,
   however, is "let me not see anything older than what anybody fetched
   last".

   So what rarely changes IS REMEMBERED (the STORABLE list), and the page
   asks for it in a single request on load (`/tarolt?url=..&url=..`). The
   browser does not send the data up - the Worker remembers what it
   fetched itself -, so there is nothing to forge.

   WRITE ONLY ON CHANGE. The KV free allowance is 1000 writes a day; NB1's
   live points change 2-4 times a day (the MLSZ gives no points during a
   match), PL squads once per round. So the whole cost is a few dozen
   writes a day. The fast-changing PL live points are DELIBERATELY not on
   the list: there the latest fetch is worthless a minute later anyway.

   The binding MAY BE MISSING (e.g. while the KV namespace does not exist):
   then the Worker behaves exactly as it does without storage - storing is
   a silent no-op.

   ARTICLE RATING (`/ertekeles`): every piece on the page can be rated from
   one to four. For the two lower scores a reason is asked for too, IN THE
   VIEWER'S OWN WORDS, because that is the kind of feedback that makes the
   next text better - a bare "two" says nothing about that. One device
   rates one piece once: the key contains the device id, so a re-rating
   overwrites one's own earlier rating instead of piling up. The content
   is ours, not personal data - apart from the device id nothing is asked
   for or stored. */

const TARGET_HOSTS = ['fantasy-api.mlsz.hu', 'draft.premierleague.com'];
// The rating's key is the article id: league|round|kind|home|away.
// A strict pattern, because it becomes a KV key: what is not recognised is
// not written.
//
// The WEEKLY COLUMN (`elemzes`) can be rated too, and for it the last field
// is not a fixture but the article's title. Without the kind in this
// pattern the Worker rejects every column rating with 400 - the viewer
// sees nothing of it, and the log shows zero ratings, as if nobody had
// written. When a new article kind is added, THIS line has to be extended too.
export const ARTICLE_KEY_PATTERN =
  /^(nb1|pl)\|\d{1,3}\|(summary|preview|elemzes)\|[^\n\r/]{1,120}$/;
export const DEVICE_PATTERN = /^[a-z0-9]{8,32}$/;
export const MAX_REASON = 600;
const ORIGINS = ['https://vinceszy.github.io',
                  'http://localhost:8910', 'http://127.0.0.1:8910'];

// What is remembered: what changes RARELY and the next visitor will need
// too. Remembering what changes every minute would only eat the quota -
// the latest response is stale by then anyway.
export const STORABLE = [
  /^\/competitions\/\d+\/rankings$/,        // NB1 live points - 2-4x a day
  /^\/api\/entry\/\d+\/event\/\d+$/,       // PL squad - fixed within a round
  /^\/api\/league\/\d+\/details$/,          // PL league data - fixed within a round
];
export const isStorable = target =>
  STORABLE.some(r => r.test(target.pathname.replace(/\/+$/, '')));

// THE STORE'S KEY is the target URL, cleaned of the cache-busting stamps
// (`fpl_`, `_`). Without it every fetch would get a new key, and the store
// would grow every minute instead of updating the same entry. The page
// does the same cleaning when looking up (funtasy.js: storedResponses).
export function storedKey(targetUrl) {
  const u = new URL(targetUrl);
  u.searchParams.delete('fpl_');
  u.searchParams.delete('_');
  return u.toString();
}

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get('Origin');
    const cors = {
      'Access-Control-Allow-Origin':
        (origin && ORIGINS.indexOf(origin) >= 0) ? origin : ORIGINS[0],
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS')
      return new Response(null, { status: 204, headers: {
        ...cors,
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Accept, Content-Type',
        'Access-Control-Max-Age': '86400',
      } });
    const ownPath = new URL(request.url).pathname.replace(/\/+$/, '');
    if (request.method !== 'GET' && !(request.method === 'POST' && ownPath === '/ertekeles'))
      return new Response('csak GET', { status: 405, headers: cors });
    // For a request from a browser the Origin must be ours; a request without
    // Origin (e.g. curl, a measurement) is let through - the target
    // restriction protects it just the same.
    if (origin && ORIGINS.indexOf(origin) < 0)
      return new Response('ismeretlen eredet', { status: 403, headers: cors });
    // For WRITING, however, the Origin is mandatory. The GETs are protected by
    // only going to the two known APIs - the rating, on the other hand, writes
    // into OUR store, and the device id is supplied by the caller, so without
    // an Origin any number of keys could be created in it from anywhere.
    if (request.method === 'POST' && !origin)
      return new Response('ismeretlen eredet', { status: 403, headers: cors });
    const ownUrl = new URL(request.url);
    // ---- /ertekeles: rating one piece (1-4), with a reason ----
    // The VALUE is the response, not the request: when there is no KV binding,
    // that is said too, otherwise the page would believe it was saved - and the
    // viewer would have written in vain.
    if (ownPath === '/ertekeles') {
      const respHeaders = new Headers(cors);
      respHeaders.set('Content-Type', 'application/json');
      respHeaders.set('Cache-Control', 'no-store');
      if (!env || !env.TAROLT)
        return new Response('{"ok":false,"ok_nelkul":"nincs tarolo"}',
                            { status: 503, headers: respHeaders });
      let input;
      try { input = await request.json(); } catch (e) { input = null; }
      const score = input && Number(input.pont);
      if (!input || !ARTICLE_KEY_PATTERN.test(String(input.cikk || '')) ||
          !DEVICE_PATTERN.test(String(input.eszkoz || '')) ||
          !(score >= 1 && score <= 4) || score !== Math.round(score))
        return new Response('{"ok":false}', { status: 400, headers: respHeaders });
      const record = {
        pont: score,
        // The viewer's OWN WORDS. There are deliberately no ready-made reasons to
        // pick: those give back our own categories, and exactly the sentence we
        // had not thought of would be left out. Cut, so that a runaway client
        // cannot fill up the store either.
        indok: String(input.indok == null ? '' : input.indok).slice(0, MAX_REASON),
        ido: new Date().toISOString(),
      };
      await env.TAROLT.put('ert/' + input.cikk + '/' + input.eszkoz, JSON.stringify(record));
      return new Response('{"ok":true}', { headers: respHeaders });
    }
    // ---- /ertekelesek: what has been received so far ----
    // Not a secret: it is about our own writing, and for the league's own audience.
    if (ownPath === '/ertekelesek') {
      const respHeaders = new Headers(cors);
      respHeaders.set('Content-Type', 'application/json');
      respHeaders.set('Cache-Control', 'no-store');
      // An empty list and "no store" are NOT the same: the first means nobody
      // has rated yet, the second that every rating gets lost. The same answer
      // to both would make the failure look like zero ratings - exactly when
      // something is wrong.
      if (!env || !env.TAROLT)
        return new Response('[]', { status: 503, headers: respHeaders });
      const listing = await env.TAROLT.list({ prefix: 'ert/', limit: 1000 });
      const out = [];
      await Promise.all((listing.keys || []).map(async k => {
        const v = await env.TAROLT.get(k.name, { type: 'text' });
        if (!v) return;
        // the end of the key is the device, before it the article id
        const t = k.name.slice(4);
        const i = t.lastIndexOf('/');
        try { out.push({ cikk: t.slice(0, i), ...JSON.parse(v) }); } catch (e) {}
      }));
      out.sort((a, b) => String(b.ido).localeCompare(String(a.ido)));
      return new Response(JSON.stringify(out), { headers: respHeaders });
    }
    // ---- /tarolt: the LAST KNOWN score, at once ----
    // Several target URLs can be asked for in one request (?url=..&url=..): so
    // the page gets the latest score of all eight managers in ONE round trip.
    // Nothing goes out upstream - if it is not stored yet, the response is
    // empty, and the page relies on the usual live fetch.
    if (ownUrl.pathname.replace(/\/+$/, '') === '/tarolt') {
      const respHeaders = new Headers(cors);
      respHeaders.set('Content-Type', 'application/json');
      respHeaders.set('Cache-Control', 'no-store');
      if (!env || !env.TAROLT) return new Response('{}', { headers: respHeaders });
      const wanted = ownUrl.searchParams.getAll('url').slice(0, 20);
      const out = {};
      await Promise.all(wanted.map(async u => {
        let key;
        try {
          const c = new URL(u);
          if (TARGET_HOSTS.indexOf(c.hostname) < 0) return;
          key = storedKey(c.toString());
        } catch (e) { return; }
        const t = await env.TAROLT.getWithMetadata(key, { type: 'text' });
        if (t && t.value != null)
          out[u] = { ido: (t.metadata && t.metadata.ido) || null, adat: t.value };
      }));
      return new Response(JSON.stringify(out), { headers: respHeaders });
    }
    let target;
    try { target = new URL(ownUrl.searchParams.get('url')); }
    catch (e) {
      return new Response('hianyzo vagy rossz ?url= parameter',
                          { status: 400, headers: cors });
    }
    if (TARGET_HOSTS.indexOf(target.hostname) < 0 || target.protocol !== 'https:')
      return new Response('nem engedett cel: ' + target.hostname,
                          { status: 403, headers: cors });
    const upstream = await fetch(target.toString(), {
      headers: { 'Accept': 'application/json',
                 'User-Agent': 'FunTasy-proxy (github.com/Vinceszy/Funtasy-Liga)' },
      cf: { cacheTtl: 60, cacheEverything: true },
    });
    const respHeaders = new Headers(cors);
    respHeaders.set('Content-Type',
            upstream.headers.get('Content-Type') || 'application/json');
    respHeaders.set('Cache-Control', 'no-store');
    // Fast-changing (not storable) responses are still STREAMED THROUGH: the
    // body is not even read, so the large PL live response does not end up in
    // memory either. Only the storable ones are buffered, because they have
    // to be compared with what is already stored.
    if (!env || !env.TAROLT || upstream.status !== 200 || !isStorable(target))
      return new Response(upstream.body, { status: upstream.status, headers: respHeaders });
    const text = await upstream.text();
    // WRITE ONLY ON CHANGE - see the quota reasoning in the header. The
    // comparison takes one KV read (the allowance is 100,000 a day, this stays
    // orders of magnitude below it), while writing is rare.
    ctx.waitUntil((async () => {
      const key = storedKey(target.toString());
      try {
        const previous = await env.TAROLT.get(key, { type: 'text' });
        if (previous === text) return;
        await env.TAROLT.put(key, text,
                             { metadata: { ido: new Date().toISOString() } });
      } catch (e) { /* storing can never spoil the response */ }
    })());
    return new Response(text, { status: upstream.status, headers: respHeaders });
  }
};
