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

### Add or update a player profile
Each player in `_src/data/players.json` gets a shareable profile page at `/stories/<id>/` with tabs for Story, Stats, Career, Honours & info, and Video, plus Share and Save as PDF. Copy an existing player as a template, then rebuild.
- `seasons`: one row per season; leave a value as `""` if it isn't confirmed. Cells stay empty, and a column that is empty for every season is hidden.
- `sources`: links to official roster or stat pages.
- `photos`: first one is the profile card; names refer to files in `assets/img/`.
- `short_quote` and `card_line`: the quote and path line shown on the player cards.
- The first player in the list is the featured story on the Player Stories page.
- Renamed a player URL? Add the old path to `REDIRECTS` in `_build.py` so old links still work.

### Add a photo
Put the original in `images/`, add a line to the `PHOTOS` list in `_tools/optimize_images.py`, run `python3 _tools/optimize_images.py`, then rebuild.

### Add a resource
Add an item to the right category in `_src/data/resources.json`. Use `"status": "partner"` only for verified, formal partners who agreed to be listed; otherwise use `"public"`.

## Forms
All forms post to Formspree (`https://formspree.io/f/mlgavqpz`). Submissions arrive at the email connected to that Formspree form. To change the endpoint, edit `FORMSPREE` in `_build.py` and rebuild.

## Donations
Donorbox: `https://donorbox.org/the-91st-foundation` (set in `_build.py` as `DONATE_URL`).
