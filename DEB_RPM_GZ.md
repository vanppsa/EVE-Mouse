# Linux Packaging & GitHub Releases Guide

Complete guide to package a Python/GTK desktop app for RPM (Fedora), DEB (Ubuntu/Debian), and Arch (PKGBUILD) with automated GitHub Releases via CI.

---

## Overview

When you push a git tag (e.g. `v1.2.0`), GitHub Actions automatically:
1. Builds an `.rpm` inside a Fedora container
2. Builds a `.deb` on an Ubuntu runner
3. Generates a `PKGBUILD` for Arch Linux
4. Creates a GitHub Release with all files attached

Users then download and install with a single command or double-click.

---

## Repository Structure

```
your-project/
├── .github/workflows/
│   ├── ci.yml                    # Lint + tests on every push
│   └── release.yml               # Build packages on tag push
├── packaging/
│   ├── your-app.sh               # Launcher script (shared)
│   ├── your-app.desktop          # Desktop entry (fixed paths)
│   ├── postinstall.sh            # Post-install setup
│   ├── prerm.sh                  # Pre-remove cleanup
│   ├── rpm/your-app.spec         # RPM spec file
│   ├── deb/build-deb.sh          # DEB builder script
│   └── arch/PKGBUILD             # Arch build script
├── app/                          # Your application code
├── main.py                       # Entry point
├── requirements.txt              # Python dependencies
└── README.md
```

---

## Step 1: Shared Scripts

### Launcher (`packaging/your-app.sh`)

The binary users run. Installs deps on first launch if needed:

```bash
#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/your-app"
VENV_DIR="${INSTALL_DIR}/venv"

if [ ! -d "${VENV_DIR}" ] || [ ! -f "${VENV_DIR}/bin/python" ]; then
    python3 -m venv --system-site-packages "${VENV_DIR}" 2>/dev/null || {
        echo "Error: Failed to create virtual environment." >&2
        exit 1
    }
    "${VENV_DIR}/bin/pip" install -q -r "${INSTALL_DIR}/requirements.txt" 2>/dev/null || {
        echo "Warning: Failed to install some Python dependencies." >&2
    }
fi

exec "${VENV_DIR}/bin/python" "${INSTALL_DIR}/main.py" "$@"
```

Installed to `/usr/bin/your-app` by the package.

### Desktop Entry (`packaging/your-app.desktop`)

Shows your app in GNOME/KDE application menu:

```ini
[Desktop Entry]
Name=Your App
Comment=Short description
Exec=/usr/bin/your-app
Icon=your-app
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
```

Installed to `/usr/share/applications/your-app.desktop`.

### Post-install (`packaging/postinstall.sh`)

Runs automatically after package installation:

```bash
#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/your-app"
VENV_DIR="${INSTALL_DIR}/venv"

# Create venv with --system-site-packages to access GTK/system libs
if [ ! -d "${VENV_DIR}" ] || [ ! -f "${VENV_DIR}/bin/python" ]; then
    python3 -m venv --system-site-packages "${VENV_DIR}" 2>/dev/null || true
    "${VENV_DIR}/bin/pip" install -q -r "${INSTALL_DIR}/requirements.txt" 2>/dev/null || {
        echo "Warning: pip install failed. Run manually:"
        echo "  ${VENV_DIR}/bin/pip install -r ${INSTALL_DIR}/requirements.txt"
    }
fi

# Add any system setup here (udev rules, services, etc.)
echo "Your App installed successfully!"
```

### Pre-remove (`packaging/prerm.sh`)

Runs before package uninstall:

```bash
#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/your-app"
VENV_DIR="${INSTALL_DIR}/venv"

if [ -d "${VENV_DIR}" ]; then
    rm -rf "${VENV_DIR}"
fi
```

---

## Step 2: RPM (Fedora / RHEL / openSUSE)

### Spec File (`packaging/rpm/your-app.spec`)

