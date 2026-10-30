#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
set -euo pipefail
browser_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$browser_root/.local-tools/qt-tools/bin:$PATH"
package="$browser_root/dist/ArcReverse-0.1.0-linux-x86_64"
if [[ -e "$package" ]]; then echo "Package directory already exists: $package" >&2;exit 1;fi
mkdir -p "$package"
cmake --install "$browser_root/build" --prefix "$package/usr"
cp "$browser_root/LICENSE" "$browser_root/THIRD_PARTY_NOTICES.md" "$package/"
cat > "$package/AppRun" <<'RUN'
#!/usr/bin/env bash
set -euo pipefail
app_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$app_root/usr/bin/arcreverse" "$@"
RUN
chmod +x "$package/AppRun"
cp "$browser_root/scripts/install_browser.sh" "$package/install.sh"
tar -C "$browser_root/dist" -czf "$package.tar.gz" "$(basename "$package")"
