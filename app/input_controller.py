import subprocess
import logging

from evdev import UInput, ecodes as e

logger = logging.getLogger("eve mouse")

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
    "playpause": e.KEY_PLAYPAUSE,
    "stop": e.KEY_STOPCD,
    "next": e.KEY_NEXTSONG,
    "prev": e.KEY_PREVIOUSSONG,
    "volup": e.KEY_VOLUMEUP,
    "voldn": e.KEY_VOLUMEDOWN,
    "mute": e.KEY_MUTE,
}


class InputController:
    _simple = {
        "a": e.KEY_A,
        "b": e.KEY_B,
        "c": e.KEY_C,
        "d": e.KEY_D,
        "e": e.KEY_E,
        "f": e.KEY_F,
        "g": e.KEY_G,
        "h": e.KEY_H,
        "i": e.KEY_I,
        "j": e.KEY_J,
        "k": e.KEY_K,
        "l": e.KEY_L,
        "m": e.KEY_M,
        "n": e.KEY_N,
        "o": e.KEY_O,
        "p": e.KEY_P,
        "q": e.KEY_Q,
        "r": e.KEY_R,
        "s": e.KEY_S,
        "t": e.KEY_T,
        "u": e.KEY_U,
        "v": e.KEY_V,
        "w": e.KEY_W,
        "x": e.KEY_X,
        "y": e.KEY_Y,
        "z": e.KEY_Z,
        "0": e.KEY_0,
        "1": e.KEY_1,
        "2": e.KEY_2,
        "3": e.KEY_3,
        "4": e.KEY_4,
        "5": e.KEY_5,
        "6": e.KEY_6,
        "7": e.KEY_7,
        "8": e.KEY_8,
        "9": e.KEY_9,
        " ": e.KEY_SPACE,
        "\n": e.KEY_ENTER,
        "-": e.KEY_MINUS,
        "=": e.KEY_EQUAL,
        "[": e.KEY_LEFTBRACE,
        "]": e.KEY_RIGHTBRACE,
        "\\": e.KEY_BACKSLASH,
        ";": e.KEY_SEMICOLON,
        "'": e.KEY_APOSTROPHE,
        "`": e.KEY_GRAVE,
        ",": e.KEY_COMMA,
        ".": e.KEY_DOT,
        "/": e.KEY_SLASH,
    }

    _shifted = {
        "!": e.KEY_1,
        "@": e.KEY_2,
        "#": e.KEY_3,
        "$": e.KEY_4,
        "%": e.KEY_5,
        "^": e.KEY_6,
        "&": e.KEY_7,
        "*": e.KEY_8,
        "(": e.KEY_9,
        ")": e.KEY_0,
        "_": e.KEY_MINUS,
        "+": e.KEY_EQUAL,
        "{": e.KEY_LEFTBRACE,
        "}": e.KEY_RIGHTBRACE,
        "|": e.KEY_BACKSLASH,
        ":": e.KEY_SEMICOLON,
        '"': e.KEY_APOSTROPHE,
        "~": e.KEY_GRAVE,
        "<": e.KEY_COMMA,
        ">": e.KEY_DOT,
        "?": e.KEY_SLASH,
        "A": (e.KEY_A, True),
        "B": (e.KEY_B, True),
        "C": (e.KEY_C, True),
        "D": (e.KEY_D, True),
        "E": (e.KEY_E, True),
        "F": (e.KEY_F, True),
        "G": (e.KEY_G, True),
        "H": (e.KEY_H, True),
        "I": (e.KEY_I, True),
        "J": (e.KEY_J, True),
        "K": (e.KEY_K, True),
        "L": (e.KEY_L, True),
        "M": (e.KEY_M, True),
        "N": (e.KEY_N, True),
        "O": (e.KEY_O, True),
        "P": (e.KEY_P, True),
        "Q": (e.KEY_Q, True),
        "R": (e.KEY_R, True),
        "S": (e.KEY_S, True),
        "T": (e.KEY_T, True),
        "U": (e.KEY_U, True),
        "V": (e.KEY_V, True),
        "W": (e.KEY_W, True),
        "X": (e.KEY_X, True),
        "Y": (e.KEY_Y, True),
        "Z": (e.KEY_Z, True),
    }

    def __init__(self):
        self._mouse = None
        self._keyboard = None

    def init_devices(self) -> None:
        self._mouse = UInput(
            {
                e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL],
                e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
            },
            name="EVE Mouse",
        )
        self._keyboard = UInput(
            {
                e.EV_KEY: list(range(0, 768)),
            },
            name="EVE Mouse Keyboard",
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

    def mousedown(self, button: str = "left") -> None:
        if not self._mouse:
            return
        btn = BTN_MAP.get(button, e.BTN_LEFT)
        self._mouse.write(e.EV_KEY, btn, 1)
        self._mouse.syn()

    def mouseup(self, button: str = "left") -> None:
        if not self._mouse:
            return
        btn = BTN_MAP.get(button, e.BTN_LEFT)
        self._mouse.write(e.EV_KEY, btn, 0)
        self._mouse.syn()

    def scroll(self, dy: int) -> None:
        if not self._mouse:
            return
        self._mouse.write(e.EV_REL, e.REL_WHEEL, dy)
        self._mouse.syn()

    def _type_with_ydotool(self, text: str) -> bool:
        try:
            r = subprocess.run(
                ["ydotool", "type", "--", text],
                capture_output=True,
                timeout=5,
            )
            if r.returncode == 0:
                return True
            logger.warning(
                f"ydotool failed (rc={r.returncode}): {r.stderr.decode()[:200]}"
            )
        except FileNotFoundError:
            logger.warning("ydotool not found")
        except Exception as ex:
            logger.warning(f"ydotool error: {ex}")
        return False

    def _type_with_wtype(self, text: str) -> bool:
        try:
            r = subprocess.run(
                ["wtype", text],
                capture_output=True,
                timeout=5,
            )
            if r.returncode == 0:
                return True
        except FileNotFoundError:
            pass
        except Exception as ex:
            logger.warning(f"wtype error: {ex}")
        return False

    def _type_with_evdev(self, text: str) -> None:
        if not self._keyboard:
            return
        for char in text:
            code = self._char_to_keycode(char)
            if code is not None:
                self._keyboard.write(e.EV_KEY, code, 1)
                self._keyboard.syn()
                self._keyboard.write(e.EV_KEY, code, 0)
                self._keyboard.syn()

    def _char_to_keycode(self, char: str) -> int | None:
        shift = False
        keycode = None
        if char in self._simple:
            keycode = self._simple[char]
        elif char in self._shifted:
            val = self._shifted[char]
            if isinstance(val, tuple):
                keycode, shift = val[0], val[1]
            else:
                shift = True
                keycode = val

        if keycode is None:
            return None

        if shift:
            self._keyboard.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
            self._keyboard.syn()
            self._keyboard.write(e.EV_KEY, keycode, 1)
            self._keyboard.syn()
            self._keyboard.write(e.EV_KEY, keycode, 0)
            self._keyboard.syn()
            self._keyboard.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
            self._keyboard.syn()
            return None

        return keycode

    def _all_chars_mapped(self, text: str) -> bool:
        for char in text:
            if char not in self._simple and char not in self._shifted:
                return False
        return True

    def type_text(self, text: str) -> None:
        if not text:
            return
        if self._all_chars_mapped(text):
            self._type_with_evdev(text)
            return
        if self._type_with_ydotool(text):
            return
        if self._type_with_wtype(text):
            return
        self._type_with_evdev(text)

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
