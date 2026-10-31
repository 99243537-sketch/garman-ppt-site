"""生成 3 套 GarmanPPT 母版（.pptx）：真实版式占位符 + 示例页 + 逐个出现的透明度动画。

用法：python3 build_masters.py <输出目录>
依赖：python-pptx 1.0.x、lxml、Pillow
"""
import copy
import os
import sys
import zipfile

from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

VERSION = "v1"
W, H = 12192000, 6858000  # 16:9，33.867 × 19.05 cm
NSMAP = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
NSDECL = " ".join(f'xmlns:{k}="{v}"' for k, v in NSMAP.items())
FONT = "微软雅黑"
FOOTER_TEXT = "母版：GarmanPPT · AI 辅助生成"


def cm(v):
    return int(round(v * 360000))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse(xml):
    return etree.fromstring(f"<root {NSDECL}>{xml}</root>")[0]


# ---------- 占位符 idx 约定：三套母版一致，换母版时内容能自动归位 ----------
IDX = dict(eyebrow=10, subtitle=1, byline=13, date=14, logo=15,
           toc=[21, 22, 23, 24], num=30, lead=31, body=1, quote=40, note=41,
           endsub=50, contact=51, ftr=11, sldnum=12)


class Part:
    """给一个版式或母版累积形状 XML，分配不重复的 id。"""

    def __init__(self):
        self.xml = []
        self.nid = 2

    def _id(self):
        self.nid += 1
        return self.nid

    def ph(self, name, kind, idx, x, y, w, h, prompt, sz, color, bold=False, algn="l",
           anchor="t", lnspc=None, lvl2=None, numcol=1, spccol=0, autofit=True):
        """kind: title / subTitle / body / pic / ftr / sldNum"""
        attrs = f'type="{kind}"' if kind != "body" else 'type="body"'
        if kind not in ("title",):
            attrs += f' idx="{idx}"'
        if kind in ("ftr", "sldNum", "pic") or kind == "body":
            attrs += ' sz="quarter"'
        if kind not in ("ftr", "sldNum"):
            attrs += ' hasCustomPrompt="1"'
        ln = f'<a:lnSpc><a:spcPct val="{lnspc * 1000}"/></a:lnSpc>' if lnspc else ""
        b = ' b="1"' if bold else ' b="0"'
        lvl1 = (f'<a:lvl1pPr marL="0" indent="0" algn="{algn}">{ln}<a:spcBef><a:spcPts val="0"/></a:spcBef>'
                f'<a:buNone/><a:defRPr sz="{int(sz * 100)}"{b}><a:solidFill><a:srgbClr val="{color}"/>'
                f'</a:solidFill></a:defRPr></a:lvl1pPr>')
        lvl2x = ""
        if lvl2:
            s2, c2 = lvl2
            lvl2x = (f'<a:lvl2pPr marL="0" indent="0" algn="{algn}"><a:spcBef><a:spcPts val="300"/></a:spcBef>'
                     f'<a:buNone/><a:defRPr sz="{int(s2 * 100)}" b="0"><a:solidFill><a:srgbClr val="{c2}"/>'
                     f'</a:solidFill></a:defRPr></a:lvl2pPr>')
        cols = f' numCol="{numcol}" spcCol="{cm(spccol)}"' if numcol > 1 else ""
        fit = "<a:normAutofit/>" if autofit else "<a:noAutofit/>"
        if kind == "sldNum":
            paras = ('<a:p><a:fld id="{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}" type="slidenum">'
                     '<a:rPr lang="zh-CN"/><a:t>‹#›</a:t></a:fld></a:p>')
        else:
            lines = prompt if isinstance(prompt, list) else [(prompt, 0)]
            paras = "".join(
                f'<a:p>{'<a:pPr lvl="%d"/>' % lv if lv else ""}<a:r><a:rPr lang="zh-CN" altLang="en-US"/>'
                f'<a:t>{esc(t)}</a:t></a:r></a:p>' for t, lv in lines)
        sid = self._id()
        self.xml.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)}"/><p:cNvSpPr><a:spLocks noGrp="1"/>'
            f'</p:cNvSpPr><p:nvPr><p:ph {attrs}/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm>'
            f'<a:off x="{cm(x)}" y="{cm(y)}"/><a:ext cx="{cm(w)}" cy="{cm(h)}"/></a:xfrm></p:spPr>'
            f'<p:txBody><a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}" wrap="square"{cols}>'
            f'{fit}</a:bodyPr><a:lstStyle>{lvl1}{lvl2x}</a:lstStyle>{paras}</p:txBody></p:sp>')

    def shape(self, prst, x, y, w, h, fill=None, line=None, lw=1.0, rot=0, adj=None, name=None,
              text=None, sz=12, color="000000", bold=False, algn="ctr", anchor="ctr"):
        sid = self._id()
        av = "".join(f'<a:gd name="{k}" fmla="val {v}"/>' for k, v in (adj or {}).items())
        f = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        ln = (f'<a:ln w="{int(lw * 12700)}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
              if line else "<a:ln><a:noFill/></a:ln>")
        r = f' rot="{rot * 60000}"' if rot else ""
        if text is None:
            tx = '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="zh-CN"/></a:p></p:txBody>'
        else:
            tx = (f'<p:txBody><a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}" wrap="square">'
                  f'<a:noAutofit/></a:bodyPr><a:lstStyle/><a:p><a:pPr algn="{algn}"/><a:r>'
                  f'<a:rPr lang="zh-CN" sz="{int(sz * 100)}" b="{1 if bold else 0}"><a:solidFill>'
                  f'<a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{esc(text)}</a:t></a:r></a:p></p:txBody>')
        self.xml.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name or "装饰 " + str(sid))}"/><p:cNvSpPr/>'
            f'<p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr><a:xfrm{r}><a:off x="{cm(x)}" y="{cm(y)}"/>'
            f'<a:ext cx="{cm(w)}" cy="{cm(h)}"/></a:xfrm><a:prstGeom prst="{prst}"><a:avLst>{av}</a:avLst>'
            f'</a:prstGeom>{f}{ln}</p:spPr>{tx}</p:sp>')

    def rect(self, x, y, w, h, fill):
        self.shape("rect", x, y, w, h, fill=fill)

    def pic(self, rid, x, y, w, h, name):
        sid = self._id()
        self.xml.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{esc(name)}" descr="Logo 示意图，请替换"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{cm(x)}" y="{cm(y)}"/><a:ext cx="{cm(w)}" cy="{cm(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


