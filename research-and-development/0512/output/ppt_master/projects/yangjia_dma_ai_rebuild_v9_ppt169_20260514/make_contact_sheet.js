const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const dir = path.join(__dirname, 'preview_png');
const files = fs.readdirSync(dir).filter(f => f.endsWith('.png')).sort();
const thumbW = 320;
const thumbH = 180;
const cols = 4;
const rows = Math.ceil(files.length / cols);
const sheetW = thumbW * cols;
const sheetH = thumbH * rows;

async function main() {
  const comps = [];
  for (let i = 0; i < files.length; i++) {
    const input = await sharp(path.join(dir, files[i])).resize(thumbW, thumbH).png().toBuffer();
    comps.push({ input, left: (i % cols) * thumbW, top: Math.floor(i / cols) * thumbH });
  }
  await sharp({ create: { width: sheetW, height: sheetH, channels: 3, background: '#EEF2F6' } })
    .composite(comps)
    .png()
    .toFile(path.join(__dirname, 'preview_contact_sheet.png'));
}

main().catch(err => { console.error(err); process.exit(1); });
