// SPDX-License-Identifier: MPL-2.0
#include "workspace.h"
#include <QJsonArray>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QTemporaryDir>
#include <QtTest>
class Tests : public QObject {
  Q_OBJECT
private slots:
  void persistence() {
    QTemporaryDir dir;
    QString id;
    {
      Workspace w(dir.filePath("db"));
      QVERIFY(w.error().isEmpty());
      id = w.addItem("pinned", "Example", "https://example.com");
      QVERIFY(!id.isEmpty());
    }
    {
      Workspace w(dir.filePath("db"));
      QCOMPARE(w.selected(), id);
      QCOMPARE(w.items().size(), 1);
    }
  }
  void cycles() {
    QTemporaryDir dir;
    Workspace w(dir.filePath("db"));
    auto a = w.addItem("folder", "A");
    auto b = w.addItem("folder", "B", "", a);
    QVERIFY(!w.move(a, b, 0));
    QCOMPARE(w.items()[0].toMap()["parent"].toString(), QString());
  }
  void isolation() {
    QTemporaryDir dir;
    Workspace w(dir.filePath("db"));
    auto p = w.addProfile("Work");
    auto s = w.addSpace("Work", p);
    auto id = w.open("https://example.com");
    auto old = w.spaces().first().toMap()["id"].toString();
    QVERIFY(w.selectSpace(old));
    QVERIFY(!w.select(id));
    QCOMPARE(w.currentSpace(), old);
  }
  void pinnedClose() {
    QTemporaryDir dir;
    Workspace w(dir.filePath("db"));
    auto id = w.addItem("pinned", "Pinned", "https://example.com");
    QVERIFY(w.close(id));
    QCOMPARE(w.items().size(), 1);
    QVERIFY(w.selected().isEmpty());
    auto temp = w.open("https://example.org");
    QVERIFY(w.close(temp));
    QCOMPARE(w.items().size(), 1);
  }
  void corruptStorageIsPreserved() {
    QTemporaryDir dir;
    const auto path = dir.filePath("db");
    {
      Workspace w(path);
      QVERIFY(w.error().isEmpty());
    }
    {
      auto db = QSqlDatabase::addDatabase("QSQLITE", "corruption-test");
      db.setDatabaseName(path);
      QVERIFY(db.open());
      QSqlQuery q(db);
      QVERIFY(q.exec("UPDATE workspace SET document='{\"version\":999}'"));
    }
    QSqlDatabase::removeDatabase("corruption-test");
    {
      Workspace w(path);
      QVERIFY(!w.error().isEmpty());
      QVERIFY(w.open("https://example.com").isEmpty());
    }
    {
      auto db = QSqlDatabase::addDatabase("QSQLITE", "preservation-test");
      db.setDatabaseName(path);
      QVERIFY(db.open());
      QSqlQuery q(db);
      QVERIFY(q.exec("SELECT document FROM workspace"));
      QVERIFY(q.next());
      QCOMPARE(q.value(0).toString(), QString("{\"version\":999}"));
    }
    QSqlDatabase::removeDatabase("preservation-test");
  }
  void folderVisibility() {
    QTemporaryDir dir;
    Workspace w(dir.filePath("db"));
    auto folder = w.addItem("folder", "Folder");
    QVERIFY(!w.addItem("pinned", "Nested", "https://example.com", folder)
                 .isEmpty());
    QCOMPARE(w.sidebarItems().size(), 2);
    QVERIFY(w.toggleFolder(folder));
    QCOMPARE(w.sidebarItems().size(), 1);
  }
  void malformed() {
    QString error;
    QVERIFY(!Workspace::validate(QJsonObject{{"version", 99}}, error));
  }
};
QTEST_GUILESS_MAIN(Tests)
#include "workspace_test.moc"
