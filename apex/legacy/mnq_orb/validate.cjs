const fs = require('fs');
const { validatePineScript } = require('pinescript-v6-validator');
for (const f of process.argv.slice(2)) {
  const src = fs.readFileSync(f, 'utf8');
  const errs = validatePineScript(src);
  console.log(`== ${f}: ${errs.filter(e => e.severity === 0).length} errors, ${errs.filter(e => e.severity === 1).length} warnings, ${errs.filter(e => e.severity > 1).length} info`);
  const lines = src.split('\n');
  for (const e of errs) console.log(`  [${['ERR','WARN','INFO','HINT'][e.severity] || e.severity}] L${e.line}:${e.column} ${e.message}\n      > ${ (lines[e.line-1]||'').trim().slice(0,140)}`);
}
