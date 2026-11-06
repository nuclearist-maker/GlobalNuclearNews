"""Reject missing new posts and unnecessary repeated checks of existing posts."""
import argparse,json,re
from pathlib import Path

def errors(manifest,first,last,report=None,http=None):
    found=[]
    posts=manifest.get('new_posts',[])
    if not posts or any(type(n) is not int or not 1<=n<=300 for n in posts) or len(set(posts))!=len(posts):
        return ['DEPLOYMENT-01: invalid new_posts']
    if posts!=list(range(first,last+1)):
        found.append('DEPLOYMENT-01: CI range must match exactly the new posts')
    changed=manifest.get('changed_features',[])
    for item in changed:
        if not item.get('path') or not item.get('reason') or not item.get('feature'):
            found.append('DEPLOYMENT-02: changed feature requires path, reason and feature')
    if report is not None:
        for key in ['articles','listing','image_url_views']:
            rows=report.get(key,[]);seen=set()
            for row in rows:
                n=row.get('post')
                if n is None:
                    match=re.search(r'(?:/|^)(\d{3})-',row.get('url',''))
                    n=int(match[1]) if match else None
                if n not in posts:found.append('DEPLOYMENT-01: non-new post checked in '+key)
                if row.get('status')!='PASS':found.append('DEPLOYMENT-03: failed check in '+key)
                seen.add(n)
            if seen!=set(posts):found.append('DEPLOYMENT-03: missing new post coverage in '+key)
    if http is not None:
        allowed_changed={x.get('path') for x in changed}
        for path,row in http.get('files',{}).items():
            match=re.search(r'(?:/|^)(\d{3})-',path)
            if match and int(match[1]) not in posts and path not in allowed_changed:
                found.append('DEPLOYMENT-01: unjustified old file fetch '+path)
            if row.get('status')!='PASS':found.append('DEPLOYMENT-03: failed public file '+path)
    return found

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--first',type=int);p.add_argument('--last',type=int);p.add_argument('--site',type=Path);p.add_argument('--report',type=Path);p.add_argument('--http',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    read=lambda x:json.loads(x.read_text(encoding='utf-8-sig'))
    manifest=read(a.manifest)
    if manifest.get('kind')=='language-edition':
        if not a.site or not (a.site/'ko/index.html').is_file():p.error('language-edition requires --site with built Korean edition')
        actual=sorted(x.relative_to(a.site).as_posix() for x in (a.site/'ko').rglob('*.html'))
        problems=[]
        if manifest.get('new_posts')!=[] or manifest.get('new_localized_pages')!=actual:problems.append('DEPLOYMENT-01: localized pages must exactly match built scope')
        if not manifest.get('changed_features') or any(not all(x.get(k) for k in ['path','reason','feature']) for x in manifest['changed_features']):problems.append('DEPLOYMENT-02: missing feature/reason')
    else:
        if a.first is None or a.last is None:p.error('article deployment requires --first and --last')
        problems=errors(manifest,a.first,a.last,read(a.report) if a.report else None,read(a.http) if a.http else None)
    result={'status':'FAIL' if problems else 'PASS','errors':problems,'scope':manifest.get('new_localized_pages') if manifest.get('kind')=='language-edition' else list(range(a.first,a.last+1))}
    if a.out:a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result));return bool(problems)

if __name__=='__main__':raise SystemExit(main())
