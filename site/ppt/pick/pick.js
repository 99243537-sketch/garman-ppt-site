/*
 * GarmanPPT 组合挑选页（静态原型）
 * 只读 site-data 里的 JSON，不连任何后端。数据路径默认 ../site-data/，
 * 部署时可在引入本脚本前设置 window.GARMAN_DATA_BASE 改掉。
 *
 * 仿相机模式转盘，四挡：
 *   P 程序自动：风格和配色都自动选（综合分第一名），并说明理由。
 *   S 风格优先：用户选风格，配色按综合分排序、标三挡，自动选该风格下第一名。
 *   C 色彩优先：用户选配色，风格按综合分排序、标三挡，自动选该配色下第一名（只在可生成风格里选）。
 *   M 手动：按数据原顺序列出，不排序、不显示挡位、不自动选；
 *          选到冲突组合只给一句软提示和原因，不推荐替换。
 * 综合分 = 矩阵分 + 文档类型加分 + 效果冲突扣分；三挡按排名切分（比例见 rules.json）。
 * URL：?mode=p|s|c|m&s=<风格id>&p=<配色id>&doc=<文档类型id>&fx=plain|glass
 */
(function () {
  const BASE = window.GARMAN_DATA_BASE || "../site-data/";
  const $ = (id) => document.getElementById(id);
  const TIER_ZH = { recommend: "推荐", neutral: "中性", against: "反对" };
  const MODES = {
    p: { name: "P · 程序自动", desc: "风格和配色都替你选好，可以再换。", angle: -66 },
    s: { name: "S · 风格优先", desc: "你选风格，配色按合适程度排好并自动选第一名。", angle: -22 },
    c: { name: "C · 色彩优先", desc: "你选配色，风格按合适程度排好并自动选第一名。", angle: 22 },
    m: { name: "M · 手动", desc: "按原顺序列出，不排序、不推荐，全部自己定。", angle: 66 },
  };
  const ORDER = ["p", "s", "c", "m"];
  let D = null;
  const DEFAULT_DOC = "teaching";   // 文档类型默认「讲课 / 培训」
  const S = { mode: "p", doc: DEFAULT_DOC, fx: "plain", style: null, pal: null, auto: false };

  Promise.all(["palettes", "styles", "matrix", "rules", "version"].map((n) =>
    fetch(BASE + n + ".json", { cache: n === "version" ? "no-store" : "default" }).then((r) => r.json())
  )).then(([p, s, m, r, v]) => {
    D = { pals: p.palettes, styles: s.styles, cells: m.cells, rules: r.rules, docTypes: r.docTypes, ver: v };
    D.palById = Object.fromEntries(D.pals.map((x) => [x.id, x]));
    D.styleById = Object.fromEntries(D.styles.map((x) => [x.id, x]));
    $("ver").textContent = v.version + " · " + v.built;
    $("skillLink").href = v.skill.zip;
    for (const d of D.docTypes) $("doc").add(new Option(d.zh, d.id));
    readUrl();
    bind();
    if (!S.style || !S.pal) autoPick();
    render();
  }).catch((e) => {
    document.querySelector("main").innerHTML = '<p class="note warn">数据没有加载成功：' + e + "</p>";
  });

  /* ---------- 计分 ---------- */
  function cell(sid, pid) { return D.cells[sid + "|" + pid]; }
  function score(sid, pid) {
    const r = raw(sid, pid);
    return { ...r, tier: tierOf(r.total, cell(sid, pid).l) };
  }
  function raw(sid, pid) {
    const c = cell(sid, pid), st = D.styleById[sid], pa = D.palById[pid], w = D.rules.weights;
    const parts = [{ k: "矩阵兼容分", v: c.s }];
    if (S.doc && st.docTypes.includes(S.doc)) parts.push({ k: "风格适合该文档", v: w.styleDocMatch });
    if (S.doc && pa.docTypes.includes(S.doc)) parts.push({ k: "配色适合该文档", v: w.paletteDocMatch });
    if (S.fx === "glass" && st.effects.glass === "conflict") parts.push({ k: "毛玻璃与风格冲突", v: w.glassConflict });
    if (S.fx === "glass" && st.effects.glass === "adjust") parts.push({ k: "毛玻璃需调整", v: w.glassAdjust });
    const [lo, hi] = D.rules.clamp;
    const total = Math.max(lo, Math.min(hi, parts.reduce((a, b) => a + b.v, 0)));
    return { total, parts };
  }
  // 三挡按排名切分：组合按综合分排序，前 share 比例为推荐，依次类推；同分归高的一挡。
  // 排名范围由 rules.tierPool 决定：ready 只算可生成的风格（预览风格套用同一组分界分数），all 算全部。
  // 分界分数随文档类型和效果变化，所以每次按当前选择重算（208 格，开销很小）。
  let cutKey = null, cuts = [];
  function tierCuts() {
    const key = S.doc + "|" + S.fx;
    if (key === cutKey) return cuts;
    const pool = Object.keys(D.cells).filter((k) => D.rules.tierPool === "all" || D.styleById[k.split("|")[0]].status === "ready");
    const xs = pool.map((k) => raw(...k.split("|")).total).sort((a, b) => b - a);
    let acc = 0; cuts = [];
    for (const t of D.rules.tiers.slice(0, -1)) { acc += t.share; cuts.push(xs[Math.max(0, Math.round(xs.length * acc) - 1)]); }
    cutKey = key; return cuts;
  }
  function tierOf(total, label) {
    if (D.rules.conflictIsAgainst && label === "冲突") return "against";
    const c = tierCuts(), i = c.findIndex((cut) => total >= cut);
    return D.rules.tiers[i < 0 ? D.rules.tiers.length - 1 : i].id;
  }
  // 排序：综合分高在前；同分时默认配色天河石在前，再按原顺序
  function rankedPals(sid) {
    return D.pals.map((p) => ({ p, sc: score(sid, p.id) }))
      .sort((a, b) => b.sc.total - a.sc.total || (b.p.default - a.p.default) || a.p.order - b.p.order);
  }
  // 某配色下的风格排序：可生成的在前
  function rankedStylesFor(pid) {
    return D.styles.map((s) => ({ s, sc: score(s.id, pid) }))
      .sort((a, b) => (b.s.status === "ready") - (a.s.status === "ready") || b.sc.total - a.sc.total || a.s.order - b.s.order);
  }
  function rankedStyles() {
    return D.styles.map((s) => ({ s, best: rankedPals(s.id)[0] }))
      .sort((a, b) => (b.s.status === "ready") - (a.s.status === "ready") || b.best.sc.total - a.best.sc.total || a.s.order - b.s.order);
  }
  // 按当前挡位自动补全另一半；M 挡不自动选
  function autoPick() {
    S.auto = false;
    if (S.mode === "p") {
      const top = rankedStyles()[0];
      S.style = top.s.id; S.pal = top.best.p.id; S.auto = true;
    } else if (S.mode === "s" && S.style) {
      S.pal = rankedPals(S.style)[0].p.id; S.auto = true;
    } else if (S.mode === "c" && S.pal) {
      S.style = rankedStylesFor(S.pal)[0].s.id; S.auto = true;
    }
  }

  /* ---------- 交互 ---------- */
  function setMode(m) {
    if (m === S.mode) return;
    S.mode = m;
    // 换挡时保留「优先」的那一半：S 留风格，C 留配色，M 清空，P 全自动
    if (m === "s") S.pal = null;
    if (m === "c") S.style = null;
    if (m === "m") { S.style = null; S.pal = null; }
    autoPick(); render();
  }
  function bind() {
    document.querySelectorAll("#disk button").forEach((b) => b.onclick = () => setMode(b.dataset.mode));
    document.querySelector(".dial").onkeydown = (e) => {
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (!d) return;
      e.preventDefault();
      setMode(ORDER[(ORDER.indexOf(S.mode) + d + ORDER.length) % ORDER.length]);
    };
    bindDrag();
    $("doc").onchange = (e) => { S.doc = e.target.value; autoPick(); render(); };
    document.querySelectorAll('input[name="fx"]').forEach((r) => r.onchange = () => {
      S.fx = r.value; autoPick(); render();
    });
    $("aiBtn").onclick = () => {
      if ($("aiBtn").getAttribute("aria-disabled") === "true") return;
      const open = $("ai").hidden; $("ai").hidden = !open; $("cmdBox").hidden = !open; $("aiBtn").setAttribute("aria-expanded", open);
    };
    $("packBtn").onclick = async () => {
      const st = D.styleById[S.style], pa = D.palById[S.pal], fx = S.fx;
      const pick = (kind) => ((fx === "glass" ? st["glass" + kind[0].toUpperCase() + kind.slice(1)] : st[kind]) || {})[pa.id];
      const tpl = pick("templates"), prev = pick("previews");
      if (!tpl || !prev) return;
      const btn = $("packBtn"), msg = $("packStatus");
      btn.disabled = true; msg.textContent = "正在打包…";
      try {
        const sk = D.ver.skill || {};
        const r = await window.GarmanPack.download({
          style: st, palette: pa, cell: cell(S.style, S.pal), fx,
          files: { tpl: "../" + tpl, prev: "../" + prev },
          version: D.ver.version, pageUrl: location.href,
          skill: { zip: sk.zip, local: sk.local || null, localUrl: sk.local ? "../" + sk.local : null },
        });
        msg.textContent = `已下载 ${r.name}（${(r.size / 1048576).toFixed(1)} MB）`;
      } catch (e) {
        msg.textContent = "打包没成功：" + e.message + "。可以先用上面的「下载模板」。";
      } finally { btn.disabled = false; }
    };
    $("copy").onclick = () => {
      navigator.clipboard.writeText($("cmd").textContent).then(() => {
        $("copy").textContent = "已复制"; setTimeout(() => $("copy").textContent = "复制", 1500);
      });
    };
  }
  // 触控 / 鼠标拖动转盘：跟手转动，松手吸附到最近的一挡；轻点字母仍按点击处理
  function bindDrag() {
    const dial = document.querySelector(".dial"), disk = $("disk");
    let start = null;
    const angleAt = (e) => {
      const r = dial.getBoundingClientRect();
      return Math.atan2(e.clientX - (r.left + r.width / 2), -(e.clientY - (r.top + r.height / 2))) * 180 / Math.PI;
    };
    dial.addEventListener("pointerdown", (e) => {
      start = { a: angleAt(e), rot: -MODES[S.mode].angle, moved: false, id: e.pointerId };
    });
    dial.addEventListener("pointermove", (e) => {
      if (!start || e.pointerId !== start.id) return;
      let d = angleAt(e) - start.a;
      if (d > 180) d -= 360; if (d < -180) d += 360;
      if (!start.moved && Math.abs(d) < 6) return;
      if (!start.moved) { start.moved = true; dial.setPointerCapture(e.pointerId); dial.classList.add("dragging"); }
      // 限制在两端挡位之间
      const rot = Math.max(-MODES.m.angle - 12, Math.min(-MODES.p.angle + 12, start.rot + d));
      disk.style.transform = `rotate(${rot}deg)`;
      start.cur = rot;
    });
    const end = () => {
      if (!start) return;
      const s = start; start = null;
      if (!s.moved) return;            // 没拖动：交给按钮的点击
      dial.classList.remove("dragging");
      const near = ORDER.reduce((a, m) => Math.abs(-MODES[m].angle - s.cur) < Math.abs(-MODES[a].angle - s.cur) ? m : a, S.mode);
      if (near === S.mode) renderDial(); else setMode(near);
    };
    dial.addEventListener("pointerup", end);
    dial.addEventListener("pointercancel", end);
  }

  function readUrl() {
    const q = new URLSearchParams(location.search);
    if (MODES[q.get("mode")]) S.mode = q.get("mode");
    if (q.has("doc")) S.doc = D.docTypes.some((d) => d.id === q.get("doc")) ? q.get("doc") : "";
    if (q.get("fx") === "glass" && D.rules.effectsAvailable.includes("glass")) S.fx = "glass";
    if (!D.rules.effectsAvailable.includes("glass")) {   // 首批只做普通效果
      const g = document.querySelector('input[name="fx"][value="glass"]');
      g.disabled = true; g.parentNode.lastChild.textContent = " 毛玻璃（即将支持）";
    }
    if (D.styleById[q.get("s")]) S.style = q.get("s");
    if (D.palById[q.get("p")]) S.pal = q.get("p");
    $("doc").value = S.doc;
    document.querySelector(`input[name="fx"][value="${S.fx}"]`).checked = true;
  }
  function writeUrl() {
    const q = new URLSearchParams();
    q.set("mode", S.mode);
    if (S.style) q.set("s", S.style);
    if (S.pal) q.set("p", S.pal);
    if (S.mode !== "m" && S.doc !== DEFAULT_DOC) q.set("doc", S.doc);   // 空串表示「不指定」
    if (S.fx !== "plain") q.set("fx", S.fx);
    history.replaceState(null, "", "?" + q);
  }

  /* ---------- 渲染 ---------- */
  function swatch(p) {
    return '<span class="sw">' + ["pale", "main", "deep", "accent", "base"].map((k) => `<i style="background:#${p.colors[k]}"></i>`).join("") + "</span>";
  }
  function li(html, pressed, onclick) {
    const el = document.createElement("li"), b = document.createElement("button");
    b.innerHTML = html; b.setAttribute("aria-pressed", pressed); b.onclick = onclick;
    el.appendChild(b); return el;
  }
  const badge = (sc, prefix) => `<span class="badge ${sc.tier}">${prefix || TIER_ZH[sc.tier]} ${sc.total}</span>`;
  const styleHtml = (s, tag) => `<span class="nm">${s.name.zh}<span class="sub">${s.tagline.zh}</span></span>${tag || ""}`;
  const palHtml = (p, tag) => `${swatch(p)}<span class="nm">${p.name.zh}<span class="sub">${p.kind} · ${p.tier}</span></span>${tag || ""}`;

  function renderDial() {
    $("disk").style.transform = `rotate(${-MODES[S.mode].angle}deg)`;
    document.querySelectorAll("#disk button").forEach((b) => {
      const a = MODES[b.dataset.mode].angle;
      // 字母沿外圈排布，随转盘一起转，和真实拨盘一样
      b.style.transform = `rotate(${a}deg) translateY(-44px)`;
      b.setAttribute("aria-checked", b.dataset.mode === S.mode);
    });
    $("modeName").textContent = MODES[S.mode].name;
    $("modeDesc").textContent = MODES[S.mode].desc;
  }

  function render() {
    const m = S.mode;
    renderDial();
    $("docWrap").hidden = m === "m";
    const A = $("listA"), B = $("listB");
    A.innerHTML = ""; B.innerHTML = "";
    const colorFirst = m === "c";
    $("headA").textContent = colorFirst ? "1 · 配色" : "1 · 风格";
    $("headB").textContent = colorFirst ? "2 · 风格" : "2 · 配色";
    A.classList.toggle("pals", colorFirst); B.classList.toggle("pals", !colorFirst);

    if (colorFirst) {
      // C：配色按原顺序，选中后风格按该配色排序
      for (const p of D.pals) A.appendChild(li(palHtml(p), p.id === S.pal, () => { S.pal = p.id; autoPick(); render(); }));
      $("hintB").textContent = "先选一套配色。";
      $("hintB").hidden = !!S.pal;
      if (S.pal) for (const { s, sc } of rankedStylesFor(S.pal))
        B.appendChild(li(styleHtml(s, badge(sc)), s.id === S.style, () => { S.style = s.id; S.auto = false; render(); }));
    } else {
      // P：风格按各自最高分排序；S、M：风格按原顺序
      const styles = m === "p" ? rankedStyles() : D.styles.map((s) => ({ s }));
      for (const { s, best } of styles)
        A.appendChild(li(styleHtml(s, best ? badge(best.sc, "最高") : ""), s.id === S.style, () => {
          S.style = s.id;
          if (m === "p" || m === "s") { S.pal = rankedPals(s.id)[0].p.id; S.auto = true; }
          render();
        }));
      $("hintB").textContent = "先选一种风格。";
      $("hintB").hidden = !!S.style;
      if (S.style) {
        const pals = m === "m" ? D.pals.map((p) => ({ p })) : rankedPals(S.style);
        for (const { p, sc } of pals)
          B.appendChild(li(palHtml(p, sc ? badge(sc) : ""), p.id === S.pal, () => { S.pal = p.id; S.auto = false; render(); }));
      }
    }

    renderOpening();
    renderResult();
    writeUrl();
  }

  function renderOpening() {
    const el = $("opening");
    if (S.mode === "m" || !S.auto || !S.style || !S.pal) { el.hidden = true; return; }
    const st = D.styleById[S.style], pa = D.palById[S.pal], sc = score(S.style, S.pal);
    const doc = D.docTypes.find((d) => d.id === S.doc);
    const why = sc.parts.map((x, i) => `${x.k} ${x.v > 0 && i ? "+" : ""}${x.v}`).join("，");
    const byDoc = doc ? "（按「" + doc.zh + "」）" : "";
    const lead = {
      p: sc.tier === "recommend" ? `我用了「${st.name.zh} × ${pa.name.zh}」` : `推荐挡里没有组合，先用了分数最高的「${st.name.zh} × ${pa.name.zh}」`,
      s: `「${st.name.zh}」配「${pa.name.zh}」最合适`,
      c: `「${pa.name.zh}」配「${st.name.zh}」最合适`,
    }[S.mode];
    el.innerHTML = `${lead}${byDoc}：综合 ${sc.total} 分（${why}）。${cell(S.style, S.pal).why} 可以换。`;
    el.hidden = false;
  }

  function renderResult() {
    const has = S.style && S.pal;
    $("out").hidden = !has;
    const note = $("note");
    note.hidden = true; note.className = "note";
    if (!has) { $("preview").innerHTML = ""; return; }
    const st = D.styleById[S.style], pa = D.palById[S.pal], c = cell(S.style, S.pal);
    // 16 种风格都有真实模板的 6 页预览图；毛玻璃版只有兼容毛玻璃的风格才有，没有时用按五色上色的示意样张
    const files = (kind) => (S.fx === "glass" ? st["glass" + kind[0].toUpperCase() + kind.slice(1)] : st[kind]) || {};
    const shot = files("previews")[pa.id];
    $("preview").classList.toggle("photo", !!shot);
    $("preview").innerHTML = shot
      ? `<a href="../${shot}" target="_blank" rel="noopener" title="打开大图"><img src="../${shot}" alt="${st.name.zh} × ${pa.name.zh} 模板 6 页预览" loading="lazy"></a>`
      : slide(c.roles, st, S.fx === "glass");

    const msgs = [];
    if (S.mode !== "m") {
      const sc = score(S.style, S.pal);
      if (sc.tier === "against") {
        // C 挡里配色是用户定的，替换建议给风格；其余挡给配色
        const alt = S.mode === "c"
          ? rankedStylesFor(S.pal).filter((x) => x.s.status === "ready" && x.sc.tier !== "against").slice(0, 3).map((x) => x.s.name.zh).join("、")
          : c.alt.map((id) => D.palById[id].name.zh).join("、");
        msgs.push(`不推荐：${c.why}${alt ? " 可以换成 " + alt + "。" : ""}`);
      } else if (c.l === "可调") msgs.push(`会自动调整：${c.act}`);
    } else if (c.l === "冲突") {
      msgs.push(`提示：这套组合在兼容矩阵里是冲突，${c.why} 仍可以用。`);
    }
    if (S.fx === "glass" && st.effects.glass === "conflict") msgs.push("提示：这种风格的禁止项里有柔和投影或渐变，和毛玻璃效果冲突。");
    if (msgs.length) { note.innerHTML = msgs.join("<br>"); note.hidden = false; if (/冲突|不推荐/.test(note.textContent)) note.classList.add("warn"); }

    const fxZh = S.fx === "glass" ? "毛玻璃" : "普通";
    $("combo").textContent = `${st.name.zh} × ${pa.name.zh} · ${fxZh}`;
    $("cmd").textContent = `用 GarmanPPT 做成 PPT。配色：${pa.name.zh}；风格：${st.name.zh}；效果：${fxZh}。\nGP1:${pa.id}/${st.id}/${S.fx}`;
    // 组合包靠母版 + 提示词，16 种风格都能用；只要当前效果有模板就可以打包
    const tpl = files("templates")[pa.id];
    const ready = !!(tpl && shot);
    $("aiBtn").setAttribute("aria-disabled", !ready);
    $("aiBtn").textContent = ready ? "用 AI 做成品" : "用 AI 做成品（这一组暂无母版）";
    if (!ready) { $("ai").hidden = true; $("cmdBox").hidden = true; $("aiBtn").setAttribute("aria-expanded", false); }
    $("packStatus").textContent = "";
    $("dlTpl").href = tpl ? "../" + tpl : "#";
    $("dlTpl").setAttribute("aria-disabled", !tpl);
    $("dlTpl").textContent = tpl ? "下载模板" : S.fx === "glass" ? "下载模板（这种风格不做毛玻璃）" : "下载模板（这组暂无）";
    $("detail").href = st.detailUrl;
  }

  // 示意样张：只示意五色角色和圆角、投影、毛玻璃，不代表真实版式
  function slide(r, st, glass) {
    const h = (k) => "#" + r[k];
    const rad = Math.min(st.ppt.radius || 0, 24);
    const hard = st.ppt.motifs.includes("hard-shadow") || st.id === "neubrutalism";
    const stroke = hard ? `stroke="${h("text")}" stroke-width="4"` : "";
    const blobs = glass ? `<circle cx="180" cy="120" r="150" fill="${h("primary")}" opacity=".7"/><circle cx="1120" cy="560" r="190" fill="${h("accent")}" opacity=".55"/><circle cx="820" cy="140" r="110" fill="${h("secondary")}" opacity=".45"/>` : "";
    const card = (x, i) => {
      const fill = glass ? `fill="#ffffff" fill-opacity=".55"` : `fill="${[h("primary"), h("background"), h("secondary")][i]}" ${i === 1 ? `stroke="${h("secondary")}" stroke-width="2"` : ""}`;
      const sh = hard && !glass ? `<rect x="${x + 10}" y="330" width="330" height="250" rx="${rad}" fill="${h("text")}"/>` : "";
      return `${sh}<rect x="${x}" y="320" width="330" height="250" rx="${rad}" ${fill} ${stroke}/>
        <rect x="${x + 30}" y="360" width="150" height="18" rx="4" fill="${i === 1 ? h("primary") : h("text")}" opacity=".85"/>
        <rect x="${x + 30}" y="400" width="250" height="10" rx="3" fill="${h("text")}" opacity=".45"/>
        <rect x="${x + 30}" y="424" width="210" height="10" rx="3" fill="${h("text")}" opacity=".45"/>`;
    };
    return `<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${st.name.zh} 示意样张">
      <defs><filter id="b"><feGaussianBlur stdDeviation="40"/></filter></defs>
      <rect width="1280" height="720" fill="${h("background")}"/>
      <g filter="url(#b)">${blobs}</g>
      <rect x="90" y="96" width="10" height="120" fill="${h("accent")}"/>
      <text x="124" y="160" font-size="64" font-weight="700" fill="${h("text")}" font-family="Microsoft YaHei, sans-serif">${st.name.zh}</text>
      <text x="126" y="210" font-size="26" fill="${h("text")}" opacity=".7" font-family="Microsoft YaHei, sans-serif">${D.palById[S.pal].name.zh} · 示意样张</text>
      ${card(90, 0)}${card(475, 1)}${card(860, 2)}
      <rect x="90" y="640" width="1100" height="2" fill="${h("secondary")}"/>
    </svg>`;
  }
})();
