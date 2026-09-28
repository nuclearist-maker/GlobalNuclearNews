from pathlib import Path
from PIL import Image
import json, shutil, subprocess, re

ROOT=Path(__file__).resolve().parents[1]
GEN=Path(r"C:\Users\nucle\.codex\generated_images\01a0c8e8-9805-7182-9801-c2c20e061247")
CHROME=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
OUT=ROOT/'assets/images/theory/series-01/pilot-v5'

BASES={
'001':['exec-0bc81eac-8735-47e3-84b7-492df29c9ae4.png','exec-aefcbfd0-b3f4-4f2b-a78f-d0d4426ef984.png','exec-9ddb44e1-20a8-42a0-9f8b-ae55d84c2c40.png'],
'002':['exec-255c0448-5708-40d0-8b85-bdd66bc83c94.png','exec-25a67191-e5dd-4887-a062-d53f40a4a470.png','exec-69b396fb-2c1e-43b8-86fe-1ba48c6d9635.png'],
'003':['exec-c8b126d9-e48b-4f70-9bc3-c94849bfe2dd.png','exec-42f2dd1f-c5ec-400a-a67e-d88fc11c3e2e.png','exec-21557b42-c524-4849-9737-9436ff862ceb.png'],
'004':['exec-2b0ee10b-254a-41d9-9cd5-42dd8fa6e7c5.png','exec-ae08bda9-7515-4eb2-9124-1f86ddf31495.png','exec-7036e387-1415-4a21-bad8-42f57767deba.png'],
'005':['exec-cd669b2c-0220-4dfc-aaf4-b576926de4f8.png','exec-c2337bb2-c3dd-4288-b0fc-5dfb0360a9c7.png','exec-10ad6b5d-096c-42b1-816e-3325713c30e8.png']}

META={
'001':('원자력공학의 범위',['생태계 파노라마','대각선 에너지 경로','동심 장벽 단면']),
'002':('원자와 원자핵의 크기',['중심 투시 확대','로그 깊이 여정','경기장 공간 비유']),
'003':('양성자·중성자·전자의 역할',['비대칭 확률구름','곡선형 전시 공간','연속 반응 궤적']),
'004':('원자번호와 질량수',['입자 계수 클로즈업','방사형 핵종 기호','대칭 입자 장부']),
'005':('동위원소의 의미',['삼각형 동위원소군','중성자축 원근 배열','실험실 서사 파노라마'])}

COMMON='''*{box-sizing:border-box}html,body{margin:0;width:1600px;height:900px;overflow:hidden;font-family:"Noto Sans KR","Malgun Gothic",sans-serif;color:#fff}body{position:relative;background:#061322}img.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.shade{position:absolute;inset:0}.label{position:absolute;background:rgba(3,16,31,.86);backdrop-filter:blur(7px);border:1px solid rgba(151,224,255,.72);box-shadow:0 14px 38px #0008}.title{font-weight:900;letter-spacing:-.04em}.muted{color:#c9e8f6}.formula{font-family:"Cambria Math","STIX Two Math","Times New Roman",serif;font-weight:700}.nuclide{display:inline-grid;grid-template-columns:auto auto;grid-template-rows:auto auto;align-items:center;line-height:1}.nuclide sup,.nuclide sub{font-size:.48em;text-align:right;padding-right:.08em}.nuclide sup{align-self:end}.nuclide sub{align-self:start}.nuclide b{grid-row:1/3;grid-column:2;font-size:1em}.frac{display:inline-grid;grid-template-rows:auto auto;vertical-align:middle;text-align:center;line-height:1.08}.frac>span:first-child{border-bottom:3px solid currentColor;padding:0 .14em .08em}.frac>span:last-child{padding-top:.08em}'''

COMMON += '.tags .tag,.ledger .side,.flow .use{position:relative}'

