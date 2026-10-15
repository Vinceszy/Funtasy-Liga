/* ==========================================================================
   bookmarklet-source.js - the READABLE source of the FALLBACK squad-saving
   bookmarklet
   ==========================================================================

   This file does not run anywhere. What goes into the browser is the
   content of bookmarklet.txt; this is the same code in a form meant for
   human eyes, so that changes are not made in the percent-encoded one-line
   version.

   TO CHANGE IT:
     1. edit this file
     2. run:  python3 bookmarklet-build.py
     3. the script regenerates bookmarklet.txt
     4. the bookmark in the browser has to be updated by hand with the new
        content (the bookmarklet runs from the browser's own copy)

   The token is a placeholder here too (IDE_A_TOKEN). NEVER commit a real
   token into this file.

   The squads are collected by GitHub Actions (collect.py) - this bookmarklet
   is only a fallback in case the server-side route breaks.
   The texts it shows are Hungarian on purpose: it runs in the browser of
   the league's members.
   ========================================================================== */

// ==BOOKMARKLET-START==
(async()=>{ const TOKEN='IDE_A_TOKEN';
const OWNER='Vinceszy',REPO='Funtasy-Liga',BRANCH='main';
const M={"Katyul":"peterkmrs","Bence":"Dill Dough","Sámsi":"samsonp","Vince":"HolVanSalah","Bazsa":"Hoxha98","Csongi":"szcsngr","Csendi":"cspeti93","Ádám":"siuu_1885"};
const API='https'+'://fantasy-api.mlsz.hu/competitions/3/';
const GH='https'+'://api.github.com/repos/'+OWNER+'/'+REPO+'/contents/';
const INC='position,position.alternatives,competition_player,competition_player.team,competition_player.countries,summary_statistics';
const INC2='position,position.alternatives,competition_player,competition_player.countries,summary_statistics';
const rid=n=>75+2*n;
const box=document.createElement('div');
box.style.cssText='position:fixed;z-index:2147483647;right:16px;bottom:16px;background:#12291D;color:#F2EFE6;border:2px solid #FFB020;border-radius:8px;padding:14px 18px;font:13px system-ui;max-width:380px;white-space:pre-line;box-shadow:0 8px 30px rgba(0,0,0,.5)';
document.body.appendChild(box);
const say=t=>{box.textContent=t;};
try{ if(!location.host.endsWith('mlsz.hu')){say('Ezt a fantasy.mlsz.hu oldalon kell futtatni!');setTimeout(()=>box.remove(),6000);return;} const hdr={Authorization:'Bearer '+TOKEN,Accept:'application/vnd.github+json'};
const get=async u=>{const r=await fetch(u,{credentials:'include'});if(!r.ok)throw new Error('HTTP '+r.status);return r.json();};
const isHun=cp=>/magyar|hungar|"HUN"/i.test(JSON.stringify(cp.countries||cp.country||''));
say('Meglévő adatok betöltése…');
let hist={rounds:{}},sha=null;
const hr=await fetch(GH+'squad_history.json?ref='+BRANCH,{headers:hdr});
if(hr.ok){const m=await hr.json();sha=m.sha;try{hist=JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(m.content.replace(/\n/g,'')),c=>c.charCodeAt(0))));}catch(e){}} if(!hist.rounds)hist.rounds={};
say('Azonosítók és fordulók…');
const ids={};let last=0;
for(const [n,u] of Object.entries(M)){ const j=await get(API+'rankings?include=user_team.user.id,rounds&per_page=5&filter[search]='+encodeURIComponent(u));
const row=(j.data||[]).find(d=>d.user_team&&d.user_team.user&&d.user_team.user.username===u)||(j.data||[])[0];
if(!row)continue;
ids[n]=row.user_team.user.id;
((row.user_team.round_statistics)||[]).forEach(s=>{if(s.points&&s.round_number>last)last=s.round_number;});
} const need=[];for(let r=1;r<=last;r++){const e=hist.rounds[r];if(!e||Object.keys(e).length<Object.keys(ids).length)need.push(r);} if(!need.length){say('Minden forduló naprakész (1–'+last+').');setTimeout(()=>box.remove(),6000);return;} for(const R of need){ hist.rounds[R]=hist.rounds[R]||{};
for(const [n,id] of Object.entries(ids)){ say('Lekérés: '+R+'. forduló · '+n);
try{ let dd=(await get(API+'user-team-players-history?include='+encodeURIComponent(INC)+'&filter[user_id]='+id+'&filter[round_id]='+rid(R))).data||[];
if(!dd[0]||!dd[0].position){ const d2=(await get(API+'user-team-players-history?include='+encodeURIComponent(INC2)+'&filter[user_id]='+id+'&filter[round_id]='+rid(R))).data||[];
const pb={};d2.forEach(x=>pb[x.id]=x.position);dd.forEach(x=>{if(!x.position)x.position=pb[x.id];});
} hist.rounds[R][n]=dd.map(d=>{const cp=d.competition_player||{},po=d.position||{};return{ name:[cp.first_name,cp.last_name].filter(Boolean).join(' ')||('#'+(cp.id||d.id)), team:(cp.team&&(cp.team.short_name||cp.team.name))||'', pos:po.monogram||po.name||'', u21:!!cp.is_u21,hun:isHun(cp), price:(cp.current_round&&cp.current_round.market_price)||null, cap:!!d.is_captain,sub:d.type==='substitutes', week:(d.summary_statistics||{}).weekly_points||0, total:(d.summary_statistics||{}).competition_points||0};});
}catch(e){console.warn(R+'/'+n,e.message);} await new Promise(s=>setTimeout(s,120));
} } say('Mentés a GitHubra…');
const b64=s=>btoa(String.fromCharCode.apply(null,new TextEncoder().encode(s)));
const stamp=new Date().toISOString();
hist.updated=stamp;
const put=async(path,obj,sh)=>{ let s2=sh;
if(s2===undefined){const r=await fetch(GH+path+'?ref='+BRANCH,{headers:hdr});if(r.ok)s2=(await r.json()).sha;} const body={message:'Keret-frissítés ('+need.join(', ')+'. forduló)',content:b64(JSON.stringify(obj)),branch:BRANCH};
if(s2)body.sha=s2;
const w=await fetch(GH+path,{method:'PUT',headers:hdr,body:JSON.stringify(body)});
if(!w.ok)throw new Error(path+': HTTP '+w.status);
};
await put('squad_history.json',hist,sha);
await put('squads.json',{updated:stamp,squads:hist.rounds[last]||{}});
say('✔ Kész — mentve: '+need.join(', ')+'. forduló.\nAz oldal 1 percen belül frissül.');
setTimeout(()=>box.remove(),10000);
}catch(e){say('Hiba: '+e.message);setTimeout(()=>box.remove(),20000);} })();
