// SPDX-License-Identifier: MPL-2.0
#include "workspace.h"
#include <QJsonArray>
#include <QJsonDocument>
#include <QSet>
#include <QSqlError>
#include <QSqlQuery>
#include <QUrl>
#include <QUrlQuery>
#include <QUuid>
#include <functional>
static QString uuid() {
  return QUuid::createUuid().toString(QUuid::WithoutBraces);
}
static int find(const QJsonArray &a, const QString &id) {
  for (int i = 0; i < a.size(); i++)
    if (a[i].toObject()["id"].toString() == id)
      return i;
  return -1;
}
void Workspace::fail(QString m) {
  error_ = m;
  emit errorChanged();
}
Workspace::Workspace(const QString &path, QObject *p)
    : QObject(p), connection_(uuid()) {
  db_ = QSqlDatabase::addDatabase("QSQLITE", connection_);
  db_.setDatabaseName(path);
  if (!db_.open()) {
    fail(db_.lastError().text());
    return;
  }
  QSqlQuery q(db_);
  if (!q.exec("CREATE TABLE IF NOT EXISTS workspace (id INTEGER PRIMARY KEY "
              "CHECK(id=1), document TEXT NOT NULL)")) {
    fail(q.lastError().text());
    return;
  }
  if (!q.exec("SELECT document FROM workspace WHERE id=1")) {
    fail(q.lastError().text());
    return;
  }
  if (q.next()) {
    QJsonParseError e;
    auto d = QJsonDocument::fromJson(q.value(0).toByteArray(), &e);
    QString issue;
    if (e.error != QJsonParseError::NoError || !d.isObject() ||
        !validate(d.object(), issue)) {
      fail("Workspace could not be loaded: " + issue + e.errorString());
      return;
    }
    doc_ = d.object();
    ready_ = true;
    return;
  }
  ready_ = true;
  QString profile = uuid(), space = uuid();
  commit(QJsonObject{{"version", 1},
                     {"profiles", QJsonArray{QJsonObject{
                                      {"id", profile}, {"title", "Default"}}}},
                     {"spaces", QJsonArray{QJsonObject{{"id", space},
                                                       {"title", "Personal"},
                                                       {"profile", profile},
                                                       {"selected", ""}}}},
                     {"items", QJsonArray{}},
                     {"currentSpace", space}});
}
Workspace::~Workspace() {
  db_.close();
  db_ = QSqlDatabase();
  QSqlDatabase::removeDatabase(connection_);
}
bool Workspace::validate(const QJsonObject &d, QString &error) {
  auto reject = [&](QString m) {
    error = m;
    return false;
  };
  if (d["version"].toInt() != 1 || !d["profiles"].isArray() ||
      !d["spaces"].isArray() || !d["items"].isArray())
    return reject("Unsupported workspace format");
  QSet<QString> ids, profiles;
  QMap<QString, QString> spaces;
  QMap<QString, QJsonObject> items;
  for (auto key : {"profiles", "spaces", "items"})
    for (auto v : d[key].toArray()) {
      if (!v.isObject())
        return reject("Invalid record");
      auto o = v.toObject();
      auto id = o["id"].toString();
      if (id.isEmpty() || ids.contains(id) || !o["title"].isString())
        return reject("Invalid identity or title");
      ids.insert(id);
      if (QString(key) == "profiles")
        profiles.insert(id);
      else if (QString(key) == "spaces")
        spaces[id] = o["profile"].toString();
      else
        items[id] = o;
    }
  if (profiles.isEmpty() || spaces.isEmpty() ||
      !spaces.contains(d["currentSpace"].toString()))
    return reject("Missing active workspace");
  for (auto p : spaces)
    if (!profiles.contains(p))
      return reject("Unknown profile");
  for (auto o : items) {
    auto kind = o["kind"].toString(), space = o["space"].toString(),
         profile = o["profile"].toString();
    if (!QStringList{"folder", "pinned", "temporary", "favorite"}.contains(
            kind) ||
        !profiles.contains(profile))
      return reject("Invalid item kind or profile");
    if (kind != "favorite" &&
        (!spaces.contains(space) || spaces[space] != profile))
      return reject("Item profile mismatch");
    if (kind == "favorite" &&
        (!o["parent"].toString().isEmpty() || !space.isEmpty()))
      return reject("Favorite must belong to a profile");
    QSet<QString> visited;
    QString parent = o["parent"].toString();
    while (!parent.isEmpty()) {
      if (parent == o["id"].toString() || visited.contains(parent) ||
          !items.contains(parent))
        return reject("Folder cycle or missing parent");
      visited.insert(parent);
      auto p = items[parent];
      if (p["kind"] != "folder" || p["space"] != o["space"])
        return reject("Invalid parent");
      parent = p["parent"].toString();
    }
  }
  for (auto v : d["spaces"].toArray()) {
    auto s = v.toObject();
    auto id = s["selected"].toString();
    if (!id.isEmpty() &&
        (!items.contains(id) || items[id]["kind"] == "folder" ||
         items[id]["profile"] != s["profile"] ||
         (items[id]["kind"] != "favorite" && items[id]["space"] != s["id"])))
      return reject("Invalid selected tab");
  }
  return true;
}
bool Workspace::commit(QJsonObject d) {
  QString issue;
  if (!ready_) {
    fail("Storage unavailable; original data has been preserved");
    return false;
  }
  if (!validate(d, issue)) {
    fail(issue);
    return false;
  }
  if (!db_.transaction()) {
    fail(db_.lastError().text());
    return false;
  }
  QSqlQuery q(db_);
  q.prepare("INSERT OR REPLACE INTO workspace(id,document) VALUES(1,?)");
  q.addBindValue(
      QString::fromUtf8(QJsonDocument(d).toJson(QJsonDocument::Compact)));
  if (!q.exec() || !db_.commit()) {
    auto error = q.lastError().text();
    db_.rollback();
    fail(error);
    return false;
  }
  doc_ = d;
  error_.clear();
  emit changed();
  emit errorChanged();
  return true;
}
QVariantList Workspace::spaces() const {
  return doc_["spaces"].toArray().toVariantList();
}
QVariantList Workspace::profiles() const {
  return doc_["profiles"].toArray().toVariantList();
}
QVariantList Workspace::items() const {
  return doc_["items"].toArray().toVariantList();
}
QString Workspace::currentSpace() const {
  return doc_["currentSpace"].toString();
}
QString Workspace::currentProfile() const {
  auto a = doc_["spaces"].toArray();
  int i = find(a, currentSpace());
  return i < 0 ? QString() : a[i].toObject()["profile"].toString();
}
QString Workspace::selected() const {
  auto a = doc_["spaces"].toArray();
  int i = find(a, currentSpace());
  return i < 0 ? QString() : a[i].toObject()["selected"].toString();
}
QString Workspace::addProfile(QString title) {
  auto d = doc_;
  auto a = d["profiles"].toArray();
  auto id = uuid();
  a.append(QJsonObject{{"id", id}, {"title", title}});
  d["profiles"] = a;
  return commit(d) ? id : QString();
}
QString Workspace::addSpace(QString title, QString profile) {
  auto d = doc_;
  auto a = d["spaces"].toArray();
  auto id = uuid();
  a.append(QJsonObject{
      {"id", id}, {"title", title}, {"profile", profile}, {"selected", ""}});
  d["spaces"] = a;
  d["currentSpace"] = id;
  return commit(d) ? id : QString();
}
QString Workspace::addItem(QString kind, QString title, QString url,
                           QString parent) {
  auto d = doc_;
  auto a = d["items"].toArray();
  auto id = uuid();
  a.append(
      QJsonObject{{"id", id},
                  {"kind", kind},
                  {"title", title},
                  {"url", url},
                  {"savedUrl", url},
                  {"parent", parent},
                  {"space", kind == "favorite" ? QString() : currentSpace()},
                  {"profile", currentProfile()},
                  {"expanded", true}});
  d["items"] = a;
  if (!commit(d))
    return {};
  if (kind != "folder")
    select(id);
  return id;
}
bool Workspace::selectSpace(QString id) {
  auto d = doc_;
  d["currentSpace"] = id;
  return commit(d);
}
bool Workspace::select(QString id) {
  auto d = doc_;
  auto a = d["spaces"].toArray();
  int i = find(a, currentSpace());
  if (i < 0)
    return false;
  auto s = a[i].toObject();
  s["selected"] = id;
  a[i] = s;
  d["spaces"] = a;
  return commit(d);
}
bool Workspace::rename(QString id, QString title) {
  auto d = doc_;
  for (auto key : {"items", "spaces", "profiles"}) {
    auto a = d[key].toArray();
    int i = find(a, id);
    if (i >= 0) {
      auto o = a[i].toObject();
      o["title"] = title;
      o["customTitle"] = true;
      a[i] = o;
      d[key] = a;
      return commit(d);
    }
  }
  return false;
}
bool Workspace::move(QString id, QString parent, int position) {
  auto d = doc_;
  auto a = d["items"].toArray();
  int i = find(a, id);
  if (i < 0)
    return false;
  auto o = a.takeAt(i).toObject();
  o["parent"] = parent;
  a.insert(qBound(0, position, int(a.size())), o);
  d["items"] = a;
  return commit(d);
}
bool Workspace::remove(QString id) {
  auto d = doc_;
  auto a = d["items"].toArray();
  QSet<QString> gone{id};
  bool more = true;
  while (more) {
    more = false;
    for (auto v : a) {
      auto o = v.toObject();
      if (gone.contains(o["parent"].toString()) &&
          !gone.contains(o["id"].toString())) {
        gone.insert(o["id"].toString());
        more = true;
      }
    }
  }
  for (int i = a.size() - 1; i >= 0; i--)
    if (gone.contains(a[i].toObject()["id"].toString()))
      a.removeAt(i);
  d["items"] = a;
  auto s = d["spaces"].toArray();
  for (int i = 0; i < s.size(); i++) {
    auto o = s[i].toObject();
    if (gone.contains(o["selected"].toString()))
      o["selected"] = "";
    s[i] = o;
  }
  d["spaces"] = s;
  if (!commit(d))
    return false;
  for (auto x : gone)
    emit pageClosed(x);
  return true;
}
bool Workspace::close(QString id) {
  auto a = doc_["items"].toArray();
  int i = find(a, id);
  if (i < 0)
    return false;
  auto o = a[i].toObject();
  if (o["kind"] == "temporary")
    return remove(id);
  auto d = doc_;
  o["url"] = o["savedUrl"];
  a[i] = o;
  d["items"] = a;
  auto s = d["spaces"].toArray();
  for (int n = 0; n < s.size(); n++) {
    auto x = s[n].toObject();
    if (x["selected"] == id)
      x["selected"] = "";
    s[n] = x;
  }
  d["spaces"] = s;
  if (!commit(d))
    return false;
  emit pageClosed(id);
  return true;
}
bool Workspace::pin(QString id, bool favorite) {
  auto d = doc_;
  auto a = d["items"].toArray();
  int i = find(a, id);
  if (i < 0)
    return false;
  auto o = a[i].toObject();
  o["kind"] = favorite ? "favorite" : "pinned";
  o["savedUrl"] = o["url"];
  if (favorite) {
    o["space"] = "";
    o["parent"] = "";
  }
  a[i] = o;
  d["items"] = a;
  return commit(d);
}
// ARC-B008: saved URL is distinct from the currently navigated URL.
bool Workspace::setPinnedUrl(QString id, QString url) {
  QUrl address(url.trimmed());
  if (!address.isValid() || address.host().isEmpty() ||
      (address.scheme() != "http" && address.scheme() != "https"))
    return false;
  auto d = doc_;
  auto a = d["items"].toArray();
  int i = find(a, id);
  if (i < 0)
    return false;
  auto o = a[i].toObject();
  if (o["kind"] != "pinned" && o["kind"] != "favorite")
    return false;
  o["savedUrl"] = address.toString();
  a[i] = o;
  d["items"] = a;
  return commit(d);
}

