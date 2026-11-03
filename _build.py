#!/usr/bin/env python3
"""Build the static site from _src/ into the repo root.

    python3 _build.py

- Page sources live in _src/pages/*.html. Each starts with a meta comment:
    <!--meta {"title": "...", "description": "...", "path": "/partners/", "nav": "partners"} -->
- Shared header/footer live in _src/layout.html.
- Player profiles come from _src/data/players.json. Each player gets a
  shareable profile page at /stories/<id>/.
- The resource directory comes from _src/data/resources.json.
- Generated files (index.html, partners/index.html, ...) are committed so
  GitHub Pages can serve them without a build step. Edit _src, then rebuild.
  (Folders starting with "_" are not published by GitHub Pages.)
"""
import html
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_src"
SITE = "https://the91st.org"
DONATE_URL = "https://donorbox.org/the-91st-foundation"
FORMSPREE = "https://formspree.io/f/mlgavqpz"
VERSION = time.strftime("%Y%m%d%H%M")
MISSING = []
REDIRECTS = {"/stories/elijah-tanger/": "/stories/elijah-tenger/"}

NAV = [
    ("stories", "/stories/", "Our Players"),
    ("mission", "/mission/", "Our Mission"),
    ("players", "/players/", "Get Support"),
    ("partners", "/partners/", "Partnerships"),
    ("resources", "/resources/", "Resources"),
    ("involved", "/get-involved/", "Get Involved"),
]

esc = html.escape


# ---------- image helper ----------
def img_widths(name):
    from PIL import Image  # only needed at build time
    out = []
    for f in sorted((ROOT / "assets/img").glob(f"{name}-*.jpg")):
        m = re.fullmatch(rf"{re.escape(name)}-(\d+)\.jpg", f.name)
        if m:
            w, h = Image.open(f).size
            out.append((int(m.group(1)), w, h))
    out.sort()
    return out


def has_img(name):
    return bool(img_widths(name))


def initials(text):
    return "".join(w[0] for w in text.split()[:2]).upper()


def picture(name, alt, sizes="100vw", cls="", eager=False, position=""):
    ws = img_widths(name)
    if not ws:
        # Photo not added yet: show a clean monogram block instead of failing the build.
        MISSING.append(name)
        return f'<div class="ph-missing {cls}" role="img" aria-label="{esc(alt)}"><span>{esc(initials(alt) or "91")}</span></div>'
    webp = ", ".join(f"/assets/img/{name}-{tag}.webp {w}w" for tag, w, _ in ws)
    jpg = ", ".join(f"/assets/img/{name}-{tag}.jpg {w}w" for tag, w, _ in ws)
    tag, w, h = ws[-1]
    style = f' style="object-position:{position}"' if position else ""
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (
        f'<picture class="{cls}"><source type="image/webp" srcset="{webp}" sizes="{sizes}">'
        f'<img src="/assets/img/{name}-{tag}.jpg" srcset="{jpg}" sizes="{sizes}" width="{w}" height="{h}" '
        f'alt="{esc(alt)}" {load} decoding="async"{style}></picture>'
    )


def picture_directive(m):
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
    name = attrs["name"]
    if attrs.get("fallback") and not has_img(name):
        name = attrs["fallback"]
    return picture(name, attrs.get("alt", ""), attrs.get("sizes", "100vw"), attrs.get("class", ""),
                   attrs.get("eager") == "true", attrs.get("position", ""))


# ---------- data ----------
PLAYERS = json.loads((SRC / "data/players.json").read_text())
RESOURCES = json.loads((SRC / "data/resources.json").read_text())
ARROW = '<span class="arrow" aria-hidden="true">&rarr;</span>'


def photo_alt(p, name):
    if name in p["photos"]:
        return p["alts"][p["photos"].index(name)]
    if name in p.get("photos_extra_alts", {}):
        return p["photos_extra_alts"][name]
    return p.get("photos_card_alt", p["name"])


def photo_pos(p, name):
    return p.get("pos", {}).get(name, "")


def last_name(p):
    return p["name"][len(p["first"]):].strip()


def now_html(p, cls="status"):
    if not p.get("now") or p.get("now_label") == "Latest":
        return ""
    return f'<p class="{cls}"><span class="dot" aria-hidden="true"></span><b>{esc(p.get("now_label", "Now"))}:</b>&nbsp;{esc(p["now"])}</p>'


