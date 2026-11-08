// SPDX-License-Identifier: MPL-2.0
// Isolated diagnostic; no personal profile or external website is opened.
import {spawn} from 'node:child_process';
import {mkdtemp,writeFile,mkdir,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import http from 'node:http';
import net from 'node:net';
const [binary,backend='wayland',style='chrome',output='/tmp/angle-cef-sample.json']=process.argv.slice(2);
if(!binary||!['wayland','x11'].includes(backend)||!['chrome','alloy'].includes(style))throw Error('binary backend style output required');
const root=await mkdtemp(path.join(tmpdir(),'angle-cef-'));
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Angle engine fixture</title><h1>Owned localhost fixture</h1>')});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const free=net.createServer();await new Promise(resolve=>free.listen(0,'127.0.0.1',resolve));const port=free.address().port;await new Promise(resolve=>free.close(resolve));
const args=[`--probe-root=${root}/profile`,'--single-profile',`--ozone-platform=${backend}`,`--remote-debugging-port=${port}`,`--user-data-dir=${root}/profile`,`--url=http://localhost:${server.address().port}/`,`--load-extension=${path.resolve('tests/extensions/content-probe')},${path.resolve('tests/extensions/popup-probe')}`];
if(style==='alloy')args.push('--use-alloy-style');
const env={...process.env,XDG_CONFIG_HOME:root+'/config',XDG_CACHE_HOME:root+'/cache',XDG_DATA_HOME:root+'/data'};
if(backend==='wayland')delete env.DISPLAY;else delete env.WAYLAND_DISPLAY;
const child=spawn(path.resolve(binary),args,{env,cwd:path.dirname(path.resolve(binary)),stdio:['ignore','pipe','pipe']});
let logs='';child.stdout.on('data',b=>logs+=b);child.stderr.on('data',b=>logs+=b);
let socket;let seq=0;const pending=new Map();
const result={backend,style,args,temporary_profile:root,checks:{render:'not_run',content_script:'not_run',sandbox:'not_run'},status:'failed'};
try{
 let targets;
 for(let i=0;i<80;i++){
  try{targets=await(await fetch(`http://127.0.0.1:${port}/json/list`,{signal:AbortSignal.timeout(1000)})).json();if(targets.some(t=>t.type==='page'))break}catch{}
  if(child.exitCode!==null)throw Error('CEF exited '+child.exitCode);
  await new Promise(r=>setTimeout(r,250));
 }
 const target=targets?.find(t=>t.type==='page'&&t.url.startsWith('http://localhost'));
 if(!target)throw Error('No fixture page DevTools target');
 socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
 socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
 async function call(method,params={}){const id=++seq;return Promise.race([new Promise(resolve=>{pending.set(id,resolve);socket.send(JSON.stringify({id,method,params}))}),new Promise((_,reject)=>setTimeout(()=>reject(Error('CDP timeout')),5000))])}
 await new Promise(r=>setTimeout(r,1500));
 result.page=await call('Runtime.evaluate',{expression:'JSON.stringify({title:document.title,marker:document.documentElement.dataset.arcReverseProbe})',returnByValue:true});
 const page=JSON.parse(result.page.result.result.value);
 result.checks.render=page.title==='Angle engine fixture'?'pass':'fail';result.checks.content_script=page.marker==='active'?'pass':'fail';
 await call('Page.navigate',{url:'chrome://sandbox/'});await new Promise(r=>setTimeout(r,700));
 result.sandbox_page=await call('Runtime.evaluate',{expression:'document.body.innerText',returnByValue:true});
 const sandbox=result.sandbox_page.result?.result?.value||'';
 result.checks.sandbox=sandbox.includes('PID namespaces\tYes')&&sandbox.includes('Seccomp-BPF sandbox\tYes')?'pass':'fail';
 result.targets=targets.map(({type,url})=>({type,url}));result.status='observed';
}catch(e){result.error=String(e)}finally{
 if(socket)socket.close();child.kill('SIGTERM');await new Promise(resolve=>{if(child.exitCode!==null)resolve();else{const timer=setTimeout(()=>{child.kill('SIGKILL');resolve()},3000);child.once('exit',()=>{clearTimeout(timer);resolve()})}});server.close();
 result.exit={code:child.exitCode,signal:child.signalCode};result.logs=logs;
 await writeFile(output,JSON.stringify(result,null,2));console.log(JSON.stringify({output,status:result.status,checks:result.checks,error:result.error}));
}
