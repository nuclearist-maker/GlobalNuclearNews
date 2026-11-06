"""Import ONLY explicitly paired Korean final manuscripts into portable public inputs.

Local-only: python tools/import_korean.py --map <internal-source-map.json>
Requires beautifulsoup4, markdown-it-py and Pillow; CI uses the rendered inputs.
"""
from __future__ import annotations
import argparse, hashlib, html, io, json, re, shutil
from pathlib import Path
from urllib.parse import urlsplit, unquote
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE='/GlobalNuclearNews/'
def sha(p):
    b=p.read_bytes()
    if p.suffix.lower() in {'.html','.md','.json','.js','.css'}:b=b.replace(b'\r\n',b'\n')
    return hashlib.sha256(b).hexdigest()
def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def read(p):return p.read_text(encoding='utf-8-sig')
def plain(t):return BeautifulSoup(t,'html.parser').get_text(' ',strip=True)
MD=MarkdownIt('commonmark',{'html':True}).enable('table')

def markdown(text):
    text=re.sub(r'^---\s*\n.*?\n---\s*\n','',text,flags=re.S)
    text=re.split(r'^##\s*(?:추천 태그|태그|해시태그)\s*$',text,flags=re.M)[0]
    # Editorial image anchors become semantic figures, including wrapped captions.
    def fig(m):
        name=m[1].strip();caption=' '.join((m[2] or '').split()) or '본문 설명 그림'
        return '\n\n<figure class="article-image"><img src="'+html.escape(name,quote=True)+'" alt="'+html.escape(caption,quote=True)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>\n\n'
    text=re.sub(r'\[이미지\s*삽입\s*:\s*([^\]\s]+\.(?:png|jpg|jpeg|webp|svg|gif))\s*(?:[—–-]\s*([^\]]*))?\]',fig,text,flags=re.I)
    # Keep TeX delimiters intact across Markdown escape processing.
    formulas=[]
    def math(m):
        formulas.append(m[0]);return f'GNNMATHPLACEHOLDER{len(formulas)-1}END'
    text=re.sub(r'\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|(?<!\$)\$(?!\s)[^$\n]+?\$(?!\$)',math,text)
    result=MD.render(text)
    for i,f in enumerate(formulas):result=result.replace(f'GNNMATHPLACEHOLDER{i}END',html.escape(f))
    return result

