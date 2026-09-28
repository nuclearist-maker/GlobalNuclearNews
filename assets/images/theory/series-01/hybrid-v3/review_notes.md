# 시각 자체검수 — 001·002 hybrid-v3

## 검사 조건

- 원본: 1600×900 PNG 개별 확인
- 모바일: 390 px 폭 축소 확인
- 중복: 파일 SHA-256 및 장면·시점·기능 비교

| 파일 | 본문·앵커 일치 | 3초 식별 | 기술·수치 | 가짜 문자 | 겹침·잘림 | 모바일 | 독립 기반 | 결과 |
|---|---|---|---|---|---|---|---|---|
| 001-thumbnail.png | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 001-body-01.png | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 001-body-02.png | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 002-thumbnail.png | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 002-body-01.png | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| 002-body-02.png | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

기술 검토: 001의 에너지 전달 순서와 다중장벽·안전기능을 본문과 대조했다. 002의 100 m 대 1 mm 비유, `R=R₀A^(1/3)`, He-4 약 2.0 fm, U-238 약 7.7 fm를 재계산했다. 서로 다른 ImageGen 요청과 서로 다른 원본을 사용했으며 크롭·색조 변경 재사용은 없다. **전체 PASS**.

## 003-007 추가 검수

15개 최종 PNG를 원본 1600×900과 400×225 접촉시트로 확인했다. 제목·수식·단위·단계 라벨은 HTML/CSS로 합성되었고 주 피사체를 가리지 않는다. 각 글의 썸네일·본문 2장은 모두 별도 ImageGen 기반이며 SHA-256과 장면 구도가 다르다. 양성자·중성자·전자 역할, A=Z+N, 수소 동위원소 구성, u 변환, 아보가드로상수 계산을 본문과 대조했다. 원본·모바일·기술·중복·가짜문자·겹침 검사는 모두 **PASS**.
