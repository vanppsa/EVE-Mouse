#!/bin/bash
set -euo pipefail

VERSION="${1:?Usage: build-deb.sh <version>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="/tmp/eve-mouse-build"

PKG_NAME="eve-mouse"
PKG_DIR="${BUILD_DIR}/${PKG_NAME}_${VERSION}_all"

rm -rf "${BUILD_DIR}"
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/opt/eve-mouse"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/usr/share/eve-mouse"

cp -r "${PROJECT_DIR}/app" "${PKG_DIR}/opt/eve-mouse/"
cp "${PROJECT_DIR}/main.py" "${PKG_DIR}/opt/eve-mouse/"
cp "${PROJECT_DIR}/requirements.txt" "${PKG_DIR}/opt/eve-mouse/"
cp "${PROJECT_DIR}/99-eve-mouse-uinput.rules" "${PKG_DIR}/opt/eve-mouse/"

cp "${PROJECT_DIR}/packaging/eve-mouse.sh" "${PKG_DIR}/usr/bin/eve-mouse"
chmod 755 "${PKG_DIR}/usr/bin/eve-mouse"

cp "${PROJECT_DIR}/packaging/eve-mouse.desktop" "${PKG_DIR}/usr/share/applications/com.eve.mouse.desktop"

cp "${PROJECT_DIR}/app/static/icons/com.eve.mouse.png" "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/com.eve.mouse.png"

cp "${PROJECT_DIR}/packaging/postinstall.sh" "${PKG_DIR}/usr/share/eve-mouse/postinstall.sh"
cp "${PROJECT_DIR}/packaging/prerm.sh" "${PKG_DIR}/usr/share/eve-mouse/prerm.sh"
chmod 755 "${PKG_DIR}/usr/share/eve-mouse/postinstall.sh"
chmod 755 "${PKG_DIR}/usr/share/eve-mouse/prerm.sh"

cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, ydotool, python3-pip, python3-venv
Maintainer: Everton <vanppsa@users.noreply.github.com>
Description: Control mouse and keyboard from your phone
 EVE Mouse is a Linux desktop application that allows you to
 control your PC's mouse and keyboard through a mobile browser
 over local Wi-Fi. Uses /dev/uinput for full X11 and Wayland
 compatibility.
Homepage: https://github.com/vanppsa/EVE-Mouse
EOF

cat > "${PKG_DIR}/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e
bash /usr/share/eve-mouse/postinstall.sh || true
POSTINST
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

cat > "${PKG_DIR}/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e
bash /usr/share/eve-mouse/prerm.sh "$1" || true
PRERM
chmod 755 "${PKG_DIR}/DEBIAN/prerm"

dpkg-deb --build "${PKG_DIR}"

cp "${BUILD_DIR}/${PKG_NAME}_${VERSION}_all.deb" "${PROJECT_DIR}/"

echo "Built: ${PKG_NAME}_${VERSION}_all.deb"
rm -rf "${BUILD_DIR}"
