"""Create web-optimized copies of the photos in /images into /assets/img.

Originals in /images are left untouched (other sites may link to them).
Run from the repo root:  python3 _tools/optimize_images.py
Requires Pillow (pip install Pillow).
"""
from pathlib import Path
from PIL import Image, ImageOps

SRC = Path("images")
OUT = Path("assets/img")
WIDTHS = [480, 960, 1440]

# name -> (source file, crop box as fractions (left, top, right, bottom) or None)
# Sharif photos are Instagram screenshots; crop removes the mute icon bottom-right.
PHOTOS = {
    "gil-action": ("gil_action.jpg", None),
    "gil-headshot": ("gil_headshot.jpg", None),
    "gil-training": ("gil_training.jpg", None),
    "elijah-action": ("elijah_action.jpg", None),
    "elijah-portrait": ("elijah_portrait.jpg", None),
    "elijah-headshot": ("elijah_headshot.jpg", None),
    "sharif-action": ("Sharif_action.jpg", (0, 0, 0.93, 0.88)),
    "sharif-training": ("Sharif_training.jpg", (0, 0, 0.93, 0.88)),
    "mohamed": ("mohamed.jpg", None),
}

OUT.mkdir(parents=True, exist_ok=True)
for name, (fname, crop) in PHOTOS.items():
    im = ImageOps.exif_transpose(Image.open(SRC / fname)).convert("RGB")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    for w in WIDTHS:
        if w > im.width and w != WIDTHS[0]:
            continue
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(OUT / f"{name}-{w}.webp", "WEBP", quality=78, method=6)
        r.save(OUT / f"{name}-{w}.jpg", "JPEG", quality=80, optimize=True, progressive=True)
    print(name, im.size)

# Social sharing image (1200x630)
base = ImageOps.exif_transpose(Image.open(SRC / "gil_action.jpg")).convert("RGB")
og = ImageOps.fit(base, (1200, 630), Image.LANCZOS, centering=(0.5, 0.35))
og.save(OUT / "og-default.jpg", "JPEG", quality=82, optimize=True)
