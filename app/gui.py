import os
import sys
import threading
import logging
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango

from app.config import load_config, save_config, get_url
from app import auth, input_ctrl

logger = logging.getLogger("eve-mouse")

PORT = 10101
APP_TITLE = "EVE-Mouse"
SAVED_PW_MASK = "••••••••"
PID_FILE = Path.home() / ".config" / "EVE-Mouse" / "app.pid"


def _clean_stale_pid():
    if not PID_FILE.exists():
        return
    try:
        old_pid = int(PID_FILE.read_text().strip())
        os.kill(old_pid, 0)
    except ProcessLookupError:
        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass
    except (ValueError, PermissionError):
        try:
            PID_FILE.unlink()
        except FileNotFoundError:
            pass


def _write_pid():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def _remove_pid():
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


class EveMouseWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        super().__init__(
            application=app,
            title=APP_TITLE,
            default_width=380,
            default_height=560,
            resizable=False,
        )
        self._server_thread = None
        self._server_running = False
        self._uvicorn_server = None
        self._cfg = load_config()

        self._build_ui()
        self._load_config_to_ui()
        self.connect("close-request", self._on_close_request)

    def _build_ui(self):
        self.set_titlebar(Gtk.HeaderBar())
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        self.set_child(main_box)

        title = Gtk.Label(label="EVE-Mouse")
        title.add_css_class("title-1")
        title.set_margin_bottom(4)
        main_box.append(title)

        subtitle = Gtk.Label(label="Remote mouse and keyboard control")
        subtitle.add_css_class("subtitle")
        subtitle.set_margin_bottom(20)
        main_box.append(subtitle)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(sep)

        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings_box.set_margin_top(16)
        settings_box.set_margin_bottom(16)
        main_box.append(settings_box)

        self._sw_keep_background = self._add_switch(
            settings_box, "Keep in background",
            "Continue running server when window is closed"
        )

        self._sw_single_session = self._add_switch(
            settings_box, "Single session",
            "Token expires when app is closed"
        )

        self._sw_single_session.connect("notify::active", self._on_session_mode_changed)

        timeout_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        timeout_row.set_margin_top(4)
        timeout_lbl = Gtk.Label(label="Session expiry (min):")
        timeout_lbl.set_xalign(0)
        timeout_lbl.set_size_request(170, -1)
        timeout_row.append(timeout_lbl)
        self._timeout_entry = Gtk.Entry()
        self._timeout_entry.set_placeholder_text("0 = no limit")
        self._timeout_entry.set_width_chars(6)
        self._timeout_entry.set_max_length(5)
        self._timeout_entry.set_hexpand(True)
        self._timeout_entry.set_alignment(0.5)
        timeout_row.append(self._timeout_entry)
        settings_box.append(timeout_row)

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(sep2)

        auth_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        auth_box.set_margin_top(16)
        auth_box.set_margin_bottom(16)
        main_box.append(auth_box)

        pw_lbl = Gtk.Label(label="Access password:")
        pw_lbl.set_xalign(0)
        pw_lbl.add_css_class("heading")
        auth_box.append(pw_lbl)

        self._pw_entry = Gtk.Entry()
        self._pw_entry.set_visibility(False)
        self._pw_entry.set_placeholder_text("Set a password")
        self._pw_entry.set_margin_top(4)
        auth_box.append(self._pw_entry)

        self._pw_toggle = Gtk.Button(label="Show password")
        self._pw_toggle.add_css_class("flat")
        self._pw_toggle.set_margin_top(2)
        self._pw_toggle.connect("clicked", self._on_toggle_password)
        auth_box.append(self._pw_toggle)

        sep3 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(sep3)

        url_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        url_box.set_margin_top(16)
        url_box.set_margin_bottom(16)
        main_box.append(url_box)

        url_lbl = Gtk.Label(label="Access URL:")
        url_lbl.set_xalign(0)
        url_lbl.add_css_class("heading")
        url_box.append(url_lbl)

        url_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        url_row.set_margin_top(4)
        self._url_label = Gtk.Label(label=get_url(PORT))
        self._url_label.add_css_class("monospace")
        self._url_label.set_selectable(True)
        self._url_label.set_xalign(0)
        self._url_label.set_hexpand(True)
        self._url_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        url_row.append(self._url_label)

        copy_btn = Gtk.Button(label="Copy")
        copy_btn.add_css_class("pill")
        copy_btn.connect("clicked", self._on_copy_url)
        url_row.append(copy_btn)
        url_box.append(url_row)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        main_box.append(spacer)

        self._start_btn = Gtk.Button(label="Start")
        self._start_btn.add_css_class("suggested-action")
        self._start_btn.set_size_request(-1, 44)
        self._start_btn.connect("clicked", self._on_toggle_server)
        self._start_btn.set_margin_top(8)
        main_box.append(self._start_btn)

    def _add_switch(self, parent, label_text, subtitle_text):
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        row.set_margin_top(8)

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label=label_text)
        lbl.set_xalign(0)
        lbl.set_hexpand(True)
        top_row.append(lbl)

        sw = Gtk.Switch()
        sw.set_valign(Gtk.Align.CENTER)
        top_row.append(sw)
        row.append(top_row)

        if subtitle_text:
            sub = Gtk.Label(label=subtitle_text)
            sub.add_css_class("caption")
            sub.set_xalign(0)
            sub.set_margin_start(2)
            row.append(sub)

        parent.append(row)
        return sw

    def _on_toggle_password(self, _btn):
        visible = self._pw_entry.get_visibility()
        self._pw_entry.set_visibility(not visible)
        self._pw_toggle.set_label("Hide password" if not visible else "Show password")

    def _on_session_mode_changed(self, switch, _pspec):
        active = switch.get_active()
        self._timeout_entry.set_sensitive(not active)

    def _on_copy_url(self, _btn):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(get_url(PORT))
        self._start_btn.set_label("URL copied!")
        def reset_label():
            if self._server_running:
                self._start_btn.set_label("Stop")
            else:
                self._start_btn.set_label("Start")
            return GLib.SOURCE_REMOVE
        GLib.timeout_add_seconds(2, reset_label)

    def _on_toggle_server(self, _btn):
        if self._server_running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        from app.server import app as fastapi_app
        import uvicorn

        pw = self._pw_entry.get_text().strip()
        if pw == SAVED_PW_MASK:
            pw = ""
        if not pw and not auth.password_hash:
            self._pw_entry.grab_focus()
            return

        if pw and (not auth.password_hash or not auth.verify_password(pw)):
            auth.set_password(pw)

        self._save_current_config()

        auth.session_mode = "single" if self._sw_single_session.get_active() else "persistent"
        timeout_str = self._timeout_entry.get_text().strip()
        auth.session_timeout_minutes = float(timeout_str) if timeout_str and timeout_str != "0" else 0

        input_ctrl.init_devices()

        config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=PORT, log_level="warning")
        self._uvicorn_server = uvicorn.Server(config)
        self._server_thread = threading.Thread(target=self._uvicorn_server.run, daemon=True)
        self._server_thread.start()
        self._server_running = True
        self.get_application().hold()

        self._url_label.set_label(get_url(PORT))
        self._start_btn.set_label("Stop")
        self._start_btn.remove_css_class("suggested-action")
        self._start_btn.add_css_class("destructive-action")

        self._show_notification()

    def _stop_server(self):
        if not self._server_running:
            return
        if self._uvicorn_server:
            self._uvicorn_server.should_exit = True
        input_ctrl.destroy_devices()
        if auth.session_mode == "single":
            auth.invalidate_all_sessions()
        self._server_running = False
        self.get_application().release()
        self._start_btn.set_label("Start")
        self._start_btn.remove_css_class("destructive-action")
        self._start_btn.add_css_class("suggested-action")

    def _on_close_request(self, _window):
        if self._server_running and self._sw_keep_background.get_active():
            self.hide()
            return True
        if self._server_running:
            self._stop_server()
        self.get_application().quit()
        return False

    def _show_restore_dialog(self, restart_callback):
        dialog = Gtk.AlertDialog()
        dialog.set_message("EVE-Mouse is running in background")
        dialog.set_detail(f"Server active at: {get_url(PORT)}")
        dialog.set_buttons(["Restore", "New Instance"])

        def on_response(source, result, user_data):
            choice = source.choose_finish(result)
            if choice == 1:
                GLib.idle_add(restart_callback)

        dialog.choose(self, None, on_response, None)

    def _save_current_config(self):
        self._cfg["password_hash"] = auth.password_hash
        self._cfg["session_mode"] = "single" if self._sw_single_session.get_active() else "persistent"
        self._cfg["keep_background"] = self._sw_keep_background.get_active()
        timeout_str = self._timeout_entry.get_text().strip()
        self._cfg["session_timeout_minutes"] = float(timeout_str) if timeout_str and timeout_str != "0" else 0
        save_config(self._cfg)

    def _load_config_to_ui(self):
        if self._cfg.get("keep_background"):
            self._sw_keep_background.set_active(True)
        if self._cfg.get("session_mode") == "single":
            self._sw_single_session.set_active(True)
            self._timeout_entry.set_sensitive(False)
        timeout = self._cfg.get("session_timeout_minutes", 0)
        if timeout > 0:
            self._timeout_entry.set_text(str(int(timeout)))
        if self._cfg.get("password_hash"):
            auth.password_hash = self._cfg["password_hash"]
            self._pw_entry.set_text(SAVED_PW_MASK)

    def _show_notification(self):
        notif = Gio.Notification.new("EVE-Mouse running")
        notif.set_body(f"Access at: {get_url(PORT)}")
        notif.set_icon_name("input-mouse-symbolic")
        self.get_application().send_notification("eve-mouse-server", notif)


