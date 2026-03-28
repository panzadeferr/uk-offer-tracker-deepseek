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

// Parse each offer and add category
const lines = offersSection.split('\n');
let newOffersSection = '';
let currentOffer = '';
let inOffer = false;

for (let line of lines) {
  // Check if line starts an offer object
  if (line.trim().startsWith('{') && line.includes('id:')) {
    inOffer = true;
    currentOffer = line;
  } else if (inOffer) {
    currentOffer += '\n' + line;
    
    // Check if this line ends the offer object
    if (line.trim().endsWith('},') || line.trim().endsWith('}')) {
      inOffer = false;
      
      // Parse the offer object to extract fields
      const offerMatch = currentOffer.match(/id:"([^"]+)"/);
      if (offerMatch) {
        const offerId = offerMatch[1];
        
        // Extract name, badge, and desc for category inference
        const nameMatch = currentOffer.match(/name:"([^"]+)"/);
        const badgeMatch = currentOffer.match(/badge:"([^"]+)"/);
        const descMatch = currentOffer.match(/desc:"([^"]+)"/);
        
        const offer = {
          name: nameMatch ? nameMatch[1] : '',
          badge: badgeMatch ? badgeMatch[1] : '',
          desc: descMatch ? descMatch[1] : ''
        };
        
        const category = inferCategory(offer);
        
        // Add category field before the closing brace
        // Find the last property before the closing brace
        const lines = currentOffer.split('\n');
        let newLines = [];
        for (let i = 0; i < lines.length; i++) {
          newLines.push(lines[i]);
          // Check if this line ends with a comma (property line) and next line is closing brace
          if (lines[i].trim().endsWith(',') && i + 1 < lines.length && lines[i + 1].trim() === '}') {
            // Add category property before the closing brace
            newLines.push(`  category:'${category}',`);
          }
        }
        currentOffer = newLines.join('\n');
      }
      
      newOffersSection += currentOffer + '\n';
      currentOffer = '';
    }
  } else {
    newOffersSection += line + '\n';
  }
}

// Replace the offers section in the content
content = content.substring(0, offersStart) + newOffersSection + content.substring(offersEnd);

// Write back to file
fs.writeFileSync(filePath, content, 'utf8');
console.log('Successfully added category fields to all offers');