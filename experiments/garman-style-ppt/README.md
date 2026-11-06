# garman-style-ppt 实验版（0.4.0-exp）

**实验性质，不合并到 main，不发版，不影响 garman-ppt 0.3.x。** 源码从 garman-ppt `tools/doc2ppt/src` 复制后改出，四条铁律不变（只摘不写、原文一段不丢、以脚本校验为准）。

## 相对 0.3.x 的实验改动

| 改动 | 说明 |
|---|---|
| StyleEngine（`src/styles.js`） | 风格只决定「怎么画」（描边、硬阴影、编号样式、底色轮换），颜色全部取 Garman 配色角色色。现有 2 种：编辑杂志风 `editorial`、新粗野主义 `neubrutalism`。plan.json 顶层 `"design"` 或 `--design` 切换 |
| 高张力 × 雅致配色自动补偿 | 新粗野主义配「雅致」档配色时，描边 2.25→3pt、阴影加深、色块对比提高约 12%，生成前提醒 |
| 风格自动选择 | 没写 `design` 时按文档关键词选，默认编辑杂志风；build 时说一句「我用了 X 风格，可以换」 |
| 4 种具名版式 | `quote` 金句、`timeline` 时间轴、`stat` 大数字、`compare` 左右对比 |
| 全部页面逐个淡入 | 封面、目录、章节、标题进页自动依次淡入；内容逐次点击淡入，上一项变淡，最后一击全部恢复并出现结论 |
| `outline` | 生成前打印页面清单 |
| `verify` 质量闸门 | build 后重新打开成品检查：文字逐字来自原文、元素不出界、字号 ≥10pt、动画目标存在、每页有淡入、原文全在备注。不通过不写文件 |

去掉了毛玻璃效果（实验版先只看版式）。

## 用法

```
npm install
node src/cli.js parse 文档.md 工作目录
node src/cli.js outline 工作目录
node src/cli.js build 工作目录 输出.pptx [--design neubrutalism] [--theme 银杏]
node src/cli.js verify 工作目录 输出.pptx
```

## 新版式的 plan.json 写法

```json
{ "type": "quote", "kicker": [..], "quote": ["P004", "金句 ≤60 字"], "support": [["P004", "补充 ≤34 字"]], "notes": ["P004"] }
{ "type": "timeline", "title": [..], "steps": [{ "no": "1", "head": [..], "body": [..], "notes": [..] }], "conclusion": [..], "intro": [..], "end": [..] }
{ "type": "stat", "title": [..], "stats": [{ "label": [..], "value": ["P018", "64"], "unit": ["P018", "个字符"], "body": [..], "notes": [..] }] }
{ "type": "compare", "title": [..], "left": { "head": [..], "points": [[..]], "notes": [..] }, "right": { .. }, "conclusion": [..] }
```

timeline 3–5 步，stat 2–4 个，compare 每栏 1–4 条。数值、单位也必须是原文摘句。

## 示例

`demo/`：《什么是 Skill》原文、plan.json、两个版本的 .pptx 和缩略图。
