// 实验版：分页方案校验 + 排版生成
// 新增：StyleEngine（风格 × 配色）、四种具名版式（quote / timeline / stat / compare）、
//       所有页面主要内容逐个「淡入」出现、生成后 verify 质量闸门（见 verify.js）。
const pptxgen = require("pptxgenjs");
const { postProcess } = require("./post.js");
const { THEMES, DEFAULT_THEME } = require("./themes.js");
const { STYLES, resolve } = require("./styles.js");

const W = 13.333, H = 7.5, M = 0.75, FONT = "Microsoft YaHei";
const TYPES = ["cover", "toc", "section", "cards", "text", "quote", "timeline", "stat", "compare", "end"];
const TOP = 2.2; // 内容区起点

// ---------- 文字测量（按微软雅黑估算，留 12% 余量） ----------
const em = (s) => [...String(s)].reduce((a, c) => a + (/[\u0000-ÿ]/.test(c) ? (/[A-Z]/.test(c) ? 0.62 : c === " " ? 0.3 : 0.55) : 1), 0);
const lines = (s, pt, wIn) => Math.max(1, Math.ceil((em(s) * pt / 72) * 1.12 / wIn));
function fit(s, wIn, hIn, max, min, ls = 1.25) {
  for (let pt = max; pt >= min; pt -= 1) if (lines(s, pt, wIn) * pt * ls / 72 <= hIn) return pt;
  return null;
}

// ---------- 序号 ----------
const ORD = /^\s*(?:第[一二三四五六七八九十百零〇两\d]+[章节部篇讲课单元步]分?\s*[、，,.．:：]?|[（(][一二三四五六七八九十百零〇\d]+[)）]\s*[、.．]?|[一二三四五六七八九十百零〇]+\s*[、.．]|\d{1,3}\s*[、．]|\d{1,3}\s*[.)）](?!\d)|[①-⑳]|[A-Za-z]\s*[、.．](?![A-Za-z\d]))\s*/;
function dropOrdinal(t) {
  const m = ORD.exec(t || "");
  return m && m[0].length < t.length ? t.slice(m[0].length) : t;
}
const showNo = (no) => (/^\d$/.test(String(no)) ? "0" + no : String(no));

// ---------- 版面几何（校验和生成共用） ----------
const G = {
  cols: (k, gap) => { const w = (W - 2 * M - gap * (k - 1)) / k; return Array.from({ length: k }, (_, j) => ({ x: M + j * (w + gap), w })); },
  cardH: (concl) => (concl ? 3.5 : 4.3),
  card: { num: 0.28, head: 1.05, headH: 1.05, body: 2.2 },
  tl: { axis: 2.85, head: 3.45, headH: 0.95, body: 4.45 },
  stat: { label: 0.3, value: 0.8, valueH: 1.4, body: 2.35 },
};

