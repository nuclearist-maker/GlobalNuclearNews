"""Build search metadata and ordinary HTML discovery links from public posts only."""
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

BASE = "https://nuclearist-maker.github.io/GlobalNuclearNews/"
SECTIONS = {"news": "Global Nuclear News", "theory": "Nuclear Theory", "concepts": "Concept Dictionary", "history": "Nuclear History"}
ESC = html.escape


def content_html_files(root):
    """Validate root ownership tokens; return only pages that need SEO metadata."""
    pages = []
    for p in sorted(root.rglob("*.html")):
        if p.parent == root and re.fullmatch(r"google[0-9a-f]{16}\.html", p.name):
            expected = ("google-site-verification: " + p.name).encode("ascii")
            if p.read_bytes() not in (expected, expected + b"\n", expected + b"\r\n"):
                raise ValueError("Invalid Google ownership file: " + p.name)
            # Never rewrite these bytes or include the token in the sitemap.
            continue
        pages.append(p)
    return pages


def posts_from(root):
    text = (root / "assets/app.js").read_text(encoding="utf-8-sig")
    data, _ = json.JSONDecoder().raw_decode(text.split("const posts = ", 1)[1])
    urls = [p["url"] for p in data]
    if len(urls) != len(set(urls)):
        raise ValueError("Duplicate post URLs")
    for p in data:
        target = (root / p["url"]).resolve()
        if not target.is_relative_to((root / "posts").resolve()) or not target.is_file():
            raise ValueError("Invalid public post: " + p["url"])
    return data


def newest(posts):
    return sorted(posts, key=lambda p: (p["date"], p.get("publishedAt", "")), reverse=True)


def cards(posts, home=False):
    return "".join(
        f'<a class="post" href="{BASE}{ESC(p["url"])}">'
        f'<img class="post-thumb" src="{BASE}{ESC(p["thumbnail"])}" alt="{ESC(p["thumbnailAlt"])}">'
        f'<div class="post-copy"><div class="post-meta"><strong>{ESC(SECTIONS.get(p["section"], p["section"])) + " · " if home else ""}{ESC(p["category"])}</strong>'
        f'{ESC(p["displayDate"]) if p["section"] == "news" else ""}</div>'
        f'<h3>{ESC(p["title"])}</h3><p>{ESC(p["summary"])}</p></div>'
        '<span class="arrow" aria-hidden="true">→</span></a>' for p in posts)


class Head(HTMLParser):
    def __init__(self):
        super().__init__(); self.title = ""; self.description = ""; self.in_title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title": self.in_title = True
        if tag == "meta" and d.get("name") == "description": self.description = d.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False

    def handle_data(self, data):
        if self.in_title: self.title += data


def metadata(text, relative, post, verification):
    # Own marked block makes repeated enrichment deterministic.
    text = re.sub(r"<!-- search-discovery:start -->.*?<!-- search-discovery:end -->", "", text, flags=re.S)
    head = Head(); head.feed(text.split("</head>", 1)[0])
    if not head.title or not head.description:
        raise ValueError("Missing title/description: " + relative)
    url = BASE if relative == "index.html" else BASE + relative
    picture = BASE + (post["thumbnail"] if post else "assets/images/global-nuclear-future-hero-v2.png")
    tags = [f'<link rel="canonical" href="{ESC(url)}">',
            f'<link rel="alternate" type="application/rss+xml" title="GlobalNuclearNews" href="{BASE}feed.xml">']
    for name, content in {"og:title": head.title, "og:description": head.description, "og:url": url,
                          "og:site_name": "GlobalNuclearNews", "og:type": "article" if post else "website",
                          "og:image": picture, "og:locale": "en_US"}.items():
        tags.append(f'<meta property="{name}" content="{ESC(content)}">')
    tags.append('<meta name="twitter:card" content="summary_large_image">')
    schema = None
    if post:
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": post["title"],
                  "description": head.description, "mainEntityOfPage": url, "url": url, "image": picture,
                  "inLanguage": "en", "publisher": {"@type": "Organization", "name": "GlobalNuclearNews"}}
        if post["section"] == "news": schema["datePublished"] = post["date"].replace(".", "-")
    elif relative == "index.html":
        schema = {"@context": "https://schema.org", "@type": "WebSite", "name": "GlobalNuclearNews", "url": BASE, "inLanguage": "en"}
        for name, token in verification.items():
            if name not in {"google-site-verification", "naver-site-verification", "msvalidate.01"} or not token:
                raise ValueError("Unsupported or empty verification token")
            tags.append(f'<meta name="{name}" content="{ESC(token)}">')
    if schema:
        data = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
        tags.append(f'<script type="application/ld+json">{data}</script>')
    block = "<!-- search-discovery:start -->\n" + "\n".join(tags) + "\n<!-- search-discovery:end -->"
    return text.replace("</head>", block + "</head>", 1)


def archive_page(title, description, content):
    menu = " · ".join(f'<a href="{BASE}{s}.html">{label}</a>' for s, label in SECTIONS.items())
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{ESC(title)} | GlobalNuclearNews</title><meta name="description" content="{ESC(description)}">'
            f'<link rel="stylesheet" href="{BASE}assets/styles.css"></head><body>'
            f'<header class="masthead"><a class="brand" href="{BASE}">GlobalNuclearNews</a></header>'
            f'<main><section class="board"><nav aria-label="Sections">{menu}</nav><h1>{ESC(title)}</h1>{content}</section></main>'
            f'<footer><a href="{BASE}archive/index.html">Article archive</a><a href="{BASE}">Home</a></footer></body></html>')


