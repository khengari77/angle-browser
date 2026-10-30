// SPDX-License-Identifier: MPL-2.0
// Independent diagnostic: no QML and no ArcReverse application services.
#include <QApplication>
#include <QDebug>
#include <QTemporaryDir>
#include <QTimer>
#include <QWebEngineExtensionInfo>
#include <QWebEngineExtensionManager>
#include <QWebEnginePage>
#include <QWebEngineProfile>
int main(int argc, char **argv) {
  QApplication app(argc, argv);
  QTemporaryDir dir;
  QWebEngineProfile profile("probe");
  profile.setPersistentStoragePath(dir.path());
  QWebEnginePage page(&profile);
  auto manager = profile.extensionManager();
  QObject::connect(manager, &QWebEngineExtensionManager::installFinished, &app,
                   [&](QWebEngineExtensionInfo info) {
                     qInfo() << "PROBE_INSTALLED" << info.name() << info.error()
                             << "loaded" << info.isLoaded() << "enabled"
                             << info.isEnabled();
                     if (!info.error().isEmpty()) {
                       app.exit(3);
                       return;
                     }
                     QTimer::singleShot(0, &app, [&, info]() {
                       qInfo() << "PROBE_ENABLING";
                       manager->setExtensionEnabled(info, true);
                       qInfo() << "PROBE_ENABLED";
                       QTimer::singleShot(1500, &app, [&]() { app.exit(0); });
                     });
                   });
  QObject::connect(&page, &QWebEnginePage::loadFinished, &app, [&](bool ok) {
    if (ok)
      manager->installExtension(QString::fromLocal8Bit(argv[1]));
    else
      app.exit(4);
  });
  QTimer::singleShot(20000, &app, [&]() { app.exit(5); });
  page.setHtml("<!doctype html><title>Native extension probe</title>",
               QUrl("http://localhost/"));
  return app.exec();
}
