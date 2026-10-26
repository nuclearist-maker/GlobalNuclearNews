"""Publish English posts from the writing folders into this GitHub Pages site.

Sources (see tools/publish_sources.json):
  theory   -> G:/내 드라이브/My_Claude/Blog-Nuclear/output-EN/<post>/web/
  news     -> G:/내 드라이브/My_Claude/Blog/output/drafts_EN/<post>/web/
  concepts -> G:/내 드라이브/My_Claude/Blog-Nuclear/output-pe-EN/<post>/web/
  history  -> G:/내 드라이브/My_Claude/Blog-Nuclear/output-history/<post>/web/

Each post folder publishes only when it contains a web/ package:
  web/post.json      metadata; "status": "ready" to publish ("draft" = skip)
  web/article.html   article body (everything after the title header); images
                     are referenced by bare file name, e.g. src="fig1.png"
  web/<images>       every image the article uses, plus the thumbnail
  web/extra_head.html (optional) extra <style> for the page head

For every ready package the script writes posts/<section>/<slug>.html, copies the
images to assets/images/<section>/<slug>/, rebuilds the posts list in
assets/app.js, and checks that every linked file exists (tools/build_en_site.py).

Usage (run from anywhere):
  python tools/publish_en_posts.py            # update the working tree, report
  python tools/publish_en_posts.py --push     # ... then commit and push to main
  python tools/publish_en_posts.py --check    # validate packages only, write nothing
  python tools/publish_en_posts.py --only theory --push   # publish one board only
  python tools/publish_en_posts.py --prune    # also remove site posts whose
                                              # source package no longer exists
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = {"news": ("news.html", "← Global Nuclear News"),
            "theory": ("theory.html", "← Nuclear Theory"),
            "concepts": ("concepts.html", "← Concept Dictionary"),
            "history": ("history.html", "← Nuclear History")}
NAV_LABELS = {"news": "Global Nuclear News", "theory": "Nuclear Theory", "concepts": "Concept Dictionary", "history": "Nuclear History"}
REQUIRED = ["status", "section", "slug", "title", "page_title", "description", "eyebrow",
            "subtitle", "date", "category", "summary", "list_title", "thumbnail",
            "thumbnailAlt", "keywords"]
ASSET_V = "20261025-en2"
IMG_RE = re.compile(r'(src|href)="([^"/\\:#?]+\.(?:png|jpe?g|webp|gif|svg))"', re.I)
KOREAN = re.compile(r"[\uac00-\ud7a3]")

BRAND = ('<a class="brand" href="../../index.html" aria-label="GlobalNuclearNews home">'
         '<span class="brand-mark" aria-hidden="true">GN</span><span><strong>GlobalNuclearNews</strong>'
         '<small>GLOBAL NUCLEAR INTELLIGENCE</small></span></a>')


def nav(section: str) -> str:
    def a(s: str, label: str) -> str:
        cls = ' class="active"' if s == section else ""
        return f'<a{cls} href="../../{SECTIONS[s][0]}">{label}</a>'
    return '<nav aria-label="Main menu">' + "".join(a(s, NAV_LABELS[s]) for s in SECTIONS) + '<a href="../../reactors.html">Reactor Data</a></nav>'


def load_packages(errors: list[str]) -> list[dict]:
    cfg = json.loads((ROOT / "tools" / "publish_sources.json").read_text(encoding="utf-8"))
    pkgs, slugs = [], set()
    for section, src in cfg.items():
        base = Path(src)
        if not base.is_dir():
            errors.append(f"source folder missing: {base}")
            continue
        for meta_path in sorted(base.glob("*/web/post.json")):
            web = meta_path.parent
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"{meta_path}: bad JSON ({e})")
                continue
            if meta.get("status") != "ready":
                print(f"  skip (status={meta.get('status')!r}): {web.parent.name}")
                continue
            where = f"{web.parent.name}"
            missing = [k for k in REQUIRED if not str(meta.get(k, "")).strip()]
            if missing:
                errors.append(f"{where}: post.json missing {missing}")
                continue
            if meta["section"] != section:
                errors.append(f"{where}: section {meta['section']!r} but found under the {section} source")
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", meta["slug"]):
                errors.append(f"{where}: slug must be lowercase letters, digits and hyphens")
            if not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", meta["date"]):
                errors.append(f"{where}: date must be YYYY.MM.DD")
            if meta["slug"] in slugs:
                errors.append(f"{where}: duplicate slug {meta['slug']}")
            slugs.add(meta["slug"])
            article = web / "article.html"
            if not article.is_file():
                errors.append(f"{where}: web/article.html missing")
                continue
            body = article.read_text(encoding="utf-8")
            extra = web / "extra_head.html"
            head = extra.read_text(encoding="utf-8") if extra.is_file() else ""
            images = {m.group(2) for m in IMG_RE.finditer(body)} | {meta["thumbnail"]}
            for name in sorted(images):
                if not (web / name).is_file():
                    errors.append(f"{where}: image {name} referenced but not in web/")
            text = json.dumps(meta, ensure_ascii=False) + body + head
            if KOREAN.search(text):
                errors.append(f"{where}: Korean characters found (site is English-only)")
            pkgs.append(dict(meta=meta, web=web, body=body, head=head, images=sorted(images),
                             folder=web.parent.name, source=section))
    return pkgs


def render(p: dict) -> str:
    m, sec = p["meta"], p["meta"]["section"]
    e = lambda k: html.escape(m[k], quote=True)
    img_base = f"../../assets/images/{sec}/{m['slug']}/"
    body = IMG_RE.sub(lambda g: f'{g.group(1)}="{img_base}{site_name(g.group(2))}"', p["body"]).strip()
    note = f"<span>{e('byline_note')}</span>" if m.get("byline_note") else ""
    date = f'<span>{e("date")}</span>' if sec == "news" else ""
    board, back = SECTIONS[sec]
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{e("description")}"><title>{e("page_title")} | GlobalNuclearNews</title>'
        f'<link rel="stylesheet" href="../../assets/styles.css?v={ASSET_V}">'
        f'<link rel="stylesheet" href="../../assets/article.css?v={ASSET_V}">{p["head"].strip()}</head>\n'
        f'<body><header class="masthead">{BRAND}{nav(sec)}</header>\n'
        f'<main class="article"><a class="back" href="../../{board}">{back}</a><article><header>'
        f'<p class="eyebrow">{e("eyebrow")}</p><h1>{e("title")}</h1><p class="subtitle">{e("subtitle")}</p>'
        f'<div class="byline">{date}{note}</div></header>\n{body}\n</article></main>\n'
        '<footer><span>© 2026 GlobalNuclearNews</span><span>Independent nuclear industry briefing</span></footer>'
        '</body></html>\n')


WEBP_QUALITY = 85


def site_name(name: str) -> str:
    """Raster images are published as WebP (keeps the site well under the Pages size limit)."""
    stem, dot, ext = name.rpartition(".")
    return f"{stem}.webp" if ext.lower() in ("png", "jpg", "jpeg") else name


def publish_image(src: Path, dst: Path) -> bool:
    """Write dst from src (converting to WebP when needed) if dst is missing or older than src."""
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix == ".webp" and src.suffix.lower() != ".webp":
        from PIL import Image
        with Image.open(src) as im:
            im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
            im.save(dst, "WEBP", quality=WEBP_QUALITY, method=6)
    else:
        shutil.copy2(src, dst)
    return True


def write_if_changed(path: Path, data: bytes) -> bool:
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def update_app_js(pkgs: list[dict]) -> bool:
    app = ROOT / "assets" / "app.js"
    src = app.read_text(encoding="utf-8")
    previous = json.JSONDecoder().raw_decode(src.split("const posts = ", 1)[1])[0]
    published = {p['url']: p.get('publishedAt', '') for p in previous}
    published_now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    entries = []
    for p in sorted(pkgs, key=lambda p: (p["meta"]["date"], p["meta"]["slug"]), reverse=True):
        m = p["meta"]
        entries.append({
            "title": m["list_title"], "date": m["date"], "displayDate": m["date"],
            "publishedAt": published.get(f"posts/{m['section']}/{m['slug']}.html", published_now),
            "section": m["section"], "category": m["category"], "summary": m["summary"],
            "thumbnail": f"assets/images/{m['section']}/{m['slug']}/{site_name(m['thumbnail'])}",
            "thumbnailAlt": m["thumbnailAlt"], "url": f"posts/{m['section']}/{m['slug']}.html",
            "keywords": m["keywords"]})
    head, sep, rest = src.partition("const posts = [")
    _, sep2, tail = rest.partition("\n];\n")
    if not sep or not sep2:
        raise SystemExit("assets/app.js: cannot find the 'const posts = [ ... ];' block")
    array = json.dumps(entries, ensure_ascii=False, indent=2)[1:-1].strip("\n")
    new = f"{head}const posts = [\n{array}\n];\n{tail}"
    return write_if_changed(app, new.encode("utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--push", action="store_true", help="commit the site changes and push to origin/main")
    ap.add_argument("--prune", action="store_true", help="delete site posts with no source package")
    ap.add_argument("--check", action="store_true", help="only validate the source packages; write nothing")
    ap.add_argument("--only", choices=sorted(SECTIONS), help="publish new/changed posts of this board only; "
                    "posts of the other board stay as they are on the site")
    ap.add_argument("--range", metavar="LO-HI", help="with --only theory: publish only slugs numbered LO..HI "
                    "(e.g. 1-50); other unpublished theory posts are held back")
    ap.add_argument("--match", metavar="REGEX", help="publish only new posts whose source folder name matches "
                    "REGEX (e.g. '^C-FM-'); other unpublished posts are held back")
    args = ap.parse_args()

    errors: list[str] = []
    print("Scanning source folders ...")
    pkgs = load_packages(errors)
    # Problems in packages that this run would hold back anyway (other board with --only,
    # outside --range) are reported but do not block publishing the requested posts.
    sources = json.loads((ROOT / "tools" / "publish_sources.json").read_text(encoding="utf-8"))
    folder_section = {d.name: sec for sec, src in sources.items() if Path(src).is_dir()
                      for d in Path(src).iterdir() if d.is_dir()}

    def in_scope(err: str) -> bool:
        folder = err.split(":", 1)[0].strip()
        if args.only and folder in folder_section and folder_section[folder] != args.only:
            return False
        if args.match and folder in folder_section and not re.search(args.match, folder):
            return False
        if args.range and re.match(r"\d{3}_", folder):
            lo, hi = (int(x) for x in args.range.split("-"))
            return lo <= int(folder[:3]) <= hi
        return True
    held_errors = [e for e in errors if not in_scope(e)]
    errors = [e for e in errors if in_scope(e)]
    for e in held_errors:
        print("  note (out of scope, not blocking):", e)
    if errors:
        print("\nBLOCKED — fix these and run again:")
        for e in errors:
            print("  -", e)
        return 1
    if args.check:
        print(f"OK: {len(pkgs)} ready package(s) are valid (nothing written).")
        return 0
    if args.only:
        # Keep the other board exactly as published: only its already-live posts stay in the list.
        held = [p for p in pkgs if p["meta"]["section"] != args.only
                and not (ROOT / "posts" / p["meta"]["section"] / f"{p['meta']['slug']}.html").exists()]
        if held:
            print(f"  --only {args.only}: holding back {len(held)} unpublished post(s) of the other board")
        pkgs = [p for p in pkgs if p not in held]
    if args.match:
        held = [p for p in pkgs if not re.search(args.match, p["folder"])
                and not (ROOT / "posts" / p["meta"]["section"] / f"{p['meta']['slug']}.html").exists()]
        if held:
            print(f"  --match {args.match}: holding back {len(held)} unpublished post(s)")
        pkgs = [p for p in pkgs if p not in held]
    if args.range:
        lo, hi = (int(x) for x in args.range.split("-"))
        def out_of_range(p):
            m = p["meta"]
            num = m["slug"].split("-")[0]
            live = (ROOT / "posts" / m["section"] / f"{m['slug']}.html").exists()
            return (m["section"] == "theory" and not live
                    and not (num.isdigit() and lo <= int(num) <= hi))
        held = [p for p in pkgs if out_of_range(p)]
        if held:
            print(f"  --range {args.range}: holding back {len(held)} theory post(s) outside the range")
        pkgs = [p for p in pkgs if p not in held]

    changed = []
    for p in pkgs:
        m = p["meta"]
        sec, slug = m["section"], m["slug"]
        page = ROOT / "posts" / sec / f"{slug}.html"
        new = not page.exists()
        touched = write_if_changed(page, render(p).encode("utf-8"))
        img_dir = ROOT / "assets" / "images" / sec / slug
        img_dir.mkdir(parents=True, exist_ok=True)
        wanted = {site_name(n) for n in p["images"]}
        for name in p["images"]:
            if publish_image(p["web"] / name, img_dir / site_name(name)):
                touched = True
        for stale in img_dir.iterdir():
            if stale.is_dir():
                shutil.rmtree(stale)
                touched = True
            elif stale.name not in wanted:
                stale.unlink()
                touched = True
        if touched:
            changed.append(("NEW" if new else "UPDATED", sec, slug, m["list_title"]))

    keep = {(p["meta"]["section"], p["meta"]["slug"]) for p in pkgs}
    orphans = [(sec, f.stem) for sec in SECTIONS for f in (ROOT / "posts" / sec).glob("*.html")
               if (sec, f.stem) not in keep]
    for sec, slug in orphans:
        if args.prune:
            (ROOT / "posts" / sec / f"{slug}.html").unlink()
            shutil.rmtree(ROOT / "assets" / "images" / sec / slug, ignore_errors=True)
            changed.append(("REMOVED", sec, slug, ""))
        else:
            print(f"  note: site post without a source package (kept; use --prune to remove): posts/{sec}/{slug}.html")

    if update_app_js(pkgs):  # the board lists exactly the ready packages
        changed.append(("LIST", "-", "assets/app.js", "post list rebuilt"))

    # Link check: package the public site exactly as the Pages workflow does.
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_en_site.py")], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        print("BLOCKED — the site build failed (missing linked file?). Nothing was pushed.")
        return 1
    print(r.stdout.splitlines()[0])

    print(f"\n{len(pkgs)} ready post(s) in sources.")
    if not changed:
        print("Site is already up to date.")
        return 0
    for kind, sec, slug, title in changed:
        print(f"  {kind:8} {sec:8} {slug}  {title}")

    if not args.push:
        print("\nWorking tree updated. Run again with --push to commit and publish.")
        return 0

    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, check=True)
    git("add", "-A", "posts", "assets")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        print("Nothing to commit.")
        return 0
    items = [f"{k.lower()} {s}" for k, sec, s, _ in changed if k != "LIST"]
    msg = "Publish English posts: " + ", ".join(items) if items else "Refresh English post list"
    git("commit", "-m", msg + "\n\nGenerated by tools/publish_en_posts.py")
    git("pull", "--rebase", "origin", "main")
    git("push", "origin", "HEAD:main")
    print("Pushed. GitHub Pages will redeploy in about a minute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
