# the91st.org

Website for The 91st Foundation. Static HTML, hosted on GitHub Pages (custom domain in `CNAME`).

## How it's organized

```
_src/                 ← edit these
  layout.html         header, footer, <head> shared by every page
  pages/*.html        one file per page (content only)
  data/players.json   player stories (used on Home and Player Stories)
  data/resources.json resource directory entries
_build.py             builds the pages
_tools/optimize_images.py   makes web-sized copies of photos
assets/               css, js, fonts, optimized images
images/               original photos (kept as-is)
index.html, partners/index.html, …   ← generated, don't edit by hand
```

Folders starting with `_` are not published by GitHub Pages.

## Making changes

1. Edit files in `_src/`.
2. Run `python3 _build.py` (needs Python 3 and `pip install Pillow`).
3. Commit everything, including the generated `.html` files, and push.

### Add or update a player story
Edit `_src/data/players.json` (copy an existing player as a template), then rebuild. Photo names refer to files in `assets/img/`.

### Add a photo
Put the original in `images/`, add a line to the `PHOTOS` list in `_tools/optimize_images.py`, run `python3 _tools/optimize_images.py`, then rebuild.

### Add a resource
Add an item to the right category in `_src/data/resources.json`. Use `"status": "partner"` only for verified, formal partners who agreed to be listed; otherwise use `"public"`.

## Forms
All forms post to Formspree (`https://formspree.io/f/mlgavqpz`). Submissions arrive at the email connected to that Formspree form. To change the endpoint, edit `FORMSPREE` in `_build.py` and rebuild.

## Donations
Donorbox: `https://donorbox.org/the-91st-foundation` (set in `_build.py` as `DONATE_URL`).