```spec
Name:           your-app
Version:        __VERSION__
Release:        1%{?dist}
Summary:        Short description of your app

License:        MIT
URL:            https://github.com/you/your-app
Source0:        %{name}-%{version}.tar.gz

Requires:       python3 >= 3.10
Requires:       python3-gobject
Requires:       gtk4
Requires:       python3-pip

BuildArch:      noarch

%description
Longer description of your application.

%prep
%setup -q -n %{name}-%{version}

%install
mkdir -p %{buildroot}/opt/your-app
cp -r app main.py requirements.txt %{buildroot}/opt/your-app/

mkdir -p %{buildroot}/usr/bin
cp packaging/your-app.sh %{buildroot}/usr/bin/your-app
chmod 755 %{buildroot}/usr/bin/your-app

mkdir -p %{buildroot}/usr/share/applications
cp packaging/your-app.desktop %{buildroot}/usr/share/applications/your-app.desktop

mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
cp app/static/icons/your-app.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/your-app.png

mkdir -p %{buildroot}/usr/share/your-app
cp packaging/postinstall.sh %{buildroot}/usr/share/your-app/postinstall.sh
cp packaging/prerm.sh %{buildroot}/usr/share/your-app/prerm.sh
chmod 755 %{buildroot}/usr/share/your-app/postinstall.sh
chmod 755 %{buildroot}/usr/share/your-app/prerm.sh

%post
bash %{_datadir}/your-app/postinstall.sh || true

%postun
bash %{_datadir}/your-app/prerm.sh remove || true

%files
/opt/your-app/
/usr/bin/your-app
%{_datadir}/applications/your-app.desktop
%{_datadir}/icons/hicolor/256x256/apps/your-app.png
%{_datadir}/your-app/
```

Key points:
- `__VERSION__` is replaced by the CI with the actual tag version
- `BuildArch: noarch` for Python apps (no compiled code)
- `Requires:` declares system dependencies — `dnf` resolves them
- `%install` copies files to the fake root (`%{buildroot}`)
- `%post` / `%postun` run scripts after install/before remove
- `%files` must list every installed path

### Common RPM gotchas

- All files installed in `%install` must be listed in `%files`
- Do NOT put `%{buildroot}` operations in `%post` — only in `%install`
- `noarch` means architecture-independent (Python, not compiled)
- Use `%{_datadir}` instead of `/usr/share` for portability

---

## Step 3: DEB (Ubuntu / Debian / Mint)

### Build Script (`packaging/deb/build-deb.sh`)

```bash
#!/bin/bash
set -euo pipefail

VERSION="${1:?Usage: build-deb.sh <version>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="/tmp/your-app-build"

PKG_NAME="your-app"
PKG_DIR="${BUILD_DIR}/${PKG_NAME}_${VERSION}_all"

rm -rf "${BUILD_DIR}"
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/opt/your-app"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_DIR}/usr/share/your-app"

# App code
cp -r "${PROJECT_DIR}/app" "${PKG_DIR}/opt/your-app/"
cp "${PROJECT_DIR}/main.py" "${PKG_DIR}/opt/your-app/"
cp "${PROJECT_DIR}/requirements.txt" "${PKG_DIR}/opt/your-app/"

# Launcher
cp "${PROJECT_DIR}/packaging/your-app.sh" "${PKG_DIR}/usr/bin/your-app"
chmod 755 "${PKG_DIR}/usr/bin/your-app"

# Desktop entry
cp "${PROJECT_DIR}/packaging/your-app.desktop" \
   "${PKG_DIR}/usr/share/applications/your-app.desktop"

# Icon
cp "${PROJECT_DIR}/app/static/icons/your-app.png" \
   "${PKG_DIR}/usr/share/icons/hicolor/256x256/apps/your-app.png"

# Scripts
cp "${PROJECT_DIR}/packaging/postinstall.sh" "${PKG_DIR}/usr/share/your-app/"
cp "${PROJECT_DIR}/packaging/prerm.sh" "${PKG_DIR}/usr/share/your-app/"
chmod 755 "${PKG_DIR}/usr/share/your-app/postinstall.sh"
chmod 755 "${PKG_DIR}/usr/share/your-app/prerm.sh"

# DEBIAN/control
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, python3-pip, python3-venv
Maintainer: Your Name <you@email.com>
Description: Short description
 Longer description of your application.
Homepage: https://github.com/you/your-app
EOF

# DEBIAN/postinst
cat > "${PKG_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
bash /usr/share/your-app/postinstall.sh || true
EOF
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# DEBIAN/prerm
cat > "${PKG_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
bash /usr/share/your-app/prerm.sh "$1" || true
EOF
chmod 755 "${PKG_DIR}/DEBIAN/prerm"

# Build
dpkg-deb --build "${PKG_DIR}"
cp "${BUILD_DIR}/${PKG_NAME}_${VERSION}_all.deb" "${PROJECT_DIR}/"

echo "Built: ${PKG_NAME}_${VERSION}_all.deb"
rm -rf "${BUILD_DIR}"
```

