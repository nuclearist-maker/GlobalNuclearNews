"""Install a Korean-only study board from portable, hash-bound inputs."""
import hashlib, html, json, re, shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from build_bilingual import BASE, PREFIX, digest

ESC=html.escape
def record_digest(row):
    return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')).hexdigest()
STYLE='''.pe-tabs{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}.pe-tools{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.pe-tools input,.pe-tools select{padding:12px;border:1px solid #8a9ba9;border-radius:8px;max-width:100%;font:inherit}.pe-list{list-style:none;padding:0}.pe-list li{padding:22px 0;border-bottom:1px solid #bac8d1}.pe-list a{font-weight:700;font-size:1.15rem}.pe-list p{margin:8px 0}.pe-meta{color:#526779}.pe-intro{max-width:75ch}.pe-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}.pe-grid a{padding:20px;border:1px solid #bac8d1;border-radius:10px}.pe-reading{max-width:920px;margin:auto;padding:32px 20px}.pe-reading img{max-width:100%;height:auto}.pe-reading figure{margin:28px 0}.pe-reading table{display:block;overflow:auto;max-width:100%}.pe-reading th,.pe-reading td{padding:10px;border:1px solid #bac8d1}.pe-reading pre{overflow:auto}.pe-reading mjx-container[display=true]{overflow-x:auto;overflow-y:hidden;padding:8px 0}.pe-reading h1{font-size:clamp(1.6rem,4vw,2.7rem);line-height:1.4}.pe-reading{overflow-wrap:anywhere;line-height:1.9}'''
JS='''const input=document.querySelector('#pe-search'),select=document.querySelector('#pe-domain');function filter(){let n=0;document.querySelectorAll('.pe-list li').forEach(el=>{el.hidden=!(el.textContent.toLocaleLowerCase().includes(input.value.trim().toLocaleLowerCase())&&(!select||!select.value||el.dataset.domain===select.value));if(!el.hidden)n++});document.querySelector('#pe-count').textContent=n+'편';}if(input){input.addEventListener('input',filter);if(select)select.addEventListener('change',filter);filter();}'''

def load(root):
    base=root/'locales/ko/pe';rows=json.loads((base/'posts.json').read_text(encoding='utf8'))
    ids=set()
    for row in rows:
        ident=row['id'];pattern=r'C-[A-Z]{2}-\d{3}' if row['group']=='concept' else r'(?:Y\d{4}-[1-4]-\d{2}|H\d{4})'
        if row['group'] not in ('concept','exam') or not re.fullmatch(pattern,ident) or ident in ids:raise ValueError('PE invalid/duplicate ID')
        ids.add(ident)
        if row['group']=='exam':
            expected=(int(ident[1:5]),int(ident.split('-')[1]) if ident.startswith('Y') else 0,int(ident.split('-')[2]) if ident.startswith('Y') else 0)
            if (row.get('year'),row.get('session'),row.get('question'))!=expected:raise ValueError('PE exam coordinates disagree with ID '+ident)
        if row['body']!='bodies/'+ident.lower()+'.html' or row['url']!='ko/pe/posts/'+ident.lower()+'.html':raise ValueError('PE unsafe path')
        if digest(base/row['body'])!=row['body_sha256']:raise ValueError('PE changed body '+ident)
        for rel,sha in row['assets'].items():
            if not re.fullmatch(r'assets/images/ko/pe/[a-f0-9]{64}\.webp',rel) or hashlib.sha256((root/rel).read_bytes()).hexdigest()!=sha:raise ValueError('PE changed/unsafe asset '+rel)
    return rows

def expected_pages(rows):
    return sorted(['ko/pe/index.html','ko/pe/concepts.html','ko/pe/exams.html']+['ko/pe/exams/'+str(y)+'.html' for y in sorted({p['year'] for p in rows if p['group']=='exam'})]+[p['url'] for p in rows])

