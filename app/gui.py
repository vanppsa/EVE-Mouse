import threading
import logging

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Pango

from app.config import load_config, save_config, get_url
from app import auth, input_ctrl

logger = logging.getLogger("eve-mouse")

PORT = 10101
APP_TITLE = "EVE-Mouse"


class EveMouseWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        super().__init__(
            application=app,
            title=APP_TITLE,
            default_width=380,
            default_height=520,
            resizable=False,
        )
        self._server_thread = None
        self._server_running = False
        self._cfg = load_config()

        self._build_ui()
        self._load_config_to_ui()

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

        subtitle = Gtk.Label(label="Controle remoto de mouse e teclado")
        subtitle.add_css_class("subtitle")
        subtitle.set_margin_bottom(20)
        main_box.append(subtitle)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(sep)

        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings_box.set_margin_top(16)
        settings_box.set_margin_bottom(16)
        main_box.append(settings_box)

        self._sw_background = self._add_switch(
            settings_box, "Manter em segundo plano",
            "Servidor continua rodando ao fechar a janela"
        )

        self._sw_single_session = self._add_switch(
            settings_box, "Sessão única",
            "Token expira ao fechar o aplicativo"
        )

        self._sw_single_session.connect("notify::active", self._on_session_mode_changed)

        timeout_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        timeout_row.set_margin_top(4)
        timeout_lbl = Gtk.Label(label="Expiração da sessão (min):")
        timeout_lbl.set_xalign(0)
        timeout_lbl.set_size_request(170, -1)
        timeout_row.append(timeout_lbl)
        self._timeout_entry = Gtk.Entry()
        self._timeout_entry.set_placeholder_text("0 = sem limite")
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

        pw_lbl = Gtk.Label(label="Senha de acesso:")
        pw_lbl.set_xalign(0)
        pw_lbl.add_css_class("heading")
        auth_box.append(pw_lbl)

        self._pw_entry = Gtk.Entry()
        self._pw_entry.set_visibility(False)
        self._pw_entry.set_placeholder_text("Defina uma senha")
        self._pw_entry.set_margin_top(4)
        auth_box.append(self._pw_entry)

        self._pw_toggle = Gtk.Button(label="Mostrar senha")
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

        url_lbl = Gtk.Label(label="URL de acesso:")
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

        copy_btn = Gtk.Button(label="Copiar")
        copy_btn.add_css_class("pill")
        copy_btn.connect("clicked", self._on_copy_url)
        url_row.append(copy_btn)
        url_box.append(url_row)

        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        main_box.append(spacer)

        self._start_btn = Gtk.Button(label="Iniciar")
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
        self._pw_toggle.set_label("Ocultar senha" if not visible else "Mostrar senha")

    def _on_session_mode_changed(self, switch, _pspec):
        active = switch.get_active()
        self._timeout_entry.set_sensitive(not active)

    def _on_copy_url(self, _btn):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(get_url(PORT))
        self._start_btn.set_label("URL copiada!")
        def reset_label():
            if self._server_running:
                self._start_btn.set_label("Parar")
            else:
                self._start_btn.set_label("Iniciar")
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
        if not pw:
            self._pw_entry.grab_focus()
            return

        if not auth.password_hash or not auth.verify_password(pw):
            auth.set_password(pw)

        self._save_current_config()

        auth.session_mode = "single" if self._sw_single_session.get_active() else "persistent"
        timeout_str = self._timeout_entry.get_text().strip()
        auth.session_timeout_minutes = float(timeout_str) if timeout_str and timeout_str != "0" else 0

        input_ctrl.init_devices()

        def run_server():
            uvicorn.run(fastapi_app, host="0.0.0.0", port=PORT, log_level="warning")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        self._server_running = True

        self._url_label.set_label(get_url(PORT))
        self._start_btn.set_label("Parar")
        self._start_btn.remove_css_class("suggested-action")
        self._start_btn.add_css_class("destructive-action")

    def _stop_server(self):
        input_ctrl.destroy_devices()
        if auth.session_mode == "single":
            auth.invalidate_all_sessions()
        self._server_running = False
        self._start_btn.set_label("Iniciar")
        self._start_btn.remove_css_class("destructive-action")
        self._start_btn.add_css_class("suggested-action")

    def _save_current_config(self):
        self._cfg["password_hash"] = auth.password_hash
        self._cfg["session_mode"] = "single" if self._sw_single_session.get_active() else "persistent"
        timeout_str = self._timeout_entry.get_text().strip()
        self._cfg["session_timeout_minutes"] = float(timeout_str) if timeout_str and timeout_str != "0" else 0
        save_config(self._cfg)

    def _load_config_to_ui(self):
        self._sw_background.set_active(False)
        if self._cfg.get("session_mode") == "single":
            self._sw_single_session.set_active(True)
            self._timeout_entry.set_sensitive(False)
        timeout = self._cfg.get("session_timeout_minutes", 0)
        if timeout > 0:
            self._timeout_entry.set_text(str(int(timeout)))
        if self._cfg.get("password_hash"):
            auth.password_hash = self._cfg["password_hash"]
            self._pw_entry.set_placeholder_text("Senha já configurada")


def run_gui():
    app = Gtk.Application(application_id="com.eve.mouse")
    app.connect("activate", lambda a: EveMouseWindow(a).present())
    app.run()
