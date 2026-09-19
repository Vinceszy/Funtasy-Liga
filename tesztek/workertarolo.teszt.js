const { jo, cim, vege } = require('./kozos');
// A WORKER "UTOLSO ISMERT ALLAS" TAROLOJA (tartalek/proxy-worker.js).
//
// MIERT KELL: a gyorsitotar lejar es eldob - aki a lejarat utan erkezik,
// annak megint meg kell varnia a teljes lekerest, kozben pedig a 3 orankent
// frissulo repo-adatot latja. A kert viselkedes viszont az, hogy "ne lassak
// regebbit annal, amit barki utoljara lekert".
//
// A Workert INNEN nem lehet elerni (a munkakornyezet nem enged ki a
// workers.dev-re), ezert a logikat itt, hamis KV-vel es hamis halozattal
// merjuk. A vegpontrol-vegpontig meres kulon, GitHub Actions-bol megy.
//
// Amit rogzit:
//  - a tarolhato valasz atmegy valtozatlanul, es egyszer el is tarolodik;
//  - VALTOZATLAN valasz nem ir ujra (a napi 1000 KV-iras miatt kritikus);
//  - valtozas eseten ir;
//  - a gyorsan valtozo PL elo pontot NEM tarolja;
//  - a gyorsitotar-toro belyeg (fpl_) nem csinal uj kulcsot;
//  - a /tarolt vegpont felfele EGYETLEN kerest sem indit;
//  - kotes nelkul a Worker pontosan ugy mukodik, mint korabban.
const PROXY = 'https://funtasy-liga.swick00.workers.dev';
const EREDET = 'https://vinceszy.github.io';
const NB1 = uname => 'https://fantasy-api.mlsz.hu/competitions/3/rankings'
  + '?include=user_team.user.id&page=1&per_page=5&filter%5Bsearch%5D=' + uname;
const PL_ELO  = 'https://draft.premierleague.com/api/event/5/live';
const PL_KERET = 'https://draft.premierleague.com/api/entry/900001/event/5';

function ujKV(){
  const tar = new Map();
  return {
    irasok: 0, olvasasok: 0, tar,
    async get(k){ this.olvasasok++; const v = tar.get(k); return v ? v.ertek : null; },
    async getWithMetadata(k){
      this.olvasasok++; const v = tar.get(k);
      return v ? { value: v.ertek, metadata: v.meta } : { value: null, metadata: null };
    },
    async put(k, v, o){ this.irasok++; tar.set(k, { ertek: v, meta: (o || {}).metadata }); },
  };
}

