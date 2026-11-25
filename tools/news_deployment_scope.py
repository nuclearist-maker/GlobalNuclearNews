"""Validate an explicitly bounded release of paired news articles."""
import hashlib,json,re,subprocess
from pathlib import Path,PurePosixPath

def digest(path):
    data=path.read_bytes()
    if path.suffix in {'.html','.css','.js','.json','.md','.txt','.xml','.py','.yml'}:data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE).decode('utf8')

def posts(script):
    if 'const posts = ' not in script:raise ValueError('missing posts metadata prefix')
    return json.JSONDecoder().raw_decode(script.split('const posts = ',1)[1])[0]

def scope_errors(manifest,root,site,require_proof=True):
    root=Path(root).resolve();site=Path(site);errors=[]
    def fail(message):errors.append('NEWS-DEPLOY: '+message)
    base=manifest.get('base_commit','');paths=manifest.get('new_news_paths',[])
    if manifest.get('kind')!='news-publication' or manifest.get('new_posts')!=[]:fail('invalid kind/reserved scope')
    if not re.fullmatch('[0-9a-f]{40}',base):return errors+['NEWS-DEPLOY: invalid base commit']
    revised=manifest.get('revised_news_paths',[])
    for group in (paths, revised):
        if not isinstance(group,list) or any(not isinstance(x,str) or not re.fullmatch(r'posts/news/\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.html',x) for x in group):
            return errors+['NEWS-DEPLOY: invalid news paths']
        if group!=sorted(set(group)):fail('news paths must be sorted and unique')
    allowed=set(paths)|set(revised)
    if not allowed or set(paths)&set(revised):fail('news path groups empty or overlapping')
    slugs={Path(path).stem for path in allowed}
    def owns_image(rel):
        return any(rel.startswith(prefix+slug+'/') for slug in slugs for prefix in ('assets/images/news/','assets/images/ko/news/'))
    files=manifest.get('release_files',{});features=manifest.get('changed_features',[])
    if not isinstance(files,dict) or not files:return errors+['NEWS-DEPLOY: missing release files']
    if not isinstance(features,list) or not features or any(not isinstance(x,dict) or not all(isinstance(x.get(k),str) and x[k].strip() for k in ['path','feature','reason']) for x in features):return errors+['NEWS-DEPLOY: invalid changed features']
    declared={x['path'] for x in features}
    if len(declared)!=len(features):fail('duplicate changed feature')
    try:
        git(root,'cat-file','-e',base+'^{commit}')
        old_paths=set(git(root,'ls-tree','-r','--name-only',base).splitlines())
        changed=set(git(root,'diff','--name-only',base,'--').splitlines())
        untracked=set(git(root,'ls-files','--others','--exclude-standard').splitlines())
        controlled=('posts/','assets/','locales/','tools/','.github/','docs/','policies/')
        changed|={x for x in untracked if x.startswith(controlled)}
        changed.discard('qa/deployments/current.json')
        # The coordinator manifest is verified separately by publication_release_guard.py.
        changed.discard('qa/deployments/publication.json')
        if changed!=set(files):fail('changed-file coverage mismatch: '+str(sorted(changed^set(files))))
        if not (set(files)&old_paths)<=declared:fail('existing changed files lack feature reasons')
        if not declared<=set(files):fail('feature outside release files')
        if any(not (root/x).is_file() for x in changed):fail('deletions are forbidden')
        old_news={x for x in old_paths if x.startswith('posts/news/') and x.endswith('.html') and not re.search(r'\.r\d+\.html$',x)}
        current={p.relative_to(root).as_posix() for p in (root/'posts/news').glob('*.html') if not re.search(r'\.r\d+\.html$',p.name)}
        if current-old_news!=set(paths) or old_news-current:fail('new news set mismatch/deletion')
        if not set(revised)<=old_news:fail('revised article absent at baseline')
        for rel in files:
            if rel.startswith(('posts/','locales/ko/posts/')) and rel.removeprefix('locales/ko/') not in allowed:
                fail('article outside declared news scope '+rel)
            if rel.startswith('assets/images/') and not owns_image(rel):
                fail('image outside declared article folders '+rel)
        for url in allowed:
            for rel in [url,'locales/ko/'+url]:
                if rel not in files or not (root/rel).is_file():fail('missing paired release body '+rel)
            for rel in [url,'ko/'+url]:
                if not (site/rel).is_file():fail('missing built article '+rel)
        for lang,name,parse in [('en','assets/app.js',posts),('ko','locales/ko/posts.json',json.loads)]:
            before=parse(git(root,'show',base+':'+name));after=parse((root/name).read_text(encoding='utf8'))
            old={x['url']:x for x in before};new={x['url']:x for x in after}
            if len(new)!=len(after) or set(new)-set(old)!=set(paths) or set(old)-set(new):fail(lang+' metadata URL set mismatch')
            if not set(revised)<=set(old):fail(lang+' revised article missing from baseline metadata')
            if [x['url'] for x in before if x['url'] not in revised]!=[x['url'] for x in after if x['url'] not in allowed]:
                fail(lang+' unrelated metadata ordering changed')
            if any(new.get(k)!=v for k,v in old.items() if k not in revised):fail(lang+' existing metadata modified')
        old_assets=json.loads(git(root,'show',base+':locales/ko/assets.json'));new_assets=json.loads((root/'locales/ko/assets.json').read_text(encoding='utf8'))
        for rel in set(old_assets)|set(new_assets):
            if old_assets.get(rel)!=new_assets.get(rel) and not (owns_image(rel) and rel.startswith('assets/images/ko/news/') and rel in files and rel in new_assets):
                fail('asset binding outside changed article files '+rel)
        for rel in files:
            if rel.startswith('assets/images/ko/') and new_assets.get(rel)!=digest(root/rel):fail('new Korean asset is not bound '+rel)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        fail('baseline/metadata validation error: '+str(exc))
    for rel,expected in files.items():
        if not isinstance(rel,str) or '\\' in rel or '..' in PurePosixPath(rel).parts or PurePosixPath(rel).is_absolute():fail('unsafe release path');continue
        path=root/rel
        if not rel.startswith(('posts/news/','assets/','locales/ko/','tools/','.github/workflows/','docs/','policies/')):fail('disallowed release path '+rel);continue
        if re.search(r'(^|/)(qa|data|local-source-archive|sources|prompts|publish)(/|$)|(?:v_final|v1_draft|fact_sheet|context|image_plan|authorization|receipt)\.(?:json|md)|_base\.(?:png|webp)|_layer\.html',rel):fail('private/source artifact '+rel)
        if rel.startswith(('posts/','assets/images/','locales/ko/posts/')) and path.suffix not in {'.html','.png','.webp','.avif','.jpg','.jpeg','.svg'}:fail('unexpected public file type '+rel)
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in path.parents if p!=root and p.is_relative_to(root)):fail('unsafe linked release path '+rel)
            if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected) or digest(path)!=expected:fail('missing/stale release digest '+rel)
        except OSError:fail('missing release file '+rel)
    if require_proof:
        proof=manifest.get('verification',{})
        for key in ['content_review_sha256','local_publish_gate_sha256']:
            if not re.fullmatch('[0-9a-f]{64}',str(proof.get(key,''))):fail('missing actual local verification '+key)
    return errors
