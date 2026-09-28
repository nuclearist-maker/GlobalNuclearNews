from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, shutil, html

ROOT=Path(__file__).resolve().parents[1]
GEN=Path(r"C:\Users\nucle\.codex\generated_images\01a0c8e8-9805-7182-9801-c2c20e061247")
FONT=Path(r"C:\Windows\Fonts\malgun.ttf"); BOLD=Path(r"C:\Windows\Fonts\malgunbd.ttf")
DATE="2026.09.28"

# id, slug, title, subtitle, core, formula, example, application
ROWS=[
(6,"atomic-mass-unit","원자질량단위 u","원자 한 개의 질량을 다루는 공통 눈금","원자질량단위 u는 탄소-12 원자 질량의 12분의 1이다. 매우 작은 원자 질량을 kg보다 간단하게 비교하기 위한 단위다.","1 u = 1.660 539 066 60 × 10⁻²⁷ kg","우라늄-235 원자 하나의 질량은 약 235 u이므로 약 3.90×10⁻²⁵ kg이다.","핵종 질량표, 반응 Q값, 질량결손과 연료 재고의 원자 수 계산에 쓰인다."),
(7,"avogadro-number","아보가드로수와 원자 개수","거시적 질량을 미시적 입자 수로 바꾸는 연결고리","1몰에는 정확히 6.02214076×10²³개의 구성 입자가 있다. 몰질량을 이용하면 손에 잡히는 시료의 질량을 원자 개수로 바꿀 수 있다.","N = (m / M) Nₐ","U-235 235 g은 약 1몰이므로 약 6.02×10²³개의 원자를 포함한다.","연료 내 핵분열 가능 원자 수와 방사능·반응률의 기초 재고를 산정한다."),
(8,"atomic-number-density","원자수밀도","단위부피 안의 표적 원자 수","원자수밀도는 단위부피에 들어 있는 원자의 수다. 같은 질량이라도 밀도와 몰질량이 다르면 중성자가 만나는 표적 수가 달라진다.","n = ρ Nₐ / M","밀도 19.1 g/cm³인 우라늄 금속은 대략 4.9×10²² atoms/cm³ 수준이다.","거시적 단면적, 평균자유행로와 원자로 반응률 계산의 출발점이다."),
(9,"nuclear-radius","원자핵 반지름","핵자 수에 따라 완만하게 커지는 핵의 크기","원자핵은 핵자가 늘수록 커지지만 부피가 질량수 A에 비례하므로 반지름은 A의 세제곱근에 비례한다.","R ≈ r₀ A^(1/3),  r₀ ≈ 1.2 fm","U-235의 반지름은 약 7.4 fm으로 수소 원자 크기보다 수만 배 작다.","핵반응의 기하학적 크기와 핵밀도가 거의 일정한 이유를 이해하게 한다."),
(10,"nuclide-chart","핵종도 읽는 법","양성자수와 중성자수로 보는 핵종의 지도","핵종도는 보통 가로축에 중성자수 N, 세로축에 양성자수 Z를 둔다. 한 칸의 이동은 핵종 구성과 붕괴 경로의 변화를 뜻한다.","A = Z + N","베타 마이너스 붕괴는 N이 1 줄고 Z가 1 늘어 핵종도에서 대각선으로 이동한다.","연료·핵분열생성물·방사성폐기물의 생성과 붕괴 사슬을 추적한다."),
(11,"stable-and-unstable-nuclei","안정핵과 불안정핵","중성자와 양성자의 균형이 만드는 안정성","가벼운 안정핵은 중성자수와 양성자수가 비슷하지만 무거운 핵은 양성자 사이 반발을 보완하려 더 많은 중성자를 필요로 한다.","안정성 ≠ 단순한 N = Z","탄소-12는 안정하지만 탄소-14는 중성자가 많아 베타 붕괴한다.","방사성동위원소 선택, 붕괴열과 장기 독성 평가의 기본이다."),
(12,"nuclear-force","핵력의 성질","짧은 거리에서 핵자를 묶는 강한 상호작용","핵력은 약 1~2 fm 범위에서 매우 강하고, 전하와 거의 무관하며 가까운 이웃에 주로 작용하는 포화 성질을 보인다.","작용범위 ≈ 1~2 fm","멀리 떨어진 두 양성자는 핵력으로 묶이지 않지만 핵 내부에서는 강하게 결합한다.","결합에너지, 핵밀도, 핵반응 모형을 해석하는 물리적 토대다."),
(13,"coulomb-and-nuclear-force","쿨롱힘과 핵력의 경쟁","반발과 결합이 결정하는 무거운 핵의 운명","양성자 사이 쿨롱힘은 멀리까지 반발하고 핵력은 짧은 거리에서 결합한다. 핵이 커질수록 장거리 반발의 누적이 중요해진다.","V꜀ ∝ Z₁Z₂ / r","무거운 핵은 변형될 때 두 부분의 전기적 반발이 핵분열을 돕는다.","핵분열 가능성, 융합 장벽과 핵종 안정성의 공통 원리를 제공한다."),
(14,"liquid-drop-model","액적모형","원자핵을 집단적으로 움직이는 액체방울로 보는 모형","액적모형은 핵자의 개별 궤도보다 표면에너지·쿨롱에너지·비대칭에너지 같은 집단 효과를 강조한다.","B = 체적항 − 표면항 − 쿨롱항 − 비대칭항 ± 쌍항","액체방울이 길어져 둘로 갈라지듯 무거운 핵도 변형 뒤 핵분열할 수 있다.","반경험적 질량식, 핵분열 장벽과 평균적인 결합에너지를 설명한다."),
(15,"nuclear-shell-model","껍질모형","핵자들의 양자 궤도와 에너지 준위","껍질모형에서는 양성자와 중성자가 평균 퍼텐셜 속의 불연속 에너지 준위를 채운다. 꽉 찬 껍질은 특별한 안정성을 준다.","에너지 준위는 양자화된다","두 핵자가 한 준위에 짝을 이루면 전체 스핀이 상쇄될 수 있다.","핵스핀, 자기모멘트, 들뜬상태와 마법수의 미시적 설명에 쓰인다."),
(16,"magic-numbers","마법수","닫힌 핵껍질이 만드는 특별한 안정성","양성자수 또는 중성자수가 2, 8, 20, 28, 50, 82, 126이면 핵껍질이 닫혀 상대적으로 안정한 경향을 보인다.","2 · 8 · 20 · 28 · 50 · 82 · 126","납-208은 Z=82, N=126인 이중 마법핵으로 매우 안정하다.","핵종의 안정성, 반응단면적과 새로운 초중원소 탐색을 예측한다."),
(17,"nuclear-spin","스핀과 각운동량","원자핵이 지니는 양자역학적 방향성","핵스핀은 핵자들의 궤도각운동량과 고유스핀이 벡터로 결합한 총각운동량이다. 고전적 자전 구와 완전히 같지는 않다.","I = Σ(lᵢ + sᵢ)","짝수 개의 양성자와 중성자가 모두 짝지어진 짝짝핵의 바닥상태 스핀은 흔히 0이다.","NMR, 핵준위 선택규칙과 검출 신호 해석의 핵심 변수다."),
(18,"nuclear-excited-state","핵의 들뜬상태","에너지를 흡수한 원자핵의 높은 준위","원자핵이 충돌이나 포획으로 에너지를 받으면 바닥상태보다 높은 불연속 준위에 머물 수 있고, 감마선이나 입자를 내며 낮아진다.","Eγ = Eᵢ − E_f","Co-60의 딸핵은 연속적인 감마 전이를 거쳐 바닥상태로 내려간다.","감마분광, 차폐 설계와 붕괴열 에너지 계산에 연결된다."),
(19,"wave-particle-duality","파동-입자 이중성","입자의 경로와 간섭을 함께 설명하는 양자 관점","중성자와 전자는 검출기에서 입자처럼 한 점에 기록되지만 결정에서는 파동처럼 회절한다. 두 모습은 실험 배치에 따라 드러난다.","λ = h / p","열중성자의 파장은 원자 간격과 비슷해 결정구조 분석에 알맞다.","중성자 회절, 산란단면적과 양자 터널링을 이해하는 기초다."),
(20,"uncertainty-principle","불확정성원리","위치와 운동량의 동시 정밀도 한계","불확정성은 측정기 결함이 아니라 양자상태의 구조다. 위치를 좁게 한정할수록 가능한 운동량의 범위가 넓어진다.","Δx Δp ≥ ħ / 2","핵자를 펨토미터 영역에 가두면 운동량과 운동에너지의 불확정성이 커진다.","핵 내부 운동, 영점에너지와 터널링의 정성적 이유를 제공한다."),
(21,"mass-energy-equivalence","질량-에너지 등가성","작은 질량 차이가 큰 에너지로 바뀌는 원리","질량은 에너지의 한 형태다. 핵반응 전후의 아주 작은 질량 차이는 빛의 속도 제곱에 비례하는 큰 에너지 차이가 된다.","E = mc²","1 g의 질량에 해당하는 에너지는 약 9×10¹³ J이지만 실제 반응은 그 일부만 전환한다.","핵분열·핵융합 에너지와 반응 Q값 계산의 출발점이다."),
(22,"mass-defect","질량결손","묶인 핵의 질량이 구성 핵자 합보다 작은 이유","원자핵을 이루는 양성자와 중성자의 자유 질량을 더한 값은 실제 핵 질량보다 크다. 차이는 결합할 때 방출된 에너지에 대응한다.","Δm = Zmₚ + Nmₙ − m핵","헬륨-4 핵은 자유 핵자 네 개의 합보다 가벼우며 차이가 큰 결합에너지다.","핵질량표에서 결합에너지와 반응 가능 에너지를 산출한다."),
(23,"binding-energy","결합에너지","원자핵을 완전히 분해하는 데 필요한 에너지","결합에너지는 핵을 자유 핵자들로 떼어내는 데 필요한 최소 에너지이며, 같은 크기의 에너지가 핵 형성 때 방출된다.","B = Δm c²","헬륨-4의 총 결합에너지는 약 28.3 MeV다.","핵 안정성과 분열·융합에서 에너지가 나오는 방향을 판단한다."),
(24,"binding-energy-per-nucleon","핵자당 결합에너지","핵종별 평균 결합 강도를 비교하는 곡선","총 결합에너지를 핵자수로 나누면 서로 다른 크기의 핵을 비교할 수 있다. 철·니켈 부근에서 최대가 된다.","B̄ = B / A","가벼운 핵의 융합과 무거운 핵의 분열은 모두 곡선의 높은 쪽으로 이동한다.","핵분열과 핵융합의 에너지 발생을 하나의 그래프로 설명한다."),
(25,"separation-energy","분리에너지","마지막 핵자 하나를 떼어내는 문턱","중성자 또는 양성자 분리에너지는 특정 핵자 하나를 핵에서 제거하는 데 필요한 에너지다. 평균 결합에너지와 달리 마지막 핵자의 상태에 민감하다.","Sₙ = [M(A−1,Z)+mₙ−M(A,Z)]c²","들뜬에너지가 중성자 분리에너지보다 높으면 중성자 방출 통로가 열릴 수 있다.","중성자 포획 후 감마 방출과 입자 방출의 경쟁을 예측한다."),
(26,"reaction-q-value","핵반응의 Q값","반응 전후 질량 차이로 계산하는 순에너지","Q값은 반응물의 총 정지질량과 생성물의 총 정지질량 차이다. 양수면 에너지가 방출되고 음수면 외부 에너지가 필요하다.","Q = (m반응물 − m생성물)c²","D-T 융합의 Q값은 약 17.6 MeV이며 생성물 운동에너지로 분배된다.","반응 가능성, 발열량과 생성입자 에너지 계산에 사용한다."),
(27,"threshold-energy","문턱에너지","흡열반응이 시작되기 위한 최소 입사에너지","Q가 음수인 반응은 에너지를 공급해야 하며 운동량 보존 때문에 |Q|보다 조금 큰 입사에너지가 필요한 경우가 많다.","Eₜₕ ≈ −Q(1 + m입사/m표적)","무거운 표적에서는 반동 몫이 작아 문턱에너지가 |Q|에 가까워진다.","가속기 조사조건과 반응 채널 개방 에너지를 정한다."),
(28,"momentum-and-recoil","운동량 보존과 반동","보이지 않는 반동까지 포함한 반응의 균형","고립된 핵반응에서 총운동량은 항상 보존된다. 광자나 입자가 한 방향으로 나가면 남은 핵은 반대 방향으로 반동한다.","Σp전 = Σp후","감마선을 방출한 핵도 아주 작은 반동에너지를 가진다.","검출 스펙트럼, 도플러 넓어짐과 문턱에너지 계산을 바로잡는다."),
(29,"compound-nucleus","복합핵 모형","입사입자를 흡수한 뒤 기억을 잃는 들뜬 핵","복합핵 반응에서는 표적과 입사입자가 먼저 에너지를 공유하는 들뜬 핵을 만든 뒤, 통계적으로 입자나 감마선을 방출한다.","a + A → C* → b + B","U-235가 열중성자를 흡수하면 U-236* 복합핵이 형성되어 핵분열할 수 있다.","중성자 반응단면적과 공명·핵분열 확률의 해석에 쓰인다."),
(30,"elastic-scattering","탄성산란","내부상태를 바꾸지 않는 충돌과 에너지 전달","탄성산란에서는 충돌 전후 입자의 종류와 핵의 내부상태가 같고, 운동에너지와 운동량이 보존된다.","K전 = K후","중성자는 질량이 비슷한 수소핵과 충돌할 때 큰 에너지를 잃는다.","경수 감속재가 빠른 중성자를 열중성자로 낮추는 원리다."),
(31,"inelastic-scattering","비탄성산란","운동에너지 일부가 핵의 들뜸으로 전환되는 충돌","비탄성산란에서는 입사입자가 에너지 일부를 핵의 들뜬상태에 넘긴다. 핵은 뒤이어 감마선을 방출할 수 있다.","n + A → n′ + A*","빠른 중성자가 철 원자핵을 들뜨게 하면 산란 중성자의 에너지가 낮아진다.","차폐체의 에너지 감속과 2차 감마 발생을 함께 평가하게 한다."),
(32,"neutron-capture","중성자 포획","전하 장벽 없이 핵에 들어가는 중성자","중성자는 전하가 없어 낮은 에너지에서도 핵에 접근할 수 있다. 포획 뒤 복합핵은 보통 감마선을 내며 안정화한다.","A(Z)+n → A+1(Z)* → A+1(Z)+γ","Co-59의 중성자 포획은 방사성 Co-60을 만들 수 있다.","원자로 제어, 방사화 분석과 재료 방사화 평가에 중요하다."),
(33,"charged-particle-reaction","하전입자 핵반응","쿨롱장벽을 넘어야 시작되는 반응","양성자나 알파입자는 표적핵과 같은 양전하이므로 전기적 반발을 이겨야 핵력이 작용하는 거리까지 접근한다.","V꜀ ≈ Z₁Z₂e² / 4πε₀R","입사에너지가 높거나 터널링 확률이 커져야 반응률이 의미 있게 증가한다.","가속기 동위원소 생산과 핵융합 반응률 설계에 적용된다."),
(34,"photonuclear-reaction","광핵반응","고에너지 광자가 원자핵을 바꾸는 과정","감마광자가 핵에 충분한 에너지를 전달하면 중성자나 양성자가 방출될 수 있다. 전자와의 일반 광전효과와 구분해야 한다.","γ + A → (A−1) + n","광자에너지가 중성자 분리에너지를 넘으면 (γ,n) 반응이 가능해진다.","가속기 차폐, 방사화와 동위원소 생산 평가에 필요하다."),
(35,"fission-energy","핵분열 에너지","무거운 핵의 결합에너지 차이가 만드는 열원","U-235 같은 무거운 핵이 둘로 갈라지면 더 강하게 결합된 중간질량 핵들이 생기며 약 200 MeV가 방출된다.","약 200 MeV / fission","에너지 대부분은 두 핵분열조각의 운동에너지이며 물질에서 열로 바뀐다.","원자로 출력, 연료 소모와 붕괴열 산정의 에너지 원천이다."),
(36,"fission-product-yield","핵분열생성물 수율","한 번의 핵분열이 만드는 두 봉우리 분포","열중성자 핵분열은 흔히 질량수가 서로 다른 두 조각을 만들어 수율곡선이 두 봉우리 형태를 보인다.","Σ 독립수율 ≈ 200%","한 핵분열에서 큰 조각과 작은 조각이 함께 생기므로 전체 조각 수율 합은 약 200%다.","붕괴열, 방사선원, 독물질과 폐기물 핵종재고를 결정한다."),
(37,"prompt-and-delayed-neutrons","즉발중성자와 지발중성자","핵분열 직후와 뒤늦게 나오는 두 중성자 집단","즉발중성자는 핵분열 직후 방출되고 지발중성자는 일부 핵분열생성물의 베타붕괴 뒤 방출된다. 지발분율은 작지만 시간척도를 바꾼다.","β = 지발중성자 / 전체 핵분열중성자","지발중성자가 없으면 출력 변화가 밀리초 수준으로 빨라져 제어가 매우 어렵다.","원자로 동특성, 임계도 제어와 안전계통 응답의 핵심이다."),
(38,"nuclear-fusion","핵융합","가벼운 핵이 합쳐져 에너지를 내는 반응","가벼운 핵 둘이 결합해 핵자당 결합에너지가 더 큰 핵을 만들면 질량 차이가 에너지로 방출된다.","D + T → He-4 + n + 17.6 MeV","D-T 반응 에너지 중 약 14.1 MeV는 중성자가, 3.5 MeV는 알파입자가 가진다.","플라즈마 가열, 중성자 벽부하와 삼중수소 증식 설계를 좌우한다."),
(39,"coulomb-barrier-tunneling","쿨롱장벽과 터널링","고전적 문턱 아래에서도 가능한 양자 투과","양전하 핵들은 쿨롱장벽에 막히지만 파동함수는 장벽 안에서 즉시 0이 되지 않아 작은 투과 확률이 존재한다.","P ∝ exp(−2G)","태양 중심 온도는 고전적으로 충분하지 않지만 터널링 덕분에 융합이 지속된다.","별의 융합률과 실험 핵융합의 온도 의존성을 설명한다."),
(40,"stellar-nucleosynthesis","별의 핵합성","별 내부에서 만들어지는 원소의 계보","별은 수소에서 헬륨, 더 무거운 별은 탄소·산소를 거쳐 철 부근까지 융합한다. 철보다 무거운 원소는 주로 중성자 포획 과정에서 형성된다.","가벼운 핵 → 철 부근까지 융합","태양은 양성자-양성자 연쇄반응으로 빛을 내고 초신성 환경은 무거운 핵종 생성을 돕는다.","핵종 존재비와 원자로 재료에 포함된 원소의 기원을 연결한다."),
(41,"discovery-of-radioactivity","방사능의 발견","빛 없이도 사진판을 감광시킨 우라늄의 신호","1896년 베크렐은 우라늄 화합물이 햇빛과 무관하게 포장된 사진판을 감광시키는 현상을 관찰했다.","자발적 핵변환의 발견","외부 에너지원이 없어도 신호가 나타난다는 사실이 원자 내부 변화의 단서였다.","방사선 계측과 핵물리학이 시작된 실험적 전환점이다."),
(42,"alpha-decay","알파붕괴","무거운 핵이 헬륨핵을 방출하는 변화","알파입자는 양성자 2개와 중성자 2개로 이루어진 He-4 핵이다. 방출 뒤 원자번호는 2, 질량수는 4 감소한다.","A(Z) → A−4(Z−2) + α","U-238은 알파붕괴해 Th-234가 된다.","외부 투과력은 낮지만 체내 유입 때 큰 선량을 줄 수 있어 내부피폭 평가가 중요하다."),
(43,"beta-minus-decay","베타 마이너스 붕괴","중성자가 양성자로 바뀌는 핵변환","중성자가 많은 핵에서 중성자 하나가 양성자·전자·반중성미자로 변한다. 질량수는 같고 원자번호는 1 증가한다.","n → p + e⁻ + ν̄ₑ","C-14는 베타 마이너스 붕괴해 N-14가 된다.","핵분열생성물 붕괴열, 베타선 차폐와 방사성 추적에 연결된다."),
(44,"beta-plus-decay","베타 플러스 붕괴","양성자가 중성자로 바뀌며 양전자를 내는 변화","양성자가 많은 핵에서 양성자 하나가 중성자·양전자·중성미자로 변한다. 양전자는 전자와 소멸해 감마광자 두 개를 만든다.","p → n + e⁺ + νₑ","F-18의 양전자 소멸광자는 PET 영상에서 서로 반대 방향으로 검출된다.","양전자방출단층촬영과 양성자 과잉 핵종의 붕괴를 설명한다."),
(45,"electron-capture","전자포획","원자핵이 안쪽 전자를 흡수하는 붕괴","양성자 과잉 핵이 원자 껍질의 전자를 포획하면 양성자가 중성자로 바뀌고 중성미자가 방출된다.","p + e⁻ → n + νₑ","전자 빈자리를 바깥 전자가 채우며 특성 X선이나 오제전자가 생길 수 있다.","저에너지 광자·전자 선원과 핵의학 핵종 특성을 평가한다."),
(46,"gamma-decay","감마붕괴","핵종은 그대로이고 에너지 준위만 낮아지는 전이","들뜬 핵은 양성자수와 중성자수를 바꾸지 않은 채 감마광자를 방출해 더 낮은 에너지 상태로 이동한다.","A(Z)* → A(Z) + γ","Co-60 붕괴 뒤의 Ni-60*는 두 감마선을 연속 방출한다.","감마분광, 차폐 두께와 외부피폭 선량평가에 직접 쓰인다."),
(47,"internal-conversion","내부전환","감마선 대신 궤도전자에 에너지를 넘기는 전이","들뜬 핵이 전이에너지를 원자 궤도전자에 직접 전달하면 전자가 방출된다. 이는 베타붕괴와 다른 과정이다.","Kₑ = E전이 − E결합","내부전환 뒤 전자껍질 빈자리가 채워지며 특성 X선이 뒤따를 수 있다.","전자선원 스펙트럼과 감마선 세기의 보정을 이해하게 한다."),
(48,"decay-constant","붕괴상수","한 핵이 단위시간에 붕괴할 확률","붕괴상수 λ는 아직 붕괴하지 않은 개별 핵이 단위시간에 붕괴할 확률을 나타낸다. 특정 핵의 정확한 붕괴 시각은 예측할 수 없다.","λ = ln2 / T½","반감기가 짧을수록 λ가 크고 같은 수의 핵에서 초당 더 많은 붕괴가 일어난다.","방사능, 반감기, 핵종재고 감소식을 하나로 연결한다."),
(49,"exponential-decay-law","지수붕괴법칙","항상 같은 비율로 줄어드는 핵종재고","각 핵의 붕괴확률이 시간에 따라 일정하면 남은 핵 수의 감소율은 현재 핵 수에 비례하고 지수함수가 된다.","N(t) = N₀e^(−λt)","처음 1,000개에서 한 반감기 뒤 500개, 두 반감기 뒤 250개가 평균적으로 남는다.","방사능 예측, 냉각기간과 방사성폐기물 재고평가의 기본식이다."),
(50,"half-life","반감기","방사성 핵종의 절반이 남는 고유 시간","반감기는 초기 핵 수와 무관하게 같은 핵종의 재고가 절반으로 줄어드는 시간이다. 붕괴가 완전히 끝나는 시간은 아니다.","T½ = ln2 / λ","I-131의 반감기는 약 8일이므로 24일 뒤에는 처음의 약 1/8이 남는다.","핵의학 투여계획, 저장·운반·해체 시점과 냉각기간을 정하는 척도다.")]

