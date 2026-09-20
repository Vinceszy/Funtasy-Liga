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
   gyorsitotarazas tehat itt sem johet vissza.

   UTOLSO ISMERT ALLAS (a `TAROLT` KV-kotes): a gyorsitotar keves ahhoz,
   amit a lapnak kell. A gyorsitotar LEJAR es eldob; ha a lejarat utan
   erkezel, megint neked kell megvarnod a teljes lekerest - kozben pedig a
   3 orankent frissulo repo-adatot latod. A KERT VISELKEDES viszont az,
   hogy "ne lassak regebbit annal, amit barki utoljara lekert".

   Ezert amit ritkan valtozik, azt MEG IS JEGYEZZUK (TAROLHATO lista), es a
   lap betolteskor egyetlen keresben elkeri (`/tarolt?url=..&url=..`). Nem
   a bongeszo kuldi fel az adatot - a Worker azt jegyzi meg, amit o maga
   kert le -, tehat nincs mit meghamisitani.

   IRAS CSAK VALTOZASKOR. A KV ingyenes kerete napi 1000 iras; az NB1 elo
   pontja naponta 2-4-szer valtozik (az MLSZ meccs kozben nem ad pontot),
   a PL keretek fordulonkent egyszer. Igy napi par tucat iras a teljes
   koltseg. A gyorsan valtozo PL elo pontok SZANDEKOSAN nincsenek a
   listan: ott a legutobbi lekeres egy perc mulva ugyis ertektelen.

   A kotes HIANYOZHAT (pl. amig a KV-nevter nincs meg): olyankor a Worker
   pontosan ugy viselkedik, mint korabban - a tarolas nema no-op.

   CIKK-ERTEKELES (`/ertekeles`): a lapon minden irashoz jar egy egytol
   negyig tarto ertekeles. A ket also fokozathoz indokot is kerunk, a nezo
   SAJAT SZAVAIVAL, mert az a fajta visszajelzes, amibol a kovetkezo szoveg
   jobb lesz - a puszta "ketto" abbol semmit nem mond meg. Egy eszkoz egy irast egyszer ertekel:
   a kulcsban benne van az eszkoz azonositoja, tehat az ujraertekeles a
   sajat korabbit irja felul, nem halmoz. A tartalom a mienk, nem szemelyes
   adat - eszkoz-azonositon kivul semmit nem kerunk es nem tarolunk. */

const CEL_HOSZTOK = ['fantasy-api.mlsz.hu', 'draft.premierleague.com'];
// Az ertekeles kulcsa a cikk azonositoja: liga|fordulo|fajta|hazai|vendeg.
// Szigoru minta, mert ebbol KV-kulcs lesz: amit nem ismerunk fel, azt nem
// irjuk be.
export const CIKK_MINTA = /^(nb1|pl)\|\d{1,3}\|(summary|preview)\|[^\n\r/]{1,120}$/;
export const ESZKOZ_MINTA = /^[a-z0-9]{8,32}$/;
export const MAX_INDOK = 600;
const EREDETEK = ['https://vinceszy.github.io',
                  'http://localhost:8910', 'http://127.0.0.1:8910'];

// Mit jegyzunk meg: ami RITKAN valtozik, es amire a kovetkezo latogatonak
// is szuksege lesz. Ami percenkent valtozik, annak a megjegyzese csak a
// kvotat enne - a legutobbi valasz addigra ugyis elavult.
export const TAROLHATO = [
  /^\/competitions\/\d+\/rankings$/,        // NB1 elo pont - naponta 2-4x
  /^\/api\/entry\/\d+\/event\/\d+$/,       // PL keret - fordulon belul fix
  /^\/api\/league\/\d+\/details$/,          // PL liga-adat - fordulon belul fix
];
export const tarolhatoE = cel =>
  TAROLHATO.some(r => r.test(cel.pathname.replace(/\/+$/, '')));

// A TAROLO KULCSA a cel-URL, megtisztitva a gyorsitotar-toro belyegektol
// (`fpl_`, `_`). Enelkul minden lekeres uj kulcsot kapna, es a tarolo
// percenkent hizna ahelyett, hogy ugyanazt frissitene. A lap ugyanezt a
// tisztitast vegzi a keresesnel (funtasy.js: taroltKulcs).
export function taroltKulcs(celUrl) {
  const u = new URL(celUrl);
  u.searchParams.delete('fpl_');
  u.searchParams.delete('_');
  return u.toString();
}

