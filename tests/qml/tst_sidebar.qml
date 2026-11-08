// SPDX-License-Identifier: MPL-2.0
import QtQuick
import QtTest
import QtWebEngine
import "../../app" as App
Item {
 width:1280;height:800
 QtObject {
  id:workspace
  property var spaces: [{id:"space",title:"Test"}]
  property var profiles: [{id:"profile",title:"Test"}]
  property var items: [{id:"fav",kind:"favorite",profile:"profile",title:"Favorite",url:"",savedUrl:"https://example.test/saved"}]
  property var sidebarItems: []
  property string currentSpace: "space"
  property string currentProfile: "profile"
  property string selected: ""
  property string error: ""
  signal changed()
  signal pageClosed(string id)
  function select(id) { selectedId=id }
  property string selectedId: ""
 }
 WebEngineProfile {id:testProfile;offTheRecord:true}
 QtObject {id:fakePage; property url url:"https://example.test/current";property string title:"Favorite";property bool lastLoadSuccess:false}
 QtObject {
  id:browserProfiles
  property bool extensionsAvailable:false
  property var extensions:[]
  function get(id) {return testProfile}
 }
 App.Main {id:app}
 TestCase {
  name:"SidebarDrag"
  when:windowShown && app.visible
  function visualChild(item,name) {
   if(item.objectName===name)return item
   for(let child of item.children||[]) {
    let result=visualChild(child,name)
    if(result)return result
   }
   return null
  }
  function test_resize_hide_reveal() {
   wait(100)
   failOnWarning(/.*TypeError.*/)
   let handle=visualChild(app.contentItem,"sidebarResizeHandle")
   verify(handle!==null)
   let oldWidth=app.sidebarWidth
   mousePress(handle,3,handle.height/2,Qt.LeftButton)
   mouseMove(handle,43,handle.height/2,30)
   mouseRelease(handle,3,handle.height/2,Qt.LeftButton)
   verify(app.sidebarWidth>oldWidth)
   verify(app.sidebarShown)
   // The handle moves with the sidebar; use a delta relative to its new origin.
   let retained=app.sidebarWidth
   mousePress(handle,3,handle.height/2,Qt.LeftButton)
   mouseMove(handle,-250,handle.height/2,30)
   mouseRelease(handle,3,handle.height/2,Qt.LeftButton)
   compare(app.sidebarShown,false)
   keyClick(Qt.Key_S,Qt.ControlModifier)
   tryCompare(app,"sidebarShown",true)
   compare(app.sidebarWidth,retained)
  }
 }
}
