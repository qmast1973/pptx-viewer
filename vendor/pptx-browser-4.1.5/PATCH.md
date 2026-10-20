# pptx-browser 4.1.5 (MIT) 로컬 사본

출처: npm `pptx-browser@4.1.5` (https://registry.npmjs.org/pptx-browser/-/pptx-browser-4.1.5.tgz), 라이선스 `LICENSE` (MIT).

수정 2곳 (2026-10-20):
- `src/render.js` 글자 그리기: `getRunColorInherited()`가 이미 `rgb(...)` 문자열을 돌려주는데 `colorToCss()`로 한 번 더 바꿔
  `rgb(undefined,…)`가 되어 글자색이 무시되고 직전 채우기 색(배경 흰색)으로 그려지던 문제 → 문자열이면 그대로 사용.
- `src/render.js` `renderTextBody`: 문단마다 `defRPr`를 선언하기 전에 `parseBullet(pPr, defRPr, …)`에서 써서
  `ReferenceError`(TDZ) → 문단 속성(pPr)이 있는 글상자는 글자가 전혀 안 그려지던 문제 → 선언을 위로 옮김.
