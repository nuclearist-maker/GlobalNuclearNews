"""Detect recurring Korean numeric-spacing defects in publishable news text.

This is a focused regression gate, not a full Korean grammar checker. Review
compound nouns manually. Preserve identifiers, dates, counters and source URLs.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re

RULES = [
    ('hangul_number', re.compile(r'(?<=[가-힣])\d')),
    ('number_unit', re.compile(r'\d(?:mSv|mrem|Sv|rem|km|cm|mm|kWh|MWh|GWh|MW|GW|kW|kg)(?![A-Za-z])')),
    ('sentence_gap', re.compile(r'[가-힣][.!?](?=[가-힣A-Za-z0-9])')),
    ('comma_gap', re.compile(r'[가-힣%],(?=[가-힣A-Za-z0-9])')),
]

def text_errors(text):
    # Opaque identifiers and hyperlinks must not be reformatted as prose.
    text = re.sub(r'https?://\S+|\b(?:AP\d+|U-\d+|SSR-\d+|NUREG-\d+|ML[A-Za-z0-9]+|SAND[\d-]+)\b', '', text)
    errors = []
    for rule, pattern in RULES:
        for m in pattern.finditer(text):
            # Numbered legal references are valid: 제1조, 제20조의2.
            if rule == 'hangul_number' and ((text[m.start()-1:m.start()]=='제' and re.match(r'\d+(?:조|항|호)',text[m.start():])) or (text[max(0,m.start()-2):m.start()]=='조의' and re.match(r'\d+(?:\s|$)',text[m.start():]))):
                continue
            errors.append({'rule':rule, 'context':text[max(0,m.start()-22):m.end()+35]})
    return errors

class TextBlocks(HTMLParser):
    breaks = {'p','h1','h2','h3','title','td','th','figcaption','li','div','section','header','footer','br'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks=[]; self.parts=[]; self.skip=0
    def flush(self):
        if self.parts: self.blocks.append(''.join(self.parts)); self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
        if self.skip: return
        if tag in self.breaks: self.flush()
        attrs=dict(attrs)
        for key in ('alt','title','aria-label'):
            if attrs.get(key): self.blocks.append(attrs[key])
        if tag=='meta' and attrs.get('name')=='description': self.blocks.append(attrs.get('content',''))
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1); return
        if not self.skip and tag in self.breaks: self.flush()
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def html_errors(path):
    parser=TextBlocks(); parser.feed(Path(path).read_text(encoding='utf-8-sig')); parser.flush()
    return [e for block in parser.blocks for e in text_errors(block)]

def site_errors(root):
    root=Path(root); errors=[]
    for p in sorted((root/'posts/news').glob('*.html')):
        errors.extend(dict(file=p.relative_to(root).as_posix(),**e) for e in html_errors(p))
    script=(root/'assets/app.js').read_text(encoding='utf-8-sig')
    posts,_=json.JSONDecoder().raw_decode(script[script.index('['):])
    for post in posts:
        if post.get('section')!='news': continue
        for key in ('title','summary','thumbnailAlt','keywords','category'):
            errors.extend(dict(file='assets/app.js',post=post.get('url'),field=key,**e) for e in text_errors(post.get(key,'')))
    return errors

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=ap.parse_args()
    errors=site_errors(args.root)
    print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))