// ---------- 校验 ----------
function check(doc, plan) {
  const P = applyCorrections(doc, plan).P;
  const errs = [], warns = [];
  const at = (i, k) => `第 ${i + 1} 页${k ? "「" + k + "」" : ""}`;
  const ex = (ref, where) => {
    if (!Array.isArray(ref) || ref.length !== 2) { errs.push(`${where}：摘句格式应为 ["段落编号", "原文摘句"]`); return ""; }
    if (!P[ref[0]]) { errs.push(`${where}：没有段落 ${ref[0]}`); return ""; }
    if (!P[ref[0]].includes(ref[1])) errs.push(`${where}：「${ref[1]}」不是 ${ref[0]} 中的原文（必须逐字摘取，不能改写）`);
    return ref[1];
  };
  const used = [];
  const take = (ids, where) => (ids || []).forEach((id) => { if (!P[id]) errs.push(`${where}：备注引用了不存在的段落 ${id}`); used.push(id); });
  const len = (t, n, where) => { if (t && em(t) > n) errs.push(`${where}超过 ${n} 字，请换短一些的摘句`); };
  const fits = (t, w, h, max, min, ls, where) => { if (t && !fit(t, w, h, max, min, ls)) errs.push(`${where}太长放不下，请换更短的摘句`); };
  const range = (arr, a, b, where, what) => { const k = (arr || []).length; if (k < a || k > b) { errs.push(`${where}：${what}要 ${a}–${b} 个（现在 ${k} 个）`); return false; } return true; };
  if (!plan || !Array.isArray(plan.slides) || !plan.slides.length) return { ok: false, errs: ["方案里没有 slides"], warns };
  if (plan.footer) ex(plan.footer, "页脚 footer");
  if (plan.theme !== undefined && !THEMES[plan.theme]) errs.push(`theme 配色「${plan.theme}」不存在，只能用：${Object.keys(THEMES).join("、")}`);
  if (plan.design !== undefined && !STYLES[plan.design]) errs.push(`design 风格「${plan.design}」不存在，只能用：${Object.keys(STYLES).join("、")}`);
  plan.slides.forEach((s, i) => {
    if (!TYPES.includes(s.type)) { errs.push(`${at(i)}：页面类型 ${s.type} 不存在，只能用 ${TYPES.join("、")}`); return; }
    const w = at(i, s.type);
    const head = () => { const t = ex(s.title, w + " 标题"); if (s.kicker) ex(s.kicker, w + " 小标题"); len(t, 26, w + "：标题"); };
    if (s.type === "cover") { ex(s.title, w + " 标题"); if (s.kicker) ex(s.kicker, w + " 小标题"); if (s.sub) ex(s.sub, w + " 副标题"); take(s.notes, w); }
    if (s.type === "section") { ex(s.title, w + " 标题"); if (s.sub) ex(s.sub, w + " 副标题"); take(s.notes, w); }
    if (s.type === "toc") {
      range(s.items, 2, 6, w, "目录项");
      (s.items || []).forEach((it, k) => fits(dropOrdinal(ex(it, `${w} 第 ${k + 1} 项`)), 9.5, 0.6, 22, 15, 1.1, `${w} 第 ${k + 1} 项`));
      take(s.notes, w);
    }
    if (s.type === "text") {
      head(); range(s.points, 1, 3, w, "正文摘句");
      (s.points || []).forEach((p, k) => len(ex(p, `${w} 第 ${k + 1} 条`), 80, `${w} 第 ${k + 1} 条`));
      take(s.notes, w);
    }
    if (s.type === "quote") {
      if (s.title) head(); else if (s.kicker) ex(s.kicker, w + " 小标题");
      len(ex(s.quote, w + " 金句"), 60, `${w} 金句`);
      if ((s.support || []).length > 2) errs.push(`${w}：补充句最多 2 条`);
      (s.support || []).forEach((p, k) => len(ex(p, `${w} 补充 ${k + 1}`), 34, `${w} 补充 ${k + 1}`));
      take(s.notes, w);
    }
    const tail = () => { if (s.conclusion) len(ex(s.conclusion, w + " 结论句"), 40, w + " 结论句"); take(s.end, w); };
    if (s.type === "cards") {
      head(); take(s.intro, w);
      if (!range(s.cards, 2, 5, w, "卡片")) return;
      const k = s.cards.length, cols = G.cols(k, 0.42), h = G.cardH(!!s.conclusion);
      s.cards.forEach((c, j) => {
        const cw = cols[j].w - 0.6, wc = `${w} 第 ${j + 1} 张卡片`;
        fits(dropOrdinal(ex(c.head, wc + " 标题")), cw, G.card.headH, k >= 4 ? 21 : 23, 16, 1.1, wc + " 标题");
        if (c.body) fits(ex(c.body, wc + " 正文"), cw, h - G.card.body - 0.25, k >= 4 ? 17 : 18, 13, 1.35, wc + " 正文");
        if (!c.no || em(String(c.no)) > 3) errs.push(`${wc}：编号 no 要 1–3 个字`);
        take(c.notes, wc);
      });
      tail();
    }
    if (s.type === "timeline") {
      head(); take(s.intro, w);
      if (!range(s.steps, 3, 5, w, "步骤")) return;
      const cols = G.cols(s.steps.length, 0.35);
      s.steps.forEach((c, j) => {
        const wc = `${w} 第 ${j + 1} 步`;
        fits(dropOrdinal(ex(c.head, wc + " 标题")), cols[j].w - 0.2, G.tl.headH, 21, 16, 1.1, wc + " 标题");
        if (c.body) fits(ex(c.body, wc + " 正文"), cols[j].w - 0.2, (s.conclusion ? 5.75 : 6.6) - G.tl.body, 16, 13, 1.35, wc + " 正文");
        if (!c.no) errs.push(`${wc}：要写编号 no`);
        take(c.notes, wc);
      });
      tail();
    }
    if (s.type === "stat") {
      head(); take(s.intro, w);
      if (!range(s.stats, 2, 4, w, "数据")) return;
      s.stats.forEach((c, j) => {
        const wc = `${w} 第 ${j + 1} 个数据`;
        const v = ex(c.value, wc + " 数值");
        if (v && em(v) > 5) errs.push(`${wc}：数值最多 5 个字符（如 64、1024、90%）`);
        if (c.unit) len(ex(c.unit, wc + " 单位"), 4, wc + " 单位");
        len(ex(c.label, wc + " 说明"), 14, wc + " 说明");
        if (c.body) len(ex(c.body, wc + " 正文"), 34, wc + " 正文");
        take(c.notes, wc);
      });
      tail();
    }
    if (s.type === "compare") {
      head(); take(s.intro, w);
      ["left", "right"].forEach((side) => {
        const c = s[side], wc = `${w} ${side === "left" ? "左栏" : "右栏"}`;
        if (!c) { errs.push(`${wc}：缺少`); return; }
        len(ex(c.head, wc + " 标题"), 12, wc + " 标题");
        range(c.points, 1, 4, wc, "要点");
        (c.points || []).forEach((p, k) => len(ex(p, `${wc} 第 ${k + 1} 条`), 22, `${wc} 第 ${k + 1} 条`));
        take(c.notes, wc);
      });
      tail();
    }
    if (s.type === "end") take(s.notes, w);
  });
  const ids = Object.keys(P);
  const miss = ids.filter((i) => !used.includes(i));
  const dup = [...new Set(used.filter((u, k) => used.indexOf(u) !== k))];
  if (miss.length) errs.push(`以下原文段落没有放进任何一页的备注：${miss.join("、")}`);
  if (dup.length) errs.push(`以下段落在备注里出现了不止一次：${dup.join("、")}`);
  const order = used.filter((u, k) => used.indexOf(u) === k);
  if (!miss.length && !dup.length && order.join() !== ids.join()) warns.push("备注里的段落顺序和原文不一致，请确认是有意调整。");
  (plan.corrections || []).forEach((c, k) => {
    const src = doc.paras.find((p) => p.id === c.para);
    if (!src || !src.text.includes(c.from)) errs.push(`修改清单第 ${k + 1} 条：「${c.from}」不在 ${c.para} 中`);
  });
  return { ok: !errs.length, errs, warns };
}

