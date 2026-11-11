"""Strict existing-article maintenance checks; never approve legacy production debt."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
from collections import Counter
from datetime import datetime
from bs4 import BeautifulSoup

PRIVATE_DIRS = {'authorizations', 'claude', 'history', 'news', 'releases', 'theory'}

def sha_bytes(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()

def safe_path(root, name):
    if not isinstance(name, str) or '\\' in name or ':' in name:
        raise ValueError('invalid relative path')
    parts=PurePosixPath(name)
    if parts.is_absolute() or '..' in parts.parts or not name or name.startswith('./'):
        raise ValueError('path escape')
    p=(Path(root)/name).resolve()
    if not p.is_relative_to(Path(root).resolve()): raise ValueError('path escape')
    return p

def private_qa(name):
    p=PurePosixPath(name)
    return len(p.parts)>2 and p.parts[0]=='qa' and p.parts[1] in PRIVATE_DIRS

def canonical_scope(manifest):
    return hashlib.sha256(json.dumps({k:v for k,v in manifest.items() if k!='release_proof'},
                                    ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def git(site,*args):
    return subprocess.check_output(['git','-C',str(site),*args],text=True,encoding='utf-8').strip()

def source_delta(site,base):
    names=set(git(site,'diff','--name-only',base).splitlines())
    names.update(git(site,'ls-files','--others','--exclude-standard').splitlines())
    return names

def scope_errors(manifest,site,built=None,require_proof=False):
    """Public CI checks; private original reviews remain mandatory locally."""
    errors=[];site=Path(site)
    try:
        if manifest.get('kind')!='editorial-maintenance' or manifest.get('new_posts')!=[]:
            errors.append('MAINT scope: wrong kind or new posts')
        base=manifest.get('base_commit','')
        if not re.fullmatch('[0-9a-f]{40}',base): raise ValueError('invalid base commit')
        changes=manifest.get('repository_changes',{})
        if not isinstance(changes,dict) or not changes: raise ValueError('empty source map')
        base_paths=set(git(site,'ls-tree','-r','--name-only',base).splitlines())
        for name,h in changes.items():
            p=safe_path(site,name)
            if not re.fullmatch('[0-9a-f]{64}',str(h)) or not p.is_file() or sha_bytes(p.read_bytes())!=h:
                errors.append('MAINT scope: changed/missing source '+name)
            if name.startswith(('posts/theory/','locales/ko/posts/theory/','assets/','qa/')):
                errors.append('MAINT scope: forbidden source '+name)
            if name.endswith('.html') and '/posts/' in '/'+name:
                if not re.match(r'^(?:locales/ko/)?posts/(?:history|news|concepts)/[^/]+\.html$',name):
                    errors.append('MAINT scope: forbidden article '+name)
                if name not in base_paths:
                    errors.append('MAINT scope: new article '+name)
            elif name.endswith('.html') and name!='editorial-policy.html':
                errors.append('MAINT scope: unapproved page kind '+name)
            elif not (name.endswith('.html') or name in {'.gitignore','locales/ko/posts.json','locales/ko/ui.json','policies/quality_gates.json','.github/workflows/deploy-pages.yml'} or re.fullmatch(r'tools/[^/]+\.py',name)):
                errors.append('MAINT scope: unsupported repository change '+name)
        actual=source_delta(site,base)
        deleted={n for n in actual if private_qa(n) and not safe_path(site,n).exists()}
        expected=set(changes)|deleted|{'qa/deployments/current.json'}
        if actual!=expected: errors.append('MAINT scope: undeclared/missing delta '+str(sorted(actual^expected)))
        tracked=git(site,'ls-files','qa').splitlines()
        if any(n!='qa/deployments/current.json' and safe_path(site,n).exists() for n in tracked):
            errors.append('MAINT scope: private QA still public')
        features=manifest.get('changed_features',[])
        expected_html={n for n in changes if n.endswith('.html')}
        expected_pairs={(n,'ko/'+n[len('locales/ko/'):] if n.startswith('locales/ko/') else n) for n in expected_html}
        if 'editorial-policy.html' in expected_html:expected_pairs.add(('editorial-policy.html','ko/editorial-policy.html'))
        seen=set()
        for row in features:
            src=row.get('source_path');target=row.get('path')
            if (src,target) in seen: errors.append('MAINT scope: duplicate feature')
            seen.add((src,target))
            if src not in expected_html or row.get('sha256')!=changes.get(src) or not row.get('feature') or not row.get('reason'):
                errors.append('MAINT scope: incomplete feature')
            if (src,target) not in expected_pairs: errors.append('MAINT scope: wrong built counterpart')
            if built and not safe_path(built,target).is_file(): errors.append('MAINT scope: missing built counterpart '+str(target))
        if seen!=expected_pairs: errors.append('MAINT scope: incomplete HTML coverage')
        if built:
            if (Path(built)/'qa').exists() or (Path(built)/'data').exists(): errors.append('MAINT scope: private package content')
            for extra in ['editorial-policy.html','ko/editorial-policy.html']:
                if not (Path(built)/extra).is_file(): errors.append('MAINT scope: missing policy counterpart')
        if require_proof:
            proof=manifest.get('release_proof',{})
            if proof.get('scope_sha256')!=canonical_scope(manifest) or proof.get('status')!='PASS':
                errors.append('MAINT scope: invalid local proof binding')
            for key in ['record_sha256','receipt_sha256','review_manifest_sha256']:
                if not re.fullmatch('[0-9a-f]{64}',str(proof.get(key,''))): errors.append('MAINT scope: missing proof '+key)
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as exc:
        errors.append('MAINT scope: '+str(exc))
    return errors

def skeleton(data):
    doc=BeautifulSoup(data.decode('utf-8-sig'),'html.parser')
    for tag in list(doc.select('figcaption, footer.source')):tag.decompose()
    for head in doc.find_all(['h2','h3']):
        if re.match(r'^(참고\s*문헌|참고\s*자료|출처|자료\s*출처)',head.get_text(strip=True)):
            nxt=head.find_next_sibling()
            if nxt and nxt.name in ['ol','ul']:nxt.decompose()
    return str(doc)

def protected_errors(before,after):
    a=BeautifulSoup(before.decode('utf-8-sig'),'html.parser');b=BeautifulSoup(after.decode('utf-8-sig'),'html.parser')
    errors=[]
    for tag in ['head','img','script','style','table','math','svg','iframe','form']:
        if [str(t) for t in a.find_all(tag)]!=[str(t) for t in b.find_all(tag)]:errors.append('changed '+tag)
    if skeleton(before)!=skeleton(after):errors.append('changed narrative/structure')
    return errors

def receipt_errors(root,entry,kind,checkpoint,author):
    """Bind every original request/response/input, not a reviewer name string."""
    from project_quality_gate import digest,read
    from claude_review_gate import review_errors
    rc_path=safe_path(root,entry['receipt']);rc=read(rc_path)
    if digest(rc_path)!=entry['sha256']:return ['receipt changed'],None
    rq=read(safe_path(root,rc['request']))
    manifest={'version':1,'kind':kind,'reviews':{checkpoint:entry}}
    errors=review_errors(manifest,root,kind,[checkpoint],rq.get('inputs',{}),author)
    return errors,rc.get('session_id')

def shard_binding_errors(root,shard):
    from project_quality_gate import read,digest
    errors=[]
    try:
        rc=read(safe_path(root,shard['receipt']));rq=read(safe_path(root,rc['request']))
        for key in ['map','packet']:
            n=shard[key]
            if rq.get('inputs',{}).get(n)!=digest(safe_path(root,n)):errors.append('shard mapping/packet not in actual review inputs')
        rows=read(safe_path(root,shard['map']))['files']
        paths=[r['path'] for r in rows]
        if len(paths)!=len(set(paths)) or set(paths)!=set(shard['paths']):errors.append('shard paths differ from actually reviewed map')
        for row in rows:
            p=safe_path(Path(root)/'GlobalNuclearNews',row['path'])
            observed=sha_bytes(p.read_bytes()) if row.get('hash_mode')=='lf-normalized' else hashlib.sha256(p.read_bytes()).hexdigest()
            if observed!=row['after_sha256']:errors.append('shard current file changed '+row['path'])
    except (KeyError,ValueError,TypeError,OSError) as exc:errors.append('invalid shard binding: '+str(exc))
    return errors

def shard_errors(root,shards,expected,author):
    errors=[];seen=set();sessions=set()
    for shard in shards:
        paths=shard.get('paths',[])
        if not paths or len(set(paths))!=len(paths) or seen.intersection(paths):errors.append('missing/duplicate/overlapping shard coverage')
        seen.update(paths)
        found,session=receipt_errors(root,shard,'editorial-maintenance','final',author)
        errors.extend(found)
        errors.extend(shard_binding_errors(root,shard))
        if session in sessions:errors.append('reused shard session')
        sessions.add(session)
    if seen!=set(expected):errors.append('incomplete shard coverage')
    return errors

def review_order_errors(root,record,shards):
    from project_quality_gate import read
    try:
        manifest=read(safe_path(root,record['checks']['COMMON-05']['claude_review']))
        phases={k:read(safe_path(root,manifest['reviews'][k]['receipt'])) for k in ['design','final']}
        design_end=datetime.fromisoformat(phases['design']['finished_at']);final_start=datetime.fromisoformat(phases['final']['started_at'])
        if design_end.tzinfo is None or final_start.tzinfo is None:return ['naive maintenance checkpoint timestamp']
        errors=[];sessions={v['session_id'] for v in phases.values()}
        for shard in shards:
            rc=read(safe_path(root,shard['receipt']))
            start=datetime.fromisoformat(rc['started_at']);end=datetime.fromisoformat(rc['finished_at'])
            if start.tzinfo is None or end.tzinfo is None or start<design_end or end>final_start:errors.append('content review outside design/final order')
            if rc['session_id'] in sessions:errors.append('content session reused as design/integration')
            sessions.add(rc['session_id'])
        return errors
    except (KeyError,ValueError,TypeError,OSError) as exc:return ['missing/invalid review order: '+str(exc)]

def maintenance_errors(record,root):
    """Called by the local project gate for every maintenance publish validation."""
    from project_quality_gate import digest,read
    errors=[];root=Path(root);site=root/'GlobalNuclearNews'
    try:
        name=record.get('maintenance')
        if name not in record['artifacts']:raise ValueError('maintenance contract not bound')
        if digest(safe_path(root,name))!=record['artifacts'][name]:raise ValueError('maintenance contract changed')
        contract=read(safe_path(root,name))
        required={contract[k] for k in ['public_scope','change_manifest','transform','move_manifest']}
        if not required.issubset(set(contract['evidence_inputs'])):raise ValueError('required maintenance inputs not bound')
        for n in contract['evidence_inputs']:
            if n not in record['artifacts'] or digest(safe_path(root,n))!=record['artifacts'][n]:raise ValueError('unbound/changed maintenance input '+n)
        public=read(site/'qa/deployments/current.json')
        core=read(safe_path(root,contract['public_scope']))
        if canonical_scope(public)!=canonical_scope(core):errors.append('public scope drift')
        errors.extend(scope_errors(public,site))
        if public['base_commit']!=contract['base_commit']:errors.append('base commit mismatch')
        source_map=contract['source_files']
        if source_map!=public['repository_changes']:errors.append('source map mismatch')
        rows=read(safe_path(root,contract['change_manifest']))['files']
        article_names={r['path'] for r in rows}
        if len(article_names)!=len(rows) or article_names!={n for n in source_map if re.match(r'^(?:locales/ko/)?posts/',n)}:
            errors.append('changed article set mismatch')
        archive=subprocess.check_output(['git','-C',str(site),'archive',contract['base_commit'],'posts','locales/ko/posts'])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            originals={m.name:tar.extractfile(m).read() for m in tar if m.name in article_names}
        # Pure functions only: the original transformer main/process is never called.
        transform=safe_path(root,contract['transform'])
        saved=sys.argv
        try:
            sys.argv=['rights_revision.py',str(site),'dry']
            spec=importlib.util.spec_from_file_location('_maintenance_transform',transform)
            mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        finally:sys.argv=saved
        for row in rows:
            n=row['path'];before=originals[n];after=safe_path(site,n).read_bytes()
            if sha_bytes(before)!=row['sha256_before'] or sha_bytes(after)!=row['sha256_after']:errors.append('article hash drift '+n)
            errors.extend(n+': '+e for e in protected_errors(before,after))
            text=before.decode('utf-8').replace('\r\n','\n');sec=Path(n).parent.name;stats=Counter();manual=[]
            if n.startswith('locales/ko/'):
                text=mod.ko_credits(text,(site/'posts'/sec/Path(n).name).read_text(encoding='utf-8'),sec,Path(n).name,stats,manual)
                text=mod.captions(text,lambda c:mod.link_licences(c,stats))
                text=mod.ref_entries_ko(text,lambda e:mod.complete_bib(mod.link_entry(e,stats),stats))
            else:
                text=mod.captions(text,lambda c:mod.link_licences(c,stats))
                if sec=='news':text=mod.captions(text,lambda c:mod.news_caption(c,stats))
                text=mod.ref_entries_en(text,lambda e:mod.complete_bib(e,stats))
                text=mod.en_footer_bare_urls(text,stats)
            if sec=='history':
                for old in mod.HTTPS_HOSTS:text=text.replace(old,'https://'+old[len('http://'):])
            if manual or text!=after.decode('utf-8').replace('\r\n','\n'):errors.append('unclassified transformation '+n)
        deleted={n for n in source_delta(site,contract['base_commit']) if private_qa(n) and not safe_path(site,n).exists()}
        moved=read(safe_path(root,contract['move_manifest']))['files']
        if deleted!=set(moved):errors.append('private archive deletion set mismatch')
        for n,h in moved.items():
            p=safe_path(root,contract['archive_base']+'/'+n)
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('private archive missing/changed '+n)
        errors.extend(shard_errors(root,contract['shards'],article_names,record['author']))
        errors.extend(review_order_errors(root,record,contract['shards']))
    except (ValueError,KeyError,TypeError,OSError,AttributeError,subprocess.SubprocessError) as exc:
        errors.append('invalid maintenance evidence: '+str(exc))
    return ['MAINT: '+e for e in errors]
