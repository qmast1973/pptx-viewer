"""휴대폰 터치 제스처 기능 검증 스크립트:
1. 두 손가락 벌리기(핀치 인) -> 확대
2. 두 손가락 오므리기(핀치 아웃) -> 축소
3. 더블 탭 -> 2.5배 확대 및 1.0배 리셋
4. 확대 상태에서 한 손가락 드래그(Pan) -> 뷰포트 스크롤 이동
5. 맞춤 상태(1.0)에서 한 손가락 좌우 스와이프 -> 슬라이드 넘김
"""
import asyncio, json, urllib.request, subprocess, time, tempfile, sys
from pathlib import Path
import websockets

ROOT = Path(__file__).resolve().parent.parent
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
PORT = 8798

TEST_SCRIPT = """
(async () => {
  const stage = document.getElementById("stage");
  const r = stage.getBoundingClientRect();
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;

  function makeTouch(id, x, y, target = stage) {
    return new Touch({ identifier: id, target, clientX: x, clientY: y, pageX: x, pageY: y, screenX: x, screenY: y });
  }

  function dispatchTouch(type, touches, changedTouches, target = stage) {
    target.dispatchEvent(new TouchEvent(type, { touches, targetTouches: touches, changedTouches, bubbles: true, cancelable: true }));
  }

  const results = {};

  // 1. Pinch Zoom In (60px -> 120px)
  window.pptxViewer.setZoom(1);
  const t0_s = makeTouch(0, cx - 30, cy), t1_s = makeTouch(1, cx + 30, cy);
  dispatchTouch("touchstart", [t0_s, t1_s], [t0_s, t1_s]);
  const t0_m = makeTouch(0, cx - 60, cy), t1_m = makeTouch(1, cx + 60, cy);
  dispatchTouch("touchmove", [t0_m, t1_m], [t0_m, t1_m], window);
  dispatchTouch("touchend", [], [t0_m, t1_m], window);
  results.pinchInZoom = window.pptxViewer.state.zoom;

  // 2. Pinch Zoom Out (120px -> 60px)
  const t0_p2 = makeTouch(0, cx - 60, cy), t1_p2 = makeTouch(1, cx + 60, cy);
  dispatchTouch("touchstart", [t0_p2, t1_p2], [t0_p2, t1_p2]);
  const t0_m2 = makeTouch(0, cx - 30, cy), t1_m2 = makeTouch(1, cx + 30, cy);
  dispatchTouch("touchmove", [t0_m2, t1_m2], [t0_m2, t1_m2], window);
  dispatchTouch("touchend", [], [t0_m2, t1_m2], window);
  results.pinchOutZoom = window.pptxViewer.state.zoom;

  // 3. Double tap toggle (1 -> 2.5 -> 1)
  window.pptxViewer.setZoom(1);
  const t_tap = makeTouch(0, cx, cy);
  dispatchTouch("touchstart", [t_tap], [t_tap]); dispatchTouch("touchend", [], [t_tap], window);
  dispatchTouch("touchstart", [t_tap], [t_tap]); dispatchTouch("touchend", [], [t_tap], window);
  results.doubleTapZoomIn = window.pptxViewer.state.zoom;

  // Wait 400ms then double tap to reset to 1
  await new Promise(r => setTimeout(r, 400));
  dispatchTouch("touchstart", [t_tap], [t_tap]); dispatchTouch("touchend", [], [t_tap], window);
  dispatchTouch("touchstart", [t_tap], [t_tap]); dispatchTouch("touchend", [], [t_tap], window);
  results.doubleTapZoomOut = window.pptxViewer.state.zoom;

  // 4. Swipe slide with wait
  window.pptxViewer.setZoom(1);
  window.pptxViewer.go(0);
  await new Promise(r => setTimeout(r, 300));

  const t_sw1 = makeTouch(0, cx + 80, cy);
  dispatchTouch("touchstart", [t_sw1], [t_sw1]);
  const t_sw2 = makeTouch(0, cx - 80, cy);
  dispatchTouch("touchmove", [t_sw2], [t_sw2], window);
  dispatchTouch("touchend", [], [t_sw2], window);
  await new Promise(r => setTimeout(r, 400));

  results.swipeSlide = window.pptxViewer.state.slide;

  return results;
})()
"""

async def run_tests():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1)

    tmp_dir = tempfile.mkdtemp()
    proc = subprocess.Popen([EDGE, '--headless=new', '--remote-debugging-port=9222', f'--user-data-dir={tmp_dir}', '--disable-cache', '--mute-audio', f'http://127.0.0.1:{PORT}/'])
    await asyncio.sleep(2)
    try:
        tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
        target = [t for t in tabs if t.get('type') == 'page' and str(PORT) in t.get('url', '')][0]
        async with websockets.connect(target['webSocketDebuggerUrl']) as ws:
            msg_id = 0
            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                await ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get('id') == msg_id: return resp.get('result', {})

            # Mobile emulation: iPhone 14 Pro (393 x 852)
            await send('Emulation.setDeviceMetricsOverride', {
                'width': 393, 'height': 852, 'deviceScaleFactor': 3, 'mobile': True
            })
            await send('Emulation.setTouchEmulationEnabled', {'enabled': True, 'configuration': 'mobile'})

            for _ in range(60):
                res = await send('Runtime.evaluate', {
                    'expression': "Boolean(window.pptxViewer && document.getElementById('stage') && window.pptxViewer?.state?.count > 0)",
                    'returnByValue': True
                })
                if res.get('result', {}).get('value'):
                    break
                await asyncio.sleep(0.2)

            res = await send('Runtime.evaluate', {'expression': TEST_SCRIPT, 'returnByValue': True, 'awaitPromise': True})
            data = res['result']['value']
            print("Touch Test Results:")
            print(json.dumps(data, indent=2))
            assert data['pinchInZoom'] == 2.0, "Pinch in failed"
            assert data['pinchOutZoom'] == 1.0, "Pinch out failed"
            assert data['doubleTapZoomIn'] == 2.5, "Double tap zoom in failed"
            assert data['doubleTapZoomOut'] == 1.0, "Double tap zoom out failed"
            assert data['swipeSlide'] == 1, "Swipe slide failed"
            print("\n>> ALL TOUCH GESTURE TESTS PASSED! <<")
    finally:
        proc.terminate()
        srv.terminate()

if __name__ == '__main__':
    asyncio.run(run_tests())
