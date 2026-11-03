"""Create web-optimized copies of the photos in /images into /assets/img.

Originals in /images are left untouched (other sites may link to them).
Run from the repo root:  python3 _tools/optimize_images.py
Requires Pillow (pip install Pillow).
"""
import re
from pathlib import Path
from PIL import Image, ImageOps

SRC = Path("images")
OUT = Path("assets/img")
WIDTHS = [480, 960, 1440, 2400]  # plus the source's own width when it is smaller than a step

# name -> (source file, crop box as fractions (left, top, right, bottom) or None)
# Sharif photos are Instagram screenshots; crop removes the mute icon bottom-right.
# Bony photos are cropped closer so he fills the frame.
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
    "alejandro-grad": ("alejandro_graduation.jpg", None),
    "alejandro-portrait": ("alejandro_portrait.jpg", None),
    "alejandro-action": ("alejandro_action.jpg", None),
    "alejandro-training": ("alejandro_training.jpg", None),
    "alejandro-training2": ("alejandro_training2.jpg", None),
    "bony-portrait": ("bony_portrait.jpg", (0.24, 0.30, 1.0, 1.0)),
    "bony-action": ("bony_action.jpg", (0.04, 0.36, 0.70, 1.0)),
    "bony-lindsey": ("bony_lindsey.jpg", None),
    "bony-lindsey-night": ("bony_lindsey_night.jpg", None),
    "embrace": ("players_embrace.jpg", None),
    "helpup": ("gilles_helped_up.jpg", None),
    "alejandro-night": ("alejandro_night.jpg", None),
    "elijah-match": ("elijah_match.jpg", None),
    "elijah-training": ("elijah_training.jpg", None),
    "elijah-mural": ("elijah_mural.jpg", None),
    "sharif-slcc": ("sharif_slcc_headshot.jpg", None),
    # Sharif at Salt Lake CC, 2026 (full-resolution originals from Mo's Drive)
    "sharif-slcc-run": ("sharif_slcc_run.jpg", None),
    "sharif-slcc-run-tall": ("sharif_slcc_run.jpg", (0.225, 0.08, 0.675, 0.92)),
    "sharif-slcc-volley": ("sharif_slcc_volley.jpg", None),
    "sharif-slcc-ball": ("sharif_slcc_ball.jpg", None),
    "sharif-trophies": ("sharif_slcc_trophies.jpg", None),
    # Stock photo: Jeffrey F Lin on Unsplash (Unsplash License, free to use)
    # https://unsplash.com/photos/three-men-standing-on-football-field-pSHpFB5WNUE
    "mentor": ("mentor_unsplash_jeffrey_f_lin.jpg", None),
}

OUT.mkdir(parents=True, exist_ok=True)
for name, (fname, crop) in PHOTOS.items():
    im = ImageOps.exif_transpose(Image.open(SRC / fname)).convert("RGB")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    steps = [w for w in WIDTHS if w < im.width] + [min(im.width, WIDTHS[-1])]
    for old in OUT.glob(f"{name}-*.*"):
        if re.fullmatch(rf"{re.escape(name)}-\d+\.(jpg|webp)", old.name):
            old.unlink()
    for w in sorted(set(steps)):
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(OUT / f"{name}-{w}.webp", "WEBP", quality=82, method=6)
        r.save(OUT / f"{name}-{w}.jpg", "JPEG", quality=84, optimize=True, progressive=True)
    print(name, im.size)

# Social sharing image (1200x630)
base = ImageOps.exif_transpose(Image.open(SRC / "gil_action.jpg")).convert("RGB")
og = ImageOps.fit(base, (1200, 630), Image.LANCZOS, centering=(0.5, 0.35))
og.save(OUT / "og-default.jpg", "JPEG", quality=82, optimize=True)
