#!/usr/bin/env python3
"""Build the static site from _src/ into the repo root.

    python3 _build.py

- Page sources live in _src/pages/*.html. Each starts with a meta comment:
    <!--meta {"title": "...", "description": "...", "path": "/partners/", "nav": "partners"} -->
- Shared header/footer live in _src/layout.html.
- Player stories come from _src/data/players.json.
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
    if not out:
        raise SystemExit(f"Missing optimized image: {name}. Run python3 _tools/optimize_images.py")
    return out


def picture(name, alt, sizes="100vw", cls="", eager=False, position=""):
    ws = img_widths(name)
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
    return picture(attrs["name"], attrs.get("alt", ""), attrs.get("sizes", "100vw"), attrs.get("class", ""),
                   attrs.get("eager") == "true", attrs.get("position", ""))


# ---------- data-driven blocks ----------
PLAYERS = json.loads((SRC / "data/players.json").read_text())
RESOURCES = json.loads((SRC / "data/resources.json").read_text())


def player_cards():
    out = []
    for i, p in enumerate(PLAYERS):
        d = f" d{i}" if i else ""
        out.append(f'''<a class="player-card reveal{d}" href="/stories/#{p["id"]}">
  <div class="ph">{picture(p["card_photo"], p["alts"][1] if p["card_photo"] == p["photos"][1] else p["alts"][0], "(min-width: 720px) 33vw, 100vw")}</div>
  <div class="meta">
    <h3>{esc(p["name"])}</h3>
    <p class="pos">{esc(p["position"])} · {esc(p["origin"])}</p>
    <blockquote>&ldquo;{esc(p["quote"])}&rdquo;</blockquote>
    <span class="link-arrow">Read {esc(p["first"])}'s story <span class="arrow" aria-hidden="true">&rarr;</span></span>
  </div>
</a>''')
    return '<div class="player-cards">\n' + "\n".join(out) + "\n</div>"


def video(vid, label, name):
    return (f'<figure class="video"><button type="button" class="yt" data-id="{vid}" aria-label="Play {esc(label)}: {esc(name)}">'
            f'<span class="play" aria-hidden="true"></span></button><figcaption>{esc(label)}</figcaption>'
            f'<noscript><a href="https://www.youtube.com/watch?v={vid}">Watch on YouTube</a></noscript></figure>')


def stories():
    out = []
    for p in PLAYERS:
        ph = p["photos"]
        if len(ph) >= 3:
            photos = (f'<div class="story-photos">'
                      f'<div class="ph">{picture(ph[0], p["alts"][0], "(min-width: 960px) 30vw, 60vw")}</div>'
                      f'<div class="ph">{picture(ph[1], p["alts"][1], "(min-width: 960px) 20vw, 40vw")}</div>'
                      f'<div class="ph">{picture(ph[2], p["alts"][2], "(min-width: 960px) 20vw, 40vw")}</div></div>')
        else:  # two landscape photos, stacked
            photos = ('<div class="story-photos story-photos--2">' + "".join(
                f'<div class="ph">{picture(n, a, "(min-width: 960px) 45vw, 100vw")}</div>' for n, a in zip(ph, p["alts"])) + '</div>')
        badges = "".join(f'<span class="badge badge--public">{esc(b)}</span>' for b in p["badges"])
        sections = "".join(f'<h3>{esc(s["h"])}</h3>' + "".join(f"<p>{esc(x)}</p>" for x in s["p"]) for s in p["sections"])
        vids = []
        if p.get("interview"):
            vids.append(video(p["interview"], "Full interview", p["name"]))
        if p.get("highlight"):
            vids.append(video(p["highlight"], "Highlight reel", p["name"]))
        vids_html = f'<div class="videos {"videos--2" if len(vids) > 1 else ""} mt-m">{"".join(vids)}</div>' if vids else ""
        stats = "".join(f'<div class="stat"><b>{esc(s["n"])}</b><span>{esc(s["l"])}</span></div>' for s in p["stats"])
        career = "".join(f'<li><strong>{esc(c["club"])}</strong><span class="lvl">{esc(c["level"])}</span><p>{esc(c["detail"])}</p></li>' for c in p["career"])
        honours = "".join(f"<li>{esc(h)}</li>" for h in p["honours"])
        facts = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in p["facts"])
        resume = (f'<a class="link-arrow" href="{p["resume"]}" target="_blank" rel="noopener">Download player résumé (PDF) <span class="arrow" aria-hidden="true">&rarr;</span></a>'
                  if p.get("resume") else "")
        out.append(f'''<article class="story" id="{p["id"]}" aria-labelledby="{p["id"]}-name">
  <div class="wrap">
    <div class="story-head">
      <div class="reveal">
        <div class="story-kicker">{badges}</div>
        <h2 class="display" id="{p["id"]}-name">{esc(p["name"])}</h2>
        <p class="pos small mt-s">{esc(p["position"])} · {esc(p["origin"])}</p>
        <blockquote class="serif-quote pull">&ldquo;{esc(p["quote"])}&rdquo;</blockquote>
      </div>
      <div class="reveal d1">{photos}</div>
    </div>
    <div class="story-body">
      <div>
        <div class="prose">{sections}</div>
        {vids_html}
      </div>
      <aside class="story-aside" aria-label="{esc(p["name"])} at a glance">
        <div class="stats-row">{stats}</div>
        <div class="aside-block"><h4>Career path</h4><ol class="timeline">{career}</ol></div>
        <div class="aside-block"><h4>Honours</h4><ul class="honours">{honours}</ul></div>
        <div class="aside-block"><h4>Player info</h4><dl class="facts">{facts}</dl><p class="as-of mt-s">{esc(p["as_of"])}</p></div>
        <div class="btn-row">
          <a class="btn btn--dark btn--sm" href="/partners/?type=club#inquiry">Clubs: ask about {esc(p["first"])}</a>
          {resume}
        </div>
      </aside>
    </div>
  </div>
</article>''')
    return "\n".join(out)


def story_index():
    return '<nav class="story-index" aria-label="Stories on this page">' + "".join(
        f'<a href="#{p["id"]}">{esc(p["name"])}</a>' for p in PLAYERS) + "</nav>"


def resources():
    out = []
    for c in RESOURCES["categories"]:
        items = []
        for it in c["items"]:
            badge = ('<span class="badge badge--now">Verified partner</span>' if it["status"] == "partner"
                     else '<span class="badge badge--public">Public resource</span>')
            items.append(f'''<div class="res"><div class="res-top"><h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it["name"])}</a></h3>{badge}</div><p>{esc(it["desc"])}</p></div>''')
        if not any(it["status"] == "partner" for it in c["items"]):
            items.append(f'''<div class="empty"><p>We are building verified listings for this category. Organizations are added after we confirm their services and agree to work together.</p><a class="link-arrow" href="#suggest">Suggest a resource <span class="arrow" aria-hidden="true">&rarr;</span></a></div>''')
        out.append(f'''<section class="dir-cat" id="{c["id"]}" aria-labelledby="{c["id"]}-h">
  <div><h2 class="h3" id="{c["id"]}-h">{esc(c["title"])}</h2><p class="mt-s">{esc(c["intro"])}</p></div>
  <div class="dir-list">{"".join(items)}</div>
</section>''')
    return "\n".join(out)


def resource_nav():
    return '<nav class="dir-nav" aria-label="Resource categories">' + "".join(
        f'<a href="#{c["id"]}">{esc(c["title"])}</a>' for c in RESOURCES["categories"]) + "</nav>"


BLOCKS = {
    "players_cards": player_cards,
    "stories": stories,
    "story_index": story_index,
    "resources": resources,
    "resource_nav": resource_nav,
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


def render(page_path):
    raw = page_path.read_text()
    m = re.match(r"\s*<!--meta\s+(\{.*?\})\s*-->\s*", raw, re.S)
    if not m:
        raise SystemExit(f"{page_path.name}: missing <!--meta {{...}} --> header")
    meta = json.loads(m.group(1))
    body = raw[m.end():]

    body = re.sub(r"\{\{picture\s+(.*?)\}\}", picture_directive, body, flags=re.S)
    for key, fn in BLOCKS.items():
        if "{{" + key + "}}" in body:
            body = body.replace("{{" + key + "}}", fn())
    body = (body.replace("{{donate_url}}", DONATE_URL)
                .replace("{{formspree}}", FORMSPREE))

    active = meta.get("nav", "")
    cur = ' aria-current="page"'
    nav = "\n".join(
        f'        <li><a href="{href}"{cur if key == active else ""}>{label}</a></li>'
        for key, href, label in NAV)
    mnav = "\n".join(
        f'        <li><a class="mm-link" href="{href}"{cur if key == active else ""}>{label}</a></li>'
        for key, href, label in NAV)

    title = meta["title"]
    full_title = title if "91st" in title else f"{title} | The 91st Foundation"
    jsonld = ""
    if meta.get("path") == "/":
        jsonld = '<script type="application/ld+json">' + json.dumps(JSONLD_ORG) + "</script>"

    layout = (SRC / "layout.html").read_text()
    out = (layout.replace("{{content}}", body)
                 .replace("{{title}}", esc(full_title))
                 .replace("{{og_title}}", esc(meta.get("og_title", full_title)))
                 .replace("{{description}}", esc(meta["description"]))
                 .replace("{{canonical}}", SITE + meta["path"])
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
        raise SystemExit(f"{page_path.name}: unresolved placeholders {leftover}")

    p = meta["path"]
    dest = ROOT / ("404.html" if p == "/404.html" else (p.strip("/") + "/index.html" if p != "/" else "index.html"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return meta


def main():
    metas = [render(p) for p in sorted((SRC / "pages").glob("*.html"))]
    urls = [m for m in metas if not m.get("noindex")]
    today = time.strftime("%Y-%m-%d")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for m in sorted(urls, key=lambda x: (x["path"] != "/", x["path"])):
        sm.append(f"  <url><loc>{SITE}{m['path']}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"Built {len(metas)} pages.")


if __name__ == "__main__":
    main()
