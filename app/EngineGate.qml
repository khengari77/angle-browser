// SPDX-License-Identifier: MPL-2.0
import QtQuick
import QtWebEngine
Window {
 width:800;height:600;visible:true
 property int priorCount:-1
 property bool popupRequested:false
 property int step:0
 onStepChanged:console.log("ENGINE_GATE_STEP",step)
 property bool busy:false
 property bool oneLoaded:false
 property bool twoLoaded:false
 function fail(message){console.error("ENGINE_GATE_FAIL: "+message);Qt.exit(3)}
 function js(view,code,callback){busy=true;view.runJavaScript(code,function(result){busy=false;callback(result)})}
 WebEngineView {id:one;width:400;height:600;profile:browserProfiles.get(workspace.currentProfile);url:gateUrl;onLoadingChanged:info=>{oneLoaded=info.status===WebEngineView.LoadSucceededStatus}}
 WebEngineView {id:two;x:400;width:400;height:600;profile:browserProfiles.get("isolation-probe");url:gateUrl;onLoadingChanged:info=>{twoLoaded=info.status===WebEngineView.LoadSucceededStatus}}
 WebEngineView {id:popup;visible:false;width:300;height:300;profile:browserProfiles.get(workspace.currentProfile);property bool loaded:false;onLoadingChanged:info=>{loaded=info.status===WebEngineView.LoadSucceededStatus}}
 Timer {interval:250;running:true;repeat:true;onTriggered:{
  if(busy||!oneLoaded||!twoLoaded)return
  if(step===0){step=1;js(one,"JSON.stringify({stored:localStorage.getItem('arcreversePersistent'),cookie:document.cookie})",value=>{let state=JSON.parse(value);if(gateRestore&&(state.stored!=="retained"||!state.cookie.includes('arcreverse_cookie=retained')))fail("storage did not survive restart");else js(one,"localStorage.setItem('arcreversePersistent','retained');document.cookie='arcreverse_cookie=retained; Max-Age=3600; SameSite=Lax; Path=/'; true",()=>{})})}
  else if(step===1){step=2;js(two,"JSON.stringify({stored:localStorage.getItem('arcreversePersistent'),cookie:document.cookie})",value=>{let state=JSON.parse(value);if(state.stored||state.cookie.includes('arcreverse_cookie=retained'))fail("profile storage leaked")})}
  else if(step===2){step=3;if(!gateRestore){browserProfiles.install(Qt.resolvedUrl(probeRoot+"content-probe"))}}
  else if(step===3){let probes=browserProfiles.extensions.filter(e=>e.name.startsWith("ArcReverse"));if(!gateRestore&&probes.length===1&&!popupRequested){popupRequested=true;browserProfiles.install(Qt.resolvedUrl(probeRoot+"popup-probe"));return}if(probes.length!==2)return;if(gateRestore&&probes.some(e=>!e.enabled)){fail("extension enable state was not restored");return}if(!gateRestore)for(let e of probes){console.log("ENGINE_GATE_ENABLE",e.name,e.id);browserProfiles.enable(e.id,true);console.log("ENGINE_GATE_ENABLED",e.name)}step=4;oneLoaded=false;one.reload()}
  else if(step===4){js(one,"document.documentElement.dataset.arcReverseProbe",value=>{if(value==="active")step=5})}
  else if(step===5){step=6;js(two,"document.documentElement.dataset.arcReverseProbe",value=>{if(value==="active")fail("extension leaked to another profile")});let e=browserProfiles.extensions.find(e=>e.name==="ArcReverse Popup Probe");popup.url=e.popup}
  else if(step===6&&popup.loaded){js(popup,"document.querySelector('#value').textContent",value=>{if(value==="")return;priorCount=Number(value);if(gateRestore&&priorCount<1){fail("extension storage did not persist");return}step=7;js(popup,"document.querySelector('#count').click(); true",()=>{})})}
  else if(step===7){js(popup,"document.querySelector('#value').textContent",value=>{if(Number(value)>priorCount){step=8;console.log("ENGINE_GATE_PASS rendering profiles MV3 content popup storage");Qt.exit(0)}})}
 }}
 Timer {interval:45000;running:true;onTriggered:fail("timeout at step "+step)}
}
