const JSZip = require("jszip");
const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const FONT = "Microsoft YaHei", MARK = "0A0B0C";
const { THEMES, DEFAULT_THEME } = require("./themes.js");
// PowerPoint / WPS 主题色板：天河石沿用 v2.3 原色板，其余按角色映射
const V23 = { dk1: "243335", lt1: "FFFFFF", dk2: "122947", lt2: "EFF8F9", accent1: "70C6D6", accent2: "1B667A", accent3: "245F4D", accent4: "59652E", accent5: "B04D2F", accent6: "315F91", hlink: "315F91", folHlink: "1B667A" };
const schemeOf = (name) => {
  if (name === DEFAULT_THEME) return V23;
  const t = THEMES[name];
  return { dk1: t.ink, lt1: "FFFFFF", dk2: t.base, lt2: t.pale, accent1: t.main, accent2: t.deep, accent3: t.base, accent4: t.muted, accent5: t.accent, accent6: t.soft, hlink: t.deep, folHlink: t.muted };
};
// ---------- 后处理：主题色与中文字体、组合、动画、毛玻璃 ----------
const SLOTS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];

function groupUnits(xml) {
  const re = /<p:(sp|pic)\b[^>]*>[\s\S]*?<\/p:\1>/g;
  const els = []; let m;
  while ((m = re.exec(xml))) {
    const body = m[0];
    const nmm = body.match(/<p:cNvPr id="(\d+)" name="([^"]*)"/);
    if (!nmm || !nmm[2].startsWith("@")) continue;
    const [key, label] = nmm[2].slice(1).split("|");
    const off = body.match(/<a:off x="(-?\d+)" y="(-?\d+)"\/>/), ext = body.match(/<a:ext cx="(\d+)" cy="(\d+)"\/>/);
    els.push({ start: m.index, end: m.index + body.length, body, key, label, x: +off[1], y: +off[2], w: +ext[1], h: +ext[2] });
  }
  if (!els.length) return { xml, ids: {} };
  const units = {};
  for (const e of els) (units[e.key] = units[e.key] || { label: e.label, els: [] }).els.push(e);
  let maxId = Math.max(...[...xml.matchAll(/<p:cNvPr id="(\d+)"/g)].map((a) => +a[1]));
  const ids = {}, repl = [];
  for (const [key, u] of Object.entries(units)) {
    const x0 = Math.min(...u.els.map((e) => e.x)), y0 = Math.min(...u.els.map((e) => e.y));
    const x1 = Math.max(...u.els.map((e) => e.x + e.w)), y1 = Math.max(...u.els.map((e) => e.y + e.h));
    const id = ++maxId; ids[key] = id; let k = 0;
    const kids = u.els.map((e) => e.body.replace(/(<p:cNvPr id="\d+" name=")[^"]*"/, (_, a) => `${a}${esc(key)} · ${esc(u.label)} · ${++k}"`)).join("");
    const g = `<p:grpSp><p:nvGrpSpPr><p:cNvPr id="${id}" name="${esc(key)} · ${esc(u.label)}"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="${x0}" y="${y0}"/><a:ext cx="${x1 - x0}" cy="${y1 - y0}"/><a:chOff x="${x0}" y="${y0}"/><a:chExt cx="${x1 - x0}" cy="${y1 - y0}"/></a:xfrm></p:grpSpPr>${kids}</p:grpSp>`;
    u.els.forEach((e, i) => repl.push({ start: e.start, end: e.end, text: i === 0 ? g : "" }));
  }
  repl.sort((a, b) => b.start - a.start);
  for (const r of repl) xml = xml.slice(0, r.start) + r.text + xml.slice(r.end);
  return { xml, ids };
}

// 实验版动画：所有页面的主要内容都逐个「淡入」。
// anim = { auto: [组合…]  进页后自动依次淡入（标题、目录项、封面元素）,
//          steps: [[组合…]…] 每次点击淡入一组, dim: 上一组变淡到 50%, end: 最后一次点击出现的结论组 }
const FADE = 500, GAP = 150;
function buildTiming(anim, ids) {
  let n = 2; const nid = () => ++n;
  const sp = (k) => { if (!ids[k]) throw new Error("找不到组合：" + k); return ids[k]; };
  const fade = (k, node, delay = 0) => { const a = nid(), b = nid(), c = nid();
    return `<p:par><p:cTn id="${a}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="${node}"><p:stCondLst><p:cond delay="${delay}"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="${b}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="${sp(k)}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set><p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="${c}" dur="${FADE}"/><p:tgtEl><p:spTgt spid="${sp(k)}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>`; };
  const opacity = (k, v, node) => { const a = nid(), b = nid(), c = nid();
    return `<p:par><p:cTn id="${a}" presetID="9" presetClass="emph" presetSubtype="0" nodeType="${node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="${b}" dur="indefinite"/><p:tgtEl><p:spTgt spid="${sp(k)}"/></p:tgtEl><p:attrNameLst><p:attrName>style.opacity</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="${v}"/></p:to></p:set><p:animEffect filter="image" prLst="opacity: ${v}"><p:cBhvr rctx="IE"><p:cTn id="${c}" dur="indefinite"/><p:tgtEl><p:spTgt spid="${sp(k)}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>`; };
  // 一个「时间组」：click=true 等待点击；false 进页自动开始
  const group = (inner, click) => { const a = nid(), b = nid();
    const cond = click ? '<p:cond delay="indefinite"/>' : '<p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>';
    return `<p:par><p:cTn id="${a}" fill="hold"><p:stCondLst>${cond}</p:stCondLst><p:childTnLst><p:par><p:cTn id="${b}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>${inner()}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>`; };
  // 自动组：依次淡入，每个比上一个晚 FADE-GAP 毫秒（互相衔接、略有重叠）
  const seq = (keys, first) => keys.map((k, i) => fade(k, i === 0 ? first : "withEffect", i * (FADE - GAP))).join("");
  const out = [];
  if (anim.auto && anim.auto.length) out.push(group(() => seq(anim.auto, "afterEffect"), false));
  const steps = anim.steps || [], faded = [];
  steps.forEach((keys, j) => out.push(group(() => {
    let s = seq(keys, "clickEffect");
    if (anim.dim && j > 0) { s += steps[j - 1].map((k) => opacity(k, "0.5", "withEffect")).join(""); faded.push(...steps[j - 1]); }
    return s;
  }, true)));
  if (steps.length && (anim.dim || anim.end)) out.push(group(() => {
    let s = "", first = true;
    if (anim.end) { s += fade(anim.end, "clickEffect"); first = false; }
    faded.forEach((k) => { s += opacity(k, "1", first ? "clickEffect" : "withEffect"); first = false; });
    return s || "";
  }, true));
  return `<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>${out.join("")}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>`;
}

async function postProcess(buf, ANIM, outType = "nodebuffer", theme = DEFAULT_THEME) {
  const zip = await JSZip.loadAsync(buf);
  let th = await zip.file("ppt/theme/theme1.xml").async("string");
  const C = schemeOf(theme);
  const scheme = `<a:clrScheme name="Garman 自然色 · ${theme}">` + SLOTS.map((k) => `<a:${k}><a:srgbClr val="${C[k]}"/></a:${k}>`).join("") + "</a:clrScheme>";
  th = th.replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, () => scheme)
    .replace(/<a:ea typeface=""\/>/g, `<a:ea typeface="${FONT}"/>`)
    .replace(/<a:font script="Hans" typeface="[^"]*"\/>/g, '<a:font script="Hans" typeface="微软雅黑"/>');
  zip.file("ppt/theme/theme1.xml", th);
  for (let i = 0; i < ANIM.length; i++) {
    const part = `ppt/slides/slide${i + 1}.xml`;
    let xml = await zip.file(part).async("string");
        xml = xml.replace(/(<\/a:r>)<a:pPr\b[^>]*?(?:\/>|>(?:(?!<\/a:pPr>)[\s\S])*?<\/a:pPr>)/g, "$1"); // 删段中多余 pPr
    xml = xml.replace(/(<a:rPr\b[^>]*?)(\/?>)/g, (all, a, b) => (/\blang=/.test(a) ? all : `${a} lang="zh-CN" altLang="en-US"${b}`));
    xml = xml.replace(/<a:latin typeface="([^"]+)"[^>]*\/>(?!<a:ea)/g, (all, f) => `${all}<a:ea typeface="${f}"/>`); // 中文也指定同一字体
    const { xml: gx, ids } = groupUnits(xml);
    xml = gx;
    if (ANIM[i]) xml = xml.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + buildTiming(ANIM[i], ids));
    else if (Object.keys(ids).length) throw new Error("有组合但没有动画：" + part);
    zip.file(part, xml);
  }
  return zip.generateAsync({ type: outType, compression: "DEFLATE", mimeType: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
}


module.exports = { postProcess };