### DEB dependency names vs RPM

| System Package | RPM (Fedora) | DEB (Ubuntu) |
|---|---|---|
| Python GObject | `python3-gobject` | `python3-gi` |
| GTK4 | `gtk4` | `gir1.2-gtk-4.0` |
| Python pip | `python3-pip` | `python3-pip` |
| Python venv | (included) | `python3-venv` |

---

## Step 4: Arch Linux (PKGBUILD)

### `packaging/arch/PKGBUILD`

```bash
pkgname=your-app
pkgver=__VERSION__
pkgrel=1
pkgdesc="Short description of your app"
arch=('any')
url="https://github.com/you/your-app"
license=('MIT')
depends=('python>=3.10' 'python-gobject' 'gtk4' 'python-pip' 'python-virtualenv')
source=("$pkgname-$pkgver.tar.gz::https://github.com/you/your-app/archive/v$pkgver.tar.gz")

package() {
    cd "${srcdir}/Your-App-${pkgver}"

    install -dm755 "${pkgdir}/opt/your-app"
    cp -r app main.py requirements.txt "${pkgdir}/opt/your-app/"

    install -Dm755 packaging/your-app.sh "${pkgdir}/usr/bin/your-app"
    install -Dm644 packaging/your-app.desktop "${pkgdir}/usr/share/applications/your-app.desktop"
    install -Dm644 app/static/icons/your-app.png "${pkgdir}/usr/share/icons/hicolor/256x256/apps/your-app.png"
    install -Dm755 packaging/postinstall.sh "${pkgdir}/usr/share/your-app/postinstall.sh"
    install -Dm755 packaging/prerm.sh "${pkgdir}/usr/share/your-app/prerm.sh"
}

post_install() {
    bash /usr/share/your-app/postinstall.sh 2>/dev/null || true
}

post_remove() {
    bash /usr/share/your-app/prerm.sh remove 2>/dev/null || true
}
```

Key points:
- `__VERSION__` replaced by CI
- `source=()` points to GitHub tarball (auto-downloaded by makepkg)
- `arch=('any')` for Python apps
- `post_install()` / `post_remove()` are special functions recognized by pacman
- Directory name in `srcdir` must match the GitHub repo name (e.g. `Your-App`)

---

## Step 5: GitHub Actions Release Workflow

### `.github/workflows/release.yml`

```yaml
name: Build & Release Packages

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build-rpm:
    runs-on: ubuntu-latest
    container: fedora:latest
    steps:
      - uses: actions/checkout@v4

      - name: Install build tools
        run: dnf install -y rpm-build

      - name: Extract version
        id: version
        run: |
          TAG="${GITHUB_REF_NAME}"
          VERSION="${TAG#v}"
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"

      - name: Prepare source tarball
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          mkdir -p ~/rpmbuild/SOURCES
          mkdir -p /tmp/your-app-${VERSION}
          cp -r app main.py requirements.txt packaging /tmp/your-app-${VERSION}/
          cd /tmp
          tar czf ~/rpmbuild/SOURCES/your-app-${VERSION}.tar.gz your-app-${VERSION}

      - name: Build RPM
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          sed "s/__VERSION__/${VERSION}/g" packaging/rpm/your-app.spec > /tmp/your-app.spec
          rpmbuild -bb /tmp/your-app.spec
          cp ~/rpmbuild/RPMS/noarch/*.rpm "${GITHUB_WORKSPACE}/"

      - name: Upload RPM artifact
        uses: actions/upload-artifact@v4
        with:
          name: rpm-package
          path: ./*.rpm

  build-deb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: |
          TAG="${GITHUB_REF_NAME}"
          VERSION="${TAG#v}"
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"

      - name: Build DEB
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          bash packaging/deb/build-deb.sh "${VERSION}"

      - name: Upload DEB artifact
        uses: actions/upload-artifact@v4
        with:
          name: deb-package
          path: ./*.deb

  build-arch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: |
          TAG="${GITHUB_REF_NAME}"
          VERSION="${TAG#v}"
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"

      - name: Prepare PKGBUILD
        run: |
          VERSION="${{ steps.version.outputs.version }}"
          mkdir -p /tmp/arch-package
          sed "s/__VERSION__/${VERSION}/g" packaging/arch/PKGBUILD > /tmp/arch-package/PKGBUILD
          tar czf arch-pkgbuild.tar.gz -C /tmp/arch-package PKGBUILD

      - name: Upload Arch artifact
        uses: actions/upload-artifact@v4
        with:
          name: arch-package
          path: arch-pkgbuild.tar.gz

  release:
    needs: [build-rpm, build-deb, build-arch]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/download-artifact@v4
        with:
          path: artifacts

      - name: List artifacts
        run: find artifacts -type f | sort

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          name: Your App ${{ github.ref_name }}
          draft: false
          prerelease: false
          generate_release_notes: true
          files: |
            artifacts/rpm-package/*.rpm
            artifacts/deb-package/*.deb
            artifacts/arch-package/*.tar.gz
          body: |
            ## Installation

            ### Fedora / RHEL
            ```bash
            sudo dnf install ./your-app-*.rpm
            ```

            ### Ubuntu / Debian / Mint
            ```bash
            sudo dpkg -i ./your-app_*_all.deb
            sudo apt install -f
            ```

            ### Arch Linux
            ```bash
            tar xzf arch-pkgbuild.tar.gz
            makepkg -si
            ```
```

