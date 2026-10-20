# 슬라이드 찾기 뷰어 (pptx-viewer)

폰 브라우저에서 `.pptx` 를 열어 보고, 글자를 찾아 그 슬라이드로 넘어가며 해당 글상자를 노란 테두리로 표시하는 웹앱.
파일은 기기 안에서만 읽고 어디로도 보내지 않는다(글꼴 이름만 Google Fonts 에 요청할 수 있음).

- 웹 주소: https://qmast1973.github.io/pptx-viewer/ (GitHub Pages)
- 로컬: `index.html` 을 브라우저로 바로 열어도 동작 (렌더러를 페이지 안에 묶어 넣어 인터넷 없이도 열림)

## 기능
- **슬라이드 표시**(2026-10-20 교체): 오픈소스 **pptx-vanilla-viewer 3.42.0**(christophervr.github.io/ooxml/pptx, Apache-2.0)가 슬라이드를 진짜 HTML 글자로 그림 → 한글이 글꼴째 보이고 도형·차트·SmartArt 표현이 좋아짐. 뷰어의 영어 메뉴는 끄고(showToolbar:false) 이 페이지의 한글 화면으로 감쌈. PC 는 뷰어의 썸네일 줄을 씀(폰은 숨김), 발표자 노트 줄은 숨김
- 화면: 어두운 앱 화면, 위 제목줄(파일 이름·쪽 수·찾기·파일 열기), PC 는 [썸네일·슬라이드 | 찾기 결과], 폰은 한 줄
- 파일 열기(고르는 창에 .pptx 만 표시), 이전/다음, 좌우 밀기, 키보드 ←/→
- 찾기: 대소문자 무시, 띄어쓰기는 그대로, 문단 단위(슬라이드 XML 은 pptx-browser 로 읽기만 함). 결과 목록·이전/다음 결과. 찾은 **글자 자체를 노랗게**(CSS Highlight API, 크롬·사파리 최신) + 그 글상자에 노란 테두리
- 확대·축소(100~500%): －/＋/맞춤 버튼, 두 손가락 핀치 줌(벌려서 확대·오므려서 축소, 손가락 위치 기준 중심 확대), 더블 탭(1배↔2.5배 토글), 확대 중 한 손가락 드래그(화면 이동/Pan), Ctrl+휠, +/−/0 키 (100% = 칸에 맞춤)
- 전체화면: 슬라이드 오른쪽 위 아이콘 또는 F 키. 안 되는 폰은 화면 덮기. 전체화면에서는 쪽 번호·🔍 찾기 막대·접기 아이콘·⋮ 메뉴(찾기, 결과 목록 보기, 이전/다음 결과·쪽, 확대·축소·맞춤, 끝)

- **앱 설치**(2026-10-20): 제목줄 **앱 설치** 버튼 → 크롬·엣지·삼성 인터넷은 설치 창, 아이폰·아이패드는 Safari '홈 화면에 추가' 안내, 그 밖은 브라우저 메뉴 안내. 설치하면 앱 창으로 열리고(manifest.webmanifest), 앱 파일을 보관해 인터넷 없이도 열림(sw.js). 설치한 앱으로 PC 에서 .pptx 를 바로 열기(file_handlers), 폰에서 카톡 등 → **공유 → 슬라이드 찾기**로 파일 받기(share_target)

## 구성
| 파일 | 내용 |
|---|---|
| `viewer.src.html` | 화면 원본 (`__BUNDLE__`, `__SAMPLE_B64__` 자리) |
| `index.html` | 만들어진 완전한 페이지 (`python tools/build.py`) — GitHub Pages 배포, 뷰어 묶음은 따로 불러옴 |
| `artifact.html` | 같은 내용의 본문 조각 — claude.ai Artifact 용, 뷰어 묶음까지 안에 넣음(약 12MB) |
| `vendor/pptx-vanilla-viewer.bundle.js` | 슬라이드 표시 라이브러리 묶음 (전역 `PVV`, 약 12MB·gzip 3.8MB). 라이선스 `vendor/pptx-vanilla-viewer-3.42.0/LICENSE`·`NOTICE`, 함께 묶인 라이브러리 고지 `…bundle.js.LEGAL.txt` |
| `tools/vv/` | 위 묶음 만들기 (package.json·entry.js, `npm install` 후 esbuild) |
| `vendor/pptx-browser-4.1.5/` · `vendor/pptx-browser.bundle.js` | 찾기용 XML 읽기 (MIT, 예전 렌더러 — 버그 2곳 수정 `PATCH.md`) |
| `manifest.webmanifest` · `icons/` · `sw.js` | 앱 설치 정보·아이콘(`tools/make_icons.py`)·서비스 워커(`tools/sw.template.js` 로 build.py 가 버전 넣어 생성 — 직접 고치지 않음) |
| `tools/search.mjs` | 화면 없이 찾기 (에이전트·시험용) |
| `tools/make_sample.py` | 첫 화면 예시 `sample/예시_발표.pptx` 생성 (python-pptx) |

## 명령
```powershell
node tools\search.mjs <파일.pptx> <찾을말>          # JSON: {slides, hits:[{slide, title, text[]}]}
cd tools/vv; npm install; npx esbuild entry.js --bundle --format=iife --global-name=PVV --minify --target=es2020 --legal-comments=external --outfile=../../vendor/pptx-vanilla-viewer.bundle.js --external:ai --external:@ai-sdk/* --external:y-websocket --external:y-webrtc --external:three --external:three/*; cd ../..   # 뷰어 버전 바꿀 때
npx -y esbuild@0.20.2 tools/entry.js --bundle --format=iife --global-name=PPTX --minify --outfile=vendor/pptx-browser.bundle.js   # 찾기용 읽기 사본 수정 후
python tools\build.py                               # index.html 다시 만들기
```
페이지 안 조작(헤드리스 시험용): `window.pptxViewer.viewer`(pptx-vanilla-viewer 인스턴스), `.open(Uint8Array, 이름)`, `.search("말")`, `.go(번호0부터)`, `.setZoom(배율)`, `.toggleFull()`, `.openFind()`, `.menu("find"|"search"|"hitPrev"|"hitNext"|"prev"|"next"|"zoomIn"|"zoomOut"|"fit"|"exit")`, `.state`({slide, count, query, hits, zoom, full, highlighted, marks}).

## 확인한 것 (2026-10-20, 헤드리스 Edge 400px 폭)
- 예시 4장: "매출" → 1·2·4쪽, 2쪽 글상자 3개 표시, 결과 없음 문구, 가로 스크롤 없음
- 실제 발표자료 6장: 열기 약 2.5초, "에이전트" 6쪽 모두 찾음, 글자 정상 표시
- 한계: `.ppt`(97~2003) 미지원, 복잡한 도형·차트·SmartArt 는 원본과 다르게 보일 수 있음(렌더러 한계)

## 라이선스
`vendor/pptx-browser-4.1.5/` 는 pptx-browser (MIT, `vendor/pptx-browser-4.1.5/LICENSE`) 수정본. 첫 화면 예시 발표자료는 이 저장소용으로 만든 가상 내용.

슬라이드 표시 부분은 pptx-viewer (Copyright 2025-present pptx-viewer contributors, Apache-2.0, `vendor/pptx-vanilla-viewer-3.42.0/NOTICE` — 포함된 mtx-decompressor 는 MPL-2.0).
