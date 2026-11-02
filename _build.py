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
    ("mission", "/mission/", "Our Mission"),
    ("players", "/players/", "For Players"),
    ("partners", "/partners/", "Partnerships"),
    ("stories", "/stories/", "Player Stories"),
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
    return p.get("photos_card_alt", p["name"])


def photo_pos(p, name):
    return p.get("pos", {}).get(name, "")


def photo_card(p, cls="", sizes="(min-width: 1000px) 30vw, (min-width: 720px) 45vw, 85vw", quote=True, sub=True):
    q = f'<span class="pc-quote">&ldquo;{esc(p["short_quote"])}&rdquo;</span>' if quote and p.get("short_quote") else ""
    line = f'<span class="pc-sub">{esc(p["card_line"])}</span>' if sub else ""
    return f'''<a class="pc tilt {cls}" href="/stories/{p["id"]}/">
  {picture(p["card_photo"], photo_alt(p, p["card_photo"]), sizes, position=photo_pos(p, p["card_photo"]))}
  <span class="pc-cap">
    <span class="pc-tag">{esc(p.get("pos_short", p["position"]))} · {esc(p["origin"])}</span>
    <span class="pc-title">{esc(p["name"])}</span>
    {q}{line}
  </span>
  <span class="pcard-glare" aria-hidden="true"></span>
</a>'''


def players_rail():
    cards = "\n".join(photo_card(p, "rail-item", "(min-width: 1000px) 26vw, 78vw", sub=False) for p in PLAYERS)
    return f'''<div class="rail-wrap">
  <div class="rail" tabindex="0" aria-label="Featured players, scroll sideways">{cards}</div>
  <div class="rail-ctrl">
    <button class="rail-btn" type="button" data-dir="-1" aria-label="Previous players">&larr;</button>
    <button class="rail-btn" type="button" data-dir="1" aria-label="Next players">&rarr;</button>
  </div>
</div>'''


def featured_story():
    p = PLAYERS[0]
    photo = p.get("featured_photo", "alejandro-night")
    vid = f'<a class="btn btn--outline-light" href="/stories/{p["id"]}/#video">&#9654; Watch the interview</a>' if p.get("interview") else ""
    return f'''<section class="cine" aria-labelledby="featured-h">
  {picture(photo, photo_alt(p, photo) if photo in p["photos"] else p["name"] + " on the ball", "100vw", eager=True, position="center 35%")}
  <div class="wrap cine-inner"><div class="cine-copy">
    <p class="eyebrow">Featured story</p>
    <h1 class="display" id="featured-h">{esc(p["name"])}</h1>
    <p class="pc-tag" style="margin:0">{esc(p.get("pos_short",""))} · {esc(p["origin"])}</p>
    <p class="cine-tag" style="color:var(--white)">&ldquo;{esc(p["quote"])}&rdquo;</p>
    <div class="btn-row"><a class="btn" href="/stories/{p["id"]}/">Meet {esc(p["first"])} {ARROW}</a>{vid}</div>
  </div></div>
</section>'''


def roster():
    cards = "\n".join(photo_card(p, "roster-card") for p in PLAYERS)
    return f'<div class="roster">{cards}</div>'


