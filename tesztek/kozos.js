// Kozos resz a bongeszos tesztekhez: indulas, allitasok, adat-hamisitas.
// Minden teszt a VALODI repo-adaton fut (nincsenek fixtura-masolatok, amik
// elavulnanak); ahol kulonleges allapot kell, azt menet kozben allitjuk elo.
const PW_UT   = process.env.PLAYWRIGHT_MODUL || '/tmp/node_modules/playwright';
const CHROME  = process.env.CHROME_UT || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const BASE    = process.env.TESZT_BASE || 'http://127.0.0.1:8910/';

let chromium;
try { chromium = require(PW_UT).chromium; }
catch (e) {
  console.error('Playwright nem talalhato (' + PW_UT + ').');
  console.error('Allitsd be a PLAYWRIGHT_MODUL kornyezeti valtozot, vagy hagyd ki a bongeszos teszteket.');
  process.exit(2);
}

const hibak = [];
/** Egy allitas. Igaz -> OK, hamis -> HIBA (es a futas vegen 1-es kilepokod). */
const jo = (felt, cimke) => {
  console.log((felt ? 'OK   ' : 'HIBA ') + cimke);
  if (!felt) hibak.push(cimke);
  return !!felt;
};
const cim = t => console.log('\n--- ' + t + ' ---');
const inditas = () => chromium.launch({ executablePath: CHROME });
const vege = async br => { if (br) await br.close(); process.exit(hibak.length ? 1 : 0); };

/** A repobol jovo JSON-t menet kozben atirja (fixtura-fajlok nelkul).

    A fajlt LEMEZROL olvassuk, nem a helyi tesztszerveren at: a szerver a
    teljes tesztsor terhelese alatt neha eldobja a kapcsolatot, es akkor a
    teszt ELOFELTETELE veszett el - a teszt mas-mas allitasnal, felrevezeto
    uzenettel bukott (az "uzenetek" harom futasban harom kulonbozo helyen).
    Egy route.fetch-es ujraprobalkozo valtozat sem volt eleg. Halozati ut
    csak akkor marad, ha a keres nem repo-fajlra mutat. */
const fs = require('fs');
const GYOKER = require('path').join(__dirname, '..');
async function jsonAtir(page, minta, atalakit) {
  await page.route(minta, async route => {
    let j = null;
    try {
      const ut = decodeURIComponent(new URL(route.request().url()).pathname);
      j = JSON.parse(fs.readFileSync(require('path').join(GYOKER, '.' + ut), 'utf8'));
    } catch (e) { /* nem repo-fajl vagy nem JSON - jon a halozati ut */ }
    if (j == null) {
      const v = await route.fetch();
      try { j = await v.json(); } catch (e) { return route.fulfill({ response: v }); }
    }
    route.fulfill({ status: 200, contentType: 'application/json',
                    body: JSON.stringify(atalakit(j) || j) });
  });
}

/** Elo API-k elvagasa: csak a tarolt adatbol dolgozzon a lap. */
async function apiKi(page) {
  for (const m of ['**mlsz.hu/**', '**premierleague.com/**',
                   '**corsproxy.io/**', '**allorigins**']) await page.route(m, r => r.abort());
}

module.exports = { BASE, chromium, jo, cim, hibak, inditas, vege, jsonAtir, apiKi };
