#!/usr/bin/env python3
"""Make one JPEG grid of many images so you can eyeball them in a single Read call.
Usage: python3 -I contact_sheet.py <images_dir> <out.jpg>
Uses Pillow if installed, otherwise the bundled sheet.swift on macOS."""
import os, subprocess, sys
src, out = sys.argv[1], sys.argv[2]
try:
    from PIL import Image, ImageDraw
    files = sorted(f for f in os.listdir(src) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    cols, w, h, lab = 6, 260, 190, 22
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, max(1, rows) * (h + lab)), "white"); dr = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(os.path.join(src, f)).convert("RGB"); im.thumbnail((w - 6, h - 6))
        x, y = (i % cols) * w, (i // cols) * (h + lab)
        sheet.paste(im, (x + (w - im.width) // 2, y + (h - im.height) // 2)); dr.text((x + 6, y + h + 4), os.path.splitext(f)[0][:34], fill="black")
    sheet.save(out, "JPEG", quality=70)
except ImportError:
    subprocess.run(["swift", os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheet.swift"), src, out], check=True)
print("wrote", out)