def run_gui():
    _clean_stale_pid()

    app = Gtk.Application(application_id="com.eve.mouse")
    window = None
    _restart = False

    def on_startup(a):
        _write_pid()

        stop_action = Gio.SimpleAction.new("stop-server", None)
        stop_action.connect("activate", lambda _a, _p: _do_stop())
        a.add_action(stop_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda _a, _p: _do_quit())
        a.add_action(quit_action)

    def on_activate(a):
        nonlocal window
        if window is None:
            window = EveMouseWindow(a)
            window.present()
            return

        was_hidden = not window.get_visible()
        window.present()

        if was_hidden and window._server_running:
            GLib.idle_add(lambda: window._show_restore_dialog(_do_restart))

    def on_shutdown(a):
        if window and window._server_running:
            window._server_running = False
            if window._uvicorn_server:
                window._uvicorn_server.should_exit = True
            input_ctrl.destroy_devices()
        _remove_pid()

    def _do_stop():
        if window and window._server_running:
            window._stop_server()
            window.present()

    def _do_quit():
        nonlocal _restart
        _restart = False
        app.quit()

    def _do_restart():
        nonlocal _restart
        _restart = True
        app.quit()

    app.connect("startup", on_startup)
    app.connect("activate", on_activate)
    app.connect("shutdown", on_shutdown)
    app.run()

    if _restart:
        os.execv(sys.executable, [sys.executable] + sys.argv)
