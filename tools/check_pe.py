"""Fail on PE inventory, navigation, source integrity and scope omissions."""
import json,re,sys
from pathlib import Path
from bs4 import BeautifulSoup
from build_pe import load,expected_pages,PREFIX,record_digest

def scope_errors(scope,root,out):
    errors=[];rows=load(root);expected=expected_pages(rows)
    actual=sorted(p.relative_to(out).as_posix() for p in (out/'ko/pe').rglob('*.html'))
    if scope.get('kind')!='pe-board':errors.append('Expected pe-board kind')
    previous=scope.get('previous_posts',{})
    current={p['url']:p for p in rows}
    if not isinstance(previous,dict) or not set(previous)<=set(current):errors.append('Invalid previous PE inventory')
    if scope.get('new_posts')!=sorted(set(current)-set(previous)):errors.append('PE article scope mismatch')
    declared={x.get('path') for x in scope.get('changed_features',[])}
    for rel,old_hash in previous.items():
        if rel in current and record_digest(current[rel])!=old_hash and rel not in declared:errors.append('Undeclared PE revision '+rel)
    if actual!=expected:errors.append('PE generated page set mismatch')
    if not scope.get('changed_features') or any(not all(x.get(k) for k in ('path','feature','reason')) for x in scope['changed_features']):errors.append('Missing changed feature reasons')
    return errors

def check(root,out):
    rows=load(root);scope=json.loads((root/'qa/deployments/current.json').read_text(encoding='utf8'))
    errors=scope_errors(scope,root,out)
    for rel in expected_pages(rows):
        p=out/rel
        if not p.is_file():continue
        text=p.read_text(encoding='utf8');s=BeautifulSoup(text,'html.parser')
        if s.html.get('lang')!='ko' or not s.h1:errors.append('Missing Korean heading '+rel)
        if s.select('link[hreflang]'):errors.append('PE must not fabricate translated counterpart '+rel)
        if re.search(r'(?:[A-Z]:[\\/]|file://|data/qa/|fact_sheet\.md|이미지\s*삽입\s*:)',text):errors.append('Private path/placeholder '+rel)
        if rel.startswith('ko/pe/posts/') and len(re.findall('[가-힣]',s.article.get_text()))<100:errors.append('Empty article '+rel)
        en=s.select_one('.language-switch [hreflang=en]')
        if not en or en['href']!=PREFIX+'index.html?lang=en':errors.append('Wrong English exit '+rel)
    for p in (out/'ko').rglob('*.html'):
        if p.is_relative_to(out/'ko/pe'):continue
        if PREFIX+'ko/pe/index.html' not in p.read_text(encoding='utf8'):errors.append('Missing PE navigation '+str(p))
    home=(out/'index.html').read_text(encoding='utf8')
    if 'id="korean-default"' not in home or 'get("lang")!=="en"' not in home:errors.append('Default routing missing')
    if errors:raise ValueError(errors)
    return {'status':'PASS','posts':len(rows),'pages':len(expected_pages(rows))}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];print(json.dumps(check(root,Path(sys.argv[1]) if len(sys.argv)>1 else root/'_site')))
