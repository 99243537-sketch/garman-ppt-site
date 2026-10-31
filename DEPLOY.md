# GarmanPPT 网站部署说明（给 Eddy）

> 仓库里的 `site/ppt/` 对应服务器上的 `/ppt/`。下文说的「包」就是 Release 里的 zip，结构与 `site/ppt/` 相同。

> 数据版本 0.5.0 · 2026-10-31 · 对应方案 v0.2（第 5、5A、5B 节）

Eddy 你好，这一包是「配色 × 风格」组合挑选页上线需要的全部东西。网站只放静态文件，**没有后端、不调模型、不做在线生成**。

## 1. 包里有什么

```
├─ 部署说明.md            本文件
├─ site-data/             网站唯一数据（脚本生成，勿手改）
│  ├─ version.json        数据版本、构建日期、技能下载地址
│  ├─ palettes.json       13 套配色
│  ├─ styles.json         16 种风格
│  ├─ matrix.json         208 格兼容矩阵（含三挡）
│  └─ rules.json          三挡切分比例、综合分权重、文档类型表、可用效果
├─ templates/             208 份「下载这套主题」.pptx（16 种风格 × 13 套配色）
├─ previews/              208 张 6 页预览图
├─ pick/                  组合挑选页（静态原型）
│  ├─ index.html
│  ├─ pick.css
│  └─ pick.js
└─ tools/                 重新生成 site-data 用（不用上线）
   ├─ export-styles.cjs
   └─ build_site_data.py
```

## 2. 放到服务器哪里（建议，路径请你确认）

```
/ppt/                     现有技能介绍页，加一个「组合挑选」入口链接到 /ppt/pick/
/ppt/pick/                ← pick/ 三个文件
/ppt/site-data/           ← site-data/ 五个 JSON
/ppt/templates/           ← templates/ 208 个 .pptx（见第 5 节）
/ppt/previews/            ← previews/ 208 张预览图
/design-styles/           风格库 v2（已有；挑选页的「详细说明」链接指向 /design-styles/?style=<id>）
```

`pick.js` 默认从 `../site-data/` 读数据。如果你把 JSON 放到别处，在 `index.html` 里 `pick.js` 之前加一行：

```html
<script>window.GARMAN_DATA_BASE = "/data/garman/0.2.0/";</script>
```

本地预览：在包的根目录运行 `python3 -m http.server`，打开 `http://localhost:8000/pick/`（直接双击 html 会因为浏览器禁止本地 fetch 而读不到数据）。

## 3. 缓存（Cloudflare）

| 文件 | 建议 |
|---|---|
| `site-data/version.json` | 不缓存（`Cache-Control: no-store`）。页面每次都实时读它 |
| 其他 JSON、`pick.js`、`pick.css` | 可以缓存；每次更新数据后清一次缓存，或者改用带版本号的目录（`/ppt/site-data/0.2.0/`）并改 `GARMAN_DATA_BASE` |
| `templates/*.pptx`、`previews/*.jpg` | 长缓存，文件名里带 `-v1`，换版本就换文件名 |

## 4. 怎么拉取、怎么更新