# ---------- 三套风格 ----------
# 每套风格提供：colors、master(part)、logo 位置、6 个版式函数。
# 版式函数写入 Part，返回 (背景色, 是否隐藏母版图形)。

class Editorial:
    key, file = "editorial", "garman-editorial-amazonite"
    title = "编辑杂志风 × 天河石"
    C = dict(bg="EFF8F9", deep="122947", ink="1E1E1E", muted="53686A", line="C8D5D4",
             accent="B04D2F", main="70C6D6", white="FFFFFF")
    theme = ["1E1E1E", "FFFFFF", "122947", "EFF8F9", "70C6D6", "B04D2F", "53686A", "C8D5D4", "1B667A", "DDF1F2"]
    logo = (29.4, 0.75, 3.6, 1.4)
    chapter_num = "01"

    def footer(self, p, dark=False):
        c = self.C
        col = c["line"] if dark else c["muted"]
        p.ph("刊头 / 页脚", "ftr", IDX["ftr"], 2.0, 0.95, 20, 0.6, "", 9, col, bold=True, anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 29.87, 17.9, 2.0, 0.6, "", 9, col, algn="r", anchor="ctr")
        p.rect(2.0, 2.45, 29.87, 0.03, c["line"])

    def cover(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 2.0, 1.5, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["muted"])
        p.ph("眉题", "body", IDX["eyebrow"], 2.0, 5.0, 22, 0.8, "眉题（建议 20 字以内）", 12, c["accent"], bold=True)
        p.ph("主标题", "title", 0, 2.0, 6.2, 24, 5.6, "主标题（建议 16 字以内，最多 2 行）", 48, c["deep"], bold=True, lnspc=110)
        p.rect(2.0, 13.0, 29.87, 0.03, c["line"])
        p.ph("署名 / 机构", "body", IDX["byline"], 2.0, 13.6, 10, 0.7, "署名 / 机构（20 字以内）", 11, c["muted"])
        p.ph("日期", "body", IDX["date"], 2.0, 14.4, 10, 0.7, "日期（12 字以内）", 11, c["muted"])
        p.ph("副标题", "subTitle", IDX["subtitle"], 16.0, 13.6, 15.87, 2.0, "副标题或一句话摘要（建议 30 字以内）", 12, c["muted"], lnspc=140)
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.footer(p)
        p.ph("目录标题", "title", 0, 2.0, 3.0, 24, 1.8, "目录标题（8 字以内）", 32, c["deep"], bold=True, anchor="ctr")
        for i, idx in enumerate(IDX["toc"]):
            y = 5.7 + i * 2.75
            p.shape("rect", 2.0, y, 2.2, 1.0, text=f"0{i + 1}", sz=16, color=c["accent"], bold=True, algn="l", anchor="t")
            p.ph(f"目录条目 {i + 1}", "body", idx, 4.6, y, 27.27, 2.0,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 18, c["deep"], bold=True,
                 lvl2=(11, c["muted"]))
            p.rect(2.0, y + 2.3, 29.87, 0.03, c["line"])
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.footer(p, dark=True)
        p.ph("章节号", "body", IDX["num"], 2.0, 3.6, 12, 4.6, "01", 96, c["main"], bold=True, anchor="b", autofit=False)
        p.ph("章节标题", "title", 0, 2.0, 8.8, 28, 2.4, "章节标题（14 字以内）", 36, c["white"], bold=True, anchor="ctr")
        p.ph("导语", "body", IDX["lead"], 2.0, 11.6, 28, 1.2, "一句导语（30 字以内）", 14, c["line"])
        return c["deep"], False

    def body(self, p):
        c = self.C
        self.footer(p)
        p.ph("标题", "title", 0, 2.0, 3.0, 27, 1.8, "正文页标题（20 字以内）", 28, c["deep"], bold=True, anchor="ctr")
        p.ph("正文", "body", IDX["body"], 2.0, 5.6, 22.0, 11.4, "正文（建议 180 字以内，最多 3 段）",
             15, c["ink"], lnspc=170)
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.footer(p)
        p.ph("标题", "title", 0, 2.0, 3.0, 27, 1.8, "正文页标题（20 字以内）", 28, c["deep"], bold=True, anchor="ctr")
        p.ph("正文", "body", IDX["body"], 2.0, 5.6, 17.5, 11.4, "正文（建议 120 字以内）", 14, c["ink"], lnspc=165)
        p.rect(21.0, 5.6, 0.12, 5.0, c["accent"])
        p.ph("引文", "body", IDX["quote"], 21.6, 5.6, 10.27, 5.0, "“引文或金句（40 字以内）”", 20, c["deep"], bold=True, lnspc=140)
        p.ph("出处 / 备注", "body", IDX["note"], 21.6, 11.2, 10.27, 0.8, "出处或备注（20 字以内）", 10, c["muted"])
        return c["bg"], False

    def end(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 2.0, 1.5, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["muted"])
        p.ph("结束语", "title", 0, 2.0, 5.0, 24, 2.6, "结束语（8 字以内）", 48, c["deep"], bold=True, anchor="b")
        p.rect(2.0, 8.3, 2.4, 0.12, c["accent"])
        p.ph("补充", "body", IDX["endsub"], 2.0, 9.0, 28, 1.0, "一句收尾的话（30 字以内）", 16, c["muted"])
        p.rect(2.0, 15.0, 29.87, 0.03, c["line"])
        p.ph("联系方式", "body", IDX["contact"], 2.0, 15.6, 28, 0.8, "联系方式 / 网址（30 字以内）", 11, c["muted"])
        return c["bg"], True