function applyCorrections(doc, plan) {
  const P = Object.fromEntries(doc.paras.map((p) => [p.id, p.text]));
  const applied = [];
  for (const c of (plan && plan.corrections) || []) if (c.accepted && P[c.para] && P[c.para].includes(c.from)) { P[c.para] = P[c.para].split(c.from).join(c.to); applied.push(c); }
  return { P, applied };
}

// ---------- 大纲（生成前给用户看的页面清单） ----------
const LABEL = { cover: "封面", toc: "目录", section: "章节", cards: "卡片", text: "正文", quote: "金句", timeline: "时间轴", stat: "数据", compare: "对比", end: "结尾" };
function outline(plan) {
  return plan.slides.map((s, i) => {
    const t = s.title ? s.title[1] : s.quote ? s.quote[1] : s.type === "toc" ? "目录" : s.type === "end" ? "谢谢" : "";
    const n = s.cards || s.steps || s.stats || s.points || s.items;
    return `${String(i + 1).padStart(2, " ")}. [${LABEL[s.type]}] ${t}${n ? `（${n.length} 项）` : ""}`;
  }).join("\n");
}

// ---------- 生成 ----------
async function build(doc, plan) {
  const { P } = applyCorrections(doc, plan);
  const ex = (ref) => ref[1];
  const body = (ids) => (ids || []).map((i) => P[i]).join("\n");
  const footer = plan.footer ? ex(plan.footer) : "";
  const theme = plan.theme || DEFAULT_THEME, design = plan.design || "editorial";
  const { S, T } = resolve(design, theme);
  const BR = design === "neubrutalism";
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; pres.title = footer || "演示文稿"; pres.author = ""; pres.company = "";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
  const ANIM = [];
  let n = 0;
  const nm = (g, p) => (g ? `@${g}|${++n}` : `${p}-${++n}`);
  const txt = (s, t, o = {}) => { const { g, ...r } = o; s.addText(t, Object.assign({ isTextBox: true, margin: 0, fontSize: 16, fontFace: FONT, color: S.ink, valign: "top", objectName: nm(g, "text") }, r)); };
  const rect = (s, x, y, w, h, o = {}) => s.addShape(o.r ? pres.shapes.ROUNDED_RECTANGLE : pres.shapes[o.shape || "RECTANGLE"], Object.assign({ x, y, w, h, fill: o.fill ? { color: o.fill } : { type: "none" }, line: o.line ? { color: o.line, width: o.lw || 1 } : { type: "none" }, objectName: nm(o.g, "shape") }, o.r ? { rectRadius: o.r } : {}));
  const hline = (s, x, y, w, color, pt, g) => s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color, width: pt }, objectName: nm(g, "rule") });

  // ---- 风格原语：版式只调这些，风格决定长相 ----
  const panel = (s, x, y, w, h, i, g, fill) => {
    if (BR) {
      rect(s, x + S.shadow, y + S.shadow, w, h, { fill: "121212", r: S.radius, g });
      rect(s, x, y, w, h, { fill: fill || S.fills[i % S.fills.length], line: "121212", lw: S.border, r: S.radius, g });
    } else hline(s, x, y, w, S.rule, 2, g);
  };
  const badge = (s, x, y, label, g, size = 26) => {
    const t = S.numPad ? showNo(label) : String(label);
    if (BR) {
      const bw = Math.max(0.6, 0.22 + 0.2 * em(t));
      rect(s, x, y, bw, 0.56, { fill: "FFFFFF", line: "121212", lw: 2, g });
      txt(s, t, { g, x, y, w: bw, h: 0.56, fontSize: 16, bold: true, color: "121212", align: "center", valign: "middle" });
    } else txt(s, t, { g, x, y: y - 0.05, w: 1.6, h: 0.6, fontSize: size, bold: true, color: S.num, valign: "middle" });
  };
  const chrome = (s, i) => {
    if (BR) {
      if (footer) txt(s, footer, { x: M, y: 7.0, w: 8, h: 0.3, fontSize: 10, bold: true, color: S.ink, valign: "middle" });
    } else {
      if (footer) txt(s, footer, { x: M, y: 0.3, w: 8, h: 0.3, fontSize: 10, bold: true, color: S.muted, valign: "middle" });
      hline(s, M, 0.72, W - 2 * M, S.hair, 0.75);
    }
    txt(s, String(i), { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, bold: BR, color: BR ? S.ink : S.muted, align: "right", valign: "middle" });
  };
  const header = (s, kicker, title) => {
    const g = "H|标题";
    if (BR) {
      if (kicker) { const kw = 0.5 + em(kicker) * 0.19; rect(s, M, 0.45, kw, 0.42, { fill: S.fills[0], line: "121212", lw: 1.5, g }); txt(s, kicker, { g, x: M, y: 0.45, w: kw, h: 0.42, fontSize: 13, bold: true, color: "121212", align: "center", valign: "middle" }); }
      txt(s, title, { g, x: M, y: 1.0, w: W - 2 * M, h: 0.85, fontSize: fit(title, W - 2 * M, 0.85, 32, 24, 1.1) || 24, bold: true, color: S.title, valign: "middle" });
    } else {
      if (kicker) txt(s, kicker, { g, x: M, y: 0.98, w: 10, h: 0.34, fontSize: 13, bold: true, color: S.accent, valign: "middle" });
      txt(s, title, { g, x: M, y: 1.32, w: W - 2 * M, h: 0.72, fontSize: fit(title, W - 2 * M, 0.72, 30, 24, 1.1) || 24, bold: true, color: S.title, valign: "middle" });
    }
  };
  const conclusion = (s, t) => {
    const g = "K|结论", y = 6.1;
    if (BR) { panel(s, M, y - 0.05, W - 2 * M, 0.66, 0, g); txt(s, t, { g, x: M + 0.3, y: y - 0.05, w: W - 2 * M - 0.6, h: 0.66, fontSize: 20, bold: true, color: "121212", valign: "middle" }); }
    else { rect(s, M, y + 0.12, 0.08, 0.38, { fill: S.accent, g }); txt(s, t, { g, x: M + 0.3, y, w: W - 2 * M - 0.3, h: 0.62, fontSize: 21, bold: true, color: S.title, valign: "middle" }); }
  };
  const slide = (bg, anim) => { const s = pres.addSlide(); ANIM.push(anim || null); s.background = { color: bg }; return s; };
  const lectureNotes = (d, keys) => {
    let t = d.intro && d.intro.length ? body(d.intro) + "\n" : "";
    keys.forEach((k, j) => { t += `【点击 ${j + 1}】${body(k)}\n`; });
    t += `【点击 ${keys.length + 1} · 全部恢复】${body(d.end)}`;
    return t.trim();
  };

  plan.slides.forEach((d, i) => {
    const no = i + 1; let s;
    if (d.type === "cover") {
      const auto = [];
      s = slide(S.cover.bg, { auto });
      if (BR) {
        panel(s, 0.75, 0.75, 7.95, 5.75, 0);
        if (d.kicker) { rect(s, 1.25, 1.25, 4.2, 0.5, { fill: "FFFFFF", line: "121212", lw: 1.5, g: "A1|眉题" }); txt(s, ex(d.kicker), { g: "A1|眉题", x: 1.25, y: 1.25, w: 4.2, h: 0.5, fontSize: 13, bold: true, color: "121212", align: "center", valign: "middle" }); auto.push("A1"); }
        const t = ex(d.title);
        txt(s, t, { g: "A2|标题", x: 1.25, y: 2.0, w: 7.0, h: 2.9, fontSize: fit(t, 7.0, 2.9, 66, 36, 1.05) || 36, bold: true, color: "121212", valign: "middle", lineSpacingMultiple: 1.05 }); auto.push("A2");
        panel(s, 9.15, 0.75, 3.45, 2.65, 1);
        if (d.sub) { const st = ex(d.sub); txt(s, st, { g: "A3|副标题", x: 9.45, y: 0.95, w: 2.85, h: 2.25, fontSize: fit(st, 2.85, 2.25, 22, 14, 1.25) || 14, bold: true, color: "121212", align: "center", valign: "middle" }); auto.push("A3"); }
        panel(s, 9.15, 3.85, 3.45, 2.65, 2);
        rect(s, 10.1, 4.4, 1.55, 1.55, { shape: "OVAL", fill: S.accent, line: "121212", lw: 2.25 });
        rect(s, 10.6, 4.9, 0.55, 0.55, { shape: "OVAL", fill: S.fills[0], line: "121212", lw: 2.25 });
      } else {
        rect(s, 8.2, 1.1, 4.7, 4.7, { shape: "OVAL", line: T.main, lw: 1.5 });
        rect(s, 9.0, 1.9, 3.1, 3.1, { shape: "OVAL", fill: T.soft });
        rect(s, 11.45, 4.6, 0.45, 0.45, { shape: "OVAL", fill: S.accent });
        hline(s, M, 0.72, W - 2 * M, S.hair, 0.75);
        if (footer) txt(s, footer, { x: M, y: 0.3, w: 8, h: 0.3, fontSize: 10, bold: true, color: S.muted, valign: "middle" });
        if (d.kicker) { txt(s, ex(d.kicker), { g: "A1|眉题", x: M, y: 1.75, w: 8, h: 0.45, fontSize: 15, bold: true, color: S.accent, valign: "middle" }); auto.push("A1"); }
        const t = ex(d.title);
        txt(s, t, { g: "A2|标题", x: M, y: 2.25, w: 8.4, h: 2.3, fontSize: fit(t, 8.4, 2.3, 72, 40, 1.05) || 40, bold: true, color: S.title, valign: "middle", lineSpacingMultiple: 1.0 }); auto.push("A2");
        rect(s, M, 4.85, 1.6, 0.09, { fill: S.accent, g: "A3|副标题" });
        if (d.sub) txt(s, ex(d.sub), { g: "A3|副标题", x: M, y: 5.15, w: 8, h: 0.55, fontSize: 20, color: S.muted, valign: "middle" });
        auto.push("A3");
      }
      s.addNotes(body(d.notes));
    } else if (d.type === "toc") {
      const auto = ["H"];
      s = slide(S.bg, { auto });
      chrome(s, no); header(s, "", "目录");
      const k = d.items.length;
      if (BR) {
        const cols = G.cols(k > 4 ? 3 : 2, 0.42), rows = Math.ceil(k / cols.length), rh = (4.55 - (rows - 1) * 0.35) / rows;
        d.items.forEach((it, j) => {
          const c = cols[j % cols.length], y = TOP + Math.floor(j / cols.length) * (rh + 0.35), g = `I${j + 1}|目录`, t = dropOrdinal(ex(it));
          panel(s, c.x, y, c.w, rh, j, g);
          txt(s, showNo(j + 1), { g, x: c.x + 0.3, y: y + 0.22, w: 1.2, h: 0.45, fontSize: 18, bold: true, color: "121212" });
          txt(s, t, { g, x: c.x + 0.3, y: y + 0.7, w: c.w - 0.6, h: rh - 0.85, fontSize: fit(t, c.w - 0.6, rh - 0.85, 22, 15, 1.15) || 15, bold: true, color: "121212", valign: "middle" });
          auto.push(`I${j + 1}`);
        });
      } else {
        const step = Math.min(0.82, 4.7 / k);
        d.items.forEach((it, j) => {
          const y = TOP + j * step, g = `I${j + 1}|目录`, t = dropOrdinal(ex(it));
          txt(s, showNo(j + 1), { g, x: M, y, w: 1.0, h: step - 0.14, fontSize: 18, bold: true, color: S.accent, valign: "middle" });
          txt(s, t, { g, x: M + 1.15, y, w: 9.5, h: step - 0.14, fontSize: fit(t, 9.5, step - 0.2, 22, 15, 1.1) || 15, bold: true, color: S.title, valign: "middle" });
          hline(s, M, y + step - 0.07, W - 2 * M, S.hair, 0.75, g);
          auto.push(`I${j + 1}`);
        });
      }
      s.addNotes(body(d.notes));
    } else if (d.type === "section") {
      const auto = [];
      s = slide(S.section.bg, { auto });
      const t = d.no ? dropOrdinal(ex(d.title)) : ex(d.title);
      if (BR) {
        if (d.no) { panel(s, 1.0, 1.9, 3.3, 3.3, 0, "A1|编号"); txt(s, String(d.no), { g: "A1|编号", x: 1.0, y: 1.9, w: 3.3, h: 3.3, fontSize: 100, bold: true, color: "121212", align: "center", valign: "middle" }); auto.push("A1"); }
        txt(s, t, { g: "A2|标题", x: 5.0, y: 2.3, w: 7.6, h: 1.5, fontSize: fit(t, 7.6, 1.5, 44, 28, 1.1) || 28, bold: true, color: "121212", valign: "bottom" }); auto.push("A2");
        if (d.sub) { txt(s, ex(d.sub), { g: "A3|副标题", x: 5.0, y: 4.0, w: 7.6, h: 0.9, fontSize: 18, bold: true, color: "121212" }); auto.push("A3"); }
        if (footer) txt(s, footer, { x: M, y: 7.0, w: 8, h: 0.3, fontSize: 10, bold: true, color: "121212", valign: "middle" });
      } else {
        if (footer) txt(s, footer, { x: M, y: 0.3, w: 8, h: 0.3, fontSize: 10, bold: true, color: S.section.sub, valign: "middle" });
        hline(s, M, 0.72, W - 2 * M, mix2(T.base), 0.75);
        if (d.no) { txt(s, String(d.no), { g: "A1|编号", x: M, y: 1.3, w: 6, h: 1.9, fontSize: 120, bold: true, color: S.section.num, valign: "bottom" }); auto.push("A1"); }
        txt(s, t, { g: "A2|标题", x: M, y: 3.45, w: 11, h: 1.1, fontSize: fit(t, 11, 1.1, 46, 28, 1.1) || 28, bold: true, color: S.section.title, valign: "middle" }); auto.push("A2");
        if (d.sub) { rect(s, M, 4.85, 0.08, 0.5, { fill: T.main, g: "A3|副标题" }); txt(s, ex(d.sub), { g: "A3|副标题", x: M + 0.3, y: 4.8, w: 11, h: 0.6, fontSize: 20, color: S.section.sub, valign: "middle" }); auto.push("A3"); }
      }
      txt(s, String(no), { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: BR ? "121212" : S.section.sub, align: "right", valign: "middle" });
      s.addNotes(body(d.notes));
    } else if (d.type === "text") {
      const k = d.points.length, steps = d.points.map((_, j) => [`P${j + 1}`]);
      s = slide(S.bg, { auto: ["H"], steps, dim: true });
      chrome(s, no); header(s, d.kicker ? ex(d.kicker) : "", ex(d.title));
      const gap = 0.3, h = Math.min(1.35, (4.5 - gap * (k - 1)) / k);
      d.points.forEach((p, j) => {
        const y = TOP + 0.1 + j * (h + gap), t = ex(p), g = `P${j + 1}|要点`;
        panel(s, M, y, W - 2 * M, h, j + 2, g);
        badge(s, M + (BR ? 0.3 : 0), y + (BR ? (h - 0.56) / 2 : 0.2), j + 1, g, 24);
        const x = M + 1.3, w = W - 2 * M - 1.6;
        txt(s, t, { g, x, y: y + 0.08, w, h: h - 0.16, fontSize: fit(t, w, h - 0.2, 22, 15, 1.3) || 15, color: S.ink, valign: "middle", lineSpacingMultiple: 1.25 });
      });
      s.addNotes(body(d.notes));
    } else if (d.type === "quote") {
      const sup = d.support || [], steps = [["Q"], ...sup.map((_, j) => [`S${j + 1}`])];
      s = slide(S.bg, { auto: d.title || d.kicker ? ["H"] : [], steps });
      chrome(s, no);
      if (d.title || d.kicker) header(s, d.kicker ? ex(d.kicker) : "", d.title ? ex(d.title) : "");
      const q = ex(d.quote), qy = 2.25, qh = 2.35;
      if (BR) {
        panel(s, M, qy, W - 2 * M, qh, 0, "Q|金句");
        txt(s, q, { g: "Q|金句", x: M + 0.5, y: qy + 0.15, w: W - 2 * M - 1.0, h: qh - 0.3, fontSize: fit(q, W - 2 * M - 1.0, qh - 0.3, 34, 22, 1.25) || 22, bold: true, color: "121212", valign: "middle", lineSpacingMultiple: 1.2 });
      } else {
        rect(s, M, qy + 0.1, 0.1, qh - 0.2, { fill: S.accent, g: "Q|金句" });
        txt(s, q, { g: "Q|金句", x: M + 0.5, y: qy, w: 10.8, h: qh, fontSize: fit(q, 10.8, qh, 36, 22, 1.25) || 22, bold: true, color: S.title, valign: "middle", lineSpacingMultiple: 1.2 });
      }
      sup.forEach((p, j) => {
        const y = 4.95 + j * 0.8, g = `S${j + 1}|补充`, t = ex(p);
        if (BR) { panel(s, M + 0.5 * j, y, 7.6, 0.6, j + 1, g); txt(s, t, { g, x: M + 0.5 * j + 0.3, y, w: 7.0, h: 0.6, fontSize: 18, bold: true, color: "121212", valign: "middle" }); }
        else { hline(s, M + 0.5, y + 0.3, 0.45, S.accent, 1.5, g); txt(s, t, { g, x: M + 1.15, y, w: 10, h: 0.6, fontSize: 20, color: S.muted, valign: "middle" }); }
      });
      s.addNotes(body(d.notes));
    } else if (d.type === "cards") {
      const k = d.cards.length, cols = G.cols(k, BR ? 0.42 : 0.45), h = G.cardH(!!d.conclusion), C = G.card;
      const steps = d.cards.map((_, j) => [`C${j + 1}`]);
      s = slide(S.bg, { auto: ["H"], steps, dim: true, end: d.conclusion ? "K" : null });
      chrome(s, no); header(s, d.kicker ? ex(d.kicker) : "", ex(d.title));
      d.cards.forEach((c, j) => {
        const { x, w } = cols[j], y = TOP, ht = c.no ? dropOrdinal(ex(c.head)) : ex(c.head), g = `C${j + 1}|${ht}`;
        const px = x + S.pad, cw = w - 2 * S.pad;
        panel(s, x, y, w, h, j, g);
        badge(s, px, y + C.num, c.no, g);
        txt(s, ht, { g, x: px, y: y + C.head, w: cw, h: C.headH, fontSize: fit(ht, cw, C.headH, k >= 4 ? 21 : 23, 16, 1.1) || 16, bold: true, color: S.title, valign: "top", lineSpacingMultiple: 1.1 });
        if (c.body) { const bt = ex(c.body); if (!BR) hline(s, px, y + C.body - 0.12, 0.6, S.accent, 1.5, g); txt(s, bt, { g, x: px, y: y + C.body, w: cw, h: h - C.body - 0.25, fontSize: fit(bt, cw, h - C.body - 0.25, k >= 4 ? 17 : 18, 13, 1.35) || 13, color: S.ink, lineSpacingMultiple: 1.3 }); }
      });
      if (d.conclusion) conclusion(s, ex(d.conclusion));
      s.addNotes(lectureNotes(d, d.cards.map((c) => c.notes)));
    } else if (d.type === "timeline") {
      const k = d.steps.length, cols = G.cols(k, 0.35), L = G.tl;
      s = slide(S.bg, { auto: ["H", "L"], steps: d.steps.map((_, j) => [`T${j + 1}`]), dim: true, end: d.conclusion ? "K" : null });
      chrome(s, no); header(s, d.kicker ? ex(d.kicker) : "", ex(d.title));
      hline(s, M, L.axis, W - 2 * M, BR ? "121212" : S.hair, BR ? 3 : 1.5, "L|轴线");
      const bottom = d.conclusion ? 5.75 : 6.6;
      d.steps.forEach((c, j) => {
        const { x, w } = cols[j], ht = dropOrdinal(ex(c.head)), g = `T${j + 1}|${ht}`;
        if (BR) {
          rect(s, x + 0.06, L.axis - 0.33 + 0.06, 0.66, 0.66, { fill: "121212", g });
          rect(s, x, L.axis - 0.33, 0.66, 0.66, { fill: S.fills[j % 4], line: "121212", lw: 2.25, g });
          txt(s, String(c.no), { g, x, y: L.axis - 0.33, w: 0.66, h: 0.66, fontSize: 20, bold: true, color: "121212", align: "center", valign: "middle" });
        } else {
          rect(s, x, L.axis - 0.13, 0.26, 0.26, { shape: "OVAL", fill: S.accent, g });
          txt(s, showNo(c.no), { g, x, y: L.axis - 0.75, w: 1.5, h: 0.5, fontSize: 22, bold: true, color: S.accent, valign: "bottom" });
        }
        txt(s, ht, { g, x, y: L.head, w: w - 0.2, h: L.headH, fontSize: fit(ht, w - 0.2, L.headH, 21, 16, 1.1) || 16, bold: true, color: S.title, lineSpacingMultiple: 1.1 });
        if (c.body) { const bt = ex(c.body); txt(s, bt, { g, x, y: L.body, w: w - 0.2, h: bottom - L.body, fontSize: fit(bt, w - 0.2, bottom - L.body, 17, 13, 1.35) || 13, color: S.ink, lineSpacingMultiple: 1.3 }); }
      });
      if (d.conclusion) conclusion(s, ex(d.conclusion));
      s.addNotes(lectureNotes(d, d.steps.map((c) => c.notes)));
    } else if (d.type === "stat") {
      const k = d.stats.length, cols = G.cols(k, 0.45), h = G.cardH(!!d.conclusion), A = G.stat;
      s = slide(S.bg, { auto: ["H"], steps: d.stats.map((_, j) => [`N${j + 1}`]), dim: true, end: d.conclusion ? "K" : null });
      chrome(s, no); header(s, d.kicker ? ex(d.kicker) : "", ex(d.title));
      d.stats.forEach((c, j) => {
        const { x, w } = cols[j], y = TOP, g = `N${j + 1}|数据`, px = x + S.pad, cw = w - 2 * S.pad;
        panel(s, x, y, w, h, j, g);
        txt(s, ex(c.label), { g, x: px, y: y + A.label, w: cw, h: 0.4, fontSize: 15, bold: true, color: BR ? "121212" : S.muted, valign: "middle" });
        const v = ex(c.value), vs = Math.min(...d.stats.map((q) => Math.min(80, Math.floor((cw - (q.unit ? em(ex(q.unit)) * 0.3 + 0.25 : 0)) * 72 / (em(ex(q.value)) * 1.2)))));
        const runs = [{ text: v, options: { fontSize: vs, bold: true, color: BR ? "121212" : S.accent } }];
        if (c.unit) runs.push({ text: ex(c.unit), options: { fontSize: 18, bold: true, color: BR ? "121212" : S.title } });
        txt(s, runs, { g, x: px, y: y + A.value, w: cw, h: A.valueH, valign: "bottom" });
        if (c.body) { const bt = ex(c.body); txt(s, bt, { g, x: px, y: y + A.body, w: cw, h: h - A.body - 0.25, fontSize: fit(bt, cw, h - A.body - 0.25, 18, 13, 1.35) || 13, color: S.ink, lineSpacingMultiple: 1.3 }); }
      });
      if (d.conclusion) conclusion(s, ex(d.conclusion));
      s.addNotes(lectureNotes(d, d.stats.map((c) => c.notes)));
    } else if (d.type === "compare") {
      s = slide(S.bg, { auto: ["H"], steps: [["L"], ["R"]], dim: true, end: d.conclusion ? "K" : null });
      chrome(s, no); header(s, d.kicker ? ex(d.kicker) : "", ex(d.title));
      const cols = G.cols(2, BR ? 0.5 : 0.9), h = G.cardH(!!d.conclusion);
      if (!BR) s.addShape(pres.shapes.LINE, { x: W / 2, y: TOP + 0.3, w: 0, h: h - 0.6, line: { color: S.hair, width: 0.75 }, objectName: "divider" });
      ["left", "right"].forEach((side, j) => {
        const c = d[side], { x, w } = cols[j], g = `${j ? "R" : "L"}|${ex(c.head)}`, px = x + S.pad, cw = w - 2 * S.pad;
        const tone = j ? S.accent : S.muted;
        panel(s, x, TOP, w, h, j ? 0 : 3, g);
        txt(s, ex(c.head), { g, x: px, y: TOP + 0.3, w: cw, h: 0.75, fontSize: 30, bold: true, color: BR ? "121212" : j ? S.title : S.muted, valign: "middle" });
        c.points.forEach((p, q) => {
          const y = TOP + 1.35 + q * 0.72;
          rect(s, px, y + 0.2, 0.14, 0.14, { fill: BR ? "121212" : tone, g });
          txt(s, ex(p), { g, x: px + 0.4, y, w: cw - 0.4, h: 0.55, fontSize: fit(ex(p), cw - 0.4, 0.55, 19, 14, 1.1) || 14, color: S.ink, valign: "middle" });
        });
      });
      if (d.conclusion) conclusion(s, ex(d.conclusion));
      s.addNotes(lectureNotes(d, [d.left.notes, d.right.notes]));
    } else if (d.type === "end") {
      s = slide(S.end.bg, { auto: ["A1"] });
      if (BR) {
        panel(s, 3.4, 2.0, 6.5, 2.8, 2, "A1|结尾", "FFFFFF");
        txt(s, "谢谢", { g: "A1|结尾", x: 3.4, y: 2.0, w: 6.5, h: 2.8, fontSize: 66, bold: true, color: "121212", align: "center", valign: "middle" });
        if (footer) txt(s, footer, { x: 3.4, y: 5.4, w: 6.5, h: 0.4, fontSize: 14, bold: true, color: "121212", align: "center" });
      } else {
        rect(s, 8.2, 1.1, 4.7, 4.7, { shape: "OVAL", line: T.main, lw: 1.5 });
        rect(s, 9.0, 1.9, 3.1, 3.1, { shape: "OVAL", fill: T.soft });
        txt(s, "谢谢", { g: "A1|结尾", x: M, y: 2.4, w: 7, h: 1.5, fontSize: 72, bold: true, color: S.title, valign: "middle" });
        rect(s, M, 4.15, 1.6, 0.09, { fill: S.accent, g: "A1|结尾" });
        if (footer) txt(s, footer, { x: M, y: 4.45, w: 7, h: 0.45, fontSize: 18, color: S.muted });
      }
      s.addNotes(body(d.notes));
    }
  });
  const raw = await pres.write({ outputType: "nodebuffer" });
  return postProcess(raw, ANIM, "nodebuffer", theme);
}
const mix2 = (hex) => require("./styles.js").mix(hex, 0.25);

module.exports = { check, build, outline, applyCorrections, dropOrdinal, TYPES, LABEL };