BASE={
6:"exec-c3a79b91-06e3-46f4-b1b0-d065fa33be59.png",7:"exec-b1fc4fa8-34c3-4725-8d98-443d04332cb2.png",8:"exec-d38f2a03-7ba2-4bdf-841d-cbaa8f08f4ef.png",9:"exec-f899795d-e525-4e50-b0c6-66cde44d65b7.png",10:"exec-a59906e2-90b3-4c7b-a486-5fd691673d11.png",11:"exec-503296f5-089c-48d0-84e1-cfe6515bb06e.png",12:"exec-2069edd0-c737-4824-be15-51ad61f396b6.png",13:"exec-efa8aa91-ec00-49d4-a538-55a710bc4ff4.png",14:"exec-82832c58-860f-4955-934f-f329a0dda3cf.png",15:"exec-19916f31-2f8d-4bfb-a802-c9f964871c75.png",16:"exec-fe8d6081-ff54-4a9e-9a75-53e794051ffc.png",17:"exec-3d336fe1-621a-40a8-9fcd-3f0b8d740d51.png",18:"exec-f5d3f392-bbd1-4612-9793-6c3cf290c8d5.png",19:"exec-922ec68d-0b0c-4f6b-bc41-6aebbef7f723.png",20:"exec-b642e827-65d5-4791-b86e-556298d7ea12.png",21:"exec-6d928c74-7dd7-4126-b96c-3952c532ee3b.png",22:"exec-da97cccc-ba34-4786-a0fe-429c4c46808a.png",23:"exec-2e4c36b7-bfc1-4715-bab6-7cd9390d1419.png",24:"exec-5ff1660c-50f0-4d5d-87d6-f9b035533ce7.png",25:"exec-aff09c8f-d978-4f0f-846e-3e731acf535c.png",26:"exec-963ea36f-3939-40ce-8d86-d5411b20f91a.png",27:"exec-e87f9200-9a96-4798-84ea-5d0cd21436ac.png",28:"exec-1c10e75e-48ea-4c95-8f08-d93453a8bb2b.png",29:"exec-70447a2a-b771-4317-b33c-5eb202ea681c.png",30:"exec-7f6e1e12-e8a9-4f54-b5af-3ea10b0a4df2.png",31:"exec-ac8396b5-63e2-4ed0-9128-1c31ab9400ff.png",32:"exec-0ad1f07f-b0aa-4eb2-90a0-53363fc2fa89.png",33:"exec-147e478e-8149-4f70-a863-91683e8bdb70.png",34:"exec-f26a166d-3919-4960-b37c-0ccf7b721fc9.png",35:"exec-80ef79cf-ace5-4943-8d8c-4335c23e69b8.png",36:"exec-607ad22d-0aa6-4b69-a488-487604f97dca.png",37:"exec-fe80bb6a-42e5-48cb-a03a-9fc8700ad7d4.png",38:"exec-d10db4a2-6731-4c1e-8a04-cbec6dd06379.png",39:"exec-a1d78303-ba5b-470c-b15e-77114e1187c7.png",40:"exec-734d5f10-e321-433e-8c12-84b92049b00b.png",41:"exec-0f38b628-c090-4291-8305-e88dca310fa8.png",42:"exec-c7472473-698f-4afb-8586-888cf49d17fa.png",43:"exec-e34d3b22-cca9-4903-96c5-857db988f455.png",44:"exec-cd609022-65a6-446a-96f3-55c4b141c4c1.png",45:"exec-ffded766-95a7-4533-b721-eda9195259ee.png",46:"exec-6266b9e0-d230-4ecf-80ff-b3bc92b7e829.png",47:"exec-c32a3bd4-1ec0-4ccf-8aec-24637f1abfe2.png",48:"exec-5ee0af9e-ba5e-401d-98dc-0e6c6cedbf10.png",49:"exec-52bbc5e6-190a-4b40-8ac3-b8c9dff762f4.png",50:"exec-c85e0709-31ea-4106-bb2d-001e7de03ee0.png"}