export default {
  async fetch(request, env, ctx) {
    const eredet = request.headers.get('Origin');
    const cors = {
      'Access-Control-Allow-Origin':
        (eredet && EREDETEK.indexOf(eredet) >= 0) ? eredet : EREDETEK[0],
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS')
      return new Response(null, { status: 204, headers: {
        ...cors,
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Accept, Content-Type',
        'Access-Control-Max-Age': '86400',
      } });
    const sajatUt = new URL(request.url).pathname.replace(/\/+$/, '');
    if (request.method !== 'GET' && !(request.method === 'POST' && sajatUt === '/ertekeles'))
      return new Response('csak GET', { status: 405, headers: cors });
    // Bongeszobol jovo keresnel az Origin kotelezoen a mienk; Origin nelkuli
    // kerest (pl. curl, meres) atengedunk - a cel-korlatozas ugyanugy vedi.
    if (eredet && EREDETEK.indexOf(eredet) < 0)
      return new Response('ismeretlen eredet', { status: 403, headers: cors });
    const sajat = new URL(request.url);
    // ---- /ertekeles: egy iras ertekelese (1-4), indokkal ----
    // Az ERTEK a valasz, nem a keres: ha nincs KV-kotes, ezt meg is mondjuk,
    // kulonben a lap azt hinne, elment - es a nezo hiaba irt volna.
    if (sajatUt === '/ertekeles') {
      const fej = new Headers(cors);
      fej.set('Content-Type', 'application/json');
      fej.set('Cache-Control', 'no-store');
      if (!env || !env.TAROLT)
        return new Response('{"ok":false,"ok_nelkul":"nincs tarolo"}',
                            { status: 503, headers: fej });
      let be;
      try { be = await request.json(); } catch (e) { be = null; }
      const pont = be && Number(be.pont);
      if (!be || !CIKK_MINTA.test(String(be.cikk || '')) ||
          !ESZKOZ_MINTA.test(String(be.eszkoz || '')) ||
          !(pont >= 1 && pont <= 4) || pont !== Math.round(pont))
        return new Response('{"ok":false}', { status: 400, headers: fej });
      const ertek = {
        pont: pont,
        // A nezo SAJAT SZAVAI. Keszre valaszthato okok szandekosan nincsenek:
        // azok a mi kategoriainkat adnak vissza, es epp az a mondat maradna
        // ki, amire nem gondoltunk. Vagjuk, hogy egy elszallt kliens se
        // tolthesse tele a tarolot.
        indok: String(be.indok == null ? '' : be.indok).slice(0, MAX_INDOK),
        ido: new Date().toISOString(),
      };
      await env.TAROLT.put('ert/' + be.cikk + '/' + be.eszkoz, JSON.stringify(ertek));
      return new Response('{"ok":true}', { headers: fej });
    }
    // ---- /ertekelesek: amit eddig kaptunk ----
    // Nem titok: a sajat irasainkrol szol, es a liga sajat kozonsegenek.
    if (sajatUt === '/ertekelesek') {
      const fej = new Headers(cors);
      fej.set('Content-Type', 'application/json');
      fej.set('Cache-Control', 'no-store');
      if (!env || !env.TAROLT) return new Response('[]', { headers: fej });
      const lista = await env.TAROLT.list({ prefix: 'ert/', limit: 1000 });
      const ki = [];
      await Promise.all((lista.keys || []).map(async k => {
        const v = await env.TAROLT.get(k.name, { type: 'text' });
        if (!v) return;
        // a kulcs vege az eszkoz, elotte a cikk azonositoja
        const t = k.name.slice(4);
        const i = t.lastIndexOf('/');
        try { ki.push({ cikk: t.slice(0, i), ...JSON.parse(v) }); } catch (e) {}
      }));
      ki.sort((a, b) => String(b.ido).localeCompare(String(a.ido)));
      return new Response(JSON.stringify(ki), { headers: fej });
    }
    // ---- /tarolt: az UTOLSO ISMERT allas, azonnal ----
    // Egyetlen keresben tobb cel-URL is kerheto (?url=..&url=..): a lap igy
    // EGY kor-utbol megkapja mind a nyolc szakvezeto legutobbi allasat.
    // Felfele semmi nem megy ki - ha nincs meg tarolva, ures a valasz, es a
    // lap a szokasos elo lekeresre tamaszkodik.
    if (sajat.pathname.replace(/\/+$/, '') === '/tarolt') {
      const fej = new Headers(cors);
      fej.set('Content-Type', 'application/json');
      fej.set('Cache-Control', 'no-store');
      if (!env || !env.TAROLT) return new Response('{}', { headers: fej });
      const kertek = sajat.searchParams.getAll('url').slice(0, 20);
      const ki = {};
      await Promise.all(kertek.map(async u => {
        let kulcs;
        try {
          const c = new URL(u);
          if (CEL_HOSZTOK.indexOf(c.hostname) < 0) return;
          kulcs = taroltKulcs(c.toString());
        } catch (e) { return; }
        const t = await env.TAROLT.getWithMetadata(kulcs, { type: 'text' });
        if (t && t.value != null)
          ki[u] = { ido: (t.metadata && t.metadata.ido) || null, adat: t.value };
      }));
      return new Response(JSON.stringify(ki), { headers: fej });
    }
    let cel;
    try { cel = new URL(sajat.searchParams.get('url')); }
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
    // A gyorsan valtozo (nem tarolhato) valaszokat tovabbra is ATFOLYATJUK:
    // a torzset el sem olvassuk, tehat a nagy PL elo-valasz sem kerul
    // memoriaba. Csak a tarolhatokat pufferoljuk, mert azokat ossze kell
    // hasonlitani a mar eltarolttal.
    if (!env || !env.TAROLT || valasz.status !== 200 || !tarolhatoE(cel))
      return new Response(valasz.body, { status: valasz.status, headers: fej });
    const torzs = await valasz.text();
    // IRAS CSAK VALTOZASKOR - lasd a fejlecben a kvota-indoklast. Az
    // osszehasonlitashoz egy KV-olvasas kell (napi 100 000 a keret, ez
    // nagysagrendekkel alatta marad), az iras viszont ritka.
    ctx.waitUntil((async () => {
      const kulcs = taroltKulcs(cel.toString());
      try {
        const regi = await env.TAROLT.get(kulcs, { type: 'text' });
        if (regi === torzs) return;
        await env.TAROLT.put(kulcs, torzs,
                             { metadata: { ido: new Date().toISOString() } });
      } catch (e) { /* a tarolas sosem ronthatja el a valaszt */ }
    })());
    return new Response(torzs, { status: valasz.status, headers: fej });
  }
};
