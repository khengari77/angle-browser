#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
set -euo pipefail
package_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
install_prefix="${1:-$HOME/.local}"
install_root="$install_prefix/opt/arcreverse-0.1.0"
if [[ ! -x "$package_root/AppRun" ]]; then echo 'Run this installer from an extracted browser package.' >&2;exit 1;fi
if [[ -e "$install_root" || -e "$install_prefix/bin/arcreverse" ]]; then echo 'Installation target exists; choose another prefix.' >&2;exit 1;fi
mkdir -p "$install_prefix/opt" "$install_prefix/bin" "$install_prefix/share/applications"
cp -a "$package_root" "$install_root"
ln -s "$install_root/AppRun" "$install_prefix/bin/arcreverse"
cat > "$install_prefix/share/applications/arcreverse.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=ArcReverse Development Alpha
Exec="$install_root/AppRun" %u
Categories=Network;WebBrowser;
MimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;
Terminal=false
DESKTOP
printf 'Installed: %s\n' "$install_prefix/bin/arcreverse"