(async () => {
  const modul = await import('file://' + require('path').join(__dirname, '..',
                                                'tartalek', 'proxy-worker.js'));
  const worker = modul.default;

  // hamis halozat: a valaszt a teszt allitja be, es szamoljuk a hivasokat
  let valaszTorzs = '{"data":[1]}', felfele = 0, utolsoCel = null;
  globalThis.fetch = async (u) => {
    felfele++; utolsoCel = String(u);
    return new Response(valaszTorzs, { status: 200,
      headers: { 'Content-Type': 'application/json' } });
  };

  const varok = [];
  const ctx = { waitUntil: p => varok.push(p) };
  const hiv = async (ut, env) => {
    const r = await worker.fetch(
      new Request(ut, { headers: { Origin: EREDET } }), env, ctx);
    await Promise.all(varok.splice(0));      // a waitUntil-ok befejezese
    return r;
  };
  const at = cel => PROXY + '/?url=' + encodeURIComponent(cel);

  // ---- 1) tarolhato valasz: atmegy es eltarolodik ----
  cim('Worker: a ritkán változó választ megjegyzi');
  const kv = ujKV();
  const env = { TAROLT: kv };
  let r = await hiv(at(NB1('HolVanSalah')), env);
  jo(r.status === 200, 'a válasz átmegy (HTTP ' + r.status + ')');
  jo((await r.text()) === valaszTorzs, 'a törzs változatlan');
  jo(felfele === 1, 'egy kérés ment felfelé — ' + felfele);
  jo(kv.irasok === 1, 'egyszer tárolt — ' + kv.irasok + ' írás');
  const kulcs = [...kv.tar.keys()][0];
  jo(!!(kv.tar.get(kulcs).meta || {}).ido, 'az időbélyeg is elmentődött');

  // ---- 2) valtozatlan valasz: NEM ir ujra ----
  cim('Worker: változatlan válaszra nem ír');
  await hiv(at(NB1('HolVanSalah')), env);
  jo(kv.irasok === 1, 'továbbra is 1 írás — ' + kv.irasok
     + ' (a napi 1000-es keret miatt ez a lényeg)');

  // ---- 3) valtozas: ir ----
  cim('Worker: változásra ír');
  valaszTorzs = '{"data":[2]}';
  await hiv(at(NB1('HolVanSalah')), env);
  jo(kv.irasok === 2, 'most már 2 írás — ' + kv.irasok);
  jo(kv.tar.size === 1, 'ugyanaz a kulcs frissült, nem új jött létre — '
     + kv.tar.size + ' kulcs');

  // ---- 4) a gyorsitotar-toro belyeg nem csinal uj kulcsot ----
  cim('Worker: az fpl_ bélyeg nem szór szét kulcsokat');
  const kv2 = ujKV(), env2 = { TAROLT: kv2 };
  await hiv(at(PL_KERET + '?fpl_=111'), env2);
  await hiv(at(PL_KERET + '?fpl_=222'), env2);
  jo(kv2.tar.size === 1, 'egyetlen kulcs — ' + kv2.tar.size);
  jo(kv2.irasok === 1, 'a második nem írt újra (ugyanaz az adat) — ' + kv2.irasok);

  // ---- 5) a gyorsan valtozo PL elo pontot nem taroljuk ----
  cim('Worker: a percenként változó PL élő pontot nem tárolja');
  const kv3 = ujKV(), env3 = { TAROLT: kv3 };
  const r3 = await hiv(at(PL_ELO), env3);
  jo(r3.status === 200, 'a válasz ugyanúgy átmegy');
  jo(kv3.irasok === 0, 'egyetlen írás sem — ' + kv3.irasok);

  // ---- 6) /tarolt: azonnali valasz, felfele semmi ----
  cim('Worker: a /tarolt nem megy ki a hálózatra');
  const elotte = felfele;
  const t = await hiv(PROXY + '/tarolt?url=' + encodeURIComponent(NB1('HolVanSalah'))
                      + '&url=' + encodeURIComponent(NB1('Hoxha98')), env);
  jo(felfele === elotte, 'egyetlen kérés sem ment felfelé — ' + (felfele - elotte));
  const j = await t.json();
  jo(!!j[NB1('HolVanSalah')], 'a tárolt állás megjött');
  jo(j[NB1('HolVanSalah')].adat === '{"data":[2]}',
     'a LEGUTÓBBI lekérés adata jött, nem a korábbi');
  jo(!!j[NB1('HolVanSalah')].ido, 'időbélyeggel együtt');
  jo(!(NB1('Hoxha98') in j), 'amit még senki nem kért le, arra nincs sor');

  // ---- 7) kotes nelkul minden marad a regiben ----
  cim('Worker: KV-kötés nélkül a régi viselkedés');
  const elotte2 = felfele;
  const r4 = await hiv(at(NB1('samsonp')), {});
  jo(r4.status === 200 && (await r4.text()) === valaszTorzs,
     'a proxy ugyanúgy szolgál ki');
  jo(felfele === elotte2 + 1, 'a lekérés megtörtént');
  const t4 = await hiv(PROXY + '/tarolt?url=' + encodeURIComponent(NB1('samsonp')), {});
  jo((await t4.text()) === '{}', 'a /tarolt üres választ ad, nem hibát');

  // ---- 8) az eredet-ellenorzes a /tarolt-ra is all ----
  cim('Worker: a /tarolt sem szolgál ki idegen eredetet');
  const r5 = await worker.fetch(
    new Request(PROXY + '/tarolt?url=' + encodeURIComponent(NB1('HolVanSalah')),
                { headers: { Origin: 'https://valaki.mas' } }), env, ctx);
  jo(r5.status === 403, 'idegen eredet elutasítva (HTTP ' + r5.status + ')');

  await vege();
})();