从 GitHub 拉取：仓库 [99243537-sketch/garman-ppt-site](https://github.com/99243537-sketch/garman-ppt-site) 每次打 `site-v*` 标签，Release 里会自动出一个 `garman-site-<版本>.zip`，内容就是仓库的 `site/ppt/` 加本说明。你沿用「定时从 GitHub 拉取」：查最新 Release，版本变了就下载解压，覆盖到服务器的 `/ppt/`（会更新 `pick/`、`site-data/`、`templates/`、`previews/` 四个目录，不碰 `/ppt/` 下其他文件）。判断有没有新版本看 Release 标签或 `site-data/version.json` 的 `version`。

```bash
# 示例：取最新 Release 的 zip（公开仓库，不需要令牌）
curl -sL https://api.github.com/repos/99243537-sketch/garman-ppt-site/releases/latest \
  | grep -o '"browser_download_url": *"[^"]*garman-site-[^"]*\.zip"' | cut -d'"' -f4
```

在线预览（不用部署也能看）：https://99243537-sketch.github.io/garman-ppt-site/ （GitHub Pages，随 main 分支自动更新）。

需要自己重新生成数据时（一般不用）：

```bash
# 在仓库根目录；tools/sources/ 里已放了当前用的两份源数据
node tools/export-styles.cjs <风格库>/design-styles/data.js tools/sources/styles-v2.json   # 风格库更新时才需要
python3 tools/build_site_data.py tools/sources/matrix-data.json tools/sources/styles-v2.json site/ppt/site-data
```

## 5. 模板下载与预览图

16 种风格 × 13 套配色，**208 个组合全部有模板和预览图**（兼容矩阵判为冲突的组合也照样有，页面标「反对」）：

- `templates/garman-<风格id>-<配色id>-v1.pptx`：6 个版式（封面、目录、章节页、正文、正文 + 引文、结尾页）加示例页，元素逐个淡入，微软雅黑，敏感词自检 0 命中。每份约 40 KB。
- `previews/<同名>.jpg`：6 页拼图，约 2000×760，每张约 100 KB。
- 7 种可生成风格各有一套手工定稿（`styles.json` 的 `template`），其余由 `tools/masters/build_all.py` 按兼容矩阵取好的五色批量生成。

对应关系写在 `styles.json` 每种风格的 `templates` 和 `previews`（键是配色 id）。挑选页任选一个组合都显示真实预览图、点开看大图，「下载模板」都能下载。技能还不能生成的 9 种风格（`status: preview`）在列表里和其他风格一样，不加标记，只是「用 AI 生成成品」按钮变灰，写「即将支持」。

全部文件约 32 MB（模板 8.6 MB + 预览图 23 MB）。

**风格签名色（0.5.0 起）**：大胆风格不再被 Garman 自然色的低彩度卡住。底色、文字和主色仍取自所选配色；波普、蒸汽波、风格派、构成主义、千禧未来风、孟菲斯、包豪斯七种风格的色块与点缀（`roles` 的 secondary / accent）换成风格自己的签名色，从候选里挑与主色色相相距最远的一到两个。矩阵分相应上调（只升不降，新分 = max(原分, 75 + 0.25 × 原分)），原来 39 个「冲突」组合因此全部解除。

## 6. 页面怎么工作（如果你要按站点风格重写，看这一节就够）

**模式转盘**：页面顶部仿相机的模式拨盘，四挡 P / S / C / M。点字母、用手指或鼠标拖着转（松手吸附到最近一挡），或聚焦后按方向键切换。

**文档类型**默认「讲课 / 培训」；URL 里 `doc=` 留空表示「不指定」。开场理由那句话放在结果区最下面。电脑版结果区占满剩余宽度并停在视口内，样张最大约为视口高度减去 220 px。

| 挡位 | 用户先选 | 另一半 | 排序与挡位 | 自动选 |
|---|---|---|---|---|
| **P 程序自动** | 不用选 | 自动 | 风格按各自最高分排，配色按综合分排，都标三挡 | 打开即选好综合第一名 |
| **S 风格优先** | 风格（原顺序） | 配色按该风格的综合分排，标三挡 | 有 | 选完风格自动选第一名配色 |
| **C 色彩优先** | 配色（原顺序，列表放左边） | 风格按该配色的综合分排，标三挡，可生成的在前 | 有 | 选完配色自动选第一名风格 |
| **M 手动** | 都自己选，原顺序 | 不排序、不显示分数和挡位、不出文档类型 | 无 | 不自动选 |

- **综合分**：`矩阵分 s + 文档类型加分 − 毛玻璃冲突扣分`，权重在 `rules.json` 的 `weights`，上限 `clamp`。
- **三挡**：矩阵结论 `l` 为「冲突」的一律反对；其余**不设分数线**，把可生成风格（`status: ready`）的组合按综合分排名（`rules.json` 的 `tierPool` 改成 `all` 就按全部 208 格），按 `tiers[].share`（现在是 1/4、1/2、1/4）切分，分界线上的同分归高的一挡；还不能生成的风格套用同一组分界分数。分界分数随所选文档类型变化，页面按当前选择重算（`pick.js` 的 `tierCuts()`）。
- **开场句**：P / S / C 自动选中时上方显示一句理由，结尾「可以换」；用户自己点了另一半就不再显示。
- **反对挡**：P、S 挡给 `alt` 里的替换配色；C 挡配色是用户定的，改为推荐 2–3 种可生成的风格。
- **M 挡的冲突组合**：只显示一句「这套组合在兼容矩阵里是冲突，{why} 仍可以用」，不给替换建议。
- **效果**：`rules.json` 的 `effectsAvailable` 现在只有 `plain`，毛玻璃选项显示「即将支持」且不可选。

**结果区**：6 页预览图（选毛玻璃效果时退回 SVG 示意样张，按该格 `roles` 五色上色）、「下载模板」、「用 AI 生成成品」（展开三步：下载技能包、复制口令、发给智能体）。口令格式：

```
用 GarmanPPT 做成 PPT。配色：银杏；风格：新粗野主义；效果：普通。
GP1:ginkgo/neubrutalism/plain
```

`status: preview` 的风格可以看预览、下载模板，但「用 AI 生成成品」不可点，按钮上写「即将支持」。

**URL 参数**（可分享）：`?mode=p|s|c|m&s=<风格id>&p=<配色id>&doc=<文档类型id>&fx=plain|glass`。

**关键字段速查**

| 文件 | 字段 | 说明 |
|---|---|---|
| matrix.json | `cells["editorial|amazonite"]` | 键是 `风格id|配色id` |
| | `s` | 矩阵兼容分 0–100 |
| | `l` | 矩阵结论：兼容 / 可调 / 冲突 |
| | `tier` | 三挡（不指定文档类型、普通效果时）：recommend / neutral / against |
| | `why` `act` | 原因、自动调整做法（中文） |
| | `roles` | 五色：background / text / primary / secondary / accent，六位十六进制无 # |
| | `alt` | 冲突时的替换配色 id，最多 3 个 |
| | `sig` | 用了风格签名色的格才有：签名色色值（已写进 `roles` 的 secondary / accent） |
| styles.json | `status` | ready 可生成 / preview 只能看 |
| | `signature` | 风格签名色（波普、蒸汽波、风格派、构成主义、千禧、孟菲斯、包豪斯有） |
| | `docTypes` `effects.glass` | 综合分加减分用 |
| palettes.json | `colors` `default` | 九色；天河石是默认 |
| rules.json | `tiers` `weights` `docTypes` `effectsAvailable` | 页面必须从这里读，不要写死；比例改成各 1/3 时只改 `share` |

## 7. 上线后请帮忙验一下

1. `/ppt/pick/` 打开后自动选中「编辑杂志风 × 天河石」，上方有一句理由。
2. 转盘拨到 C，选「吉丁虫」，左列是配色、右列是风格并自动选中第一名；拨到 M：列表变成原顺序，没有分数；选「波普艺术 × 鹦鹉螺」，预览里能看到波普的红、蓝签名色。
3. 任选一种风格和任一配色（共 208 组），都能看到 6 页预览图并下到 pptx；「复制」按钮能复制口令（需要 https）。
4. 手机宽度下没有横向滚动。
5. 改一次 `version.json` 后刷新页面，页脚版本号立即变化（说明没被缓存）。

## 8. 还没定、可能会变的

切分比例、文档类型表、毛玻璃兼容表以后还可能调，只会改 JSON 的值，**字段和结构不变**，你不用改页面。另外请你回复两件事：挑选页用这个原型直接上线还是你重写（方案 Q8）；JSON 的实际放置路径（Q9）。

另：/ppt/ 介绍页还停在 0.3.0，技能已到 0.3.2，麻烦顺手同步版本号和下载链接。
