"""从兼容矩阵和风格库生成网站用的 site-data（配色、风格、矩阵、规则）。

用法：
  node export-styles.cjs design-styles/data.js styles-v2.json
  python3 build_site_data.py matrix-data.json styles-v2.json ../site-data

产物全部由本脚本生成，请勿手改。阈值、权重、文档类型表、毛玻璃兼容表都是暂定值，
集中写在下面的 RULES / DOC_TYPES / STYLE_META / PALETTE_META 里，改这里再重跑。
"""
import json, sys, os, datetime

MATRIX, STYLES_V2, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DATA_VERSION = "0.7.2"

# ---- 规则（暂定，待赵盾按实际分布定）----
RULES = {
    # 三挡不设固定分数线：把全部 208 格按综合分从高到低排，前 1/4 推荐、中间 1/2 中性、后 1/4 反对。
    # 落在分界线上的同分组合归同一挡（偏高的一挡）。比例可改，比如各 1/3。
    "tiers": [
        {"id": "recommend", "zh": "推荐", "en": "Recommended", "share": 0.25},
        {"id": "neutral",   "zh": "中性", "en": "Neutral",     "share": 0.50},
        {"id": "against",   "zh": "反对", "en": "Not advised", "share": 0.25},
    ],
    "tierMethod": "quantile",
    # 排名范围：ready = 只在可生成的风格里排名切分（预览风格套用同一组分界分数）；all = 全部 208 格
    "tierPool": "ready",
    "conflictIsAgainst": True,          # 矩阵结论为「冲突」一律归反对
    "weights": {
        "styleDocMatch": 10,            # 风格适合该文档类型
        "paletteDocMatch": 5,           # 配色适合该文档类型
        "glassConflict": -30,           # 选了毛玻璃，风格与毛玻璃冲突
        "glassAdjust": -10,             # 选了毛玻璃，风格需调整
    },
    "clamp": [0, 115],                  # 上限不截到 100，否则满分组合加了文档类型分也拉不开
    "effectsAvailable": ["plain", "glass"],   # 0.6.0 起开放毛玻璃（与毛玻璃冲突的风格不出毛玻璃模板）
    "pending": ["tiers.share", "weights", "docTypes", "styles[].docTypes", "palettes[].docTypes", "styles[].effects.glass"],
}

DOC_TYPES = [
    ("report",   "工作汇报 / 总结", "Work report / review"),
    ("official", "公文 / 公共事务", "Official / public affairs"),
    ("teaching", "讲课 / 培训",     "Lecture / training"),
    ("reading",  "读书分享 / 人文", "Book talk / humanities"),
    ("tech",     "科技 / 数据",     "Tech / data"),
    ("event",    "活动 / 宣传",     "Event / promotion"),
    ("festive",  "节庆 / 传统文化", "Festive / tradition"),
    ("product",  "产品介绍 / 发布", "Product / launch"),
    ("student",  "学生 / 校园",     "Student / campus"),
    ("culture",  "文艺 / 设计",     "Arts / design"),
]

# 风格：英文 id 已在风格库里；这里补状态、文档类型、毛玻璃兼容、模板（全部暂定）
READY = {"editorial", "neubrutalism", "art-nouveau",   # 母版 v1 三套
         "swiss-style", "japanese-minimal", "bento-grid", "metro"}   # 10-31 增到 7 种
