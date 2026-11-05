
from pathlib import Path
import json

from app.browser_automation.browser_manager import SESSION_DIR


class SessionManager:

    @staticmethod
    def get_session_path(user_id: str) -> Path:
        return SESSION_DIR / str(user_id) / "storage_state.json"

    @staticmethod
    def session_exists(user_id: str) -> bool:
        return SessionManager.get_session_path(user_id).is_file()

    @staticmethod
    def delete_session(user_id: str) -> bool:
        session_path = SessionManager.get_session_path(user_id)

        if session_path.exists():
            session_path.unlink()
            return True

        return False

    @staticmethod
    def inspect_session(user_id: str) -> dict:
        session_path = SessionManager.get_session_path(user_id)

        if not session_path.exists():
            return {"exists": False}

        try:
            data = json.loads(session_path.read_text(encoding="utf-8"))

            return {
                "exists": True,
                "cookies_count": len(data.get("cookies", [])),
                "origins_count": len(data.get("origins", [])),
            }

        except (OSError, json.JSONDecodeError):
            return {
                "exists": True,
                "valid": False,
            }
