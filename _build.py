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


def tilt_card(p, extra_cls="", sizes="(min-width: 1000px) 30vw, (min-width: 720px) 45vw, 85vw"):
    levels = " ".join(p.get("level", []))
    lv = "".join(f'<span class="chip-sm">{esc(l)}</span>' for l in p.get("level", []))
    return f'''<a class="pcard tilt {extra_cls}" href="/stories/{p["id"]}/" data-level="{esc(levels)}">
  <div class="pcard-inner">
    <div class="pcard-photo">{picture(p["card_photo"], photo_alt(p, p["card_photo"]), sizes)}</div>
    <div class="pcard-shade" aria-hidden="true"></div>
    <div class="pcard-top">{lv}</div>
    <div class="pcard-info">
      <span class="pcard-pos">{esc(p.get("pos_short", p["position"]))} · {esc(p["origin"])}</span>
      <h3 class="pcard-name">{esc(p["name"])}</h3>
      <span class="pcard-line">{esc(p["card_line"])}</span>
      <span class="pcard-cta">View profile {ARROW}</span>
    </div>
    <span class="pcard-glare" aria-hidden="true"></span>
  </div>
</a>'''


def players_rail():
    cards = "\n".join(tilt_card(p, "rail-item", "(min-width: 1000px) 26vw, 78vw") for p in PLAYERS)
    return f'''<div class="rail-wrap">
  <div class="rail" tabindex="0" aria-label="Featured players, scroll sideways">{cards}</div>
  <div class="rail-ctrl">
    <button class="rail-btn" type="button" data-dir="-1" aria-label="Previous players">&larr;</button>
    <button class="rail-btn" type="button" data-dir="1" aria-label="Next players">&rarr;</button>
  </div>
</div>'''


def roster():
    levels = []
    for p in PLAYERS:
        for l in p.get("level", []):
            if l not in levels:
                levels.append(l)
    chips = '<button type="button" class="filter is-on" data-filter="all" aria-pressed="true">All players</button>' + "".join(
        f'<button type="button" class="filter" data-filter="{esc(l)}" aria-pressed="false">{esc(l)}</button>' for l in levels)
    cards = "\n".join(tilt_card(p) for p in PLAYERS)
    return f'''<div class="filters" role="group" aria-label="Filter players">{chips}</div>
<p class="small filter-count" aria-live="polite"><span data-count>{len(PLAYERS)}</span> players</p>
<div class="roster">{cards}</div>'''


def video(vid, label, name):
    return (f'<figure class="video"><button type="button" class="yt" data-id="{vid}" aria-label="Play {esc(label)}: {esc(name)}">'
            f'<span class="play" aria-hidden="true"></span><span class="yt-label">{esc(label)}</span></button>'
            f'<noscript><a href="https://www.youtube.com/watch?v={vid}">Watch on YouTube</a></noscript></figure>')


def season_table(p):
    rows = p.get("seasons") or []
    if not rows:
        return '<p class="empty-note">Season-by-season statistics will be added after they are confirmed with official sources. Achievements and career history are listed below.</p>'
    def cell(v):
        return esc(v) if v else '<span class="na" title="Not yet confirmed">—</span>'
    body = "".join(
        f'<tr><th scope="row">{esc(r["season"])}</th><td class="team">{esc(r["team"])}<span>{esc(r.get("level",""))}</span></td>'
        f'<td data-l="GP">{cell(r["gp"])}</td><td data-l="GS">{cell(r["gs"])}</td><td data-l="G">{cell(r["g"])}</td><td data-l="A">{cell(r["a"])}</td><td data-l="Min">{cell(r["min"])}</td>'
        f'<td class="tnote">{esc(r.get("note",""))}</td></tr>' for r in rows)
    t = p.get("seasons_total")
    foot = (f'<tfoot><tr><th scope="row">{esc(t["season"])}</th><td class="team"></td><td data-l="GP">{esc(t["gp"])}</td><td data-l="GS">{esc(t["gs"])}</td>'
            f'<td data-l="G">{esc(t["g"])}</td><td data-l="A">{esc(t["a"])}</td><td data-l="Min">{esc(t["min"])}</td><td class="tnote"></td></tr></tfoot>') if t else ""
    return f'''<div class="table-wrap" tabindex="0" role="region" aria-label="Season statistics, scroll sideways on small screens">
<table class="stats-table">
  <thead><tr><th scope="col">Season</th><th scope="col">Team</th><th scope="col" title="Games played">GP</th><th scope="col" title="Games started">GS</th><th scope="col" title="Goals">G</th><th scope="col" title="Assists">A</th><th scope="col" title="Minutes">Min</th><th scope="col">Notes</th></tr></thead>
  <tbody>{body}</tbody>{foot}
</table></div>
<p class="small mt-s">{esc(p.get("seasons_note",""))} &ldquo;—&rdquo; means not yet confirmed.</p>'''


