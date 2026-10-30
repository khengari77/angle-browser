// SPDX-License-Identifier: MPL-2.0
#include "workspace.h"
#include <QDir>
#include <QFile>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>
#include <QQuickWebEngineProfile>
#include <QQuickWindow>
#include <QSettings>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QTimer>
#include <QWebEngineExtensionInfo>
#include <QWebEngineExtensionManager>
#include <QtWebEngineQuick/qtwebenginequickglobal.h>
class Profiles : public QObject {
  Q_OBJECT
  Q_PROPERTY(QVariantList extensions READ extensions NOTIFY extensionsChanged)
  Q_PROPERTY(bool extensionsAvailable READ extensionsAvailable CONSTANT)
public:
  Profiles(QString root, Workspace *w) : root_(root), w_(w) {
    connect(w, &Workspace::changed, this, &Profiles::extensionsChanged);
  }
  Q_INVOKABLE QQuickWebEngineProfile *get(QString id) {
    if (!profiles_.contains(id)) {
      auto p = new QQuickWebEngineProfile(id, this);
      p->setPersistentStoragePath(root_ + "/profiles/" + id);
      p->setCachePath(root_ + "/cache/" + id);
      profiles_[id] = p;
      auto manager = p->extensionManager();
      connect(
          manager, &QWebEngineExtensionManager::loadFinished, this,
          [this, id, manager](const QWebEngineExtensionInfo &e) {
            QSettings settings;
            if (settings.value("extensions/" + id + "/" + e.id(), false)
                    .toBool()) {
              if (QCoreApplication::arguments().contains("--engine-gate"))
                manager->setExtensionEnabled(e, true);
            }
            emit extensionsChanged();
          },
          Qt::QueuedConnection);
      connect(manager, &QWebEngineExtensionManager::installFinished, this,
              [this](const QWebEngineExtensionInfo &) {
                emit extensionsChanged();
              });
      connect(manager, &QWebEngineExtensionManager::uninstallFinished, this,
              [this](const QWebEngineExtensionInfo &) {
                emit extensionsChanged();
              });
    }
    return profiles_[id];
  }
  bool extensionsAvailable() const { return false; }
  QVariantList extensions() {
    QVariantList out;
    for (auto e : get(w_->currentProfile())->extensionManager()->extensions()) {
      QFile manifest(e.path() + "/manifest.json");
      QStringList permissions;
      QUrl popup;
      if (manifest.open(QIODevice::ReadOnly)) {
        auto m = QJsonDocument::fromJson(manifest.readAll()).object();
        for (auto key : {"permissions", "host_permissions"})
          for (auto v : m[key].toArray())
            permissions.append(v.toString());
        for (auto script : m["content_scripts"].toArray())
          for (auto match : script.toObject()["matches"].toArray())
            permissions.append(match.toString());
        auto relative = m["action"].toObject()["default_popup"].toString();
        if (!relative.isEmpty()) {
          auto candidate = QUrl("chrome-extension://" + e.id() + "/")
                               .resolved(QUrl(relative));
          if (candidate.scheme() == "chrome-extension" &&
              candidate.host() == e.id())
            popup = candidate;
        }
      }
      out.append(QVariantMap{{"id", e.id()},
                             {"name", e.name()},
                             {"enabled", e.isEnabled()},
                             {"popup", popup},
                             {"error", e.error()},
                             {"permissions", permissions.join(", ")}});
    }
    return out;
  }
  Q_INVOKABLE void install(QUrl path) {
    qInfo() << "EXTENSION_INSTALL" << path;
    get(w_->currentProfile())
        ->extensionManager()
        ->installExtension(path.toLocalFile());
  }
  Q_INVOKABLE void enable(QString id, bool enabled) {
    if (!QCoreApplication::arguments().contains("--engine-gate"))
      return;
    auto p = get(w_->currentProfile());
    for (auto e : p->extensionManager()->extensions())
      if (e.id() == id) {
        p->extensionManager()->setExtensionEnabled(e, enabled);
        QSettings s;
        s.setValue("extensions/" + w_->currentProfile() + "/" + id, enabled);
      }
    emit extensionsChanged();
  }
  Q_INVOKABLE void uninstall(QString id) {
    auto m = get(w_->currentProfile())->extensionManager();
    for (auto e : m->extensions())
      if (e.id() == id)
        m->uninstallExtension(e);
    emit extensionsChanged();
  }

private:
  QString root_;
  Workspace *w_;
  QMap<QString, QQuickWebEngineProfile *> profiles_;
signals:
  void extensionsChanged();
};
int main(int argc, char **argv) {
  QtWebEngineQuick::initialize();
  QGuiApplication app(argc, argv);
  QQuickStyle::setStyle("Basic");
  app.setOrganizationName("ArcReverse");
  app.setApplicationName("ArcReverse");
  QTemporaryDir temporary;
  bool smoke = app.arguments().contains("--smoke");
  bool gate = app.arguments().contains("--engine-gate");
  auto root =
      gate ? qEnvironmentVariable("ARCREVERSE_TEST_DATA")
      : smoke
          ? temporary.path()
          : QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
  if (gate && root.isEmpty())
    return 4;
  if (gate || smoke) {
    QSettings::setDefaultFormat(QSettings::IniFormat);
    QSettings::setPath(QSettings::IniFormat, QSettings::UserScope,
                       root + "/settings");
  }
  QDir().mkpath(root);
  Workspace workspace(root + "/workspace.sqlite");
  Profiles profiles(root, &workspace);
  QQmlApplicationEngine engine;
  engine.rootContext()->setContextProperty("workspace", &workspace);
  engine.rootContext()->setContextProperty("browserProfiles", &profiles);
  engine.rootContext()->setContextProperty(
      "probeRoot",
      QUrl::fromLocalFile(QDir::currentPath() + "/tests/extensions/")
          .toString());
  engine.rootContext()->setContextProperty(
      "gateUrl", qEnvironmentVariable("ARCREVERSE_TEST_URL"));
  engine.rootContext()->setContextProperty(
      "gateRestore", app.arguments().contains("--restore"));
  QObject::connect(&engine, &QQmlApplicationEngine::exit, &app,
                   &QCoreApplication::exit);
  engine.loadFromModule("ArcReverse", gate ? "EngineGate" : "Main");
  if (engine.rootObjects().isEmpty())
    return 1;
  if (smoke) {
    workspace.open("https://example.com");
    auto timer = new QTimer(&app);
    QObject::connect(timer, &QTimer::timeout, &app, [&]() {
      auto object = engine.rootObjects().first();
      if (object->property("engineLoaded").toBool()) {
        if (auto window = qobject_cast<QQuickWindow *>(object))
          window->grabWindow().save("artifacts/browser-smoke.png");
        qInfo("ENGINE_RENDER_PASS");
        app.exit(0);
      }
    });
    timer->start(500);
    QTimer::singleShot(30000, &app, [&]() {
      qCritical("ENGINE_RENDER_TIMEOUT");
      app.exit(2);
    });
  }
  return app.exec();
}
#include "main.moc"
