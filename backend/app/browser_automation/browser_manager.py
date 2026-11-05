
from pathlib import Path
from playwright.async_api import async_playwright


BACKEND_DIR = Path(__file__).resolve().parents[2]
SESSION_DIR = BACKEND_DIR / "storage" / "browser_sessions"


class BrowserManager:

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self, user_id: str, headless: bool = False):
        if self.browser:
            raise RuntimeError("Browser is already running.")

        user_session_dir = SESSION_DIR / str(user_id)
        user_session_dir.mkdir(parents=True, exist_ok=True)

        state_file = user_session_dir / "storage_state.json"

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=headless
        )

        context_options = {
            "accept_downloads": True,
        }

        if state_file.exists():
            context_options["storage_state"] = str(state_file)

        self.context = await self.browser.new_context(
            **context_options
        )

        self.page = await self.context.new_page()

        return self.page

    async def save_session(self, user_id: str):
        if not self.context:
            raise RuntimeError("Browser context is not active.")

        user_session_dir = SESSION_DIR / str(user_id)
        user_session_dir.mkdir(parents=True, exist_ok=True)

        state_file = user_session_dir / "storage_state.json"

        await self.context.storage_state(path=str(state_file))

        return str(state_file)

    async def close(self):
        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        self.context = None
        self.browser = None
        self.playwright = None
        self.page = None
