// StyleEngine（实验）：版式风格与配色解耦。
// 风格只决定「怎么画」（描边、阴影、圆角、编号样式、底色分配），颜色一律取自 Garman 配色的角色色。
// 同一套版式代码 × 任意风格 × 任意配色。
const { THEMES } = require("./themes.js");

const mix = (hex, t, to = "FFFFFF") => {
  const a = parseInt(hex, 16), b = parseInt(to, 16);
  const ch = (n, s) => (n >> s) & 255;
  return [16, 8, 0].map((s) => Math.round(ch(a, s) + (ch(b, s) - ch(a, s)) * t).toString(16).padStart(2, "0")).join("").toUpperCase();
};
const lum = (hex) => { const n = parseInt(hex, 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255; };

const STYLES = {
  // 编辑杂志风：浅底、细线分栏、大号强调色编号、无边框卡片
  editorial: {
    name: "编辑杂志风", tension: "low",
    make: (T) => ({
      bg: T.pale, title: T.base, ink: T.ink, muted: T.muted, accent: T.accent, num: T.accent, rule: T.base, hair: T.line,
      cover: { bg: T.pale }, section: { bg: T.base, num: T.main, title: "FFFFFF", sub: T.soft },
      end: { bg: T.pale }, border: 0, shadow: 0, radius: 0, pad: 0, gap: 0.45,
      fills: [T.pale, T.pale, T.pale, T.pale], numPad: true,
    }),
  },
  // 新粗野主义：粗黑描边、硬阴影、色块卡片轮换
  neubrutalism: {
    name: "新粗野主义", tension: "high",
    make: (T) => {
      const K = "121212", second = mix(T.accent, 0.45);
      return {
        bg: T.pale, title: K, ink: K, muted: "3A3A3A", accent: T.accent, num: K, rule: K, hair: K,
        cover: { bg: T.pale }, section: { bg: second, num: K, title: K, sub: K },
        end: { bg: T.main }, border: 2.25, shadow: 0.09, radius: 0.08, pad: 0.3, gap: 0.42,
        fills: [T.main, second, "FFFFFF", T.soft], numPad: true,
      };
    },
  },
};

// 文档类型 → 风格（第一版只用关键词粗分，默认编辑杂志风）
function pickStyle(doc) {
  const all = doc.paras.map((p) => p.text).join("");
  if (/活动|开学|嘉年华|招募|比赛|运动会|少儿/.test(all)) return "neubrutalism";
  return "editorial";
}

// 高张力风格 × 低饱和（雅致）配色：加粗描边、焦点色提高对比，生成前提醒
function resolve(styleKey, themeName) {
  const T = THEMES[themeName], st = STYLES[styleKey];
  const S = st.make(T), notes = [];
  if (st.tension === "high" && T.tier === "雅致") {
    S.border = 3; S.shadow = 0.12;
    S.fills = S.fills.map((f) => (f === "FFFFFF" ? f : mix(f, 0.12, lum(f) > 0.5 ? "000000" : "FFFFFF")));
    notes.push(`${st.name} × ${themeName}：配色偏素雅，已自动加粗描边、焦点色提高约 12% 对比度。`);
  }
  return { S, T, name: st.name, notes };
}

module.exports = { STYLES, pickStyle, resolve, mix };
