"""第三批 9 套 GarmanPPT 母版版式：包豪斯、装饰艺术、构成主义、风格派、孟菲斯、波普艺术、
千禧未来风、蒸汽波、玻璃拟态。

和母版 v1、第二批一致：6 个版式、占位符 idx 约定相同、示例页逐个淡入、微软雅黑。
颜色全部来自兼容矩阵该格的五色角色（roles）加配色本身的九色，由 build_all.py 注入；
这里的默认值只是单独运行时的示例（天河石）。
用法：python3 build_masters_batch3.py <输出目录>（build_masters.py 需在同一目录）
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_masters import IDX, build  # noqa: E402

SW, SH = 33.867, 19.05
DEFAULT_ROLES = dict(background="EFF8F9", text="243335", primary="70C6D6", secondary="B04D2F", accent="122947")
DEFAULT_PAL = dict(main="70C6D6", soft="DDF1F2", pale="EFF8F9", deep="1B667A", base="122947", accent="B04D2F",
                   ink="243335", muted="53686A", line="C8D5D4")


def make_colors(R, P):
    """五色角色 + 配色九色 → 风格类用的 C 与主题 10 色。"""
    C = dict(bg=R["background"], ink=R["text"], pri=R["primary"], sec=R["secondary"], acc=R["accent"],
             white="FFFFFF", black="141414", **{"p_" + k: v for k, v in P.items()})
    theme = [C["ink"] if _dark(C["bg"]) is False else "141414", "FFFFFF", P["base"], P["pale"],
             C["pri"], C["sec"], C["ink"], P["line"], P["deep"], P["soft"]]
    return C, theme


def _lum(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _dark(h):
    return _lum(h) < 0.2


def on(fill):
    """放在某个色块上的文字用黑还是白。"""
    return "FFFFFF" if _lum(fill) < 0.35 else "141414"


# ---------- 在 Part 上追加效果：透明度、柔边、投影 ----------
def alpha_fill(p, a):
    x = p.xml[-1]
    i = x.index('<a:solidFill><a:srgbClr val="')
    j = x.index('"/>', i)
    p.xml[-1] = x[:j] + f'"><a:alpha val="{int(a * 1000)}"/></a:srgbClr>' + x[j + 3:]


def alpha_line(p, a):
    x = p.xml[-1]
    i = x.index('<a:ln w=')
    k = x.index('<a:srgbClr val="', i)
    j = x.index('"/>', k)
    p.xml[-1] = x[:j] + f'"><a:alpha val="{int(a * 1000)}"/></a:srgbClr>' + x[j + 3:]


def effect(p, eff):
    x = p.xml[-1]
    i = x.index("</p:spPr>")
    p.xml[-1] = x[:i] + f"<a:effectLst>{eff}</a:effectLst>" + x[i:]


def soft_edge(p, cm):
    effect(p, f'<a:softEdge rad="{int(cm * 360000)}"/>')


def drop_shadow(p, alpha=18):
    effect(p, '<a:outerShdw blurRad="228600" dist="76200" dir="5400000" algn="t" rotWithShape="0">'
              f'<a:srgbClr val="000000"><a:alpha val="{alpha * 1000}"/></a:srgbClr></a:outerShdw>')


class Base:
    """通用骨架：目录、正文、引文、结尾的占位符位置；各风格覆盖封面、章节页和装饰钩子。"""
    key, file, title = "base", "garman-base", "基础"
    logo = (29.4, 0.7, 3.6, 1.4)
    chapter_num = "01"
    bold_title = True

    def __init__(self):
        self.C, self.theme = make_colors(DEFAULT_ROLES, DEFAULT_PAL)

    # 钩子
    def deco(self, p, kind):
        pass

    def panel(self, p, x, y, w, h, i=0):
        pass

    def tc(self):          # 标题色
        return self.C["ink"]

    def nc(self, i=0):     # 编号色
        return self.C["acc"] if not _dark(self.C["bg"]) else self.C["pri"]

    def footer(self, p, dark=False):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], 2.0, 18.05, 16, 0.6, "", 9, c["ink"], anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 29.87, 18.05, 2.0, 0.6, "", 9, c["ink"], algn="r", anchor="ctr")

    def head(self, p, x=2.0, w=26.0):
        p.ph("标题", "title", 0, x, 1.4, w, 2.0, "正文页标题（20 字以内）", 28, self.tc(), bold=self.bold_title, anchor="ctr")

    def toc_head(self, p):
        p.ph("目录标题", "title", 0, 2.0, 1.4, 20, 2.0, "目录标题（8 字以内）", 30, self.tc(), bold=self.bold_title, anchor="ctr")

    def toc(self, p):
        c = self.C
        self.deco(p, "toc")
        self.footer(p)
        self.toc_head(p)
        for i, idx in enumerate(IDX["toc"]):
            x = 2.4 if i % 2 == 0 else 17.6
            y = 4.6 if i < 2 else 10.9
            self.panel(p, x - 0.4, y - 0.4, 14.6, 5.6, i)
            p.shape("rect", x + 0.4, y + 0.3, 3, 1.2, text=f"0{i + 1}", sz=20, color=self.nc(i), bold=True, algn="l", anchor="t")
            p.ph(f"目录条目 {i + 1}", "body", idx, x + 0.4, y + 2.0, 12.8, 2.6,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 20, c["ink"], bold=True, lvl2=(12, c["ink"]))
        return c["bg"], False

    def body(self, p):
        c = self.C
        self.deco(p, "body")
        self.footer(p)
        self.head(p)
        self.panel(p, 2.0, 4.4, 21.0, 12.8, 0)
        p.ph("正文", "body", IDX["body"], 2.8, 5.2, 19.4, 11.2, "正文（建议 180 字以内，最多 3 段）", 15, c["ink"], lnspc=165)
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.deco(p, "quote")
        self.footer(p)
        self.head(p)
        self.panel(p, 2.0, 4.4, 15.0, 12.8, 0)
        p.ph("正文", "body", IDX["body"], 2.8, 5.2, 13.4, 11.2, "正文（建议 120 字以内）", 14, c["ink"], lnspc=165)
        self.panel(p, 18.0, 4.4, 13.87, 9.0, 1)
        p.ph("引文", "body", IDX["quote"], 18.9, 5.2, 12.07, 7.4, "“引文或金句（40 字以内）”", 22, self.qc(), bold=True, anchor="ctr", lnspc=135)
        p.ph("出处 / 备注", "body", IDX["note"], 18.9, 14.0, 12.07, 0.8, "出处或备注（20 字以内）", 11, c["ink"])
        return c["bg"], False

    def qc(self):          # 引文色
        return self.C["ink"]

    def end(self, p):
        c = self.C
        self.deco(p, "end")
        p.ph("Logo", "pic", IDX["logo"], 2.0, 1.4, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["ink"])
        p.ph("结束语", "title", 0, 2.0, 5.6, 20, 3.4, "结束语（8 字以内）", 54, self.tc(), bold=self.bold_title, anchor="b")
        p.ph("补充", "body", IDX["endsub"], 2.0, 9.6, 20, 1.2, "一句收尾的话（30 字以内）", 16, c["ink"])
        p.ph("联系方式", "body", IDX["contact"], 2.0, 16.0, 20, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"])
        return c["bg"], True

    def cover_text(self, p, x=2.0, y=4.4, w=19.0, size=48, algn="l"):
        c = self.C
        p.ph("眉题", "body", IDX["eyebrow"], x, y, w, 0.8, "眉题（建议 20 字以内）", 12, self.nc(), bold=True, algn=algn)
        p.ph("主标题", "title", 0, x, y + 1.2, w, 5.6, "主标题（建议 16 字以内，最多 2 行）", size, self.tc(), bold=self.bold_title, algn=algn, anchor="ctr", lnspc=105)
        p.ph("副标题", "subTitle", IDX["subtitle"], x, y + 7.2, w, 1.4, "副标题或一句话摘要（建议 30 字以内）", 15, c["ink"], algn=algn)
        p.ph("署名 / 机构", "body", IDX["byline"], x, y + 9.6, w / 2, 0.8, "署名 / 机构（20 字以内）", 11, c["ink"], algn=algn)
        p.ph("日期", "body", IDX["date"], x + (w / 2 if algn == "l" else 0), y + (9.6 if algn == "l" else 10.5), w / 2 if algn == "l" else w, 0.8,
             "日期（12 字以内）", 11, c["ink"], algn=algn)

    def chapter_text(self, p, x=2.0, numcol=None, tcol=None, algn="l", y=3.6):
        c = self.C
        p.ph("章节号", "body", IDX["num"], x, y, 14, 5.4, "01", 110, numcol or self.nc(), bold=True, algn=algn, anchor="b", autofit=False)
        p.ph("章节标题", "title", 0, x, y + 5.8, 22, 2.4, "章节标题（14 字以内）", 38, tcol or self.tc(), bold=True, algn=algn, anchor="ctr")
        p.ph("导语", "body", IDX["lead"], x, y + 8.4, 22, 1.2, "一句导语（30 字以内）", 14, tcol or c["ink"], algn=algn)


# ---------------------------------------------------------------- 包豪斯
class Bauhaus(Base):
    """点线面三原色：每页最多三个几何形，至少一个出血；粗黑尺规线。"""
    key, file, title = "bauhaus", "garman-bauhaus", "包豪斯"

    def deco(self, p, kind):
        c = self.C
        if kind in ("toc", "body", "quote"):
            p.shape("ellipse", 28.6, -2.6, 7.6, 7.6, fill=c["pri"])
            p.rect(2.0, 3.6, 4.0, 0.22, c["ink"])
        if kind == "body":
            p.rect(24.6, 9.0, 6.6, 6.6, c["sec"])
            p.shape("triangle", 27.2, 13.0, 6.67, 6.05, fill=c["acc"])
        if kind == "end":
            p.shape("ellipse", 19.0, 2.0, 15.0, 15.0, fill=c["pri"])
            p.rect(26.0, 11.0, 7.87, 8.05, c["sec"])
            p.shape("triangle", 20.0, 12.0, 7.0, 7.05, fill=c["acc"])

    def cover(self, p):
        c = self.C
        p.shape("ellipse", 20.5, -3.0, 16.0, 16.0, fill=c["pri"])
        p.rect(20.5, 13.0, 6.4, 6.05, c["sec"])
        p.shape("triangle", 27.4, 12.4, 6.47, 6.65, fill=c["acc"])
        p.rect(2.0, 3.6, 5.0, 0.3, c["ink"])
        self.cover_text(p, y=4.4, w=17.5, size=50)
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.footer(p)
        p.shape("ellipse", -4.0, 3.0, 17.0, 17.0, fill=c["pri"])
        p.rect(27.6, 0, 6.27, 6.27, c["sec"])
        p.ph("章节号", "body", IDX["num"], 1.0, 6.6, 11, 6.0, "01", 120, on(c["pri"]), bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.ph("章节标题", "title", 0, 15.0, 7.0, 17, 2.4, "章节标题（14 字以内）", 38, c["ink"], bold=True, anchor="ctr")
        p.rect(15.0, 9.8, 4.0, 0.22, c["ink"])
        p.ph("导语", "body", IDX["lead"], 15.0, 10.4, 17, 1.6, "一句导语（30 字以内）", 14, c["ink"])
        return c["bg"], False


# ---------------------------------------------------------------- 装饰艺术
class ArtDeco(Base):
    """深底、对称、金属线：双线框加四角阶梯，标题上方放射线。"""
    key, file, title = "art-deco", "garman-art-deco", "装饰艺术"
    logo = (26.4, 1.55, 3.6, 0.9)

    def frame(self, p):
        c = self.C
        p.shape("rect", 0.9, 0.9, SW - 1.8, SH - 1.8, line=c["pri"], lw=1.5)
        p.shape("rect", 1.3, 1.3, SW - 2.6, SH - 2.6, line=c["pri"], lw=0.5)
        for (x, y) in [(1.3, 1.3), (SW - 3.3, 1.3), (1.3, SH - 3.3), (SW - 3.3, SH - 3.3)]:
            for k in range(3):
                d = 0.5 + k * 0.6
                xx = x if x < 10 else x + 2.0 - d
                yy = y if y < 10 else y + 2.0 - d
                p.shape("rect", xx, yy, d, d, line=c["pri"], lw=0.75)

    def rays(self, p, cx, cy, n=13, length=30, spread=150, col=None):
        for k in range(n):
            ang = -spread / 2 + spread * k / (n - 1)
            p.shape("rect", cx - 0.02, cy - length / 2, 0.04, length, fill=col or self.C["sec"], rot=ang)

    def deco(self, p, kind):
        c = self.C
        self.frame(p)
        if kind in ("body", "quote", "toc"):
            p.rect(SW / 2 - 4, 3.6, 8, 0.04, c["pri"])
            p.shape("diamond", SW / 2 - 0.3, 3.32, 0.6, 0.6, fill=c["acc"])

    def head(self, p, x=2.0, w=26.0):
        p.ph("标题", "title", 0, 3.0, 1.6, SW - 6.0, 1.8, "正文页标题（20 字以内）", 26, self.C["pri"], bold=True, algn="ctr", anchor="ctr")

    def tc(self):
        return self.C["pri"]

    def footer(self, p, dark=False):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], SW / 2 - 8, 16.85, 16, 0.5, "", 8, c["pri"], algn="ctr", anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 26.4, 16.85, 2.6, 0.5, "", 8, c["pri"], algn="r", anchor="ctr")

    def toc_head(self, p):
        p.ph("目录标题", "title", 0, 3.0, 1.6, SW - 6.0, 1.8, "目录标题（8 字以内）", 26, self.C["pri"], bold=True, algn="ctr", anchor="ctr")

    def cover(self, p):
        c = self.C
        self.rays(p, SW / 2, SH + 2.0, n=17, length=34, spread=140)
        p.shape("rect", 3.0, 3.0, SW - 6.0, 10.6, fill=c["bg"])
        self.frame(p)
        p.ph("Logo", "pic", IDX["logo"], SW / 2 - 2.5, 1.9, 5.0, 1.6, "插入 logo（透明 PNG）", 9, c["pri"])
        p.ph("眉题", "body", IDX["eyebrow"], 4.0, 4.0, SW - 8.0, 0.8, "眉题（建议 20 字以内）", 12, c["acc"], bold=True, algn="ctr")
        p.ph("主标题", "title", 0, 4.0, 5.0, SW - 8.0, 4.6, "主标题（建议 16 字以内，最多 2 行）", 44, c["pri"], bold=True, algn="ctr", anchor="ctr", lnspc=110)
        p.rect(SW / 2 - 5, 10.0, 10, 0.04, c["pri"])
        p.shape("diamond", SW / 2 - 0.3, 9.72, 0.6, 0.6, fill=c["acc"])
        p.ph("副标题", "subTitle", IDX["subtitle"], 4.0, 10.6, SW - 8.0, 1.0, "副标题或一句话摘要（建议 30 字以内）", 14, c["ink"], algn="ctr")
        p.ph("署名 / 机构", "body", IDX["byline"], 4.0, 12.0, SW / 2 - 4.6, 0.8, "署名 / 机构（20 字以内）", 11, c["ink"], algn="r")
        p.ph("日期", "body", IDX["date"], SW / 2 + 0.6, 12.0, SW / 2 - 4.6, 0.8, "日期（12 字以内）", 11, c["ink"])
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.rays(p, SW / 2, 6.0, n=24, length=40, spread=345, col=c["sec"])
        p.shape("ellipse", SW / 2 - 3.6, 2.4, 7.2, 7.2, fill=c["bg"], line=c["pri"], lw=1.5)
        self.frame(p)
        self.footer(p)
        p.ph("章节号", "body", IDX["num"], SW / 2 - 3.6, 2.4, 7.2, 7.2, "01", 66, c["pri"], bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.shape("rect", 3.0, 10.6, SW - 6.0, 4.6, fill=c["bg"])
        p.ph("章节标题", "title", 0, 3.0, 11.0, SW - 6.0, 2.2, "章节标题（14 字以内）", 34, c["pri"], bold=True, algn="ctr", anchor="ctr")
        p.ph("导语", "body", IDX["lead"], 3.0, 13.4, SW - 6.0, 1.0, "一句导语（30 字以内）", 13, c["ink"], algn="ctr")
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.rays(p, SW / 2, SH + 2.0, n=17, length=34, spread=140)
        p.shape("rect", 3.0, 3.0, SW - 6.0, 11.0, fill=c["bg"])
        self.frame(p)
        p.ph("Logo", "pic", IDX["logo"], SW / 2 - 2.5, 3.4, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["pri"])
        p.ph("结束语", "title", 0, 4.0, 6.0, SW - 8.0, 3.0, "结束语（8 字以内）", 48, c["pri"], bold=True, algn="ctr", anchor="ctr")
        p.ph("补充", "body", IDX["endsub"], 4.0, 9.6, SW - 8.0, 1.0, "一句收尾的话（30 字以内）", 15, c["ink"], algn="ctr")
        p.ph("联系方式", "body", IDX["contact"], 4.0, 12.0, SW - 8.0, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"], algn="ctr")
        return c["bg"], True

    def qc(self):
        return self.C["pri"]

    def nc(self, i=0):
        return self.C["acc"]


# ---------------------------------------------------------------- 构成主义
class Constructivism(Base):
    """斜线、红黑对撞：一条贯穿全页的斜向长条或楔形。"""
    key, file, title = "constructivism", "garman-constructivism", "构成主义"

    def bar(self, p, y, h=3.0, rot=-12, col=None):
        p.shape("rect", -4.0, y, SW + 8.0, h, fill=col or self.C["pri"], rot=rot)

    def deco(self, p, kind):
        c = self.C
        if kind in ("body", "quote", "toc"):
            self.bar(p, 17.2, 1.4)
            p.rect(2.0, 3.6, 7.0, 0.3, c["pri"])
        if kind == "body":
            p.shape("ellipse", 25.6, 5.0, 5.4, 5.4, fill=c["ink"])
            p.shape("rtTriangle", 23.4, 9.6, 8.4, 5.2, fill=c["sec"])
        if kind == "end":
            self.bar(p, 11.0, 4.0)
            p.shape("ellipse", 25.0, 1.8, 6.0, 6.0, fill=c["ink"])

    def nc(self, i=0):
        return self.C["pri"]

    def cover(self, p):
        c = self.C
        self.bar(p, 11.4, 4.2)
        p.shape("ellipse", 24.6, 1.6, 7.4, 7.4, fill=c["ink"])
        p.shape("rtTriangle", 20.0, 4.6, 6.2, 4.4, fill=c["sec"], rot=0)
        p.ph("眉题", "body", IDX["eyebrow"], 2.0, 1.8, 16, 0.8, "眉题（建议 20 字以内）", 13, c["pri"], bold=True)
        p.ph("主标题", "title", 0, 2.0, 2.9, 20, 7.2, "主标题（建议 16 字以内，最多 2 行）", 56, c["ink"], bold=True, anchor="ctr", lnspc=100)
        p.ph("副标题", "subTitle", IDX["subtitle"], 2.0, 10.2, 18, 1.0, "副标题或一句话摘要（建议 30 字以内）", 14, c["ink"], bold=True)
        p.ph("署名 / 机构", "body", IDX["byline"], 2.0, 11.4, 7, 0.8, "署名 / 机构（20 字以内）", 11, c["ink"], bold=True)
        p.ph("日期", "body", IDX["date"], 9.4, 11.4, 6, 0.8, "日期（12 字以内）", 11, c["ink"])
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.bar(p, 8.6, 5.4)
        p.shape("ellipse", 21.0, 1.2, 5.0, 5.0, fill=c["ink"])
        p.ph("章节号", "body", IDX["num"], 2.0, 0.8, 12, 6.6, "01", 130, c["ink"], bold=True, anchor="b", autofit=False)
        p.ph("章节标题", "title", 0, 14.0, 14.2, 18, 2.0, "章节标题（14 字以内）", 34, c["ink"], bold=True, algn="r", anchor="ctr")
        p.ph("导语", "body", IDX["lead"], 14.0, 16.4, 18, 0.9, "一句导语（30 字以内）", 13, c["ink"], algn="r")
        return c["bg"], False


# ---------------------------------------------------------------- 风格派
class DeStijl(Base):
    """横竖粗黑线和三原色格子：正文放在白格子里，色块格子不放字。"""
    key, file, title = "de-stijl", "garman-de-stijl", "风格派"
    logo = (27.0, 0.7, 3.6, 1.4)
    LW = 0.32

    def grid(self, p, xs, ys, fills):
        k = self.C["black"]
        for (x0, y0, x1, y1, col) in fills:
            p.rect(x0, y0, x1 - x0, y1 - y0, col)
        for x in xs:
            p.rect(x - self.LW / 2, 0, self.LW, SH, k)
        for (y, xa, xb) in ys:
            p.rect(xa, y - self.LW / 2, xb - xa, self.LW, k)

    def tc(self):
        return self.C["black"]

    def nc(self, i=0):
        return self.C["black"]

    def deco(self, p, kind):
        c = self.C
        if kind in ("body", "quote"):
            self.grid(p, [24.6, 29.0], [(4.0, 0, SW), (9.6, 24.6, SW), (14.4, 24.6, SW)],
                      [(24.6, 4.0, 29.0, 9.6, c["pri"]), (29.0, 9.6, SW, 14.4, c["sec"]), (24.6, 14.4, 29.0, SH, c["acc"])])
        if kind == "toc":
            self.grid(p, [31.4], [(4.0, 0, SW), (11.2, 31.4, SW)],
                      [(31.4, 4.0, SW, 11.2, c["pri"]), (31.4, 11.2, SW, SH, c["acc"])])
        if kind == "end":
            self.grid(p, [22.0, 28.0], [(6.0, 22.0, SW), (13.0, 22.0, SW)],
                      [(22.0, 0, 28.0, 6.0, c["sec"]), (28.0, 6.0, SW, 13.0, c["pri"]), (22.0, 13.0, 28.0, SH, c["acc"])])

    def quote(self, p):
        c = self.C
        self.deco(p, "quote")
        self.footer(p)
        self.head(p)
        p.ph("正文", "body", IDX["body"], 2.0, 4.8, 10.6, 11.6, "正文（建议 120 字以内）", 13, c["ink"], lnspc=160)
        p.rect(13.4, 4.0, self.LW, SH - 4.0, c["black"])
        p.ph("引文", "body", IDX["quote"], 14.4, 4.8, 9.4, 8.0, "“引文或金句（40 字以内）”", 22, c["black"], bold=True, lnspc=135)
        p.ph("出处 / 备注", "body", IDX["note"], 14.4, 13.4, 9.4, 0.8, "出处或备注（20 字以内）", 10, c["ink"])
        return c["bg"], False

    def body(self, p):
        c = self.C
        self.deco(p, "body")
        self.footer(p)
        self.head(p)
        p.ph("正文", "body", IDX["body"], 2.0, 4.8, 21.4, 11.6, "正文（建议 180 字以内，最多 3 段）", 15, c["ink"], lnspc=165)
        return c["bg"], False

    def footer(self, p, dark=False):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], 2.0, 18.05, 16, 0.6, "", 9, c["ink"], anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 20.0, 18.05, 2.0, 0.6, "", 9, c["ink"], algn="r", anchor="ctr")

    def cover(self, p):
        c = self.C
        self.grid(p, [21.2, 28.4], [(11.6, 0, 21.2), (5.4, 21.2, SW), (13.8, 21.2, SW)],
                  [(21.2, 0, 28.4, 5.4, c["pri"]), (28.4, 5.4, SW, 13.8, c["sec"]), (0, 11.6, 6.0, SH, c["acc"]),
                   (21.2, 13.8, 28.4, SH, c["p_soft"])])
        p.rect(6.0, 11.6, self.LW, SH - 11.6, c["black"])
        p.ph("眉题", "body", IDX["eyebrow"], 1.6, 1.4, 18, 0.8, "眉题（建议 20 字以内）", 12, c["black"], bold=True)
        p.ph("主标题", "title", 0, 1.6, 2.6, 18.4, 7.8, "主标题（建议 16 字以内，最多 2 行）", 50, c["black"], bold=True, anchor="ctr", lnspc=105)
        p.ph("副标题", "subTitle", IDX["subtitle"], 7.0, 12.4, 13.4, 2.0, "副标题或一句话摘要（建议 30 字以内）", 14, c["ink"])
        p.ph("署名 / 机构", "body", IDX["byline"], 7.0, 15.6, 13.4, 0.8, "署名 / 机构（20 字以内）", 11, c["ink"], bold=True)
        p.ph("日期", "body", IDX["date"], 7.0, 16.5, 13.4, 0.8, "日期（12 字以内）", 11, c["ink"])
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.grid(p, [12.0, 27.0], [(10.6, 0, 12.0), (7.0, 12.0, SW), (15.4, 27.0, SW)],
                  [(0, 0, 12.0, 10.6, c["pri"]), (27.0, 7.0, SW, 15.4, c["acc"]), (0, 10.6, 12.0, SH, c["p_soft"])])
        self.footer(p)
        p.ph("章节号", "body", IDX["num"], 13.0, 0.4, 13, 6.2, "01", 110, c["black"], bold=True, anchor="b", autofit=False)
        p.ph("章节标题", "title", 0, 13.0, 8.0, 13.4, 3.4, "章节标题（14 字以内）", 34, c["black"], bold=True, anchor="t")
        p.ph("导语", "body", IDX["lead"], 13.0, 11.8, 13.4, 2.0, "一句导语（30 字以内）", 13, c["ink"])
        return c["bg"], False


# ---------------------------------------------------------------- 孟菲斯
class Memphis(Base):
    """撞色、波浪线、点阵和玩具般的形状散布在四周，正文区留空。"""
    key, file, title = "memphis", "garman-memphis", "孟菲斯"

    def dots(self, p, x, y, cols=6, rows=4, gap=0.6, d=0.18, col=None):
        for i in range(cols):
            for j in range(rows):
                p.shape("ellipse", x + i * gap, y + j * gap, d, d, fill=col or self.C["ink"])

    def scatter(self, p, n=4):
        c = self.C
        p.shape("wave", 21.0, 1.0, 5.4, 1.4, fill=c["sec"], adj={"adj1": 20000, "adj2": 0})
        p.shape("triangle", 1.0, 15.6, 2.6, 2.4, fill=c["pri"], rot=-18)
        p.shape("ellipse", 30.4, 14.4, 2.2, 2.2, line=c["ink"], lw=3)
        if n > 3:
            self.dots(p, 27.0, 16.0, cols=5, rows=3)
            p.shape("donut", 0.4, 6.4, 1.2, 1.2, fill=c["acc"], line=c["ink"], lw=1.5)

    def panel(self, p, x, y, w, h, i=0):
        c = self.C
        p.rect(x + 0.25, y + 0.25, w, h, c["ink"])
        p.shape("rect", x, y, w, h, fill=[c["white"], c["acc"], c["white"], c["pri"]][i % 4] if i else c["white"], line=c["ink"], lw=2)

    def nc(self, i=0):
        return self.C["ink"]

    def deco(self, p, kind):
        self.scatter(p, 4 if kind in ("toc", "end") else 3)

    def head(self, p, x=2.0, w=24.0):
        super().head(p, 3.2, 22.0)

    def cover(self, p):
        c = self.C
        self.scatter(p)
        p.shape("ellipse", 22.6, 3.4, 8.6, 8.6, fill=c["pri"])
        p.shape("triangle", 25.6, 9.6, 6.2, 5.6, fill=c["sec"], rot=12)
        p.shape("wave", 21.0, 14.0, 7.4, 2.0, fill=c["acc"], adj={"adj1": 20000, "adj2": 0})
        self.dots(p, 19.6, 2.4, cols=4, rows=5, gap=0.7)
        self.panel(p, 2.4, 3.0, 17.6, 12.4)
        self.cover_text(p, x=3.4, y=3.6, w=15.6, size=44)
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.scatter(p)
        p.shape("ellipse", 3.0, 3.6, 10.0, 10.0, fill=c["pri"], line=c["ink"], lw=3)
        self.dots(p, 11.4, 11.4, cols=5, rows=4, gap=0.7)
        p.ph("章节号", "body", IDX["num"], 3.0, 3.6, 10.0, 10.0, "01", 110, on(c["pri"]), bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.ph("章节标题", "title", 0, 15.4, 6.2, 16, 2.6, "章节标题（14 字以内）", 38, c["ink"], bold=True, anchor="b")
        p.shape("wave", 15.4, 9.2, 6.0, 1.0, fill=c["sec"], adj={"adj1": 20000, "adj2": 0})
        p.ph("导语", "body", IDX["lead"], 15.4, 10.6, 16, 1.4, "一句导语（30 字以内）", 14, c["ink"])
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.scatter(p)
        self.panel(p, 6.0, 4.0, 21.87, 9.0)
        p.ph("Logo", "pic", IDX["logo"], 13.93, 1.0, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["ink"])
        p.ph("结束语", "title", 0, 7.0, 4.8, 19.87, 4.6, "结束语（8 字以内）", 50, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("补充", "body", IDX["endsub"], 7.0, 9.8, 19.87, 1.2, "一句收尾的话（30 字以内）", 15, c["ink"], algn="ctr")
        p.ph("联系方式", "body", IDX["contact"], 7.0, 14.6, 19.87, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"], algn="ctr")
        return c["bg"], True


# ---------------------------------------------------------------- 波普艺术
class PopArt(Base):
    """漫画分格、粗黑描边、角落网点，爆炸对话框全份最多两处。"""
    key, file, title = "pop-art", "garman-pop-art", "波普艺术"

    def halftone(self, p, x, y, cols=9, rows=6, gap=0.7, col=None):
        for i in range(cols):
            for j in range(rows):
                d = 0.62 * (1 - (i + j) / (cols + rows))
                if d > 0.06:
                    p.shape("ellipse", x + i * gap + (0.35 if j % 2 else 0), y + j * gap, d, d, fill=col or self.C["sec"])

    def panel(self, p, x, y, w, h, i=0):
        c = self.C
        p.shape("rect", x, y, w, h, fill=[c["white"], c["acc"], c["white"], c["white"]][i % 4], line=c["ink"], lw=4)

    def nc(self, i=0):
        return self.C["sec"]

    def deco(self, p, kind):
        if kind in ("toc", "body", "quote"):
            self.halftone(p, 27.0, 14.0, cols=9, rows=6)

    def cover(self, p):
        c = self.C
        self.halftone(p, 0.6, 0.6, cols=12, rows=8, gap=0.75, col=c["pri"])
        self.panel(p, 2.0, 3.4, 19.0, 13.4)
        p.shape("rect", 22.0, 3.4, 9.87, 13.4, fill=c["pri"], line=c["ink"], lw=4)
        p.shape("irregularSeal1", 21.0, 1.0, 9.0, 6.4, fill=c["acc"], line=c["ink"], lw=3)
        p.ph("眉题", "body", IDX["eyebrow"], 22.6, 3.1, 5.8, 1.6, "眉题（20 字以内）", 12, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("主标题", "title", 0, 3.0, 4.4, 17.0, 7.0, "主标题（建议 16 字以内，最多 2 行）", 50, c["ink"], bold=True, anchor="ctr", lnspc=100)
        p.ph("副标题", "subTitle", IDX["subtitle"], 23.0, 9.0, 7.87, 4.0, "副标题或一句话摘要（建议 30 字以内）", 16, on(c["pri"]), bold=True, anchor="ctr")
        p.ph("署名 / 机构", "body", IDX["byline"], 3.0, 13.4, 8.0, 0.8, "署名 / 机构（20 字以内）", 12, c["ink"], bold=True)
        p.ph("日期", "body", IDX["date"], 3.0, 14.4, 8.0, 0.8, "日期（12 字以内）", 12, c["ink"])
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.halftone(p, 18.0, 0.8, cols=20, rows=12, gap=0.8, col=c["acc"])
        p.shape("irregularSeal2", 2.0, 2.0, 13.0, 11.0, fill=c["sec"], line=c["ink"], lw=4)
        p.ph("章节号", "body", IDX["num"], 4.0, 4.4, 9.0, 6.0, "01", 100, on(c["sec"]), bold=True, algn="ctr", anchor="ctr", autofit=False)
        self.panel(p, 16.0, 9.4, 15.87, 6.6)
        p.ph("章节标题", "title", 0, 17.0, 10.2, 14, 2.6, "章节标题（14 字以内）", 34, c["ink"], bold=True, anchor="ctr")
        p.ph("导语", "body", IDX["lead"], 17.0, 13.2, 14, 1.4, "一句导语（30 字以内）", 13, c["ink"])
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.halftone(p, 0.6, 10.0, cols=14, rows=10, gap=0.8, col=c["pri"])
        p.shape("irregularSeal1", 6.0, 2.2, 22.0, 12.0, fill=c["acc"], line=c["ink"], lw=4)
        p.ph("Logo", "pic", IDX["logo"], 26.4, 1.0, 5.4, 2.2, "插入 logo（透明 PNG）", 10, c["ink"])
        p.ph("结束语", "title", 0, 10.0, 5.6, 14.0, 3.2, "结束语（8 字以内）", 48, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("补充", "body", IDX["endsub"], 10.0, 9.0, 14.0, 1.2, "一句收尾的话（30 字以内）", 14, c["ink"], bold=True, algn="ctr")
        p.ph("联系方式", "body", IDX["contact"], 2.0, 16.6, 29.87, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"], algn="r")
        return c["bg"], True


# ---------------------------------------------------------------- 千禧未来风
class Y2K(Base):
    """半透明塑料感圆角卡片、四角星与气泡、柔和投影。"""
    key, file, title = "y2k", "garman-y2k", "千禧未来风"

    def star(self, p, x, y, d, col=None):
        p.shape("star4", x, y, d, d, fill=col or self.C["acc"], adj={"adj": 12500})

    def bubble(self, p, x, y, d):
        c = self.C
        p.shape("ellipse", x, y, d, d, fill=c["white"], line=c["pri"], lw=1.5)
        alpha_fill(p, 55)
        p.shape("ellipse", x + d * 0.22, y + d * 0.18, d * 0.25, d * 0.18, fill=c["white"])

    def panel(self, p, x, y, w, h, i=0):
        c = self.C
        p.shape("roundRect", x, y, w, h, fill=[c["white"], c["sec"], c["white"], c["sec"]][i % 4],
                line=c["pri"], lw=1.25, adj={"adj": int(0.7 / min(w, h) * 100000)})
        alpha_fill(p, 85)
        drop_shadow(p)

    def nc(self, i=0):
        return self.C["pri"] if _lum(self.C["pri"]) < 0.5 else self.C["ink"]

    def deco(self, p, kind):
        self.star(p, 26.8, 1.4, 1.4)
        self.star(p, 25.8, 3.0, 0.7, self.C["pri"])
        if kind in ("body", "quote", "end"):
            self.bubble(p, 27.0, 14.0, 2.6)

    def cover(self, p):
        c = self.C
        p.shape("ellipse", 18.0, -4.0, 20.0, 20.0, fill=c["pri"])
        alpha_fill(p, 55)
        soft_edge(p, 2.0)
        p.shape("ellipse", 22.0, 9.0, 12.0, 12.0, fill=c["sec"])
        soft_edge(p, 1.5)
        self.panel(p, 2.0, 2.6, 21.0, 13.8)
        self.star(p, 21.2, 1.4, 2.6)
        self.star(p, 24.4, 3.8, 1.2, c["pri"])
        self.bubble(p, 26.0, 12.0, 3.4)
        self.cover_text(p, x=3.4, y=3.0, w=18.2, size=44)
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.footer(p)
        p.shape("ellipse", -3.0, 0.0, 19.0, 19.0, fill=c["pri"])
        alpha_fill(p, 60)
        soft_edge(p, 2.0)
        self.panel(p, 3.0, 4.0, 10.0, 10.0)
        self.star(p, 11.6, 2.6, 2.4)
        p.ph("章节号", "body", IDX["num"], 3.0, 4.0, 10.0, 10.0, "01", 100, self.nc(), bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.ph("章节标题", "title", 0, 15.4, 6.6, 16.4, 2.6, "章节标题（14 字以内）", 36, c["ink"], bold=True, anchor="b")
        p.ph("导语", "body", IDX["lead"], 15.4, 9.6, 16.4, 1.4, "一句导语（30 字以内）", 14, c["ink"])
        self.bubble(p, 27.0, 12.6, 3.0)
        return c["bg"], False


# ---------------------------------------------------------------- 蒸汽波
class Vaporwave(Base):
    """霓虹落日和透视网格只用于封面和章节页；内容页用复古视窗框。"""
    key, file, title = "vaporwave", "garman-vaporwave", "蒸汽波"

    def scene(self, p, horizon=11.0, sun=(SW / 2, 8.0, 9.0)):
        c = self.C
        vx = SW / 2
        for k in range(-9, 10):  # 透视放射线：以消失点为中心的长线，上半截被天空盖住
            ang = k * 8.5
            p.shape("rect", vx - 0.025, horizon - 30, 0.05, 60, fill=c["pri"], rot=ang)
        y, step = horizon + 0.3, 0.35
        while y < SH:
            p.rect(0, y, SW, 0.05, c["pri"])
            step *= 1.45
            y += step
        p.rect(0, 0, SW, horizon, c["bg"])
        cx, cy, d = sun
        p.shape("ellipse", cx - d / 2, cy - d / 2, d, d, fill=c["sec"])
        for k in range(5):  # 落日条纹：用底色横条切开
            yy = cy + d * 0.08 + k * d * 0.09
            p.rect(cx - d / 2, yy, d, 0.12 + k * 0.08, c["bg"])
        p.rect(0, horizon - 0.04, SW, 0.08, c["pri"])

    def window(self, p, x, y, w, h, title=True):
        c = self.C
        p.shape("rect", x, y, w, h, fill=c["p_base"] if _dark(c["bg"]) else c["white"], line=c["pri"], lw=1.5)
        p.rect(x, y, w, 0.9, c["pri"])
        for k in range(3):
            p.shape("rect", x + w - 0.8 - k * 0.7, y + 0.2, 0.5, 0.5, fill=c["bg"], line=c["ink"], lw=0.75)

    def panel(self, p, x, y, w, h, i=0):
        self.window(p, x, y - 0.6, w, h + 0.6)

    def nc(self, i=0):
        return self.C["sec"]

    def qc(self):
        return self.C["pri"]

    def tc(self):
        return self.C["ink"]

    def cover(self, p):
        c = self.C
        self.scene(p, horizon=12.2, sun=(24.6, 7.6, 8.4))
        p.ph("眉题", "body", IDX["eyebrow"], 2.0, 2.2, 16, 0.8, "眉题（建议 20 字以内）", 12, c["pri"], bold=True)
        p.ph("主标题", "title", 0, 2.0, 3.2, 17.0, 6.4, "主标题（建议 16 字以内，最多 2 行）", 46, c["ink"], bold=True, anchor="ctr", lnspc=105)
        p.ph("副标题", "subTitle", IDX["subtitle"], 2.0, 9.8, 17.0, 1.0, "副标题或一句话摘要（建议 30 字以内）", 14, c["ink"])
        p.ph("署名 / 机构", "body", IDX["byline"], 2.0, 13.0, 9.0, 0.8, "署名 / 机构（20 字以内）", 11, c["ink"], bold=True)
        p.ph("日期", "body", IDX["date"], 2.0, 13.9, 9.0, 0.8, "日期（12 字以内）", 11, c["ink"])
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.scene(p, horizon=12.0, sun=(SW / 2, 7.4, 9.6))
        self.footer(p)
        p.ph("章节号", "body", IDX["num"], SW / 2 - 4.8, 2.6, 9.6, 6.0, "01", 90, c["bg"], bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.rect(4.0, 13.0, SW - 8.0, 3.6, c["bg"])
        p.ph("章节标题", "title", 0, 4.0, 13.2, SW - 8.0, 2.0, "章节标题（14 字以内）", 34, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("导语", "body", IDX["lead"], 4.0, 15.4, SW - 8.0, 1.0, "一句导语（30 字以内）", 13, c["pri"], algn="ctr")
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.scene(p, horizon=11.6, sun=(SW / 2, 6.0, 8.0))
        p.ph("Logo", "pic", IDX["logo"], 1.6, 1.2, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["ink"])
        p.rect(4.0, 12.4, SW - 8.0, 5.0, c["bg"])
        p.ph("结束语", "title", 0, 4.0, 12.6, SW - 8.0, 2.4, "结束语（8 字以内）", 44, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("补充", "body", IDX["endsub"], 4.0, 15.0, SW - 8.0, 1.0, "一句收尾的话（30 字以内）", 14, c["pri"], algn="ctr")
        p.ph("联系方式", "body", IDX["contact"], 4.0, 16.2, SW - 8.0, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"], algn="ctr")
        return c["bg"], True


# ---------------------------------------------------------------- 玻璃拟态
class Glass(Base):
    """深底上两三个模糊色团，前面浮着半透明磨砂面板，面板带 1 像素半透明白边。"""
    key, file, title = "glassmorphism", "garman-glassmorphism", "玻璃拟态"

    def blobs(self, p, spots):
        c = self.C
        for (x, y, d, col) in spots:
            p.shape("ellipse", x, y, d, d, fill=c[col])
            soft_edge(p, d * 0.22)

    def panel(self, p, x, y, w, h, i=0):
        c = self.C
        p.shape("roundRect", x, y, w, h, fill="FFFFFF", line="FFFFFF", lw=1, adj={"adj": int(0.6 / min(w, h) * 100000)})
        alpha_fill(p, 14)
        alpha_line(p, 45)

    def nc(self, i=0):
        return self.C["pri"]

    def qc(self):
        return self.C["ink"]

    def deco(self, p, kind):
        self.blobs(p, [(-4.0, 11.0, 10.0, "pri"), (24.0, 9.0, 13.0, "sec")])

    def cover(self, p):
        c = self.C
        self.blobs(p, [(-5.0, 9.0, 15.0, "pri"), (20.0, 6.0, 15.0, "sec"), (15.0, -5.5, 7.0, "p_main")])
        self.panel(p, 2.4, 2.6, 22.0, 13.8)
        self.cover_text(p, x=3.6, y=3.2, w=19.6, size=44)
        return c["bg"], True

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.blobs(p, [(2.0, 1.0, 14.0, "pri"), (22.0, 8.0, 12.0, "sec")])
        self.panel(p, 4.0, 4.2, 25.87, 10.6)
        self.chapter_text(p, x=5.6, numcol=c["ink"], tcol=c["ink"], y=3.4)
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.blobs(p, [(-2.0, 6.0, 14.0, "pri"), (22.0, -3.0, 14.0, "sec")])
        self.panel(p, 4.0, 3.4, 25.87, 12.2)
        p.ph("Logo", "pic", IDX["logo"], 14.43, 4.2, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["ink"])
        p.ph("结束语", "title", 0, 5.0, 6.6, 23.87, 3.0, "结束语（8 字以内）", 48, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("补充", "body", IDX["endsub"], 5.0, 10.0, 23.87, 1.2, "一句收尾的话（30 字以内）", 15, c["ink"], algn="ctr")
        p.ph("联系方式", "body", IDX["contact"], 5.0, 13.6, 23.87, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"], algn="ctr")
        return c["bg"], True


BATCH3 = {cls.key: cls for cls in (Bauhaus, ArtDeco, Constructivism, DeStijl, Memphis, PopArt, Y2K, Vaporwave, Glass)}

if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    tmpdir = os.path.join(outdir, ".tmp")
    os.makedirs(tmpdir, exist_ok=True)
    for cls in BATCH3.values():
        print(build(cls(), outdir, tmpdir))
