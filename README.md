# 슬라이드 찾기 뷰어 (pptx-viewer)

폰 브라우저에서 `.pptx` 를 열어 보고, 글자를 찾아 그 슬라이드로 넘어가며 해당 글상자를 노란 테두리로 표시하는 웹앱.
파일은 기기 안에서만 읽고 어디로도 보내지 않는다(글꼴 이름만 Google Fonts 에 요청할 수 있음).

- 웹 주소: https://qmast1973.github.io/pptx-viewer/ (GitHub Pages)
- 로컬: `index.html` 을 브라우저로 바로 열어도 동작 (렌더러를 페이지 안에 묶어 넣어 인터넷 없이도 열림)

## 기능
- 화면(2026-10-20, christophervr.github.io/ooxml/pptx 앱 화면 참고): 어두운 앱 화면, 위 제목줄(파일 이름·쪽 수·찾기·파일 열기), PC 는 왼쪽 썸네일 줄(현재 쪽 주황 표시, 찾은 쪽 노란 점)·가운데 슬라이드·오른쪽 찾기 결과, 폰은 한 줄(슬라이드 → 상태줄 → 가로 썸네일 → 결과). 썸네일은 따로 불러온 두 번째 렌더러로 그려 쪽 넘김을 막지 않음
- 파일 열기(고르는 창에 .pptx 만 표시), 이전/다음, 좌우 밀기, 키보드 ←/→
- 확대·축소(100~500%): －/＋/맞춤 버튼, 두 손가락 벌리기, Ctrl+휠, +/−/0 키. 확대하면 슬라이드 칸 안에서 밀어 보고, 좌우 밀기 쪽 넘김은 100%일 때만
- 전체화면: 슬라이드 오른쪽 위에 떠 있는 아이콘 버튼(보통 화면 = 펼치기 아이콘, 전체화면 = 접기 아이콘) 또는 F 키. 브라우저 전체화면이 안 되는 폰(아이폰 등)은 화면을 덮는 방식으로 대신하고 Esc·버튼으로 끝
- 전체화면에서는 아래 버튼줄을 숨기고 오른쪽 위에 쪽 번호·🔍 찾기·접기 아이콘·⋮ 메뉴만 둔다. 🔍(또는 메뉴 '찾기')는 전체화면 안에 찾기 막대(입력·찾기·n/전체·◀▶·✕, Esc 로 닫기)를 띄운다. 메뉴: 찾기, 찾기 결과 목록 보기(전체화면 끝), 이전/다음 결과(찾은 게 있을 때), 이전/다음 쪽, 확대·축소·화면에 맞춤, 전체화면 끝
- 찾기: 대소문자 무시, 띄어쓰기는 그대로. 결과 목록(쪽 번호·제목·찾은 문단)을 누르면 그 슬라이드로 이동, '이전/다음 결과'
- 찾은 글상자 표시: 슬라이드 XML 에 위치가 적힌 글상자만 (레이아웃에서 위치를 물려받는 자리표시자·그룹 안 글상자는 목록에만 나옴)

## 구성
| 파일 | 내용 |
|---|---|
| `viewer.src.html` | 화면 원본 (`__BUNDLE__`, `__SAMPLE_B64__` 자리) |
| `index.html` | 만들어진 완전한 페이지 (`python tools/build.py`) — GitHub Pages 배포 |
| `artifact.html` | 같은 내용의 본문 조각 — claude.ai Artifact 용 |
| `vendor/pptx-browser-4.1.5/` | 오픈소스 렌더러 사본 (MIT). 버그 2곳 수정 — `PATCH.md` |
| `vendor/pptx-browser.bundle.js` | 위 사본을 esbuild 로 묶은 것 (전역 `PPTX`) |
| `tools/search.mjs` | 화면 없이 찾기 (에이전트·시험용) |
| `tools/make_sample.py` | 첫 화면 예시 `sample/예시_발표.pptx` 생성 (python-pptx) |

## 명령
```powershell
node tools\search.mjs <파일.pptx> <찾을말>          # JSON: {slides, hits:[{slide, title, text[]}]}
npx -y esbuild@0.20.2 tools/entry.js --bundle --format=iife --global-name=PPTX --minify --outfile=vendor/pptx-browser.bundle.js   # 렌더러 수정 후
python tools\build.py                               # index.html 다시 만들기
```
페이지 안 조작(헤드리스 시험용): `window.pptxViewer.open(Uint8Array, 이름)`, `.search("말")`, `.go(번호0부터)`, `.setZoom(배율)`, `.toggleFull()`, `.openFind()`, `.menu("find"|"search"|"hitPrev"|"hitNext"|"prev"|"next"|"zoomIn"|"zoomOut"|"fit"|"exit")`, `.state`({slide, count, query, hits, zoom, full}).

## 확인한 것 (2026-10-20, 헤드리스 Edge 400px 폭)
- 예시 4장: "매출" → 1·2·4쪽, 2쪽 글상자 3개 표시, 결과 없음 문구, 가로 스크롤 없음
- 실제 발표자료 6장: 열기 약 2.5초, "에이전트" 6쪽 모두 찾음, 글자 정상 표시
- 한계: `.ppt`(97~2003) 미지원, 복잡한 도형·차트·SmartArt 는 원본과 다르게 보일 수 있음(렌더러 한계)

## 라이선스
`vendor/pptx-browser-4.1.5/` 는 pptx-browser (MIT, `vendor/pptx-browser-4.1.5/LICENSE`) 수정본. 첫 화면 예시 발표자료는 이 저장소용으로 만든 가상 내용.
