import asyncio
from curl_cffi.requests import AsyncSession
from pathlib import Path
from json import load

SESSION_FILE = Path("./sessions/linkedin_session.json")
with open(SESSION_FILE) as f:
    raw = load(f).get("cookies", [])
    linkedin = [c for c in raw if "linkedin" in c.get("domain", "").lower()]
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in linkedin)

async def main():
    async with AsyncSession(timeout=15, impersonate="chrome124") as s:
        r = await s.get(
            "https://www.linkedin.com/search/results/content/?keywords=web%20development&datePosted=past-24h&sortBy=date&page=1",
            headers={"Cookie": cookie_str, "Accept-Language": "en-US,en;q=0.9"}
        )
        html = r.text
        with open("page_sample.html", "w", encoding="utf-8") as f:
            f.write(html[:200000])
        print(f"Status: {r.status_code}, HTML len: {len(html)}")

asyncio.run(main())
