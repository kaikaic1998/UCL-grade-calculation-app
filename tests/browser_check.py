"""Run calculator checks with Python, websocket-client and an existing Edge/Chrome.

The app itself needs no dependencies. Run: python tests/browser_check.py
"""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request
import websocket

ROOT = Path(__file__).resolve().parents[1]
BROWSER = next((p for p in [
    shutil.which('msedge'), shutil.which('google-chrome'), shutil.which('chromium'),
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
] if p and Path(p).is_file()), None)
if not BROWSER:
    raise SystemExit('No existing Edge/Chrome found. Open index.html for manual checks.')

ENGINE_TESTS = r"""
(() => {
  const checks=[];
  function check(name, fn) {try {fn();checks.push({name,ok:true});}catch(e){checks.push({name,ok:false,error:e.message});}}
  function eq(actual,expected) {if(actual!==expected)throw Error(JSON.stringify(actual)+' != '+JSON.stringify(expected));}
  function truth(v) {if(!v)throw Error('Expected true');}
  function full(taught=65,project=80) {
    const d=Grade.defaults();
    d.modules.forEach(m=>{m.condonement='yes';m.assessments.forEach(a=>{a.score=m.kind==='project'?project:taught;a.requirement='none';});});
    return d;
  }
  function marks(d,values) {d.modules.forEach((m,i)=>m.assessments.forEach(a=>a.score=values[i]));return d;}
  check('Nine correct defaults and 180 credits',()=>{const d=Grade.defaults();eq(d.modules.length,9);eq(Grade.evaluate(d.modules).total,180);eq(d.modules[0].assessments[0].weight,86);eq(d.modules[8].credits,60);});
  check('Blank inputs stay incomplete',()=>{const r=Grade.evaluate(Grade.defaults().modules);eq(r.mark,null);eq(r.low,0);eq(r.high,10000);eq(r.complete,false);});
  check('65 taught + 80 project = 70',()=>{const r=Grade.evaluate(full().modules);eq(r.mark,7000);eq(r.band,'Distinction');truth(r.eligible);eq(r.conditional,false);});
  check('75 taught + 60 project still Distinction',()=>{const r=Grade.evaluate(full(75,60).modules);eq(r.mark,7000);eq(r.band,'Distinction');truth(r.eligible);});
  check('70 taught + 60 project = 66.67',()=>eq(Grade.evaluate(full(70,60).modules).mark,6667));
  check('50/50 module exam 40 + work 60 = pass average',()=>{const d=full(),m=d.modules[3];m.assessments[0].score=40;m.assessments[1].score=60;eq(Grade.moduleResult(m).mark,5000);m.assessments[0].requirement='must';eq(Grade.moduleResult(m).failed.length,1);eq(Grade.evaluate(d.modules).eligible,false);});
  check('Raw marks and decimal half-up rounding',()=>{eq(Grade.percent(32,40),8000);eq(Grade.percent(49.995,100),5000);eq(Grade.percent(1.005,100),101);eq(Grade.percent(1e-7,1e-7),10000);});
  check('Module mean rounds before degree mean',()=>{const d=full(),m=d.modules[3];m.assessments[0].score=49.99;m.assessments[1].score=50;eq(Grade.moduleResult(m).mark,5000);});
  check('Zero is a mark, not missing',()=>{const d=full();d.modules[0].assessments.forEach(a=>a.score=0);truth(Grade.evaluate(d.modules).complete);eq(Grade.moduleResult(d.modules[0]).mark,0);});
  check('Invalid weights block results',()=>{const d=full();d.modules[0].assessments[0].weight=85;truth(Grade.evaluate(d.modules).invalid.length);eq(Grade.solve(d).status,'invalid');});
  check('Invalid raw marks block results',()=>{const d=full();d.modules[0].assessments[0].max=0;truth(Grade.evaluate(d.modules).invalid.length);});
  check('69.50 direct Distinction boundary',()=>eq(Grade.evaluate(full(69.5,69.5).modules).band,'Distinction'));
  check('69.49 without qualifying credits is Merit',()=>eq(Grade.evaluate(full(69.49,69.49).modules).band,'Merit'));
  check('68.50 and 90 qualifying credits is Distinction',()=>{const r=Grade.evaluate(marks(full(),[70,70,67,67,67,67,67,67,70]).modules);eq(r.mark,6850);eq(r.c70,90);eq(r.band,'Distinction');});
  check('68.50 with fewer than 90 qualifying credits is Merit',()=>{const r=Grade.evaluate(full(68.5,68.5).modules);eq(r.c70,0);eq(r.band,'Merit');});
  check('59.50 direct Merit boundary',()=>eq(Grade.evaluate(full(59.5,59.5).modules).band,'Merit'));
  check('59.49 without qualifying credits is Pass',()=>eq(Grade.evaluate(full(59.49,59.49).modules).band,'Pass'));
  check('58.50 and 90 qualifying credits is Merit',()=>{const r=Grade.evaluate(marks(full(),[60,60,57,57,57,57,57,57,60]).modules);eq(r.mark,5850);eq(r.c60,90);eq(r.band,'Merit');});
  check('Failed dissertation prevents award',()=>{const r=Grade.evaluate(full(95,49.99).modules);eq(r.eligible,false);truth(r.reasons.some(s=>s.includes('project must')));});
  check('30 taught credits may be condoned',()=>{const d=full(70,70);d.modules.slice(0,2).forEach(m=>m.assessments.forEach(a=>a.score=40));const r=Grade.evaluate(d.modules);eq(r.condoned,30);truth(r.eligible);});
  check('45 taught failed credits cannot be condoned',()=>{const d=full(70,70);d.modules.slice(0,3).forEach(m=>m.assessments.forEach(a=>a.score=40));eq(Grade.evaluate(d.modules).eligible,false);});
  check('Unknown condonement is conditional',()=>{const d=full();d.modules[0].condonement='unknown';d.modules[0].assessments.forEach(a=>a.score=45);truth(Grade.evaluate(d.modules).conditional);});
  check('Non-condonable failed module prevents award',()=>{const d=full();d.modules[0].condonement='must';d.modules[0].assessments.forEach(a=>a.score=45);eq(Grade.evaluate(d.modules).eligible,false);});
  check('Mark below 40 prevents award',()=>{const d=full();d.modules[0].assessments.forEach(a=>a.score=39.99);eq(Grade.evaluate(d.modules).eligible,false);});
  check('Dissertation solver respects final rounding',()=>{const d=full(65,80);d.modules[8].assessments[0].score=null;d.settings.vary=[d.modules[8].assessments[0].id];const s=Grade.solve(d);eq(s.status,'solution');eq(s.percentage,7849);eq(s.evaluation.mark,6950);eq(Grade.evaluate(d.modules,new Map([[s.ids[0],7848]])).mark,6949);});
  check('Alternative route affects solver',()=>{const d=marks(full(),[70,70,67,67,67,67,67,67,70]);d.modules[8].assessments[0].score=null;d.settings.vary=[d.modules[8].assessments[0].id];eq(Grade.solve(d).percentage,7000);});
  check('Module solver ignores unrelated blank modules',()=>{const d=Grade.defaults(),m=d.modules[3];d.settings.scope=m.id;d.settings.target='50';d.settings.vary=[m.assessments[0].id];m.assessments[1].score=60;eq(Grade.solve(d).percentage,3999);m.assessments[0].requirement='must';eq(Grade.solve(d).percentage,5000);});
  check('Selected assessments use a common percentage',()=>{const d=full();d.settings.vary=d.modules.flatMap(m=>m.assessments.map(a=>a.id));const s=Grade.solve(d);eq(s.percentage,6950);eq(s.evaluation.mark,6950);});
  check('Unselected blanks are reported',()=>eq(Grade.solve(Grade.defaults()).status,'missing'));
  check('Impossible target is reported',()=>{const d=full(40,60);d.settings.vary=[d.modules[8].assessments[0].id];eq(Grade.solve(d).status,'impossible');});
  check('Already achieved target is reported',()=>eq(Grade.solve(full(80,80)).status,'achieved'));
  check('Blank custom target is invalid, not zero',()=>{const d=full();d.settings.scope=d.modules[0].id;d.settings.target='custom';d.settings.customTarget=null;eq(Grade.solve(d).status,'invalid');});
  check('Custom credits and missing projects are explicit',()=>{const d=full();d.modules.pop();const r=Grade.evaluate(d.modules);truth(r.custom);eq(r.eligible,false);eq(r.mark,6500);});
  check('Empty modules are safe',()=>{const d=full();d.modules=[];eq(Grade.evaluate(d.modules).mark,null);eq(Grade.solve(d).status,'invalid');});
  check('JSON round-trip and duplicate ID rejection',()=>{const restored=Grade.assertDocument(JSON.parse(JSON.stringify(full())));eq(Grade.evaluate(restored.modules).mark,7000);restored.modules[1].id=restored.modules[0].id;let rejected=false;try{Grade.assertDocument(restored);}catch(e){rejected=true;}truth(rejected);});
  check('Invalid numeric JSON rejected',()=>{const d=full();d.modules[0].assessments[0].score=-5;let rejected=false;try{Grade.assertDocument(d);}catch(e){rejected=true;}truth(rejected);});
  check('Incomplete input remains recoverable as draft',()=>{const d=full();d.modules[0].credits=null;Grade.assertDocument(d);truth(Grade.evaluate(d.modules).invalid.length);});
  return checks;
})()
"""


