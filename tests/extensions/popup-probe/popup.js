// SPDX-License-Identifier: MPL-2.0
function render(){chrome.storage.local.get({count:0},s=>document.querySelector('#value').textContent=s.count)}
document.querySelector('#count').onclick=()=>chrome.storage.local.get({count:0},s=>chrome.storage.local.set({count:s.count+1},render));render();
