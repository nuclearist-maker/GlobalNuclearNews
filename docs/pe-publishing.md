# 발전기술사 준비 게시판 추가·갱신

한국어판의 `ko/pe/index.html`에서 개념설명과 연도별 기출문제 풀이를 제공합니다. 연도는 게시물 메타데이터에서 자동 생성하며 교시·문제번호 순으로 정렬합니다. 영어 번역이 없는 글은 한국어판에만 표시합니다.

## 원본 패키지

입력 폴더의 `concept/<slug>/` 또는 `exam/<slug>/` 아래에 다음을 둡니다.

- `final_post.md`: 제목과 본문, 참고문헌, 상대 경로 이미지 참조
- `meta.json`: `id`, `title`, `domain`, `created_at`, `related`, `status`
- 본문 참조 이미지와 선택적인 `thumbnail_01.png`

개념 ID는 `C-FM-001` 같은 `C-분야코드-세자리번호`, 기출 ID는 `Y2026-1-01` 같은 `Y연도-교시-두자리문제번호`, 연도 총정리는 `H2026` 형식입니다. ID는 URL이 되므로 발행 후 바꾸지 않습니다. 기본 발행 상태는 `발행`, `ready`, `published`입니다.

```powershell
python tools/import_pe.py --source <input-root> --receipt <private-receipt.json>
python tools/build_en_site.py
python tools/check_search_discovery.py
python tools/check_bilingual.py
python tools/check_pe.py
python tools/check_deployment_scope.py --manifest qa/deployments/current.json --site _site
```

`--include-finals`는 상태와 관계없이 모든 최종본을 게시하도록 명시적으로 승인받은 경우에만 사용합니다. 원본 작업자료와 가져오기 영수증은 공개 저장소 밖에 보관합니다. 원본을 삭제하거나 초안 상태로 바꾸어도 이미 가져온 게시물은 자동 삭제하지 않습니다. 삭제는 별도 편집 작업입니다.

가져오기는 공개 가능한 HTML 본문과 실제 참조 이미지, 공개 메타데이터만 생성합니다. `locales/ko/pe/posts.json`과 `bodies/`, `assets/images/ko/pe/`를 함께 커밋해야 합니다. 영어 게시물 배포를 다시 실행해도 이 입력에서 게시판을 재생성합니다.

가져오기는 `qa/deployments/current.json`에 `kind: pe-board`, 이번 신규 URL, 이전 게시물 해시와 변경 기능·사유도 기록합니다. 이 선언을 검토하고 독립 검토, 신규 글·변경 기능의 화면 검사를 완료합니다. 모든 검사 성공 후 정상 Git 배포 절차로 게시합니다. 가져오기 명령 자체는 push하지 않습니다.

## 기본 언어

프로젝트 루트와 `index.html`은 `lang=en` 쿼리가 없으면 한국어 홈으로 이동합니다. 영어 홈 링크는 `index.html?lang=en`을 사용합니다. 언어 선택용 쿠키는 없으며 기존 영어 글의 직접 주소는 유지합니다. JavaScript를 사용하지 않는 환경에서는 루트의 정적 영어 화면에 있는 KOR 링크로 한국어판에 들어갈 수 있습니다.
