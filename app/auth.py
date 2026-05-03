import time
import uuid
from dataclasses import dataclass, field

import bcrypt


@dataclass
class Session:
    token: str
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class AuthManager:
    def __init__(self):
        self._password_hash: str = ""
        self._sessions: dict[str, Session] = {}
        self.session_mode: str = "persistent"
        self.session_timeout_minutes: float = 0

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @password_hash.setter
    def password_hash(self, value: str):
        self._password_hash = value

    def set_password(self, plain_password: str) -> str:
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        self._password_hash = hashed
        return hashed

    def verify_password(self, plain_password: str) -> bool:
        if not self._password_hash:
            return False
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), self._password_hash.encode("utf-8")
            )
        except Exception:
            return False

    def create_session(self) -> str:
        token = str(uuid.uuid4())
        expires_at = None
        if self.session_timeout_minutes > 0:
            expires_at = time.time() + (self.session_timeout_minutes * 60)
        self._sessions[token] = Session(token=token, expires_at=expires_at)
        return token

    def is_valid_session(self, token: str | None) -> bool:
        if not token:
            return False
        session = self._sessions.get(token)
        if not session:
            return False
        if session.is_expired():
            del self._sessions[token]
            return False
        return True

    def invalidate_session(self, token: str) -> None:
        self._sessions.pop(token, None)

    def invalidate_all_sessions(self) -> None:
        self._sessions.clear()

    def cleanup_expired(self) -> None:
        expired = [t for t, s in self._sessions.items() if s.is_expired()]
        for t in expired:
            del self._sessions[t]
