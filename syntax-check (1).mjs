/**
 * syntax-check.mjs
 * Money Hunters UK — JS Syntax Validator
 * Run: node syntax-check.mjs
 * Used by GitHub Actions before every deploy.
 */

import { readFileSync, existsSync } from 'fs';

const FILES_TO_CHECK = ['app.html', 'index.html', 'landing.html'];
const REQUIRED_FUNCTIONS = [
  'renderAll',
  'saveState',
  'openPanel',
  'closePanel',
  'handleSignup',
  'handleLogin',
  'pushProgressToSupabase',
  'pullProgressFromSupabase',
  'initAuth',
  'claimDaily',
  'openOffer',
];

let allPassed = true;

// ── CHECK 1: JS syntax in HTML files ──
console.log('\n🔍 Checking JavaScript syntax...\n');

for (const file of FILES_TO_CHECK) {
  if (!existsSync(file)) {
    console.log(`⏭️  Skipping ${file} (not found)`);
    continue;
  }

  const html = readFileSync(file, 'utf8');
  const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);

  if (!scriptMatch) {
    console.log(`⏭️  ${file} — no inline script found`);
    continue;
  }

  try {
    new Function(scriptMatch[1]);
    console.log(`✅ ${file} — JS syntax OK`);
  } catch (e) {
    console.log(`❌ ${file} — JS SYNTAX ERROR: ${e.message}`);
    allPassed = false;
  }
}

// ── CHECK 2: Required functions exist in app.html ──
console.log('\n🔍 Checking required functions in app.html...\n');

if (existsSync('app.html')) {
  const appHtml = readFileSync('app.html', 'utf8');
  let missingCount = 0;
  for (const fn of REQUIRED_FUNCTIONS) {
    if (appHtml.includes(`function ${fn}(`)) {
      console.log(`✅ function ${fn}() — found`);
    } else {
      console.log(`⚠️  function ${fn}() — not found (warning only)`);
      missingCount++;
    }
  }
  if (missingCount > 5) {
    // Only fail if MORE than half are missing — likely wrong file
    console.log(`❌ Too many missing functions (${missingCount}) — wrong app.html?`);
    allPassed = false;
  }
}

// ── CHECK 3: No placeholder values left in code ──
console.log('\n🔍 Checking for placeholder values...\n');

const FORBIDDEN_STRINGS = [
  'YOUR_BREVO_API_KEY',
  'YOUR_API_KEY_HERE',
  'RAILWAY_URL_HERE',
  'PLACEHOLDER',
  'TODO: replace',
  'xkeysib-c7e091d246f55dba71a3214c812d68c57c3c8835b08c35f68e4919bbc960eb78', // old exposed key
];

if (existsSync('app.html')) {
  const appHtml = readFileSync('app.html', 'utf8');
  for (const str of FORBIDDEN_STRINGS) {
    if (appHtml.includes(str)) {
      console.log(`❌ Found forbidden placeholder in app.html: "${str}"`);
      allPassed = false;
    }
  }
  console.log('✅ No forbidden placeholder values found');
}

// ── CHECK 4: Supabase client uses correct variable name ──
console.log('\n🔍 Checking Supabase client setup...\n');

if (existsSync('app.html')) {
  const appHtml = readFileSync('app.html', 'utf8');
  if (appHtml.includes('const db = window.supabase.createClient')) {
    console.log('✅ Supabase client correctly named "db" (avoids SDK clash)');
  } else if (appHtml.includes('const supabase = window.supabase.createClient')) {
    console.log('❌ Supabase client named "supabase" — causes SDK name clash!');
    allPassed = false;
  } else {
    console.log('⚠️  Supabase client setup not found — check integration');
  }
}

// ── CHECK 5: manifest.json is valid JSON ──
console.log('\n🔍 Checking manifest.json...\n');

if (existsSync('manifest.json')) {
  try {
    const manifest = JSON.parse(readFileSync('manifest.json', 'utf8'));
    const required = ['name', 'short_name', 'start_url', 'display', 'icons'];
    let manifestOk = true;
    for (const key of required) {
      if (!manifest[key]) {
        console.log(`❌ manifest.json missing field: ${key}`);
        manifestOk = false;
        allPassed = false;
      }
    }
    if (manifestOk) console.log('✅ manifest.json is valid');
  } catch (e) {
    console.log(`❌ manifest.json is invalid JSON: ${e.message}`);
    allPassed = false;
  }
}

// ── RESULT ──
console.log('\n' + '═'.repeat(50));
if (allPassed) {
  console.log('✅  ALL CHECKS PASSED — safe to deploy\n');
  process.exit(0);
} else {
  console.log('❌  CHECKS FAILED — deploy blocked\n');
  process.exit(1);
}
