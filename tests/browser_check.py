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
  check('Invalid weights block results',()=>{const d=full();d.modules[0].assessments[0].weight=85;truth(Grade.evaluate(d.modules).invalid.length);});
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
  check('Custom credits and missing projects are explicit',()=>{const d=full();d.modules.pop();const r=Grade.evaluate(d.modules);truth(r.custom);eq(r.eligible,false);eq(r.mark,6500);});
  check('Empty modules are safe',()=>{const d=full();d.modules=[];eq(Grade.evaluate(d.modules).mark,null);});
  check('JSON round-trip and duplicate ID rejection',()=>{const restored=Grade.assertDocument(JSON.parse(JSON.stringify(full())));eq(Grade.evaluate(restored.modules).mark,7000);restored.modules[1].id=restored.modules[0].id;let rejected=false;try{Grade.assertDocument(restored);}catch(e){rejected=true;}truth(rejected);});
  check('Invalid numeric JSON rejected',()=>{const d=full();d.modules[0].assessments[0].score=-5;let rejected=false;try{Grade.assertDocument(d);}catch(e){rejected=true;}truth(rejected);});
  check('Incomplete input remains recoverable as draft',()=>{const d=full();d.modules[0].credits=null;Grade.assertDocument(d);truth(Grade.evaluate(d.modules).invalid.length);});
  check('Legacy backup keeps marks and loads default forecasts without old controls',()=>{const d=full();delete d.forecast;d.settings={scope:'degree',target:'distinction',vary:['retired-selection']};const restored=Grade.assertDocument(JSON.parse(JSON.stringify(d)));eq(Grade.evaluate(restored.modules).mark,7000);eq(restored.settings,undefined);eq(restored.forecast.target,'distinction');eq(restored.forecast.assumption,70);});
  check('Independent estimates differ by module credits and preserve entered state',()=>{const d=Grade.defaults(),before=JSON.stringify(d);const a=Grade.estimateModule(d.modules,d.modules[0].id,'distinction',70),p=Grade.estimateModule(d.modules,d.modules[8].id,'distinction',70);eq(a.status,'needed');eq(a.percentage,5194);eq(p.percentage,6549);eq(a.evaluation.mark,6850);eq(p.evaluation.mark,6850);eq(JSON.stringify(d),before);});
  check('Other-module assumption changes reachability and required project marks',()=>{const d=Grade.defaults();eq(Grade.estimateModule(d.modules,d.modules[0].id,'distinction',60).status,'impossible');eq(Grade.estimateModule(d.modules,d.modules[8].id,'distinction',60).percentage,8849);});
  check('Project-only blank uses final rounding and entered taught marks',()=>{const d=full(65,80),p=d.modules[8];p.assessments[0].score=null;const e=Grade.estimateModule(d.modules,p.id,'distinction',null);eq(e.percentage,7849);eq(e.assumptionUsed,false);eq(e.evaluation.mark,6950);eq(Grade.evaluate(d.modules,new Map([[p.assessments[0].id,7848]])).mark,6949);});
  check('Completed module exam what-if uses degree target and keeps coursework fixed',()=>{const d=full(65,80),m=d.modules[0],before=JSON.stringify(d);const e=Grade.estimateModule(d.modules,m.id,'distinction',70);eq(e.mode,'exam');eq(e.percentage,5795);eq(e.assessmentIds.length,1);eq(e.assessmentIds[0],m.assessments[0].id);eq(JSON.stringify(d),before);const lower=new Map([[m.assessments[0].id,e.percentage-1]]);eq(Grade.meets(Grade.evaluate(d.modules,lower),'distinction'),false);});
  check('Multiple module blanks receive the same percentage',()=>{const d=Grade.defaults(),m=d.modules[7];const e=Grade.estimateModule(d.modules,m.id,'distinction',70);eq(e.assessmentIds.length,3);const r=e.evaluation.results.find(r=>r.module.id===m.id);truth(r.parts.every(p=>p.percent===e.percentage));});
  check('Known separate-pass requirements constrain estimated blank exams',()=>{const d=Grade.defaults(),m=d.modules[0];m.assessments[0].requirement='must';m.assessments[0].minimum=55;eq(Grade.estimateModule(d.modules,m.id,'pass',70).percentage,5500);});
  check('Fixed failed component cannot be repaired by estimating a different blank',()=>{const d=Grade.defaults(),m=d.modules[0];m.assessments[0].score=40;m.assessments[0].requirement='must';eq(Grade.estimateModule(d.modules,m.id,'pass',70).status,'impossible');});
  check('Condonement and mandatory module pass alter required estimates',()=>{const d=Grade.defaults(),m=d.modules[0];m.condonement='yes';eq(Grade.estimateModule(d.modules,m.id,'pass',70).percentage,4000);m.condonement='must';eq(Grade.estimateModule(d.modules,m.id,'pass',70).percentage,5000);});
  check('Completed module without an exam is fixed, but its blanks can be estimated',()=>{const d=full(),m=d.modules[4];eq(Grade.estimateModule(d.modules,m.id,'distinction',70).status,'fixed');m.assessments[0].score=null;eq(Grade.estimateModule(d.modules,m.id,'distinction',70).mode,'blanks');});
  check('Failed fixed project blocks estimates in other modules',()=>{const d=Grade.defaults();d.modules[8].assessments[0].score=49;eq(Grade.estimateModule(d.modules,d.modules[0].id,'pass',70).status,'impossible');});
  check('Actual lower classifications and projected classifications remain distinct',()=>{const d=full(60,60),f=Grade.forecast(d.modules,70);eq(f.status,'current');truth(Grade.meets(f.evaluation,'pass'));truth(Grade.meets(f.evaluation,'merit'));eq(Grade.meets(f.evaluation,'distinction'),false);d.modules[8].assessments[0].score=null;eq(Grade.forecast(d.modules,70).status,'projected');eq(Grade.meets(Grade.evaluate(d.modules),'pass'),false);});
  check('Missing assumptions and invalid weights block appropriate estimates',()=>{const d=Grade.defaults();eq(Grade.forecast(d.modules,null).status,'assumption');eq(Grade.estimateModule(d.modules,d.modules[0].id,'merit',null).status,'assumption');d.modules[0].assessments[0].weight=85;eq(Grade.estimateModule(d.modules,d.modules[8].id,'pass',70).status,'invalid');});
  check('Raw-mark denominators are respected in forecasts',()=>{const d=full(),m=d.modules[0],a=m.assessments[0];a.max=40;a.score=26;const r=Grade.moduleResult(m);eq(r.parts[0].percent,6500);eq(r.mark,6500);a.score=null;const e=Grade.estimateModule(d.modules,m.id,'distinction',70);eq(e.percentage,5795);eq(Grade.percent(40*e.percentage/10000,40),5795);});
  check('Changing fixed assessment denominators and weights recalculates required marks',()=>{const d=full(),m=d.modules[0];m.assessments[0].score=null;const initial=Grade.estimateModule(d.modules,m.id,'distinction',70).percentage;m.assessments[1].max=200;const changedMax=Grade.estimateModule(d.modules,m.id,'distinction',70).percentage;truth(changedMax>initial);m.assessments.forEach(a=>a.weight=50);const changedWeights=Grade.estimateModule(d.modules,m.id,'distinction',70).percentage;truth(changedWeights>changedMax);});
  check('Forecast settings persist and invalid target names are rejected',()=>{const d=full();d.forecast={target:'merit',assumption:63};const restored=Grade.assertDocument(JSON.parse(JSON.stringify(d)));eq(restored.forecast.target,'merit');eq(restored.forecast.assumption,63);d.forecast.target='toString';let rejected=false;try{Grade.assertDocument(d);}catch(e){rejected=true;}truth(rejected);});
  check('Custom categories and exam roles survive JSON round-trip',()=>{const d=full(),c=Grade.addCategory(d,'Written test',true),a=d.modules[0].assessments[0];a.type=c.name;a.isExam=c.isExam;const restored=Grade.assertDocument(JSON.parse(JSON.stringify(d)));eq(restored.categories.find(x=>x.name==='Written test').isExam,true);eq(restored.modules[0].assessments[0].type,'Written test');eq(Grade.estimateModule(restored.modules,restored.modules[0].id,'distinction',70).percentage,5795);});
  check('Renaming Exam preserves completed-exam estimates and custom labels',()=>{const d=full(),c=d.categories.find(c=>c.name==='Exam'),a=d.modules[0].assessments[0];a.label='Paper 1';Grade.updateCategory(d,c.id,'Final test',true);eq(a.type,'Final test');eq(a.label,'Paper 1');eq(d.modules[1].assessments[0].label,'Final test');eq(a.score,65);eq(a.weight,86);eq(Grade.estimateModule(d.modules,d.modules[0].id,'distinction',70).percentage,5795);});
  check('Removing a used category requires reassignment without losing assessments',()=>{const d=full(),c=d.categories.find(c=>c.name==='Group activity'),to=d.categories.find(c=>c.name==='Coursework'),before=JSON.stringify(d);let rejected=false;try{Grade.removeCategory(d,c.id);}catch(e){rejected=true;}truth(rejected);eq(JSON.stringify(d),before);const count=d.modules.flatMap(m=>m.assessments).length;Grade.removeCategory(d,c.id,to.id);eq(d.modules.flatMap(m=>m.assessments).length,count);truth(!d.categories.some(x=>x.id===c.id));truth(!d.modules.some(m=>m.assessments.some(a=>a.type==='Group activity')));eq(Grade.evaluate(d.modules).mark,7000);Grade.assertDocument(d);});
  check('Duplicate or blank category names are rejected',()=>{const d=full(),before=JSON.stringify(d);for(const name of ['  ',' exam ']){let rejected=false;try{Grade.addCategory(d,name);}catch(e){rejected=true;}truth(rejected);}eq(JSON.stringify(d),before);});
  check('Legacy Other categories migrate without losing scores',()=>{const d=full();delete d.categories;const a=d.modules[0].assessments[1];a.type='Other';a.label='Other';const restored=Grade.assertDocument(JSON.parse(JSON.stringify(d)));eq(restored.modules[0].assessments[1].type,'Custom assessment');eq(restored.modules[0].assessments[1].score,65);truth(restored.categories.some(c=>c.name==='Custom assessment'));truth(!restored.categories.some(c=>c.name==='Other'));eq(Grade.evaluate(restored.modules).mark,7000);});
  check('Legacy defaults and empty category libraries remain valid',()=>{const d=full();delete d.categories;const restored=Grade.assertDocument(d);eq(restored.categories.length,5);truth(restored.modules[0].assessments[0].isExam);const empty={version:1,categories:[],modules:[]};eq(Grade.assertDocument(empty).categories.length,0);});
  check('Unknown category references and duplicate library names are rejected',()=>{const d=full();d.categories[1].name='Exam';let rejected=false;try{Grade.assertDocument(d);}catch(e){rejected=true;}truth(rejected);const other=full();other.modules[0].assessments[0].type='Missing';rejected=false;try{Grade.assertDocument(other);}catch(e){rejected=true;}truth(rejected);});
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

            ui_check('UI: retired automatic-mark controls are absent', "!document.querySelector('[data-action=vary]') && !document.getElementById('apply') && !document.getElementById('target') && !document.querySelector('#assessment-map button')")
            ui_check('UI: initial nine modules render', "document.querySelectorAll('.module').length===9 && document.getElementById('classification').textContent==='Incomplete'")
            ui_check('UI: default categories are manageable and Other is absent', "document.querySelectorAll('.category-row').length===5 && ![...document.querySelector('.assessment-type').options].some(o=>o.value==='Other')")
            ui_check('UI: add and rename a custom category updates dropdowns and labels', r"""(() => {document.getElementById('category-manager').open=true;document.getElementById('new-category-name').value='Lab report';document.getElementById('category-add-form').requestSubmit();if(![...document.querySelector('.assessment-type').options].some(o=>o.value==='Lab report'))return false;const type=document.querySelector('.assessment-type');type.value='Lab report';type.dispatchEvent(new Event('input',{bubbles:true}));const row=[...document.querySelectorAll('.category-row')].find(row=>row.querySelector('[data-category-name]').value==='Lab report');row.querySelector('[data-category-name]').value='Presentation';row.querySelector('[data-category-action=save]').click();return document.querySelector('.assessment-type').value==='Presentation' && document.querySelector('[data-field=label]').value==='Presentation' && document.querySelector('[data-field=weight]').value==='86' && document.querySelector('.category-chip').textContent.includes('Presentation');})()""")
            ui_check('UI: used category deletion reassigns assessments and supports undo', r"""(() => {const row=()=>[...document.querySelectorAll('.category-row')].find(row=>row.querySelector('[data-category-name]').value==='Presentation');row().querySelector('[data-category-action=remove]').click();if(document.getElementById('category-reassign').hidden)return false;document.getElementById('confirm-category-remove').click();if(document.querySelector('.assessment-type').value!=='Presentation')return false;const choose=()=>{const replacement=document.getElementById('category-replacement');replacement.value=[...replacement.options].find(o=>o.textContent==='Exam').value;document.getElementById('confirm-category-remove').click();};choose();if(document.querySelector('.assessment-type').value!=='Exam')return false;document.getElementById('undo').click();if(document.querySelector('.assessment-type').value!=='Presentation')return false;row().querySelector('[data-category-action=remove]').click();choose();return document.querySelector('.assessment-type').value==='Exam' && document.querySelector('[data-field=weight]').value==='86' && document.querySelectorAll('tbody tr').length===17 && document.querySelectorAll('.category-row').length===5;})()""")
            ui_check('UI: unused categories can be removed directly', r"""(() => {document.getElementById('new-category-name').value='Unused category';document.getElementById('category-add-form').requestSubmit();const row=[...document.querySelectorAll('.category-row')].find(row=>row.querySelector('[data-category-name]').value==='Unused category');row.querySelector('[data-category-action=remove]').click();return document.querySelectorAll('.category-row').length===5 && document.getElementById('category-reassign').hidden;})()""")
            ui_check('UI: automatic independent forecasts render without writing marks', "document.getElementById('degree-target').value==='distinction' && document.querySelector('.map-module .estimate').textContent.includes('51.94%') && document.querySelector('.map-module:last-child .estimate').textContent.includes('65.49%') && document.querySelector('[data-field=score]').value==='' && document.querySelectorAll('.rank-badge.met').length===3 && document.getElementById('forecast-status').textContent.includes('Projected')")
            ui_check('UI: target and other-module assumption update estimates live', r"""(() => {const target=document.getElementById('degree-target'),assumption=document.getElementById('other-assumption');target.value='pass';target.dispatchEvent(new Event('change'));if(!document.querySelector('.map-module .estimate').textContent.includes('40.00%'))return false;target.value='distinction';target.dispatchEvent(new Event('change'));assumption.value='60';assumption.dispatchEvent(new Event('input'));if(!document.querySelector('.map-module .estimate').textContent.includes('not achievable') || !document.querySelector('.map-module:last-child .estimate').textContent.includes('88.49%'))return false;assumption.value='70';assumption.dispatchEvent(new Event('input'));return document.querySelector('.map-module .estimate').textContent.includes('51.94%');})()""")
            ui_check('UI: assessment map shows all modules and categories without internal scrolling', "document.querySelectorAll('.map-module').length===9 && document.querySelectorAll('.category-chip').length===17 && getComputedStyle(document.getElementById('assessment-map')).overflowY!=='auto' && getComputedStyle(document.getElementById('overview-message')).maxHeight==='none'")
            ui_check('UI: typing preserves focus and updates mark', r"""(() => {const input=document.querySelector('[data-field="score"]');input.focus();input.value='80';input.dispatchEvent(new Event('input',{bubbles:true}));return document.activeElement===input && document.querySelector('.assessment-result').textContent.includes('80.00%');})()""")
            ui_check('UI: entered marks appear in the map', "document.querySelector('.category-chip').classList.contains('entered') && document.querySelector('.category-chip').textContent.includes('80.00%')")
            ui_check('UI: storage captures entered mark', "JSON.parse(localStorage.getItem('ucl-grade-calculator-v1')).modules[0].assessments[0].score===80")
            js("document.getElementById('degree-target').value='merit';document.getElementById('degree-target').dispatchEvent(new Event('change'));document.getElementById('other-assumption').value='63';document.getElementById('other-assumption').dispatchEvent(new Event('input'))")
            js("document.getElementById('new-category-name').value='Saved category';document.getElementById('category-add-form').requestSubmit()")
            command('Page.reload')
            wait_ready()
            ui_check('UI: file autosave restores on reload', "document.querySelector('[data-field=score]').value==='80'")
            ui_check('UI: target and assumption survive reload', "document.getElementById('degree-target').value==='merit' && document.getElementById('other-assumption').value==='63'")
            ui_check('UI: custom categories survive reload', "[...document.querySelector('.assessment-type').options].some(o=>o.value==='Saved category') && document.querySelectorAll('.category-row').length===6")
            ui_check('UI: bulk deletion and undo restore module', r"""(() => {document.querySelector('[data-action="select-module"]').click();document.getElementById('delete-selected').click();if(document.querySelectorAll('.module').length!==8)return false;document.getElementById('undo').click();return document.querySelectorAll('.module').length===9 && document.querySelector('[data-field=score]').value==='80';})()""")
            ui_check('UI: adding and deleting assessment', r"""(() => {const count=document.querySelectorAll('tbody tr').length;document.querySelector('[data-action="add-assessment"]').click();if(document.querySelectorAll('tbody tr').length!==count+1)return false;document.querySelector('.module tbody tr:last-child [data-action="delete-assessment"]').click();return document.querySelectorAll('tbody tr').length===count;})()""")
            ui_check('UI: single module deletion and undo', r"""(() => {document.querySelector('[data-action="delete-module"]').click();if(document.querySelectorAll('.module').length!==8)return false;document.getElementById('undo').click();return document.querySelectorAll('.module').length===9;})()""")
            ui_check('UI: mixed module and assessment bulk deletion', r"""(() => {const n=document.querySelectorAll('tbody tr').length;document.querySelector('[data-action="select-module"]').click();document.querySelectorAll('.module')[1].querySelector('[data-action="select-assessment"]').click();document.getElementById('delete-selected').click();if(document.querySelectorAll('.module').length!==8 || document.querySelectorAll('tbody tr').length!==n-3)return false;document.getElementById('undo').click();return document.querySelectorAll('.module').length===9 && document.querySelectorAll('tbody tr').length===n;})()""")
            ui_check('UI: add module with editable default assessment', "(() => {document.getElementById('add-module').click();const ok=document.querySelectorAll('.module').length===10 && document.querySelector('.module:last-child [data-field=weight]').value==='100';document.querySelector('.module:last-child [data-action=delete-module]').click();return ok && document.querySelectorAll('.module').length===9;})()")
            ui_check('UI: text labels render safely', r"""(() => {const input=document.querySelector('[data-field="name"]');input.value='<img src=x onerror=alert(1)>';input.dispatchEvent(new Event('input',{bubbles:true}));return document.querySelector('[data-field="name"]').value==='<img src=x onerror=alert(1)>' && !document.querySelector('img');})()""")
            js("localStorage.setItem('ucl-grade-calculator-v1',JSON.stringify((()=>{const d=Grade.defaults();d.modules.forEach(m=>m.assessments.forEach(a=>a.score=m.kind==='project'?80:65));return d;})()))")
            command('Page.reload')
            wait_ready()
            ui_check('UI: completed exam what-if shows required and entered scores without changing inputs', "document.querySelector('.map-module .estimate').textContent.includes('Exam needed: 57.95%') && document.querySelector('.map-module .estimate').textContent.includes('Entered 65.00%') && document.querySelector('[data-field=score]').value==='65'")
            ui_check('UI: manual project edit updates overall grade', r"""(() => {if(document.getElementById('overall').textContent!=='70.00%')return false;const score=document.querySelector('.module:last-child [data-field="score"]');score.value='60';score.dispatchEvent(new Event('input',{bubbles:true}));return document.getElementById('overall').textContent==='63.33%' && document.querySelector('.map-module:last-child').textContent.includes('60.00%');})()""")
            ui_check('UI: lower MSc levels met are shown even when the selected higher target is unreachable', "document.querySelector('.map-module .estimate').textContent.includes('not achievable') && document.querySelector('.map-module:last-child .estimate').textContent.includes('Project needed:') && document.querySelector('[data-rank=pass]').dataset.met==='true' && document.querySelector('[data-rank=merit]').dataset.met==='true' && document.querySelector('[data-rank=distinction]').dataset.met==='false' && !document.getElementById('forecast-status').textContent.includes('Projected')")
            ui_check('UI: overview identifies weight totals above and below 100 and clears corrected warnings', r"""(() => {const input=document.querySelector('[data-field="weight"]');const set=value=>{input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));};for(const [value,total,direction] of [['85','99.00%','below'],['96','110.00%','over'],['120','134.00%','over']]){set(value);const warning=document.querySelector('.map-module .weight-warning');if(!warning || !warning.textContent.includes(total) || !warning.textContent.includes(direction+' 100%') || document.querySelectorAll('.has-weight-warning').length!==1 || document.getElementById('overall').textContent!=='—')return false;}set('86');if(document.querySelector('.weight-warning'))return false;set('85');return document.getElementById('classification').textContent==='Invalid inputs';})()""")
            ui_check('UI: separate-pass requirement still updates live', r"""(() => {const module=document.querySelectorAll('.module')[3];const rows=module.querySelectorAll('tbody tr');for(const [row,value] of [[rows[0],'40'],[rows[1],'60']]){const score=row.querySelector('[data-field=score]');score.value=value;score.dispatchEvent(new Event('input',{bubbles:true}));}const requirement=rows[0].querySelector('[data-field=requirement]');requirement.value='must';requirement.dispatchEvent(new Event('input',{bubbles:true}));return module.querySelector('.module-result').textContent.includes('Separate-pass requirement unmet') && !rows[0].querySelector('.minimum').hidden;})()""")
            # Test export and import using real browser file I/O in the isolated profile.
            js("document.getElementById('new-category-name').value='Exported category';document.getElementById('new-category-exam').checked=true;document.getElementById('category-add-form').requestSubmit();const type=document.querySelector('.assessment-type');type.value='Exported category';type.dispatchEvent(new Event('input',{bubbles:true}))")
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
            checks.append({'name': 'UI: JSON export includes custom categories and exam roles', 'ok': any(c['name'] == 'Exported category' and c['isExam'] for c in backup['categories']) and backup['modules'][0]['assessments'][0]['type'] == 'Exported category'})
            backup['modules'][0]['name'] = 'Imported scenario'
            import_path = Path(temp) / 'import.json'
            import_path.write_text(json.dumps(backup), encoding='utf-8')
            js('window.confirm=()=>true')
            import_file(import_path)
            wait_js("document.getElementById('feedback').textContent==='Scenario imported.'")
            ui_check('UI: valid JSON import restores structure and data', "document.querySelector('[data-field=name]').value==='Imported scenario' && document.querySelectorAll('.module').length===9")
            ui_check('UI: JSON import restores a custom exam category without losing marks', "document.querySelector('.assessment-type').value==='Exported category' && document.querySelector('[data-field=score]').value==='65' && JSON.parse(localStorage.getItem('ucl-grade-calculator-v1')).modules[0].assessments[0].isExam===true")
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
            js("document.getElementById('category-manager').open=true;document.getElementById('category-manager').scrollIntoView({block:'start'});new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
            screenshot = command('Page.captureScreenshot', {'format': 'png'})
            (ROOT / 'tests' / 'preview-categories.png').write_bytes(base64.b64decode(screenshot['data']))
            command('Emulation.setDeviceMetricsOverride', {'width': 390, 'height': 844, 'deviceScaleFactor': 1, 'mobile': True})
            command('Emulation.setPageScaleFactor', {'pageScaleFactor': 1})
            js('window.scrollTo(0,0); new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            ui_check('UI: narrow layout has no page overflow', "window.innerWidth===390 && document.documentElement.scrollWidth<=390 || {innerWidth:window.innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('main,main>*,.module-head,.module-result,.module-footer')].filter(e=>e.getBoundingClientRect().right>390).map(e=>({tag:e.tagName,cls:e.className,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))}")
            ui_check('UI: category manager remains usable on a narrow screen', "document.getElementById('category-manager').open && document.getElementById('new-category-name').getBoundingClientRect().width<=390 && document.querySelector('.category-row').getBoundingClientRect().right<=390")
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