def locate(base,name):
    value=unquote(urlsplit(name).path)
    if urlsplit(name).scheme or value.startswith('/') or '..' in Path(value).parts:
        raise ValueError('Nonportable image reference: '+name)
    paths=[base/value,base/'assets'/value,base.parent/value,base.parent/'figs'/value,base.parent/'images'/value,base/'figs'/value,base/'images'/value]
    existing=list(dict.fromkeys(p.resolve() for p in paths if p.is_file()))
    if not existing:
        # Some final manuscripts name an image under an explicit source subfolder.
        existing=[p for p in base.glob('*/'+Path(value).name) if p.is_file()]
    if not existing:raise ValueError(f'Missing Korean image {name} in {base}')
    if len(existing)>1 and len({sha(p) for p in existing})>1:raise ValueError(f'Ambiguous Korean image {name} in {base}')
    return existing[0]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--map',type=Path,required=True);args=ap.parse_args()
    pairs=json.loads(read(args.map));source=read(ROOT/'assets/app.js');posts=json.JSONDecoder().raw_decode(source.split('const posts = ',1)[1])[0]
    byurl={p['url']:p for p in posts};assert len(pairs)==len(byurl) and {r['url'] for r in pairs}==set(byurl)
    vocab=json.loads(read(ROOT/'locales/ko/ui.json'))|json.loads(read(ROOT/'locales/ko/categories.json'))
    records=[];evidence=[];jobs={};issues=[];errors=[]
    cache=args.map.parent/'import-cache';cache.mkdir(exist_ok=True)
    def prepare(row):
        if len(row['ko'])!=1:raise ValueError('Exactly one Korean final required: '+row['url'])
        src=Path(row['ko'][0]);ep=Path(row['en']);en=byurl[row['url']];sec=en['section'];slug=Path(row['url']).stem
        cachepath=cache/(slug+'.json')
        if cachepath.exists():
            c=json.loads(read(cachepath));out=ROOT/'locales/ko'/row['url']
            if c['source_sha256']==sha(src) and c['record']['en_sha256']==sha(ROOT/row['url']) and out.exists() and sha(out)==c['record']['ko_sha256']:
                records.append(c['record']);evidence.append(c['evidence'])
                for im in c['evidence']['images']:
                    if not im['shared']:jobs[ROOT/im['output']]=(Path(im['source']),'.thumb.' in im['output'],im['source_sha256'])
                return
        text=read(src);base=src.parent
        soup=BeautifulSoup(text if src.suffix=='.html' else markdown(text),'html.parser')
        if src.suffix=='.html':
            soup=BeautifulSoup(str(soup.select_one('main.article article')),'html.parser')
            for el in soup.select('article > header .eyebrow,article > header .subtitle,article > header .byline'):el.decompose()
            if soup.article:soup.article.unwrap()
        h=soup.find('h1')
        if not h:raise ValueError('Missing Korean heading: '+str(src))
        title=h.get_text(' ',strip=True);h.decompose()
        for el in soup.select('script,style,iframe,form'):el.decompose()
        if not re.search('[가-힣]',title):raise ValueError('Korean title required: '+str(src))
        for el in soup.find_all():
            for attr in list(el.attrs):
                if attr.startswith('on') or attr in ('style','srcset'):del el[attr]
        # Use only actual referenced final figures. Match original EN source bytes
        # to share unlabelled historical photographs without a second encoding.
        image_receipts=[]
        def asset(p,thumb=False):
            digest=sha(p)
            candidate=ep.parent/p.name
            shared=candidate if candidate.is_file() and sha(candidate)==digest else None
            if shared:
                name=shared.stem+'.webp' if shared.suffix.lower() in {'.png','.jpg','.jpeg'} else shared.name
                target=ROOT/'assets/images'/sec/slug/name
                if target.is_file():
                    image_receipts.append({'source':str(p),'source_sha256':digest,'output':target.relative_to(ROOT).as_posix(),'shared':True})
                    return BASE+target.relative_to(ROOT).as_posix()
            name=p.stem+('.thumb' if thumb else '')+'.avif'
            target=ROOT/'assets/images/ko'/sec/slug/name
            jobs[target]=(p,thumb,digest)
            image_receipts.append({'source':str(p),'source_sha256':digest,'output':target.relative_to(ROOT).as_posix(),'shared':False})
            return BASE+target.relative_to(ROOT).as_posix()
        for img in soup.find_all('img'):
            value=img.get('src','')
            if src.name=='nrc-original.html':
                p=src.parent/'nrc-assets'/Path(value).name
            else:p=locate(base,value)
            img['src']=asset(p);img['loading']='lazy'
            if not img.get('alt'):img['alt']=title+' 설명 그림'
            if not img.find_parent('figure'):
                figure=soup.new_tag('figure',attrs={'class':'article-image'});img.wrap(figure)
        for a in soup.find_all('a',href=True):
            href=a['href']
            if src.name=='nrc-original.html' and re.search(r'\.(?:png|webp|jpg)$',href):
                a['href']=asset(src.parent/'nrc-assets'/Path(href).name);continue
            if href.startswith(('https://','http://','#','mailto:')):continue
            # Resolve known Korean concept/series cross-references to public pairs.
            target=None
            m=re.search(r'([CP]-[A-Z]{2}-\d{3})',href,re.I)
            if m:
                target=next((r['url'] for r in pairs if Path(r['url']).name.startswith(m[1].lower()+'-')),None)
            if target:a['href']=BASE+'ko/'+target
            else:issues.append({'url':row['url'],'unresolved_link':href});a.unwrap()
        paragraphs=[p.get_text(' ',strip=True) for p in soup.find_all('p') if not p.find('img') and len(p.get_text(strip=True))>35]
        summary=(paragraphs[0] if paragraphs else title)
        if len(summary)>220:summary=summary[:217].rsplit(' ',1)[0]+'…'
        candidates=[base/'thumbnail_01.png',base/'thumbnail_01_rev.png',base/'thumbnail.png',base/'assets/thumbnail_01.png',base.parent/'images/thumbnail_01.png',base.parent/'images/thumbnail_ko.png']
        thumb=next((p for p in candidates if p.is_file()),None)
        if thumb:thumbnail=asset(thumb,True)
        elif src.name=='nrc-original.html':thumbnail=soup.find('img')['src']
        else:raise ValueError('Missing Korean thumbnail: '+str(src))
        # Insert a thumbnail if the source does not already contain it.
        if not any('thumbnail' in im.get('src','') for im in soup.find_all('img')):
            fig=soup.new_tag('figure',attrs={'class':'article-image'});im=soup.new_tag('img',src=thumbnail,alt=title+' 대표 이미지');fig.append(im);soup.insert(0,fig)
        body=str(soup)
        if '이미지 삽입:' in body:raise ValueError('Unresolved image anchor: '+str(src))
        out=ROOT/'locales/ko'/row['url'];out.parent.mkdir(parents=True,exist_ok=True);out.write_text(body,encoding='utf8')
        record=dict(en,title=title,summary=summary,category=vocab[en['category']],thumbnail=thumbnail,thumbnailAlt=title+' 대표 이미지',keywords=title+' '+en.get('keywords',''),en_sha256=sha(ROOT/row['url']),ko_sha256=sha(out))
        receipt=dict(url=row['url'],source=str(src),source_sha256=sha(src),en_sha256=record['en_sha256'],ko_sha256=record['ko_sha256'],images=image_receipts)
        records.append(record);evidence.append(receipt)
        dump(cachepath,{'source_sha256':sha(src),'record':record,'evidence':receipt})
        if len(records)%50==0:print('Prepared',len(records),'/',len(pairs),flush=True)
    def safe_prepare(row):
        try:prepare(row)
        except Exception as exc:
            errors.append({'url':row['url'],'error':str(exc)});print('IMPORT ERROR',row['url'],str(exc),flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(safe_prepare,pairs))
    dump(args.map.parent/'import-errors.json',errors)
    if errors:raise SystemExit(f'{len(errors)} import errors; see import-errors.json')
    order={r['url']:i for i,r in enumerate(pairs)}
    records.sort(key=lambda r:order[r['url']]);evidence.sort(key=lambda r:order[r['url']])
    def encode(item):
        target,(p,thumb,digest)=item;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.stat().st_mtime>=p.stat().st_mtime:return
        with Image.open(p) as im:
            im.thumbnail((640,640) if thumb else (1440,2000))
            im.convert('RGBA' if im.mode in ('RGBA','LA') else 'RGB').save(target,'AVIF',quality=42 if not thumb else 40,speed=6)
    print('Encoding',len(jobs),'Korean images',flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(encode,jobs.items()))
    for row in evidence:
        for im in row['images']:im['output_sha256']=sha(ROOT/im['output'])
    dump(ROOT/'locales/ko/assets.json',{im['output']:im['output_sha256'] for r in evidence for im in r['images']})
    dump(ROOT/'locales/ko/posts.json',records);dump(args.map.parent/'import-evidence.json',evidence);dump(args.map.parent/'link-issues.json',issues)
    print('Imported',len(records),'articles; unresolved local cross-links:',len(issues),flush=True)
    if issues:raise SystemExit(1)
if __name__=='__main__':main()
