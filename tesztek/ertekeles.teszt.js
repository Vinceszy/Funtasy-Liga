const { jo, cim, vege } = require('./kozos');
// A CIKK-ERTEKELES TAROLASA (tartalek/proxy-worker.js: /ertekeles).
//
// MIERT KELL: az irasok attol lesznek jobbak, hogy megtudjuk, MI nem
// tetszett. A puszta pontszam ehhez keves, tehat az also ket fokozathoz a
// lap indokot ker - a Worker dolga az, hogy ezt el is tarolja, es hogy amit
// nem ismer fel, azt ne irja be.
//
// A Workert INNEN nem lehet elerni, ezert a logikat hamis KV-vel merjuk -
// ugyanugy, mint a tarolonal (tesztek/workertarolo.teszt.js).
//
// Amit rogzit:
//  - ervenyes ertekeles eltarolodik, a pont es az indok egyutt;
//  - UGYANAZ AZ ESZKOZ ugyanarra a cikkre nem halmoz, hanem felulir;
//  - mas eszkoz kulon sort kap;
//  - a tartomanyon kivuli pont, az ismeretlen cikk-azonosito es a rossz
//    eszkoz-azonosito 400-at kap, es NEM ir;
//  - a tul hosszu indok le van vagva (egy elszallt kliens se tolthesse tele);
//  - keszre valaszthato okokat NEM tarolunk: a nezo sajat szavai kellenek;
//  - GET-tel nem lehet ertekelni, es KV-kotes nelkul megmondja, hogy nem ment el;
//  - a /ertekelesek visszaadja, amit kaptunk.
const PROXY = 'https://funtasy-liga.swick00.workers.dev';
const EREDET = 'https://vinceszy.github.io';
const CIKK = 'nb1|7|summary|Bence|Csendi';
const ESZKOZ = 'k7x2m9q1abcd';

function ujKV(){
  const tar = new Map();
  return {
    irasok: 0, tar,
    async get(k){ const v = tar.get(k); return v == null ? null : v; },
    async getWithMetadata(k){ const v = tar.get(k);
      return { value: v == null ? null : v, metadata: null }; },
    async put(k, v){ this.irasok++; tar.set(k, v); },
    async list({ prefix, limit }){
      return { keys: [...tar.keys()].filter(k => k.startsWith(prefix || ''))
                       .slice(0, limit || 1000).map(name => ({ name })) };
    },
  };
}

