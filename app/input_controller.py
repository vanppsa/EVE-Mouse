import subprocess

from evdev import UInput, ecodes as e

BTN_MAP = {
    "left": e.BTN_LEFT,
    "right": e.BTN_RIGHT,
    "middle": e.BTN_MIDDLE,
}

SPECIAL_KEY_MAP = {
    "enter": e.KEY_ENTER,
    "backspace": e.KEY_BACKSPACE,
    "tab": e.KEY_TAB,
    "esc": e.KEY_ESC,
    "space": e.KEY_SPACE,
    "up": e.KEY_UP,
    "down": e.KEY_DOWN,
    "left": e.KEY_LEFT,
    "right": e.KEY_RIGHT,
    "shift": e.KEY_LEFTSHIFT,
    "ctrl": e.KEY_LEFTCTRL,
    "alt": e.KEY_LEFTALT,
    "super": e.KEY_LEFTMETA,
    "delete": e.KEY_DELETE,
    "home": e.KEY_HOME,
    "end": e.KEY_END,
    "page_up": e.KEY_PAGEUP,
    "page_down": e.KEY_PAGEDOWN,
    "f1": e.KEY_F1,
    "f2": e.KEY_F2,
    "f3": e.KEY_F3,
    "f4": e.KEY_F4,
    "f5": e.KEY_F5,
    "f6": e.KEY_F6,
    "f7": e.KEY_F7,
    "f8": e.KEY_F8,
    "f9": e.KEY_F9,
    "f10": e.KEY_F10,
    "f11": e.KEY_F11,
    "f12": e.KEY_F12,
}


class InputController:

    def __init__(self):
        self._mouse = None
        self._keyboard = None

    def init_devices(self) -> None:
        self._mouse = UInput(
            {
                e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
                e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
            },
            name="EVE-Mouse",
        )
        self._keyboard = UInput(
            {
                e.EV_KEY: list(range(0, 768)),
            },
            name="EVE-Mouse-keyboard",
        )

    def destroy_devices(self) -> None:
        if self._mouse:
            self._mouse.close()
            self._mouse = None
        if self._keyboard:
            self._keyboard.close()
            self._keyboard = None

    def move_mouse(self, dx: float, dy: float) -> None:
        if not self._mouse:
            return
        self._mouse.write(e.EV_REL, e.REL_X, int(dx))
        self._mouse.write(e.EV_REL, e.REL_Y, int(dy))
        self._mouse.syn()

    def click(self, button: str = "left") -> None:
        if not self._mouse:
            return
        btn = BTN_MAP.get(button, e.BTN_LEFT)
        self._mouse.write(e.EV_KEY, btn, 1)
        self._mouse.syn()
        self._mouse.write(e.EV_KEY, btn, 0)
        self._mouse.syn()

    def scroll(self, dy: int) -> None:
        if not self._mouse:
            return
        self._mouse.write(e.EV_REL, e.REL_WHEEL, dy)
        self._mouse.syn()

    def type_text(self, text: str) -> None:
        try:
            subprocess.run(
                ["ydotool", "type", "--", text],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass

    def special_key(self, key: str) -> None:
        if not self._keyboard:
            return
        code = SPECIAL_KEY_MAP.get(key)
        if code is None:
            return
        self._keyboard.write(e.EV_KEY, code, 1)
        self._keyboard.syn()
        self._keyboard.write(e.EV_KEY, code, 0)
        self._keyboard.syn()

    @property
    def is_initialized(self) -> bool:
        return self._mouse is not None and self._keyboard is not None