def cat(n): return "핵물리 기초" if n<=20 else ("질량·에너지·핵반응" if n<=40 else "방사성붕괴와 시간")
def series(n): return "series-01" if n<=20 else ("series-02" if n<=40 else "series-03")
def fit(im):
    w,h=im.size; target=1600/900
    if w/h>target: nw=int(h*target); im=im.crop(((w-nw)//2,0,(w+nw)//2,h))
    else: nh=int(w/target); im=im.crop((0,(h-nh)//2,w,(h+nh)//2))
    return im.resize((1600,900),Image.Resampling.LANCZOS)
def font(p,b=False): return ImageFont.truetype(str(BOLD if b else FONT),p)
def wrap(draw,text,f,maxw):
    out=[]; line=""
    for ch in text:
        if draw.textlength(line+ch,font=f)<=maxw: line+=ch
        else: out.append(line); line=ch
    if line: out.append(line)
    return out
def composite(base,title,kicker,body,formula,out):
    im=base.copy().filter(ImageFilter.GaussianBlur(.35)); d=ImageDraw.Draw(im,"RGBA")
    d.rounded_rectangle((70,70,910,830),radius=30,fill=(3,18,38,222),outline=(90,204,255,150),width=2)
    d.text((115,115),kicker,font=font(27,True),fill=(105,215,255,255))
    y=170
    for line in wrap(d,title,font(54,True),700): d.text((115,y),line,font=font(54,True),fill="white"); y+=70
    d.rounded_rectangle((115,y+15,820,y+135),radius=22,fill=(0,128,190,75),outline=(115,220,255,120),width=2)
    d.text((150,y+48),formula,font=font(31,True),fill=(255,205,102,255))
    y+=180
    for line in wrap(d,body,font(28),690): d.text((115,y),line,font=font(28),fill=(225,237,246,255),spacing=12); y+=47
    im.save(out,optimize=True)

def article(row, prev, nxt):
    n,slug,title,subtitle,core,formula,example,application=row; num=f"{n:03d}"; s=series(n)
    prevlink=f'<a href="{prev[0]:03d}-{prev[1]}.html">← {html.escape(prev[2])}</a>' if prev else '<span></span>'
    nextlink=f'<a href="{nxt[0]:03d}-{nxt[1]}.html">{html.escape(nxt[2])} →</a>' if nxt else '<a href="../../theory.html">목록으로 →</a>'
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(subtitle)}"><title>{html.escape(title)} | GlobalNuclearNews</title><link rel="stylesheet" href="../../assets/styles.css?v=20260928-2"><link rel="stylesheet" href="../../assets/article.css?v=20260928-2"></head><body><header class="masthead"><a class="brand" href="../../index.html"><span class="brand-mark">GN</span><span><strong>GlobalNuclearNews</strong><small>GLOBAL NUCLEAR INTELLIGENCE</small></span></a><nav><a href="../../news.html">글로벌 원자력 뉴스</a><a class="active" href="../../theory.html">원자력 이론</a></nav></header><main class="article"><a class="back" href="../../theory.html">← 원자력 이론 목록</a><article><header><p class="eyebrow">{cat(n)} · {num}</p><h1>{html.escape(title)}</h1><p class="subtitle">{html.escape(subtitle)}</p><div class="byline"><span>{DATE}</span><span>원자력 이론 {num} / 300</span></div></header><figure class="article-image"><img src="../../assets/images/theory/{s}/{num}-thumbnail.png" alt="{html.escape(title)} 개념을 표현한 3차원 과학 이미지"><figcaption>{html.escape(subtitle)}</figcaption></figure><div class="lead"><strong>핵심 개념</strong><p>{html.escape(core)}</p></div><section><h2>{html.escape(title)}의 기본 원리</h2><p>{html.escape(core)} 관련 값을 계산할 때에는 단위와 계의 경계를 먼저 정해야 하며, 평균적인 설명과 개별 핵종의 실제 자료를 구분해야 합니다.</p><figure class="article-image"><img src="../../assets/images/theory/{s}/hybrid-v1/{num}-body-01.png" alt="{html.escape(title)}의 정의와 핵심 관계식"><figcaption>개념을 지배하는 정의와 관계식을 실제 물리 장면 위에 함께 정리했다.</figcaption></figure></section><section><h2>관계식과 계산 예시</h2><p><strong>{html.escape(formula)}</strong>가 핵심 관계입니다. {html.escape(example)} 계산에서는 입력값의 단위를 일관되게 맞추고, 근삿값이 적용되는 범위를 확인해야 합니다.</p><figure class="article-image"><img src="../../assets/images/theory/{s}/hybrid-v1/{num}-body-02.png" alt="{html.escape(title)}의 계산 예시와 공학적 활용"><figcaption>간단한 예시를 통해 수식이 실제 원자력공학 판단으로 이어지는 과정을 보여준다.</figcaption></figure></section><section><h2>원자력공학에서의 활용</h2><p>{html.escape(application)} 이 개념 하나만으로 실제 계통을 모두 설명할 수는 없으므로, 평가 목적에 맞는 핵자료와 재료조건, 에너지 범위 및 불확실성을 함께 적용해야 합니다.</p></section><section><h2>해석에서 주의할 점</h2><p>그림은 이해를 위한 개념 표현이며 입자 크기와 거리, 시간척도를 실제 비율로 그린 것이 아닙니다. 관계식은 대표적인 형태이므로 정밀 해석에서는 핵종별 평가핵자료와 보존법칙, 실험조건을 우선합니다.</p></section><footer class="source"><strong>참고자료</strong><span>NIST, CODATA Fundamental Physical Constants; IAEA Nuclear Data Services, LiveChart of Nuclides; NNDC, NuDat 3; DOE Office of Science, Nuclear Physics.</span><span>Lamarsh & Baratta, Introduction to Nuclear Engineering, 3rd ed.; Shultis & Faw, Fundamentals of Nuclear Science and Engineering.</span></footer><nav class="series-nav">{prevlink}{nextlink}</nav></article></main><footer><span>© 2026 GlobalNuclearNews</span><span>Independent nuclear industry briefing</span></footer></body></html>'''

def main():
    raise RuntimeError(
        "이 레거시 일괄 생성기는 한 개의 기반 이미지를 썸네일과 두 본문 이미지에 "
        "재사용하고 정형 문장을 반복하므로 폐기되었습니다. 게시물은 5편 단위로 서로 다른 "
        "ImageGen 기반 장면을 제작한 뒤 tools/qa_theory_posts.py의 독립 QA를 통과해야 합니다."
    )
    postdir=ROOT/"posts/theory"; assets=ROOT/"assets/images/theory"; plans=ROOT/"docs/theory-image-plans"
    plans.mkdir(parents=True,exist_ok=True)
    metadata=[]
    for i,row in enumerate(ROWS):
        n,slug,title,subtitle,core,formula,example,application=row; num=f"{n:03d}"; s=series(n)
        dest=assets/s; hybrid=dest/"hybrid-v1"; srcdir=dest/"sources"/num
        for p in (dest,hybrid,srcdir): p.mkdir(parents=True,exist_ok=True)
        src=GEN/BASE[n]
        if not src.exists(): raise FileNotFoundError(src)
        shutil.copy2(src,srcdir/"imagegen-base.png")
        base=fit(Image.open(src).convert("RGB")); base.save(dest/f"{num}-thumbnail.png",optimize=True)
        composite(base,title,"핵심 정의",core,formula,hybrid/f"{num}-body-01.png")
        composite(base,title,"계산 예시와 적용",example+" "+application,formula,hybrid/f"{num}-body-02.png")
        plan={"post":num,"title":title,"base":BASE[n],"thumbnail":{"role":"목록 식별","text":"없음"},"body_01":{"role":"정의와 관계식","anchor":"기본 원리 뒤"},"body_02":{"role":"계산 예시와 활용","anchor":"관계식과 계산 예시 뒤"},"qa":["1600x900","결정론적 한글 레이어","본문 중복 최소화","원본 장면 보존"]}
        (srcdir/"image_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
        (srcdir/"review_notes.md").write_text(f"# {num} 이미지 QA\n\n- 3D 기반 장면: ImageGen 전용 도구 사용\n- 한글·수식: Pillow 결정론적 레이어\n- 최종 크기: 1600×900\n- 썸네일과 본문 합성 이미지의 가독성 자동 점검 대상\n",encoding="utf-8")
        prev=ROWS[i-1][:3] if i else (5,"isotopes","동위원소의 의미")
        nxt=ROWS[i+1][:3] if i+1<len(ROWS) else None
        (postdir/f"{num}-{slug}.html").write_text(article(row,prev,nxt),encoding="utf-8")
        metadata.append({"title":title,"date":"2026-09-28","displayDate":DATE,"section":"theory","category":cat(n),"summary":subtitle,"thumbnail":f"assets/images/theory/{s}/{num}-thumbnail.png","thumbnailAlt":title+" 개념 이미지","url":f"posts/theory/{num}-{slug}.html","keywords":title.replace("·"," ")+" 원자력 이론"})
    (ROOT/"assets/theory-posts-006-050.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    app=ROOT/"assets/app.js"; text=app.read_text(encoding="utf-8")
    marker="const posts=[\n"
    block="".join("  "+json.dumps(x,ensure_ascii=False,separators=(',',':'))+",\n" for x in reversed(metadata))
    text=text.replace(marker,marker+block,1); app.write_text(text,encoding="utf-8")
    f=postdir/"005-isotopes.html"; t=f.read_text(encoding="utf-8"); t=t.replace('<a href="../../theory.html">목록으로 →</a>','<a href="006-atomic-mass-unit.html">원자질량단위 u →</a>'); f.write_text(t,encoding="utf-8")
    print(f"built {len(ROWS)} posts, {len(ROWS)*3} final images")

if __name__=="__main__": main()
