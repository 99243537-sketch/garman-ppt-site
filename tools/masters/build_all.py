"""按「16 种风格 × 13 套配色」批量生成「下载这套主题」.pptx（共 208 份）。

版式沿用母版 v1（build_masters.py）、第二批（build_masters_batch2.py）与第三批
（build_masters_batch3.py）的 16 个风格类，只把颜色换成兼容矩阵里该格取好的
五色角色（roles）和配色本身的九色。冲突组合也照样生成（页面上标「反对」）。
已有的 7 份手工定稿（每种风格一套）保持原样，不重复生成。
用法：python3 build_all.py <site-data 目录> <输出目录>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_masters import Editorial, Brutal, Nouveau, build  # noqa: E402
from build_masters_batch2 import Swiss, Japanese, Bento, Metro  # noqa: E402
from build_masters_batch3 import BATCH3, make_colors  # noqa: E402

CLASSES = {"editorial": Editorial, "neubrutalism": Brutal, "art-nouveau": Nouveau,
           "swiss-style": Swiss, "japanese-minimal": Japanese, "bento-grid": Bento, "metro": Metro, **BATCH3}


def colors(sid, R, P):
    """返回 (C, theme)：C 是风格类用到的具名颜色，theme 是 PowerPoint 主题 10 色。"""
    if sid in BATCH3:
        return make_colors(R, P)
    if sid == "editorial":
        C = dict(bg=R["background"], deep=R["primary"], ink=R["text"], muted=R["secondary"], line=P["line"],
                 accent=R["accent"], main=P["main"], white="FFFFFF")
        theme = [C["ink"], "FFFFFF", C["deep"], C["bg"], C["main"], C["accent"], C["muted"], C["line"], P["deep"], P["soft"]]
    elif sid == "neubrutalism":
        C = dict(bg=R["background"], ink=R["text"], yellow=R["primary"], blue=R["secondary"], white="FFFFFF", beige=R["accent"])
        theme = [C["ink"], "FFFFFF", C["ink"], C["bg"], C["yellow"], C["blue"], C["beige"], C["ink"], C["yellow"], C["blue"]]
    elif sid == "art-nouveau":
        C = dict(bg=R["background"], deep=R["secondary"], accent=R["accent"], line=R["primary"], ink=R["text"], card=P["soft"])
        theme = [C["ink"], "FFFFFF", C["deep"], C["bg"], C["deep"], C["accent"], C["line"], C["card"], C["ink"], C["accent"]]
    elif sid == "swiss-style":
        C = dict(bg=R["background"], ink=R["text"], muted=R["secondary"], line=P["line"], accent=R["accent"], white="FFFFFF")
        theme = [C["ink"], "FFFFFF", P["base"], P["pale"], P["main"], C["accent"], C["muted"], C["line"], P["deep"], P["soft"]]
    elif sid == "japanese-minimal":
        C = dict(bg=R["background"], ink=R["text"], muted=P["muted"], line=R["secondary"], soft=R["primary"],
                 dot=R["accent"], deep=P["deep"])
        theme = [C["ink"], "FFFFFF", P["base"], C["bg"], C["soft"], C["dot"], C["muted"], C["line"], C["deep"], P["soft"]]
    elif sid == "bento-grid":
        C = dict(bg=R["background"], ink=R["text"], muted=P["muted"], line=P["line"], main=R["primary"], soft=P["soft"],
                 blue=R["accent"], deep=P["deep"], white="FFFFFF")
        theme = [C["ink"], "FFFFFF", P["base"], C["bg"], C["main"], C["blue"], C["muted"], C["line"], C["deep"], C["soft"]]
    elif sid == "metro":
        C = dict(bg=R["background"], ink=R["text"], main=R["primary"], deep=R["secondary"], accent=R["accent"],
                 muted=P["line"], dark=R["background"], panel=P["base"])
        theme = [C["bg"], "FFFFFF", P["base"], P["pale"], C["main"], C["accent"], C["muted"], P["line"], C["deep"], P["soft"]]
    return C, theme


def main(site_data, outdir):
    pals = json.load(open(os.path.join(site_data, "palettes.json"), encoding="utf-8"))["palettes"]
    styles = json.load(open(os.path.join(site_data, "styles.json"), encoding="utf-8"))["styles"]
    cells = json.load(open(os.path.join(site_data, "matrix.json"), encoding="utf-8"))["cells"]
    tmp = os.path.join(outdir, ".tmp")
    os.makedirs(tmp, exist_ok=True)
    only = set(sys.argv[3:])  # 可选：只生成这些风格 id
    for st in styles:
        if only and st["id"] not in only:
            continue
        base = CLASSES[st["id"]]
        for p in pals:
            if (st.get("template") or {}).get("palette") == p["id"]:
                continue  # 手工定稿的那一套（styles.json 的 template）不覆盖
            s = base()
            s.key = st["id"]
            s.file = f"garman-{st['id']}-{p['id']}"
            s.title = f"{st['name']['zh']} × {p['name']['zh']}"
            s.C, s.theme = colors(st["id"], cells[f"{st['id']}|{p['id']}"]["roles"], p["colors"])
            print(build(s, outdir, tmp))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
