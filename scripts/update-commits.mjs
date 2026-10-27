// Writes the commit count into the banners, the Treato card and its generator. Usage: node scripts/update-commits.mjs <count>
import { readFileSync, writeFileSync } from "node:fs";

const n = Number(process.argv[2]);
if (!Number.isInteger(n) || n <= 0) throw new Error(`bad count: ${process.argv[2]}`);
const exact = n.toLocaleString("en-US");
const about = (Math.floor(n / 100) * 100).toLocaleString("en-US");

function edit(file, rules) {
  const before = readFileSync(file, "utf8");
  let after = before;
  for (const [re, to] of rules) {
    if (!re.test(after)) throw new Error(`${file}: pattern not found: ${re}`);
    after = after.replace(re, to);
  }
  if (after !== before) writeFileSync(file, after);
}

const sentence = [/about [\d,]+ commits since March 2025/, `about ${about} commits since March 2025`];
edit("assets/treato.svg", [
  sentence,
  [/(count commits<\/text><text [^>]*>)[\d,]+\+?(<\/text>)/, `$1${exact}$2`],
]);
for (const theme of ["light", "dark"]) {
  edit(`assets/banner-${theme}.svg`, [[/(<tspan class="n" id="commits">)[\d,]+(<\/tspan>)/, `$1${exact}$2`]]);
}
edit("scripts/make_svgs.py", [sentence, [/\("commits", "[\d,]+\+?"\)/, `("commits", "${exact}")`]]);
console.log(`commit counter: ${exact}`);
