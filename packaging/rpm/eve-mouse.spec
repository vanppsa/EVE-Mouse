Name:           eve-mouse
Version:        __VERSION__
Release:        1%{?dist}
Summary:        Control mouse and keyboard from your phone over Wi-Fi

License:        MIT
URL:            https://github.com/vanppsa/EVE-Mouse
Source0:        %{name}-%{version}.tar.gz

Requires:       python3 >= 3.10
Requires:       python3-gobject
Requires:       gtk4
Requires:       ydotool
Requires:       python3-pip

BuildArch:      noarch

%description
EVE Mouse is a Linux desktop application that allows you to control
your PC's mouse and keyboard through a mobile browser over local Wi-Fi.
Uses /dev/uinput for full X11 and Wayland compatibility.

%prep
%setup -q -n %{name}-%{version}

%install
mkdir -p %{buildroot}/opt/eve-mouse
cp -r app main.py requirements.txt 99-eve-mouse-uinput.rules %{buildroot}/opt/eve-mouse/

mkdir -p %{buildroot}/usr/bin
cp packaging/eve-mouse.sh %{buildroot}/usr/bin/eve-mouse
chmod 755 %{buildroot}/usr/bin/eve-mouse

mkdir -p %{buildroot}/usr/share/applications
cp packaging/eve-mouse.desktop %{buildroot}/usr/share/applications/com.eve.mouse.desktop

mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
cp app/static/icons/com.eve.mouse.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/com.eve.mouse.png

%post
bash /opt/eve-mouse/../../usr/bin/eve-mouse-postinstall 2>/dev/null || bash %{_datadir}/eve-mouse/postinstall.sh 2>/dev/null || true

mkdir -p %{buildroot}/usr/share/eve-mouse
cp packaging/postinstall.sh %{buildroot}%{_datadir}/eve-mouse/postinstall.sh
cp packaging/prerm.sh %{buildroot}%{_datadir}/eve-mouse/prerm.sh

%postun
bash %{_datadir}/eve-mouse/prerm.sh remove 2>/dev/null || true

%files
/opt/eve-mouse/
/usr/bin/eve-mouse
%{_datadir}/applications/com.eve.mouse.desktop
%{_datadir}/icons/hicolor/256x256/apps/com.eve.mouse.png
%{_datadir}/eve-mouse/
