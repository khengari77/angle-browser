// SPDX-License-Identifier: MPL-2.0
chrome.storage.local.get({visits:0}, state => { chrome.storage.local.set({visits:state.visits+1});document.documentElement.dataset.arcReverseProbe="active"; });
