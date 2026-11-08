// SPDX-License-Identifier: MPL-2.0
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtWebEngine
import QtCore
ApplicationWindow {
 id: root; width: 1280; height: 800; visible: true; title: "Angle — development prototype"
 Settings {id:appSettings;property bool dark:false}
 property bool dark:appSettings.dark
 color: dark ? "#29252e" : "#e8dedb"
 font.family: "Sans Serif"
 palette.button: dark ? "#403947" : "#f3ebe8"
 palette.buttonText: dark ? "#eee7f0" : "#302c31"
 palette.highlight: "#a185a8"
 property bool engineLoaded: active !== null && active.lastLoadSuccess
 property var pages: ({})
 property var active: null
 function activate(id) {
  if (!id) { active=null; return }
  if (!pages[id]) {
   let item=workspace.items.find(x => x.id===id)
   if (!item || item.kind==="folder") return
   let page=pageComponent.createObject(content, {tabId:id, profile:browserProfiles.get(item.profile), url:item.url})
   let next=Object.assign({},pages);next[id]=page;pages=next
  }
  active=pages[id]
 }
 Connections {
  target: workspace
  function onChanged() { root.activate(workspace.selected) }
  function onPageClosed(id) {if(root.pages[id]) {root.pages[id].destroy();let next=Object.assign({},root.pages);delete next[id];root.pages=next}}
 }
 Component.onCompleted: activate(workspace.selected)
 Shortcut {sequence:"Ctrl+T";onActivated:{command.replaceCurrent=false;command.open()}}
 Shortcut {sequence:"Ctrl+L";onActivated:{command.replaceCurrent=true;command.open()}}
 Shortcut {sequence:"Ctrl+S";onActivated:sidebar.visible=!sidebar.visible}
 Shortcut {sequence:"Ctrl+Tab";onActivated:{let tabs=workspace.items.filter(x=>x.kind!=="folder"&&x.profile===workspace.currentProfile&&(x.space===workspace.currentSpace||x.kind==="favorite"));if(tabs.length)workspace.select(tabs[(tabs.findIndex(x=>x.id===workspace.selected)+1)%tabs.length].id)}}
 Shortcut {sequence:"Ctrl+W";onActivated:workspace.close(workspace.selected)}
 Component {
  id: pageComponent
  WebEngineView {
   property string tabId
   property bool lastLoadSuccess: false
   anchors.fill: parent; visible: root.active===this
   onLoadingChanged: function(info) {if(info.status===WebEngineView.LoadSucceededStatus){lastLoadSuccess=true;workspace.navigate(tabId,url.toString(),title)}}
   onNewWindowRequested: function(request) {workspace.open(request.requestedUrl.toString())}
   onPermissionRequested: function(permission) {permissionDialog.permission=permission;permissionDialog.open()}
   onRenderProcessTerminated: {reloadDialog.open()}
  }
 }
 RowLayout {
  anchors.fill:parent; anchors.margins:8; spacing:8
  ColumnLayout {
   id:sidebar; Layout.minimumWidth:238; Layout.maximumWidth:238; Layout.preferredWidth:238;Layout.fillHeight:true;spacing:8
   RowLayout {
    ToolButton {text:"‹";onClicked:if(root.active)root.active.goBack()}
    ToolButton {text:"›";onClicked:if(root.active)root.active.goForward()}
    ToolButton {text:"↻";onClicked:if(root.active)root.active.reload()}
    Item {Layout.fillWidth:true}
    ToolButton {text:"☰";onClicked:settings.open()}
   }
   Button {text: root.active ? root.active.title.slice(0,28) : "Search or enter URL";Layout.fillWidth:true;onClicked:command.open()}
   Flow {
    Layout.fillWidth:true;spacing:6
    Repeater {
     model:workspace.items.filter(x=>x.kind==="favorite"&&x.profile===workspace.currentProfile)
     Button {required property var modelData;text:modelData.title.slice(0,2);width:52;height:48;onClicked:workspace.select(modelData.id)}
    }
   }
   ComboBox {id:spaceSelect;Layout.fillWidth:true;model:workspace.spaces;textRole:"title";valueRole:"id";currentIndex:workspace.spaces.findIndex(x=>x.id===workspace.currentSpace);onActivated:workspace.selectSpace(currentValue)}
   ScrollView {
    Layout.fillWidth:true;Layout.fillHeight:true;clip:true
    Column {
     width:sidebar.width;spacing:4
     Repeater {
      model:workspace.sidebarItems
      Rectangle {
       id:tabRow
       required property var modelData
       property string itemId: modelData.id
       width:sidebar.width;height:38;radius:8;color:workspace.selected===modelData.id?(root.dark?"#514759":"#fffcfa"):"transparent"
       RowLayout {
        anchors.fill:parent;anchors.margins:6;anchors.leftMargin:6+modelData.depth*12
        Label {text:modelData.kind==="folder"?"▸":modelData.kind==="pinned"?"◆":"○";color:"#6d6464"}
        Label {text:modelData.title;elide:Text.ElideRight;Layout.fillWidth:true;color:root.dark?"#eee7f0":"#302c31"}
        ToolButton {visible:modelData.kind!=="folder";text:"×";onClicked:workspace.close(modelData.id)}
       }
       Rectangle {id:dragProxy;width:24;height:24;opacity:0;Drag.active:rowMouse.drag.active;Drag.source:tabRow;Drag.keys:["workspace-item"]}
       MouseArea {id:rowMouse;anchors.fill:parent;anchors.rightMargin:36;acceptedButtons:Qt.LeftButton|Qt.RightButton;drag.target:dragProxy
        onPressed:mouse=>{dragProxy.x=mouse.x;dragProxy.y=mouse.y}
        onReleased:{dragProxy.Drag.drop();dragProxy.x=0;dragProxy.y=0}
        onClicked:mouse=>{if(mouse.button===Qt.RightButton){itemMenu.item=modelData;itemMenu.popup()}else if(modelData.kind==="folder")workspace.toggleFolder(modelData.id);else workspace.select(modelData.id)}
       }
       DropArea {anchors.fill:parent;keys:["workspace-item"];onDropped:drop=>{workspace.move(drop.source.itemId,modelData.kind==="folder"?modelData.id:modelData.parent,modelData.position);drop.acceptProposedAction()}}
      }
     }
     Button {text:"+ New tab";flat:true;onClicked:command.open()}
    }
   }
   Label {text:workspace.error;visible:text.length>0;wrapMode:Text.Wrap;Layout.fillWidth:true;color:"#962e30"}
   RowLayout {Button {text:"+ Space";onClicked:newSpace.open()} Button {text:"+ Folder";onClicked:workspace.addItem("folder","New Folder")}}
  }
  Rectangle {
   Layout.minimumWidth:300;Layout.fillWidth:true;Layout.fillHeight:true;color:root.dark?"#211e25":"#ffffff";radius:12;clip:true
   Item {id:content;anchors.fill:parent}
   Column {anchors.centerIn:parent;visible:!root.active;spacing:12
    Label {text:"Angle";font.pixelSize:34;color:"#534951"}
    Label {text:"Your space on the internet";color:"#91868c"}
    Button {text:"Open a page   Ctrl+T";onClicked:command.open()}
   }
  }
 }
 Popup {
  id:command;property bool replaceCurrent:false;anchors.centerIn:parent;width:600;padding:16;modal:true;focus:true;closePolicy:Popup.CloseOnEscape|Popup.CloseOnPressOutside
  onOpened:{entry.text=replaceCurrent&&root.active?root.active.url.toString():"";entry.forceActiveFocus();entry.selectAll()}
  ColumnLayout {anchors.fill:parent
   TextField {id:entry;Layout.fillWidth:true;placeholderText:"Search or enter a URL";onAccepted:{if(command.replaceCurrent&&root.active){let address=workspace.resolveInput(text);if(address)root.active.url=address}else workspace.open(text);command.close()}}
   Repeater {model:workspace.items.filter(x=>x.kind!=="folder"&&x.profile===workspace.currentProfile&&entry.text.length>0&&x.title.toLowerCase().includes(entry.text.toLowerCase())).slice(0,6)
    Button {required property var modelData;text:modelData.title;Layout.fillWidth:true;onClicked:{if(modelData.space)workspace.selectSpace(modelData.space);workspace.select(modelData.id);command.close()}}
   }
  }
 }
 Menu {id:itemMenu;property var item
  MenuItem {text:"Pin tab";onTriggered:workspace.pin(itemMenu.item.id)}
  MenuItem {text:"Add to Favorites";onTriggered:workspace.pin(itemMenu.item.id,true)}
  MenuItem {text:"Back to Pinned URL";visible:!!itemMenu.item&&(itemMenu.item.kind==="pinned"||itemMenu.item.kind==="favorite");onTriggered:{workspace.select(itemMenu.item.id);root.activate(itemMenu.item.id);if(root.active)root.active.url=itemMenu.item.savedUrl}}
  MenuItem {text:"Edit Pinned URL";visible:!!itemMenu.item&&(itemMenu.item.kind==="pinned"||itemMenu.item.kind==="favorite");onTriggered:{pinnedUrlDialog.itemId=itemMenu.item.id;pinnedUrlField.text=itemMenu.item.savedUrl;pinnedUrlDialog.open()}}
  MenuItem {text:"Rename";onTriggered:{renameDialog.itemId=itemMenu.item.id;renameField.text=itemMenu.item.title;renameDialog.open()}}
  MenuItem {text:"Remove";onTriggered:workspace.remove(itemMenu.item.id)}
 }
 Dialog {id:pinnedUrlDialog;property string itemId;anchors.centerIn:parent;title:"Edit Pinned URL";standardButtons:Dialog.Ok|Dialog.Cancel
  TextField {id:pinnedUrlField;width:360;placeholderText:"https://example.com"}
  onAccepted:if(!workspace.setPinnedUrl(itemId,pinnedUrlField.text)){pinnedUrlError.open()}
 }
 Dialog {id:pinnedUrlError;anchors.centerIn:parent;title:"Invalid pinned URL";standardButtons:Dialog.Ok;Label {text:"Enter an absolute HTTP or HTTPS URL."}}
 Dialog {id:renameDialog;property string itemId;anchors.centerIn:parent;title:"Rename";standardButtons:Dialog.Ok|Dialog.Cancel;TextField {id:renameField}onAccepted:workspace.rename(itemId,renameField.text)}
 Dialog {id:newSpace;anchors.centerIn:parent;title:"Create a Space";standardButtons:Dialog.Ok|Dialog.Cancel
  ColumnLayout {TextField {id:spaceTitle;placeholderText:"Space name"}ComboBox {id:profileSelect;model:workspace.profiles;textRole:"title";valueRole:"id"}}
  onAccepted:workspace.addSpace(spaceTitle.text,profileSelect.currentValue)
 }
 Dialog {id:permissionDialog;property var permission;anchors.centerIn:parent;title:"Website permission";standardButtons:Dialog.Yes|Dialog.No
  Label {text:permissionDialog.permission ? permissionDialog.permission.origin.toString()+" requests permission "+permissionDialog.permission.permissionType : ""}
  onAccepted:permission.grant();onRejected:permission.deny()
 }
 Dialog {id:reloadDialog;anchors.centerIn:parent;title:"Page process stopped";standardButtons:Dialog.Ok;onAccepted:if(root.active)root.active.reload()}
 Dialog {id:extensionApproval;property var extension;anchors.centerIn:parent;title:"Enable extension";standardButtons:Dialog.Ok|Dialog.Cancel
  Label {width:400;wrapMode:Text.Wrap;text:extensionApproval.extension?extensionApproval.extension.name+" requests: "+extensionApproval.extension.permissions:""}
  onAccepted:browserProfiles.enable(extension.id,true)
 }
 FolderDialog {id:extensionFolder;onAccepted:browserProfiles.install(selectedFolder)}
 Dialog {id:settings;anchors.centerIn:parent;width:480;title:"Profiles and extensions";standardButtons:Dialog.Close
  ColumnLayout {anchors.fill:parent
   CheckBox {text:"Dark appearance";checked:appSettings.dark;onClicked:appSettings.dark=checked}
   RowLayout {TextField {id:profileName;placeholderText:"New profile"}Button {text:"Create";onClicked:browserProfiles.get(workspace.addProfile(profileName.text))}}
   Button {text:"Install unpacked MV3 extension";enabled:browserProfiles.extensionsAvailable;onClicked:extensionFolder.open()}
   Label {visible:!browserProfiles.extensionsAvailable;text:"Extension validation is blocked by a runtime crash. This build is a browsing prototype, not the planned alpha.";wrapMode:Text.Wrap;Layout.fillWidth:true}
   Label {text:"Enable only extensions whose requested permissions you trust.";wrapMode:Text.Wrap;Layout.fillWidth:true}
   Repeater {model:browserProfiles.extensions
    RowLayout {required property var modelData
     CheckBox {enabled:browserProfiles.extensionsAvailable;text:modelData.name;checked:modelData.enabled;onClicked:{if(checked){extensionApproval.extension=modelData;extensionApproval.open()}else browserProfiles.enable(modelData.id,false)}}
     Button {text:"Popup";enabled:modelData.popup.toString().length>0;onClicked:{extensionPopup.popupUrl=modelData.popup;extensionPopup.open()}}
     Button {text:"Remove";onClicked:browserProfiles.uninstall(modelData.id)}
    }
   }
  }
 }
 Popup {id:extensionPopup;property url popupUrl;anchors.centerIn:parent;width:400;height:450;modal:true
  WebEngineView {anchors.fill:parent;profile:browserProfiles.get(workspace.currentProfile);url:extensionPopup.popupUrl}
 }
}
