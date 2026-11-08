// SPDX-License-Identifier: MPL-2.0
// Rendering-only experiment: original Qt Quick/CEF integration, not product code.
#include "include/cef_app.h"
#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include "include/cef_command_line.h"
#include <QGuiApplication>
#include <QQuickWindow>
#include <QQuickPaintedItem>
#include <QPainter>
#include <QImage>
#include <QMutex>
#include <QMutexLocker>
#include <QTimer>
#include <filesystem>
#include <fstream>
#include <iostream>
class Surface final : public QQuickPaintedItem {
 public:
  using QQuickPaintedItem::QQuickPaintedItem;
  void frame(const void* buffer,int w,int h) {
    {QMutexLocker lock(&mutex_);image_=QImage(static_cast<const uchar*>(buffer),w,h,QImage::Format_ARGB32).copy();}
    update();
    if(!reported_){std::cout<<"QT_CEF_FRAME "<<w<<"x"<<h<<std::endl;reported_=true;}
  }
  void paint(QPainter* painter) override {QMutexLocker lock(&mutex_);painter->drawImage(boundingRect(),image_);}
 private:
  QMutex mutex_;QImage image_;bool reported_=false;
};
Surface* surface=nullptr;
CefRefPtr<CefBrowser> browser;
class Client final : public CefClient,public CefLifeSpanHandler,public CefRenderHandler {
 public:
  CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override{return this;}
  CefRefPtr<CefRenderHandler> GetRenderHandler() override{return this;}
  void GetViewRect(CefRefPtr<CefBrowser>,CefRect& rect) override{rect=CefRect(0,0,std::max(1,int(surface->width())),std::max(1,int(surface->height())));}
  void OnPaint(CefRefPtr<CefBrowser>,PaintElementType type,const RectList&,const void* buffer,int w,int h) override {
    if(type==PET_VIEW&&surface)surface->frame(buffer,w,h);
  }
  void OnAfterCreated(CefRefPtr<CefBrowser> created) override{browser=created;}
  void OnBeforeClose(CefRefPtr<CefBrowser>) override{browser=nullptr;QCoreApplication::quit();}
 private: IMPLEMENT_REFCOUNTING(Client);
};
class App final : public CefApp,public CefBrowserProcessHandler {
 public:
  CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override{return this;}
  void OnBeforeCommandLineProcessing(const CefString& type,CefRefPtr<CefCommandLine> cmd) override {
    if(!type.empty()||!cmd->HasSwitch("persist-extension-config"))return;
    auto root=cmd->GetSwitchValue("probe-root").ToString();if(root.empty())return;
    std::filesystem::create_directories(root);
    auto filename=root+"/enabled-extension-paths.txt";
    if(cmd->HasSwitch("load-extension")){std::ofstream out(filename);out<<cmd->GetSwitchValue("load-extension").ToString();}
    else{std::ifstream in(filename);std::string paths;std::getline(in,paths);if(!paths.empty()&&paths.size()<=8192)cmd->AppendSwitchWithValue("load-extension",paths);}
  }
  void OnContextInitialized() override {
    CefWindowInfo info;info.SetAsWindowless(0); // API forces Alloy style.
    CefBrowserSettings settings;settings.background_color=CefColorSetARGB(255,255,255,255);
    CefBrowserHost::CreateBrowser(info,new Client,CefCommandLine::GetGlobalCommandLine()->GetSwitchValue("url"),settings,nullptr,nullptr);
  }
 private: IMPLEMENT_REFCOUNTING(App);
};
int main(int argc,char** argv) {
  CefMainArgs args(argc,argv);CefRefPtr<App> app=new App;
  int code=CefExecuteProcess(args,app,nullptr);if(code>=0)return code;
  QGuiApplication gui(argc,argv);gui.setQuitOnLastWindowClosed(false);
  auto cmd=CefCommandLine::CreateCommandLine();cmd->InitFromArgv(argc,argv);
  const auto root=cmd->GetSwitchValue("probe-root").ToString();if(root.empty())return 2;
  QQuickWindow window;window.setTitle("Angle CEF Qt rendering spike");window.resize(800,600);
  Surface view(window.contentItem());surface=&view;view.setWidth(window.width());view.setHeight(window.height());
  QObject::connect(&window,&QQuickWindow::widthChanged,[&](){view.setWidth(window.width());if(browser)browser->GetHost()->WasResized();});
  QObject::connect(&window,&QQuickWindow::heightChanged,[&](){view.setHeight(window.height());if(browser)browser->GetHost()->WasResized();});
  window.show();
  std::cout<<"QT_BACKEND "<<QGuiApplication::platformName().toStdString()<<std::endl;
  CefSettings settings;settings.windowless_rendering_enabled=true;settings.external_message_pump=true;settings.persist_session_cookies=true;
  CefString(&settings.root_cache_path)=root;CefString(&settings.cache_path)=root+"/profile";
  CefString(&settings.resources_dir_path)=cmd->GetSwitchValue("resources-dir-path");
  CefString(&settings.locales_dir_path)=cmd->GetSwitchValue("locales-dir-path");
  if(!CefInitialize(args,settings,app,nullptr))return CefGetExitCode();
  QObject::connect(&gui,&QGuiApplication::lastWindowClosed,[](){if(browser)browser->GetHost()->CloseBrowser(true);else QCoreApplication::quit();});
  QTimer pump;QObject::connect(&pump,&QTimer::timeout,[]{CefDoMessageLoopWork();});pump.start(10);
  QTimer capture;QObject::connect(&capture,&QTimer::timeout,[&](){window.grabWindow().save(QString::fromStdString(root+"/qt-frame.png"));});capture.start(1000);
  const int result=gui.exec();pump.stop();capture.stop();
  window.grabWindow().save(QString::fromStdString(root+"/qt-frame.png"));
  surface=nullptr;browser=nullptr;CefShutdown();return result;
}
