// SPDX-License-Identifier: MPL-2.0
// Original, isolated browser/profile probe. Links the verified prebuilt CEF SDK.
#include "include/cef_app.h"
#include "include/cef_browser.h"
#include "include/cef_command_line.h"
#include "include/cef_client.h"
#include "include/cef_request_context.h"
#include "include/cef_request_context_handler.h"
#include "include/views/cef_browser_view.h"
#include "include/views/cef_window.h"
#include <iostream>
#include <filesystem>
#include <fstream>

int windows = 0;
class Client final : public CefClient, public CefLifeSpanHandler {
 public:
  CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
  void OnAfterCreated(CefRefPtr<CefBrowser> browser) override {
    ++windows;
    std::cout << "PROBE_BROWSER " << browser->GetIdentifier() << std::endl;
  }
  void OnBeforeClose(CefRefPtr<CefBrowser>) override {
    if (--windows == 0) CefQuitMessageLoop();
  }
 private:
  IMPLEMENT_REFCOUNTING(Client);
};
class Window final : public CefWindowDelegate {
 public:
  Window(CefRefPtr<CefBrowserView> view, cef_runtime_style_t style) : view_(view), style_(style) {}
  void OnWindowCreated(CefRefPtr<CefWindow> window) override {
    window->AddChildView(view_); window->SetSize(CefSize(800,600)); window->Show();
  }
  bool CanClose(CefRefPtr<CefWindow>) override {
    auto browser=view_->GetBrowser(); return !browser || browser->GetHost()->TryCloseBrowser();
  }
  cef_runtime_style_t GetWindowRuntimeStyle() override { return style_; }
 private:
  CefRefPtr<CefBrowserView> view_;
  cef_runtime_style_t style_;
  IMPLEMENT_REFCOUNTING(Window);
};
class View final : public CefBrowserViewDelegate {
 public:
  explicit View(cef_runtime_style_t style):style_(style){}
  cef_runtime_style_t GetBrowserRuntimeStyle() override {return style_;}
 private:
  cef_runtime_style_t style_;
  IMPLEMENT_REFCOUNTING(View);
};
class ContextReady final : public CefRequestContextHandler {
 public:
  ContextReady(CefRefPtr<Client> client, cef_runtime_style_t style, std::string url)
      :client_(client),style_(style),url_(url){}
  void OnRequestContextInitialized(CefRefPtr<CefRequestContext> request) override {
    std::cout << "PROBE_CONTEXT " << request->GetCachePath().ToString() << std::endl;
    auto view=CefBrowserView::CreateBrowserView(client_,url_,CefBrowserSettings(),nullptr,request,new View(style_));
    CefWindow::CreateTopLevelWindow(new Window(view,style_));
  }
 private:
  CefRefPtr<Client> client_;
  cef_runtime_style_t style_;
  std::string url_;
  IMPLEMENT_REFCOUNTING(ContextReady);
};
class App final : public CefApp, public CefBrowserProcessHandler {
 public:
  CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override {return this;}
  void OnBeforeCommandLineProcessing(const CefString& process_type, CefRefPtr<CefCommandLine> cmd) override {
    if(!process_type.empty()||!cmd->HasSwitch("persist-extension-config"))return;
    const auto root=cmd->GetSwitchValue("probe-root").ToString();
    if(root.empty())return;
    std::filesystem::create_directories(root);
    const auto file=root+"/enabled-extension-paths.txt";
    if(cmd->HasSwitch("load-extension")) {
      std::ofstream output(file);output<<cmd->GetSwitchValue("load-extension").ToString();
    } else {
      std::ifstream input(file);std::string paths;std::getline(input,paths);
      if(!paths.empty()&&paths.size()<=8192) {
        cmd->AppendSwitchWithValue("load-extension",paths);
        std::cout<<"PROBE_EXTENSION_CONFIG_RESTORED"<<std::endl;
      }
    }
  }
  CefRefPtr<CefClient> GetDefaultClient() override {return client_;}
  void OnContextInitialized() override {
    auto cmd=CefCommandLine::GetGlobalCommandLine();
    auto style=cmd->HasSwitch("use-alloy-style")?CEF_RUNTIME_STYLE_ALLOY:CEF_RUNTIME_STYLE_CHROME;
    client_=new Client;
    CefRequestContextSettings context;
    CefString(&context.cache_path)=cmd->GetSwitchValue("probe-root").ToString()+"/profile-b";
    context.persist_session_cookies=true;
    if(cmd->HasSwitch("native-window")) {
      CefWindowInfo info;info.runtime_style=style;
      CefBrowserHost::CreateBrowser(info,client_,cmd->GetSwitchValue("url"),CefBrowserSettings(),nullptr,CefRequestContext::GetGlobalContext());
    } else {
      auto view=CefBrowserView::CreateBrowserView(client_,cmd->GetSwitchValue("url"),CefBrowserSettings(),nullptr,CefRequestContext::GetGlobalContext(),new View(style));
      CefWindow::CreateTopLevelWindow(new Window(view,style));
    }
    if(cmd->HasSwitch("single-profile"))return;
    other_=CefRequestContext::CreateContext(context,new ContextReady(client_,style,cmd->GetSwitchValue("url").ToString()));
    other_->GetCookieManager(nullptr);
  }
 private:
  CefRefPtr<Client> client_;
  CefRefPtr<CefRequestContext> other_;
  IMPLEMENT_REFCOUNTING(App);
};
int main(int argc,char**argv) {
  CefMainArgs args(argc,argv);
  CefRefPtr<App> app=new App;
  int subprocess=CefExecuteProcess(args,app,nullptr);
  if(subprocess>=0)return subprocess;
  auto cmd=CefCommandLine::CreateCommandLine();cmd->InitFromArgv(argc,argv);
  auto root=cmd->GetSwitchValue("probe-root").ToString();
  if(root.empty()){std::cerr<<"--probe-root required\n";return 2;}
  CefSettings settings;
  CefString(&settings.root_cache_path)=root;
  CefString(&settings.cache_path)=root+"/profile-a";
  settings.persist_session_cookies=true;
  CefString(&settings.resources_dir_path)=cmd->GetSwitchValue("resources-dir-path");
  CefString(&settings.locales_dir_path)=cmd->GetSwitchValue("locales-dir-path");
  // no_sandbox remains false. Packaging must preserve sandbox support.
  if(!CefInitialize(args,settings,app,nullptr))return CefGetExitCode();
  CefRunMessageLoop();CefShutdown();return 0;
}
