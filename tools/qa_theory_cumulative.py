"""Cumulative preflight; never grants independent visual/publication approval."""
from __future__ import annotations
import argparse
import collections
import difflib
import hashlib
import itertools
import json
import re
import sys
import importlib.metadata
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
from PIL import Image
from theory_qa_cache import ComputationCache,default_cache_dir,fingerprint

ROOT = Path(__file__).resolve().parents[1]


def norm(s):
    return re.sub(r'[^가-힣A-Za-z0-9]', '', s).lower()


def local_path(base, value):
    u = urlsplit(value)
    if u.scheme or u.netloc:
        raise ValueError('external asset requires separate verification: ' + value)
    return (base / unquote(u.path)).resolve()


def image_hashes(path,cache=None):
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    saved=cache.get('image-dhash',[sha],lambda v:isinstance(v,list) and len(v)==3 and isinstance(v[0],str) and len(v[0])==64 and all(c in '0123456789abcdef' for c in v[0]) and all(type(x)is int and x>0 for x in v[1:])) if cache else None
    if saved is not None:return sha,int(saved[0],16),tuple(saved[1:])
    with Image.open(path) as im:
        gray = im.convert('L').resize((17, 16), Image.Resampling.LANCZOS)
        pixels = list(gray.get_flattened_data()) if hasattr(gray, 'get_flattened_data') else list(gray.getdata())
        bits = [pixels[y*17+x] > pixels[y*17+x+1] for y in range(16) for x in range(16)]
        dh = sum(int(v) << i for i, v in enumerate(bits))
        size = im.size
    if cache:cache.put('image-dhash',[sha],[f'{dh:064x}',*size])
    return sha, dh, size


def text_coverage(a,b):
    blocks=difflib.SequenceMatcher(None,a['body'],b['body'],autojunk=False).get_matching_blocks()
    common_sentences={norm(s) for s in a['sentences']} & {norm(s) for s in b['sentences']}
    def covered(post,side):
        intervals=[(getattr(x,side),getattr(x,side)+x.size) for x in blocks if x.size>=40]
        for sentence in common_sentences:
            start=0
            while True:
                start=post['body'].find(sentence,start)
                if start<0:break
                intervals.append((start,start+len(sentence)));start+=len(sentence)
        end=total=0
        for left,right in sorted(intervals):
            total+=max(0,right-max(left,end));end=max(end,right)
        return total
    return [covered(a,'a'),covered(b,'b')]


