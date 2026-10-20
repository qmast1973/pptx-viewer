"""viewer.src.html 에 묶은 렌더러(vendor/pptx-browser.bundle.js)와 예시 발표자료(sample/예시_발표.pptx, base64)를 넣어
- index.html    : 완전한 문서 (doctype·viewport 포함) — GitHub Pages 로 배포되는 페이지
- artifact.html : 본문 조각 — claude.ai Artifact 로 올리는 파일 (Artifact 가 doctype·viewport 를 감싸 줌)
을 만든다."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "viewer.src.html").read_text(encoding="utf-8")
bundle = (ROOT / "vendor" / "pptx-browser.bundle.js").read_text(encoding="utf-8")
assert "</script" not in bundle
src = src.replace("__BUNDLE__", bundle)
b64 = base64.b64encode((ROOT / "sample" / "예시_발표.pptx").read_bytes()).decode()
body = src.replace("__SAMPLE_B64__", b64)
(ROOT / "artifact.html").write_text(body, encoding="utf-8")
head = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta name="viewport" '
        'content="width=device-width,initial-scale=1,viewport-fit=cover">\n')
page = head + body.replace("</style>\n", "</style>\n</head>\n<body>\n", 1) + "\n</body>\n</html>\n"
(ROOT / "index.html").write_text(page, encoding="utf-8")
print("index.html", len(page), "/ artifact.html", len(body), "bytes")
