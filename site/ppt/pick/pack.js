/* GarmanPPT 组合包：在浏览器里把「母版 + 预览图 + 提示词 + 先读我（+ 技能包）」打成一个 zip。
 * 不依赖第三方库：pptx / jpg / zip 本身已压缩，这里用 ZIP 的「存储」方式（不再压缩），文件名按 UTF-8 标记。
 * 用法：GarmanPack.download({ style, palette, cell, fx, files, version, pageUrl })
 */
(function () {
  "use strict";

  // ---------- 极简 ZIP 写入器（store） ----------
  const CRC_TABLE = (() => {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(buf) {
    let c = 0xffffffff;
    for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }
  function dosTime(d) {
    return {
      time: (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1),
      date: ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate(),
    };
  }
  function makeZip(entries) {   // entries: [{name, data: Uint8Array}]
    const enc = new TextEncoder(), { time, date } = dosTime(new Date());
    const parts = [], central = [];
    let offset = 0;
    for (const e of entries) {
      const name = enc.encode(e.name), crc = crc32(e.data), size = e.data.length;
      const h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true);
      h.setUint16(8, 0, true); h.setUint16(10, time, true); h.setUint16(12, date, true);
      h.setUint32(14, crc, true); h.setUint32(18, size, true); h.setUint32(22, size, true);
      h.setUint16(26, name.length, true); h.setUint16(28, 0, true);
      parts.push(new Uint8Array(h.buffer), name, e.data);
      const c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true);
      c.setUint16(8, 0x0800, true); c.setUint16(10, 0, true); c.setUint16(12, time, true); c.setUint16(14, date, true);
      c.setUint32(16, crc, true); c.setUint32(20, size, true); c.setUint32(24, size, true);
      c.setUint16(28, name.length, true); c.setUint32(42, offset, true);
      central.push(new Uint8Array(c.buffer), name);
      offset += 30 + name.length + size;
    }
    const cdSize = central.reduce((a, b) => a + b.length, 0);
    const end = new DataView(new ArrayBuffer(22));
    end.setUint32(0, 0x06054b50, true); end.setUint16(8, entries.length, true); end.setUint16(10, entries.length, true);
    end.setUint32(12, cdSize, true); end.setUint32(16, offset, true);
    return new Blob([...parts, ...central, new Uint8Array(end.buffer)], { type: "application/zip" });
  }

  // ---------- 风格字段的中文说法 ----------
  const ZH = {
    // 版式
    "asymmetric-grid": "不对称网格", bento: "大小不一的便当格", "card-stack": "卡片堆叠", collage: "拼贴",
    "color-field-grid": "色块网格", "comic-panel": "漫画分格", "cover-big-type": "封面大字", "diagonal-split": "斜线分割",
    "frosted-panels": "磨砂面板", "full-bleed-image": "满版图片", "geometric-blocks": "几何色块", "hero-object": "一个主视觉物体",
    "horizon-scene": "地平线场景", "multi-column": "多栏排版", "organic-frame": "有机曲线边框", "pull-quote": "大号引文",
    "single-focus": "单一焦点", "symmetric-frame": "对称边框", tiles: "磁贴", "vertical-text": "竖排文字",
    // 元素
    "blurred-blob": "模糊色团", botanical: "植物纹样", bubble: "气泡", chrome: "金属铬质感", circle: "圆形",
    "diagonal-bar": "斜向长条", "dot-pattern": "圆点阵", "drop-cap": "首字下沉", "frosted-card": "磨砂卡片",
    hairline: "极细线", halftone: "网点", halo: "光晕", "hard-shadow": "硬投影（不模糊）", "line-icon": "线性图标",
    "live-tile": "动态磁贴", "metallic-line": "金属细线", "orthogonal-lines": "横竖粗黑线", "page-furniture": "页眉页脚等版面部件",
    "paper-texture": "纸张质感", "perspective-grid": "透视网格", photomontage: "照片拼贴", "red-dot": "一个红点",
    "retro-window": "复古窗口", "rounded-card": "圆角卡片", sparkle: "四角星闪光", "speech-burst": "爆炸对话框",
    square: "方形", squiggle: "波浪线", "stepped-arch": "阶梯拱形", sunburst: "放射线", "sunset-stripes": "条纹落日",
    "thick-outline": "粗描边", "thick-rule": "粗分隔线", triangle: "三角形", "visible-grid": "可见网格",
    wedge: "楔形", "whiplash-curve": "鞭状曲线",
    // 禁止项
    "3d-effects": "3D 效果", "centered-layout": "居中排版", clipart: "剪贴画", "dense-text": "大段密集文字", emoji: "表情符号",
    "equal-cells": "等大的格子", "flat-icons": "扁平图标", gradient: "渐变", "high-saturation": "高饱和颜色",
    "justified-text": "两端对齐", "low-contrast-text": "低对比度文字", "many-fonts": "多种字体", "muted-colors": "灰暗的颜色",
    ornament: "装饰花纹", "rounded-corners": "圆角", skeuomorphism: "拟物质感", "soft-shadow": "柔和投影",
    "stock-photo": "图库照片", "thin-outline": "细描边",
    // 密度
    low: "低（留白多）", medium: "中", high: "高",
  };
  const zh = (k) => ZH[k] || k;
  const ROLE_ZH = { background: "背景", text: "文字", primary: "主色", secondary: "辅助色", accent: "点缀色" };
  const ROLE_USE = {
    background: "页面底色", text: "标题和正文", primary: "主要色块、章节号、强调",
    secondary: "次要色块、卡片", accent: "小面积点缀（编号、图标、关键数字）",
  };

  function prompt(o) {
    const { style: st, palette: pa, cell: c, fx } = o;
    const fxZh = fx === "glass" ? "毛玻璃" : "普通";
    const p = st.ppt;
    const rows = Object.keys(ROLE_ZH).map((k) =>
      `| ${ROLE_ZH[k]} | #${c.roles[k]} | ${ROLE_USE[k]} |`).join("\n");
    let fixNote = "";
    if (c.fix) fixNote = `\n> 说明：${c.act}这是为了让${st.name.zh}的撞色感出得来，请照用，不要换回配色原色。\n`;
    const glassNote = fx === "glass"
      ? "\n7. 毛玻璃效果：母版已在底层放了模糊色团，卡片是半透明色块加白色细边和柔和投影。新增的卡片照这个做法，不要做成不透明色块。"
      : "";
    return `# 请用这套母版把我的文档做成 PPT

请用附件「${o.files.tplName}」的版式和配色，把我提供的文档做成一份 PPT（.pptx）。附件「${o.files.prevName}」是这套母版 6 个版式的样子，供你参考。

## 这一组

- 配色：${pa.name.zh}（${pa.id}）
- 风格：${st.name.zh}（${st.id}）
- 效果：${fxZh}
- 口令：GP1:${pa.id}/${st.id}/${fx}

## 必须遵守

1. 只用母版里的 6 个版式新建页面：封面、目录、章节页、正文、正文 + 引文、结尾页。不要另画版式，不要改动母版里的色块、线条和装饰。文件里已有 6 张示例页，可以直接改内容复用，用不上的删掉。
2. 文字放进占位符，遵守占位符提示里的字数上限；放不下就拆成两页，不要缩小字号。
3. 颜色只用下面五色：

| 用途 | 色值 | 用在哪 |
| --- | --- | --- |
${rows}
${fixNote}
4. 字体统一用微软雅黑，不要混用其他字体。
5. 示例页里的元素设好了逐个淡入的动画；新页面照同样方式设置。
6. 保留文件属性里「AI 辅助生成」的标识。${glassNote}

## ${st.name.zh}的风格要点

- 一句话：${st.tagline.zh}
- 版式倾向：${p.layouts.map(zh).join("、")}
- 常用元素：${p.motifs.map(zh).join("、")}
- 禁止：${p.forbid.map(zh).join("、")}
- 圆角：${p.radius ? "可以有" : "不要"}；投影：${p.shadow ? "可以有" : "不要"}；信息密度：${zh(p.density)}
- 配色做法：${(p.colorRule && p.colorRule.note && p.colorRule.note.zh) || "按上面五色的用途来"}

## 页数和结构

- 封面 1 页、目录 1 页；每一章先放 1 张章节页，再放 2 到 4 张正文页；最后 1 页结尾页。
- 有金句或关键结论的地方，用「正文 + 引文」版式。

## 交付

- 输出 .pptx 文件。
- 做完列出每一页的标题，并标出哪些地方拆了页或删减了内容。
- 如果你装了 GarmanPPT 技能，也同时遵守技能里的规范；两者冲突时，以本母版和本提示词为准。
`;
  }

  function readme(o, skillLine) {
    const { style: st, palette: pa, fx } = o;
    const fxZh = fx === "glass" ? "毛玻璃" : "普通";
    return `GarmanPPT 组合包：${st.name.zh} × ${pa.name.zh}（${fxZh}）

怎么用
1. 打开你的智能体（Claude、ChatGPT、Kimi、豆包、WorkBuddy 等能读写 pptx 的都可以）。
2. 上传三样东西：「${o.files.tplName}」「${o.files.prevName}」和你自己的文档。
3. 打开「提示词.md」，把全文复制粘贴到对话框发送。
4. 收到 PPT 后打开检查；哪页不满意，直接告诉它改哪页。

不用智能体也可以：直接打开母版 .pptx，在每个版式里填内容。

${skillLine}

这一组的在线页面：${o.pageUrl}
数据版本 ${o.version}。母版由赵盾 AI 学习工作室制作，AI 辅助生成，经人工审核。
`;
  }

  async function fetchBytes(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url} ${r.status}`);
    return new Uint8Array(await r.arrayBuffer());
  }

  async function download(o) {
    const enc = new TextEncoder();
    const base = `GarmanPPT-${o.style.name.zh}-${o.palette.name.zh}${o.fx === "glass" ? "-毛玻璃" : ""}`;
    o.files.tplName = `母版-${o.style.name.zh}-${o.palette.name.zh}${o.fx === "glass" ? "-毛玻璃" : ""}.pptx`;
    o.files.prevName = `预览-${o.style.name.zh}-${o.palette.name.zh}${o.fx === "glass" ? "-毛玻璃" : ""}.jpg`;
    const entries = [
      { name: `${base}/${o.files.tplName}`, data: await fetchBytes(o.files.tpl) },
      { name: `${base}/${o.files.prevName}`, data: await fetchBytes(o.files.prev) },
      { name: `${base}/提示词.md`, data: enc.encode(prompt(o)) },
    ];
    // 技能包：服务器上有同源副本（version.json 的 skill.local）就一起打包；没有就给下载链接
    let skillLine = `技能包（可选）：${o.skill.zip}`;
    if (o.skill.local) {
      try {
        const name = o.skill.local.split("/").pop();
        const data = await fetchBytes(o.skill.localUrl);
        // 服务器把不存在的路径回落成网页时也是 200，所以再看一眼 zip 文件头「PK」
        if (data[0] !== 0x50 || data[1] !== 0x4b) throw new Error("not a zip");
        entries.push({ name: `${base}/${name}`, data });
        skillLine = `技能包（可选）：已放在本文件夹的 ${name}，装了技能的智能体会同时遵守技能里的规范。`;
      } catch (e) { /* 副本取不到就退回链接 */ }
    }
    entries.unshift({ name: `${base}/先读我.txt`, data: enc.encode(readme(o, skillLine)) });
    const blob = makeZip(entries);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${base}.zip`;
    document.body.appendChild(a); a.click();
    setTimeout(() => a.remove(), 1000);
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    return { name: a.download, size: blob.size, files: entries.map((e) => e.name) };
  }

  window.GarmanPack = { download, prompt, makeZip };
})();
