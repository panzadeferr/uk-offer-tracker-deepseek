const fs = require('fs');
const path = require('path');

// Read the app.html file
const filePath = path.join(__dirname, 'app.html');
let content = fs.readFileSync(filePath, 'utf8');

// Function to infer category (same as in the JavaScript)
function inferCategory(offer) {
  const text = `${offer.name} ${offer.badge} ${offer.desc}`.toLowerCase();
  if (/(bank|switch|current account|pension|biscuit)/.test(text)) return 'bank';
  if (/(invest|share|trading|savings|avios|gold)/.test(text)) return 'invest';
  if (/cashback/.test(text)) return 'cashback';
  if (/(gift|airtime|jam doughnut|cheddar|everup)/.test(text)) return 'gift';
  if (/(business|amex|worldfirst|tide)/.test(text)) return 'business';
  if (/(earn|survey|task|sb|gems)/.test(text)) return 'earn';
  if (/(mobile|sim|lebara|app)/.test(text)) return 'mobile';
  if (/(travel|transfer|energy|utilities)/.test(text)) return 'travel';
  return 'freebie';
}

// Find the offers array in the content
const offersStart = content.indexOf('const offers = [');
if (offersStart === -1) {
  console.error('Could not find offers array');
  process.exit(1);
}

// Find the end of the offers array
let bracketCount = 0;
let i = offersStart;
for (; i < content.length; i++) {
  if (content[i] === '[') bracketCount++;
  if (content[i] === ']') {
    bracketCount--;
    if (bracketCount === 0) {
      break;
    }
  }
}

const offersEnd = i + 1;
const offersSection = content.substring(offersStart, offersEnd);

// Split into lines and process each offer
const lines = offersSection.split('\n');
let newOffersSection = '';

for (let line of lines) {
  // Check if line contains an offer object
  if (line.includes('id:"') && line.includes('name:"')) {
    // Extract offer data
    const idMatch = line.match(/id:"([^"]+)"/);
    const nameMatch = line.match(/name:"([^"]+)"/);
    const badgeMatch = line.match(/badge:"([^"]+)"/);
    const descMatch = line.match(/desc:"([^"]+)"/);
    
    if (idMatch && nameMatch) {
      const offer = {
        name: nameMatch[1],
        badge: badgeMatch ? badgeMatch[1] : '',
        desc: descMatch ? descMatch[1] : ''
      };
      
      const category = inferCategory(offer);
      
      // Add category before the closing brace
      if (line.includes('},') || line.includes('}')) {
        // Find the last comma before the closing brace
        const lastCommaIndex = line.lastIndexOf(',');
        if (lastCommaIndex !== -1) {
          line = line.substring(0, lastCommaIndex + 1) + ` category:'${category}',` + line.substring(lastCommaIndex + 1);
        } else {
          // If no comma, add before the closing brace
          const braceIndex = line.indexOf('}');
          if (braceIndex !== -1) {
            line = line.substring(0, braceIndex) + ` category:'${category}',` + line.substring(braceIndex);
          }
        }
      }
    }
  }
  newOffersSection += line + '\n';
}

// Replace the offers section in the content
content = content.substring(0, offersStart) + newOffersSection + content.substring(offersEnd);

// Write back to file
fs.writeFileSync(filePath, content, 'utf8');
console.log('Successfully added category fields to all offers');