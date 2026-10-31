"""给已生成的模板叠一层「毛玻璃」效果，另存为 *-glass-v1.pptx。

做法（只动版式里的装饰形状，占位符和动画不动）：
1. 每个版式最底层加三团模糊色团（primary / accent / secondary，柔边），给玻璃一个可透的背景；
2. 面积够大的实色色块（卡片、格子、面板）改成 72% 不透明，加 1 磅半透明白边和柔和投影，
   保留原来的颜色，所以放在上面的文字对比度基本不变；
3. 小形状（点、线、星、编号底块）、椭圆等非矩形、已带透明度或特效的装饰不动。

用法：python3 glassify.py <site-data 目录> <输出目录> <pptx…>
文件名须是 garman-<风格id>-<配色id>-v1.pptx（或手工定稿名，按 styles.json 的 templates 反查）。
"""
import json
import os
import sys

from lxml import etree
from pptx import Presentation

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
MIN_AREA = 0.02          # 占版面 2% 以上的实色形状才算卡片
FULL_AREA = 0.85         # 接近整页的底色块不算卡片
CARD_ALPHA = 72          # 卡片不透明度（%）


def _lum(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _blob(sid, x, y, d, color, soft):
    return etree.fromstring(
        f'<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="{sid}" name="玻璃色团 {sid}"/><p:cNvSpPr/>'
        f'<p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{d}" cy="{d}"/></a:xfrm>'
        f'<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{color}"><a:alpha val="80000"/></a:srgbClr></a:solidFill>'
        f'<a:ln><a:noFill/></a:ln><a:effectLst><a:softEdge rad="{soft}"/></a:effectLst></p:spPr></p:sp>')


def glassify(src, dst, roles):
    prs = Presentation(src)
    W, H = prs.slide_width, prs.slide_height
    dark = _lum(roles["background"]) < 0.2
    for L in prs.slide_layouts:
        tree = L._element.find(".//p:cSld/p:spTree", NS)
        ids = [int(e.get("id")) for e in L._element.iter(f"{{{P}}}cNvPr")]
        nid = max(ids) + 1
        # 1. 底层三团色团：左上、右下、右上
        spots = [(-0.10, -0.18, 0.42, "primary"), (0.70, 0.55, 0.45, "accent"), (0.62, -0.20, 0.28, "secondary")]
        anchor = tree.find("p:grpSpPr", NS)
        for k, (fx, fy, fd, role) in enumerate(spots):
            d = int(W * fd)
            anchor.addnext(_blob(nid + k, int(W * fx), int(H * fy), d, roles[role], int(d * 0.24)))
            anchor = anchor.getnext()
        # 2. 大色块改半透明 + 白边 + 柔和投影
        for sp in L.shapes:
            if sp.is_placeholder or sp.shape_type != 1 or sp.name.startswith("玻璃色团"):
                continue
            area = (sp.width * sp.height) / (W * H)
            if not (MIN_AREA <= area <= FULL_AREA):
                continue
            spPr = sp._element.find("p:spPr", NS)
            geom = spPr.find("a:prstGeom", NS)
            clr = spPr.find("a:solidFill/a:srgbClr", NS)
            # 只处理矩形 / 圆角矩形卡片；已经带透明度或特效（柔边、投影）的形状是风格自己的装饰，不动
            if (clr is None or geom is None or geom.get("prst") not in ("rect", "roundRect")
                    or clr.find("a:alpha", NS) is not None or spPr.find("a:effectLst", NS) is not None):
                continue
            etree.SubElement(clr, f"{{{A}}}alpha").set("val", str(CARD_ALPHA * 1000))
            ln = spPr.find("a:ln", NS)
            if ln is not None:
                spPr.remove(ln)
            ln = etree.fromstring(f'<a:ln xmlns:a="{A}" w="12700"><a:solidFill><a:srgbClr val="FFFFFF">'
                                  f'<a:alpha val="{35 if dark else 70}000"/></a:srgbClr></a:solidFill></a:ln>')
            eff = etree.fromstring(f'<a:effectLst xmlns:a="{A}"><a:outerShdw blurRad="304800" dist="63500" dir="5400000" '
                                   f'algn="t" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="{30 if dark else 14}000"/>'
                                   f'</a:srgbClr></a:outerShdw></a:effectLst>')
            # 顺序：fill → ln → effectLst
            clr.getparent().addnext(ln)
            ln.addnext(eff)
    prs.core_properties.title = (prs.core_properties.title or "") + " · 毛玻璃"
    prs.save(dst)
    return dst


def main(site_data, outdir, files):
    styles = json.load(open(os.path.join(site_data, "styles.json"), encoding="utf-8"))["styles"]
    cells = json.load(open(os.path.join(site_data, "matrix.json"), encoding="utf-8"))["cells"]
    by_file = {os.path.basename(f): (s["id"], pid) for s in styles for pid, f in s["templates"].items()}
    os.makedirs(outdir, exist_ok=True)
    for f in files:
        sid, pid = by_file[os.path.basename(f)]
        dst = os.path.join(outdir, f"garman-{sid}-{pid}-glass-v1.pptx")
        print(glassify(f, dst, cells[f"{sid}|{pid}"]["roles"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