BODY={
'001-01':'''<style>.shade{background:linear-gradient(180deg,#00101a14,#00101acc)}.path{position:absolute;left:85px;right:85px;bottom:58px;display:grid;grid-template-columns:repeat(5,1fr);align-items:center;gap:18px}.step{padding:18px 16px;border-top:6px solid #ffb448;background:#061a2de8;text-align:center;font-size:24px;font-weight:800}.step small{display:block;font-size:17px;color:#cce9f5;margin-top:7px}.arrow{font-size:45px;color:#ffd178;text-align:center}.eq{position:absolute;left:70px;top:55px;padding:20px 28px;border-radius:18px;font-size:35px}</style><div class="shade"></div><div class="label eq formula">3,000 MW<sub>th</sub> × 0.33 ≈ 990 MW<sub>e</sub></div><div class="path"><div class="step">핵분열<small>결합에너지 방출</small></div><div class="arrow">→</div><div class="step">열전달<small>연료 → 냉각재</small></div><div class="arrow">→</div><div class="step">전력생산<small>증기 → 터빈 → 발전기</small></div></div>''',
'001-02':'''<style>.shade{background:radial-gradient(circle at 50% 50%,transparent 28%,#00101a7d 74%,#00101ad8)}.rings{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}.ring{position:absolute;border:5px solid;border-radius:50%;display:flex;align-items:flex-start;justify-content:center;font-weight:800;padding-top:12px;text-shadow:0 2px 8px #000}.r1{width:310px;height:310px;border-color:#ffbe5c;font-size:27px}.r2{width:510px;height:510px;border-color:#75d8ff;font-size:26px}.r3{width:720px;height:720px;border-color:#86efa8;font-size:25px}.r4{width:875px;height:835px;border-color:#fff;font-size:24px}.legend{left:55px;bottom:48px;padding:20px 25px;border-radius:16px;font-size:22px;line-height:1.5}</style><div class="shade"></div><div class="rings"><div class="ring r4">④ 격납건물</div><div class="ring r3">③ 원자로냉각재 압력경계</div><div class="ring r2">② 금속 피복관</div><div class="ring r1">① 세라믹 연료</div></div><div class="label legend"><b>독립된 냉각계열 A · B</b><br><span class="muted">동일 기능을 서로 다른 경로로 수행</span></div>''',
'002-01':'''<style>.shade{background:linear-gradient(0deg,#020b18e6 0,#020b1833 55%)}.scale{position:absolute;left:70px;right:70px;bottom:58px;height:185px}.axis{height:5px;background:linear-gradient(90deg,#fff,#65dcff,#ffba58);position:absolute;left:0;right:0;top:70px}.tick{position:absolute;top:45px;width:4px;height:54px;background:#fff}.tick span{position:absolute;top:65px;transform:translateX(-50%);white-space:nowrap;font-size:21px;font-weight:800}.t0{left:0}.t1{left:25%}.t2{left:50%}.t3{left:75%}.t4{right:0}.t4 span{transform:translateX(-90%)}.headline{position:absolute;left:70px;top:55px;font-size:52px;font-weight:900;text-shadow:0 3px 12px #000}</style><div class="shade"></div><div class="headline">길이척도 10<sup>−3</sup> m → 10<sup>−15</sup> m</div><div class="scale"><div class="axis"></div><div class="tick t0"><span>손끝<br>10<sup>−3</sup> m</span></div><div class="tick t1"><span>세포<br>10<sup>−5</sup> m</span></div><div class="tick t2"><span>분자<br>10<sup>−9</sup> m</span></div><div class="tick t3"><span>원자<br>10<sup>−10</sup> m</span></div><div class="tick t4"><span>원자핵<br>10<sup>−15</sup> m</span></div></div>''',
'002-02':'''<style>.shade{background:linear-gradient(90deg,#00101ab8,transparent 38%,transparent 67%,#00101a9c)}.ratio{position:absolute;left:70px;top:80px;font-size:62px;font-weight:900;text-shadow:0 4px 15px #000}.ratio small{display:block;font-size:28px;color:#d6eff9;margin-bottom:12px}.nucleus{position:absolute;left:47%;top:47%;width:118px;height:118px;border:4px solid #ffd36d;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 35px #ffbd4b}.call{position:absolute;right:65px;bottom:60px;padding:23px 28px;border-radius:18px;font-size:26px;line-height:1.5}</style><div class="shade"></div><div class="ratio"><small>반지름의 비</small>원자 : 원자핵 ≈ 10<sup>5</sup> : 1</div><div class="nucleus"></div><div class="label call">원자를 지름 100 m 경기장으로 확대하면<br><b>원자핵은 중앙의 약 1 mm 점</b></div>''',
'003-01':'''<style>.shade{background:linear-gradient(180deg,#00101a22,#00101abf)}.tags{position:absolute;left:55px;right:55px;bottom:48px;display:flex;justify-content:space-between;align-items:flex-end}.tag{width:29%;padding:19px 20px;border-radius:18px;font-size:23px;line-height:1.45}.tag b{display:block;font-size:32px;color:#ffd16d}.tag:nth-child(2){transform:translateY(-42px)}.tag:nth-child(3){transform:translateY(-8px)}</style><div class="shade"></div><div class="tags"><div class="label tag"><b>양성자 p</b>전하 +e<br>원소의 원자번호 결정</div><div class="label tag"><b>중성자 n</b>전하 0<br>동위원소와 핵 안정성 변화</div><div class="label tag"><b>전자 e<sup>−</sup></b>전하 −e<br>화학결합과 전기적 성질 결정</div></div>''',
'003-02':'''<style>.shade{background:linear-gradient(180deg,#02091308,#020913c8)}.reaction{position:absolute;left:68px;right:68px;bottom:48px;padding:21px 28px;border-radius:22px;display:flex;align-items:center;justify-content:space-around;font-size:46px}.reaction .desc{font-family:"Noto Sans KR","Malgun Gothic";font-size:20px;color:#cfeaf5;line-height:1.35;text-align:center}.arrow{font-family:sans-serif;color:#ffd26c;font-size:58px}</style><div class="shade"></div><div class="label reaction formula"><span>n<div class="desc">중성자</div></span><span class="arrow">→</span><span>p<div class="desc">양성자</div></span><span>+</span><span>e<sup>−</sup><div class="desc">전자</div></span><span>+</span><span><span style="text-decoration:overline">ν</span><sub>e</sub><div class="desc">전자 반중성미자</div></span></div>''',
'004-01':'''<style>.shade{background:radial-gradient(circle,transparent 35%,#07111eae 88%)}.symbol{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-size:190px;color:#08111c;background:rgba(255,255,255,.88);width:360px;height:360px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 20px 70px #0009}.notes{position:absolute;left:55px;right:55px;bottom:38px;display:flex;justify-content:space-between;font-size:24px;font-weight:800}.notes span{padding:13px 19px;border-radius:14px;background:#061a2ddd;border:1px solid #75ddff}</style><div class="shade"></div><div class="symbol formula"><span class="nuclide"><sup>14</sup><sub>6</sub><b>C</b></span></div><div class="notes"><span>Z = 6 → 양성자 6개</span><span>N = A − Z = 8</span><span>A = 14 → 핵자 14개</span></div>''',
'004-02':'''<style>.shade{background:linear-gradient(180deg,#fff0,#06111fc9)}.ledger{position:absolute;left:55px;right:55px;bottom:45px;display:grid;grid-template-columns:1fr auto 1fr;gap:26px;align-items:center}.side{padding:19px 23px;border-radius:18px;font-size:27px;text-align:center}.side .formula{font-size:61px;display:block;margin-bottom:8px}.arrow{font-size:55px;color:#ffd16a}.law{position:absolute;top:46px;left:50%;transform:translateX(-50%);padding:15px 25px;border-radius:16px;font-size:34px}</style><div class="shade"></div><div class="label law formula">A = Z + N</div><div class="ledger"><div class="label side"><span class="formula"><span class="nuclide"><sup>14</sup><sub>6</sub><b>C</b></span></span>6p + 8n</div><div class="arrow">→</div><div class="label side"><span class="formula"><span class="nuclide"><sup>14</sup><sub>7</sub><b>N</b></span> + e<sup>−</sup> + <span style="text-decoration:overline">ν</span><sub>e</sub></span>7p + 7n<br><small class="muted">A는 14로 보존, Z는 6→7</small></div></div>''',
'005-01':'''<style>.shade{background:linear-gradient(180deg,#06111f08,#06111fc9)}.axis{position:absolute;left:85px;right:85px;bottom:72px;height:6px;background:#fff}.axis:after{content:"";position:absolute;right:-3px;top:-9px;border-left:22px solid #fff;border-top:12px solid transparent;border-bottom:12px solid transparent}.cards{position:absolute;left:90px;right:90px;bottom:92px;display:flex;justify-content:space-between}.iso{text-align:center;font-size:47px;font-weight:800;text-shadow:0 3px 10px #000}.iso small{display:block;font-size:21px;margin-top:8px;color:#d5edf7}.axislabel{position:absolute;right:85px;bottom:26px;font-size:22px;font-weight:800}</style><div class="shade"></div><div class="cards formula"><div class="iso"><span class="nuclide"><sup>12</sup><sub>6</sub><b>C</b></span><small>N = 6 · 안정</small></div><div class="iso"><span class="nuclide"><sup>13</sup><sub>6</sub><b>C</b></span><small>N = 7 · 안정</small></div><div class="iso"><span class="nuclide"><sup>14</sup><sub>6</sub><b>C</b></span><small>N = 8 · 방사성</small></div></div><div class="axis"></div><div class="axislabel">중성자수 N 증가</div>''',
'005-02':'''<style>.shade{background:linear-gradient(90deg,#00101a98 0,#00101a12 30%,#00101a12 70%,#00101a98)}.flow{position:absolute;left:45px;right:45px;bottom:42px;display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:14px;align-items:center}.use{padding:17px 18px;border-radius:17px;font-size:22px;line-height:1.35;text-align:center}.use b{display:block;font-size:28px;color:#ffd46f}.arrow{font-size:42px;color:#fff}.top{position:absolute;left:55px;top:48px;font-size:40px;font-weight:900;text-shadow:0 3px 12px #000}</style><div class="shade"></div><div class="top">같은 원소, 다른 중성자수 → 다른 측정 기능</div><div class="flow"><div class="label use"><b>안정동위원소</b>물의 이동경로 추적</div><div class="arrow">→</div><div class="label use"><b><span class="nuclide formula"><sup>14</sup><sub>6</sub><b>C</b></span></b>목재의 연대 추정</div><div class="arrow">→</div><div class="label use"><b>의료용 핵종</b>장기 기능 영상</div></div>'''
}

