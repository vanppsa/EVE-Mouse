# EVE Mouse

> Turn your smartphone into a remote trackpad and keyboard for Linux (X11 & Wayland).
> Optimized for **Fedora 44 Workstation (GNOME)**.

**EVE Mouse** is a tool that allows you to control your Linux computer's mouse and keyboard through any smartphone browser (Android or iPhone), using your local Wi-Fi network.

Unlike other solutions, EVE Mouse uses `/dev/uinput` at the kernel level, ensuring full compatibility with both **X11** and the modern **Wayland** display server (default in Fedora/GNOME).

<p align="center">
  <img src="EVE%20Mouse.gif" alt="EVE Mouse Demo" width="300">
</p>

---

## Features

* **Multi-touch Trackpad:** Control the cursor with precision, tap to click, and use two-finger scroll.
* **Double-click:** Tap twice on the trackpad for double-click.
* **Full Keyboard:** Type directly from your phone's keyboard to your PC (with IME/composition support).
* **Special Keys:** Quick access to Enter, Backspace, Tab, Esc, Space, Arrow keys, Ctrl, Alt, Super, and F1–F12.
* **Native Interface:** GTK4 configuration window that integrates seamlessly with GNOME.
* **Keep in Background:** Continue running the server when the window is closed.
* **Session Control:** Persistent or single-session mode with configurable timeout.
* **Security:** Password-protected access with bcrypt-hashed passwords and HttpOnly session cookies.
* **Low Latency:** WebSocket communication for real-time responsiveness.
* **Single Instance:** PID-based lock prevents multiple instances from running.

---

## Compatibility

| Distribution | Desktop | Status | Notes |
|---|---|---|---|
| **Fedora 40+** | GNOME (Wayland) | Primary target | Fully tested |
| **Ubuntu 22.04+** | GNOME / KDE | Compatible | `gir1.2-gtk-4.0` required |
| **Debian 12+** | GNOME / KDE | Compatible | Same as Ubuntu |
| **Arch Linux** | Any | Compatible | All deps in official repos |
| **Manjaro** | Any | Compatible | Same as Arch |
| **openSUSE Tumbleweed** | GNOME | Compatible | All deps in repos |
| **Ubuntu 20.04** | Any | Not supported | No GTK4 in repos |
| **Alpine** | Any | Not supported | No systemd, no GTK4 by default |
| **NixOS** | Any | Possible | Requires custom packaging |

**Requirements:** Linux kernel with `uinput` module, systemd (for ydotool service), GTK4, Python 3.10+.

---

## Installation

### Option 1: Setup Script (Recommended)

Single command that handles everything:

```bash
git clone https://github.com/vanppsa/EVE-Mouse.git
cd EVE-Mouse
./setup.sh
```

The `setup.sh` script automatically:
- Detects your Linux distribution
- Installs system dependencies
- Configures `/dev/uinput` udev rule
- Adds your user to the `input` group
- Enables ydotool service
- Creates Python virtual environment
- Runs the desktop entry installer

> **Note:** You may need to log out and back in after setup if it's your first time in the `input` group.

---

### Option 2: Install Script

```bash
git clone https://github.com/vanppsa/EVE-Mouse.git
cd EVE-Mouse
./install.sh
```

Same as option 1, but splits the process into two steps.

---

### Option 3: Manual Step by Step

For users who want to understand each step or troubleshoot.

#### 1. System Dependencies

```bash
sudo dnf install python3-gobject python3-venv gtk4 ydotool
```

#### 2. `/dev/uinput` Access

EVE Mouse needs write access to `/dev/uinput` for kernel-level input injection.

**Option A — udev rule (recommended):**
```bash
sudo cp 99-eve-mouse-uinput.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger /dev/uinput
```

**Option B — input group only:**
```bash
sudo usermod -aG input $USER
```

> **Important:** If using the group method, you must **log out and log back in** for the change to take effect.

#### 3. Configure ydotool (Wayland support)

```bash
systemctl --user enable --now ydotool.service
```

