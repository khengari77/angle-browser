# Third-party components

Angle's original code is MPL-2.0. Qt, Chromium and their dependencies retain their own licenses. No Arc executable, artwork, source or decompiler output is part of the browser distribution.

The application dynamically links Qt Core, Gui, Qml, Quick, Quick Controls, SQL and WebEngine. Open-source Qt components are distributed under their applicable LGPL/GPL alternatives; WebEngine also includes Chromium and numerous independently licensed components. Preserve the SDK's license texts and attribution files when packaging. See https://doc.qt.io/qt-6.10/qtwebengine-licensing.html.

Dependency source and modifications must be made available as required by each component's license; MPL does not replace these requirements. Development SDK files remain local under `.local-tools`. A distribution must carry its actual dependency version inventory and license files.

The research tools use independently installed REA and Ghidra, which are not required at browser runtime and are not bundled with it.
