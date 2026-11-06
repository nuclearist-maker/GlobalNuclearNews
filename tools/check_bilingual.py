"""Fail closed on incomplete locales, links, metadata and untranslated UI."""
import json,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup,Comment,Doctype
from build_bilingual import BASE,KBASE,PREFIX,vocabulary,translate,digest
from search_discovery import content_html_files,posts_from

def check(root,source=None):
    source=source or Path(__file__).resolve().parents[1]
    en=posts_from(root);ko=posts_from(root/'ko');words=vocabulary(source)
    scope=json.loads((source/'qa/deployments/current.json').read_text(encoding='utf8'))
    assert scope.get('kind')=='language-edition' and scope.get('new_posts')==[], 'Invalid localization deployment scope'
    actual=sorted(p.relative_to(root).as_posix() for p in content_html_files(root/'ko'))
    assert scope.get('new_localized_pages')==actual, 'Localization deployment coverage mismatch'
    assert scope.get('changed_features') and all(x.get('path') and x.get('feature') and x.get('reason') for x in scope['changed_features']), 'Missing changed feature reasons'
    assert {p['url'] for p in en}=={p['url'] for p in ko},'Different article sets'
    checked=0;links=0;missing=[];untranslated=[]
    for path in content_html_files(root):
        rel=path.relative_to(root).as_posix();is_ko=rel.startswith('ko/');pair=rel[3:] if is_ko else rel
        text=path.read_text(encoding='utf8');s=BeautifulSoup(text,'html.parser');lang='ko' if is_ko else 'en'
        assert s.html.get('lang')==lang,(rel,'lang')
        assert not re.search(r'(?:[A-Z]:[\\/]|file://|local-source-archive|data/qa/|v1_draft\.md|fact_sheet\.md)',text),(rel,'private path')
        assert '이미지 삽입:' not in text,(rel,'image placeholder')
        nav=s.select_one('.language-switch');assert nav is not None,(rel,'language switch')
        hrefs={a['hreflang']:urljoin(BASE+rel,a['href']) for a in nav.find_all('a')}
        if pair=='index.html':hrefs['en']=BASE if hrefs['en']==BASE+'index.html' else hrefs['en']
        assert hrefs=={'en':BASE if pair=='index.html' else BASE+pair,'ko':KBASE+pair},(rel,hrefs)
        assert len(nav.select('[aria-current="true"]'))==1 and nav.select_one('[aria-current="true"]')['hreflang']==lang,(rel,'current language')
        alternate={a['hreflang']:a['href'] for a in s.select('link[hreflang]')}
        assert alternate==dict(hrefs,**{'x-default':hrefs['en']}),(rel,'hreflang')
        assert s.select_one('meta[property="og:locale"]')['content']==('ko_KR' if is_ko else 'en_US'),(rel,'og locale')
        for tag in s.select('script[type="application/ld+json"]'):
            data=json.loads(tag.string);assert data['inLanguage']==lang,(rel,'schema locale')
        for el in s.find_all():
            for attr in ['src','href']:
                value=el.get(attr)
                if not value:continue
                absolute=urljoin(BASE+rel,value);u=urlsplit(absolute)
                if absolute.startswith(BASE):
                    target=unquote(u.path[len(PREFIX):]) or 'index.html'
                    dest=root/target
                    if dest.is_dir():dest/= 'index.html'
                    if not dest.is_file():missing.append((rel,value))
                    links+=1
        if is_ko:
            # Known English UI may not remain anywhere outside original article text.
            for node in s.find_all(string=True):
                if isinstance(node,(Comment,Doctype)) or node.parent.name in ('script','style'):continue
                if node.parent.find_parent('article') and pair.startswith('posts/'):continue
                v=str(node).strip()
                if v in words and words[v]!=v:untranslated.append((rel,v))
            if pair.startswith('posts/'):
                article=s.select_one('main.article article');assert article and len(re.findall('[가-힣]',article.get_text()))>100,(rel,'empty Korean article')
        checked+=1
    assert not missing,('Missing public links',missing[:30])
    assert not untranslated,('Untranslated UI',untranslated[:30])
    assert not re.search(r'localStorage|sessionStorage|document\.cookie|navigator\.language', (root/'ko/assets/i18n.js').read_text(encoding='utf8'))
    return {'status':'PASS','articles_per_locale':len(en),'html_pages':checked,'local_references':links,'untranslated_known_ui':0,'missing_local_references':0}
if __name__=='__main__':print(json.dumps(check(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'_site')))