(async () => {
  const modul = await import('file://' + require('path').join(__dirname, '..',
                                                'tartalek', 'proxy-worker.js'));
  const worker = modul.default;
  const varok = [];
  const ctx = { waitUntil: p => varok.push(p) };
  globalThis.fetch = async () => new Response('{}', { status: 200 });

  const kuld = async (torzs, env, mod) => {
    const r = await worker.fetch(new Request(PROXY + '/ertekeles', {
      method: mod || 'POST', headers: { Origin: EREDET, 'Content-Type': 'application/json' },
      ...(mod === 'GET' ? {} : { body: JSON.stringify(torzs) }),
    }), env, ctx);
    await Promise.all(varok.splice(0));
    return r;
  };

  // ---- 1) ervenyes ertekeles ----
  cim('Értékelés: eltárolódik a pont és az indok');
  const kv = ujKV(), env = { TAROLT: kv };
  let r = await kuld({ cikk: CIKK, eszkoz: ESZKOZ, pont: 2,
                       indok: 'Semmi nem derült ki belőle.' }, env);
  jo(r.status === 200, 'HTTP 200 — ' + r.status);
  jo((await r.json()).ok === true, 'a válasz nyugtáz');
  jo(kv.irasok === 1, 'egy írás — ' + kv.irasok);
  const kulcs = [...kv.tar.keys()][0];
  jo(kulcs === 'ert/' + CIKK + '/' + ESZKOZ, 'a kulcsban a cikk ÉS az eszköz — ' + kulcs);
  const mentett = JSON.parse(kv.tar.get(kulcs));
  jo(mentett.pont === 2, 'a pont elmentődött — ' + mentett.pont);
  jo(mentett.indok === 'Semmi nem derült ki belőle.', 'a néző saját szavai is');
  jo(!('okok' in mentett),
     'készre választható okokat nem tárolunk — a mi kategóriáink nem tanítanak semmire');
  jo(!!mentett.ido, 'időbélyeggel');

  // ---- 2) ugyanaz az eszkoz nem halmoz ----
  cim('Értékelés: ugyanaz az eszköz felülír, nem halmoz');
  await kuld({ cikk: CIKK, eszkoz: ESZKOZ, pont: 4 }, env);
  jo(kv.tar.size === 1, 'továbbra is egy sor — ' + kv.tar.size);
  jo(JSON.parse(kv.tar.get(kulcs)).pont === 4, 'az új pont lépett a régi helyére');
  await kuld({ cikk: CIKK, eszkoz: 'masikeszkoz99', pont: 1, indok: 'Unalmas.' }, env);
  jo(kv.tar.size === 2, 'másik eszköz külön sort kap — ' + kv.tar.size);

  // ---- 3) amit nem ismerunk fel, azt nem irjuk be ----
  cim('Értékelés: a hibás kérés nem ír');
  const rossz = [
    ['tartományon kívüli pont', { cikk: CIKK, eszkoz: ESZKOZ, pont: 7 }],
    ['nulla pont',              { cikk: CIKK, eszkoz: ESZKOZ, pont: 0 }],
    ['tört pont',               { cikk: CIKK, eszkoz: ESZKOZ, pont: 2.5 }],
    ['ismeretlen liga',         { cikk: 'xx|7|summary|A|B', eszkoz: ESZKOZ, pont: 3 }],
    ['ismeretlen fajta',        { cikk: 'nb1|7|vicc|A|B', eszkoz: ESZKOZ, pont: 3 }],
    ['perjel a cikkben',        { cikk: 'nb1|7|summary|A/B', eszkoz: ESZKOZ, pont: 3 }],
    ['rossz eszközazonosító',   { cikk: CIKK, eszkoz: 'RÖVID', pont: 3 }],
    ['hiányzó cikk',            { eszkoz: ESZKOZ, pont: 3 }],
  ];
  for (const [cimke, torzs] of rossz) {
    const elotte = kv.irasok;
    const v = await kuld(torzs, env);
    jo(v.status === 400 && kv.irasok === elotte, cimke + ' -> HTTP ' + v.status
       + ', írás: ' + (kv.irasok - elotte));
  }

  // ---- 4) a tul hosszu indok le van vagva ----
  cim('Értékelés: a túl hosszú indok levágva');
  const kv2 = ujKV(), env2 = { TAROLT: kv2 };
  await kuld({ cikk: CIKK, eszkoz: ESZKOZ, pont: 1, indok: 'x'.repeat(5000),
               okok: new Array(50).fill('y'.repeat(200)) }, env2);
  const m2 = JSON.parse(kv2.tar.get('ert/' + CIKK + '/' + ESZKOZ));
  jo(m2.indok.length === modul.MAX_INDOK, 'az indok ' + m2.indok.length + ' karakter');
  jo(!('okok' in m2), 'a kívülről küldött okokat el sem tároljuk');

  // ---- 5) GET-tel nem lehet ertekelni, kotes nelkul pedig szol ----
  cim('Értékelés: GET nem megy, kötés nélkül megmondja');
  const g = await kuld(null, env, 'GET');
  jo(g.status === 400, 'GET-re nem ír, hanem hibázik — HTTP ' + g.status);
  const n = await kuld({ cikk: CIKK, eszkoz: ESZKOZ, pont: 3 }, {});
  jo(n.status === 503, 'kötés nélkül HTTP 503 — ' + n.status
     + ' (nem hazudjuk azt, hogy elment)');

  // ---- 6) a lista visszaadja ----
  cim('Értékelés: a lista visszaadja, amit kaptunk');
  const l = await worker.fetch(new Request(PROXY + '/ertekelesek',
    { headers: { Origin: EREDET } }), env, ctx);
  const lista = await l.json();
  jo(Array.isArray(lista) && lista.length === 2, 'két értékelés jött — ' + lista.length);
  jo(lista.every(x => x.cikk === CIKK), 'mindkettő a cikkhez tartozik');
  jo(lista.some(x => x.indok === 'Unalmas.'), 'az indok is benne van');

  await vege(null);
})();
