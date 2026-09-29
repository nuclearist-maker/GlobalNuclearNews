from pathlib import Path
from bs4 import BeautifulSoup
import runpy

ROOT = Path(__file__).resolve().parents[1]
GENERIC = ("기본 원리", "관계식과 계산 예시")
TEXT = runpy.run_path(str(ROOT / "tools/rewrite_theory_006_010.py"))["TEXT"]
CASES = {
6: ("질량차를 에너지로 바꾸는 검산", "반응 전후 질량차가 0.001 u라고 가정하면 방출 가능한 에너지는 0.001×931.494≈0.931 MeV입니다. 계산에서는 먼저 모든 질량이 중성 원자질량인지 핵질량인지 통일합니다. 그다음 반응 전후의 전자 수가 상쇄되는지 확인하고, 질량차의 부호가 발열반응과 일치하는지 검산합니다. 0.001 u처럼 작은 차이도 원자 한 개에서는 MeV 규모가 되므로 측정 질량의 자릿수와 반올림 위치가 결과를 좌우합니다."),
7: ("연료봉 재고로 확장하는 계산", "연료 시료에 우라늄이 1,000 g 들어 있고 U-235 질량분율이 4.95%라면 U-235 질량은 49.5 g입니다. 이를 235 g/mol로 나누고 아보가드로상수를 곱하면 약 1.27×10²³개의 U-235 원자를 얻습니다. 실제 연료에서는 U-234와 U-238도 각각 계산하며, 제조자료가 질량분율인지 원자분율인지 먼저 확인해야 합니다. 이러한 구분 없이 농축도 숫자만 적용하면 초기 핵종 재고와 반응률이 함께 어긋납니다."),
8: ("온도 변화가 반응률에 미치는 영향", "냉각재 질량은 그대로인데 열팽창으로 부피가 5% 증가하면 원자수밀도는 원래 값의 1/1.05, 즉 약 95.2%로 감소합니다. 미시적 단면적과 중성자속이 같다는 단순 조건에서는 거시적 단면적과 단위길이당 반응 가능성도 같은 비율로 줄어듭니다. 실제 원자로에서는 온도에 따라 중성자 에너지분포와 단면적도 변하므로, 이 계산은 밀도 효과만 분리해 이해하는 첫 단계로 사용합니다."),
9: ("반지름식의 적용범위 비교", "탄소-12와 납-208에 같은 r₀=1.2 fm를 적용하면 각각 약 2.75 fm와 7.11 fm를 얻습니다. 질량수는 약 17.3배지만 반지름은 약 2.6배입니다. 이 값은 핵의 평균적인 크기를 비교하는 데 유용하지만 측정된 전하반지름과 정확히 같다고 볼 수는 없습니다. 정밀 해석에서는 핵종별 변형과 표면확산, 사용한 실험 탐침을 함께 기록해야 비교의 의미가 유지됩니다. 또한 계산 결과에는 사용한 r₀ 값과 반지름 정의를 반드시 병기해야 합니다."),
10:("붕괴사슬을 좌표로 검산하는 사례", "코발트-60의 베타마이너스붕괴에서는 Z가 27에서 28로 증가하고 N은 33에서 32로 감소하여 질량수 60이 유지됩니다. 핵종도에서는 오른쪽 아래 또는 왼쪽 위처럼 도표의 축 배치에 따른 대각선 이동으로 표시됩니다. 따라서 화살표 방향을 외우기보다 ΔZ=+1, ΔN=−1을 먼저 계산해야 합니다. 이어서 니켈-60의 감마전이는 Z와 N을 바꾸지 않으므로 같은 칸 안에서 에너지상태만 변한다고 해석합니다. 마지막에는 평가핵자료의 반감기와 분기비를 대조해 실제 경로인지 확인해야 합니다.")}

for number in range(6, 11):
    path = next((ROOT / "posts/theory").glob(f"{number:03d}-*.html"))
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    sections = soup.select("main section")
    removable = []
    figures = []
    for section in sections:
        heading = section.find("h2")
        title = heading.get_text(" ", strip=True) if heading else ""
        if title.endswith(GENERIC) or title in GENERIC:
            figure = section.find("figure")
            if figure:
                figures.append(figure.extract())
            removable.append(section)
    for section in removable:
        section.decompose()
    summary = next((s for s in soup.select("main section") if s.find("h2") and s.find("h2").get_text(" ", strip=True) == "핵심 정리"), None)
    present = {s.find("h2").get_text(" ", strip=True) for s in soup.select("main section") if s.find("h2")}
    for title in ("원자력공학에서의 활용", "해석에서 주의할 점"):
        if title not in present:
            section = soup.new_tag("section")
            heading = soup.new_tag("h2"); heading.string = title
            paragraph = soup.new_tag("p"); paragraph.string = TEXT[number][title]
            section.extend([heading, paragraph])
            summary.insert_before(section) if summary else soup.select_one("main article").append(section)
    case_title, case_text = CASES[number]
    existing_case = next((s for s in soup.select("main section") if s.find("h2") and s.find("h2").get_text(" ", strip=True) == case_title), None)
    if existing_case:
        existing_case.find("p").string = case_text
    else:
        section = soup.new_tag("section")
        heading = soup.new_tag("h2"); heading.string = case_title
        paragraph = soup.new_tag("p"); paragraph.string = case_text
        section.extend([heading, paragraph])
        summary.insert_before(section) if summary else soup.select_one("main article").append(section)
    remaining = soup.select("main section")
    for figure, section in zip(figures, remaining[:2]):
        paragraph = section.find("p")
        paragraph.insert_after(figure)
    path.write_text(str(soup), encoding="utf-8")
    print(path.name)
