# GarmanPPT 网站部署说明（给 Eddy）

> 仓库里的 `site/ppt/` 对应服务器上的 `/ppt/`。下文说的「包」就是 Release 里的 zip，结构与 `site/ppt/` 相同。

> 数据版本 0.6.0 · 2026-10-31 · 对应方案 v0.2（第 5、5A、5B 节）

Eddy 你好，这一包是「配色 × 风格」组合挑选页上线需要的全部东西。网站只放静态文件，**没有后端、不调模型、不做在线生成**。

## 0. 这次更新要点（0.6.0）

和你上次拿到的 0.2.3 包相比：

| 变化 | 说明 |
|---|---|
| 模板从 7 份增加到 260 份 | 16 种风格 × 13 套配色共 208 份普通模板，外加 52 份毛玻璃模板；每份都配一张 6 页预览图（`previews/`，新目录） |
| 开放毛玻璃效果 | `rules.json` 的 `effectsAvailable` 加入 `glass`；`styles.json` 新增 `glassTemplates` / `glassPreviews` |
| 大胆风格会提饱和或加签名色 | `matrix.json` 里七种风格的格子新增 `fix` / `slots` / `sig`，`styles.json` 新增 `signature`；原来的 39 个冲突组合全部解除 |
| 包变大 | 约 40 MB（模板 11 MB + 预览图 29 MB），以前不到 1 MB |
| 发布方式 | 从「赵盾发 zip 给你」改成 GitHub Release 自动附 zip，可以定时拉取（见第 4 节） |

**你这次需要做的**：
1. 按第 4A 节覆盖 `/ppt/` 下的 `pick/`、`site-data/`、`templates/`、`previews/` 四个目录。
2. **清一次 Cloudflare 缓存，包括 `templates/` 和 `previews/`**。这次很多模板保留了原来的文件名（`-v1`）但内容变了，按第 3 节的长缓存规则会读到旧文件。
3. 按第 7 节验一遍。

JSON 的字段只增不改，原有字段的含义不变；页面原型 `pick/` 已经按新字段更新好了。

## 1. 包里有什么

```
├─ 部署说明.md            本文件
├─ site-data/             网站唯一数据（脚本生成，勿手改）
│  ├─ version.json        数据版本、构建日期、技能下载地址
│  ├─ palettes.json       13 套配色
│  ├─ styles.json         16 种风格
│  ├─ matrix.json         208 格兼容矩阵（含三挡）
│  └─ rules.json          三挡切分比例、综合分权重、文档类型表、可用效果
├─ templates/             260 份 .pptx：208 份普通（16 种风格 × 13 套配色）+ 52 份毛玻璃
├─ previews/              260 张 6 页预览图
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
/ppt/previews/            ← previews/ 260 张预览图
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

### 4A. 手动部署（第一次部署或想手动更新时）

```bash
VER=0.6.0                                  # 要部署的版本
WEB=/var/www/zhaodun.work/ppt              # 服务器上 /ppt/ 的实际目录，按你的路径改
TMP=$(mktemp -d)

# 1. 下载并解压（zip 根目录就是 pick/ site-data/ templates/ previews/ 部署说明.md）
curl -fL -o "$TMP/site.zip" \
  "https://github.com/99243537-sketch/garman-ppt-site/releases/download/site-v$VER/garman-site-$VER.zip"
unzip -q "$TMP/site.zip" -d "$TMP/site"

# 2. 核对版本号
grep '"version"' "$TMP/site/site-data/version.json"        # 应显示 "version": "0.6.0"

# 3. 逐个目录同步；--delete 只删这四个目录里已不在包中的旧文件，不碰 /ppt/ 下其他内容
for d in pick site-data templates previews; do
  mkdir -p "$WEB/$d"
  rsync -a --delete "$TMP/site/$d/" "$WEB/$d/"
done
rm -rf "$TMP"
```

然后清 Cloudflare 缓存：在 Cloudflare 后台 →「缓存」→「配置」→「清除缓存」，选「全部清除」最省事；如果套餐支持「自定义清除 → 按前缀」，清 `zhaodun.work/ppt/` 即可。最后按第 7 节自检。

### 4B. 自动拉取（可选，沿用你「定时从 GitHub 拉取」的方式）

下面这个脚本只在 Release 版本变化时才下载并覆盖，可以直接放进 cron：

```bash
#!/usr/bin/env bash
# /usr/local/bin/garman-site-pull.sh：有新 Release 就下载、校验、覆盖到 /ppt/
set -euo pipefail
REPO=99243537-sketch/garman-ppt-site
WEB=/var/www/zhaodun.work/ppt              # 按你的路径改
STAMP=/var/lib/garman-site.version         # 记录当前已部署的版本

TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4)
VER=${TAG#site-v}
[ -n "$VER" ] || { echo "取不到最新版本"; exit 1; }
[ "$(cat "$STAMP" 2>/dev/null)" = "$VER" ] && exit 0      # 没有新版本

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/site.zip" "https://github.com/$REPO/releases/download/$TAG/garman-site-$VER.zip"
unzip -q "$TMP/site.zip" -d "$TMP/site"
grep -q "\"version\": \"$VER\"" "$TMP/site/site-data/version.json" || { echo "包内版本与标签不一致"; exit 1; }
for d in pick site-data templates previews; do
  mkdir -p "$WEB/$d"; rsync -a --delete "$TMP/site/$d/" "$WEB/$d/"
done
echo "$VER" > "$STAMP"
echo "已部署 garman-site $VER"

# 可选：用 Cloudflare API 清缓存（需要一个只有「缓存清除」权限的令牌）
# curl -fsS -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE/purge_cache" \
#   -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" --data '{"purge_everything":true}'
```

```cron
# 每小时第 7 分钟检查一次
7 * * * * /usr/local/bin/garman-site-pull.sh >> /var/log/garman-site-pull.log 2>&1
```

公开仓库，不需要 GitHub 令牌；匿名调用 GitHub API 每小时限 60 次，每小时查一次绰绰有余。

## 5. 模板下载与预览图

16 种风格 × 13 套配色，**208 个组合全部有模板和预览图**（兼容矩阵判为冲突的组合也照样有，页面标「反对」）：

- `templates/garman-<风格id>-<配色id>-v1.pptx`：6 个版式（封面、目录、章节页、正文、正文 + 引文、结尾页）加示例页，元素逐个淡入，微软雅黑，敏感词自检 0 命中。每份约 40 KB。
- `previews/<同名>.jpg`：6 页拼图，约 2000×760，每张约 100 KB。
- 7 种可生成风格各有一套手工定稿（`styles.json` 的 `template`），其余由 `tools/masters/build_all.py` 按兼容矩阵取好的五色批量生成。

对应关系写在 `styles.json` 每种风格的 `templates` 和 `previews`（键是配色 id）。挑选页任选一个组合都显示真实预览图、点开看大图，「下载模板」都能下载。技能还不能生成的 9 种风格（`status: preview`）在列表里和其他风格一样，不加标记，只是「用 AI 生成成品」按钮变灰，写「即将支持」。

全部文件约 40 MB（模板 11 MB + 预览图 29 MB）。

**提饱和 + 风格签名色（0.5.0 起，0.6.0 改为混合策略）**：大胆风格不再被 Garman 自然色的低彩度卡住。底色、文字和主色仍取自所选配色；波普、蒸汽波、风格派、构成主义、千禧未来风、孟菲斯、包豪斯七种风格的色块与点缀（`roles` 的 secondary / accent）先从签名色里挑与主色色相相距最远的一到两个作为目标色，然后逐个槽位处理：配色九色里有色相相近（±20°）且本身有彩的颜色，就保留这个色相、把饱和度和明度提到目标色的水平（提饱和）；没有才直接用签名色。两个槽位色相太近时提饱和的那个退回签名色。每格的 `fix` 记 boost / signature / mixed，`slots` 记每个槽位用的哪种做法。矩阵分只升不降：新分 = max(原分, 75 + 0.25 × 原分) + 每个提饱和槽位 3 分。原来 39 个「冲突」组合因此全部解除。现在 91 格里 7 格全提饱和、28 格混合、56 格全签名色。

**毛玻璃（0.6.0 起）**：`effectsAvailable` 加了 `glass`。与毛玻璃兼容的风格（`effects.glass` 为 ok / adjust：千禧未来风、蒸汽波、日式极简、便当盒、玻璃拟态）有毛玻璃版模板：在普通模板的每个版式底层加三团柔边色团，矩形卡片改成 72% 不透明、加半透明白边和柔和投影（`tools/masters/glassify.py`）；玻璃拟态本身就是毛玻璃，直接用原模板。对应关系在 `styles.json` 的 `glassTemplates` / `glassPreviews`。与毛玻璃冲突的 11 种风格仍可选毛玻璃（综合分扣 30 分、显示冲突提示），只是没有模板，显示示意样张和「这种风格不做毛玻璃」。技能目前只生成普通效果，所以选毛玻璃时「用 AI 生成成品」显示「即将支持」。

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
- **效果**：`rules.json` 的 `effectsAvailable` 现在是 `plain`、`glass`；如果去掉 `glass`，页面上毛玻璃选项会显示「即将支持」且不可选。

**结果区**：6 页预览图（毛玻璃效果下没有毛玻璃模板的风格退回 SVG 示意样张，按该格 `roles` 五色上色）、「下载模板」、「用 AI 生成成品」（展开三步：下载技能包、复制口令、发给智能体）。口令格式：

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
| | `fix` `slots` `sig` | 七种大胆风格的格才有：处理方式（boost / signature / mixed）、每个槽位的做法、用到的签名色色值（都已写进 `roles`） |
| styles.json | `status` | ready 可生成 / preview 只能看 |
| | `signature` | 风格签名色候选（波普、蒸汽波、风格派、构成主义、千禧、孟菲斯、包豪斯有） |
| | `glassTemplates` `glassPreviews` | 毛玻璃版模板和预览图（键是配色 id；与毛玻璃冲突的风格为空） |
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
