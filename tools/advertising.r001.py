"""Install and validate the owner's AdSense code in generated public pages."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

from search_discovery import content_html_files

CLIENT = "ca-pub-4448806184780595"
SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + CLIENT
CODE = f'<script async src="{SRC}" crossorigin="anonymous"></script>'


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.heads = self.ends = 0
        self.ads = []

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.heads += 1
            self.in_head = True
        if tag == "script" and any("adsbygoogle.js" in (v or "") for k, v in attrs if k == "src"):
            self.ads.append((attrs, self.in_head))

    def handle_endtag(self, tag):
        if tag == "head":
            self.ends += 1
            self.in_head = False


def inspect(text):
    page = Scripts()
    page.feed(text)
    if page.heads != 1 or page.ends != 1:
        raise ValueError("Expected exactly one complete head element")
    return page


def validate(text):
    page = inspect(text)
    if len(page.ads) != 1:
        raise ValueError("Expected exactly one AdSense script")
    attrs, in_head = page.ads[0]
    if not in_head or len(attrs) != 3 or dict(attrs) != {"async": None, "src": SRC, "crossorigin": "anonymous"}:
        raise ValueError("Incorrect AdSense placement, publisher or attributes")


def add_code(text):
    page = inspect(text)
    if not page.ads:
        text = re.sub(r"</head\s*>", lambda m: CODE + "\n" + m[0], text, count=1, flags=re.I)
    validate(text)
    return text


def install(root):
    pages = content_html_files(root)
    for path in pages:
        text = path.read_text(encoding="utf-8")
        updated = add_code(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
    return check(root)


def check(root):
    pages = content_html_files(root)
    if not pages:
        raise ValueError("No public content pages")
    for path in pages:
        try:
            validate(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ValueError(f"{path}: {error}") from error
    return {"status": "PASS", "pages": len(pages), "client": CLIENT}


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "_site"
    print(json.dumps(check(root)))