#### 4. Python Environment

```bash
git clone https://github.com/vanppsa/EVE-Mouse.git
cd EVE-Mouse
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. (Optional) Desktop Entry

To launch EVE Mouse from your GNOME application menu:

```bash
mkdir -p ~/.local/share/applications
sed -e "s|__PYTHON__|$(pwd)/venv/bin/python|g" \
    -e "s|__INSTALL_DIR__|$(pwd)|g" \
    com.eve.mouse.desktop.template > ~/.local/share/applications/com.eve.mouse.desktop
```

#### 6. (Optional) wtype

`wtype` is used as a fallback for text input if `ydotool` is unavailable:

```bash
# Fedora
sudo dnf install wtype

# Debian/Ubuntu
sudo apt install wtype

# Arch
sudo pacman -S wtype
```

---

### Other Linux Distributions

#### Ubuntu / Debian

```bash
sudo apt install python3-gi python3-venv gir1.2-gtk-4.0 ydotool
sudo usermod -aG input $USER
systemctl --user enable --now ydotool.service
```

#### Arch Linux / Manjaro

```bash
sudo pacman -S --needed python-gobject gtk4 ydotool python-virtualenv
sudo usermod -aG input $USER
systemctl --user enable --now ydotool.service
```

#### openSUSE Tumbleweed

```bash
sudo zypper install -y python3-gobject python3-venv gtk4 ydotool
sudo usermod -aG input $USER
systemctl --user enable --now ydotool.service
```

---

## How to Use

1. Run the application:
```bash
# Inside your venv
python main.py
```

2. In the **EVE Mouse** window, set an **Access Password**.
3. Click **Start Server**.
4. The application will display an **Access URL** (e.g., `http://192.168.1.15:10101`).
5. On your phone, connect to the same Wi-Fi network and open the URL in your browser.
6. Enter your password and enjoy your remote control.

> The server runs on port **10101** by default.

---

## How It Works

```
Phone Browser ──WebSocket──> FastAPI Server ──> InputController
                                  │                    │
                                  │                    ├── /dev/uinput (evdev)
                                  │                    ├── ydotool (Wayland text)
                                  │                    └── wtype (fallback)
                                  │
                                  └── GTK4 GUI (main thread)
```

**Text input fallback chain:** `evdev` direct → `ydotool` → `wtype` → `evdev` direct.

---

## Technologies Used

* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) (Python)
* **Desktop UI:** GTK4 + PyGObject (system package)
* **Input Injection:** `python-evdev` (`/dev/uinput`) and `ydotool`
* **Text Fallbacks:** `ydotool` → `wtype` → `evdev` direct
* **Communication:** WebSockets
* **Security:** `bcrypt` (password hashing), HttpOnly cookies (session management)
* **Mobile Frontend:** HTML5, CSS3, Vanilla JS

---

## Project Structure

```
EVE-Mouse/
├── main.py                           # Entry point
├── setup.sh                          # One-command setup script
├── install.sh                        # Desktop entry + icon installer
├── requirements.txt                  # Python dependencies (pip)
├── EVE Mouse.gif                     # Demo GIF
├── com.eve.mouse.desktop.template    # GNOME desktop entry template
├── 99-eve-mouse-uinput.rules         # Udev rule for /dev/uinput
├── .github/workflows/ci.yml          # GitHub Actions CI
├── app/
│   ├── __init__.py                   # Global singletons (auth, input_ctrl)
│   ├── gui.py                        # GTK4 window + server lifecycle
│   ├── server.py                     # FastAPI backend + WebSocket handler
│   ├── input_controller.py           # Input injection (evdev/ydotool/wtype)
│   ├── auth.py                       # Session management + bcrypt auth
│   ├── config.py                     # Configuration persistence (~/.config/EVE Mouse/)
│   └── static/
│       ├── index.html                # Mobile trackpad interface
│       ├── login.html                # Mobile login page
│       └── icons/
│           └── com.eve.mouse.png     # Application icon
```

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
