"""把 .pptx 渲染成 6 页拼图预览（3×2，约 2017×758 JPG）。
依赖 LibreOffice（soffice）、poppler（pdftoppm）、Pillow。
用法：python3 render_previews.py <输出目录> <pptx…>
"""
import glob
import os
import subprocess
import sys
import tempfile

from PIL import Image

W, H, GAP = 667, 375, 8


def render(pptx, outdir, tmp):
    name = os.path.splitext(os.path.basename(pptx))[0]
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx],
                   check=True, capture_output=True)
    pdf = os.path.join(tmp, name + ".pdf")
    subprocess.run(["pdftoppm", "-r", "50", "-f", "1", "-l", "6", "-png", pdf, os.path.join(tmp, name)], check=True)
    pages = sorted(glob.glob(os.path.join(tmp, name + "-*.png")))[:6]
    sheet = Image.new("RGB", (W * 3 + GAP * 2, H * 2 + GAP), "white")
    for i, f in enumerate(pages):
        im = Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS)
        sheet.paste(im, ((i % 3) * (W + GAP), (i // 3) * (H + GAP)))
        os.remove(f)
    os.remove(pdf)
    out = os.path.join(outdir, name + ".jpg")
    sheet.save(out, quality=82, optimize=True)
    return out


if __name__ == "__main__":
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for f in sys.argv[2:]:
            print(render(f, outdir, tmp))