def vcard(p, sizes="(min-width: 1000px) 240px, 72vw"):
    """Tall player card: big name, position, short headline, current status."""
    return f'''<a class="vcard tilt" href="/stories/{p["id"]}/" data-search="{search_text(p)}">
  <span class="vcard-photo">{picture(p["card_photo"], photo_alt(p, p["card_photo"]), sizes, position=photo_pos(p, p["card_photo"]))}</span>
  <span class="vcard-cap">
    <span class="pc-tag">{esc(p.get("pos_short", p["position"]))}</span>
    <span class="vcard-name"><span>{esc(p["first"])}</span>{esc(last_name(p))}</span>
    <span class="vcard-line">{esc(p.get("tagline", ""))}</span>
    {now_html(p, "vcard-now").replace("<p ", "<span ").replace("</p>", "</span>")}
  </span>
  <span class="pcard-glare" aria-hidden="true"></span>
</a>'''


def lineup(label="Players"):
    cards = "\n".join(vcard(p) for p in PLAYERS)
    return f'''<div class="rail-wrap">
  <div class="rail lineup" tabindex="0" aria-label="{esc(label)}, scroll sideways">{cards}</div>
  <div class="rail-ctrl">
    <button class="rail-btn" type="button" data-dir="-1" aria-label="Previous players">&larr;</button>
    <button class="rail-btn" type="button" data-dir="1" aria-label="Next players">&rarr;</button>
  </div>
</div>'''


def players_rail():
    return lineup("Featured players")


def stage_bg(photo, sharp=False):
    """Blurred, green-shaded copy of the photo behind the hero. High-resolution photos can stay sharp."""
    return (f'<div class="stage-bg{" stage-bg--sharp" if sharp else ""}" aria-hidden="true">'
            f'{picture(photo, "", "100vw" if sharp else "480px")}</div>')


def featured_story():
    n = len(PLAYERS)
    slides, dots = [], []
    for i, p in enumerate(PLAYERS):
        photo = p.get("feature_photo", p["card_photo"])
        vid = (f'<a class="btn btn--outline-light" href="/stories/{p["id"]}/#video">&#9654; Watch the interview</a>'
               if p.get("interview") else "")
        hidden = "" if i == 0 else ' aria-hidden="true"'
        count = f"{i + 1:02d} / {n:02d}"
        slides.append(f'''<div class="feat-slide stage{" is-active" if i == 0 else ""}" role="group" aria-roledescription="slide" aria-label="{i + 1} of {n}: {esc(p["name"])}"{hidden}>
  {stage_bg(p.get("hero_bg", photo), sharp=bool(p.get("hero_bg")))}
  <div class="wrap stage-grid">
    <div class="stage-copy">
      <p class="eyebrow">Featured player <span class="feat-count">{count}</span></p>
      <h2 class="feat-name"><span>{esc(p["first"])}</span>{esc(last_name(p))}</h2>
      <p class="feat-meta">{esc(p["position"])} · {esc(p["origin"])}</p>
      <p class="feat-tagline">{esc(p.get("tagline", ""))}</p>
      <p class="serif-quote">&ldquo;{esc(p["short_quote"])}&rdquo;</p>
      {now_html(p)}
      <div class="btn-row"><a class="btn" href="/stories/{p["id"]}/">Meet {esc(p["first"])} {ARROW}</a>{vid}</div>
    </div>
    <figure class="stage-photo tilt" data-tilt-max="5">{picture(photo, photo_alt(p, photo), "(min-width: 900px) 460px, 100vw", eager=(i == 0), position=photo_pos(p, photo))}<span class="pcard-glare" aria-hidden="true"></span></figure>
  </div>
</div>''')
        cur = "true" if i == 0 else "false"
        dots.append(f'<button type="button" class="feat-dot" aria-label="Show {esc(p["name"])}" aria-current="{cur}"><span>{esc(p["first"])}</span></button>')
    return f'''<section class="feature" data-feature aria-roledescription="carousel" aria-label="Featured players">
  <h1 class="visually-hidden">Our Players</h1>
  <div class="feat-slides">{"".join(slides)}</div>
  <div class="feat-ctrl"><div class="wrap feat-ctrl-in">
    <div class="feat-dots">{"".join(dots)}</div>
    <div class="feat-btns">
      <button type="button" class="feat-btn" data-feat="-1" aria-label="Previous player">&larr;</button>
      <button type="button" class="feat-btn feat-pause" aria-pressed="false" aria-label="Pause rotation"><span aria-hidden="true">II</span></button>
      <button type="button" class="feat-btn" data-feat="1" aria-label="Next player">&rarr;</button>
    </div>
  </div></div>
</section>'''