STYLE_META = {
    "bauhaus":          (["teaching", "culture"],               "conflict"),
    "swiss-style":      (["report", "official", "tech", "product"], "conflict"),
    "editorial":        (["reading", "teaching", "culture"],    "conflict"),
    "japanese-minimal": (["culture", "reading", "festive"],     "adjust"),
    "art-deco":         (["festive", "event"],                  "conflict"),
    "art-nouveau":      (["culture", "reading", "festive"],     "conflict"),
    "constructivism":   (["event"],                             "conflict"),
    "de-stijl":         (["culture"],                           "conflict"),
    "memphis":          (["student", "event"],                  "conflict"),
    "pop-art":          (["event", "student"],                  "conflict"),
    "neubrutalism":     (["student", "event", "product"],       "conflict"),
    "metro":            (["report", "tech"],                    "conflict"),
    "y2k":              (["tech", "event"],                     "ok"),
    "vaporwave":        (["culture", "event"],                  "ok"),
    "glassmorphism":    (["tech", "product"],                   "ok"),
    "bento-grid":       (["product", "report", "tech"],         "ok"),
}
TEMPLATES = {  # 母版 v1：每套风格一份「下载这套主题」.pptx（文件由母版线程产出，此处只引用路径）
    "editorial":    {"palette": "amazonite", "file": "templates/garman-editorial-amazonite-v1.pptx"},
    "neubrutalism": {"palette": "ginkgo",    "file": "templates/garman-neubrutalism-ginkgo-v1.pptx"},
    "art-nouveau":  {"palette": "nautilus",  "file": "templates/garman-art-nouveau-nautilus-v1.pptx"},
    # 第二批（10-31）
    "swiss-style":      {"palette": "blue-magpie",  "file": "templates/garman-swiss-blue-magpie-v1.pptx"},
    "japanese-minimal": {"palette": "plum-blossom", "file": "templates/garman-japanese-minimal-plum-blossom-v1.pptx"},
    "bento-grid":       {"palette": "tallow-tree",  "file": "templates/garman-bento-grid-tallow-tree-v1.pptx"},
    "metro":            {"palette": "kingfisher",   "file": "templates/garman-metro-kingfisher-v1.pptx"},
}

# 配色：英文 id 与文档类型（取自配色说明里的「适合……」，暂定）
PALETTE_META = {
    "天河石":   ("amazonite",    "Amazonite",        ["report", "official"]),
    "鹦鹉螺":   ("nautilus",     "Nautilus",         ["reading", "culture"]),
    "鲍鱼壳":   ("abalone",      "Abalone",          ["tech"]),
    "翠鸟":     ("kingfisher",   "Kingfisher",       ["teaching", "event", "student"]),
    "红嘴蓝鹊": ("blue-magpie",  "Red-billed Blue Magpie", ["event"]),
    "鸢尾":     ("iris",         "Iris",             ["culture", "reading"]),
    "梅花":     ("plum-blossom", "Plum Blossom",     ["festive"]),
    "栾树":     ("goldenrain",   "Goldenrain Tree",  ["official"]),
    "槭枫":     ("maple",        "Maple",            ["report"]),
    "乌桕":     ("tallow-tree",  "Chinese Tallow",   ["culture"]),
    "黄金宝螺": ("golden-cowry", "Golden Cowry",     ["festive", "event"]),
    "银杏":     ("ginkgo",       "Ginkgo",           ["student"]),
    "吉丁虫":   ("jewel-beetle", "Jewel Beetle",     ["official"]),
}
COLOR_KEYS = ["main", "soft", "pale", "deep", "base", "accent", "ink", "muted", "line"]

m = json.load(open(MATRIX, encoding="utf-8"))
v2 = json.load(open(STYLES_V2, encoding="utf-8"))["STYLES"]
v2_by_id = {s["id"]: s for s in v2}
assert [s["id"] for s in m["styles"]] == [s["id"] for s in v2], "矩阵与风格库的风格 id 或顺序不一致"
assert set(STYLE_META) == set(v2_by_id), "STYLE_META 缺风格"
assert set(PALETTE_META) == {p["name"] for p in m["palettes"]}, "PALETTE_META 缺配色"
assert len(m["cells"]) == len(v2) * len(m["palettes"]), "矩阵格数不对"

