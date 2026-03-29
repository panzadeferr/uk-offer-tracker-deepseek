const fs = require('fs');
let html = fs.readFileSync('app.html', 'utf8');

const cats = {
  'chase-uk':'bank','lloyds-bank':'bank','first-direct':'bank','natwest':'bank',
  'santander':'bank','barclays':'bank','co-operative-bank':'bank','monzo':'bank',
  'revolut':'bank','zopa-biscuit':'bank','ifast-global-bank':'bank',
  'freetrade':'invest','robinhood-uk':'invest','webull':'invest','wealthify':'invest',
  'wealthyhood':'invest','ig-trading':'invest','plum':'invest','pensionbee':'invest','moneybox':'invest',
  'topcashback':'cashback','quidco':'cashback','rakuten':'cashback','slide':'cashback','complete-savings':'cashback',
  'airtime-rewards':'gift','cheddar':'gift','jam-doughnut':'gift','everup':'gift','nx-rewards':'gift',
  'tide':'business','worldfirst':'business','amex-business-platinum':'business',
  'freecash':'earn','swagbucks':'earn','gemsloot':'earn','cash-in-style':'earn',
  'lebara-mobile':'mobile',
  'octopus-energy':'travel','trainpal':'travel','wise':'travel','avios-british-airways':'travel',
  'costa-coffee':'freebie','zilch':'freebie','glint-pay':'freebie','curve-pay':'freebie','trading-212':'freebie'
};

let changed = 0;
for (const [id, cat] of Object.entries(cats)) {
  const escaped = id.replace(/-/g, '\\-');
  const pattern = new RegExp('(\\{\\s*id:"' + escaped + '",\\s*)(name:)', 'g');
  const before = html;
  html = html.replace(pattern, (m, p1, p2) => p1 + 'category:"' + cat + '", ' + p2);
  if (html !== before) changed++;
}

// Replace the inferCategory function with the simple version
html = html.replace(
  /function inferCategory\(offer\) \{[\s\S]*?return "freebie";\s*\}/,
  'function inferCategory(offer) {\n      return offer.category || \'freebie\';\n    }'
);

fs.writeFileSync('app.html', html, 'utf8');
console.log('Done. Categories added to ' + changed + ' of ' + Object.keys(cats).length + ' offers.');
