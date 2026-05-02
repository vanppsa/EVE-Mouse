# EVE-Mouse - Project Context & Instructions

This file provides architectural context and development guidelines for the **EVE-Mouse** project.

## Project Overview

**EVE-Mouse** is a Linux desktop application (optimized for Fedora 44 / GNOME) that allows users to control their PC's mouse and keyboard through a mobile browser (iPhone/Android) over a local Wi-Fi network.

### Architecture & Components

The application consists of two main parts:

1.  **Desktop App (Python + GTK4):** A native GNOME interface for configuration and server lifecycle management.
2.  **Mobile Web Frontend (Vanilla HTML/CSS/JS):** A "trackpad" interface served by the backend and accessed via the phone's browser.

#### Folder Structure & Key Files

*   `main.py`: Entry point. Initializes the GTK4 GUI and global singletons.
*   `app/gui.py`: GTK4 window implementation. Manages the FastAPI/Uvicorn server thread.
*   `app/server.py`: FastAPI backend. Handles HTTP routes (login/static) and the WebSocket (`/ws`) for real-time input events.
*   `app/input_controller.py`: Input injection core. Uses `/dev/uinput` via `python-evdev` and `ydotool` for keyboard/mouse emulation.
*   `app/auth.py`: Session management (UUID4) and authentication (bcrypt).
*   `app/config.py`: Configuration persistence at `~/.config/EVE-Mouse/config.json`.
*   `app/static/`: Mobile frontend assets (`index.html`, `login.html`).

## Tech Stack

*   **Language:** Python 3
*   **GUI:** PyGObject (GTK4)
*   **Web Server:** FastAPI + Uvicorn (WebSockets)
*   **Input Injection:** `python-evdev` (Kernel-level, X11 & Wayland compatible)
*   **Text Input Fallbacks:** `ydotool` -> `wtype` -> `evdev` (direct)
*   **Security:** bcrypt (hashing) and HttpOnly Cookies for sessions

## Setup & Execution

### System Dependencies (Fedora)

```bash
sudo dnf install python3-gobject gtk4 ydotool
sudo usermod -aG input $USER
# Log out and log back in to apply group permissions
```

### ydotool Service

`ydotool` must run as a user service for text injection to work correctly:

```bash
systemctl --user enable --now ydotool.service
```

### Python Environment

```bash
pip install -r requirements.txt
```

### Running the Project

```bash
python main.py
```

## Development Conventions

### Threading & Event Loop

*   **GTK4 Main Loop:** Must always run on the `main thread`.
*   **FastAPI Server:** Runs in a separate daemon thread managed by `EveMouseWindow` in `gui.py`.
*   **Communication:** The server interacts with hardware through the `input_ctrl` singleton.

### Global Singletons

The following singletons are defined in `app/__init__.py` and should be used to maintain consistent state:
*   `auth`: Instance of `AuthManager`.
*   `input_ctrl`: Instance of `InputController`.

### WebSocket Protocol

Mobile events are sent as JSON messages:
*   `mousemove`: `{ "type": "mousemove", "dx": float, "dy": float }`
*   `click`: `{ "type": "click", "button": "left" | "right" | "middle" }`
*   `scroll`: `{ "type": "scroll", "dy": int }`
*   `keydown`: `{ "type": "keydown", "text": string }`
*   `special_key`: `{ "type": "special_key", "key": string }`

### Coding Style

*   **Backend:** Follow PEP 8. Use the "eve mouse" logger for debugging.
*   **Frontend:** Keep it vanilla (no heavy frameworks). CSS uses `:root` variables for theming.
*   **Security:** Never store plain-text passwords. Use `auth.set_password()`.

## Important Security & Hardware Notes

*   **Low-level Access:** Requires access to `/dev/uinput`. User must be in the `input` group.
*   **Wayland Support:** `evdev` and `ydotool` are essential for Wayland compatibility (X11 tools like `xdotool` will not work).
*   **Local Network:** The server listens on `0.0.0.0`, but is intended strictly for trusted local networks.
