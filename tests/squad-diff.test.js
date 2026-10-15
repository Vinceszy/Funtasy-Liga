const { BASE, check, section, failures, launch, finish, blockApis } = require('./common');
// The Különbségek view: on desktop two columns (the shared players in both),
// on mobile one shared block + the two managers separately.
const num = t => parseFloat((t.match(/[-+]?[\d.]*,?\d+/)||['0'])[0].replace('.','').replace(',','.'));

(async()=>{
  const br=await launch();
  const pageErrors=[];
  for (const [w,h,label] of [[1000,1200,'DESKTOP'],[390,1700,'MOBILE']]){
    const p=await br.newPage({viewport:{width:w,height:h}});
    p.on('pageerror',e=>pageErrors.push(label+': '+e.message));
    for(const m of ['**mlsz.hu/**','**corsproxy.io/**','**allorigins**']) await p.route(m,r=>r.abort());
    await p.goto(BASE + 'nb1/'); await p.waitForSelector('#table tr');
    await p.evaluate(()=>showMatchRound('Bazsa','Csendi',4));
    // We narrow to the modal (#mBody): the rows of the home page player list
    // carry THE SAME .plr class, so a page-level query would count them too -
    // the shared player would turn up a third time among the list rows, and
    // the count would fail falsely. (That did happen in a live run.)
    await p.waitForSelector('#mBody .plr');
    console.log('=== '+label+' ===');
    await p.click('#elteresGomb'); await p.waitForTimeout(250);

    const visibleNames = await p.$$eval('#mBody .plr', ns=>ns.filter(n=>n.offsetParent!==null)
      .map(n=>n.querySelector('.nm').textContent.trim().split('▼')[0].trim()));
    // The shared player is taken FROM THE DATA, not hard-coded: the change of
    // name order (surname first) already broke the hard-coded name once.
    const sharedName = await p.evaluate(async () => {
      const j = await (await fetch('../keretek/4.json')).json();
      const b = new Set((j.squads['Bazsa']||[]).map(x=>x.name));
      return ((j.squads['Csendi']||[]).map(x=>x.name).find(n=>b.has(n))) || '(no shared player)';
    });
    if (label==='DESKTOP'){
      check(visibleNames.filter(x=>x===sharedName).length===2, 'the shared player is in BOTH columns ('+sharedName+')');
      check(await p.locator('.mobilkozos').isVisible()===false, 'the mobile shared block is hidden on desktop');
      const columns = await p.$$eval('.sqcol', ns=>ns.map(n=>({
        head:n.querySelector('h3').innerText.replace(/\n/g,' '),
        sections:[...n.querySelectorAll('.szakasz')].map(x=>x.innerText),
        totals:[...n.querySelectorAll('.osszesito')].map(x=>x.innerText.replace(/\n/g,' '))})));
      columns.forEach((o,i)=>{
        check(o.sections.length===2, `column ${i+1}: two sections (${o.sections.join(' / ')})`);
        const [shared,diff,final]=o.totals.map(num);
        check(Math.abs(shared+diff-final)<0.005 && Math.abs(final-num(o.head))<0.005,
           `column ${i+1} totals: ${shared} + ${diff} = ${final} (header ${num(o.head)}) — ${o.totals.join(' | ')}`);
      });
    } else {
      check(visibleNames.filter(x=>x===sharedName).length===1, 'on mobile the shared player is shown only ONCE');
      check(await p.locator('.mobilkozos').isVisible()===true, 'the shared block stands separately on mobile');
      const order = await p.evaluate(()=>[...document.querySelectorAll('.mobilkozos,.sqcol h3')]
        .filter(n=>n.offsetParent!==null)
        .map(n=>n.classList.contains('mobilkozos')?'SHARED BLOCK':n.innerText.split('\n')[0]));
      check(JSON.stringify(order)===JSON.stringify(['SHARED BLOCK','Bazsa','Csendi']),
         'order: '+order.join(' → '));
    }
    // the breakdown still opens
    await p.locator('#mBody .plr[data-acc]:visible').first().click(); await p.waitForTimeout(400);
    check(await p.locator('.accpanel').count()===1, 'the points breakdown opens');
    // switching off
    await p.click('#elteresGomb'); await p.waitForTimeout(250);
    check(await p.locator('.szakasz').count()===0, 'switched off, the usual squad view comes back');
    await p.close();
  }
  section('The shared player is found with MIXED sources too');
  // THE EXCLUDED BUG: "for Csongi and me it shows no shared player, although
  // Lehoczki is a substitute for both of us". The live match view fetches the
  // TWO squads SEPARATELY, and if only one arrives, the other stays the
  // STORED one. The two sources, however, give a DIFFERENT NAME FORM - the
  // stored one the Hungarian order ("Lehoczki Bendegúz"), the live fetch the
  // first name-surname form ("Bendegúz Lehoczki") -, and the pairing went by
  // NAME: in that case ZERO shared players came out.
  // From now on the ID pairs them, which is the same in both sources.
  {
    const p = await br.newPage({ viewport: { width: 1300, height: 1000 } });
    const err = []; p.on('pageerror', e => err.push(e.message));
    await blockApis(p);
    await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#table tr', { timeout: 20000 });
    await p.waitForTimeout(1000);
    const m = await p.evaluate(async () => {
      const r = T.lastPlayedRound();
      const squads = await roundSquads(r);
      const names = Object.keys(squads);
      // we need a pair who DO have a shared player
      const key = x => roleKey(x);
      let A = null, B = null;
      for (let i = 0; i < names.length && !A; i++)
        for (let j = i + 1; j < names.length; j++) {
          const a = new Set((squads[names[i]] || []).map(key));
          if ((squads[names[j]] || []).some(x => a.has(key(x)))) {
            A = names[i]; B = names[j]; break;
          }
        }
      if (!A) return null;
      const western = n => { const q = n.split(' ');
        return q.length > 1 ? q.slice(1).concat(q[0]).join(' ') : n; };
      const live = l => l.map(x => ({ ...x, name: western(x.name) }));
      const count = (X, Y) => {
        MATCH = { h: A, v: B, A: X, B: Y, hp: null, vp: null, r: r, live: true };
        matchBody();
        const s = document.querySelector('.szuroinfo');
        return s ? parseInt(s.textContent) : 0;
      };
      return { pair: A + ' vs ' + B,
               stored: count(squads[A], squads[B]),
               mixed: count(squads[A], live(squads[B])),
               bothLive: count(live(squads[A]), live(squads[B])) };
    });
    if (!m) check(true, 'skipped: there is no pair who have a shared player');
    else {
      check(m.stored > 0, m.pair + ': ' + m.stored + ' shared players from the stored data');
      check(m.mixed === m.stored,
         'with MIXED sources (one live, the other stored) the same number: ' + m.mixed
         + ' — the name order does not matter');
      check(m.bothLive === m.stored,
         'the same number with both in the live form too: ' + m.bothLive);
    }
    check(err.length === 0, 'no JS error' + (err.length ? ': ' + err.join(' | ') : ''));
    await p.close();
  }

  console.log('pageerror:', pageErrors.length?pageErrors:'none');
  // finish() sets the exit code from the failed checks; without it a failed
  // assertion would still end the run with exit code 0.
  await finish(br);
})();