def board_order(section, posts):
    if section == "concepts": return sorted(posts, key=lambda p: p["title"].casefold())
    if section == "history": return sorted(posts, key=lambda p: p["url"])
    return newest(posts)


def enrich(root, config):
    posts = posts_from(root)
    postmap = {p["url"]: p for p in posts}
    verification = config.get("verification", {})
    key = config["indexnow_key"]
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key): raise ValueError("Invalid IndexNow key")
    archive = root / "archive"; archive.mkdir(exist_ok=True)
    archive_links = []
    for section, label in SECTIONS.items():
        selected = [p for p in posts if p["section"] == section]
        selected = board_order(section, selected)
        total = (len(selected) + 9) // 10
        for n in range(1, total + 1):
            links = []
            if n > 1: links.append(f'<a href="{section}-{n-1}.html" rel="prev">Previous</a>')
            for i in range(1, total + 1):
                current = ' aria-current="page"' if i == n else ''
                links.append(f'<a href="{section}-{i}.html"{current}>{i}</a>')
            if n < total: links.append(f'<a href="{section}-{n+1}.html" rel="next">Next</a>')
            paging = '<nav class="pagination" aria-label="Archive pages" style="gap:16px">' + " ".join(links) + '</nav>'
            title = f"{label} archive — page {n}"
            content = '<div class="post-list">' + cards(selected[(n-1)*10:n*10]) + '</div>' + paging
            (archive / f"{section}-{n}.html").write_text(archive_page(title, f"Browse {label} articles, page {n} of {total}.", content), encoding="utf-8")
        if total: archive_links.append(f'<li><a href="{section}-1.html">{label}: {len(selected)} articles</a></li>')
    (archive / "index.html").write_text(archive_page("Article archive", "Browse all nuclear news, theory lessons, concept dictionary entries and nuclear history articles.", '<ul>' + ''.join(archive_links) + '</ul>'), encoding="utf-8")
    for name in ["index", *SECTIONS]:
        p = root / f"{name}.html"; text = p.read_text(encoding="utf-8")
        if name == 'index':
            board_links = ''.join(f'<a href="{section}.html">{ESC(label)} →</a>' for section, label in SECTIONS.items())
            text = re.sub(r'<p class="browse-all">.*?</p>', '<p class="browse-all">' + board_links + '</p>', text, flags=re.S)
            board_filters = '<button class="selected" type="button" data-filter="All">All</button>' + ''.join(f'<button type="button" data-filter="{section}">{ESC(label)}</button>' for section, label in SECTIONS.items())
            text = re.sub(r'(<div class="filters"[^>]*>).*?(</div>)', lambda m: m[1] + board_filters + m[2], text, flags=re.S)
        selected = newest(posts)[:5] if name == "index" else [x for x in posts if x["section"] == name]
        if name != "index": selected = board_order(name, selected)[:10]
        text = text.replace('<div id="post-list" class="post-list" aria-live="polite"></div>', '<div id="post-list" class="post-list" aria-live="polite">' + cards(selected, home=name == 'index') + '</div>')
        if 'data-discovery-links' not in text:
            links = f'<span data-discovery-links><a href="{BASE}archive/index.html">Article archive</a> · <a href="{BASE}sitemap.xml">Sitemap</a> · <a href="{BASE}feed.xml">RSS</a></span>'
            text = text.replace('</footer>', links + '</footer>', 1)
        p.write_text(text, encoding="utf-8")
    html_files = content_html_files(root)
    for p in html_files:
        rel = p.relative_to(root).as_posix()
        p.write_text(metadata(p.read_text(encoding="utf-8"), rel, postmap.get(rel), verification), encoding="utf-8")
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    sitemap = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for p in html_files:
        rel = p.relative_to(root).as_posix()
        item = ET.SubElement(sitemap, 'url'); ET.SubElement(item, 'loc').text = BASE if rel == 'index.html' else BASE + rel
    ET.indent(sitemap, space='  ')
    ET.ElementTree(sitemap).write(root / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    rss = ET.Element('rss', version='2.0'); channel = ET.SubElement(rss, 'channel')
    for tag, val in {'title': 'GlobalNuclearNews', 'link': BASE, 'description': 'Nuclear news, theory and concepts.', 'language': 'en'}.items(): ET.SubElement(channel, tag).text = val
    for p in newest(posts)[:50]:
        item = ET.SubElement(channel, 'item')
        for tag, val in {'title': p['title'], 'link': BASE + p['url'], 'description': p['summary'], 'guid': BASE + p['url']}.items(): ET.SubElement(item, tag).text = val
    ET.indent(rss, space='  ')
    ET.ElementTree(rss).write(root / 'feed.xml', encoding='utf-8', xml_declaration=True)
    (root / f'{key}.txt').write_text(key, encoding='utf-8')
    return {'posts': len(posts), 'sitemap_urls': len(html_files), 'archive_pages': len(list(archive.glob('*.html')))}
