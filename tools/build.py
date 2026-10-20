"""viewer.src.html 에 묶은 렌더러(vendor/pptx-browser.bundle.js)와 예시 발표자료(sample/예시_발표.pptx)를 base64 로 넣어 index.html 을 만든다."""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "viewer.src.html").read_text(encoding="utf-8")
bundle = (ROOT / "vendor" / "pptx-browser.bundle.js").read_text(encoding="utf-8")
assert "</script" not in bundle
src = src.replace("__BUNDLE__", bundle)
b64 = base64.b64encode((ROOT / "sample" / "예시_발표.pptx").read_bytes()).decode()
(ROOT / "index.html").write_text(src.replace("__SAMPLE_B64__", b64), encoding="utf-8")
print("index.html", len(src) + len(b64), "bytes")
