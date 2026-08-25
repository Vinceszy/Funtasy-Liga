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
  console.log('pageerror:', hibak.length?hibak:'nincs');
  await br.close();
})();