### Critical: RPM in containers

When using `container: fedora:latest`, the home directory is `/github/home/` not `/root/`. The build writes RPMs to `~/rpmbuild/RPMS/` which maps to `/github/home/rpmbuild/RPMS/`. The `upload-artifact` action can't access paths outside the workspace. **Solution: copy the RPM to `${GITHUB_WORKSPACE}/` before uploading.**

---

## Step 6: Release Flow

```bash
# 1. Develop on your branch
git commit -m "some feature"

# 2. Merge to main
git checkout main
git merge your-branch

# 3. Tag and push
git tag v1.2.0
git push origin main --tags

# 4. GitHub Actions builds and publishes automatically
# 5. Packages appear at github.com/you/your-app/releases
```

### Updating a broken release

```bash
# Delete tag locally and remotely
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0

# Fix the issue, commit, then retag
git tag v1.2.0
git push origin v1.2.0
```

---

## Step 7: CI Workflow (Lint + Tests)

Separate from releases. Runs on every push to main:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install deps
        run: |
          pip install ruff
          sudo apt-get update && sudo apt-get install -y python3-gi gir1.2-gtk-4.0

      - name: Ruff check
        run: ruff check .

      - name: Ruff format check
        run: ruff format --check .

      - name: Python compile check
        run: |
          python3 -m py_compile main.py
          python3 -m py_compile app/__init__.py

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install deps
        run: |
          sudo apt-get update && sudo apt-get install -y python3-gi gir1.2-gtk-4.0
          pip install -r requirements.txt

      - name: Module import tests
        run: |
          python3 -c "from app.config import load_config; print('CONFIG OK')"
          python3 -c "from app.server import app; print('SERVER OK')"
```

---

## Checklist for New Projects

- [ ] Create `packaging/` directory with shared scripts
- [ ] Write `.spec` file (RPM) — adapt `Requires:` to your deps
- [ ] Write `build-deb.sh` — adapt `Depends:` to your deps
- [ ] Write `PKGBUILD` — adapt `depends=` to your deps
- [ ] Create `.github/workflows/ci.yml`
- [ ] Create `.github/workflows/release.yml`
- [ ] Add `*.rpm *.deb` to `.gitignore`
- [ ] Update `README.md` with package installation instructions
- [ ] Test: push a `v0.1.0` tag and verify the release
- [ ] Delete test tag/release when confirmed working

---

## Common Pitfalls

1. **RPM: files listed in `%files` but not created in `%install`** — Every path in `%files` must exist in `%{buildroot}`
2. **RPM: `%{buildroot}` in `%post`** — Never use buildroot in post scripts; they run on the user's machine
3. **Container builds: artifact path** — Copy files to `${GITHUB_WORKSPACE}/` before upload
4. **DEB: missing `python3-venv`** — Ubuntu needs this explicit dep; Fedora includes it
5. **Arch: wrong `srcdir` name** — Must match GitHub repo name (case-sensitive)
6. **Desktop entry: `Terminal=true`** — Use `false` for GUI apps, `true` for CLI apps
7. **Version in spec/PKGBUILD** — Use `__VERSION__` placeholder, replaced by CI via `sed`
