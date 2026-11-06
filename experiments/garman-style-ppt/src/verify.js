// verify：生成后的 .pptx 质量闸门（不信生成代码，重新打开成品逐页检查）
// 1 页面文字逐字来自原文（模板用语、编号除外） 2 元素不出界 3 动画目标都存在
// 4 原文每段都在备注里 5 字号不小于 10pt 6 每页正文都有逐个淡入动画
const JSZip = require("jszip");
const SW = 12192000, SH = 6858000;
const TEMPLATE = new Set(["目录", "谢谢"]);
const unxml = (s) => s.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, "&");

async function verify(buf, P, plan) {
  const zip = await JSZip.loadAsync(buf);
  const paras = Object.values(P), errs = [], info = [];
  const slides = Object.keys(zip.files).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f)).sort((a, b) => +a.match(/\d+/)[0] - +b.match(/\d+/)[0]);
  let notesAll = "", fades = 0;
  for (const f of slides) {
    const i = +f.match(/\d+/)[0], xml = await zip.file(f).async("string"), at = `第 ${i} 页`;
    for (const m of xml.matchAll(/<a:t>([^<]*)<\/a:t>/g)) {
      const t = unxml(m[1]).trim();
      if (!t || TEMPLATE.has(t) || /^(0?\d{1,2}|[一二三四五六七八九十]{1,3})$/.test(t)) continue;
      if (!paras.some((p) => p.includes(t))) errs.push(`${at}：「${t}」在原文里找不到`);
    }
    for (const m of xml.matchAll(/<a:off x="(-?\d+)" y="(-?\d+)"\/><a:ext cx="(\d+)" cy="(\d+)"\/>/g)) {
      const [x, y, w, h] = m.slice(1).map(Number);
      if (x < 0 || y < 0 || x + w > SW + 2000 || y + h > SH + 2000) errs.push(`${at}：有元素超出页面（x=${(x / 914400).toFixed(2)}″ y=${(y / 914400).toFixed(2)}″）`);
    }
    for (const m of xml.matchAll(/sz="(\d+)"/g)) if (+m[1] < 1000) errs.push(`${at}：字号 ${+m[1] / 100}pt 小于 10pt`);
    const ids = new Set([...xml.matchAll(/<p:cNvPr id="(\d+)"/g)].map((a) => a[1]));
    for (const m of xml.matchAll(/<p:spTgt spid="(\d+)"\/>/g)) if (!ids.has(m[1])) errs.push(`${at}：动画指向不存在的元素 ${m[1]}`);
    const nf = (xml.match(/filter="fade"/g) || []).length; fades += nf;
    const type = plan.slides[i - 1] && plan.slides[i - 1].type;
    if (!nf) errs.push(`${at}（${type}）：没有逐个淡入动画`);
    const nr = Object.keys(zip.files).find((k) => k === `ppt/notesSlides/notesSlide${i}.xml`);
    if (nr) notesAll += [...(await zip.file(nr).async("string")).matchAll(/<a:t>([^<]*)<\/a:t>/g)].map((a) => unxml(a[1])).join("");
  }
  const miss = Object.entries(P).filter(([, t]) => !notesAll.includes(t)).map(([k]) => k);
  if (miss.length) errs.push(`备注里缺少原文段落：${miss.join("、")}`);
  info.push(`${slides.length} 页，淡入动画 ${fades} 个，原文 ${paras.length} 段全部在备注里${miss.length ? "（有缺失）" : ""}`);
  return { ok: !errs.length, errs, info };
}
module.exports = { verify };