class Brutal:
    key, file = "neubrutalism", "garman-neubrutalism-ginkgo"
    title = "新粗野主义 × 银杏"
    C = dict(bg="F7F5EE", ink="121212", yellow="F0CF4C", blue="82B2FF", white="FFFFFF", beige="EFEBDC")
    theme = ["121212", "FFFFFF", "121212", "F7F5EE", "F0CF4C", "82B2FF", "EFEBDC", "121212", "F0CF4C", "82B2FF"]
    logo = (29.4, 0.6, 3.6, 1.4)
    chapter_num = "01"

    def card(self, p, x, y, w, h, fill, off=0.3, lw=3):
        p.shape("roundRect", x + off, y + off, w, h, fill=self.C["ink"], adj={"adj": 6000})
        p.shape("roundRect", x, y, w, h, fill=fill, line=self.C["ink"], lw=lw, adj={"adj": 6000})

    def footer(self, p):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], 2.0, 18.0, 18, 0.6, "", 9, c["ink"], bold=True, anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 29.87, 18.0, 2.0, 0.6, "", 9, c["ink"], bold=True, algn="r", anchor="ctr")

    def head(self, p):
        p.ph("标题", "title", 0, 2.0, 1.2, 26, 2.0, "正文页标题（20 字以内）", 28, self.C["ink"], bold=True, anchor="ctr")

    def cover(self, p):
        c = self.C
        self.card(p, 1.78, 1.78, 19.3, 13.72, c["yellow"])
        self.card(p, 2.79, 2.79, 9.0, 1.27, c["white"], off=0.16, lw=2.25)
        p.ph("眉题", "body", IDX["eyebrow"], 2.95, 2.84, 8.7, 1.17, "眉题（20 字以内）", 10, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("主标题", "title", 0, 2.79, 5.08, 17.78, 6.6, "主标题（建议 16 字以内，最多 2 行）", 54, c["ink"], bold=True, anchor="ctr", lnspc=105)
        p.ph("署名 / 机构", "body", IDX["byline"], 2.79, 12.45, 8.6, 1.2, "署名 / 机构（20 字以内）", 12, c["ink"], bold=True, anchor="ctr")
        p.ph("日期", "body", IDX["date"], 11.6, 12.45, 8.9, 1.2, "日期（12 字以内）", 12, c["ink"], bold=True, anchor="ctr")
        self.card(p, 22.35, 1.78, 9.65, 6.35, c["blue"])
        p.ph("副标题", "subTitle", IDX["subtitle"], 23.1, 2.5, 8.15, 4.9, "副标题或一句话摘要（建议 30 字以内）", 20, c["ink"], bold=True, algn="ctr", anchor="ctr")
        self.card(p, 22.35, 9.14, 9.65, 6.35, c["white"])
        p.ph("Logo", "pic", IDX["logo"], 24.17, 11.1, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["ink"])
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.footer(p)
        p.ph("目录标题", "title", 0, 2.0, 1.2, 26, 2.0, "目录标题（8 字以内）", 28, c["ink"], bold=True, anchor="ctr")
        fills = [c["yellow"], c["blue"], c["white"], c["beige"]]
        for i, idx in enumerate(IDX["toc"]):
            x = 2.0 if i % 2 == 0 else 17.4
            y = 4.2 if i < 2 else 10.9
            self.card(p, x, y, 14.4, 5.6, fills[i])
            p.shape("rect", x + 0.8, y + 0.6, 3, 1.0, text=f"0{i + 1}", sz=16, color=c["ink"], bold=True, algn="l", anchor="t")
            p.ph(f"目录条目 {i + 1}", "body", idx, x + 0.8, y + 2.2, 12.8, 2.8,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 20, c["ink"], bold=True, lvl2=(12, c["ink"]))
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.card(p, 2.2, 4.4, 9.0, 9.0, c["yellow"], off=0.4)
        p.ph("章节号", "body", IDX["num"], 2.2, 4.4, 9.0, 9.0, "01", 120, c["ink"], bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.ph("章节标题", "title", 0, 13.4, 6.4, 18.4, 2.6, "章节标题（14 字以内）", 40, c["ink"], bold=True, anchor="b")
        p.ph("导语", "body", IDX["lead"], 13.4, 9.4, 18.4, 2.0, "一句导语（30 字以内）", 14, c["ink"], bold=True)
        return c["blue"], False

    def body(self, p):
        c = self.C
        self.footer(p)
        self.head(p)
        self.card(p, 2.0, 4.2, 29.5, 12.8, c["white"])
        p.ph("正文", "body", IDX["body"], 3.0, 5.0, 27.5, 11.2, "正文（建议 180 字以内，最多 3 段）", 16, c["ink"], lnspc=160)
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.footer(p)
        self.head(p)
        self.card(p, 2.0, 4.2, 18.4, 12.8, c["white"])
        p.ph("正文", "body", IDX["body"], 3.0, 5.0, 16.4, 11.2, "正文（建议 120 字以内）", 16, c["ink"], lnspc=160)
        self.card(p, 21.4, 4.2, 10.1, 8.6, c["yellow"])
        p.ph("引文", "body", IDX["quote"], 22.2, 5.0, 8.5, 7.0, "“引文或金句（40 字以内）”", 22, c["ink"], bold=True, anchor="ctr", lnspc=130)
        self.card(p, 21.4, 14.0, 10.1, 1.6, c["blue"], off=0.16, lw=2.25)
        p.ph("出处 / 备注", "body", IDX["note"], 21.8, 14.1, 9.3, 1.4, "出处或备注（20 字以内）", 11, c["ink"], bold=True, algn="ctr", anchor="ctr")
        return c["bg"], False

    def end(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 13.93, 0.8, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["ink"])
        self.card(p, 5.0, 3.8, 23.87, 8.0, c["white"], off=0.4)
        p.ph("结束语", "title", 0, 6.0, 4.4, 21.87, 6.8, "结束语（8 字以内）", 44, c["ink"], bold=True, algn="ctr", anchor="ctr")
        self.card(p, 8.9, 12.8, 16.07, 1.5, c["blue"], off=0.16, lw=2.25)
        p.ph("补充", "body", IDX["endsub"], 9.2, 12.85, 15.47, 1.4, "一句收尾的话（30 字以内）", 14, c["ink"], bold=True, algn="ctr", anchor="ctr")
        p.ph("联系方式", "body", IDX["contact"], 5.0, 15.6, 23.87, 0.8, "联系方式 / 网址（30 字以内）", 11, c["ink"], bold=True, algn="ctr")
        return c["yellow"], True


class Nouveau:
    key, file = "art-nouveau", "garman-art-nouveau-nautilus"
    title = "新艺术运动 × 鹦鹉螺"
    C = dict(bg="F8F5EE", deep="725A21", accent="9F5947", line="C8BCA7", ink="353025", card="F2EADC")
    theme = ["353025", "FFFFFF", "725A21", "F8F5EE", "725A21", "9F5947", "C8BCA7", "F2EADC", "353025", "9F5947"]
    logo = (25.0, 2.0, 3.6, 1.4)
    chapter_num = "壹"

    def frame(self, p, dark=False):
        c = self.C
        outer, inner = (c["card"], c["line"]) if dark else (c["deep"], c["line"])
        p.shape("rect", 1.14, 1.14, 31.58, 16.76, line=outer, lw=1.5)
        p.shape("rect", 1.57, 1.57, 30.72, 15.9, line=inner, lw=0.75)
        if dark:
            return
        for (x, y, rot) in [(1.57, 1.57, 0), (28.99, 1.57, 90), (28.99, 14.17, 180), (1.57, 14.17, 270)]:
            p.shape("arc", x, y, 3.3, 3.3, line=c["deep"], lw=1.25, rot=rot)
            p.shape("arc", x + 0.64, y + 0.64, 2.03, 2.03, line=c["line"], lw=1.0, rot=rot)
        for (x, y) in [(1.35, 1.35), (32.06, 1.35), (32.06, 17.25), (1.35, 17.25)]:
            p.shape("ellipse", x, y, 0.46, 0.46, fill=c["accent"])

    def divider(self, p, y, cx=16.93):
        c = self.C
        p.rect(cx - 6.35, y + 0.29, 5.71, 0.03, c["deep"])
        p.rect(cx + 0.64, y + 0.29, 5.71, 0.03, c["deep"])
        p.shape("diamond", cx - 0.3, y, 0.61, 0.61, fill=c["card"], line=c["deep"], lw=1)
        p.shape("ellipse", cx - 0.1, y + 0.2, 0.2, 0.2, fill=c["accent"])

    def footer(self, p, dark=False):
        c = self.C
        col = c["line"] if dark else c["accent"]
        p.ph("页脚", "ftr", IDX["ftr"], 9.93, 16.6, 14, 0.6, "", 9, col, algn="ctr", anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 25.0, 16.6, 3.6, 0.6, "", 9, col, algn="r", anchor="ctr")

    def head(self, p):
        p.ph("标题", "title", 0, 3.81, 2.2, 26.25, 1.8, "正文页标题（20 字以内）", 28, self.C["ink"], bold=True, algn="ctr", anchor="ctr")
        self.divider(p, 4.4)

    def cover(self, p):
        c = self.C
        self.frame(p)
        p.ph("Logo", "pic", IDX["logo"], 14.43, 1.9, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["accent"])
        p.ph("眉题", "body", IDX["eyebrow"], 3.81, 4.3, 26.25, 0.8, "眉题（建议 20 字以内）", 12, c["deep"], algn="ctr")
        p.ph("主标题", "title", 0, 3.81, 5.4, 26.25, 3.8, "主标题（建议 16 字以内，最多 2 行）", 40, c["ink"], bold=True, algn="ctr", anchor="ctr")
        self.divider(p, 9.8)
        p.ph("副标题", "subTitle", IDX["subtitle"], 3.81, 10.9, 26.25, 1.4, "副标题或一句话摘要（建议 30 字以内）", 16, c["deep"], algn="ctr")
        p.ph("署名 / 机构", "body", IDX["byline"], 3.81, 13.6, 12.62, 0.8, "署名 / 机构（20 字以内）", 11, c["ink"], algn="r")
        p.shape("ellipse", 16.83, 13.9, 0.2, 0.2, fill=c["accent"])
        p.ph("日期", "body", IDX["date"], 17.44, 13.6, 12.62, 0.8, "日期（12 字以内）", 11, c["ink"])
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.frame(p)
        self.footer(p)
        p.ph("目录标题", "title", 0, 3.81, 2.2, 26.25, 1.8, "目录标题（8 字以内）", 28, c["ink"], bold=True, algn="ctr", anchor="ctr")
        self.divider(p, 4.4)
        w, gap = 5.4, 1.2
        x0 = (33.867 - (4 * w + 3 * gap)) / 2
        for i, idx in enumerate(IDX["toc"]):
            x = x0 + i * (w + gap)
            p.shape("round2SameRect", x, 5.8, w, 9.8, fill=c["card"], line=c["line"], lw=1, adj={"adj1": 50000, "adj2": 0})
            p.shape("ellipse", x + w / 2 - 0.8, 7.2, 1.6, 1.6, line=c["accent"], lw=1,
                    text="壹贰叁肆"[i], sz=14, color=c["accent"], bold=True)
            p.ph(f"目录条目 {i + 1}", "body", idx, x + 0.3, 9.4, w - 0.6, 5.6,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 18, c["ink"], bold=True, algn="ctr",
                 lvl2=(11, c["accent"]))
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.frame(p, dark=True)
        self.footer(p, dark=True)
        p.shape("ellipse", 14.43, 3.0, 5.0, 5.0, line=c["card"], lw=1.5)
        p.shape("ellipse", 14.73, 3.3, 4.4, 4.4, line=c["line"], lw=0.75)
        p.ph("章节号", "body", IDX["num"], 14.43, 3.0, 5.0, 5.0, "壹", 54, c["card"], bold=True, algn="ctr", anchor="ctr", autofit=False)
        p.ph("章节标题", "title", 0, 3.81, 9.4, 26.25, 2.0, "章节标题（14 字以内）", 32, c["card"], bold=True, algn="ctr", anchor="ctr")
        p.ph("导语", "body", IDX["lead"], 3.81, 11.8, 26.25, 1.0, "一句导语（30 字以内）", 13, c["line"], algn="ctr")
        return c["deep"], False

    def body(self, p):
        c = self.C
        self.frame(p)
        self.footer(p)
        self.head(p)
        p.ph("正文", "body", IDX["body"], 6.0, 5.8, 21.87, 9.8, "正文（建议 180 字以内，最多 3 段）",
             15, c["ink"], lnspc=170)
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.frame(p)
        self.footer(p)
        self.head(p)
        p.ph("正文", "body", IDX["body"], 4.0, 5.8, 15.6, 9.8, "正文（建议 120 字以内）", 15, c["ink"], lnspc=170)
        p.rect(20.6, 6.0, 0.03, 8.0, c["deep"])
        p.ph("引文", "body", IDX["quote"], 21.6, 6.2, 8.4, 6.0, "“引文或金句（40 字以内）”", 20, c["deep"], bold=True, lnspc=150)
        p.ph("出处 / 备注", "body", IDX["note"], 21.6, 13.0, 8.4, 0.8, "出处或备注（20 字以内）", 10, c["accent"])
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.frame(p)
        p.ph("Logo", "pic", IDX["logo"], 14.43, 2.0, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["accent"])
        p.ph("结束语", "title", 0, 3.81, 5.2, 26.25, 3.0, "结束语（8 字以内）", 44, c["ink"], bold=True, algn="ctr", anchor="ctr")
        self.divider(p, 8.9)
        p.ph("补充", "body", IDX["endsub"], 3.81, 9.9, 26.25, 1.2, "一句收尾的话（30 字以内）", 15, c["deep"], algn="ctr")
        p.ph("联系方式", "body", IDX["contact"], 3.81, 13.2, 26.25, 0.8, "联系方式 / 网址（30 字以内）", 11, c["accent"], algn="ctr")
        return c["bg"], True


LAYOUTS = [("封面", "cover"), ("目录", "toc"), ("章节页", "chapter"), ("正文", "body"),
           ("正文 + 引文", "quote"), ("结尾页", "end")]

# 示例页：每个占位符填一段写好的提示语；顺序即出现动画的顺序
SAMPLES = {
    "cover": [(IDX["eyebrow"], ["眉题，例如：年度工作汇报"]),
              (0, ["主标题写在这里", "建议 16 字以内"]),
              (IDX["subtitle"], ["副标题或一句话摘要，建议 30 字以内"]),
              (IDX["byline"], ["署名 / 机构"]), (IDX["date"], ["2026 年 11 月"])],
    "toc": [(0, ["本期内容"])] + [(idx, [(t, 0), ("一句话说明这一部分，16 字以内", 1)])
                                  for idx, t in zip(IDX["toc"], ["第一部分", "第二部分", "第三部分", "第四部分"])],
    "chapter": [(IDX["num"], ["{num}"]), (0, ["章节标题，14 字以内"]), (IDX["lead"], ["一句导语，说明这一章要讲什么。"])],
    "body": [(0, ["正文页标题，20 字以内"]),
             (IDX["body"], ["正文第一段：先写结论，再写依据。每页建议不超过 180 字、最多 3 段，字太多就拆成两页。",
                            "正文第二段：用具体的数字和例子说话，比形容词更有说服力。",
                            "正文第三段：写下一步或这一页留给听众的问题。"])],
    "quote": [(0, ["正文页标题，20 字以内"]),
              (IDX["body"], ["正文第一段：这一版式适合「观点 + 金句」。左侧写论述，建议 120 字以内。",
                             "正文第二段：右侧的引文会最后出现，留给讲者停顿。"]),
              (IDX["quote"], ["“引文或金句放在这里，40 字以内。”"]),
              (IDX["note"], ["出处或备注，20 字以内"])],
    "end": [(0, ["谢谢聆听"]), (IDX["endsub"], ["一句收尾的话，30 字以内"]),
            (IDX["contact"], ["联系方式 / 网址，30 字以内"])],
}


def make_logo_png(path, color):
    w, h = 875, 350
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rgb = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    step = 28
    for x in range(10, w - 10, step):  # 虚线边框
        d.line([(x, 10), (min(x + 16, w - 10), 10)], fill=rgb + (255,), width=5)
        d.line([(x, h - 10), (min(x + 16, w - 10), h - 10)], fill=rgb + (255,), width=5)
    for y in range(10, h - 10, step):
        d.line([(10, y), (10, min(y + 16, h - 10))], fill=rgb + (255,), width=5)
        d.line([(w - 10, y), (w - 10, min(y + 16, h - 10))], fill=rgb + (255,), width=5)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
    except OSError:
        font = ImageFont.load_default()
    tw, th = d.textbbox((0, 0), "YOUR LOGO", font=font)[2:]
    d.text(((w - tw) / 2, (h - th) / 2 - 10), "YOUR LOGO", fill=rgb + (255,), font=font)
    im.save(path)


def set_bg(cSld, color):
    for old in cSld.findall("p:bg", NSMAP):
        cSld.remove(old)
    cSld.insert(0, parse(f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
                         f'<a:effectLst/></p:bgPr></p:bg>'))


def clear_tree(spTree):
    for el in list(spTree):
        if etree.QName(el).localname not in ("nvGrpSpPr", "grpSpPr", "extLst"):
            spTree.remove(el)


def fill_tree(spTree, part):
    for x in part.xml:
        spTree.append(parse(x))


def patch_theme(master, style):
    theme_part = master.part.part_related_by(RT.THEME)
    root = etree.fromstring(theme_part.blob)
    a = NSMAP["a"]
    names = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6"]
    cs = root.find(f".//{{{a}}}clrScheme")
    cs.set("name", "Garman " + style.title)
    for n, v in zip(names, style.theme):
        el = cs.find(f"{{{a}}}{n}")
        for ch in list(el):
            el.remove(ch)
        etree.SubElement(el, f"{{{a}}}srgbClr", val=v)
    for tag in ("majorFont", "minorFont"):
        fnt = root.find(f".//{{{a}}}{tag}")
        fnt.find(f"{{{a}}}latin").set("typeface", FONT)
        fnt.find(f"{{{a}}}ea").set("typeface", FONT)
    root.find(f".//{{{a}}}fontScheme").set("name", FONT)
    theme_part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def master_txstyles(style):
    ink = style.theme[0]
    def lvl(n, sz):
        return (f'<a:lvl{n}pPr marL="0" indent="0" algn="l"><a:lnSpc><a:spcPct val="130000"/></a:lnSpc>'
                f'<a:spcBef><a:spcPts val="600"/></a:spcBef><a:buNone/><a:defRPr sz="{sz}">'
                f'<a:solidFill><a:srgbClr val="{ink}"/></a:solidFill><a:latin typeface="+mn-lt"/>'
                f'<a:ea typeface="+mn-ea"/></a:defRPr></a:lvl{n}pPr>')
    body = "".join(lvl(i, s) for i, s in zip(range(1, 10), [1600, 1400, 1200, 1200, 1200, 1200, 1200, 1200, 1200]))
    return parse(
        f'<p:txStyles><p:titleStyle><a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
        f'<a:buNone/><a:defRPr sz="3200" b="1"><a:solidFill><a:srgbClr val="{ink}"/></a:solidFill>'
        f'<a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/></a:defRPr></a:lvl1pPr></p:titleStyle>'
        f'<p:bodyStyle>{body}</p:bodyStyle><p:otherStyle><a:lvl1pPr><a:defRPr sz="1200">'
        f'<a:solidFill><a:srgbClr val="{ink}"/></a:solidFill><a:latin typeface="+mn-lt"/>'
        f'<a:ea typeface="+mn-ea"/></a:defRPr></a:lvl1pPr></p:otherStyle></p:txStyles>')


def fade_timing(spids, dur=500):
    """依次出现：进入幻灯片后自动开始，每个元素在上一个之后淡入（透明度）。"""
    n = [3]

    def nid():
        n[0] += 1
        return n[0]

    items, delay = [], 0
    for i, sp in enumerate(spids):
        a, b, c, d = nid(), nid(), nid(), nid()
        items.append(
            f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{b}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" '
            f'nodeType="{"afterEffect" if i else "withEffect"}"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst><p:set><p:cBhvr><p:cTn id="{c}" dur="1" fill="hold"><p:stCondLst>'
            f'<p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl>'
            f'<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set><p:animEffect transition="in" filter="fade">'
            f'<p:cBhvr><p:cTn id="{d}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr>'
            f'</p:animEffect></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        delay += dur
    bld = "".join(f'<p:bldP spid="{sp}" grpId="0"/>' for sp in spids)
    return parse(
        '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
        '<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
        '<p:childTnLst><p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
        '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
        + "".join(items) +
        '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0">'
        '<p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0">'
        '<p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par>'
        f'</p:tnLst><p:bldLst>{bld}</p:bldLst></p:timing>')


def build(style, outdir, tmpdir):
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    master = prs.slide_master
    patch_theme(master, style)

    # 删掉不用的默认版式，保留 6 个改造
    layouts = list(prs.slide_layouts)
    for lo in layouts[6:]:
        prs.slide_layouts.remove(lo)
    layouts = list(prs.slide_layouts)

    # 母版：背景、文字样式、logo 示意图、页脚与页码
    mel = master._element
    set_bg(mel.cSld, style.C["bg"])
    mel.replace(mel.find("p:txStyles", NSMAP), master_txstyles(style))
    logo_png = os.path.join(tmpdir, f"logo-{style.key}.png")
    make_logo_png(logo_png, style.theme[6] if style.key != "neubrutalism" else "121212")
    _, rid = master.part.get_or_add_image_part(logo_png)
    mp = Part()
    mp.ph("标题", "title", 0, 2.0, 3.0, 27, 1.8, "单击此处编辑母版标题样式", 28, style.theme[0], bold=True)
    mp.ph("正文", "body", 1, 2.0, 5.6, 29.87, 11.4, "单击此处编辑母版文本样式", 16, style.theme[0])
    style.footer(mp)
    mp.xml = [x for x in mp.xml if "装饰" not in x]  # 母版只留占位符，装饰线放在版式里
    mp.pic(rid, *style.logo, "Logo（视图 > 幻灯片母版中右键「更改图片」）")
    st = mel.cSld.spTree
    clear_tree(st)
    fill_tree(st, mp)

    for lo, (name, fn) in zip(layouts, LAYOUTS):
        el = lo._element
        el.cSld.set("name", name)
        for k in ("type", "preserve"):
            if k in el.attrib:
                del el.attrib[k]
        p = Part()
        bg, hide_master = getattr(style, fn)(p)
        set_bg(el.cSld, bg)
        if hide_master:
            el.set("showMasterSp", "0")
        clear_tree(el.cSld.spTree)
        fill_tree(el.cSld.spTree, p)

    # 示例页
    for lo, (name, fn) in zip(layouts, LAYOUTS):
        slide = prs.slides.add_slide(lo)
        sp_by_idx = {ph.placeholder_format.idx: ph for ph in slide.placeholders}
        order = []
        if IDX["logo"] in sp_by_idx:
            sp_by_idx[IDX["logo"]].insert_picture(logo_png)
            sp_by_idx = {ph.placeholder_format.idx: ph for ph in slide.placeholders}
        for idx, lines in SAMPLES[fn]:
            ph = sp_by_idx[idx]
            tf = ph.text_frame
            for i, ln in enumerate(lines):
                text, lvl = ln if isinstance(ln, tuple) else (ln, 0)
                text = text.replace("{num}", style.chapter_num)
                para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                para.text = text
                para.level = lvl
            order.append(ph.shape_id)
        # 页脚与页码：python-pptx 不会自动复制，手动从版式克隆
        for lph in lo.placeholders:
            if lph.placeholder_format.idx in (IDX["ftr"], IDX["sldnum"]):
                new = copy.deepcopy(lph._element)
                new.find(".//p:cNvPr", NSMAP).set("id", str(900 + lph.placeholder_format.idx))
                spPr = new.find("p:spPr", NSMAP)
                for ch in list(spPr):
                    spPr.remove(ch)
                if lph.placeholder_format.idx == IDX["ftr"]:
                    tb = new.find("p:txBody", NSMAP)
                    for para in tb.findall("a:p", NSMAP):
                        tb.remove(para)
                    tb.append(parse(f'<a:p><a:r><a:rPr lang="zh-CN"/><a:t>{FOOTER_TEXT}</a:t></a:r></a:p>'))
                lst = new.find("p:txBody/a:lstStyle", NSMAP)
                for ch in list(lst):
                    lst.remove(ch)
                slide.shapes._spTree.append(new)
        slide._element.append(fade_timing(order))

    cp = prs.core_properties
    cp.title = f"GarmanPPT 母版 · {style.title}"
    cp.author = "赵盾 AI 学习工作室"
    cp.subject = "GarmanPPT 免费母版"
    cp.keywords = "GarmanPPT; 母版; AIGC"
    cp.comments = f"AI 辅助生成：GarmanPPT {VERSION}。本母版由 AI 辅助设计与生成，经人工审核。"
    cp.last_modified_by = "GarmanPPT"
    cp.revision = 1

    out = os.path.join(outdir, f"{style.file}-{VERSION}.pptx")
    prs.save(out)
    add_custom_props(out, {"AIGC": "GarmanPPT", "GarmanStyle": style.key, "GarmanVersion": VERSION})
    return out


def add_custom_props(path, props):
    """隐式标注：写入 docProps/custom.xml 自定义属性。"""
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(b"</Types>", b'<Override PartName="/docProps/custom.xml" ContentType='
                                    b'"application/vnd.openxmlformats-officedocument.custom-properties+xml"/></Types>')
            elif item.filename == "_rels/.rels":
                data = data.replace(b"</Relationships>", b'<Relationship Id="rIdCustom1" Type="http://schemas.'
                                    b'openxmlformats.org/officeDocument/2006/relationships/custom-properties" '
                                    b'Target="docProps/custom.xml"/></Relationships>')
            zout.writestr(item, data)
        body = "".join(
            f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{i + 2}" name="{k}">'
            f'<vt:lpwstr>{esc(v)}</vt:lpwstr></property>' for i, (k, v) in enumerate(props.items()))
        zout.writestr("docProps/custom.xml",
                      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Properties xmlns="http://schemas.'
                      'openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.'
                      f'openxmlformats.org/officeDocument/2006/docPropsVTypes">{body}</Properties>')
    os.replace(tmp, path)


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    tmpdir = os.path.join(outdir, ".tmp")
    os.makedirs(tmpdir, exist_ok=True)
    for s in (Editorial(), Brutal(), Nouveau()):
        print(build(s, outdir, tmpdir))