def profile_body(p, idx):
    ph = p["photos"]
    prev_p = PLAYERS[idx - 1]
    next_p = PLAYERS[(idx + 1) % len(PLAYERS)]
    badges = "".join(f'<span class="badge badge--public">{esc(b)}</span>' for b in p["badges"])
    keyfacts = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in p.get("key", []))
    counters = "".join(
        f'<div class="counter"><b data-count-to="{esc(s["n"])}">{esc(s["n"])}</b><span>{esc(s["l"])}</span></div>' for s in p["stats"])
    vids = []
    if p.get("interview"):
        vids.append(video(p["interview"], "Full interview", p["name"]))
    if p.get("highlight"):
        vids.append(video(p["highlight"], "Highlight reel", p["name"]))
    vids_html = f'<div class="videos {"videos--2" if len(vids) > 1 else ""}">{"".join(vids)}</div>' if vids else ""
    story = "".join(f'<h3>{esc(s["h"])}</h3>' + "".join(f"<p>{esc(x)}</p>" for x in s["p"]) for s in p["sections"])
    quotes = "".join(f'<blockquote class="qcard tilt-soft"><p>&ldquo;{esc(q)}&rdquo;</p><cite>{esc(p["name"])}</cite></blockquote>' for q in p.get("quotes", []))
    career = "".join(f'<li><strong>{esc(c["club"])}</strong><span class="lvl">{esc(c["level"])}</span><p>{esc(c["detail"])}</p></li>' for c in p["career"])
    honours = "".join(f"<li>{esc(h)}</li>" for h in p["honours"])
    facts = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in p["facts"])
    sources = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(l)}</a></li>' for l, u in p.get("sources", []))
    sources_html = f'<div class="aside-block"><h3 class="aside-h">Official sources</h3><ul class="src-list">{sources}</ul></div>' if sources else ""
    resume = (f'<a class="btn btn--ghost btn--sm" href="{p["resume"]}" target="_blank" rel="noopener">Résumé (PDF)</a>' if p.get("resume") else "")
    aka = f'<p class="aka">{esc(p["aka"])}</p>' if p.get("aka") else ""
    contact = f'/partners/?type=club&amp;player={esc(p["name"]).replace(" ", "+")}#inquiry'
    side = [(ph[1] if len(ph) > 1 else ph[0]), (ph[2] if len(ph) > 2 else ph[-1])]
    gallery = "".join(f'<div class="ph tilt-soft">{picture(n, photo_alt(p, n), "(min-width: 960px) 22vw, 45vw", position=photo_pos(p, n))}</div>' for n in dict.fromkeys(side))
    tabs = [("overview", "Overview"), ("video", "Video"), ("stats", "Stats"), ("career", "Career"), ("story", "Story")]
    if not vids:
        tabs = [t for t in tabs if t[0] != "video"]
    tabnav = "".join(f'<a href="#{i}">{l}</a>' for i, l in tabs)

    return f'''<article class="profile" aria-labelledby="pname">
<section class="profile-hero">
  <div class="wrap profile-hero-grid">
    <div class="profile-intro reveal">
      <a class="back-link" href="/stories/">&larr; All players</a>
      <div class="story-kicker mt-s">{badges}</div>
      <h1 class="display" id="pname">{esc(p["name"])}</h1>
      {aka}
      <p class="pos">{esc(p["position"])} · {esc(p["origin"])}</p>
      <p class="lede mt-s">{esc(p.get("headline", ""))}</p>
      <p class="status"><span class="dot" aria-hidden="true"></span>{esc(p.get("status", ""))}</p>
      <div class="btn-row mt-m no-print">
        <a class="btn" href="{contact}">Contact about {esc(p["first"])} {ARROW}</a>
        {('<a class="btn btn--ghost" href="#video">Watch interview</a>' if vids else '')}
      </div>
      <div class="util-row no-print">
        <button type="button" class="util" data-share>Share profile</button>
        <button type="button" class="util" data-print>Save as PDF</button>
        {resume}
      </div>
    </div>
    <div class="profile-card-wrap reveal d1">
      <div class="profile-card tilt" data-tilt-max="7">
        <div class="pcard-inner">
          <div class="pcard-photo">{picture(ph[0], photo_alt(p, ph[0]), "(min-width: 960px) 38vw, 90vw", eager=True)}</div>
          <div class="pcard-shade" aria-hidden="true"></div>
          <div class="pcard-info">
            <span class="pcard-pos">{esc(p.get("pos_short", ""))}</span>
            <span class="pcard-name">{esc(p["name"])}</span>
          </div>
          <span class="pcard-glare" aria-hidden="true"></span>
        </div>
      </div>
    </div>
  </div>
</section>

<nav class="tabbar no-print" aria-label="Profile sections"><div class="wrap">{tabnav}</div></nav>

<section class="section section--tight" id="overview" aria-label="Overview">
  <div class="wrap">
    <dl class="keyfacts reveal">{keyfacts}</dl>
    <div class="counters reveal d1">{counters}</div>
  </div>
</section>

{f"""<section class="section section--mint" id="video" aria-labelledby="video-h">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">Watch</p><h2 class="h2" id="video-h">In his own words.</h2></div>
    {vids_html}
  </div>
</section>""" if vids else ""}

<section class="section" id="stats" aria-labelledby="stats-h">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow">Statistics</p><h2 class="h2" id="stats-h">Season by season.</h2></div>
    {season_table(p)}
  </div>
</section>

<section class="section section--mint" id="career" aria-labelledby="career-h">
  <div class="wrap profile-cols">
    <div>
      <p class="eyebrow">Career</p><h2 class="h2" id="career-h">The path so far.</h2>
      <ol class="timeline mt-m">{career}</ol>
    </div>
    <div class="profile-side">
      <div class="aside-block"><h3 class="aside-h">Honours &amp; achievements</h3><ul class="honours">{honours}</ul></div>
      <div class="aside-block"><h3 class="aside-h">Player info</h3><dl class="facts">{facts}</dl><p class="as-of mt-s">{esc(p["as_of"])}</p></div>
      {sources_html}
    </div>
  </div>
</section>

<section class="section" id="story" aria-labelledby="story-h">
  <div class="wrap profile-cols">
    <div class="prose">
      <p class="eyebrow">His story</p><h2 class="h2" id="story-h">Beyond the stat sheet.</h2>
      <blockquote class="serif-quote pull">&ldquo;{esc(p["quote"])}&rdquo;</blockquote>
      {story}
    </div>
    <div class="profile-side">
      <div class="gallery">{gallery}</div>
      {quotes}
    </div>
  </div>
</section>

<section class="cta-band no-print" aria-labelledby="pcta">
  <div class="wrap inner">
    <h2 class="h2" id="pcta">Interested in {esc(p["first"])}?</h2>
    <div class="btn-row">
      <a class="btn btn--dark" href="{contact}">Contact The 91st</a>
      <a class="btn btn--light" href="mailto:team@the91st.org?subject={esc(p['name']).replace(' ', '%20')}%20-%20player%20inquiry">Email us</a>
    </div>
  </div>
</section>

<nav class="pnav no-print" aria-label="More players">
  <div class="wrap pnav-inner">
    <a href="/stories/{prev_p["id"]}/"><span class="small">Previous player</span><strong>&larr; {esc(prev_p["name"])}</strong></a>
    <a href="/stories/{next_p["id"]}/" class="r"><span class="small">Next player</span><strong>{esc(next_p["name"])} &rarr;</strong></a>
  </div>
</nav>
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
            items.append('''<div class="empty"><p>We are building verified listings for this category. Organizations are added after we confirm their services and agree to work together.</p><a class="link-arrow" href="#suggest">Suggest a resource <span class="arrow" aria-hidden="true">&rarr;</span></a></div>''')
        out.append(f'''<section class="dir-cat" id="{c["id"]}" aria-labelledby="{c["id"]}-h">
  <div><h2 class="h3" id="{c["id"]}-h">{esc(c["title"])}</h2><p class="mt-s">{esc(c["intro"])}</p></div>
  <div class="dir-list">{"".join(items)}</div>
</section>''')
    return "\n".join(out)


def resource_nav():
    return '<nav class="dir-nav" aria-label="Resource categories">' + "".join(
        f'<a href="#{c["id"]}">{esc(c["title"])}</a>' for c in RESOURCES["categories"]) + "</nav>"


BLOCKS = {
    "players_rail": players_rail,
    "roster": roster,
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
