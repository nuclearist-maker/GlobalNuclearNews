"""Install portable Korean inputs after English enrichment, then link both editions."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,html,json,re,shutil,posixpath
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup,Comment,Doctype
from search_discovery import BASE,SECTIONS,enrich,content_html_files

PREFIX='/GlobalNuclearNews/'
KBASE=BASE+'ko/'
def digest(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def read(p):return p.read_text(encoding='utf8')
def vocabulary(root):
    words={}
    for n in ['ui','categories','reactors']:words.update(json.loads(read(root/f'locales/ko/{n}.json')))
    return words
def translate(raw,words):
    s=raw.strip()
    if s in words:return raw.replace(s,words[s])
    rules=[
      (r'^(\d+) records · showing the first 10$',lambda m:f'{m[1]}건 · 첫 10건 표시'),
      (r'^PRIS fields checked: (.+)$',lambda m:f'PRIS 항목 확인일: {m[1]}'),
      (r'^Baseline only · source review: (.+) · not revalidated$',lambda m:f'기존 자료만 있음 · 출처 검토일: {m[1]} · 재검증하지 않음'),
      (r'^(.+) · checked (.+)$',lambda m:f'{translate(m[1],words)} · 확인일 {m[2]}'),
      (r'^Baseline stage: (.+)\. Current PRIS inventory: (.+)\.$',lambda m:f"기존 단계: {'·'.join(translate(x,words) for x in m[1].split('; '))}. 현재 PRIS 분류: {translate(m[2],words)}."),
      (r'^(.+) archive — page (\d+)$',lambda m:f'{translate(m[1],words)} 글 모음 — {m[2]}쪽'),
      (r'^Browse (.+) articles, page (\d+) of (\d+)\.$',lambda m:f'{translate(m[1],words)} 게시물 · {m[2]} / {m[3]}쪽'),
      (r'^(.+): (\d+) articles$',lambda m:f'{translate(m[1],words)}: {m[2]}편')]
    for pattern,fn in rules:
        m=re.match(pattern,s)
        if m:return raw.replace(s,fn(m))
    for sep in [' | ',' · ']:
        if sep in s:return raw.replace(s,sep.join(translate(x,words) for x in s.split(sep)))
    if s.endswith(' →'):return raw.replace(s,translate(s[:-2],words)+' →')
    if s.startswith('← '):return raw.replace(s,'← '+translate(s[2:],words))
    return raw
def localize(text,words):
    soup=BeautifulSoup(text,'html.parser')
    for node in list(soup.find_all(string=True)):
        if isinstance(node,(Comment,Doctype)) or node.parent.name in ('script','style'):continue
        value=translate(str(node),words)
        if value!=str(node):node.replace_with(value)
    for el in soup.find_all():
        for attr in ['alt','aria-label','placeholder']:
            if el.get(attr):el[attr]=translate(el[attr],words)
        if el.name=='meta' and (el.get('name')=='description' or el.get('property') in ('og:title','og:description')):el['content']=translate(el['content'],words)
    if soup.html:soup.html['lang']='ko'
    return str(soup)

STYLE='''.masthead{gap:18px;height:auto;min-height:84px;padding-top:10px;padding-bottom:10px}.masthead>nav:not(.language-switch){gap:18px}.masthead .language-switch{display:flex;align-items:center;gap:3px;border:1px solid #7b96a8;border-radius:999px;padding:3px;flex-shrink:0;margin-left:auto}.masthead .language-switch a{display:inline-flex;align-items:center;justify-content:center;min-width:42px;min-height:36px;padding:4px 10px;border-radius:999px;font:700 14px/1.2 Arial,sans-serif;color:inherit;text-decoration:none}.masthead .language-switch a[aria-current=true]{background:#ffdd82;color:#092034}.masthead .language-switch a:focus-visible{outline:3px solid #54cfff;outline-offset:3px}html[lang=ko] body{word-break:keep-all;overflow-wrap:anywhere}html[lang=ko] .article{line-height:1.85}html[lang=ko] .article table{display:block;max-width:100%;overflow:auto}html[lang=ko] .article img{max-width:100%;height:auto}html[lang=ko] .article pre{white-space:pre-wrap;overflow:auto}html[lang=ko] .article h1{line-height:1.4}html[lang=ko] .article-image a{display:block}@media(max-width:800px){.masthead{flex-wrap:wrap}.masthead .language-switch{order:1;width:auto;gap:3px}.masthead>nav:not(.language-switch){order:2;width:100%}.masthead .brand{min-width:0}}'''

def switch(text,rel,language):
    en=BASE if rel=='index.html' else BASE+rel;ko=KBASE+rel
    text=re.sub(r'<!-- language-switch:start -->.*?<!-- language-switch:end -->','',text,flags=re.S)
    soup=BeautifulSoup(text,'html.parser');head=soup.head
    for tag in head.select('link[hreflang]'):tag.decompose()
    for tag in head.select('link[rel=stylesheet]'):
        if tag.get('href')==PREFIX+'assets/languages.css':tag.decompose()
    head.append(soup.new_tag('link',rel='stylesheet',href=PREFIX+'assets/languages.css'))
    for lang,url in [('en',en),('ko',ko),('x-default',en)]:head.append(soup.new_tag('link',rel='alternate',hreflang=lang,href=url))
    nav=soup.new_tag('nav',attrs={'class':'language-switch','aria-label':'언어 선택' if language=='ko' else 'Language selection'})
    for lang,label,url in [('en','EN',en),('ko','KR',ko)]:
        current=('ko/' if language=='ko' else '')+rel
        target=('ko/'+rel) if lang=='ko' else rel
        a=soup.new_tag('a',href=posixpath.relpath(target,posixpath.dirname(current) or '.'),lang=lang,hreflang=lang);a['aria-label']='한국어' if lang=='ko' else 'English'
        if lang==language:a['aria-current']='true'
        a.string=label;nav.append(a)
    masthead=soup.select_one('.masthead')
    if not masthead:raise ValueError('BILINGUAL: missing masthead '+rel)
    masthead.append(Comment(' language-switch:start '));masthead.append(nav);masthead.append(Comment(' language-switch:end '))
    return str(soup)

def install(root,out):
    inputs=root/'locales/ko';words=vocabulary(root)
    # New source UI prose must be explicitly localized; do not silently ship it.
    allowed={'GlobalNuclearNews','GN','IAEA PRIS Analytics','IAEA Reference Data Series No. 2','Natural Earth','AboutAds','RSS'}
    for source in root.glob('*.html'):
        if re.search(r'\.r\d+\.html$',source.name) or source.name.startswith('google'):continue
        sample=BeautifulSoup(read(source),'html.parser')
        for el in sample.select('.reactor-record,script,style'):el.decompose()
        values=[str(n).strip() for n in sample.find_all(string=True) if not isinstance(n,(Comment,Doctype))]
        values += [el[a] for el in sample.find_all() for a in ['aria-label','alt','placeholder'] if el.get(a)]
        for value in values:
            if re.search('[A-Za-z]{2}',value) and not re.search('[가-힣]',value) and value not in allowed and not value.startswith('©') and translate(value,words)==value:
                raise ValueError('BILINGUAL: untranslated UI key: '+value)
    inventory=json.loads(read(root/'assets/reactor-display.js').removeprefix('window.REACTOR_DISPLAY = ').strip().removesuffix(';'))['inventory']['records']
    for record in inventory:
        for field in ['country','status','businessState','scope','rowUnit','verification','statusNote']:
            value=record.get(field)
            if value and not re.search('[가-힣]',translate(value,words)):
                raise ValueError('BILINGUAL: untranslated reactor '+field+': '+value)
    if not (inputs/'posts.json').is_file():raise ValueError('BILINGUAL: Korean input missing; run python tools/import_korean.py --map <internal-source-map.json>')
    enposts=json.JSONDecoder().raw_decode(read(root/'assets/app.js').split('const posts = ',1)[1])[0]
    posts=json.loads(read(inputs/'posts.json'));urls=[p['url'] for p in posts]
    if len(urls)!=len(set(urls)) or set(urls)!={p['url'] for p in enposts}:raise ValueError('BILINGUAL: incomplete/duplicate Korean counterparts')
    for p in posts:
        for key,path in [('en_sha256',root/p['url']),('ko_sha256',inputs/p['url'])]:
            if digest(path)!=p[key]:raise ValueError('BILINGUAL: stale counterpart '+p['url']+'; run python tools/import_korean.py --map <internal-source-map.json>')
    assets=json.loads(read(inputs/'assets.json'))
    for rel,expected in assets.items():
        asset=(root/rel).resolve()
        if not asset.is_relative_to((root/'assets/images').resolve()) or hashlib.sha256(asset.read_bytes()).hexdigest()!=expected:raise ValueError('BILINGUAL: changed/unsafe asset '+rel)
    ko=out/'ko';ko.mkdir(exist_ok=True);(ko/'assets').mkdir(exist_ok=True)
    (out/'assets/languages.css').write_text(STYLE,encoding='utf8')
    app=read(root/'assets/app.js');_,start=app.split('const posts = ',1);_,end=json.JSONDecoder().raw_decode(start)
    categories={p['url']:p['category'] for p in enposts}
    app_posts=[dict(p,category=categories[p['url']]) for p in posts]
    (ko/'assets/app.js').write_text('const posts = '+json.dumps(app_posts,ensure_ascii=False,indent=2)+start[end:],encoding='utf8')
    runtime='window.GNN_KO_WORDS = '+json.dumps(words,ensure_ascii=False)+';\n'+read(inputs/'runtime.js')
    (ko/'assets/i18n.js').write_text(runtime,encoding='utf8')
    for source in root.glob('*.html'):
        if re.search(r'\.r\d+\.html$',source.name) or source.name.startswith('google'):continue
        soup=BeautifulSoup(read(source),'html.parser')
        for el in soup.find_all():
            for attr in ['src','href']:
                if el.get(attr,'').startswith('assets/'):
                    el[attr]=PREFIX+('ko/' if el[attr].split('?')[0]=='assets/app.js' else '')+el[attr]
        soup.head.append(soup.new_tag('script',src=PREFIX+'ko/assets/i18n.js',defer=True))
        (ko/source.name).write_text(localize(str(soup),words),encoding='utf8')
    for p in posts:
        source=BeautifulSoup(read(root/p['url']),'html.parser');article=source.select_one('main.article article')
        if article is None:raise ValueError('BILINGUAL: unknown article structure '+p['url'])
        article.clear()
        header=BeautifulSoup('<header><p class="eyebrow">'+html.escape(p['category'])+'</p><h1>'+html.escape(p['title'])+'</h1><div class="byline">'+(html.escape(p['date']) if p['section']=='news' else '')+'</div></header>','html.parser')
        article.append(header);article.append(BeautifulSoup(read(inputs/p['url']),'html.parser'))
        source.title.string=p['title']+' | GlobalNuclearNews';source.find('meta',attrs={'name':'description'})['content']=p['summary']
        for el in source.find_all():
            for attr in ['href','src']:
                if el.get(attr,'').startswith('../../assets/'):el[attr]=PREFIX+el[attr][6:]
        for im in source.select('figure img'):
            if not im.find_parent('a'):im.wrap(source.new_tag('a',href=im['src']))
        if re.search(r'\$\$|\\\(|\\\[',str(article)):
            cfg=source.new_tag('script');cfg.string="window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};";source.head.append(cfg)
            source.head.append(source.new_tag('script',src='https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js',defer=True))
        target=ko/p['url'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(localize(str(source),words),encoding='utf8')
    references=set()
    for p in ko.rglob('*.html'):references.update(re.findall(r'(?:src|href)="(/GlobalNuclearNews/assets/images/ko/[^"?#]+)',read(p)))
    references.update(p['thumbnail'] for p in posts if '/assets/images/ko/' in p['thumbnail'])
    def copy_image(ref):
        rel=unquote(ref.removeprefix(PREFIX));src=(root/rel).resolve()
        if not src.is_relative_to((root/'assets/images/ko').resolve()) or not src.is_file():raise ValueError('BILINGUAL: missing/unsafe image '+ref)
        dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    with ThreadPoolExecutor(max_workers=16) as pool:list(pool.map(copy_image,references))
    config=json.loads(read(root/'tools/search_config.json'));config['verification']={}
    enrich(ko,config,base=KBASE,language='ko',sections={s:words[label] for s,label in SECTIONS.items()})
    for p in content_html_files(ko):
        rel=p.relative_to(ko).as_posix();text=localize(read(p),words)
        if rel=='index.html':text=text.replace('href="'+KBASE+'"','href="'+KBASE+'index.html"').replace('content="'+KBASE+'"','content="'+KBASE+'index.html"')
        p.write_text(switch(text,rel,'ko'),encoding='utf8')
    for p in content_html_files(out):
        if p.is_relative_to(ko):continue
        rel=p.relative_to(out).as_posix()
        if not (ko/rel).is_file():raise ValueError('BILINGUAL: no Korean page '+rel)
        p.write_text(switch(read(p),rel,'en'),encoding='utf8')
    ns='{http://www.sitemaps.org/schemas/sitemap/0.9}';tree=ET.parse(out/'sitemap.xml');ktree=ET.parse(ko/'sitemap.xml')
    for loc in ktree.iter(ns+'loc'):
        if loc.text==KBASE:loc.text=KBASE+'index.html'
    ktree.write(ko/'sitemap.xml',encoding='utf8',xml_declaration=True)
    for entry in ktree.getroot():tree.getroot().append(entry)
    tree.write(out/'sitemap.xml',encoding='utf8',xml_declaration=True)
    return {'articles_per_language':len(posts),'korean_pages':len(content_html_files(ko)),'korean_images':len(references)}
