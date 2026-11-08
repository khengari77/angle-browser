// SPDX-License-Identifier: MPL-2.0
import {spawn} from 'node:child_process';
import {mkdtemp,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
const [binary,backend,style,output]=process.argv.slice(2);
if(!binary||!['wayland','x11'].includes(backend)||!['chrome','alloy'].includes(style)||!output)throw Error('binary backend style output');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Angle CEF fixture</title><h1>Owned fixture</h1>')});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const url=`http://localhost:${server.address().port}/`;
async function freePort(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p}
async function connect(wsUrl){
 const ws=new WebSocket(wsUrl);await Promise.race([new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject}),wait(5000).then(()=>{throw Error('websocket timeout')})]);
 let seq=0;const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
 return {close:()=>ws.close(),async call(method,params={}){const id=++seq;let timer;try{const m=await Promise.race([new Promise(resolve=>{pending.set(id,resolve);ws.send(JSON.stringify({id,method,params}))}),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(method+' timeout')),5000)})]);if(m.error)throw Error(JSON.stringify(m.error));return m.result}finally{clearTimeout(timer);pending.delete(id)}},async eval(expression){const r=await this.call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true,userGesture:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}};
}
const result={format:'angle-cef-gate-v1',backend,style,profile_architecture:'isolated-process-per-profile',extension_restore:'probe-owned enabled-path registry',requested_repeats:3,cycles:[],qualification:'not_qualified',environment:{native_xorg_tested:false},remaining:['Qt embedding','compositor input/DPI checks']};
try{
 for(let repeat=0;repeat<3;repeat++){
  const root=await mkdtemp(path.join(tmpdir(),'angle-cef-gate-'));
  for(let phase=0;phase<2;phase++){
   const port=await freePort();const portB=await freePort();const runtime=process.env.ANGLE_CEF_RUNTIME||path.dirname(path.resolve(binary));const args=[`--probe-root=${root}/a`,'--single-profile','--persist-extension-config',`--ozone-platform=${backend}`,`--remote-debugging-port=${port}`,`--url=${url}`,`--resources-dir-path=${runtime}`,`--locales-dir-path=${runtime}/locales`];
   if(!phase)args.push(`--load-extension=${path.resolve('tests/extensions/content-probe')},${path.resolve('tests/extensions/popup-probe')}`);
   if(style==='alloy')args.push('--use-alloy-style');else args.push('--native-window');
   const env={...process.env,XDG_DATA_HOME:root+'/data',XDG_CONFIG_HOME:root+'/config',XDG_CACHE_HOME:root+'/cache'};
   if(backend==='wayland')delete env.DISPLAY;else delete env.WAYLAND_DISPLAY;
   const child=spawn(path.resolve(binary),args,{env,stdio:['ignore','pipe','pipe']});
   const argsB=args.filter(x=>!x.startsWith('--load-extension=')).map(x=>x.startsWith('--probe-root=')?`--probe-root=${root}/b`:x.startsWith('--remote-debugging-port=')?`--remote-debugging-port=${portB}`:x);
   const childB=spawn(path.resolve(binary),argsB,{env,stdio:['ignore','pipe','pipe']});
   const record={repeat,phase,args,argsB,checks:Object.fromEntries(['two_profiles_render','fixture_load','content_script','extension_isolation','storage_isolation','storage_restart','extension_worker','action_popup','extension_storage_restart','popup_storage','sandbox','clean_shutdown'].map(name=>[name,'not_run'])),logs:'',status:'failed'};result.cycles.push(record);
   for(const proc of [child,childB]){proc.stdout.on('data',b=>record.logs+=b);proc.stderr.on('data',b=>record.logs+=b);proc.on('error',e=>record.logs+=String(e));}let connections=[];
   const check=(name,ok)=>{record.checks[name]=ok?'pass':'fail';if(!ok)throw Error(name+' failed')};
   const list=async()=>{let targets=[];for(const [profile,endpoint] of [["a",port],["b",portB]])targets.push(...(await(await fetch(`http://127.0.0.1:${endpoint}/json/list`,{signal:AbortSignal.timeout(5000)})).json()).map(t=>({...t,probe_profile:profile})));return targets};
   try{
    let pages=[],lastTargets=[];const deadline=Date.now()+45000;
    for(let i=0;i<100&&Date.now()<deadline;i++){try{const targets=await list();lastTargets=targets;pages=['a','b'].map(profile=>targets.find(x=>x.probe_profile===profile&&x.type==='page'&&x.url===url)).filter(Boolean);if(pages.length===2)break}catch{}if([child,childB].some(p=>p.exitCode!==null||p.signalCode))throw Error('premature browser process exit');await wait(250)}
    record.targets=lastTargets;
    check('two_profiles_render',pages.length===2);
    const a=await connect(pages[0].webSocketDebuggerUrl),b=await connect(pages[1].webSocketDebuggerUrl);connections.push(a,b);
    const loadDeadline=Date.now()+15000;
    let loaded=false;
    while(Date.now()<loadDeadline) {
      record.fixture_titles=[await a.eval("document.title"),await b.eval("document.title")];
      loaded=record.fixture_titles.every(title=>title==='Angle CEF fixture');
      if(loaded)break;
      await wait(200);
    }
    check('fixture_load',loaded);
    await wait(500);
    const state=()=>`JSON.stringify({marker:document.documentElement.dataset.arcReverseProbe,local:localStorage.getItem('angle-test'),cookie:document.cookie})`;
    let sa=JSON.parse(await a.eval(state())),sb=JSON.parse(await b.eval(state()));
    // First-phase extension identifies global profile A. On restore use retained storage.
    let one=a,two=b;
    if((!phase&&sb.marker==='active')||(phase&&sb.local==='retained')){one=b;two=a;[sa,sb]=[sb,sa]}
    check('content_script',sa.marker==='active');check('extension_isolation',sb.marker===undefined);
    check('storage_isolation',sb.local===null&&!sb.cookie.includes('angle_cookie='));
    if(phase)check('storage_restart',sa.local==='retained'&&sa.cookie.includes('angle_cookie=retained'));
    await one.eval("localStorage.setItem('angle-test','retained');document.cookie='angle_cookie=retained;Max-Age=3600;SameSite=Lax;Path=/';true");
    await one.call('Page.bringToFront');
    let worker;
    for(let i=0;i<30;i++){worker=(await list()).find(t=>t.type==='service_worker'&&t.url.endsWith('/background.js'));if(worker)break;await wait(200)}
    check('extension_worker',!!worker);
    const w=await connect(worker.webSocketDebuggerUrl);connections.push(w);
    record.extension_windows=await w.eval('chrome.windows.getAll().then(windows=>windows.map(w=>({id:w.id,type:w.type,focused:w.focused})))');
    let windowId=record.extension_windows.find(w=>w.focused)?.id??record.extension_windows[0]?.id;
    if(windowId===undefined)throw Error('No extension-visible host window');
    await w.eval(`chrome.windows.update(${windowId},{focused:true}).then(()=>true)`);
    if(process.env.HYPRLAND_INSTANCE_SIGNATURE) {
      const focus=spawn('hyprctl',['dispatch','focuswindow',`pid:${child.pid}`],{stdio:'ignore'});
      record.compositor_focus=await new Promise(resolve=>{focus.once('error',e=>resolve(String(e)));focus.once('exit',code=>resolve(code));});
    }
    await wait(300);
    windowId=await w.eval('chrome.windows.getLastFocused().then(w=>w.id)');
    await w.eval(`chrome.action.openPopup({windowId:${windowId}}).then(()=>true)`);
    let popup;
    for(let i=0;i<30;i++){popup=(await list()).find(t=>t.type==='page'&&t.url.endsWith('/popup.html'));if(popup)break;await wait(100)}
    check('action_popup',!!popup);
    const p=await connect(popup.webSocketDebuggerUrl);connections.push(p);await wait(150);
    const before=Number(await p.eval("document.querySelector('#value').textContent"));
    if(phase)check('extension_storage_restart',before>=1);
    await p.eval("document.querySelector('#count').click();true");await wait(200);
    check('popup_storage',Number(await p.eval("document.querySelector('#value').textContent"))===before+1);
    await one.call('Page.navigate',{url:'chrome://sandbox/'});await wait(300);
    const sandbox=await one.eval('document.body.innerText');record.sandbox=sandbox;
    check('sandbox',sandbox.includes('PID namespaces\tYes')&&sandbox.includes('Seccomp-BPF sandbox\tYes'));
    record.status='passed';
    try{await one.call('Browser.close')}catch{}
    try{await two.call('Browser.close')}catch{}
   }catch(e){record.error=String(e)}finally{
    for(const c of connections)c.close();
    for(const proc of [child,childB]) {
     for(let i=0;i<30&&proc.exitCode===null&&!proc.signalCode;i++)await wait(100);
     if(proc.exitCode===null&&!proc.signalCode){proc.kill('SIGTERM');await wait(500)}
     if(proc.exitCode===null&&!proc.signalCode)proc.kill('SIGKILL');
    }
    record.exits=[child,childB].map(p=>({code:p.exitCode,signal:p.signalCode}));
    record.checks.clean_shutdown=[child,childB].every(p=>p.exitCode===0)?'pass':'fail';
    if(record.status==='passed'&&record.checks.clean_shutdown!=='pass'){record.status='failed';record.error='Unclean shutdown'}
   }
   await writeFile(output,JSON.stringify(result,null,2));
   console.log(JSON.stringify({repeat,phase,status:record.status,error:record.error}));
   if(record.status!=='passed')throw Error(record.error||'gate failed');
  }
 }
 result.qualification='standalone_pass';
}catch(e){result.error=String(e)}finally{server.close();await writeFile(output,JSON.stringify(result,null,2));console.log(JSON.stringify({output,qualification:result.qualification,error:result.error}));if(result.qualification!=='standalone_pass')process.exitCode=1;}
