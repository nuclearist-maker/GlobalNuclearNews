"""Import approved PE final manuscripts; never copy working folders wholesale.

python tools/import_pe.py --source <output-pe> --receipt <private.json>
Use --include-finals only when all final_post.md files are explicitly approved.
"""
import argparse, hashlib, json, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from bs4 import BeautifulSoup, Comment
from PIL import Image
from import_korean import markdown, locate, sha, read, dump
from build_pe import record_digest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '/GlobalNuclearNews/'

def repair_korean_emphasis(soup):
    """Render unparsed strong delimiters adjoining a Korean particle safely."""
    pattern = re.compile(r'(?<!\\)\*\*([^*\n]+?)\*\*(?=[가-힣A-Za-z])')
    for node in list(soup.find_all(string=True)):
        if isinstance(node, Comment) or node.find_parent(['code', 'pre', 'script', 'style']):
            continue
        value = str(node)
        matches = list(pattern.finditer(value))
        if not matches:continue
        offset = 0
        for match in matches:
            node.insert_before(value[offset:match.start()])
            strong = soup.new_tag('strong');strong.string = match[1]
            node.insert_before(strong);offset = match.end()
        node.insert_before(value[offset:]);node.extract()
    return soup

def repair_numeric_section_references(soup):
    """Keep literal bracketed limits plus dotted SR numbers, not broken links."""
    for link in list(soup.find_all('a', href=True)):
        if link.find_parent(['code', 'pre', 'script', 'style']):continue
        if re.fullmatch(r'[0-9]+(?:\.[0-9]+){2,}', link['href']):
            link.replace_with('[' + link.get_text() + '](' + link['href'] + ')')
    return soup

