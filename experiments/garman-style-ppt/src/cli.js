// GarmanPPT 实验版（garman-style-ppt 0.4.0-exp）· 不是正式版，不替代 skill 里的 doc2ppt.cjs
// 用法：
//   node src/cli.js parse   <文档> <工作目录>
//   node src/cli.js check   <工作目录>
//   node src/cli.js outline <工作目录>                       → 打印页面清单
//   node src/cli.js build   <工作目录> [输出.pptx] [--theme 银杏] [--design neubrutalism]
//   node src/cli.js verify  <工作目录> <文件.pptx>            → 重新检查成品
const fs = require("fs");
const path = require("path");
const { parse } = require("./parse.js");
const { check, build, outline, applyCorrections } = require("./core.js");
const { verify } = require("./verify.js");
const { VERSION } = require("./version.js");
const { THEMES } = require("./themes.js");
const { STYLES, pickStyle, resolve } = require("./styles.js");
const log = (...a) => console.log(...a);
const die = (m, code = 1) => { console.error(m); process.exit(code); };
const readJSON = (f) => { try { return JSON.parse(fs.readFileSync(f, "utf8")); } catch (e) { die(`读不了 ${f}：${e.message}`); } };
const opt = (argv, k) => { const i = argv.indexOf(k); return i >= 0 ? argv.splice(i, 2)[1] : null; };

(async () => {
  const argv = process.argv.slice(2);
  const theme = opt(argv, "--theme"), design = opt(argv, "--design");
  const [cmd, a, b] = argv;
  log(`== GarmanPPT 实验版 ${VERSION} ==`);
  if (cmd === "parse") {
    fs.mkdirSync(b, { recursive: true });
    const doc = await parse(a);
    fs.writeFileSync(path.join(b, "paras.json"), JSON.stringify(doc, null, 1));
    fs.writeFileSync(path.join(b, "paras.txt"), doc.paras.map((p) => `${p.id}${p.level ? ` [标题${p.level}]` : ""} ${p.text}`).join("\n") + "\n");
    log(`已读取《${doc.source}》：${doc.paras.length} 段。建议风格：${STYLES[pickStyle(doc)].name}`);
    return;
  }
  if (!a) die("用法见文件开头");
  const doc = readJSON(path.join(a, "paras.json")), plan = readJSON(path.join(a, "plan.json"));
  if (theme) { if (!THEMES[theme]) die(`配色「${theme}」不存在`); plan.theme = theme; }
  if (design) { if (!STYLES[design]) die(`风格「${design}」不存在，可用：${Object.keys(STYLES).join("、")}`); plan.design = design; }
  if (!plan.design) plan.design = pickStyle(doc);
  const r = check(doc, plan);
  r.errs.forEach((e) => log("✗ " + e)); r.warns.forEach((e) => log("! " + e));
  log(r.ok ? "校验通过。" : `校验未通过：${r.errs.length} 个问题。`);
  if (!r.ok) process.exit(3);
  if (cmd === "check") return;
  if (cmd === "outline") { log(outline(plan)); return; }
  const P = applyCorrections(doc, plan).P;
  if (cmd === "verify") { const v = await verify(fs.readFileSync(b), P, plan); v.info.forEach((x) => log(x)); v.errs.forEach((e) => log("✗ " + e)); log(v.ok ? "verify 通过。" : "verify 未通过。"); process.exit(v.ok ? 0 : 4); }
  if (cmd === "build") {
    const rs = resolve(plan.design, plan.theme || "天河石");
    log(`我用了「${rs.name}」风格 × 「${plan.theme || "天河石"}」配色，可以换（--design / --theme）。`);
    rs.notes.forEach((x) => log("提醒：" + x));
    log("页面清单：\n" + outline(plan));
    const out = b || path.join(a, "演示文稿.pptx");
    const buf = await build(doc, plan);
    const v = await verify(buf, P, plan);
    v.info.forEach((x) => log(x)); v.errs.forEach((e) => log("✗ " + e));
    if (!v.ok) die("verify 未通过，未写出文件。", 4);
    fs.writeFileSync(out, buf); log(`verify 通过。已生成：${out}`);
  }
})().catch((e) => die("出错：" + (e && e.stack || e)));