def cache_namespace():
    # Rule/code and runtime changes invalidate derived values; mtime is never used.
    return fingerprint({'code':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cache_code':hashlib.sha256(Path(__file__).with_name('theory_qa_cache.py').read_bytes()).hexdigest(),'python':sys.version,'pillow':importlib.metadata.version('Pillow'),'bs4':importlib.metadata.version('beautifulsoup4'),'schema':1})


def metadata(path):
    # Parse only the data literal; no eval or execution of application JavaScript.
    source = path.read_text(encoding='utf-8')
    match = re.search(r'const\s+posts\s*=\s*', source)
    if not match:
        raise ValueError('const posts data not found')
    literal = source[match.end():].split('\n];', 1)[0] + '\n]'
    literal = re.sub(r'([{,]\s*)([A-Za-z_$][\w$]*)\s*:', r'\1"\2":', literal)
    return json.loads(literal)


def audit(root, first, last, threshold=20, cache_dir=None):
    cache=ComputationCache(cache_dir,cache_namespace())
    findings, reviews, posts, images = [], [], [], []
    def finding(code, detail, **kw):
        findings.append(dict(code=code, detail=detail, **kw))
    try:
        meta = metadata(root/'assets/app.js')
    except (ValueError, OSError) as e:
        meta = []
        finding('METADATA_PARSE', str(e))
    for number in range(first, last+1):
        pid = f'{number:03d}'
        matches = list((root/'posts/theory').glob(pid+'-*.html'))
        if len(matches) != 1:
            finding('HTML_COUNT', str(len(matches)), post=pid)
            continue
        path = matches[0]
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        title = soup.select_one('article h1')
        title = title.get_text(' ', strip=True) if title else ''
        nodes = soup.select('article .lead p, article section p, article section li, article section td, article figcaption')
        strings = [x.get_text(' ', strip=True) for x in nodes]
        body = norm(' '.join(strings))
        sentences = [s.strip() for text in strings for s in re.split(r'(?<=[.!?])\s+', text) if len(norm(s)) >= 24]
        post = dict(post=pid, title=title, html=str(path.relative_to(root)), html_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), visible_chars=len(body), body=body, sentences=sentences)
        posts.append(post)
        entries = []
        for row in meta:
            try:
                if local_path(root, row.get('url', '')) == path.resolve(): entries.append(row)
            except ValueError: pass
        if len(entries) != 1:
            finding('METADATA_COUNT', str(len(entries)), post=pid)
        else:
            row = entries[0]
            for key in ('title','date','section','category','summary','thumbnail','thumbnailAlt','url','keywords'):
                if not row.get(key): finding('METADATA_MISSING', key, post=pid)
            if row.get('title') != title or row.get('section') != 'theory':
                finding('METADATA_IDENTITY', 'title or section mismatch', post=pid)
            eyebrow = soup.select_one('article .eyebrow')
            category = eyebrow.get_text(' ',strip=True).rsplit('·',1)[0].strip() if eyebrow else ''
            if row.get('category') != category: finding('METADATA_CATEGORY', category, post=pid)
            byline = soup.select_one('article .byline span')
            if byline and norm(row.get('date','')) != norm(byline.get_text()): finding('METADATA_DATE', byline.get_text(), post=pid)
        for index, tag in enumerate(soup.select('article img')):
            try:
                image = local_path(path.parent, tag.get('src',''))
                image.relative_to(root.resolve())
            except ValueError as e:
                finding('IMAGE_PATH', str(e), post=pid); continue
            if not image.is_file():
                finding('IMAGE_MISSING', str(image), post=pid); continue
            sha, dh, size = image_hashes(image,cache)
            role_match = re.search(r'(thumbnail|body-\d+)', image.stem)
            role = role_match.group(1) if role_match else f'image-{index}'
            rec = dict(post=pid, role=role, path=str(image.relative_to(root.resolve())).replace('\\','/'), sha256=sha, dhash=f'{dh:064x}', size=list(size))
            images.append(rec)
            if not tag.get('alt','').strip(): finding('IMAGE_ALT', rec['path'], post=pid)
            if index == 0 and len(entries) == 1:
                try:
                    if local_path(root, entries[0].get('thumbnail','')) != image: finding('METADATA_THUMBNAIL', rec['path'],post=pid)
                except ValueError as e: finding('METADATA_THUMBNAIL',str(e),post=pid)
                if entries[0].get('thumbnailAlt') != tag.get('alt'):
                    reviews.append(dict(code='ALT_TEXT_DIFFERENCE',post=pid,detail='listing and article alt differ; confirm both describe current image'))
            # Require the actual image version, not an older design from any ancestor.
            version = image.parent.name
            series = next((a for a in image.parents if re.fullmatch(r'series-\d+',a.name)),None)
            design = series/'sources'/pid/version/'visual_design.json' if series else None
            if not design or not design.is_file():
                # A source revision may explicitly produce a differently named asset revision.
                # Accept only a unique exact final path, never a basename/old-plan fallback.
                explicit=[]
                for candidate in sorted((series/'sources'/pid).glob('*/visual_design.json')) if series else []:
                    try: candidate_data=json.loads(candidate.read_text(encoding='utf-8'))
                    except (ValueError,OSError): continue
                    for entry in candidate_data.get('images',[]):
                        target=entry.get('final_asset_path')
                        if target and local_path(root,target)==image:
                            explicit.append(candidate);break
                if len(explicit)==1:
                    design=explicit[0]
                    reviews.append(dict(code='EXPLICIT_CROSS_VERSION_SOURCE',post=pid,image=rec['path'],design=str(design.relative_to(root.resolve())),detail='Unique exact final_asset_path mapping; inspect source revision correspondence manually.'))
                else:
                    finding('CURRENT_DESIGN_MISSING', str(design),post=pid,image=rec['path'],explicit_matches=len(explicit)); continue
            rec['design'] = str(design.relative_to(root.resolve()))
            if not design.with_suffix('.md').is_file(): finding('DESIGN_MD_MISSING',rec['design'],post=pid)
            try: data=json.loads(design.read_text(encoding='utf-8'))
            except ValueError as e: finding('DESIGN_PARSE',str(e),post=pid);continue
            candidates=[x for x in data.get('images',[]) if x.get('role')==role or Path(x.get('png',x.get('file',''))).name==image.name]
            if len(candidates)!=1:
                finding('DESIGN_IMAGE_MATCH',f'{len(candidates)} matches',post=pid,image=rec['path']);continue
            item=candidates[0]; sig=item.get('composition_signature')
            if not sig: finding('SIGNATURE_MISSING',rec['path'],post=pid);continue
            rec['signature']=sig
            rec['signature_normalized']=norm(json.dumps(sig,ensure_ascii=False,sort_keys=True) if not isinstance(sig,str) else sig)
            # Removing only article-title tokens catches cosmetic renaming, but is heuristic.
            sk=rec['signature_normalized']
            for token in sorted(re.findall(r'[가-힣A-Za-z]{2,}',title),key=len,reverse=True): sk=sk.replace(norm(token),'')
            rec['signature_without_title']=sk
            dimensions=('screen_split','panel_position','subject_position','flow_direction','camera_view','graph_type')
            rec['composition_dimensions']={k:item[k] for k in dimensions if k in item}
    ownership=collections.defaultdict(dict)
    for p in posts:
        for s in p['sentences']: ownership[norm(s)][p['post']]=s
    for s,owners in ownership.items():
        if len(owners)>=3: finding('SENTENCE_IN_THREE_POSTS',next(iter(owners.values())),posts=list(owners))
    text_pairs=[]
    text_keys={p['post']:fingerprint([p['body'],p['sentences']]) for p in posts}
    for a,b in itertools.combinations(posts,2):
        # Exact contiguous normalized text, not fuzzy semantic equivalence; 40-char floor avoids terminology alone.
        key=[text_keys[a['post']],text_keys[b['post']]]
        coverage=cache.get('text-pair',key,lambda v:isinstance(v,list) and len(v)==2 and all(type(x)is int and 0<=x<=len(p['body']) for x,p in zip(v,[a,b])))
        if coverage is None:
            coverage=text_coverage(a,b);cache.put('text-pair',key,coverage)
        ca,cb=coverage
        common=min(ca,cb)
        ra=ca/max(1,len(a['body']));rb=cb/max(1,len(b['body']))
        if max(ra,rb)>=.15:
            rec=dict(posts=[a['post'],b['post']],matched_chars=common,ratios=[round(ra,4),round(rb,4)])
            text_pairs.append(rec);finding('BODY_OVERLAP_15_PERCENT','exact sentences >=24 characters plus contiguous matches >=40; overlapping spans counted once',**rec)
    for a,b in itertools.combinations(images,2):
        pair=[a['path'],b['path']]
        distance=(int(a['dhash'],16)^int(b['dhash'],16)).bit_count()
        if a['path']==b['path']: finding('DUPLICATE_IMAGE_REFERENCE','same actual path',images=pair)
        elif a['sha256']==b['sha256']: finding('IDENTICAL_IMAGE_SHA256','identical file content',images=pair)
        elif distance<=threshold: finding('PERCEPTUAL_SIMILARITY','manual inspection required; dHash is not semantic proof',distance=distance,images=pair)
        if a.get('signature_normalized') and a.get('signature_normalized')==b.get('signature_normalized'):
            finding('IDENTICAL_COMPOSITION_SIGNATURE','same composition signature',images=pair)
        elif a.get('signature_normalized') and b.get('signature_normalized'):
            sa=a['signature_without_title'];sb=b['signature_without_title']
            ratio=difflib.SequenceMatcher(None,sa,sb).ratio()
            dims=a['composition_dimensions'];same=[k for k,v in dims.items() if b['composition_dimensions'].get(k)==v]
            if (sa and sa==sb) or ratio>=.7 or len(same)>=3:
                reviews.append(dict(code='SIMILAR_COMPOSITION',images=pair,similarity=round(ratio,3),same_dimensions=same,detail='제목 단어 변경으로 서명 중복을 우회할 수 있습니다. 실제 구도를 수동 판정하세요.'))
    for p in posts: p.pop('body');p.pop('sentences')
    cache.close();statistics=cache.stats()
    return dict(range=[first,last],status='FAIL' if findings else 'PREFLIGHT_PASS',scope='AUTOMATED_PREFLIGHT_ONLY',independent_visual_approval=False,release_authorized=False,release_blocked=True,findings=findings,manual_review=reviews,posts=posts,images=images,text_overlap=text_pairs,computation_cache=statistics,limitations=['범위는 사용자가 지정한 승인 대상 범위이며 기존 승인/봉인을 읽거나 변경하지 않습니다.','의미가 같은 의역, 이미지 임베딩, 과학 정확성, 모바일 판독성은 판정하지 않습니다.','dHash 256-bit는 후보 탐지이며 재사용 확정/부정 근거가 아닙니다.','제목 제거 서명 비교는 휴리스틱입니다. 새/변경 이미지 및 미해결 후보의 원본·390px 독립 검토가 별도로 필요하며 변경 없는 과거 승인 재사용은 해시 결합 증거를 요구합니다.','문장 3편 반복은 일반론인지 사람이 판정하며 동일문구 후보를 보수적으로 차단합니다.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first',type=int,required=True);parser.add_argument('--last',type=int,required=True)
    parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--dhash-threshold',type=int,default=20)
    parser.add_argument('--cache-dir',type=Path,default=default_cache_dir())
    parser.add_argument('--no-cache',action='store_true',help='Full recomputation for audit/recovery; same decision rules')
    args=parser.parse_args()
    if not 1<=args.first<=args.last: parser.error('require 1 <= first <= last')
    root=args.root.resolve();result=audit(root,args.first,args.last,args.dhash_threshold,None if args.no_cache else args.cache_dir)
    out=root/f'qa/theory/cumulative_{args.first:03d}_{args.last:03d}'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f'# 누적 QA {args.first:03d}–{args.last:03d}', '',f"판정: **{result['status']}**. 자동 PASS는 독립 승인이나 게시 승인이 아닙니다.",'',f"차단 후보 {len(result['findings'])}건 / 수동 확인 {len(result['manual_review'])}건",'','## 차단 후보']
    lines += ['- '+json.dumps(x,ensure_ascii=False) for x in result['findings']]
    lines += ['','## 유사 구도·메타데이터 수동 판정']+['- '+json.dumps(x,ensure_ascii=False) for x in result['manual_review']]
    lines += ['','## 적용 한계']+['- '+x for x in result['limitations']]
    out.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],findings=len(result['findings']),manual_review=len(result['manual_review']),output=str(out)),ensure_ascii=False))
    return 1 if result['findings'] else 0

if __name__=='__main__':
    raise SystemExit(main())
