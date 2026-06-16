import asyncio, sys
sys.path.insert(0, ".")
from scraper.linkedin_search import LinkedInSearchEngine

async def main():
    engine = LinkedInSearchEngine()
    session = await engine._get_session()
    # Get the actual rendered HTML
    result = await session.fetch(
        "https://www.linkedin.com/search/results/content/?keywords=ai%20automation&datePosted=past-24h&sortBy=date&page=1",
        load_dom=True,
        network_idle=True,
        wait=5000,
    )
    html = result.html_content if hasattr(result, 'html_content') else result.body.decode()
    with open("rendered_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {len(html)} bytes")
    await engine._cleanup()

asyncio.run(main())