# ---- 风格签名色 + 提饱和（混合策略）----
# 赵盾 2026-10-31 定：配色定底子，大胆风格可自带签名色；同日补充：配色自身色相够用时优先提饱和。
# 底色、文字、主色仍取自所选配色。secondary / accent 两个槽位：先从签名色里挑与主色色相相距最远的
# 1–2 个作为「目标色」；对每个目标色，如果配色九色里有色相相近（±HUE_TOL°）且本身有彩（S ≥ MIN_S）的颜色，
# 就保留配色的色相、把饱和度和明度提到目标色的水平（提饱和）；找不到才直接用签名色。
# 每格记 fix：boost（全部提饱和）/ signature（全部签名色）/ mixed，slots 记每个槽位的做法。
SIGNATURE = {  # 风格 id: [(中文名, 色值)…]，候选来自风格库该风格的经典配色
    "pop-art":        [("红", "E8312F"), ("蓝", "1F6FD1"), ("黄", "FFD400")],
    "vaporwave":      [("霓虹粉", "F772C8"), ("青", "2DCCF0"), ("薄荷", "3DF2A8")],
    "de-stijl":       [("红", "C62A2A"), ("蓝", "1F3F95"), ("黄", "EFC12B")],
    "constructivism": [("红", "B5262B")],
    "y2k":            [("电光蓝", "3A7BFF"), ("丁香紫", "B48CFF"), ("泡泡糖粉", "FF5FC8")],
    "memphis":        [("珊瑚红", "FF7A85"), ("薄荷", "4FC9B0"), ("柠檬黄", "FFD23F")],
    "bauhaus":        [("群青", "2D4E9C"), ("朱红", "C8442F"), ("镉黄", "E8B22A")],
}
SIG_LIFT = (75, 0.25)   # 新分 = max(原分, 75 + 0.25 × 原分)：补足颜色要求后，最低 15 分也到 79（中性线）
BOOST_BONUS = 3         # 每个提饱和的槽位再加 3 分：保留了配色本来的色相，辨识度更好
HUE_TOL, MIN_S = 20, 0.18
BOOST_FROM = ["main", "accent", "deep", "base", "muted"]   # 可以拿来提饱和的配色色位

import colorsys

def _hsv(h):
    return colorsys.rgb_to_hsv(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))

def _hex(hsv):
    return "".join(f"{round(c * 255):02X}" for c in colorsys.hsv_to_rgb(*hsv))

def _hd(a, b):
    d = abs(_hsv(a)[0] - _hsv(b)[0]) * 360 % 360
    return min(d, 360 - d)

def label_of(score):
    return "兼容" if score >= 70 else "可调" if score >= 45 else "冲突"

def boost_for(target, pal, used):
    """配色里与目标色色相相近的有彩色 → 保留其色相、提到目标色的饱和度与明度；没有返回 None。"""
    best = None
    for k in BOOST_FROM:
        c = pal[k]
        hh, ss, vv = _hsv(c)
        if k in used or ss < MIN_S or _hd(c, target) > HUE_TOL:
            continue
        if best is None or _hd(c, target) < _hd(best[1], target):
            best = (k, c)
    if not best:
        return None
    th, ts, tv = _hsv(target)
    return best[0], _hex((_hsv(best[1])[0], max(ts, _hsv(best[1])[1]), tv))

