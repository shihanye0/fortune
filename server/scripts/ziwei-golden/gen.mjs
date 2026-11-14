import { astro } from 'iztro';
import { Solar } from 'lunar-javascript';
import fs from 'node:fs';

const shichen = (h) => Math.floor((h + 1) / 2) % 12;
const cases = [];
for (let y = 1984; y <= 1993; y++) cases.push({ y, m: 6, d: 15, h: 10, g: 1 - (y - 1984) % 2 });
for (let h = 0; h <= 22; h++) cases.push({ y: 1987, m: 6, d: 1, h, g: 0 });
cases.push({ y: 1987, m: 6, d: 1, h: 23, g: 0 });
// leap month scan (max 8 cases, early+late day)
const seen = new Set();
for (let y = 2000; y <= 2026; y++) {
  for (let m = 1; m <= 12; m++) {
    const lmn = Solar.fromYmd(y, m, 15).getLunar().getMonth();
    if (lmn < 0 && !seen.has(y + '-' + m)) {
      seen.add(y + '-' + m);
      cases.push({ y, m, d: 5, h: 10, g: 1 });
      cases.push({ y, m, d: 25, h: 14, g: 0 });
    }
  }
}
console.log('cases:', cases.length);
// map iztro astrolabe to our expected format
const mapChart = (y, m, d, h, g) => {
  const t = shichen(h);
  const a = astro.bySolar(`${y}-${m}-${d}`, t, g ? '男' : '女', true, 'zh-CN');
  return {
    soul: a.earthlyBranchOfSoulPalace,
    body: a.earthlyBranchOfBodyPalace,
    five_elements: a.fiveElementsClass,
    ju: parseInt(a.fiveElementsClass[1], 10),
    ming_zhu: a.soul,
    shen_zhu: a.body,
    palaces: a.palaces.map((p) => ({
      name: p.name, branch: p.earthlyBranch, stem: p.heavenlyStem,
      major: p.majorStars.map((s) => ({ n: s.name, b: s.brightness || null, m: s.mutagen || null })),
      minor: p.minorStars.map((s) => ({ n: s.name, b: s.brightness || null, m: s.mutagen || null })),
    })),
    da_xian: a.palaces.map((p) => p.decadal?.range || null),
  };
};
const out = [];
for (const c of cases) {
  const exp = mapChart(c.y, c.m, c.d, c.h, c.g);
  out.push({ birth: c, expected: exp });
}
fs.writeFileSync('../../tests/fixtures/ziwei_golden.json', JSON.stringify(out, null, 1));
console.log('written', out.length, 'golden cases');
