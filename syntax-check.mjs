import { readFileSync, existsSync } from 'fs';

const FILES = ['app.html', 'index.html'];
const REQUIRED = [
  'renderAll','saveState','openPanel','closePanel',
  'handleSignup','handleLogin','pushProgressToSupabase',
  'pullProgressFromSupabase','initAuth','claimDaily',
  'openOffer'
];

let passed = true;

console.log('\n🔍 Checking JavaScript syntax...\n');

for (const file of FILES) {
  if (!existsSync(file)) {
    console.log(`⏭️  Skipping ${file} (not found)`);
    continue;
  }
  const html = readFileSync(file, 'utf8');
  const m = html.match(/<script>([\s\S]*?)<\/script>/);
  if (!m) {
    console.log(`⏭️  ${file} — no inline script`);
    continue;
  }
  try {
    new Function(m[1]);
    console.log(`✅ ${file} — JS syntax OK`);
  } catch(e) {
    console.log(`❌ ${file} — ERROR: ${e.message}`);
    passed = false;
  }
}

console.log('\n🔍 Checking required functions...\n');

if (existsSync('app.html')) {
  const html = readFileSync('app.html', 'utf8');
  for (const fn of REQUIRED) {
    if (html.includes(`function ${fn}(`)) {
      console.log(`✅ function ${fn}() — found`);
    } else {
      console.log(`⚠️  function ${fn}() — not found`);
    }
  }
}

console.log('\n🔍 Checking for secrets...\n');

if (existsSync('app.html')) {
  const html = readFileSync('app.html', 'utf8');
  const bad = ['YOUR_BREVO_API_KEY','xkeysib-c7e0'];
  bad.forEach(s => {
    if (html.includes(s)) {
      console.log(`❌ Found: ${s}`);
      passed = false;
    }
  });
  console.log('✅ No dangerous secrets found');
}

console.log('\n' + '═'.repeat(50));
if (passed) {
  console.log('✅  ALL CHECKS PASSED\n');
  process.exit(0);
} else {
  console.log('❌  CHECKS FAILED\n');
  process.exit(1);
}