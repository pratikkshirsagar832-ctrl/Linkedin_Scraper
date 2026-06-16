from pathlib import Path
from json import dump, load
import asyncio


class LinkedInSessionManager:
    def __init__(self, cookie_dir: str = "./sessions"):
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.cookie_dir / "linkedin_session.json"

    def save_cookies(self, cookies: list[dict]) -> None:
        with open(self.session_file, "w") as f:
            dump({"cookies": cookies}, f)

    def load_cookies(self) -> list[dict] | None:
        if not self.session_file.exists():
            return None
        with open(self.session_file) as f:
            data = load(f)
            return data.get("cookies")

    def _login_sync(self) -> bool:
        """Sync method — runs in a thread pool to avoid blocking the event loop"""
        from patchright.sync_api import sync_playwright

        print("Opening browser for LinkedIn login...")
        print("Please log in in the opened browser window (5 min timeout).")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://www.linkedin.com/login", timeout=60000)

            print("Waiting for login...")
            try:
                page.wait_for_url("https://www.linkedin.com/feed/**", timeout=300000)
                cookies = context.cookies()
                self.save_cookies([
                    {"name": c["name"], "value": c["value"], "domain": c["domain"],
                     "path": c.get("path", "/"), "httpOnly": c.get("httpOnly", False),
                     "secure": c.get("secure", False), "sameSite": c.get("sameSite", "Lax")}
                    for c in cookies
                ])
                print("Login successful! Session saved.")
                browser.close()
                return True
            except Exception as e:
                print(f"Login failed: {e}")
                browser.close()
                return False

    async def login_flow(self) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._login_sync)

    def is_logged_in(self) -> bool:
        if not self.session_file.exists():
            return False
        try:
            cookies = self.load_cookies()
            if not cookies:
                return False
            li_at = any(c.get("name") == "li_at" for c in cookies)
            return li_at
        except Exception:
            return False
