from pathlib import Path
from PIL import Image, ImageChops
import argparse, json, re, sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--first',type=int,default=1); ap.add_argument('--last',type=int,default=5); args=ap.parse_args()
    findings=[]; checked=0
    forbidden=[r'(?<![<\w])T1/2',r'10-\d+',r'\b(?:U|C|H)-\d+\b']
    for n in range(args.first,args.last+1):
        num=f'{n:03d}'; src=ROOT/f'assets/images/theory/series-01/sources/{num}/pilot-v5'; mf=src/'formula_manifest.json'
        if not mf.exists(): findings.append(f'{num}: formula_manifest.json 누락'); continue
        data=json.loads(mf.read_text(encoding='utf-8'))
        for ent in data['images']:
            checked+=1; hp=src/ent['html']; pp=ROOT/'assets/images/theory/series-01/pilot-v5'/ent['png']
            if not hp.exists() or not pp.exists(): findings.append(f'{num}: {ent["html"]} 또는 PNG 누락'); continue
            h=hp.read_text(encoding='utf-8')
            for token in ent['required_tokens']:
                if token not in h: findings.append(f'{num} {ent["html"]}: 필수 토큰 누락 {token}')
            for pat in forbidden:
                if re.search(pat,h): findings.append(f'{num} {ent["html"]}: 평문 수식 금지 패턴 {pat}')
            if '\ufffd' in h or '□' in h: findings.append(f'{num} {ent["html"]}: 대체 글리프 포함')
            im=Image.open(pp).convert('RGB')
            if im.size!=(1600,900): findings.append(f'{num} {ent["png"]}: 규격 {im.size}')
            mobile=im.resize((390,219),Image.Resampling.LANCZOS)
            if ImageChops.difference(mobile,Image.new('RGB',mobile.size,mobile.getpixel((0,0)))).getbbox() is None: findings.append(f'{num} {ent["png"]}: 모바일 렌더가 단색')
    result={'range':[args.first,args.last],'checked_formula_images':checked,'finding_count':len(findings),'status':'PASS' if not findings else 'FAIL','findings':findings}
    out=ROOT/f'qa/theory/formula_qa_{args.first:03d}_{args.last:03d}.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2)); sys.exit(1 if findings else 0)

if __name__=='__main__': main()
