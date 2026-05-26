const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const project = __dirname;
const inDir = path.join(project, 'svg_output');
const outDir = path.join(project, 'preview_png');
fs.mkdirSync(outDir, { recursive: true });

async function main() {
  const files = fs.readdirSync(inDir).filter(f => f.endsWith('.svg')).sort();
  for (const file of files) {
    let svg = fs.readFileSync(path.join(inDir, file), 'utf8');
    svg = svg.replace(/href="\.\.\/images\/([^"]+)"/g, (_, name) => {
      const img = fs.readFileSync(path.join(project, 'images', name));
      const ext = path.extname(name).slice(1).toLowerCase();
      const mime = ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : 'image/png';
      return `href="data:${mime};base64,${img.toString('base64')}"`;
    });
    const out = path.join(outDir, file.replace('.svg', '.png'));
    await sharp(Buffer.from(svg), { density: 144 }).resize(1280, 720).png().toFile(out);
    console.log(out);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
