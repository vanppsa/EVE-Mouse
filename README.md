# EVE-Mouse

> Control your Linux mouse and keyboard from your phone via local network (Wi-Fi), using only the browser.
> Compatible with **X11 and Wayland** (Fedora 44 / GNOME).

## Overview

EVE-Mouse is a Linux desktop app (Fedora 44 / GNOME) with two parts:

- **Desktop app (GTK4):** A configuration window that starts a local web server.
- **Mobile frontend:** A web page accessed from any phone browser (iPhone or Android) that turns the entire screen into a **trackpad + text input + special keys**.

Communication between phone and PC happens via **WebSocket** over the local Wi-Fi network with minimal latency. All mouse and keyboard injection is done via `/dev/uinput` (kernel level), which works on both X11 and Wayland.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  LINUX PC (Fedora 44)            │
│                                                  │
│  ┌─────────────────┐     ┌────────────────────┐  │
│  │  GTK4 GUI       │────▶│  FastAPI + WS      │  │
│  │  (settings)     │     │  port :10101       │  │
│  └─────────────────┘     └────────┬───────────┘  │
│                                   │              │
│                       ┌───────────▼───────────┐  │
│                       │   input_controller    │  │
│                       │   python-evdev        │  │
│                       │   /dev/uinput         │  │
│                       │   ydotool (text)      │  │
│                       └───────────────────────┘  │
└──────────────────────────────────────────────────┘
                ▲
                │  WebSocket — local Wi-Fi
                │  http://192.168.x.x:10101
                ▼
┌──────────────────────────┐
│  iPhone / Android        │
│  (Safari or Chrome)      │
│                          │
│  ┌──────────────────┐    │
│  │ Text input field  │    │
│  ├──────────────────┤    │
│  │                  │    │
│  │  Trackpad area   │    │
│  │  (touch & drag)  │    │
│  │                  │    │
│  ├─────────┬────────┤    │
│  │  [ L ]  │  [ R ] │    │
│  └─────────┴────────┘    │
│  [Enter][Del][Tab][Esc]   │
└──────────────────────────┘
```

## Tech Stack

- **GUI:** Python + PyGObject (GTK4) — native GNOME, no heavy dependencies
- **Server:** FastAPI + Uvicorn — async, built-in WebSocket support
- **Input injection:** python-evdev + /dev/uinput — only reliable option on Wayland
- **Text typing:** ydotool (primary) → wtype (fallback) → evdev direct (fallback)
- **Mobile frontend:** HTML + CSS + JS vanilla — no framework, works on any browser
- **Communication:** WebSocket via FastAPI — minimal latency for real-time trackpad
- **Auth:** bcrypt + UUID4 token in HttpOnly cookie
- **Config:** JSON at `~/.config/EVE-Mouse/config.json`

## File Structure

```
EVE-Mouse/
├── main.py                   # Entry point: starts GTK4 GUI (main thread)
├── requirements.txt          # Python dependencies
├── EVE-Mouse.desktop         # GNOME menu shortcut
├── .gitignore
│
└── app/
    ├── __init__.py           # Shared auth + input_ctrl singletons
    ├── gui.py                # GTK4 settings window
    ├── server.py             # FastAPI: HTTP routes + WebSocket
    ├── input_controller.py   # Mouse/keyboard injection via evdev + ydotool
    ├── auth.py               # bcrypt password + session management
    ├── config.py             # Read/write config.json
    │
    └── static/
        ├── login.html        # Login screen (mobile browser)
        └── index.html        # Trackpad + text input interface
```

## Installation

### System dependencies (DNF)

```bash
sudo dnf install python3-gobject gtk4 ydotool
mkdir -p ~/.config/systemd/user
sudo cp /usr/lib/systemd/system/ydotool.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ydotool.service

sudo usermod -aG input $USER
# Log out and log back in for the input group to take effect
```

### Python environment

```bash
python3 -m venv ~/.local/share/EVE-Mouse/venv
~/.local/share/EVE-Mouse/venv/bin/pip install -r requirements.txt
```

### Run

```bash
~/.local/share/EVE-Mouse/venv/bin python /path/to/EVE-Mouse/main.py
```

Or search for **EVE-Mouse** in the GNOME application menu.

## Configuration

### GUI Settings

- **Keep in background** — server keeps running when the window is closed
- **Single session** — token expires when the app is closed
- **Session expiry (min)** — time in minutes; `0` = no limit
- **Access password** — password used for browser login
- **Access URL** — auto-detected local IP + port (read-only)
- **Copy** — copies URL to clipboard
- **Start / Stop** — toggles the web server

### config.json (`~/.config/EVE-Mouse/config.json`)

```json
{
  "password_hash": "$2b$12$...",
  "port": 10101,
  "session_mode": "persistent",
  "session_timeout_minutes": 0,
  "trackpad_sensitivity": 1.5
}
```

## Server Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/status` | Healthcheck — returns `{ "ok": true }` |
| `GET` | `/login` | Serves the login page |
| `POST` | `/auth/login` | Validates password, sets session cookie |
| `GET` | `/auth/logout` | Invalidates session, redirects to /login |
| `GET` | `/` | Serves trackpad interface (requires auth) |
| `WS` | `/ws` | WebSocket for real-time input events (requires auth) |

## WebSocket Protocol

All messages between phone and PC are JSON:

```
{ "type": "mousemove", "dx": 5.2, "dy": -3.1 }    // Move mouse
{ "type": "click", "button": "left" }               // "left" | "right" | "middle"
{ "type": "dblclick", "button": "left" }            // Double click
{ "type": "scroll", "dy": -2 }                      // Scroll
{ "type": "keydown", "text": "Hello World" }        // Type text
{ "type": "special_key", "key": "enter" }           // enter|backspace|tab|esc|space|arrows|ctrl|alt|super|f1-f12
```

## Mobile Interface

- **Top bar:** text input field (opens phone keyboard) + connection status + exit button
- **Trackpad area:** touch and drag to move mouse, tap to click, double-tap to double-click
- **Two-finger scroll:** swipe with two fingers to scroll
- **Special keys row:** Enter, Del, Tab, Esc, Space, arrow keys, Ctrl, Alt, Super
- **Bottom buttons:** Left click (L) and Right click (R)

## Important Notes

- **`input` group:** Your user MUST be in the `input` group. Run `sudo usermod -aG input $USER` and log out/in.
- **ydotool daemon:** Must run as a **user service** (`systemctl --user`). System-level service won't create the user socket.
- **Port 10101:** Chosen because ports below 1024 require root on Linux.
- **GTK4 on main thread:** The GTK loop must run on the main thread — server runs in a daemon thread.
- **WebSocket + cookies:** Browsers send cookies on WebSocket connections on the same origin — works natively.
- **Local network only:** Do not expose port 10101 to the internet.