def main():
    with tempfile.TemporaryDirectory(prefix='ucl-grade-check-') as temp:
        process = subprocess.Popen([
            BROWSER, '--headless=new', '--disable-gpu', '--no-first-run',
            '--no-default-browser-check', '--remote-debugging-port=0',
            '--remote-allow-origins=http://localhost', f'--user-data-dir={temp}', 'about:blank',
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        ws = None
        try:
            port_file = Path(temp) / 'DevToolsActivePort'
            deadline = time.monotonic() + 20
            while not port_file.exists():
                if time.monotonic() > deadline:
                    raise RuntimeError('Browser debugging endpoint did not start')
                time.sleep(.1)
            port = port_file.read_text().splitlines()[0]
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list') as response:
                targets = json.load(response)
            target = next(t for t in targets if t['type'] == 'page')
            ws = websocket.create_connection(target['webSocketDebuggerUrl'], origin='http://localhost', timeout=20)
            counter = 0
            events = []

            def command(method, params=None):
                nonlocal counter
                counter += 1
                ws.send(json.dumps({'id': counter, 'method': method, 'params': params or {}}))
                while True:
                    message = json.loads(ws.recv())
                    if message.get('id') == counter:
                        if 'error' in message:
                            raise RuntimeError(message['error'])
                        return message.get('result', {})
                    events.append(message)

            def js(expression):
                result = command('Runtime.evaluate', {'expression': expression, 'returnByValue': True, 'awaitPromise': True})
                if 'exceptionDetails' in result:
                    raise RuntimeError(result['exceptionDetails'])
                return result['result'].get('value')

            def wait_ready():
                time.sleep(.1)
                deadline = time.monotonic() + 10
                while not js("document.readyState==='complete' && !!document.getElementById('overall')"):
                    if time.monotonic() > deadline:
                        raise RuntimeError('Page did not load')
                    time.sleep(.05)

            def wait_js(expression):
                deadline = time.monotonic() + 5
                while not js(expression):
                    if time.monotonic() > deadline:
                        raise RuntimeError('Browser action did not finish: ' + expression)
                    time.sleep(.05)

            def import_file(path):
                document = command('DOM.getDocument')
                node = command('DOM.querySelector', {'nodeId': document['root']['nodeId'], 'selector': '#import-file'})
                command('DOM.setFileInputFiles', {'nodeId': node['nodeId'], 'files': [str(path)]})

            command('Runtime.enable')
            command('Page.enable')
            command('Page.navigate', {'url': (ROOT / 'index.html').as_uri()})
            wait_ready()
            checks = js(ENGINE_TESTS)

            def ui_check(name, expression):
                try:
                    value = js(expression)
                    checks.append({'name': name, 'ok': value is True, 'error': None if value is True else repr(value)})
                except Exception as error:
                    checks.append({'name': name, 'ok': False, 'error': str(error)})

            ui_check('UI: initial nine modules render', "document.querySelectorAll('.module').length===9 && document.getElementById('classification').textContent==='Incomplete'")
            ui_check('UI: assessment map shows all modules and categories without internal scrolling', "document.querySelectorAll('.map-module').length===9 && document.querySelectorAll('.category-chip').length===17 && getComputedStyle(document.getElementById('assessment-map')).overflowY!=='auto' && getComputedStyle(document.getElementById('solver-message')).maxHeight==='none'")
            ui_check('UI: map selection synchronises Vary and preserves keyboard focus', r"""(() => {document.querySelector('.category-chip').click();const chip=document.querySelector('.category-chip');const ok=chip.getAttribute('aria-pressed')==='true' && document.querySelector('[data-action=vary]').checked && document.activeElement===chip;chip.click();return ok && document.querySelector('.category-chip').getAttribute('aria-pressed')==='false' && !document.querySelector('[data-action=vary]').checked;})()""")
            ui_check('UI: typing preserves focus and updates mark', r"""(() => {const input=document.querySelector('[data-field="score"]');input.focus();input.value='80';input.dispatchEvent(new Event('input',{bubbles:true}));return document.activeElement===input && document.querySelector('.assessment-result').textContent.includes('80.00%');})()""")
            ui_check('UI: entered marks appear as fixed in the map', "document.querySelector('.category-chip').classList.contains('fixed') && document.querySelector('.category-chip').textContent.includes('80.00%')")
            ui_check('UI: storage captures entered mark', "JSON.parse(localStorage.getItem('ucl-grade-calculator-v1')).modules[0].assessments[0].score===80")
            command('Page.reload')
            wait_ready()
            ui_check('UI: file autosave restores on reload', "document.querySelector('[data-field=score]').value==='80'")
            ui_check('UI: bulk deletion and undo restore module', r"""(() => {document.querySelector('[data-action="select-module"]').click();document.getElementById('delete-selected').click();if(document.querySelectorAll('.module').length!==8)return false;document.getElementById('undo').click();return document.querySelectorAll('.module').length===9 && document.querySelector('[data-field=score]').value==='80';})()""")
            ui_check('UI: adding and deleting assessment', r"""(() => {const count=document.querySelectorAll('tbody tr').length;document.querySelector('[data-action="add-assessment"]').click();if(document.querySelectorAll('tbody tr').length!==count+1)return false;document.querySelector('.module tbody tr:last-child [data-action="delete-assessment"]').click();return document.querySelectorAll('tbody tr').length===count;})()""")
            ui_check('UI: single module deletion and undo', r"""(() => {document.querySelector('[data-action="delete-module"]').click();if(document.querySelectorAll('.module').length!==8)return false;document.getElementById('undo').click();return document.querySelectorAll('.module').length===9;})()""")
            ui_check('UI: mixed module and assessment bulk deletion', r"""(() => {const n=document.querySelectorAll('tbody tr').length;document.querySelector('[data-action="select-module"]').click();document.querySelectorAll('.module')[1].querySelector('[data-action="select-assessment"]').click();document.getElementById('delete-selected').click();if(document.querySelectorAll('.module').length!==8 || document.querySelectorAll('tbody tr').length!==n-3)return false;document.getElementById('undo').click();return document.querySelectorAll('.module').length===9 && document.querySelectorAll('tbody tr').length===n;})()""")
            ui_check('UI: add module with editable default assessment', "(() => {document.getElementById('add-module').click();const ok=document.querySelectorAll('.module').length===10 && document.querySelector('.module:last-child [data-field=weight]').value==='100';document.querySelector('.module:last-child [data-action=delete-module]').click();return ok && document.querySelectorAll('.module').length===9;})()")
            ui_check('UI: text labels render safely', r"""(() => {const input=document.querySelector('[data-field="name"]');input.value='<img src=x onerror=alert(1)>';input.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('vary-clear').click();return document.querySelector('[data-field="name"]').value==='<img src=x onerror=alert(1)>' && !document.querySelector('img');})()""")
            js("localStorage.setItem('ucl-grade-calculator-v1',JSON.stringify((()=>{const d=Grade.defaults();d.modules.forEach(m=>m.assessments.forEach(a=>a.score=m.kind==='project'?80:65));return d;})()))")
            command('Page.reload')
            wait_ready()
            ui_check('UI: project solver and Apply', r"""(() => {if(document.getElementById('overall').textContent!=='70.00%')return false;document.getElementById('vary-project').click();if(!document.getElementById('solver-message').textContent.includes('78.49%'))return false;document.getElementById('apply').click();return document.getElementById('overall').textContent==='69.50%' && document.querySelector('.module:last-child [data-field="score"]').value==='78.49';})()""")
            ui_check('UI: invalid weights block final result', r"""(() => {const input=document.querySelector('[data-field="weight"]');input.value='85';input.dispatchEvent(new Event('input',{bubbles:true}));return document.getElementById('classification').textContent==='Invalid inputs' && document.getElementById('overall').textContent==='—';})()""")
            ui_check('UI: module targets and separate-pass minimum update', r"""(() => {const scope=document.getElementById('scope');scope.value=document.querySelectorAll('.module')[3].querySelector('[data-field=name]').dataset.mid;scope.dispatchEvent(new Event('change'));const rows=document.querySelectorAll('.module')[3].querySelectorAll('tbody tr');const score=rows[1].querySelector('[data-field=score]');score.value='60';score.dispatchEvent(new Event('input',{bubbles:true}));rows[0].querySelector('[data-action=vary]').click();const requirement=rows[0].querySelector('[data-field=requirement]');requirement.value='must';requirement.dispatchEvent(new Event('input',{bubbles:true}));return document.getElementById('solver-message').textContent.includes('50.00%') && !rows[0].querySelector('.minimum').hidden;})()""")
            # Test export and import using real browser file I/O in the isolated profile.
            downloads = Path(temp) / 'downloads'
            downloads.mkdir()
            command('Browser.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': str(downloads)})
            js("document.getElementById('export').click()")
            exported = downloads / 'ucl-grade-scenario.json'
            deadline = time.monotonic() + 5
            while not exported.exists():
                if time.monotonic() > deadline:
                    raise RuntimeError('JSON export did not download')
                time.sleep(.05)
            backup = json.loads(exported.read_text(encoding='utf-8'))
            checks.append({'name': 'UI: JSON export downloads complete state', 'ok': backup['version'] == 1 and len(backup['modules']) == 9})
            backup['modules'][0]['name'] = 'Imported scenario'
            import_path = Path(temp) / 'import.json'
            import_path.write_text(json.dumps(backup), encoding='utf-8')
            js('window.confirm=()=>true')
            import_file(import_path)
            wait_js("document.getElementById('feedback').textContent==='Scenario imported.'")
            ui_check('UI: valid JSON import restores structure and data', "document.querySelector('[data-field=name]').value==='Imported scenario' && document.querySelectorAll('.module').length===9")
            import_path.write_text('{"version":999}', encoding='utf-8')
            import_file(import_path)
            wait_js("document.getElementById('feedback').textContent.startsWith('Import failed:')")
            ui_check('UI: rejected JSON import retains current data', "document.querySelector('[data-field=name]').value==='Imported scenario'")
            ui_check('UI: reset cancellation retains marks', "(() => {window.confirm=()=>false;document.getElementById('reset').click();return document.querySelector('[data-field=name]').value==='Imported scenario';})()")
            ui_check('UI: confirmed reset restores blank defaults', "(() => {window.confirm=()=>true;document.getElementById('reset').click();return document.querySelector('[data-field=name]').value==='Supervised Learning' && document.querySelector('[data-field=score]').value==='';})()")
            js("localStorage.removeItem('ucl-grade-calculator-v1')")
            command('Page.reload')
            wait_ready()
            command('Emulation.setDeviceMetricsOverride', {'width': 1280, 'height': 1000, 'deviceScaleFactor': 1, 'mobile': False})
            js('window.scrollTo(0,0); new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            screenshot = command('Page.captureScreenshot', {'format': 'png'})
            (ROOT / 'tests' / 'preview.png').write_bytes(base64.b64decode(screenshot['data']))
            command('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
            command('Emulation.setPageScaleFactor', {'pageScaleFactor': 1})
            js('window.scrollTo(0,0); new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            ui_check('UI: narrow layout has no page overflow', "window.innerWidth===390 && document.documentElement.scrollWidth<=390 || {innerWidth:window.innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('main,main>*,.module-head,.module-result,.module-footer')].filter(e=>e.getBoundingClientRect().right>390).map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))}")
            screenshot = command('Page.captureScreenshot', {'format': 'png'})
            (ROOT / 'tests' / 'preview-mobile.png').write_bytes(base64.b64decode(screenshot['data']))
            exceptions = [e for e in events if e.get('method') == 'Runtime.exceptionThrown']
            checks.append({'name': 'UI: no uncaught JavaScript exceptions', 'ok': not exceptions, 'error': exceptions or None})
            report = {'passed': sum(c['ok'] for c in checks), 'total': len(checks), 'checks': checks}
            (ROOT / 'tests' / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps({'passed': report['passed'], 'total': report['total'], 'failures': [c for c in checks if not c['ok']]}, indent=2))
            if report['passed'] != report['total']:
                raise SystemExit(1)
        finally:
            if ws:
                ws.close()
            # Terminate only the isolated browser launched by this test.
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            time.sleep(.5)


if __name__ == '__main__':
    main()