zh_name = {s["id"]: s["name"]["zh"] for s in v2}
pal_by_name = {p["name"]: p for p in m["palettes"]}
for key, c in m["cells"].items():
    sid, pname = key.split("|")
    if sid not in SIGNATURE:
        continue
    pal = pal_by_name[pname]
    targets = sorted(SIGNATURE[sid], key=lambda x: -_hd(x[1], c["roles"]["primary"]))[:2]
    roles, slots, boosted, signed, used = dict(c["roles"]), {}, [], [], set()
    for slot, (name, hexv) in zip(("secondary", "accent"), targets):
        b = boost_for(hexv, pal, used)
        if b:
            used.add(b[0])
            roles[slot] = b[1]; slots[slot] = {"how": "boost", "from": b[0], "target": name}
            boosted.append(name)
        else:
            roles[slot] = hexv; slots[slot] = {"how": "signature", "target": name}
            signed.append(name)
    # 两个槽位色相太近就失去撞色感（< 35°，且不低于两个目标色本身距离的 0.8 倍）：把提饱和的槽位退回签名色
    if len(slots) == 2 and _hd(roles["secondary"], roles["accent"]) < min(35, 0.8 * _hd(targets[0][1], targets[1][1])):
        for slot, (name, hexv) in zip(("secondary", "accent"), targets):
            if slots[slot]["how"] == "boost":
                roles[slot] = hexv; slots[slot] = {"how": "signature", "target": name}
                boosted.remove(name); signed.append(name)
    fix = "boost" if not signed else "signature" if not boosted else "mixed"
    old = c["s"]
    c["s"] = min(100, max(old, round(SIG_LIFT[0] + SIG_LIFT[1] * old)) + BOOST_BONUS * len(boosted))
    c["l"] = label_of(c["s"])
    c["fix"], c["slots"] = fix, slots
    c["sig"] = [roles[k] for k, v in slots.items() if v["how"] == "signature"]
    parts = []
    if boosted:
        parts.append(f"把本配色里接近{'、'.join(boosted)}的颜色提高饱和度")
    if signed:
        parts.append(f"加入{zh_name[sid]}签名色{'、'.join(signed)}")
    how = "，".join(parts)
    c["why"] = f"{c['why']} 已{how}补足。" if old < 70 else c["why"]
    c["act"] = f"底色、文字和主色用本配色；色块与点缀{how}。"
    c["roles"] = roles

pid = {n: PALETTE_META[n][0] for n in PALETTE_META}
palettes = []
for i, p in enumerate(m["palettes"]):
    i_d, en, docs = PALETTE_META[p["name"]]
    palettes.append({
        "id": i_d, "order": i, "name": {"zh": p["name"], "en": en},
        "kind": p["kind"], "tier": p["tier"], "desc": {"zh": p["desc"]},
        "colors": {k: p[k] for k in COLOR_KEYS},
        "glass": True, "default": p["name"] == "天河石", "docTypes": docs,
    })

def tpl_file(sid, pid):
    t = TEMPLATES.get(sid)
    if t and t["palette"] == pid:
        return t["file"]
    return f"templates/garman-{sid}-{pid}-v1.pptx"

def glass_files(sid, glass, palettes, ext):
    if glass == "conflict":
        return {}
    if sid == "glassmorphism":
        f = lambda p: tpl_file(sid, p)
    else:
        f = lambda p: f"templates/garman-{sid}-{p}-glass-v1.pptx"
    out = {p["id"]: f(p["id"]) for p in palettes}
    if ext == "jpg":
        out = {k: "previews/" + os.path.basename(v)[:-5] + ".jpg" for k, v in out.items()}
    return out

styles = []
for i, s in enumerate(v2):
    docs, glass = STYLE_META[s["id"]]
    ppt = s["ppt"]
    styles.append({
        "id": s["id"], "order": i, "name": s["name"], "tagline": s["tagline"], "era": s["era"],
        "status": "ready" if s["id"] in READY else "preview",
        "docTypes": docs, "effects": {"glass": glass},
        "signature": [{"zh": n, "hex": h} for n, h in SIGNATURE.get(s["id"], [])],
        "template": TEMPLATES.get(s["id"]),   # 每种风格手工定稿的那一套（推荐展示用）
        # 可生成风格 × 全部 13 套配色：模板与 6 页预览图（tools/masters/build_all.py 生成）
        "templates": {p["id"]: tpl_file(s["id"], p["id"]) for p in palettes},   # 16 种风格全有模板
        "previews": {p["id"]: "previews/" + os.path.basename(tpl_file(s["id"], p["id"]))[:-5] + ".jpg"
                     for p in palettes},
        # 毛玻璃版：与毛玻璃兼容（ok / adjust）的风格才有，由 tools/masters/glassify.py 生成；玻璃拟态本身就是毛玻璃，直接用原模板
        "glassTemplates": glass_files(s["id"], glass, palettes, "pptx"),
        "glassPreviews": glass_files(s["id"], glass, palettes, "jpg"),
        "ppt": {k: ppt[k] for k in ("layouts", "motifs", "forbid", "radius", "shadow", "density", "colorRule")},
        "detailUrl": f"/design-styles/?style={s['id']}",
    })

