// SPDX-License-Identifier: MPL-2.0
#pragma once
#include <QJsonObject>
#include <QObject>
#include <QSqlDatabase>
#include <QVariantList>
class Workspace : public QObject {
  Q_OBJECT
  Q_PROPERTY(QVariantList spaces READ spaces NOTIFY changed)
  Q_PROPERTY(QVariantList profiles READ profiles NOTIFY changed)
  Q_PROPERTY(QVariantList items READ items NOTIFY changed)
  Q_PROPERTY(QVariantList sidebarItems READ sidebarItems NOTIFY changed)
  Q_PROPERTY(QString currentSpace READ currentSpace NOTIFY changed)
  Q_PROPERTY(QString currentProfile READ currentProfile NOTIFY changed)
  Q_PROPERTY(QString selected READ selected NOTIFY changed)
  Q_PROPERTY(QString error READ error NOTIFY errorChanged)
public:
  explicit Workspace(const QString &path, QObject *parent = nullptr);
  ~Workspace();
  QVariantList sidebarItems() const;
  QVariantList spaces() const;
  QVariantList profiles() const;
  QVariantList items() const;
  QString currentSpace() const;
  QString currentProfile() const;
  QString selected() const;
  QString error() const { return error_; }
  Q_INVOKABLE QString addProfile(QString title);
  Q_INVOKABLE QString addSpace(QString title, QString profile);
  Q_INVOKABLE QString addItem(QString kind, QString title, QString url = "",
                              QString parent = "");
  Q_INVOKABLE bool selectSpace(QString id);
  Q_INVOKABLE bool select(QString id);
  Q_INVOKABLE bool rename(QString id, QString title);
  Q_INVOKABLE bool move(QString id, QString parent, int position);
  Q_INVOKABLE bool close(QString id);
  Q_INVOKABLE bool remove(QString id);
  Q_INVOKABLE bool pin(QString id, bool favorite = false);
  Q_INVOKABLE bool setPinnedUrl(QString id, QString url);
  Q_INVOKABLE bool navigate(QString id, QString url, QString title);
  Q_INVOKABLE QString open(QString input);
  Q_INVOKABLE QString resolveInput(QString input);
  Q_INVOKABLE bool toggleFolder(QString id);
  static bool validate(const QJsonObject &doc, QString &error);
  QJsonObject document() const { return doc_; }
signals:
  void changed();
  void errorChanged();
  void pageClosed(QString id);

private:
  QJsonObject doc_;
  QSqlDatabase db_;
  QString connection_, error_;
  bool ready_ = false;
  bool commit(QJsonObject candidate);
  void fail(QString message);
};