def video(vid, label, name):
    return (f'<figure class="video"><button type="button" class="yt" data-id="{vid}" aria-label="Play {esc(label)}: {esc(name)}">'
            f'<span class="play" aria-hidden="true"></span><span class="yt-label">{esc(label)}</span></button>'
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
    ph = p["photos"]
    next_p = PLAYERS[(idx + 1) % len(PLAYERS)]
    facts = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in p.get("key", []))
    counters = "".join(f'<div class="counter"><b data-count-to="{esc(s["n"])}">{esc(s["n"])}</b><span>{esc(s["l"])}</span></div>' for s in p["stats"])
    vids = []
    if p.get("interview"):
        vids.append(video(p["interview"], "Full interview", p["name"]))
    if p.get("highlight"):
        vids.append(video(p["highlight"], "Highlight reel", p["name"]))
    sections = p["sections"]
    intro = "".join(f"<p>{esc(x)}</p>" for x in sections[0]["p"])
    rest = "".join(f'<h3>{esc(s["h"])}</h3>' + "".join(f"<p>{esc(x)}</p>" for x in s["p"]) for s in sections[1:])
    quotes = "".join(f'<blockquote class="qcard"><p>&ldquo;{esc(q)}&rdquo;</p><cite>{esc(p["name"])}</cite></blockquote>' for q in p.get("quotes", []))
    path = "".join(f'<li><b>{esc(c["club"])}</b><span>{esc(c["level"])}</span><p>{esc(c["detail"])}</p></li>' for c in reversed(p["career"]))
    honours = "".join(f"<li>{esc(h)}</li>" for h in p["honours"])
    info = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in p["facts"])
    sources = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(l)}</a></li>' for l, u in p.get("sources", []))
    sources_html = f'<div class="aside-block"><h3 class="aside-h">Official sources</h3><ul class="src-list">{sources}</ul></div>' if sources else ""
    resume = (f'<a class="util" href="{p["resume"]}" target="_blank" rel="noopener">Résumé (PDF)</a>' if p.get("resume") else "")
    contact = f'/partners/?type=club&amp;player={esc(p["name"]).replace(" ", "+")}#inquiry'
    status = f'<p class="status"><span class="dot" aria-hidden="true"></span>{esc(p["status"])}</p>' if p.get("status") else ""
    head = (f'<div class="phero-head">{picture(p["headshot"], p["name"] + " official headshot", "92px")}</div>' if p.get("headshot") else "")
    gallery = "".join(f'<div class="ph">{picture(n, photo_alt(p, n), "(min-width: 960px) 22vw, 33vw", position=photo_pos(p, n))}</div>' for n in ph[:3])
    video_feature = (f'<div>{vids[0]}</div>' if vids else f'<div class="gallery3" style="margin-top:0">{gallery}</div>')

    tabs = [("story", "Story")]
    if p.get("seasons"):
        tabs.append(("stats", "Stats"))
    tabs += [("career", "Career"), ("honours", "Honours & info")]
    if vids:
        tabs.append(("video", "Video"))
    tabbar = "".join(f'<button type="button" role="tab" id="tab-{i}" aria-controls="{i}" aria-selected="{"true" if n == 0 else "false"}" tabindex="{0 if n == 0 else -1}">{l}</button>' for n, (i, l) in enumerate(tabs))

    stats_panel = (f'''<section class="tabpanel" id="stats" role="tabpanel" aria-labelledby="tab-stats" hidden><div class="wrap">
  <h2 class="h2 mb-0" style="margin-bottom:28px">Season by season.</h2>{season_table(p)}</div></section>''' if p.get("seasons") else "")
    video_panel = (f'''<section class="tabpanel" id="video" role="tabpanel" aria-labelledby="tab-video" hidden><div class="wrap">
  <div class="videos {"videos--2" if len(vids) > 1 else ""}">{"".join(vids)}</div></div></section>''' if vids else "")

    return f'''<article class="profile" aria-labelledby="pname">
<section class="phero">
  <div class="phero-photo">{picture(p["hero_photo"], photo_alt(p, p["hero_photo"]), "(min-width: 900px) 62vw, 100vw", eager=True, position=p.get("hero_pos", ""))}</div>
  <div class="wrap phero-inner">
    <a class="back-link" href="/stories/">&larr; All players</a>
    <div class="phero-copy">
      {head}
      <p class="eyebrow">{esc(p["position"])} · {esc(p["origin"])}</p>
      <h1 class="display" id="pname">{esc(p["name"])}</h1>
      <p class="serif-quote">&ldquo;{esc(p["short_quote"])}&rdquo;</p>
      {status}
      <div class="btn-row no-print"><a class="btn" href="{contact}">Contact about {esc(p["first"])} {ARROW}</a>{('<a class="btn btn--outline-light" href="#video" data-open-tab="video">&#9654; Watch interview</a>' if vids else '')}</div>
    </div>
    <div class="factbar"><dl>{facts}</dl><div class="util-row no-print" style="margin:0"><button type="button" class="util" data-share>Share</button><button type="button" class="util" data-print>Save as PDF</button>{resume}</div></div>
  </div>
</section>

<section class="section section--tight" aria-label="Highlights">
  <div class="wrap"><div class="counters" style="margin-top:0">{counters}</div></div>
</section>

<div class="ptabbar no-print" data-tabs><div class="wrap" role="tablist" aria-label="Profile sections">{tabbar}</div></div>

<section class="tabpanel" id="story" role="tabpanel" aria-labelledby="tab-story"><div class="wrap">
  <div class="story-grid">
    {video_feature}
    <div class="prose">
      <h2 class="h2" style="margin-bottom:14px">His story.</h2>
      <p class="story-lede">{esc(p.get("headline", ""))}</p>
      {intro}
      <details class="more"><summary>Read his full story</summary><div class="more-body">{rest}</div></details>
    </div>
  </div>
  {('<div class="tiles mt-l">' + quotes + '</div>') if quotes else ""}
  {('<div class="gallery3">' + gallery + '</div>') if vids else ""}
</div></section>

{stats_panel}

<section class="tabpanel" id="career" role="tabpanel" aria-labelledby="tab-career" hidden><div class="wrap">
  <h2 class="h2" style="margin-bottom:32px">The path so far.</h2>
  <ol class="path">{path}</ol>
</div></section>

<section class="tabpanel" id="honours" role="tabpanel" aria-labelledby="tab-honours" hidden><div class="wrap profile-cols">
  <div class="aside-block"><h3 class="aside-h">Honours &amp; achievements</h3><ul class="honours">{honours}</ul></div>
  <div class="profile-side">
    <div class="aside-block"><h3 class="aside-h">Player info</h3><dl class="facts">{info}</dl><p class="as-of mt-s">{esc(p["as_of"])}</p></div>
    {sources_html}
  </div>
</div></section>

{video_panel}

<section class="cta-band no-print" aria-labelledby="pcta">
  <div class="wrap inner">
    <h2 class="h2" id="pcta">Interested in {esc(p["first"])}?</h2>
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
