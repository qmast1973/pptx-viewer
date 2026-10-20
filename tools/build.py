"""viewer.src.html 로 배포용 페이지 두 개를 만든다.
- index.html    : 완전한 문서 (doctype·viewport 포함) — GitHub Pages. 슬라이드 뷰어 묶음은 vendor/pptx-vanilla-viewer.bundle.js 를 따로 불러온다(한 번 받으면 브라우저가 보관)
- artifact.html : 본문 조각 — claude.ai Artifact. 다른 파일을 불러올 수 없으므로 뷰어 묶음까지 페이지 안에 넣는다
찾기용 pptx-browser 묶음(vendor/pptx-browser.bundle.js)과 예시 발표자료(sample/예시_발표.pptx, base64)는 두 페이지 모두 안에 넣는다."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PVV_TAG = '<script src="vendor/pptx-vanilla-viewer.bundle.js"></script>'
src = (ROOT / "viewer.src.html").read_text(encoding="utf-8")
bundle = (ROOT / "vendor" / "pptx-browser.bundle.js").read_text(encoding="utf-8")
pvv = (ROOT / "vendor" / "pptx-vanilla-viewer.bundle.js").read_text(encoding="utf-8")
assert "</script" not in bundle and "</script" not in pvv and src.count(PVV_TAG) == 1
src = src.replace("__BUNDLE__", bundle)
b64 = base64.b64encode((ROOT / "sample" / "예시_발표.pptx").read_bytes()).decode()
body = src.replace("__SAMPLE_B64__", b64)
(ROOT / "artifact.html").write_text(body.replace(PVV_TAG, "<script>" + pvv + "</script>"), encoding="utf-8")
head = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta name="viewport" '
        'content="width=device-width,initial-scale=1,viewport-fit=cover">\n')
page = head + body.replace("</style>\n", "</style>\n</head>\n<body>\n", 1) + "\n</body>\n</html>\n"
(ROOT / "index.html").write_text(page, encoding="utf-8")
print("index.html", len(page), "/ artifact.html", len(body) + len(pvv), "bytes / pvv bundle", len(pvv))