def install(root,out):
    rows=load(root);byid={p['id']:p for p in rows}
    (out/'assets/pe.css').write_text(STYLE,encoding='utf8');(out/'assets/pe.js').write_text(JS,encoding='utf8')
    def page(rel,title,body,description=None):
        url=BASE+rel;description=description or title+' — 발전기술사 준비'
        text=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{ESC(title)} | GlobalNuclearNews</title><meta name="description" content="{ESC(description,quote=True)}"><link rel="canonical" href="{url}"><meta property="og:url" content="{url}"><meta property="og:locale" content="ko_KR"><meta property="og:title" content="{ESC(title,quote=True)}"><meta property="og:description" content="{ESC(description,quote=True)}"><link rel="stylesheet" href="{PREFIX}assets/styles.css"><link rel="stylesheet" href="{PREFIX}assets/languages.css"><link rel="stylesheet" href="{PREFIX}assets/pe.css"><link rel="alternate" type="application/rss+xml" href="{PREFIX}ko/pe/feed.xml" title="발전기술사 준비"></head><body><header class="masthead"><a class="brand" href="{PREFIX}ko/index.html">GlobalNuclearNews</a><nav aria-label="주 메뉴"><a href="{PREFIX}ko/index.html">홈</a><a href="{PREFIX}ko/pe/index.html">발전기술사 준비</a></nav><nav class="language-switch" aria-label="언어 선택"><a href="{PREFIX}index.html?lang=en" hreflang="en" lang="en">EN 홈</a><a href="{PREFIX}{rel}" aria-current="true" hreflang="ko" lang="ko">KOR</a></nav></header><main class="pe-reading"><nav class="pe-tabs" aria-label="발전기술사 준비 하위 그룹"><a href="{PREFIX}ko/pe/concepts.html">개념설명</a><a href="{PREFIX}ko/pe/exams.html">연도별 기출문제 풀이</a></nav><h1>{ESC(title)}</h1>{body}</main><footer><a href="{PREFIX}ko/index.html">한국어 홈</a><a href="{PREFIX}ko/pe/feed.xml">발전기술사 RSS</a></footer><script src="{PREFIX}assets/pe.js" defer></script></body></html>'''
        data={'@context':'https://schema.org','@type':'Article' if rel.startswith('ko/pe/posts/') else 'CollectionPage','name':title,'url':url,'inLanguage':'ko','description':description}
        if data['@type']=='Article':data['headline']=title
        text=text.replace('</head>','<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script></head>')
        # A single dollar sign is a reactivity unit in these manuscripts.
        # Load TeX only for explicit math delimiters, never for unit symbols.
        if re.search(r'\$\$|\\\(|\\\[',body):
            math_config=json.dumps({'tex':{'inlineMath':[['$','$'],[chr(92)+'(',chr(92)+')']]},'options':{'skipHtmlTags':['script','noscript','style','textarea','pre','code']}})
            text=text.replace('</head>','<script>window.MathJax='+math_config+';</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"></script></head>')
        dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf8')
    def listing(selected):
        domains=sorted({p['domain'] for p in selected})
        controls='<div class="pe-tools"><label>게시물 검색 <input id="pe-search" type="search" placeholder="제목·개념·문제번호 검색"></label><label>분야 <select id="pe-domain"><option value="">전체 분야</option>'+''.join(f'<option>{ESC(d)}</option>' for d in domains)+'</select></label></div><p id="pe-count" role="status">'+str(len(selected))+'편</p>'
        return controls+'<ul class="pe-list">'+''.join(f'<li data-domain="{ESC(p["domain"],quote=True)}"><span class="pe-meta">{ESC(p["id"])} · {ESC(p["domain"])}'+(f' · {p["session"]}교시 {p["question"]}번' if p['id'].startswith('Y') else (' · 연도별 총정리' if p['id'].startswith('H') else ''))+f'</span><p><a href="{PREFIX}{p["url"]}">{ESC(p["title"])}</a></p><p>{ESC(p["summary"])}</p></li>' for p in selected)+'</ul>'
    concepts=[p for p in rows if p['group']=='concept'];exams=[p for p in rows if p['group']=='exam'];years=sorted({p['year'] for p in exams},reverse=True)
    yearlinks='<div class="pe-grid">'+''.join(f'<a href="{PREFIX}ko/pe/exams/{y}.html">{y}년 · {sum(p["year"]==y for p in exams)}편 →</a>' for y in years)+'</div>'
    page('ko/pe/index.html','발전기술사 준비',f'<p class="pe-intro">원자력발전기술사 학습을 위한 개념설명과 연도별 기출문제 풀이를 모았습니다. 새로운 개념과 기출문제 풀이를 계속 추가합니다.</p><div class="pe-grid"><a href="concepts.html">개념설명 · {len(concepts)}편 →</a><a href="exams.html">연도별 기출문제 풀이 · {len(exams)}편 →</a></div><h2>연도별 기출문제</h2>'+yearlinks)
    page('ko/pe/concepts.html','개념설명',listing(concepts))
    page('ko/pe/exams.html','연도별 기출문제 풀이',yearlinks)
    for year in years:page(f'ko/pe/exams/{year}.html',f'{year}년 기출문제 풀이',listing(sorted([p for p in exams if p['year']==year],key=lambda p:(p['session'],p['question']))))
    for p in rows:
        related=[byid[x] for x in p['related'] if x in byid]
        content=BeautifulSoup((root/'locales/ko/pe'/p['body']).read_text(encoding='utf8'),'html.parser')
        for img in content.select('img[src]'):
            if not img.find_parent('a'):img.wrap(content.new_tag('a',href=img['src']))
        body=('<p class="pe-meta">그림을 누르면 크게 볼 수 있습니다.</p>' if content.img else '')+'<article>'+str(content)+'</article>'
        if related:body+='<aside><h2>함께 공부하기</h2><ul>'+''.join(f'<li><a href="{PREFIX}{r["url"]}">{ESC(r["title"])}</a></li>' for r in related)+'</ul></aside>'
        page(p['url'],p['title'],body,p['summary'])
        for rel in p['assets']:
            dest=out/rel
            if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/rel,dest)
    # Add one navigation entry to each existing Korean page; preserve article bodies.
    for path in (out/'ko').rglob('*.html'):
        if path.is_relative_to(out/'ko/pe'):continue
        soup=BeautifulSoup(path.read_text(encoding='utf8'),'html.parser');mast=soup.select_one('.masthead');nav=mast.select_one('nav:not(.language-switch)')
        if nav is None:nav=soup.new_tag('nav',attrs={'aria-label':'주 메뉴'});mast.insert(1,nav)
        a=soup.new_tag('a',href=PREFIX+'ko/pe/index.html');a.string='발전기술사 준비';nav.append(a)
        path.write_text(str(soup),encoding='utf8')
    for name in ('sitemap.xml','ko/sitemap.xml'):
        tree=ET.parse(out/name);ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
        for rel in expected_pages(rows):
            entry=ET.SubElement(tree.getroot(),ns+'url');ET.SubElement(entry,ns+'loc').text=BASE+rel
        tree.write(out/name,encoding='utf8',xml_declaration=True)
    rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel')
    for key,value in [('title','발전기술사 준비'),('link',BASE+'ko/pe/index.html'),('description','개념설명과 연도별 기출문제 풀이'),('language','ko')]:ET.SubElement(channel,key).text=value
    for p in sorted(rows,key=lambda p:(p['date'],p['id']),reverse=True)[:50]:
        item=ET.SubElement(channel,'item')
        for key,value in [('title',p['title']),('link',BASE+p['url']),('guid',BASE+p['url']),('description',p['summary'])]:ET.SubElement(item,key).text=value
    ET.ElementTree(rss).write(out/'ko/pe/feed.xml',encoding='utf8',xml_declaration=True)
    # Redirect only the entry page. Explicit English home links opt out.
    for path in out.rglob('*.html'):
        if path.is_relative_to(out/'ko'):continue
        text=path.read_text(encoding='utf8')
        text=re.sub(r'(<a\b[^>]*\bhref=")('+re.escape(BASE)+r'|(?:'+re.escape(PREFIX)+r')?index\.html|(?:\.\./)+index\.html)"',lambda m:m[1]+m[2]+'?lang=en"',text)
        if path==out/'index.html':text=text.replace('<head>','<head><script id="korean-default">if(new URLSearchParams(location.search).get("lang")!=="en")location.replace("'+PREFIX+'ko/index.html"+location.hash);</script>',1)
        path.write_text(text,encoding='utf8')
    return {'concepts':len(concepts),'exams':len(exams),'years':years}