def roster():
    return lineup("All players")


def search_text(p):
    bits = [p["name"], p["position"], p.get("pos_short", ""), p["origin"], p.get("now", ""), p.get("tagline", "")]
    bits += [c["club"] + " " + c["level"] for c in p.get("career", [])] + [v for _, v in p.get("key", [])]
    return esc(" ".join(bits).lower())


def player_finder():
    items = "".join(
        f'<li data-search="{search_text(p)}"><a href="/stories/{p["id"]}/">'
        f'<span class="fr-thumb">{picture(p["card_photo"], "", "56px", position=photo_pos(p, p["card_photo"]))}</span>'
        f'<span class="fr-txt"><b>{esc(p["name"])}</b><span>{esc(p.get("pos_short", p["position"]))} · {esc(p.get("now", ""))}</span></span>'
        f'<span class="fr-go" aria-hidden="true">&rarr;</span></a></li>' for p in PLAYERS)
    return f'''<section class="finder" id="find" aria-labelledby="find-h">
  <div class="wrap finder-in">
    <h2 class="finder-h" id="find-h">Find a player</h2>
    <div class="finder-box">
      <label class="visually-hidden" for="find-q">Search players by name, position, school, or country</label>
      <input id="find-q" type="search" placeholder="Name, position, school, or country" autocomplete="off" data-finder aria-controls="find-results" aria-describedby="find-count">
      <p class="visually-hidden" id="find-count" aria-live="polite"></p>
    </div>
    <ul class="finder-results" id="find-results">{items}</ul>
    <p class="finder-empty" hidden>No players match that search. Try a position like &ldquo;forward&rdquo; or a school like &ldquo;Salt Lake&rdquo;.</p>
  </div>
</section>'''


def hero_rotator():
    """Home banner: rotating player photos (not their card photo). Name and position only; each links to the profile."""
    order = [p["id"] for p in sorted(PLAYERS, key=lambda x: x["id"] != "elijah-tenger")]
    byid = {p["id"]: p for p in PLAYERS}
    slides = []
    for n, pid in enumerate(order):
        p = byid[pid]
        hp = p.get("home_photo")
        if not hp:
            continue
        name, pos, alt = hp
        first = n == 0
        hidden = "" if first else ' aria-hidden="true" tabindex="-1"'
        slides.append(f'<a class="rot-slide{" is-active" if first else ""}" href="/stories/{p["id"]}/"{hidden}>'
                      f'{picture(name, alt, "(min-width: 900px) 480px, 100vw", eager=first, position=pos)}'
                      f'<span class="rot-cap"><b>{esc(p["name"])}</b><span>{esc(p.get("pos_short", p["position"]))}</span></span></a>')
    return f'''<figure class="stage-photo stage-photo--tall stage-rot tilt" data-tilt-max="5" data-rotator aria-label="Our players">
      {"".join(slides)}
      <span class="pcard-glare" aria-hidden="true"></span>
      <span class="rot-progress" aria-hidden="true"></span>
    </figure>'''


def hero_rotator_bg():
    out = []
    for n, p in enumerate(sorted(PLAYERS, key=lambda x: x["id"] != "elijah-tenger")):
        if p.get("home_photo"):
            out.append(f'<div class="rot-bg{" is-active" if n == 0 else ""}">{picture(p["home_photo"][0], "", "480px")}</div>')
    return f'<div class="stage-bg" aria-hidden="true" data-rotator-bg>{"".join(out)}</div>'


