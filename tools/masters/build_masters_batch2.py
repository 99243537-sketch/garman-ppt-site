"""第二批 4 套 GarmanPPT 母版：瑞士国际主义、日式极简、便当盒布局、Metro 磁贴。

复用母版 v1 的 build_masters.py（占位符 idx 约定、示例页、逐个淡入动画、隐式标注都一致），
这里只新增 4 个风格类。配色与五色角色取自兼容矩阵对应格。
用法：python3 build_masters_batch2.py <输出目录>（build_masters.py 需在同一目录）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_masters import IDX, build  # noqa: E402


class Swiss:
    """瑞士国际主义 × 红嘴蓝鹊：白底、齐左、细线网格，红色只做一块方块和编号（≤10%）。"""
    key, file = "swiss-style", "garman-swiss-blue-magpie"
    title = "瑞士国际主义 × 红嘴蓝鹊"
    C = dict(bg="FFFFFF", ink="2C303B", muted="5D6372", line="CDD1DA", accent="B1483E", white="FFFFFF")
    theme = ["2C303B", "FFFFFF", "1C2746", "F2F5FC", "93AEF8", "B1483E", "5D6372", "CDD1DA", "4A5C8B", "E5EBFA"]
    logo = (29.4, 0.75, 3.6, 1.4)
    chapter_num = "01"
    X0, COL = 1.69, 2.54  # 5% 边距；12 栏，每栏约 2.54 cm

    def footer(self, p, dark=False):
        c = self.C
        col = c["line"] if dark else c["muted"]
        p.ph("页脚", "ftr", IDX["ftr"], self.X0, 17.9, 16, 0.6, "", 9, col, anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 29.87, 17.9, 2.3, 0.6, "", 9, col, algn="r", anchor="ctr")
        p.rect(self.X0, 17.6, 30.49, 0.02, c["line"] if not dark else c["muted"])

    def cover(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 26.0, 1.5, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["muted"])
        p.rect(self.X0, 1.69, 1.6, 1.6, c["accent"])
        p.ph("眉题", "body", IDX["eyebrow"], self.X0, 4.4, 20, 0.8, "眉题（建议 20 字以内）", 12, c["ink"], bold=True)
        p.ph("主标题", "title", 0, self.X0, 5.6, 28, 7.2, "主标题（建议 16 字以内，最多 2 行）", 60, c["ink"], bold=True, anchor="t", lnspc=100)
        p.rect(self.X0, 13.6, 30.49, 0.02, c["ink"])
        p.ph("署名 / 机构", "body", IDX["byline"], self.X0, 14.0, 9.5, 0.7, "署名 / 机构（20 字以内）", 11, c["ink"], bold=True)
        p.ph("日期", "body", IDX["date"], self.X0, 14.8, 9.5, 0.7, "日期（12 字以内）", 11, c["muted"])
        p.ph("副标题", "subTitle", IDX["subtitle"], self.X0 + 4 * self.COL * 1.0 + 1.0, 14.0, 19.0, 2.4, "副标题或一句话摘要（建议 30 字以内）", 14, c["muted"], lnspc=140)
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.footer(p)
        p.ph("目录标题", "title", 0, self.X0, 1.6, 9.0, 3.0, "目录标题（8 字以内）", 32, c["ink"], bold=True, anchor="t")
        for i, idx in enumerate(IDX["toc"]):
            y = 2.2 + i * 3.7
            p.rect(12.0, y - 0.4, 20.18, 0.02, c["line"])
            p.shape("rect", 12.0, y, 2.6, 1.4, text=f"0{i + 1}", sz=24, color=c["accent"], bold=True, algn="l", anchor="t")
            p.ph(f"目录条目 {i + 1}", "body", idx, 15.2, y, 16.9, 2.6,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 20, c["ink"], bold=True, lvl2=(12, c["muted"]))
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.footer(p, dark=True)
        p.rect(self.X0, 1.69, 1.6, 1.6, c["accent"])
        p.ph("章节号", "body", IDX["num"], self.X0, 3.4, 14, 7.2, "01", 160, c["white"], bold=True, anchor="b", autofit=False)
        p.ph("章节标题", "title", 0, 17.0, 6.4, 15.2, 2.6, "章节标题（14 字以内）", 32, c["white"], bold=True, anchor="b")
        p.ph("导语", "body", IDX["lead"], 17.0, 9.4, 15.2, 2.0, "一句导语（30 字以内）", 14, c["line"], lnspc=140)
        return c["ink"], False

    def body(self, p):
        c = self.C
        self.footer(p)
        p.ph("标题", "title", 0, self.X0, 1.6, 9.0, 6.0, "正文页标题（20 字以内）", 28, c["ink"], bold=True, anchor="t", lnspc=110)
        p.rect(self.X0, 8.2, 1.0, 0.12, c["accent"])
        p.ph("正文", "body", IDX["body"], 12.0, 1.8, 20.18, 15.0, "正文（建议 180 字以内，最多 3 段）",
             15, c["ink"], lnspc=165, numcol=2, spccol=1.2)
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.footer(p)
        p.ph("标题", "title", 0, self.X0, 1.6, 9.0, 6.0, "正文页标题（20 字以内）", 28, c["ink"], bold=True, anchor="t", lnspc=110)
        p.ph("正文", "body", IDX["body"], self.X0, 9.0, 9.0, 8.0, "正文（建议 120 字以内）", 13, c["ink"], lnspc=160)
        p.rect(12.0, 1.8, 0.02, 15.0, c["line"])
        p.ph("引文", "body", IDX["quote"], 13.2, 1.8, 19.0, 10.0, "“引文或金句（40 字以内）”", 36, c["ink"], bold=True, lnspc=120)
        p.rect(13.2, 12.6, 1.0, 0.12, c["accent"])
        p.ph("出处 / 备注", "body", IDX["note"], 13.2, 13.1, 19.0, 0.8, "出处或备注（20 字以内）", 11, c["muted"])
        return c["bg"], False

    def end(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 26.0, 1.5, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["muted"])
        p.rect(self.X0, 1.69, 1.6, 1.6, c["accent"])
        p.ph("结束语", "title", 0, self.X0, 4.6, 28, 5.0, "结束语（8 字以内）", 72, c["ink"], bold=True, anchor="b")
        p.rect(self.X0, 13.6, 30.49, 0.02, c["ink"])
        p.ph("补充", "body", IDX["endsub"], self.X0, 14.0, 14, 1.2, "一句收尾的话（30 字以内）", 14, c["ink"])
        p.ph("联系方式", "body", IDX["contact"], 17.0, 14.0, 15.2, 0.8, "联系方式 / 网址（30 字以内）", 11, c["muted"])
        return c["bg"], True


class Japanese:
    """日式极简 × 梅花：大量留白、居左单一焦点、一条细线一个苔绿小点。"""
    key, file = "japanese-minimal", "garman-japanese-minimal-plum-blossom"
    title = "日式极简 × 梅花"
    C = dict(bg="FBF2F5", ink="392C31", muted="705E64", line="D9CDD1", soft="DCB5C3", dot="2E7A56", deep="814A60")
    theme = ["392C31", "FFFFFF", "2F262A", "FBF2F5", "DCB5C3", "2E7A56", "705E64", "D9CDD1", "814A60", "F8E6EC"]
    logo = (28.6, 1.4, 3.6, 1.4)
    chapter_num = "其一"
    X0 = 3.39  # 10% 边距

    def footer(self, p, dark=False):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], self.X0, 17.0, 14, 0.6, "", 8, c["muted"], anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 28.1, 17.0, 2.4, 0.6, "", 8, c["muted"], algn="r", anchor="ctr")

    def dot(self, p, x, y, d=0.5):
        p.shape("ellipse", x, y, d, d, fill=self.C["dot"])

    def cover(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 25.1, 1.4, 5.4, 2.2, "插入 logo（透明 PNG）", 10, c["muted"])
        self.dot(p, self.X0, 5.2, 0.6)
        p.ph("眉题", "body", IDX["eyebrow"], self.X0 + 1.2, 5.05, 20, 0.9, "眉题（建议 20 字以内）", 12, c["muted"], anchor="ctr")
        p.ph("主标题", "title", 0, self.X0, 6.8, 22, 4.4, "主标题（建议 16 字以内，最多 2 行）", 40, c["ink"], bold=False, lnspc=130)
        p.rect(self.X0, 11.8, 4.0, 0.02, c["soft"])
        p.ph("副标题", "subTitle", IDX["subtitle"], self.X0, 12.4, 20, 1.4, "副标题或一句话摘要（建议 30 字以内）", 14, c["muted"], lnspc=150)
        p.ph("署名 / 机构", "body", IDX["byline"], self.X0, 15.4, 12, 0.7, "署名 / 机构（20 字以内）", 10, c["muted"])
        p.ph("日期", "body", IDX["date"], 18.5, 15.4, 12, 0.7, "日期（12 字以内）", 10, c["muted"], algn="r")
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.footer(p)
        p.ph("目录标题", "title", 0, self.X0, 2.6, 14, 1.6, "目录标题（8 字以内）", 26, c["ink"], anchor="ctr")
        p.rect(self.X0, 4.8, 4.0, 0.02, c["soft"])
        for i, idx in enumerate(IDX["toc"]):
            y = 6.0 + i * 2.6
            p.shape("rect", self.X0, y, 1.6, 1.0, text="一二三四"[i], sz=14, color=c["deep"], algn="l", anchor="t")
            p.ph(f"目录条目 {i + 1}", "body", idx, self.X0 + 2.0, y, 20, 2.2,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 16, c["ink"], lvl2=(11, c["muted"]))
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.footer(p)
        p.ph("章节号", "body", IDX["num"], self.X0, 5.0, 12, 4.0, "其一", 66, c["soft"], anchor="b", autofit=False)
        self.dot(p, self.X0, 9.5, 0.5)
        p.ph("章节标题", "title", 0, self.X0, 10.0, 22, 2.0, "章节标题（14 字以内）", 30, c["ink"], anchor="ctr")
        p.ph("导语", "body", IDX["lead"], self.X0, 12.4, 22, 1.0, "一句导语（30 字以内）", 13, c["muted"])
        return c["bg"], False

    def body(self, p):
        c = self.C
        self.footer(p)
        p.ph("标题", "title", 0, self.X0, 2.6, 22, 1.6, "正文页标题（20 字以内）", 24, c["ink"], anchor="ctr")
        p.rect(self.X0, 4.8, 4.0, 0.02, c["soft"])
        p.ph("正文", "body", IDX["body"], self.X0, 6.0, 20.0, 10.0, "正文（建议 180 字以内，最多 3 段）",
             14, c["ink"], lnspc=190)
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.footer(p)
        p.ph("标题", "title", 0, self.X0, 2.6, 22, 1.6, "正文页标题（20 字以内）", 24, c["ink"], anchor="ctr")
        p.rect(self.X0, 4.8, 4.0, 0.02, c["soft"])
        p.ph("正文", "body", IDX["body"], self.X0, 6.0, 13.0, 10.0, "正文（建议 120 字以内）", 13, c["ink"], lnspc=190)
        self.dot(p, 19.4, 6.3, 0.5)
        p.ph("引文", "body", IDX["quote"], 19.4, 7.4, 11.0, 6.0, "“引文或金句（40 字以内）”", 20, c["deep"], lnspc=170)
        p.ph("出处 / 备注", "body", IDX["note"], 19.4, 13.8, 11.0, 0.8, "出处或备注（20 字以内）", 10, c["muted"])
        return c["bg"], False

    def end(self, p):
        c = self.C
        p.ph("Logo", "pic", IDX["logo"], 25.1, 1.4, 5.4, 2.2, "插入 logo（透明 PNG）", 10, c["muted"])
        p.ph("结束语", "title", 0, self.X0, 6.0, 22, 2.6, "结束语（8 字以内）", 40, c["ink"], anchor="b")
        self.dot(p, self.X0, 9.4, 0.6)
        p.ph("补充", "body", IDX["endsub"], self.X0 + 1.2, 9.2, 20, 1.0, "一句收尾的话（30 字以内）", 14, c["muted"], anchor="ctr")
        p.ph("联系方式", "body", IDX["contact"], self.X0, 15.4, 22, 0.7, "联系方式 / 网址（30 字以内）", 10, c["muted"])
        return c["bg"], True


class Bento:
    """便当盒布局 × 乌桕：大小不一的圆角格子，每格讲一件事；杏橙主格、秋空蓝点睛格。"""
    key, file = "bento-grid", "garman-bento-grid-tallow-tree"
    title = "便当盒布局 × 乌桕"
    C = dict(bg="FBF3EF", ink="392E27", muted="6F6056", line="D9CFC8", main="E9A679", soft="F7E8DE",
             blue="1672AB", deep="80512F", white="FFFFFF")
    theme = ["392E27", "FFFFFF", "2E2821", "FBF3EF", "E9A679", "1672AB", "6F6056", "D9CFC8", "80512F", "F7E8DE"]
    logo = (29.4, 0.7, 3.6, 1.4)
    chapter_num = "01"
    G = 0.5  # 格子间距

    def cell(self, p, x, y, w, h, fill, line=None):
        r = int(0.45 / min(w, h) * 100000)  # 约 16 px 圆角，不随格子大小变化
        p.shape("roundRect", x, y, w, h, fill=fill, line=line, lw=0.75, adj={"adj": r})

    def footer(self, p, dark=False):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], 1.69, 18.1, 16, 0.6, "", 9, c["muted"], anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 29.9, 18.1, 2.3, 0.6, "", 9, c["muted"], algn="r", anchor="ctr")

    def head(self, p):
        p.ph("标题", "title", 0, 1.69, 1.0, 26, 1.8, "正文页标题（20 字以内）", 26, self.C["ink"], bold=True, anchor="ctr")

    def cover(self, p):
        c = self.C
        self.cell(p, 1.69, 1.69, 19.0, 15.67, c["white"])
        p.ph("眉题", "body", IDX["eyebrow"], 2.9, 2.9, 16.6, 0.8, "眉题（建议 20 字以内）", 12, c["deep"], bold=True)
        p.ph("主标题", "title", 0, 2.9, 4.4, 16.6, 6.6, "主标题（建议 16 字以内，最多 2 行）", 48, c["ink"], bold=True, anchor="ctr", lnspc=110)
        p.ph("署名 / 机构", "body", IDX["byline"], 2.9, 14.6, 8.0, 0.8, "署名 / 机构（20 字以内）", 11, c["muted"])
        p.ph("日期", "body", IDX["date"], 11.5, 14.6, 8.0, 0.8, "日期（12 字以内）", 11, c["muted"], algn="r")
        self.cell(p, 21.2, 1.69, 10.98, 9.6, c["main"])
        p.ph("副标题", "subTitle", IDX["subtitle"], 22.3, 2.8, 8.8, 7.4, "副标题或一句话摘要（建议 30 字以内）", 18, c["ink"], bold=True, anchor="b", lnspc=130)
        self.cell(p, 21.2, 11.79, 5.24, 5.57, c["blue"])
        self.cell(p, 26.94, 11.79, 5.24, 5.57, c["soft"])
        p.ph("Logo", "pic", IDX["logo"], 27.42, 13.9, 4.3, 1.7, "插入 logo（透明 PNG）", 9, c["muted"])
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.footer(p)
        p.ph("目录标题", "title", 0, 1.69, 1.0, 26, 1.8, "目录标题（8 字以内）", 26, c["ink"], bold=True, anchor="ctr")
        boxes = [(1.69, 3.6, 15.0, 6.8, c["main"]), (17.19, 3.6, 15.0, 6.8, c["white"]),
                 (1.69, 10.9, 15.0, 6.6, c["white"]), (17.19, 10.9, 15.0, 6.6, c["soft"])]
        for i, (idx, (x, y, w, h, f)) in enumerate(zip(IDX["toc"], boxes)):
            self.cell(p, x, y, w, h, f)
            p.shape("rect", x + 0.9, y + 0.8, 3, 1.0, text=f"0{i + 1}", sz=16, color=c["blue"] if i else c["ink"], bold=True, algn="l", anchor="t")
            p.ph(f"目录条目 {i + 1}", "body", idx, x + 0.9, y + 2.6, w - 1.8, h - 3.2,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 20, c["ink"], bold=True, lvl2=(12, c["muted"]))
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.cell(p, 1.69, 2.6, 11.0, 14.9, c["blue"])
        p.ph("章节号", "body", IDX["num"], 2.9, 3.5, 8.6, 6.0, "01", 110, c["white"], bold=True, anchor="t", autofit=False)
        self.cell(p, 13.19, 2.6, 19.0, 9.6, c["white"])
        p.ph("章节标题", "title", 0, 14.4, 3.6, 16.6, 4.6, "章节标题（14 字以内）", 36, c["ink"], bold=True, anchor="b")
        p.ph("导语", "body", IDX["lead"], 14.4, 8.6, 16.6, 2.4, "一句导语（30 字以内）", 14, c["muted"], lnspc=140)
        self.cell(p, 13.19, 12.7, 9.25, 4.8, c["main"])
        self.cell(p, 22.94, 12.7, 9.25, 4.8, c["soft"])
        return c["bg"], False

    def body(self, p):
        c = self.C
        self.footer(p)
        self.head(p)
        self.cell(p, 1.69, 3.6, 20.5, 13.9, c["white"])
        p.ph("正文", "body", IDX["body"], 2.8, 4.6, 18.3, 12.0, "正文（建议 180 字以内，最多 3 段）", 15, c["ink"], lnspc=165)
        self.cell(p, 22.69, 3.6, 9.5, 6.7, c["main"])
        self.cell(p, 22.69, 10.8, 9.5, 6.7, c["soft"])
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.footer(p)
        self.head(p)
        self.cell(p, 1.69, 3.6, 15.0, 13.9, c["white"])
        p.ph("正文", "body", IDX["body"], 2.8, 4.6, 12.8, 12.0, "正文（建议 120 字以内）", 14, c["ink"], lnspc=165)
        self.cell(p, 17.19, 3.6, 15.0, 9.4, c["blue"])
        p.ph("引文", "body", IDX["quote"], 18.3, 4.7, 12.8, 7.2, "“引文或金句（40 字以内）”", 22, c["white"], bold=True, anchor="ctr", lnspc=140)
        self.cell(p, 17.19, 13.5, 15.0, 4.0, c["main"])
        p.ph("出处 / 备注", "body", IDX["note"], 18.3, 14.6, 12.8, 1.8, "出处或备注（20 字以内）", 12, c["ink"], bold=True, anchor="ctr")
        return c["bg"], False

    def end(self, p):
        c = self.C
        self.cell(p, 1.69, 1.69, 20.5, 15.67, c["white"])
        p.ph("结束语", "title", 0, 2.9, 3.0, 18.1, 6.4, "结束语（8 字以内）", 54, c["ink"], bold=True, anchor="b")
        p.ph("补充", "body", IDX["endsub"], 2.9, 10.2, 18.1, 1.4, "一句收尾的话（30 字以内）", 16, c["muted"])
        p.ph("联系方式", "body", IDX["contact"], 2.9, 15.0, 18.1, 0.8, "联系方式 / 网址（30 字以内）", 11, c["muted"])
        self.cell(p, 22.69, 1.69, 9.5, 7.6, c["soft"])
        p.ph("Logo", "pic", IDX["logo"], 24.44, 4.2, 6.0, 2.4, "插入 logo（透明 PNG）", 10, c["muted"])
        self.cell(p, 22.69, 9.79, 9.5, 7.57, c["main"])
        return c["bg"], True


class Metro:
    """Metro 磁贴 × 翠鸟：深底白字，纯色方块磁贴，无圆角、无投影、无线条装饰。"""
    key, file = "metro", "garman-metro-kingfisher"
    title = "Metro 磁贴 × 翠鸟"
    C = dict(bg="001532", ink="FFFFFF", main="55BCFA", deep="2C6485", accent="AC5107", muted="9FB3C4", dark="001532")
    theme = ["001532", "FFFFFF", "0E294A", "EFF6FB", "55BCFA", "AC5107", "9FB3C4", "C9D3D9", "2C6485", "DFEEF8"]
    logo = (29.4, 0.7, 3.6, 1.4)
    chapter_num = "01"

    def tile(self, p, x, y, w, h, fill):
        p.rect(x, y, w, h, fill)

    def footer(self, p, dark=False):
        c = self.C
        p.ph("页脚", "ftr", IDX["ftr"], 1.35, 18.1, 16, 0.6, "", 9, c["muted"], anchor="ctr")
        p.ph("页码", "sldNum", IDX["sldnum"], 30.2, 18.1, 2.3, 0.6, "", 9, c["muted"], algn="r", anchor="ctr")

    def head(self, p):
        p.ph("标题", "title", 0, 1.35, 1.0, 26, 2.0, "正文页标题（20 字以内）", 30, self.C["ink"], bold=False, anchor="ctr")

    def cover(self, p):
        c = self.C
        p.ph("眉题", "body", IDX["eyebrow"], 1.35, 2.0, 18, 0.8, "眉题（建议 20 字以内）", 12, c["main"])
        p.ph("主标题", "title", 0, 1.35, 3.2, 18.5, 7.6, "主标题（建议 16 字以内，最多 2 行）", 54, c["ink"], bold=False, anchor="t", lnspc=105)
        p.ph("副标题", "subTitle", IDX["subtitle"], 1.35, 11.6, 17, 2.0, "副标题或一句话摘要（建议 30 字以内）", 14, c["muted"], lnspc=140)
        p.ph("署名 / 机构", "body", IDX["byline"], 1.35, 15.6, 9, 0.7, "署名 / 机构（20 字以内）", 11, c["ink"])
        p.ph("日期", "body", IDX["date"], 1.35, 16.4, 9, 0.7, "日期（12 字以内）", 11, c["muted"])
        self.tile(p, 20.6, 1.35, 11.9, 7.6, c["main"])
        self.tile(p, 20.6, 9.25, 5.8, 5.8, c["accent"])
        self.tile(p, 26.7, 9.25, 5.8, 5.8, c["deep"])
        p.ph("Logo", "pic", IDX["logo"], 21.2, 15.6, 5.0, 2.0, "插入 logo（透明 PNG）", 9, c["muted"])
        return c["bg"], True

    def toc(self, p):
        c = self.C
        self.footer(p)
        p.ph("目录标题", "title", 0, 1.35, 1.0, 26, 2.0, "目录标题（8 字以内）", 30, c["ink"], anchor="ctr")
        tiles = [(1.35, 3.8, 15.3, 6.6, c["main"], c["dark"]), (16.95, 3.8, 15.3, 6.6, c["deep"], c["ink"]),
                 (1.35, 10.7, 15.3, 6.6, c["accent"], c["ink"]), (16.95, 10.7, 15.3, 6.6, "0E294A", c["ink"])]
        for i, (idx, (x, y, w, h, f, tc)) in enumerate(zip(IDX["toc"], tiles)):
            self.tile(p, x, y, w, h, f)
            p.ph(f"目录条目 {i + 1}", "body", idx, x + 0.8, y + h - 3.4, w - 1.6, 2.8,
                 [("条目标题（6 字）", 0), ("一句说明（16 字以内）", 1)], 22, tc, lvl2=(12, tc))
            p.shape("rect", x + 0.8, y + 0.6, 3, 1.2, text=f"0{i + 1}", sz=20, color=tc, algn="l", anchor="t")
        return c["bg"], False

    def chapter(self, p):
        c = self.C
        self.footer(p)
        self.tile(p, 1.35, 1.35, 12.0, 15.9, c["main"])
        p.ph("章节号", "body", IDX["num"], 2.2, 2.2, 10.3, 7.0, "01", 120, c["dark"], anchor="t", autofit=False)
        p.ph("章节标题", "title", 0, 14.6, 5.4, 17.5, 3.2, "章节标题（14 字以内）", 40, c["ink"], anchor="b")
        p.ph("导语", "body", IDX["lead"], 14.6, 9.2, 17.5, 2.0, "一句导语（30 字以内）", 14, c["muted"], lnspc=140)
        self.tile(p, 14.6, 13.0, 4.2, 4.2, c["accent"])
        return c["bg"], False

    def body(self, p):
        c = self.C
        self.footer(p)
        self.head(p)
        p.ph("正文", "body", IDX["body"], 1.35, 4.0, 20.5, 13.0, "正文（建议 180 字以内，最多 3 段）", 15, c["ink"], lnspc=165)
        self.tile(p, 23.0, 4.0, 9.5, 6.3, c["main"])
        self.tile(p, 23.0, 10.6, 4.6, 4.6, c["accent"])
        self.tile(p, 27.9, 10.6, 4.6, 4.6, c["deep"])
        return c["bg"], False

    def quote(self, p):
        c = self.C
        self.footer(p)
        self.head(p)
        p.ph("正文", "body", IDX["body"], 1.35, 4.0, 14.6, 13.0, "正文（建议 120 字以内）", 14, c["ink"], lnspc=165)
        self.tile(p, 16.95, 4.0, 15.3, 9.6, c["main"])
        p.ph("引文", "body", IDX["quote"], 17.8, 4.8, 13.6, 8.0, "“引文或金句（40 字以内）”", 24, c["dark"], anchor="ctr", lnspc=135)
        self.tile(p, 16.95, 13.9, 15.3, 3.3, c["deep"])
        p.ph("出处 / 备注", "body", IDX["note"], 17.8, 14.6, 13.6, 1.9, "出处或备注（20 字以内）", 12, c["ink"], anchor="ctr")
        return c["bg"], False

    def end(self, p):
        c = self.C
        p.ph("结束语", "title", 0, 1.35, 4.0, 18.5, 4.0, "结束语（8 字以内）", 60, c["ink"], anchor="b")
        p.ph("补充", "body", IDX["endsub"], 1.35, 8.8, 18.5, 1.2, "一句收尾的话（30 字以内）", 16, c["muted"])
        p.ph("联系方式", "body", IDX["contact"], 1.35, 16.0, 18.5, 0.8, "联系方式 / 网址（30 字以内）", 11, c["muted"])
        self.tile(p, 20.6, 1.35, 5.8, 5.8, c["accent"])
        self.tile(p, 26.7, 1.35, 5.8, 5.8, c["deep"])
        self.tile(p, 20.6, 7.45, 11.9, 9.8, c["main"])
        p.ph("Logo", "pic", IDX["logo"], 1.35, 1.35, 5.0, 2.0, "插入 logo（透明 PNG）", 10, c["muted"])
        return c["bg"], True


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    tmpdir = os.path.join(outdir, ".tmp")
    os.makedirs(tmpdir, exist_ok=True)
    for s in (Swiss(), Japanese(), Bento(), Metro()):
        print(build(s, outdir, tmpdir))