def quantile_cuts(scores):
    """返回每挡的最低分：排名落在该挡最后一位的那个分数。"""
    xs = sorted(scores, reverse=True); n = len(xs); acc = 0; cuts = []
    for t in RULES["tiers"][:-1]:
        acc += t["share"]
        cuts.append(xs[max(0, round(n * acc) - 1)])
    return cuts

def tier_of(score, label, cuts):
    if RULES["conflictIsAgainst"] and label == "冲突":
        return "against"
    for t, cut in zip(RULES["tiers"], cuts):
        if score >= cut:
            return t["id"]
    return RULES["tiers"][-1]["id"]

CUTS = quantile_cuts([c["s"] for k, c in m["cells"].items()
                      if RULES["tierPool"] == "all" or k.split("|")[0] in READY])
cells = {}
for s in v2:
    row = [(n, m["cells"][f"{s['id']}|{n}"]) for n in PALETTE_META]
    ranked = sorted(row, key=lambda x: (-x[1]["s"], x[0] != "天河石", list(PALETTE_META).index(x[0])))
    for n, c in row:
        alt = [pid[a] for a, ac in ranked if a != n and ac["l"] != "冲突"][:3] if c["l"] == "冲突" else []
        cells[f"{s['id']}|{pid[n]}"] = {
            "s": c["s"], "l": c["l"], "tier": tier_of(c["s"], c["l"], CUTS),
            "why": c["why"], "act": c["act"], "roles": c["roles"], "alt": alt,
            **({k: c[k] for k in ("fix", "slots", "sig") if k in c}),
        }

# 无文档类型、普通效果下的全局排序（P 模式开场兜底用；页面里会按用户选的文档类型重算）
order = sorted(cells, key=lambda k: (-cells[k]["s"],
               v2_by_id[k.split("|")[0]]["id"] not in READY,
               k.split("|")[1] != "amazonite"))
for r, k in enumerate(order, 1):
    cells[k]["rankBase"] = r

stamp = datetime.date.today().isoformat()
os.makedirs(OUT, exist_ok=True)
def dump(name, obj):
    obj = {"_note": "由 build_site_data.py 生成，请勿手改", "version": DATA_VERSION, **obj}
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

dump("palettes.json", {"palettes": palettes})
dump("styles.json", {"styles": styles})
dump("matrix.json", {"key": "风格id|配色id", "cells": cells})
dump("rules.json", {"rules": RULES, "docTypes": [{"id": a, "zh": b, "en": c} for a, b, c in DOC_TYPES]})
dump("version.json", {"built": stamp, "files": ["palettes.json", "styles.json", "matrix.json", "rules.json"],
                      "skill": {"name": "garman-ppt", "version": "0.3.2",
                                "zip": "https://github.com/99243537-sketch/garman-ppt/releases/tag/v0.3.2",
                                # 同源副本（相对 /ppt/）：服务器上放了这个文件，组合包就把技能一起打进去；
                                # 文件不存在时挑选页自动退回成只给 GitHub 链接
                                "local": "downloads/garman-ppt-0.3.2.zip"}})

# 挑选页引用 pick.css / pick.js 时带 ?v=<数据版本>，换版时浏览器和 CDN 不会读到旧文件
_idx = os.path.join(OUT, "..", "pick", "index.html")
if os.path.exists(_idx):
    import re
    _h = open(_idx, encoding="utf-8").read()
    open(_idx, "w", encoding="utf-8").write(re.sub(r'((?:pick|pack)\.(?:css|js))\?v=[0-9.]+', rf'\1?v={DATA_VERSION}', _h))

from collections import Counter
c = Counter(v["tier"] for v in cells.values())
cr = Counter(v["tier"] for k, v in cells.items() if k.split("|")[0] in READY)
print(f"{len(palettes)} 配色 · {len(styles)} 风格 · {len(cells)} 格")
print("三挡（全部）：", dict(c))
print("三挡（ready 风格）：", dict(cr))
print("分界分数：", CUTS)
print("全局第一：", order[0], cells[order[0]]["s"])
