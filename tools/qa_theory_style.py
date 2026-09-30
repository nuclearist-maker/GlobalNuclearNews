from pathlib import Path
from bs4 import BeautifulSoup
import argparse, collections, hashlib, json, re, sys

ROOT=Path(__file__).resolve().parents[1]
NON_HONORIFIC=re.compile(r'(?<!니)다\.$')
HONORIFIC=re.compile(r'(?:합니다|입니다|됩니다|있습니다|없습니다|보여줍니다|나타냅니다|사용합니다|확인합니다|정합니다|읽습니다|뜻합니다|같습니다|아닙니다|필요합니다|중요합니다|가능합니다|구분합니다|적용합니다|해석합니다|계산합니다|변합니다|달라집니다|이어집니다|남습니다|줄어듭니다|커집니다|작아집니다)\.$')

def sentences(text):
    return [re.sub(r'\s+',' ',x).strip() for x in re.split(r'(?<=[.!?])\s+',text) if len(x.strip())>=18]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--first',type=int,required=True); ap.add_argument('--last',type=int,required=True); ap.add_argument('--compare-first',type=int,default=1); args=ap.parse_args()
    findings=[]; per={}; all_sent=collections.defaultdict(list)
    files={int(p.name[:3]):p for p in (ROOT/'posts/theory').glob('*.html') if p.name[:3].isdigit()}
    for n in range(args.compare_first,args.last+1):
        p=files.get(n)
        if not p: findings.append(f'{n:03d}: HTML 누락'); continue
        soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
        for citation in soup.select('a.citation'): citation.decompose()
        nodes=soup.select('main section p, main .lead p, main figcaption')
        visible=' '.join(x.get_text(' ',strip=True) for x in nodes)
        local=[]
        for node in nodes:
            for s in sentences(node.get_text(' ',strip=True)):
                if NON_HONORIFIC.search(s): local.append(f'비경어체: {s}')
                norm=re.sub(r'[^가-힣A-Za-z0-9]','',s)
                if len(norm)>=24: all_sent[hashlib.sha256(norm.encode()).hexdigest()].append((n,s))
        per[f'{n:03d}']={'visible_chars':len(re.sub(r'\s+','',visible)),'non_honorific':len(local),'findings':local}
        if args.first<=n<=args.last and local: findings.extend(f'{n:03d}: {x}' for x in local)
    for vals in all_sent.values():
        posts=sorted({n for n,_ in vals})
        if len(posts)>=3 and any(args.first<=n<=args.last for n in posts):
            findings.append(f'반복문장 {posts}: {vals[0][1]}')
    result={'range':[args.first,args.last],'compare_range':[args.compare_first,args.last],'status':'PASS' if not findings else 'FAIL','finding_count':len(findings),'posts':per,'findings':findings}
    out=ROOT/f'qa/theory/style_qa_{args.first:03d}_{args.last:03d}.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'finding_count':len(findings),'output':str(out)},ensure_ascii=False)); sys.exit(1 if findings else 0)

if __name__=='__main__': main()