def player_table():
    rows = []
    for p in PLAYERS:
        film = []
        if p.get("interview"):
            film.append(f'<a href="https://www.youtube.com/watch?v={p["interview"]}" target="_blank" rel="noopener">Interview</a>')
        for n, h in enumerate([x for x in (p.get("highlight"), p.get("highlight2")) if x]):
            film.append(f'<a href="https://www.youtube.com/watch?v={h}" target="_blank" rel="noopener">Highlights{" " + str(n + 1) if p.get("highlight2") else ""}</a>')
        rows.append(f'<tr data-search="{search_text(p)}"><th scope="row"><a href="/stories/{p["id"]}/">{esc(p["name"])}</a></th>'
                    f'<td data-k="Position">{esc(p["position"])}</td><td data-k="From">{esc(p["origin"])}</td>'
                    f'<td data-k="Team">{esc(p.get("now", ""))}</td><td class="film" data-k="Film">{" · ".join(film)}</td></tr>')
    return f'''<div class="table-wrap" tabindex="0" role="region" aria-label="Players at a glance">
<table class="stats-table glance-table">
  <thead><tr><th scope="col">Player</th><th scope="col">Position</th><th scope="col">From</th><th scope="col">Current or latest team</th><th scope="col">Film</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table></div>'''


def video(vid, label, name):
    return (f'<figure class="video"><button type="button" class="yt" data-id="{vid}" aria-label="Play {esc(label)}: {esc(name)}">'
            f'<span class="play" aria-hidden="true"></span></button><figcaption>{esc(label)}</figcaption>'
            f'<noscript><a href="https://www.youtube.com/watch?v={vid}">Watch on YouTube</a></noscript></figure>')


STAT_COLS = [("gp", "GP", "Games played"), ("gs", "GS", "Games started"), ("g", "G", "Goals"), ("a", "A", "Assists"), ("min", "Min", "Minutes")]


def season_table(p):
    rows = p.get("seasons") or []
    cols = [c for c in STAT_COLS if any(r.get(c[0]) for r in rows)]   # drop columns with no data at all
    head = "".join(f'<th scope="col" title="{t}">{l}</th>' for _, l, t in cols)
    body = "".join(
        f'<tr><th scope="row">{esc(r["season"])}</th><td class="team">{esc(r["team"])}<span>{esc(r.get("level",""))}</span></td>'
        + "".join(f'<td data-l="{l}">{esc(r.get(k, ""))}</td>' for k, l, _ in cols)
        + f'<td class="tnote">{esc(r.get("note",""))}</td></tr>' for r in rows)
    t = p.get("seasons_total")
    foot = (f'<tfoot><tr><th scope="row">{esc(t["season"])}</th><td class="team"></td>'
            + "".join(f'<td data-l="{l}">{esc(t.get(k, ""))}</td>' for k, l, _ in cols)
            + '<td class="tnote"></td></tr></tfoot>') if t else ""
    return f'''<div class="table-wrap" tabindex="0" role="region" aria-label="Season statistics">
<table class="stats-table">
  <thead><tr><th scope="col">Season</th><th scope="col">Team</th>{head}<th scope="col">Notes</th></tr></thead>
  <tbody>{body}</tbody>{foot}
</table></div>'''


