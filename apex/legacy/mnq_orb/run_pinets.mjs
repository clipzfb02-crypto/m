import fs from 'fs';
import { PineTS } from 'pinets';
const [,, scriptPath, dataPath, outPath] = process.argv;
const src = fs.readFileSync(scriptPath, 'utf8');
const candles = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const MNQ = { current_contract: 'MNQZ2025', description: 'Micro E-mini Nasdaq-100', isin: '', main_tickerid: 'CME_MINI:MNQ1!', prefix: 'CME_MINI',
  root: 'MNQ', ticker: 'MNQ1!', tickerid: 'CME_MINI:MNQ1!', type: 'futures', basecurrency: '', country: 'US', currency: 'USD', timezone: 'America/Chicago',
  employees: 0, industry: '', sector: '', shareholders: 0, shares_outstanding_float: 0, shares_outstanding_total: 0, expiration_date: 0,
  session: '1700-1600', volumetype: 'base', mincontract: 1, minmove: 1, mintick: 0.25, pointvalue: 2, pricescale: 4,
  recommendations_buy: 0, recommendations_buy_strong: 0, recommendations_date: 0, recommendations_hold: 0, recommendations_sell: 0, recommendations_sell_strong: 0,
  recommendations_total: 0, target_price_average: 0, target_price_date: 0, target_price_estimates: 0, target_price_high: 0, target_price_low: 0, target_price_median: 0 };
const provider = {
  async getMarketData() { return candles; },
  async getSymbolInfo() { return MNQ; },
  configure() {}
};
const pineTS = new PineTS(provider, 'CME_MINI:MNQ1!', '5');
const t0 = Date.now();
const res = await pineTS.run(src);
const out = {};
for (const [k, v] of Object.entries(res.plots || {})) out[k] = (v.data || v).map(p => (p && typeof p === 'object' && 'value' in p) ? p.value : p);
fs.writeFileSync(outPath, JSON.stringify(out));
console.log('ran in', Date.now() - t0, 'ms');
