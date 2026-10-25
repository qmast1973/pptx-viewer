"""실제 입력 경로(CDP Input.dispatchTouchEvent)로 핀치·밀기·더블탭을 넣어 보는 시험 (헤드리스 Chrome, 소리 끔).
tools/test_touch.py 는 자바스크립트로 만든 가짜 터치라서 안쪽 라이브러리의 자체 핀치와 겹쳐 생기는 문제(2026-10-21: 핀치 한 번에 3~5%만 확대)를 잡지 못했다. 이 시험이 그걸 잡는다.
  python tools/test_touch_real.py [폴더 또는 https 주소] [포트]   (기본: 이 폴더를 http.server 로 띄움)
기대: 2배 핀치 → zoom 2, 한 번 더 → 4, 오므리면 줄어 맞춤(1), 왼쪽 밀기 → 다음 쪽, 더블 탭 → 2.5 → 1."""
import asyncio, json, urllib.request, subprocess, tempfile, sys, shutil
import websockets
ROOT = sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parent.parent)
PORT, DBG = int(sys.argv[2]) if len(sys.argv) > 2 else 8791, 9333
REMOTE = ROOT.startswith('http')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

async def main():
    srv = None if REMOTE else subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--directory", ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp = tempfile.mkdtemp()
    proc = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={DBG}', f'--user-data-dir={tmp}', '--disable-cache', '--mute-audio', '--no-first-run', ROOT if REMOTE else f'http://127.0.0.1:{PORT}/'])
    try:
        await asyncio.sleep(3)
        tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{DBG}/json').read().decode())
        target = [t for t in tabs if t.get('type') == 'page' and t.get('url', '').startswith('http')][0]
        async with websockets.connect(target['webSocketDebuggerUrl'], max_size=None) as ws:
            n = 0
            async def send(m, p=None):
                nonlocal n; n += 1
                await ws.send(json.dumps({'id': n, 'method': m, 'params': p or {}}))
                while True:
                    r = json.loads(await ws.recv())
                    if r.get('method') == 'Runtime.exceptionThrown':
                        d = r['params']['exceptionDetails']; print('   !! EXC', d.get('text'), (d.get('exception') or {}).get('description', '')[:300])
                    if r.get('method') == 'Runtime.consoleAPICalled' and r['params']['type'] in ('error', 'warning'):
                        print('   !! CONSOLE', [a.get('value') or a.get('description') for a in r['params']['args']][:3])
                    if r.get('id') == n: return r.get('result', {})
            async def ev(js):
                r = await send('Runtime.evaluate', {'expression': js, 'returnByValue': True, 'awaitPromise': True})
                return r.get('result', {}).get('value')
            await send('Runtime.enable')
            await send('Emulation.setDeviceMetricsOverride', {'width': 393, 'height': 852, 'deviceScaleFactor': 3, 'mobile': True})
            await send('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
            for _ in range(80):
                if await ev("Boolean(window.pptxViewer && window.pptxViewer.state.count>0)"): break
                await asyncio.sleep(0.25)
            await asyncio.sleep(1.5)
            await ev("window.__log=[];for(const t of ['touchstart','touchmove','touchend','touchcancel'])window.addEventListener(t,e=>window.__log.push(t+':'+e.touches.length+(e.defaultPrevented?'P':'')),{capture:true,passive:true});1")
            probe = "(()=>{const w=document.querySelector('.pptxv-stage-wrap');const r=w?w.getBoundingClientRect():{width:0};return {zoom:window.pptxViewer.state.zoom, wrapW:Math.round(r.width), tr:w?w.style.transform:''}})()"
            r = await ev("(()=>{const r=document.getElementById('stage').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
            cx, cy = r
            print('stage center', cx, cy, 'start', await ev(probe))
            async def touch(kind, pts):
                await send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})
            async def pinch(d0, d1, steps=20, dt=0.016):
                await touch('touchStart', [(cx - d0/2, cy), (cx + d0/2, cy)])
                for i in range(1, steps + 1):
                    d = d0 + (d1 - d0) * i / steps
                    await touch('touchMove', [(cx - d/2, cy), (cx + d/2, cy)])
                    await asyncio.sleep(dt)
                    if i in (steps // 2, steps): print(f'   step {i}/{steps} d={d:.0f}', await ev(probe))
                await touch('touchEnd', [])
                await asyncio.sleep(0.6)
            print('--- pinch out 100 -> 200 (2x)'); await pinch(100, 200); print('after', await ev(probe))
            print('--- pinch out 100 -> 200 again'); await pinch(100, 200); print('after', await ev(probe))
            print('events', await ev('JSON.stringify(window.__log.slice(0,12))'), await ev('window.__log.length'))
            print('--- pinch in 200 -> 100'); await pinch(200, 100); print('after', await ev(probe))
            print('--- pinch in to fit (200 -> 20)'); await pinch(200, 20); print('after', await ev(probe))
            async def drag(x0, y0, x1, y1, steps=8):
                await touch('touchStart', [(x0, y0)])
                for i in range(1, steps + 1):
                    await touch('touchMove', [(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)]); await asyncio.sleep(0.016)
                await touch('touchEnd', []); await asyncio.sleep(0.5)
            await ev("window.pptxViewer.setZoom(1)"); await asyncio.sleep(0.5)
            s0 = await ev("window.pptxViewer.state.slide")
            await drag(cx + 100, cy, cx - 100, cy); s1 = await ev("window.pptxViewer.state.slide")
            print('swipe left: slide', s0, '->', s1)
            async def tap():
                await touch('touchStart', [(cx, cy)]); await touch('touchEnd', [])
            await tap(); await asyncio.sleep(0.1); await tap(); await asyncio.sleep(0.6)
            print('double tap ->', await ev(probe))
            sl = "(()=>{const v=document.querySelector('.pptxv-viewport');return [v.scrollLeft,v.scrollTop]})()"
            b0 = await ev(sl); await drag(cx + 60, cy + 60, cx - 20, cy - 20); print('pan scroll', b0, '->', await ev(sl))
            await tap(); await asyncio.sleep(0.1); await tap(); await asyncio.sleep(0.6)
            print('double tap again ->', await ev(probe))
    finally:
        proc.terminate()
        if srv: srv.terminate()
        await asyncio.sleep(1)
        shutil.rmtree(tmp, ignore_errors=True)
asyncio.run(main())