def profile_body(p, idx):
    next_p = PLAYERS[(idx + 1) % len(PLAYERS)]
    first = esc(p["first"])
    key = p.get("key", [])
    facts = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in key)
    counters = "".join(f'<div class="counter"><b data-count-to="{esc(s["n"])}">{esc(s["n"])}</b><span>{esc(s["l"])}</span></div>' for s in p["stats"])
    vids = []
    if p.get("interview"):
        vids.append(video(p["interview"], "Full interview", p["name"]))
    hl = [x for x in (p.get("highlight"), p.get("highlight2")) if x]
    for n, h in enumerate(hl):
        vids.append(video(h, "Highlight reel" + (f" {n + 1}" if len(hl) > 1 else ""), p["name"]))
    sections = p["sections"]
    intro = "".join(f"<p>{esc(x)}</p>" for x in sections[0]["p"])
    rest = "".join(f'<h3>{esc(s["h"])}</h3>' + "".join(f"<p>{esc(x)}</p>" for x in s["p"]) for s in sections[1:])
    quotes = "".join(f'<blockquote class="qcard"><p>&ldquo;{esc(q)}&rdquo;</p><cite>{esc(p["name"])}</cite></blockquote>' for q in p.get("quotes", []))
    path = "".join(f'<li><b>{esc(c["club"])}</b><span>{esc(c["level"])}</span><p>{esc(c["detail"])}</p></li>' for c in reversed(p["career"]))
    honours = "".join(f"<li>{esc(h)}</li>" for h in p["honours"])
    # Details not already shown in the hero fact bar
    shown = {v.lower() for _, v in key} | {k.lower() for k, _ in key}
    extra = [(k, v) for k, v in p["facts"] if k.lower() not in shown and v.lower() not in shown]
    info = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in extra)
    sources = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(l)}</a></li>' for l, u in p.get("sources", []))
    resume = (f'<a class="util" href="{p["resume"]}" target="_blank" rel="noopener">Résumé (PDF)</a>' if p.get("resume") else "")
    contact = f'/partners/?type=club&amp;player={esc(p["name"]).replace(" ", "+")}#inquiry'
    head = (f'<div class="phero-head">{picture(p["headshot"], p["name"] + " official headshot", "92px")}</div>' if p.get("headshot") else "")
    gallery = "".join(f'<div class="ph tilt" data-tilt-max="4">{picture(n, photo_alt(p, n), "(min-width: 1000px) 260px, 45vw", position=photo_pos(p, n))}</div>' for n in p["photos"][:3])
    hero = p["hero_photo"]
    watch = '<a class="btn btn--outline-light" href="#video">&#9654; Watch film</a>' if vids else ""

    film = (f'''<section class="section film" id="video" aria-labelledby="film-h">
  <div class="wrap">
    <div class="head-row"><h2 class="h2" id="film-h">Watch {first}.</h2><p>{"Full interview and highlights." if len(vids) > 1 else "Full interview."}</p></div>
    <div class="videos videos--{min(len(vids), 3)}">{"".join(vids)}</div>
  </div>
</section>''' if vids else "")

    table = season_table(p) if p.get("seasons") else ""
    glance_left = (f'<div><h3 class="aside-h">Season by season</h3>{table}</div>' if table else "")

    return f'''<article class="profile" aria-labelledby="pname">
<section class="stage stage--profile">
  {stage_bg(p.get("hero_bg", hero), sharp=bool(p.get("hero_bg")))}
  <div class="wrap">
    <a class="back-link" href="/stories/">&larr; All players</a>
    <div class="stage-grid">
      <div class="stage-copy">
        {head}
        <p class="eyebrow">{esc(p["position"])} · {esc(p["origin"])}</p>
        <h1 class="display" id="pname">{esc(p["name"])}</h1>
        {now_html(p)}
        <p class="feat-tagline">{esc(p.get("tagline", ""))}</p>
        <p class="serif-quote">&ldquo;{esc(p["short_quote"])}&rdquo;</p>
        <div class="btn-row no-print"><a class="btn" href="{contact}">Contact about {first} {ARROW}</a>{watch}</div>
      </div>
      <figure class="stage-photo tilt" data-tilt-max="5">{picture(hero, photo_alt(p, hero), "(min-width: 900px) 460px, 100vw", eager=True, position=p.get("hero_pos", ""))}<span class="pcard-glare" aria-hidden="true"></span></figure>
    </div>
    <div class="factbar"><dl>{facts}</dl><div class="util-row no-print" style="margin:0"><button type="button" class="util" data-share>Share</button><button type="button" class="util" data-print>Save as PDF</button>{resume}</div></div>
  </div>
</section>

{film}

<section class="section section--mint" id="stats" aria-labelledby="glance-h">
  <div class="wrap">
    <h2 class="h2" id="glance-h">At a glance.</h2>
    <div class="counters">{counters}</div>
    <div class="glance-grid{" glance-grid--one" if not table else ""}">
      {glance_left}
      <div class="aside-block" id="honours"><h3 class="aside-h">Honours &amp; achievements</h3><ul class="honours">{honours}</ul><p class="as-of mt-s">{esc(p["as_of"])}</p></div>
    </div>
  </div>
</section>

<section class="section" id="career" aria-labelledby="path-h">
  <div class="wrap">
    <h2 class="h2" id="path-h" style="margin-bottom:36px">The path so far.</h2>
    <ol class="path">{path}</ol>
  </div>
</section>

<section class="section section--tight" id="story" aria-labelledby="story-h">
  <div class="wrap story-grid">
    <div class="prose">
      <h2 class="h2" id="story-h" style="margin-bottom:14px">His story.</h2>
      <p class="story-lede">{esc(p.get("headline", ""))}</p>
      {intro}
      <details class="more"><summary>Read his full story</summary><div class="more-body">{rest}</div></details>
      {('<div class="quote-stack">' + quotes + '</div>') if quotes else ""}
    </div>
    <div class="mosaic">{gallery}</div>
  </div>
</section>

<section class="section section--tight info-band" aria-labelledby="info-h">
  <div class="wrap info-row">
    {f'<div><h3 class="aside-h" id="info-h">Player details</h3><dl class="facts facts--grid">{info}</dl></div>' if info else '<h3 class="visually-hidden" id="info-h">Sources</h3>'}
    {f'<div><h3 class="aside-h">Official sources</h3><ul class="src-list">{sources}</ul></div>' if sources else ""}
  </div>
</section>

<section class="cta-band no-print" aria-labelledby="pcta">
  <div class="wrap inner">
    <h2 class="h2" id="pcta">Interested in {first}?</h2>
    <div class="btn-row">
      <a class="btn btn--dark" href="{contact}">Contact The 91st</a>
      <a class="btn btn--light" href="/stories/{next_p["id"]}/">Next: {esc(next_p["name"])} &rarr;</a>
    </div>
  </div>
</section>
</article>'''



