"""Validate generated SEO and crawl discovery; exits nonzero on failure."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, urljoin, unquote
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from search_discovery import BASE, posts_from, newest


class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.canon=[]; self.cards=[]; self.meta={}
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if d.get('href'): self.links.append(d['href'])
        if d.get('src'): self.links.append(d['src'])
        if tag=='link' and d.get('rel')=='canonical': self.canon.append(d['href'])
        if tag=='a' and d.get('class')=='post': self.cards.append(d['href'])
        if tag=='meta': self.meta[d.get('name',d.get('property',''))]=d.get('content','')


def check(root):
    posts=posts_from(root); html_files=sorted(root.rglob('*.html')); urls=set(); parsed={}
    for p in html_files:
        rel=p.relative_to(root).as_posix(); url=BASE if rel=='index.html' else BASE+rel; urls.add(url)
        text=p.read_text(encoding='utf-8'); page=Page();page.feed(text);parsed[rel]=page
        assert page.canon==[url], rel
        assert page.meta.get('description') and page.meta.get('og:url')==url, rel
        assert 'noindex' not in page.meta.get('robots','').lower(),rel
        for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S):json.loads(script)
        for link in page.links:
            full=urljoin(url,link)
            if full.startswith(BASE):
                path=unquote(urlsplit(full).path[len(urlsplit(BASE).path):]) or 'index.html'
                assert (root/path).is_file(),(rel,path)
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap=[n.text for n in ET.parse(root/'sitemap.xml').findall('s:url/s:loc',ns)]
    assert len(sitemap)==len(set(sitemap)) and set(sitemap)==urls
    feed=ET.parse(root/'feed.xml'); items=feed.findall('channel/item')
    assert [i.findtext('link') for i in items]==[BASE+p['url'] for p in newest(posts)[:50]]
    assert parsed['index.html'].cards==[BASE+p['url'] for p in newest(posts)[:5]]
    for name in ['news','theory','concepts']:assert len(parsed[name+'.html'].cards)==10
    # Walk real anchor links from the homepage without evaluating JavaScript.
    pending=['index.html']; seen=set()
    while pending:
        rel=pending.pop()
        if rel in seen:continue
        seen.add(rel);url=BASE if rel=='index.html' else BASE+rel
        for link in parsed[rel].links:
            full=urljoin(url,link)
            if full.startswith(BASE):
                child=unquote(urlsplit(full).path[len(urlsplit(BASE).path):]) or 'index.html'
                if child in parsed:pending.append(child)
    assert {p['url'] for p in posts}<=seen, 'Some posts cannot be found without JS'
    for rel,page in parsed.items():
        if rel.startswith('archive/') and rel!='archive/index.html':assert 1<=len(page.cards)<=10
    return {'status':'PASS','posts':len(posts),'html_pages':len(html_files),'crawl_reachable_pages':len(seen),'rss_items':len(items)}


if __name__=='__main__':
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'_site'
    print(json.dumps(check(root)))
