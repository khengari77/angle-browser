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
  name:"FavoriteContextMenu"
  when:windowShown && app.visible
  function initTestCase() {wait(100)}
  function visualChild(item,name) {
   if (item.objectName===name) return item
   for(let child of item.children||[]) {
    let result=visualChild(child,name)
    if(result) return result
   }
   return null
  }
  function test_rightClickAndLeftClick() {
   failOnWarning(/.*TypeError.*/)
   let tile=visualChild(app.contentItem,"favoriteTile-fav")
   verify(tile!==null)
   mouseClick(tile,tile.width/2,tile.height/2,Qt.LeftButton)
   compare(workspace.selectedId,"fav")
   mouseClick(tile,tile.width/2,tile.height/2,Qt.RightButton)
   let menu=findChild(app,"itemMenu")
   tryCompare(menu,"opened",true)
   compare(menu.item.id,"fav")
   verify(findChild(app,"restorePinnedUrlAction").visible)
   verify(findChild(app,"editPinnedUrlAction").visible)
   let edit=findChild(app,"editPinnedUrlAction")
   mouseClick(edit,edit.width/2,edit.height/2,Qt.LeftButton)
   let dialog=findChild(app,"pinnedUrlDialog")
   tryCompare(dialog,"opened",true)
   compare(dialog.itemId,"fav")
   dialog.close()
   app.pages={"fav":fakePage}
   mouseClick(tile,tile.width/2,tile.height/2,Qt.RightButton)
   tryCompare(menu,"opened",true)
   let restore=findChild(app,"restorePinnedUrlAction")
   mouseClick(restore,restore.width/2,restore.height/2,Qt.LeftButton)
   compare(fakePage.url.toString(),"https://example.test/saved")
   menu.close()
  }
 }
}
