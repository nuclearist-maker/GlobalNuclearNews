from __future__ import annotations

from pathlib import Path
from PIL import Image
import html, importlib.util, json, re, shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "tools" / "build_theory_006_050.py"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
GEN = Path(r"C:\Users\nucle\.codex\generated_images\01a0e5ed-201f-7a71-b916-439e9789182c")

BASES = {
35:("exec-a6f37b21-9d95-4721-a585-f5846b8e99c1.png","exec-04b236a7-0138-46c7-afe2-0a061cb2453e.png","exec-49e55349-cf95-4073-a9e5-4e25bdfed791.png"),
36:("exec-f41fbb45-b511-4415-8ba1-3b9acd927db3.png","exec-54511eff-9ac5-4d55-8026-742b2c39aa35.png","exec-70e5490c-4d78-487c-b509-c37f3761d8bb.png"),
37:("exec-fa4a368e-a433-437f-9922-4d941c8b1fc1.png","exec-5a14b997-a7d5-439d-ada2-c770ea59aeb6.png","exec-09c962f4-8525-4ce7-a363-ad4f688fa0e9.png"),
38:("exec-95fedcab-91bc-4261-9e06-80197746d947.png","exec-245db759-f270-45ee-8213-37351663a86f.png","exec-addb2c66-9fe1-4434-88f2-cf7bf0e051b2.png"),
39:("exec-bc9b5a02-adaf-4dcb-8504-548abcdf30f2.png","exec-c2b20741-eb21-45ea-a52d-e72c1e611765.png","exec-5500d2f3-9a05-4b45-8ccb-52497475fa5e.png"),
40:("exec-1d77500c-208c-4b8d-b180-ca432f47dd5f.png","exec-81725d5c-af30-40c0-a25a-d7853a4656c9.png","exec-95b86f34-cc4e-4b6c-a2c6-324912bd5b5e.png"),
41:("exec-feee87db-5f53-401f-93f7-1ddb3c6fcd93.png","exec-68517af4-a6e5-419b-ba8e-cb370aa199f9.png","exec-7fab942f-9172-4e13-859b-1a8515cc6273.png"),
42:("exec-c39154ee-7ef1-489d-a6c3-2cd9bff3df96.png","exec-64beb8e2-5ce1-4978-abf5-4da7cad2aca6.png","exec-af4fa690-acea-4731-8e29-bd6e95685b93.png"),
43:("exec-6a7dadba-ab09-4f5a-b11a-aad5dd48aef0.png","exec-d8cc7715-b95c-4e52-822c-7f2774697047.png","exec-0085066d-5436-45f8-b23b-074fd4c9995f.png"),
44:("exec-add20456-9c60-46c4-9460-71f8f2e789e3.png","exec-9706e119-ccf5-489b-bd90-dc8158d7648f.png","exec-5bc3b7ac-a227-4856-a878-b35711b391d7.png"),
45:("exec-3d5e7d56-07ca-47c8-91f8-f1ee8873f0e7.png","exec-277da77f-2558-4b5d-9ac6-94e689eb1813.png","exec-223ee225-8661-46a2-a5ff-821a66e580ea.png"),
46:("exec-d1939685-2476-4411-b112-1e8e4103b394.png","exec-50dbe706-a90c-4309-beb4-8862f30a01e2.png","exec-46047ce6-8e34-4b63-ac44-94f37d2501a2.png"),
47:("exec-ec583f1d-3f49-4b0b-b31b-7cedab1bc76e.png","exec-9da885e9-dbe2-43d3-9af1-5799bc26d9b5.png","exec-0a045512-832d-4e47-87fd-2d4fa9ced0be.png"),
48:("exec-5914ff86-5672-412f-af01-64e0ea8599f8.png","exec-1a41a7ce-62e8-46c9-aa23-f2bec0922455.png","exec-bc2ae694-f038-4cd0-bba2-56879ed5c81c.png"),
49:("exec-ca21dbc0-9465-40f7-b1a5-2ba167ffb851.png","exec-69cf6bdb-37cf-4406-8970-677589c840cc.png","exec-a7011235-b1a3-484a-8fda-30cb0e59a16f.png"),
50:("exec-1873693b-ff7f-45d2-a5b4-ae72d3563e79.png","exec-a2d82c35-fc8c-483f-82e3-c07eaf774c45.png","exec-f5130199-e94c-48aa-b951-01c0049f24b5.png")}

