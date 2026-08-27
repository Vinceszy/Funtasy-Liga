/* FunTasy sajat CORS-proxy - Cloudflare Worker.

   MIERT LETEZIK: a bongeszo az MLSZ/FPL API-t kozvetlenul nem erheti el
   (nincs CORS-fejlec a valaszukban - merve: naplo/proxy-meres.txt), ezert
   minden elo lekeres kozvetiton megy at. 2026-08-27-en a ket ingyenes
   kozvetito egyszerre esett ki (kvota/tulterheles) - mindket liga elo resze
   leallt. A sajat Worker a sajat fiokunk alatt fut, senki nem kapcsolja le,
   es az ingyenes keret (100 000 keres/nap) a forgalmunk sokszorosa.

   TELEPITES: a worker a REPOHOZ kotve epul (Cloudflare "connect to git"),
   a beallitasokat a gyokerbeli wrangler.toml adja - minden main-re erkezo
   push utan a Cloudflare ujratelepiti. Kezzel nem kell kodot masolni; a
   worker URL-je a funtasy.js SAJAT_PROXY konstansaban all.

   MIT CSINAL: ?url=<kodolt cel-URL> alaku GET keresre lekeri a celt, es a
   valaszt CORS-fejleccel adja vissza. Csak a ket ismert API-t szolgalja ki,
   es csak a sajat oldalunknak - masnak nem proxy, nem lehet visszaelni vele.

   EDGE-CACHE: az MLSZ-valaszokat 60 masodpercig a Cloudflare peremhaloja
   tarolja, tehat ha nyolcan nezik ugyanazt a meccset, az MLSZ fele EGY
   keres megy ki percenkent, nem nyolc. Az FPL elo lekereseit a lap sajat
   fpl_= belyege szandekosan kihagyja ebbol (percre friss kell). A bongeszo
   fele no-store megy - a "beragadt pontszam" hibat okozo bongeszo/proxy-
   gyorsitotarazas tehat itt sem johet vissza. */

const CEL_HOSZTOK = ['fantasy-api.mlsz.hu', 'draft.premierleague.com'];
const EREDETEK = ['https://vinceszy.github.io',
                  'http://localhost:8910', 'http://127.0.0.1:8910'];

export default {
  async fetch(request) {
    const eredet = request.headers.get('Origin');
    const cors = {
      'Access-Control-Allow-Origin':
        (eredet && EREDETEK.indexOf(eredet) >= 0) ? eredet : EREDETEK[0],
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS')
      return new Response(null, { status: 204, headers: {
        ...cors,
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Accept',
        'Access-Control-Max-Age': '86400',
      } });
    if (request.method !== 'GET')
      return new Response('csak GET', { status: 405, headers: cors });
    // Bongeszobol jovo keresnel az Origin kotelezoen a mienk; Origin nelkuli
    // kerest (pl. curl, meres) atengedunk - a cel-korlatozas ugyanugy vedi.
    if (eredet && EREDETEK.indexOf(eredet) < 0)
      return new Response('ismeretlen eredet', { status: 403, headers: cors });
    let cel;
    try { cel = new URL(new URL(request.url).searchParams.get('url')); }
    catch (e) {
      return new Response('hianyzo vagy rossz ?url= parameter',
                          { status: 400, headers: cors });
    }
    if (CEL_HOSZTOK.indexOf(cel.hostname) < 0 || cel.protocol !== 'https:')
      return new Response('nem engedett cel: ' + cel.hostname,
                          { status: 403, headers: cors });
    const valasz = await fetch(cel.toString(), {
      headers: { 'Accept': 'application/json',
                 'User-Agent': 'FunTasy-proxy (github.com/Vinceszy/Funtasy-Liga)' },
      cf: { cacheTtl: 60, cacheEverything: true },
    });
    const fej = new Headers(cors);
    fej.set('Content-Type',
            valasz.headers.get('Content-Type') || 'application/json');
    fej.set('Cache-Control', 'no-store');
    return new Response(valasz.body, { status: valasz.status, headers: fej });
  }
};