def resources():
    out = []
    for c in RESOURCES["categories"]:
        items = []
        for it in c["items"]:
            badge = ('<span class="badge badge--now">Verified partner</span>' if it["status"] == "partner"
                     else '<span class="badge badge--public">Public resource</span>')
            items.append(f'''<div class="res"><div class="res-top"><h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it["name"])}</a></h3>{badge}</div><p>{esc(it["desc"])}</p></div>''')
        if not any(it["status"] == "partner" for it in c["items"]):
            items.append('''<div class="empty"><p>Listings coming soon.</p><a class="link-arrow" href="#suggest">Suggest a resource <span class="arrow" aria-hidden="true">&rarr;</span></a></div>''')
        out.append(f'''<section class="dir-cat" id="{c["id"]}" aria-labelledby="{c["id"]}-h">
  <div><h2 class="h3" id="{c["id"]}-h">{esc(c["title"])}</h2><p class="mt-s">{esc(c["intro"])}</p></div>
  <div class="dir-list">{"".join(items)}</div>
</section>''')
    return "\n".join(out)


ICONS = {
    "football": '<circle cx="12" cy="12" r="9"/><path d="M12 7l4 3-1.5 4.5h-5L8 10z"/>',
    "education": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>',
    "career": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2"/>',
    "wellbeing": '<path d="M20.8 5.6a5 5 0 00-7.1 0L12 7.3l-1.7-1.7a5 5 0 10-7.1 7.1L12 21.5l8.8-8.8a5 5 0 000-7.1z"/>',
    "transition": '<path d="M5 12h14M13 6l6 6-6 6"/>',
}


def resource_nav():
    return '<div class="cats" role="group" aria-label="Filter by category">' + "".join(
        f'<button type="button" class="cat" data-cat="{c["id"]}" aria-pressed="false"><span class="icon"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(c["id"], "")}</svg></span><span class="t">{esc(c["title"])}</span></button>'
        for c in RESOURCES["categories"]) + "</div>"


BLOCKS = {
    "players_rail": players_rail,
    "roster": roster,
    "featured_story": featured_story,
    "player_table": player_table,
    "hero_rotator": hero_rotator,
    "hero_rotator_bg": hero_rotator_bg,
    "player_finder": player_finder,
    "resources": resources,
    "resource_nav": resource_nav,
    "player_count": lambda: str(len(PLAYERS)),
    "player_ids": lambda: json.dumps([p["id"] for p in PLAYERS]),
}

JSONLD_ORG = {
    "@context": "https://schema.org",
    "@type": "NGO",
    "name": "The 91st Foundation",
    "alternateName": "The 91st",
    "url": SITE + "/",
    "logo": SITE + "/assets/favicon.svg",
    "email": "team@the91st.org",
    "slogan": "For what comes after the final whistle.",
    "description": "The 91st Foundation supports college soccer players as they transition beyond competitive soccer by connecting them with opportunities in professional football, education, career development, and wellbeing.",
    "taxID": "42-2269701",
    "nonprofitStatus": "Nonprofit501c3",
    "sameAs": ["https://www.instagram.com/91stclub", "https://www.youtube.com/@91stclub", "https://www.tiktok.com/@91stclub"],
}