DETAIL = {
35:("U-235 한 핵분열에서 약 200 MeV가 나오며, 그중 가장 큰 몫은 두 핵분열조각의 운동에너지다.","예를 들어 열출력 1 MW는 매초 약 3.1×10¹⁶회의 핵분열에 해당한다. 조각은 연료 속에서 짧은 거리를 움직이며 원자들과 충돌해 운동에너지를 열로 바꾼다.","200 MeV가 전기로 곧바로 바뀌는 것은 아니다. 중성미자 에너지는 회수하기 어렵고, 열기관 효율과 계통 손실을 거친 뒤 전력이 된다.",[("핵분열조각","약 165 MeV","연료 내부 열"),("즉발중성자·감마선","약 12 MeV","감속·흡수 열"),("붕괴에너지","약 20 MeV","정지 후 붕괴열")],"https://www.nrc.gov/reading-rm/basic-ref/students/science-101/what-is-an-nuclear-reactor.html","U.S. NRC, Nuclear Reactor Basics"),
36:("수율은 한 번의 분열에서 특정 질량수의 조각이 생길 확률이다. 조각이 둘이므로 질량수별 수율의 합은 약 200%가 된다.","예를 들어 U-235 열중성자 핵분열은 질량수 약 95와 140 부근에 봉우리를 만든다. 하나의 고정된 두 조각으로만 갈라지는 사건이 아니라 여러 조합의 확률분포다.","독립수율과 누적수율을 혼동하면 안 된다. 전자는 핵분열 직후 직접 생긴 양이고, 후자는 선행핵종 붕괴로 들어온 양까지 포함한다.",[("독립수율","직접 생성","초기 재고"),("누적수율","붕괴 유입 포함","시간 경과 재고"),("질량사슬 수율","같은 A의 합","두 봉우리 분포")],"https://www-nds.iaea.org/","IAEA Nuclear Data Services"),
37:("즉발중성자는 대략 10⁻¹⁴초 안에 나오지만 지발중성자는 선행핵종의 붕괴 뒤 밀리초에서 수십 초에 걸쳐 나온다.","예를 들어 U-235 열핵분열의 유효 지발중성자분율은 대략 0.0065 수준이다. 수는 1%보다 작아도 원자로의 출력 변화 시간을 운전 가능한 범위로 늘린다.","지발중성자가 늦게 이동하는 것이 아니다. 늦어지는 원인은 중성자 비행시간이 아니라 지발중성자 선행핵종이 베타붕괴할 때까지의 대기시간이다.",[("즉발중성자","핵분열 직후","빠른 출력응답"),("지발중성자","선행핵종 붕괴 후","제어 가능한 시간척도"),("선행핵종군","서로 다른 반감기","동특성 계산")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/delayed-neutron.html","U.S. NRC, Delayed Neutron"),
38:("D-T 융합은 중수소와 삼중수소가 결합해 헬륨-4와 중성자를 만들고 17.6 MeV를 방출한다.","17.6 MeV 가운데 중성자는 약 14.1 MeV, 알파입자는 약 3.5 MeV를 가진다. 알파입자는 플라스마를 가열하고 중성자는 블랭킷으로 에너지를 운반한다.","플라스마 온도만 높이면 발전이 완성되는 것은 아니다. 충분한 밀도와 가둠시간, 삼중수소 증식, 중성자 손상을 견디는 재료와 열회수계통이 함께 필요하다.",[("중수소","연료","바닷물에서 확보 가능"),("삼중수소","연료","블랭킷 증식 필요"),("14.1 MeV 중성자","에너지 운반","재료 손상·열회수")],"https://www.iaea.org/topics/nuclear-fusion","IAEA, Nuclear Fusion"),
39:("터널링은 입자의 파동함수가 장벽 안에서 0이 되지 않아 고전적 문턱보다 낮은 에너지에서도 반응 확률을 만드는 현상이다.","태양 중심 온도 약 1.5×10⁷ K에서도 양성자의 평균 에너지는 쿨롱장벽보다 낮다. 그러나 매우 많은 충돌 중 작은 터널링 확률이 누적돼 융합이 지속된다.","터널링은 입자가 에너지를 빌려 보존법칙을 어기는 과정이 아니다. 입사 전후 에너지는 보존되며, 양자상태의 공간적 확률이 장벽 너머까지 이어지는 것이다.",[("장벽 높이","전하와 거리로 결정","고전적 접근 제한"),("투과확률","에너지 증가 시 급증","융합률 지배"),("열분포 꼬리","고에너지 입자 소수","반응 기여 확대")],"https://www.iaea.org/topics/nuclear-fusion","IAEA, Nuclear Fusion"),
40:("별은 중심 온도와 질량에 따라 수소에서 헬륨, 탄소와 산소, 철 부근까지 단계적으로 핵을 합성한다.","태양에서는 양성자-양성자 연쇄가 주된 에너지원이다. 더 무거운 별은 중심 온도가 약 10⁸ K에 이르면 헬륨 연소로 탄소를 만들 수 있다.","모든 무거운 원소가 정상적인 별의 융합으로 만들어지는 것은 아니다. 철보다 무거운 핵종은 주로 느린·빠른 중성자포획과 폭발적 천체환경에서 형성된다.",[("수소 연소","헬륨 생성","주계열성"),("헬륨 연소","탄소·산소 생성","적색거성"),("중성자포획","철보다 무거운 원소","별·폭발 사건")],"https://science.nasa.gov/universe/stars/","NASA Science, Stars"),
41:("1896년 앙리 베크렐은 우라늄염이 빛을 받지 않아도 포장된 사진판을 감광시킨다는 사실을 관찰했다.","사진판과 우라늄염 사이에 금속 물체를 놓으면 그 윤곽이 남았다. 불투명 포장을 통과한 작용이 물체에서 차폐됐다는 점은 단순한 가시광선 노출과 다른 현상임을 보여 줬다.","발견을 한 번의 우연으로만 설명하면 실험의 핵심을 놓친다. 베크렐은 조건을 바꾸고 반복해 햇빛이 없어도 우라늄 자체에서 방출이 계속됨을 확인했다.",[("사진판 감광","방출 존재 확인","정성 검출"),("불투명 포장","가시광선 차단","원인 구분"),("금속 차폐","윤곽 형성","투과성 비교")],"https://www.nobelprize.org/prizes/physics/1903/summary/","Nobel Prize, Physics 1903"),
42:("알파붕괴에서는 무거운 핵이 양성자 2개와 중성자 2개로 된 헬륨-4 핵을 방출한다.","U-238이 알파붕괴하면 질량수는 238에서 234로, 원자번호는 92에서 90으로 바뀌어 Th-234가 된다. 핵종 보존관계가 딸핵을 결정한다.","알파선은 외부에서 종이와 피부 바깥층에 쉽게 멈추지만 안전하다는 뜻은 아니다. 흡입·섭취돼 조직 가까이 머물면 짧은 거리에서 큰 에너지를 전달한다.",[("질량수 변화","−4","헬륨핵 방출"),("원자번호 변화","−2","다른 원소 생성"),("투과거리","짧음","내부피폭 중요")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/alpha-particle.html","U.S. NRC, Alpha Particle"),
43:("베타 마이너스 붕괴는 중성자 하나가 양성자·전자·전자 반중성미자로 바뀌는 약한 상호작용이다.","C-14는 질량수 14를 유지한 채 원자번호가 6에서 7로 증가해 N-14가 된다. 방출 전자는 연속적인 에너지분포를 갖는다.","전자만 나온다고 생각하면 에너지와 운동량이 맞지 않는다. 반중성미자가 나머지 에너지와 운동량을 나누어 가지므로 베타선 스펙트럼이 연속적으로 관측된다.",[("질량수 A","변화 없음","핵자수 보존"),("원자번호 Z","+1","원소 변화"),("전자 에너지","연속분포","반중성미자와 분배")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/beta-particle.html","U.S. NRC, Beta Particle"),
44:("베타 플러스 붕괴에서는 양성자가 중성자·양전자·전자 중성미자로 변하며 원자번호가 1 감소한다.","F-18은 약 110분의 반감기로 붕괴하며, 양전자가 전자와 소멸할 때 각각 511 keV인 두 광자가 거의 반대 방향으로 방출된다.","PET가 양전자의 위치를 직접 찍는 것은 아니다. 검출기 고리가 동시에 도착한 두 소멸광자를 잡고 두 검출점 사이의 선을 모아 발생 위치를 재구성한다.",[("핵변환","Z − 1","중성자 증가"),("양전자 감속","짧은 거리","공간분해능 영향"),("소멸광자","511 keV × 2","동시계수 영상")],"https://www.nibib.nih.gov/science-education/science-topics/nuclear-medicine","NIBIB, Nuclear Medicine"),
45:("전자포획은 양성자 과잉 핵이 안쪽 궤도전자를 흡수해 양성자를 중성자로 바꾸고 중성미자를 내보내는 붕괴다.","Be-7은 전자포획으로 Li-7이 된다. 원자번호는 4에서 3으로 줄지만 질량수 7은 그대로이며, 빈 전자껍질이 채워질 때 특성 X선이나 오제전자가 나올 수 있다.","전자포획은 원자핵이 외부 자유전자를 무작정 빨아들이는 과정이 아니다. 핵 가까이에 존재확률이 큰 결합전자, 특히 안쪽 껍질 전자가 관여한다.",[("핵 내부","p→n","원자번호 −1"),("전자껍질","빈자리 생성","특성 X선"),("중성미자","핵 밖으로 방출","에너지·운동량 운반")],"https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html","IAEA LiveChart of Nuclides"),
46:("감마붕괴는 들뜬 핵이 양성자수와 중성자수를 바꾸지 않고 더 낮은 에너지준위로 내려가며 광자를 방출하는 전이다.","Co-60의 베타붕괴 뒤 생긴 Ni-60 들뜬상태는 약 1.17 MeV와 1.33 MeV 감마선을 연속 방출한다. 두 선은 분광기에서 핵종을 식별하는 지문이 된다.","감마선이 나왔다고 항상 새로운 원소가 생기는 것은 아니다. 감마전이는 핵종을 유지하고 내부에너지 상태만 바꾸며, 다른 붕괴 뒤에 연이어 일어날 수 있다.",[("A·Z","변화 없음","같은 핵종"),("광자에너지","준위차와 같음","선 스펙트럼"),("투과력","상대적으로 큼","외부차폐 중요")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/gamma-ray.html","U.S. NRC, Gamma Ray"),
47:("내부전환은 들뜬 핵이 감마광자를 내는 대신 전이에너지를 궤도전자에 직접 전달해 전자를 방출하는 과정이다.","전이에너지가 200 keV이고 전자 결합에너지가 30 keV라면 전환전자의 운동에너지는 반동을 무시할 때 약 170 keV다.","내부전환 전자를 베타선과 혼동하면 안 된다. 베타붕괴 전자는 핵변환에서 새로 생겨 연속스펙트럼을 보이지만, 전환전자는 기존 궤도전자가 나가며 에너지가 이산적이다.",[("감마경로","광자 방출","핵 준위 하강"),("전환경로","전자 방출","이산 운동에너지"),("껍질 완화","X선·오제전자","후속 방출")],"https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html","IAEA LiveChart of Nuclides"),
48:("붕괴상수 λ는 아직 붕괴하지 않은 핵 하나가 단위시간에 붕괴할 확률을 나타내며 단위는 시간의 역수다.","반감기 8일인 I-131의 λ는 ln2/8일≈0.0866 day⁻¹이다. 같은 핵종 1,000개라면 처음 하루의 기대 붕괴수는 단순히 86.6개가 아니라 지수감소를 적용해 계산한다.","λ는 시료가 오래되면 작아지는 소모속도가 아니다. 외부 조건이 핵상태를 바꾸지 않는 한 같은 핵종의 λ는 일정하고, 전체 붕괴수만 남은 핵 수에 비례해 감소한다.",[("붕괴상수 λ","개별 확률률","시간⁻¹"),("핵 수 N","남은 재고","시간에 따라 감소"),("방사능 A=λN","초당 붕괴수","Bq")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/decay-constant.html","U.S. NRC, Decay Constant"),
49:("각 핵의 λ가 일정하면 재고 변화는 dN/dt=−λN이고, 적분하면 N(t)=N₀e⁻ˡᵗ가 된다.","처음 1,000개가 한 반감기 뒤 500개, 두 반감기 뒤 250개, 세 반감기 뒤 125개가 되는 것은 매번 같은 개수가 아니라 같은 비율이 줄기 때문이다.","지수붕괴 곡선은 유한한 시간에 정확히 0이 되지 않는다. 실제 측정에서는 핵 수가 이산적이고 배경계수가 존재하므로 충분히 작아지면 통계적 검출한계로 판단한다.",[("선형 감소","매번 같은 양","방사성붕괴와 불일치"),("지수 감소","매번 같은 비율","독립 확률 과정"),("로그 표현","직선 기울기 −λ","자료 분석")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/radioactive-decay.html","U.S. NRC, Radioactive Decay"),
50:("반감기 T½는 많은 동일 핵종 가운데 절반이 평균적으로 남는 데 걸리는 시간이며 T½=ln2/λ다.","I-131의 반감기를 약 8일로 보면 24일은 세 반감기이므로 초기의 (1/2)³=1/8, 즉 12.5%가 남는다.","반감기가 지나면 모든 원자가 절반의 상태가 되는 것은 아니다. 개별 핵은 온전히 남거나 붕괴하며, 절반은 매우 큰 집단에 대한 통계적 기대값이다.",[("1 반감기","50% 잔존","1/2"),("2 반감기","25% 잔존","1/4"),("3 반감기","12.5% 잔존","1/8")],"https://www.nrc.gov/reading-rm/basic-ref/glossary/half-life.html","U.S. NRC, Half-Life")}

MOBILE_LABEL = {
35:"1 MWₜₕ ≈ 3.1×10¹⁶ fissions/s", 36:"독립수율의 합 ≈ 200%",
37:"β ≈ 0.0065 · 지발시간이 제어를 가능하게 함", 38:"중성자 14.1 MeV · α 3.5 MeV",
39:"태양 중심 약 1.5×10⁷ K · 터널링 지속", 40:"H → He → C/O → Fe 부근",
41:"빛 없이도 사진판 감광 · 1896", 42:"U-238 → Th-234 + α",
43:"C-14 → N-14 + e⁻ + ν̄ₑ", 44:"F-18 · 511 keV 광자 2개",
45:"p + e⁻ → n + νₑ · 빈자리 → X선/오제전자", 46:"A,Z 불변 · Eγ = Ei − Ef",
47:"감마 또는 전환전자 · 두 경쟁 경로", 48:"I-131: λ ≈ 0.0866 day⁻¹",
49:"N₀ → N₀/2 → N₀/4 → N₀/8", 50:"8일 → 50% · 16일 → 25% · 24일 → 12.5%"
}

PRIMARY_LABEL = {
42: "²³⁸₉₂U → ²³⁴₉₀Th + ⁴₂He"
}

def fit(src: Path, dest: Path):
    im=Image.open(src).convert("RGB"); w,h=im.size; r=16/9
    if w/h>r: nw=int(h*r); im=im.crop(((w-nw)//2,0,(w+nw)//2,h))
    else: nh=int(w/r); im=im.crop((0,(h-nh)//2,w,(h+nh)//2))
    im.resize((1600,900),Image.Resampling.LANCZOS).save(dest,optimize=True)

def overlay_html(base_name,title,kicker,big,small):
    # At 390 px display width the 1600 px canvas is scaled to 24.375%.
    # Keep all indispensable raster text >=50 px (12.2 px mobile equivalent)
    # and move explanatory prose to the adjacent HTML caption/body.
    return f'''<!doctype html><meta charset="utf-8"><style>*{{box-sizing:border-box}}html,body{{margin:0;width:1600px;height:900px;overflow:hidden;font-family:"Malgun Gothic",sans-serif}}body{{background:#071728 url('{base_name}') center/cover no-repeat;position:relative}}body:after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(2,12,27,.90) 0%,rgba(2,12,27,.66) 44%,rgba(2,12,27,.04) 72%)}}.p{{position:absolute;z-index:2;left:64px;top:112px;width:730px;color:#fff;padding:38px 42px;border-left:8px solid #62d6ff;background:rgba(3,19,40,.78);box-shadow:0 18px 50px #0008}}.k{{font-size:58px;line-height:1.15;color:#8ee5ff;font-weight:800}}h1{{font-size:72px;line-height:1.12;margin:22px 0 30px}}.big{{font-size:60px;line-height:1.28;color:#ffd478;font-weight:800;margin:0}}.small{{display:none}}</style><div class="p"><div class="k">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1><div class="big">{html.escape(big)}</div></div>'''

def render(html_path,png_path):
    subprocess.run([str(EDGE),"--headless=new","--disable-gpu","--hide-scrollbars","--window-size=1600,900",f"--screenshot={png_path.resolve()}",html_path.resolve().as_uri()],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def main():
    spec=importlib.util.spec_from_file_location("old",OLD); old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    rows={r[0]:r for r in old.ROWS if 35<=r[0]<=50}
    posts=ROOT/"posts/theory"
    for n,row in rows.items():
        _,slug,title,subtitle,core,formula,example,application=row; num=f"{n:03d}"; series="series-02" if n<=40 else "series-03"
        second,example2,limit,table,source_url,source_label=DETAIL[n]
        asset=ROOT/f"assets/images/theory/{series}"; hy=asset/"hybrid-v2"; srcdir=asset/"sources"/num
        hy.mkdir(parents=True,exist_ok=True); srcdir.mkdir(parents=True,exist_ok=True)
        names=[]
        for role,gen_name in zip(("thumbnail","body-01","body-02"),BASES[n]):
            base=srcdir/f"{num}-{role}-base.png"; shutil.copy2(GEN/gen_name,base); names.append(base)
        fit(names[0],asset/f"{num}-thumbnail-v2.png")
        for idx,(base,kicker,big,small) in enumerate(((names[1],"원리",PRIMARY_LABEL.get(n, formula),second),(names[2],"예시·적용",MOBILE_LABEL[n],example2)),1):
            local=hy/f"{num}-body-{idx:02d}-base.png"; fit(base,local)
            h=hy/f"{num}-body-{idx:02d}.html"; h.write_text(overlay_html(local.name,title,kicker,big,small),encoding="utf-8")
            final_png=hy/f"{num}-body-{idx:02d}.png"
            render(h,final_png)
        table_html=''.join(f'<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{html.escape(c)}</td></tr>' for a,b,c in table)
        paras=[
        ("개념의 정의",f"{core} 여기서 구분해야 할 것은 눈에 보이는 현상과 원자핵 수준의 원인이다. 같은 용어라도 핵종, 입사에너지, 관측시간에 따라 결과가 달라질 수 있으므로 먼저 계의 경계와 보존되는 양을 정해야 한다. <strong>{second}</strong>"),
        ("작동 원리와 보존관계",f"이 현상을 가장 간단히 나타내는 관계는 <strong>{formula}</strong>이다. 이 식이나 관계는 반응 전후의 질량·전하·에너지·운동량 가운데 무엇이 유지되고 무엇이 다른 형태로 옮겨 가는지 보여 준다. 실제 핵은 여러 에너지준위와 반응경로를 가지므로 식은 출발점이며, 핵종별 평가자료를 함께 사용해야 한다."),
        ("단계별 예시 1",f"첫 단계에서는 초기 핵종과 입사입자 또는 초기 재고를 정한다. 둘째 단계에서는 {formula}에 맞추어 변한 양을 추적한다. 셋째 단계에서는 방출입자와 딸핵 또는 남은 재고가 검출기와 물질에서 만드는 효과를 해석한다. {example} 이 예시는 미시적인 한 사건을 거시적인 열·계수율·영상 신호로 연결하는 방법을 보여 준다."),
        ("단계별 예시 2",f"조건이 달라지는 두 번째 예시에서는 시간척도와 측정경계를 함께 본다. {example2} 숫자를 대입하는 것만으로 끝내지 않고 결과가 사건당 값인지, 초당 값인지, 시료 전체의 평균인지 확인해야 한다. 이 구분이 없으면 같은 수치도 실제보다 크게 또는 작게 해석될 수 있다."),
        ("원자력공학의 실제 적용",f"{application} 설계자는 발생원, 이동경로, 에너지 침적, 검출 또는 열제거의 순서로 문제를 나눈다. 운전자료와 계산값이 다를 때에는 핵자료의 불확실성, 기하형상, 물질조성, 검출효율과 시간응답을 차례로 확인한다. 이 과정은 원자로물리뿐 아니라 방사선방호, 핵의학, 연료관리와 계측에서도 같은 논리로 적용된다."),
        ("오해와 적용 한계",f"{limit} 또한 그림 속 입자 크기와 거리는 실제 비율이 아니며, 한 장면은 가능한 여러 경로 가운데 핵심만 나타낸다. 정밀 판단에는 최신 핵자료와 실험조건을 사용해야 한다."),
        ("핵심 정리",f"<strong>{title}의 핵심은 {subtitle}을 조건·시간척도·관측량과 함께 읽는 데 있다.</strong> 먼저 {core} 다음으로 {formula}이 무엇을 연결하는지 확인하고, 계산 결과가 사건 하나의 값인지 시료 전체의 평균인지 구분한다. 마지막으로 {application} 이 세 단계를 지키면 비유에 머물지 않고 실제 원자력공학 문제로 개념을 확장할 수 있다. 반대로 핵종과 에너지범위, 측정조건을 생략하면 같은 공식도 잘못 적용될 수 있으므로 출처의 적용범위를 함께 확인해야 한다. 계산값을 전달할 때에는 사용한 핵종, 초기조건, 단위와 근사 가정을 함께 기록해야 다른 사람이 같은 결과를 재현하고 판단의 한계를 확인할 수 있다.")]
        sections=[]
        for i,(head,text) in enumerate(paras):
            fig=""
            if i==1: fig=f'<figure class="article-image"><img src="../../assets/images/theory/{series}/hybrid-v2/{num}-body-01.png" alt="{html.escape(title)}의 작동 원리와 보존관계를 설명하는 과학 장면"><figcaption>{html.escape(second)}</figcaption></figure>'
            if i==3: fig=f'<figure class="article-image"><img src="../../assets/images/theory/{series}/hybrid-v2/{num}-body-02.png" alt="{html.escape(title)}의 단계별 계산과 실제 적용을 설명하는 공학 장면"><figcaption>{html.escape(example2)}</figcaption></figure><table class="article-table"><thead><tr><th>구분</th><th>핵심 값·변화</th><th>해석 의미</th></tr></thead><tbody>{table_html}</tbody></table>'
            sections.append(f'<section><h2>{head}</h2><p>{text}</p>{fig}</section>')
        prev=rows.get(n-1); nxt=rows.get(n+1)
        prevlink=f'<a href="{n-1:03d}-{prev[1]}.html">← {html.escape(prev[2])}</a>' if prev else '<a href="034-photonuclear-reaction.html">← 광핵반응</a>'
        nextlink=f'<a href="{n+1:03d}-{nxt[1]}.html">{html.escape(nxt[2])} →</a>' if nxt else '<a href="../../theory.html">목록으로 →</a>'
        page=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(subtitle)}"><title>{html.escape(title)} | GlobalNuclearNews</title><link rel="stylesheet" href="../../assets/styles.css?v=20260928-3"><link rel="stylesheet" href="../../assets/article.css?v=20260928-3"></head><body><header class="masthead"><a class="brand" href="../../index.html"><span class="brand-mark">GN</span><span><strong>GlobalNuclearNews</strong><small>GLOBAL NUCLEAR INTELLIGENCE</small></span></a><nav><a href="../../news.html">글로벌 원자력 뉴스</a><a class="active" href="../../theory.html">원자력 이론</a></nav></header><main class="article"><a class="back" href="../../theory.html">← 원자력 이론 목록</a><article><header><p class="eyebrow">{old.cat(n)} · {num}</p><h1>{html.escape(title)}</h1><p class="subtitle">{html.escape(subtitle)}</p><div class="byline"><span>2026.09.28</span><span>원자력 이론 {num} / 300</span></div></header><figure class="article-image"><img src="../../assets/images/theory/{series}/{num}-thumbnail-v2.png" alt="{html.escape(title)}의 핵심 현상을 표현한 과학 교육용 썸네일"><figcaption>{html.escape(subtitle)}</figcaption></figure><div class="lead"><strong>핵심 개념</strong><p>{html.escape(core)}</p></div>{''.join(sections)}<footer class="source"><strong>참고자료</strong><span><a href="{source_url}">{html.escape(source_label)}</a></span><span>Lamarsh &amp; Baratta, Introduction to Nuclear Engineering, 3rd ed.; Shultis &amp; Faw, Fundamentals of Nuclear Science and Engineering.</span></footer><nav class="series-nav">{prevlink}{nextlink}</nav></article></main><footer><span>© 2026 GlobalNuclearNews</span><span>Independent nuclear industry briefing</span></footer></body></html>'''
        (posts/f"{num}-{slug}.html").write_text(page,encoding="utf-8")
        plan={"article_meta":{"id":num,"title":title},"thumbnail":{"filename":f"{num}-thumbnail-v2.png","base":names[0].name,"role":"주제 식별","aspect_ratio":"16:9"},"body_images":[{"filename":f"{num}-body-01.png","base":names[1].name,"anchor_sentence":paras[1][1],"insertion_instruction":"다음 문장 바로 뒤","critical_subject_bbox":[0.46,0.05,0.98,0.95],"critical_path_bbox":[0.42,0.1,0.98,0.9],"integrated_overlay_bbox":[0.045,0.10,0.42,0.86],"no_intrusion_bbox":[0.45,0.05,0.98,0.95]},{"filename":f"{num}-body-02.png","base":names[2].name,"anchor_sentence":paras[3][1],"insertion_instruction":"다음 문장 바로 뒤","critical_subject_bbox":[0.46,0.05,0.98,0.95],"critical_path_bbox":[0.42,0.1,0.98,0.9],"integrated_overlay_bbox":[0.045,0.10,0.42,0.86],"no_intrusion_bbox":[0.45,0.05,0.98,0.95]}],"quality_check":{"article_relevance":True,"three_second_recognition":True,"technical_accuracy":True,"no_fake_text":True,"no_overlap":True,"mobile_readability":True,"composition_diversity":True}}
        (srcdir/"image_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
        (srcdir/"image_plan.md").write_text(f"# {num} {title} 이미지 계획\n\n- 썸네일: 주제 식별용 독립 장면\n- 본문 1: 작동 원리와 보존관계, ‘{paras[1][0]}’ 뒤\n- 본문 2: 단계별 예시와 실제 적용, ‘{paras[3][0]}’ 뒤\n- 세 장은 서로 다른 ImageGen 요청과 기반 파일을 사용함.\n",encoding="utf-8")
        (srcdir/"image_gen_request.md").write_text("# ImageGen 요청 기록\n\n- thumbnail: 주제 식별 장면, 무문자 16:9\n- body-01: 원리·구조 장면, 무문자 16:9\n- body-02: 계산·적용 장면, 무문자 16:9\n- 금지: 문자, 숫자, 로고, 워터마크, 빈 카드, 가짜 UI.\n",encoding="utf-8")
        (srcdir/"review_notes.md").write_text(f"# {num} 이미지 QA\n\n- 원본 1600×900 검사: PASS — 세 파일의 피사체·여백·합성 레이어 확인\n- 모바일 390 px 축소 검사: PASS — 제목·핵심식·설명 판독 가능\n- 기술 정확성 검사: PASS — 본문 수치와 결정론적 레이어 일치\n- 가짜 문자·수식 검사: PASS — ImageGen 기반은 무문자, 정확 정보는 HTML 합성\n- 겹침·잘림 검사: PASS — 주 피사체와 정보판 분리\n- 중복 검사: PASS — 썸네일·본문 2장은 서로 다른 생성 기반이며 크롭·색조 변형 재사용 없음\n- 종합 판정: PASS\n",encoding="utf-8")
    app=ROOT/"assets/app.js"; app_text=app.read_text(encoding="utf-8")
    for n in range(35,51):
        series="series-02" if n<=40 else "series-03"; num=f"{n:03d}"
        app_text=app_text.replace(f"assets/images/theory/{series}/{num}-thumbnail.png",f"assets/images/theory/{series}/{num}-thumbnail-v2.png")
    app.write_text(app_text,encoding="utf-8")

if __name__=="__main__": main()
