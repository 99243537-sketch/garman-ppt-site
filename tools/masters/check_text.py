"""发布前敏感词自检：扫描 .pptx 内全部文字（幻灯片、版式、母版、备注、文件属性）和传入的其他文本文件。
用法：python3 check_text.py 词表.txt 文件1 [文件2 ...]；有命中时退出码为 1。"""
import re, sys, zipfile
words = [w.strip() for w in open(sys.argv[1], encoding="utf-8") if w.strip() and not w.startswith("#")]
pats = {"手机号": re.compile(r"1[3-9]\d{9}"), "邮箱": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")}
hits = 0
for f in sys.argv[2:]:
    parts = {}
    if f.endswith(".pptx"):
        with zipfile.ZipFile(f) as z:
            for n in z.namelist():
                if n.endswith(".xml"):
                    x = z.read(n).decode("utf-8", "ignore")
                    parts[n] = " ".join(re.findall(r"<a:t>([^<]*)</a:t>", x)) + " " + " ".join(
                        re.findall(r'(?:descr|name)="([^"]*)"', x)) + (re.sub(r"<[^>]+>", " ", x) if n.startswith("docProps/") else "")
    else:
        parts[f] = open(f, encoding="utf-8").read()
    for n, t in parts.items():
        for w in words:
            if w in t:
                hits += 1; print(f"{f} | {n} | 命中词：{w}")
        for k, p in pats.items():
            for m in p.findall(t):
                hits += 1; print(f"{f} | {n} | {k}：{m}")
print(f"检查完成，命中 {hits} 处")
sys.exit(1 if hits else 0)