bool Workspace::navigate(QString id, QString url, QString title) {
  auto d = doc_;
  auto a = d["items"].toArray();
  int i = find(a, id);
  if (i < 0)
    return false;
  auto o = a[i].toObject();
  o["url"] = url;
  if (!o["customTitle"].toBool())
    o["title"] = title.isEmpty() ? url : title;
  a[i] = o;
  d["items"] = a;
  return commit(d);
}
bool Workspace::toggleFolder(QString id) {
  auto d = doc_;
  auto a = d["items"].toArray();
  int i = find(a, id);
  if (i < 0)
    return false;
  auto o = a[i].toObject();
  o["expanded"] = !o["expanded"].toBool();
  a[i] = o;
  d["items"] = a;
  return commit(d);
}
QString Workspace::resolveInput(QString input) {
  input = input.trimmed();
  if (input.isEmpty())
    return {};
  QUrl url;
  if (input.contains(' ') ||
      (!input.contains('.') && !input.contains(":") && input != "localhost")) {
    url = QUrl("https://duckduckgo.com/");
    QUrlQuery q;
    q.addQueryItem("q", input);
    url.setQuery(q);
  } else
    url = QUrl::fromUserInput(input);
  if (!QStringList{"http", "https"}.contains(url.scheme())) {
    fail("Only HTTP and HTTPS navigation is supported here");
    return {};
  }
  return url.toString();
}
QString Workspace::open(QString input) {
  auto url = resolveInput(input);
  return url.isEmpty() ? QString() : addItem("temporary", input, url);
}

QVariantList Workspace::sidebarItems() const {
  QVariantList out;
  auto all = doc_["items"].toArray();
  std::function<void(QString, int)> append = [&](QString parent, int depth) {
    for (int index = 0; index < all.size(); index++) {
      auto o = all[index].toObject();
      if (o["space"].toString() != currentSpace() || o["kind"] == "favorite" ||
          o["parent"].toString() != parent)
        continue;
      o["depth"] = depth;
      o["position"] = index;
      out.append(o.toVariantMap());
      if (o["kind"] == "folder" && o["expanded"].toBool())
        append(o["id"].toString(), depth + 1);
    }
  };
  append("", 0);
  return out;
}
