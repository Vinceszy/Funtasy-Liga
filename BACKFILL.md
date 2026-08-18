# Visszamenőleges keret-gyűjtés (1–4. forduló)

Az automata a mostani fordulótól kezdve mindent elment. A korábbi fordulók keretei
csak kézzel pótolhatók — ehhez az alábbi kis szkript adja ki készen a JSON-t.

## Így csináld

1. Nyisd meg a **https://fantasy.mlsz.hu/** oldalt (bejelentkezve), és nyomj **F12 → Console**.
2. Másold be az alábbi szkriptet, Enter.
3. A konzol kiírja a kész JSON-blokkot — másold ki (jobb klikk → Copy object).
4. A repóban a `squad_history.json` fájlban a `"rounds"` alá illeszd be az adott forduló
   számával kulcsolva, pl. `"4": { ...ide a kimásolt objektum... }`.

```js
(async () => {
  const MEMBERS = {"Katyul":"peterkmrs","Bence":"Dill Dough","Sámsi":"samsonp","Vince":"HolVanSalah",
                   "Bazsa":"Hoxha98","Csongi":"szcsngr","Csendi":"cspeti93","Ádám":"siuu_1885"};
  const C = 3, out = {};
  const dn = (o,d=0) => { if(!o||typeof o!=='object'||d>6) return null;
    const f=o.first_name,l=o.last_name; if(f||l) return [f,l].filter(Boolean).join(' ');
    for(const k of ['name','short_name']) if(typeof o[k]==='string'&&o[k].trim()) return o[k].trim();
    for(const k in o){ const r=dn(o[k],d+1); if(r) return r; } return null; };
  for (const [name, uname] of Object.entries(MEMBERS)) {
    const rk = await (await fetch(`https://fantasy-api.mlsz.hu/competitions/${C}/rankings?include=user_team.user.id&per_page=5&filter[search]=${encodeURIComponent(uname)}`)).json();
    const row = (rk.data||[]).find(d=>d.user_team?.user?.username===uname) || rk.data?.[0];
    const id = row?.user_team?.user?.id; if(!id){ console.warn('nincs id:', uname); continue; }
    const j = await (await fetch(`https://fantasy-api.mlsz.hu/competitions/${C}/user-team-players-history?include=competition_player.player,competition_player.team&filter[user_id]=${id}`)).json();
    out[name] = (j.data||[]).map(d => ({
      name: dn(d.competition_player) || ('#'+(d.competition_player_id||d.id)),
      team: d.competition_player?.team?.short_name || d.competition_player?.team?.name || '',
      cap: !!d.is_captain, sub: d.type==='substitutes',
      week: d.summary_statistics?.weekly_points ?? 0,
      total: d.summary_statistics?.competition_points ?? 0
    }));
    console.log(name, out[name].length, 'fő');
  }
  console.log('--- MÁSOLD KI EZT ---');
  console.log(JSON.stringify(out));
})();
```

**Fontos:** ez mindig az *aktuális* keretet adja vissza, tehát a hét lezárása után,
de az új forduló piacnyitása előtt érdemes lefuttatni, ha egy adott fordulót akarsz rögzíteni.
