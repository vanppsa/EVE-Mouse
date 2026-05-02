# 🖱️ EVE Mouse

> Turn your smartphone into a remote trackpad and keyboard for Linux (X11 & Wayland).
> Optimized for **Fedora 44 Workstation (GNOME)**.

**EVE Mouse** is a tool that allows you to control your Linux computer's mouse and keyboard through any smartphone browser (Android or iPhone), using your local Wi-Fi network.

Unlike other solutions, EVE Mouse uses `/dev/uinput` at the kernel level, ensuring full compatibility with both **X11** and the modern **Wayland** display server (default in Fedora/GNOME).

---

## ✨ Features

*   **Multi-touch Trackpad:** Control the cursor with precision, tap to click, and use two-finger scroll.
*   **Full Keyboard:** Type directly from your phone's keyboard to your PC.
*   **Special Keys:** Quick access to Enter, Esc, Tab, Delete, and arrow keys.
*   **Native Interface:** GTK4 configuration window that integrates seamlessly with GNOME.
*   **Security:** Password-protected access with encrypted sessions via bcrypt.
*   **Low Latency:** WebSocket communication for real-time responsiveness.

---

## 🚀 Installation (Fedora 44 Workstation)

Follow these steps to install and configure EVE Mouse on Fedora:

### 1. System Dependencies
Open your terminal and install the required packages:

```bash
sudo dnf install python3-gobject gtk4 ydotool
```

### 2. Permission Configuration
To allow the app to simulate mouse and keyboard events, your user needs access to input devices:

```bash
sudo usermod -aG input $USER
```
> **Important:** You must **Log out** and **Log in** again for the group change to take effect.

### 3. Configure ydotool (Wayland support)
Fedora uses Wayland by default. To enable keyboard support, start the `ydotool` service:

```bash
# Enable the user-level service
systemctl --user enable --now ydotool
```

### 4. Python Environment
Clone the repository and set up your virtual environment:

```bash
git clone https://github.com/seu-usuario/nautilus-2.git EVE-Mouse
cd EVE-Mouse
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🐧 Other Linux Distributions

### Ubuntu / Debian
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 ydotool
sudo usermod -aG input $USER
systemctl --user enable --now ydotool
```

### Arch Linux
```bash
sudo pacman -S python-gobject gtk4 ydotool
sudo usermod -aG input $USER
systemctl --user enable --now ydotool
```

---

## 🛠️ How to Use

1.  Run the application:
    ```bash
    # Inside your venv
    python main.py
    ```
2.  In the **EVE Mouse** window, set an **Access Password**.
3.  Click **Start Server**.
4.  The application will display an **Access URL** (e.g., `http://192.168.1.15:10101`).
5.  On your phone, connect to the same Wi-Fi network and open the URL in your browser.
6.  Enter your password and enjoy your remote control.

---

## 🛠️ Technologies Used

*   **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Desktop UI:** GTK4 + PyGObject
*   **Input Injection:** `python-evdev` and `ydotool`
*   **Communication:** WebSockets
*   **Mobile Frontend:** HTML5, CSS3, Vanilla JS (no heavy frameworks)

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
*Developed to provide the best remote control experience on Linux.*