def wrap_page(meta, body):
    body = re.sub(r"\{\{picture\s+(.*?)\}\}", picture_directive, body, flags=re.S)
    for key, fn in BLOCKS.items():
        if "{{" + key + "}}" in body:
            body = body.replace("{{" + key + "}}", fn())
    body = body.replace("{{donate_url}}", DONATE_URL).replace("{{formspree}}", FORMSPREE)

    active = meta.get("nav", "")
    cur = ' aria-current="page"'
    nav = "\n".join(f'        <li><a href="{href}"{cur if key == active else ""}>{label}</a></li>' for key, href, label in NAV)
    mnav = "\n".join(f'        <li><a class="mm-link" href="{href}"{cur if key == active else ""}>{label}</a></li>' for key, href, label in NAV)

    title = meta["title"]
    full_title = title if "91st" in title else f"{title} | The 91st Foundation"
    jsonld = meta.get("jsonld", "")
    if meta.get("path") == "/":
        jsonld = '<script type="application/ld+json">' + json.dumps(JSONLD_ORG) + "</script>"
    og_image = meta.get("og_image", "/assets/img/og-default.jpg")

    layout = (SRC / "layout.html").read_text()
    out = (layout.replace("{{content}}", body)
                 .replace("{{title}}", esc(full_title))
                 .replace("{{og_title}}", esc(meta.get("og_title", full_title)))
                 .replace("{{description}}", esc(meta["description"]))
                 .replace("{{canonical}}", SITE + meta["path"])
                 .replace("{{og_image}}", SITE + og_image)
                 .replace("{{site}}", SITE)
                 .replace("{{nav}}", nav)
                 .replace("{{mobile_nav}}", mnav)
                 .replace("{{home_current}}", ' aria-current="page"' if meta["path"] == "/" else "")
                 .replace("{{jsonld}}", jsonld)
                 .replace("{{donate_url}}", DONATE_URL)
                 .replace("{{version}}", VERSION))
    if meta.get("noindex"):
        out = out.replace('<meta name="theme-color"', '<meta name="robots" content="noindex">\n<meta name="theme-color"')
    leftover = re.findall(r"\{\{[a-z_]+.*?\}\}", out)
    if leftover:
        raise SystemExit(f"{meta['path']}: unresolved placeholders {leftover}")

    p = meta["path"]
    dest = ROOT / ("404.html" if p == "/404.html" else (p.strip("/") + "/index.html" if p != "/" else "index.html"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return meta


def render(page_path):
    raw = page_path.read_text()
    m = re.match(r"\s*<!--meta\s+(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        raise SystemExit(f"{page_path.name}: missing <!--meta {{...}} --> header")
    return wrap_page(json.loads(m.group(1)), raw[m.end():])


def render_profiles():
    metas = []
    for i, p in enumerate(PLAYERS):
        person = {
            "@context": "https://schema.org", "@type": "Person", "name": p["name"],
            "description": p.get("headline", ""), "url": f"{SITE}/stories/{p['id']}/",
            "homeLocation": p["origin"],
        }
        og = f"/assets/img/{p['card_photo']}-960.jpg" if has_img(p["card_photo"]) else "/assets/img/og-default.jpg"
        meta = {
            "title": f"{p['name']}, {p.get('pos_short', 'player')} profile",
            "description": f"{p['name']}: {p.get('headline', '')} Stats, career history, honours, and full interview.",
            "path": f"/stories/{p['id']}/", "nav": "stories", "og_image": og,
            "jsonld": '<script type="application/ld+json">' + json.dumps(person) + "</script>",
        }
        metas.append(wrap_page(meta, profile_body(p, i)))
    return metas


def main():
    metas = [render(p) for p in sorted((SRC / "pages").glob("*.html"))]
    metas += render_profiles()
    for old, new in REDIRECTS.items():
        d = ROOT / old.strip("/")
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Moved</title><link rel="canonical" href="{SITE}{new}"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={new}"></head><body><p>This page moved to <a href="{new}">{SITE}{new}</a>.</p></body></html>\n')
    urls = [m for m in metas if not m.get("noindex")]
    today = time.strftime("%Y-%m-%d")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for m in sorted(urls, key=lambda x: (x["path"] != "/", x["path"])):
        sm.append(f"  <url><loc>{SITE}{m['path']}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"Built {len(metas)} pages.")
    if MISSING:
        print("Photos not added yet (showing monogram placeholders):", ", ".join(sorted(set(MISSING))))


if __name__ == "__main__":
    main()