def convert(source, receipt, include_finals=False):
    target = ROOT/'locales/ko/pe'
    target.mkdir(parents=True, exist_ok=True)
    candidates = [(group, p) for group in ('concept','exam') for p in sorted((source/group).glob('*/final_post.md'))]
    def prepare(item):
        group, src = item
        meta = json.loads(read(src.parent/'meta.json'))
        if not include_finals and meta.get('status') not in ('발행','ready','published'):
            return None
        ident = meta['id']
        for key in ('title','domain','created_at','related'):
            if key not in meta:raise ValueError('Missing metadata '+key+': '+ident)
        if not isinstance(meta['related'],list):raise ValueError('Invalid related list: '+ident)
        pattern = r'C-[A-Z]{2}-\d{3}' if group == 'concept' else r'(?:Y\d{4}-[1-4]-\d{2}|H\d{4})'
        if not re.fullmatch(pattern, ident):raise ValueError('Invalid PE ID: '+ident)
        soup = repair_numeric_section_references(repair_korean_emphasis(BeautifulSoup(markdown(read(src)), 'html.parser')))
        heading = soup.find('h1')
        if not heading:raise ValueError('Missing heading: '+ident)
        title = heading.get_text(' ',strip=True)
        heading.decompose()
        for comment in soup.find_all(string=lambda x:isinstance(x,Comment)):comment.extract()
        for el in soup.select('script,style,iframe,form,object,embed'):el.decompose()
        for el in soup.find_all():
            for attr in list(el.attrs):
                if attr.startswith('on') or attr in ('style','srcset'):del el[attr]
        images = []
        def asset(path,thumb=False):
            if path.is_symlink() or not path.resolve().is_relative_to(src.parent.resolve()):raise ValueError('Image escapes article folder')
            source_hash = sha(path)
            # Content address avoids overwriting approved images and supports reuse.
            rel = 'assets/images/ko/pe/'+source_hash+'.webp'
            dst = ROOT/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():
                with Image.open(path) as im:
                    im=im.convert('RGB')
                    if thumb:im.thumbnail((800,800))
                    im.save(dst,'WEBP',quality=88,method=4)
            images.append({'source':str(path),'source_sha256':source_hash,'output':rel,'sha256':sha(dst)})
            return PREFIX+rel
        for a in soup.find_all('a',href=True):
            if re.search(r'\.(png|jpg|jpeg|webp)$',a['href'],re.I):
                a['href']=asset(locate(src.parent,a['href']))
        for img in soup.find_all('img'):
            img['src'] = asset(locate(src.parent,img.get('src','')))
            img['loading'] = 'lazy'
            if not img.get('alt'):img['alt']=title+' 설명 그림'
            if not img.find_parent('figure'):img.wrap(soup.new_tag('figure',attrs={'class':'article-image'}))
        # Resolve cross-links only after all immutable IDs are known.
        thumb = src.parent/'thumbnail_01.png'
        thumbnail = asset(thumb,True) if thumb.is_file() else (soup.img['src'] if soup.img else '')
        paragraphs = [p.get_text(' ',strip=True) for p in soup.find_all('p') if not p.find('img')]
        summary = next((p for p in paragraphs if len(p)>35), title)[:220]
        row = {'id':ident,'group':group,'title':title,'domain':meta.get('domain','개념'),
               'year':int(ident[1:5]) if group=='exam' else None,
               'session':int(ident.split('-')[1]) if ident.startswith('Y') else 0,
               'question':int(ident.split('-')[2]) if ident.startswith('Y') else 0,
               'url':'ko/pe/posts/'+ident.lower()+'.html','body':'bodies/'+ident.lower()+'.html',
               'summary':summary,'thumbnail':thumbnail,'date':meta.get('created_at',''),
               'related':meta.get('related',[])}
        return row,soup,{'source':str(src),'source_sha256':sha(src),'metadata_sha256':sha(src.parent/'meta.json'),'images':images}
    with ThreadPoolExecutor(max_workers=8) as pool:
        prepared = [x for x in pool.map(prepare,candidates) if x]
    old = json.loads(read(target/'posts.json')) if (target/'posts.json').exists() else []
    records = {p['id']:p for p in old}
    ids = [r['id'] for r,_,_ in prepared]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate PE IDs')
    urls = {r['id']:PREFIX+r['url'] for r,_,_ in prepared}
    urls.update({r['id']:PREFIX+r['url'] for r in old if r['id'] not in urls})
    evidence = []
    for row,soup,proof in prepared:
        for a in soup.find_all('a',href=True):
            href=a['href'];u=urlsplit(href)
            if href.startswith(PREFIX+'assets/images/ko/pe/') and any(PREFIX+x['output']==href for x in proof['images']):continue
            if u.scheme in ('http','https','mailto') or href.startswith('#'):continue
            if u.scheme or u.netloc:raise ValueError('Unsafe link '+row['id']+': '+href)
            m=re.search(r'C-[A-Z]{2}-\d{3}|Y\d{4}-[1-4]-\d{2}|H\d{4}',href,re.I)
            if m and m[0].upper() in urls:a['href']=urls[m[0].upper()]
            else:raise ValueError('Unresolved or unsafe link '+row['id']+': '+href)
        body=target/row['body'];body.parent.mkdir(exist_ok=True)
        body.write_text(str(soup),encoding='utf8');row['body_sha256']=sha(body)
        row['assets']={x['output']:x['sha256'] for x in proof['images']}
        records[row['id']]=row;proof['id']=row['id'];proof['output_sha256']=row['body_sha256'];evidence.append(proof)
    dump(target/'posts.json', sorted(records.values(),key=lambda p:p['id']))
    previous={p['url']:record_digest(p) for p in old}
    changed=[{'path':'index.html','feature':'default language','reason':'Use Korean entry with explicit English opt-in'},
             {'path':'ko/pe/index.html','feature':'study board','reason':'Regenerate study navigation and year groups'},
             {'path':'ko/index.html','feature':'Korean navigation','reason':'Link the study board on Korean pages'},
             {'path':'sitemap.xml','feature':'search discovery','reason':'Include study board and imported articles'}]
    changed += [{'path':p['url'],'feature':'article revision','reason':'Reimport an updated final manuscript'} for p in records.values() if p['url'] in previous and previous[p['url']]!=record_digest(p)]
    dump(ROOT/'qa/deployments/current.json',{'version':1,'kind':'pe-board','new_posts':sorted(p['url'] for p in records.values() if p['url'] not in previous),'previous_posts':previous,'changed_features':changed})
    dump(receipt,{'include_finals':include_finals,'imported':len(prepared),'sources':evidence})
    print(json.dumps({'imported':len(prepared),'total':len(records),'concepts':sum(p['group']=='concept' for p in records.values()),'exams':sum(p['group']=='exam' for p in records.values())}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--include-finals',action='store_true');a=p.parse_args()
    if a.receipt.resolve().is_relative_to(ROOT):p.error('Receipt must be outside public repository')
    convert(a.source,a.receipt,a.include_finals)