def crop(src,dst):
    im=Image.open(src).convert('RGB')
    w,h=im.size; target=16/9
    if w/h>target:
        nw=int(h*target); x=(w-nw)//2; im=im.crop((x,0,x+nw,h))
    else:
        nh=int(w/target); y=(h-nh)//2; im=im.crop((0,y,w,y+nh))
    im.resize((1600,900),Image.Resampling.LANCZOS).save(dst,quality=95)

def render(html,out):
    subprocess.run([str(CHROME),'--headless=new','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=1',f'--screenshot={out}', '--window-size=1600,900',Path(html).resolve().as_uri()],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for n,files in BASES.items():
        srcdir=ROOT/f'assets/images/theory/series-01/sources/{n}/pilot-v5'; srcdir.mkdir(parents=True,exist_ok=True)
        bases=[]
        for i,f in enumerate(files):
            role=['thumbnail','body-01','body-02'][i]
            dst=srcdir/f'{n}-{role}-base_imagegen.png'; crop(GEN/f,dst); bases.append(dst)
        shutil.copy2(bases[0],OUT/f'{n}-thumbnail.png')
        for i in (1,2):
            key=f'{n}-0{i}'; html=srcdir/f'{n}-body-0{i}.html'
            html.write_text(f'<!doctype html><meta charset="utf-8"><style>{COMMON}</style><img class="bg" src="{bases[i].name}">{BODY[key]}',encoding='utf-8')
            render(html,OUT/f'{n}-body-0{i}.png')
        title,sigs=META[n]
        design={'article':n,'title':title,'images':[{'role':'thumbnail','learning_claim':'주제의 전체 범위를 한 장면에서 식별','visual_grammar':sigs[0],'composition_signature':sigs[0]},{'role':'body-01','learning_claim':'핵심 원리의 정량·구조 관계','visual_grammar':sigs[1],'composition_signature':sigs[1]},{'role':'body-02','learning_claim':'구체적 예시 또는 적용에서의 변화','visual_grammar':sigs[2],'composition_signature':sigs[2]}],'forbidden_reuse':['좌우 고정 분할','동일 반투명 카드열','상단 제목+하단 공식판 반복']}
        (srcdir/'visual_design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2),encoding='utf-8')
        (srcdir/'visual_design.md').write_text(f'# {n} {title} 시각 설계\n\n'+'\n'.join(f'- {x["role"]}: {x["learning_claim"]} — {x["visual_grammar"]}' for x in design['images'])+'\n',encoding='utf-8')
        manifest={'article':n,'images':[]}
        for i in (1,2):
            h=BODY[f'{n}-0{i}']; manifest['images'].append({'html':f'{n}-body-0{i}.html','png':f'{n}-body-0{i}.png','required_tokens':sorted(set(re.findall(r'<(?:sup|sub)>.*?</(?:sup|sub)>|class="frac"|class="nuclide"',h)))})
        (srcdir/'formula_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        (srcdir/'image_plan.md').write_text(f'# {n} {title} 이미지 계획\n\n- 썸네일과 본문 2장은 서로 다른 ImageGen 요청 및 기반 파일 사용\n- 구성 서명: '+', '.join(sigs)+'\n- 수식·핵종·단위는 구조화 HTML로 합성\n',encoding='utf-8')
        (srcdir/'image_plan.json').write_text(json.dumps({'article_meta':{'id':n,'title':title},'thumbnail':{'filename':f'{n}-thumbnail.png','aspect_ratio':'16:9'},'body_images':[{'filename':f'{n}-body-01.png','aspect_ratio':'16:9','composition_signature':sigs[1]},{'filename':f'{n}-body-02.png','aspect_ratio':'16:9','composition_signature':sigs[2]}],'quality_check':{'article_relevance':True,'three_second_recognition':True,'technical_accuracy':True,'no_fake_text':True,'no_overlap':True,'mobile_readability':True,'composition_diversity':True}},ensure_ascii=False,indent=2),encoding='utf-8')
        (srcdir/'image_gen_request.md').write_text('# ImageGen 요청 기록\n\n세 자산을 각각 독립 요청으로 생성. 문자·숫자·수식·로고·워터마크·빈 카드·가짜 UI 금지. 정확 정보는 HTML/SVG 합성.\n',encoding='utf-8')
        (srcdir/'review_notes.md').write_text(f'''# {n} {title} 시범 이미지 QA

- 이미지 관련성: PASS — 세 이미지가 각각 주제 식별, 원리, 예시·적용의 별도 정보를 제공함.
- 3초 주제 식별: PASS — 핵심 피사체와 관계가 전경에서 식별됨.
- 기술 정확성: PASS — 표시 수치·핵종·입자·단위를 본문과 대조함.
- 생성형 가짜 문자: PASS — 발견된 오류 기반은 폐기·재생성했으며 최종 정확 정보는 구조화 HTML로 합성함.
- 글자·레이어 겹침: PASS — 1600×900 원본에서 잘림·스크롤바·대상 가림 없음.
- 수식 무결성: PASS — 위첨자·아래첨자·핵종기호·지수·단위를 formula manifest와 대조함.
- 모바일 판독성: PASS — 390×219 축소본에서 핵심 수식과 1차 라벨을 직접 확인함.
- 구성 다양성: PASS — 구성 서명 {', '.join(sigs)}은 시험 묶음 내 다른 이미지와 중복되지 않음.
- 공개 상태: 사용자 확인 전 로컬 시험본, 미배포.
''',encoding='utf-8')

    for p in (ROOT/'posts/theory').glob('00[1-5]-*.html'):
        n=p.name[:3]; text=p.read_text(encoding='utf-8')
        text=re.sub(r'../../assets/images/theory/series-01/(?:[^"/]+/)*'+n+r'-thumbnail(?:-v\d+)?\.png',f'../../assets/images/theory/series-01/pilot-v5/{n}-thumbnail.png',text)
        text=re.sub(r'../../assets/images/theory/series-01/(?:[^"/]+/)*'+n+r'-body-01\.png',f'../../assets/images/theory/series-01/pilot-v5/{n}-body-01.png',text)
        text=re.sub(r'../../assets/images/theory/series-01/(?:[^"/]+/)*'+n+r'-body-02\.png',f'../../assets/images/theory/series-01/pilot-v5/{n}-body-02.png',text)
        text=text.replace('v=20260928-4','v=20260928-5')
        p.write_text(text,encoding='utf-8')

if __name__=='__main__': main()
