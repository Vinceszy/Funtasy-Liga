const { BASE, jo, cim, hibak, inditas, vege, apiKi } = require('./kozos');
// A Kulonbsegek nezet: gepen ket oszlop (kozos mindkettoben), mobilon egy
// kozos blokk + a ket szakvezeto kulon.
const szam = t => parseFloat((t.match(/[-+]?[\d.]*,?\d+/)||['0'])[0].replace('.','').replace(',','.'));

const nyit = async (p,w,h) => {
  const o = await p.context().newPage({});
  return o;
};
(async()=>{
  const br=await inditas();
  const hibak=[];
  for (const [w,h,cimke] of [[1000,1200,'GÉP'],[390,1700,'MOBIL']]){
    const p=await br.newPage({viewport:{width:w,height:h}});
    p.on('pageerror',e=>hibak.push(cimke+': '+e.message));
    for(const m of ['**mlsz.hu/**','**corsproxy.io/**','**allorigins**']) await p.route(m,r=>r.abort());
    await p.goto(BASE + 'nb1/'); await p.waitForSelector('#table tr');
    await p.evaluate(()=>showMatchRound('Bazsa','Csendi',4));
    // A modalra szukitunk (#mBody): a fooldali jatekoslista sorai UGYANAZT a
    // .plr osztalyt viselik, tehat egy oldal-szintu lekerdezes azokat is
    // beszamolna - a kozos jatekos harmadszor is elojonne a lista sorai
    // kozott, es a szamlalas hamisan bukna. (Igy is tortent, 2026-08-25.)
    await p.waitForSelector('#mBody .plr');
    console.log('=== '+cimke+' ===');
    await p.click('#elteresGomb'); await p.waitForTimeout(250);

    const lathatoNevek = await p.$$eval('#mBody .plr', ns=>ns.filter(n=>n.offsetParent!==null)
      .map(n=>n.querySelector('.nm').textContent.trim().split('▼')[0].trim()));
    // A kozos jatekost az ADATBOL vesszuk, nem bedrotozva: a nevsorrend-
    // valtas (vezeteknev elol) egyszer mar megbuktatta a bedrotozott nevet.
    const kozosNev = await p.evaluate(async () => {
      const j = await (await fetch('../keretek/4.json')).json();
      const b = new Set((j.squads['Bazsa']||[]).map(x=>x.name));
      return ((j.squads['Csendi']||[]).map(x=>x.name).find(n=>b.has(n))) || '(nincs kozos)';
    });
    if (cimke==='GÉP'){
      jo(lathatoNevek.filter(x=>x===kozosNev).length===2, 'a közös játékos MINDKÉT oszlopban ott van ('+kozosNev+')');
      jo(await p.locator('.mobilkozos').isVisible()===false, 'a mobil közös blokk gépen rejtve');
      const oszlopok = await p.$$eval('.sqcol', ns=>ns.map(n=>({
        fej:n.querySelector('h3').innerText.replace(/\n/g,' '),
        szakaszok:[...n.querySelectorAll('.szakasz')].map(x=>x.innerText),
        ossz:[...n.querySelectorAll('.osszesito')].map(x=>x.innerText.replace(/\n/g,' '))})));
      oszlopok.forEach((o,i)=>{
        jo(o.szakaszok.length===2, `${i+1}. oszlop: két szakasz (${o.szakaszok.join(' / ')})`);
        const [kozos,elt,vegso]=o.ossz.map(szam);
        jo(Math.abs(kozos+elt-vegso)<0.005 && Math.abs(vegso-szam(o.fej))<0.005,
           `${i+1}. oszlop összegei: ${kozos} + ${elt} = ${vegso} (fejléc ${szam(o.fej)}) — ${o.ossz.join(' | ')}`);
      });
    } else {
      jo(lathatoNevek.filter(x=>x===kozosNev).length===1, 'mobilon a közös játékos csak EGYSZER látszik');
      jo(await p.locator('.mobilkozos').isVisible()===true, 'a közös blokk külön áll mobilon');
      const sorrend = await p.evaluate(()=>[...document.querySelectorAll('.mobilkozos,.sqcol h3')]
        .filter(n=>n.offsetParent!==null)
        .map(n=>n.classList.contains('mobilkozos')?'KÖZÖS BLOKK':n.innerText.split('\n')[0]));
      jo(JSON.stringify(sorrend)===JSON.stringify(['KÖZÖS BLOKK','Bazsa','Csendi']),
         'sorrend: '+sorrend.join(' → '));
    }
    // a bontas tovabbra is nyilik
    await p.locator('#mBody .plr[data-acc]:visible').first().click(); await p.waitForTimeout(400);
    jo(await p.locator('.accpanel').count()===1, 'a pont-bontás nyílik');
    // kikapcsolas
    await p.click('#elteresGomb'); await p.waitForTimeout(250);
    jo(await p.locator('.szakasz').count()===0, 'kikapcsolva a megszokott keret-nézet jön vissza');
    await p.close();
  }
  cim('A közös játékos VEGYES forrásnál is megvan');
  // BEJELENTETT: "Csonginak es nekem nem ir kozos jatekost, pedig Lehoczki
  // mindkettonknel csere". Az elo meccs-nezet a KET keretet KULON keri le,
  // es ha csak az egyik jon meg, a masik a TAROLT marad. A ket forras viszont
  // MAS NEVALAKOT ad - a tarolt magyar sorrendet ("Lehoczki Bendegúz"), az
  // elo lekeres a keresztnev-vezeteknev alakot ("Bendegúz Lehoczki") -, es a
  // parositas NEV szerint ment: ilyenkor NULLA kozos jatekos jott ki.
  // Mostantol az AZONOSITO parosit, az mindket forrasban ugyanaz.
  {
    const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
    const err = []; p.on('pageerror', e => err.push(e.message));
    await apiKi(p);
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await p.waitForTimeout(1000);
    const m = await p.evaluate(async () => {
      const r = T.lastPlayedRound();
      const kt = await keretFordulo(r);
      const nevek = Object.keys(kt);
      // olyan par kell, akiknek VAN kozos jatekosuk
      const kulcs = x => szerepKulcs(x);
      let A = null, B = null;
      for (let i = 0; i < nevek.length && !A; i++)
        for (let j = i + 1; j < nevek.length; j++) {
          const a = new Set((kt[nevek[i]] || []).map(kulcs));
          if ((kt[nevek[j]] || []).some(x => a.has(kulcs(x)))) {
            A = nevek[i]; B = nevek[j]; break;
          }
        }
      if (!A) return null;
      const nyugati = n => { const q = n.split(' ');
        return q.length > 1 ? q.slice(1).concat(q[0]).join(' ') : n; };
      const elo = l => l.map(x => ({ ...x, name: nyugati(x.name) }));
      const db = (X, Y) => {
        MECCS = { h: A, v: B, A: X, B: Y, hp: null, vp: null, r: r, elo: true };
        meccsTest();
        const s = document.querySelector('.szuroinfo');
        return s ? parseInt(s.textContent) : 0;
      };
      return { par: A + ' vs ' + B,
               tarolt: db(kt[A], kt[B]),
               vegyes: db(kt[A], elo(kt[B])),
               mindketto: db(elo(kt[A]), elo(kt[B])) };
    });
    if (!m) jo(true, 'kihagyva: nincs olyan pár, akiknek közös játékosa van');
    else {
      jo(m.tarolt > 0, m.par + ': tárolt adatból ' + m.tarolt + ' közös játékos');
      jo(m.vegyes === m.tarolt,
         'VEGYES forrásnál (egyik élő, másik tárolt) ugyanannyi: ' + m.vegyes
         + ' — a névsorrend nem számít');
      jo(m.mindketto === m.tarolt,
         'mindkettő élő alakban is ugyanannyi: ' + m.mindketto);
    }
    jo(err.length === 0, 'nincs JS-hiba' + (err.length ? ': ' + err.join(' | ') : ''));
    await p.close();
  }

  console.log('pageerror:', hibak.length?hibak:'nincs');
  await br.close();
})();
