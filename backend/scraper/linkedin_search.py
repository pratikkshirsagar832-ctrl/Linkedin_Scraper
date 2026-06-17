from urllib.parse import quote
import asyncio
import json
import uuid
from pathlib import Path
from json import load

from scrapling.fetchers.stealth_chrome import AsyncStealthySession
from scrapling.parser import Selector
from openai import OpenAI
from models.lead import Lead
from core.config import settings


TIME_FILTER_MAP = {
    "latest": "%22past-24h%22",
    "7_days": "%22past-week%22",
    "14_days": "%22past-two-weeks%22",
    "27_days": "%22r2592000%22",
    "2_months": "%22r4838400%22",
}

LINKEDIN_SEARCH_URL = "https://www.linkedin.com/search/results/content/?keywords={keyword}&sortBy=%22date%22&datePosted={time_filter}"
SESSION_FILE = Path("./sessions/linkedin_session.json")

QUERY_GEN_PROMPT = """You are a LinkedIn search query expert. Return a JSON object with key "queries" containing exactly 10 SHORT search queries (2-5 words each) that find people expressing buying intent.

CRITICAL: Queries must be SHORT (under 40 chars).

Focus on intent signals mixed with job titles:
- "looking for X"
- "need X"
- "hiring X"
- "help X"

Example for "web development":
{"queries": ["looking for web developer", "need react developer", "hiring full stack dev", "help with website", "recommendation web developer", "need ecommerce site", "looking for frontend dev", "hiring software developer", "help with web app", "recommendation for developer"]}

Generate 10 SHORT queries for the topic the user provides."""

AI_EXTRACT_PROMPT = """You are analyzing LinkedIn posts for lead generation. Determine if the poster is looking for a service or has a problem to solve.

Return JSON with key "leads" containing an array. For each lead:
- "author_name": person's name
- "post_text": main content
- "qualified": true/false
- "confidence": 0.0 to 1.0
- "reason": short explanation

LEAD = needs help, looking for, hiring, asking for recommendations, complaining about a problem
NOT = generic, promotion, news, offering services

Posts:"""


SAMESITE_MAP = {"no_restriction": "None", "unspecified": "Lax", "none": "None", "lax": "Lax", "strict": "Strict"}

def _sanitize_samesite(cookies: list[dict]) -> list[dict]:
    for c in cookies:
        ss = c.get("sameSite", "")
        if ss and ss.lower() in SAMESITE_MAP:
            c["sameSite"] = SAMESITE_MAP[ss.lower()]
        elif not ss or ss.lower() not in ("lax", "strict", "none"):
            c["sameSite"] = "Lax"
    return cookies

def _load_session_cookies() -> list[dict] | None:
    if not SESSION_FILE.exists():
        return None
    try:
        with open(SESSION_FILE) as f:
            data = load(f)
            raw = data.get("cookies", [])
            linkedin = [c for c in raw if "linkedin" in c.get("domain", "").lower()]
            if not linkedin:
                return None
            allowed = {"name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"}
            return _sanitize_samesite([{k: v for k, v in c.items() if k in allowed and v is not None} for c in linkedin])
    except Exception as e:
        print(f"Cookie error: {e}")
        return None


def _extract_posts_from_dom(html: str) -> list[dict]:
    """Extract posts from rendered HTML. Always returns author_profile from DOM /in/ links."""
    posts = []
    if not html:
        return posts
    sel = Selector(content=html)
    items = sel.css('div[role="listitem"]')
    if not items or len(items) == 0:
        items = sel.css('div.feed-shared-update-v2, li.search-result, article.search-result')
    for item in items:
        try:
            text = item.get_all_text(strip=True)
            if not text or len(text) < 30:
                continue
            profile_link = ""
            link_el = item.css('a[href*="/in/"]').first
            if link_el:
                href = link_el.attrib.get("href", "")
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.linkedin.com" + href
                profile_link = href

            # Try to get author name from near the profile link
            author_name = "LinkedIn User"
            if profile_link:
                name_tag = item.css('span[dir="ltr"]').first
                if name_tag:
                    name_text = name_tag.get_all_text(strip=True)
                    if name_text and len(name_text) < 60:
                        author_name = name_text

            posts.append({
                "author_name": author_name,
                "author_profile": profile_link,
                "raw_text": text,
            })
        except Exception:
            continue
    return posts


class SearchSession:
    def __init__(self, session_id: str, topic: str, queries: list[str], time_filter: str):
        self.session_id = session_id
        self.topic = topic
        self.queries = queries
        self.time_filter = time_filter
        self.current_query_index = 0
        self.cache = {}
        self.offsets = {}
        self.exhausted = False

    def get_next_batch(self) -> list[Lead] | None:
        idx = self.current_query_index
        if idx not in self.cache:
            return None
        cached = self.cache[idx]
        offset = self.offsets.get(idx, 0)
        if offset >= len(cached):
            return None
        batch = cached[offset:offset + 10]
        self.offsets[idx] = offset + len(batch)
        return batch

    def store_results(self, leads: list[Lead]):
        idx = self.current_query_index
        sorted_leads = sorted(leads, key=lambda x: x.intent_score, reverse=True)[:20]
        self.cache[idx] = sorted_leads
        self.offsets[idx] = 0

    def advance_query(self):
        self.current_query_index += 1
        if self.current_query_index >= len(self.queries):
            self.exhausted = True
            return None
        return self.queries[self.current_query_index]


class LinkedInSearchEngine:
    def __init__(self, timeout: int = 60000, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = None
        self._ai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self._warmed = False
        self._sessions: dict[str, SearchSession] = {}

    async def _get_session(self) -> AsyncStealthySession:
        if self._session is None:
            cookies = _load_session_cookies()
            self._session = AsyncStealthySession(
                headless=True,
                block_ads=True,
                disable_resources=True,
                cookies=cookies,
                timeout=self.timeout,
                solve_cloudflare=True,
            )
            await self._session.start()
        return self._session

    def _build_url(self, keyword: str, time_filter: str) -> str:
        tf = TIME_FILTER_MAP.get(time_filter, TIME_FILTER_MAP["latest"])
        return LINKEDIN_SEARCH_URL.format(keyword=quote(keyword), time_filter=tf)

    async def generate_queries(self, topic: str) -> list[str]:
        if not self._ai_client:
            return [topic] * 10
        try:
            loop = asyncio.get_event_loop()
            def call():
                return self._ai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": QUERY_GEN_PROMPT},
                        {"role": "user", "content": f"Generate 10 intent-based LinkedIn search queries for: {topic}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
            resp = await loop.run_in_executor(None, call)
            result = json.loads(resp.choices[0].message.content)
            if isinstance(result, list):
                queries = result
            elif isinstance(result, dict) and result.get("queries"):
                queries = result["queries"]
            elif isinstance(result, dict) and result.get("results"):
                queries = result["results"]
            else:
                queries = []
            queries = [str(q).strip() for q in queries if q and str(q).strip()]
            seen = set()
            unique = []
            for q in queries:
                key = q.lower().strip()
                if key not in seen:
                    seen.add(key)
                    unique.append(q)
                    if len(unique) == 10:
                        break
            print(f"Generated {len(unique)} intent queries for '{topic}'")
            if unique:
                return unique
        except Exception as e:
            print(f"Query gen error: {e}")
        return [topic] * 10

    async def _extract_post_urls_js(self, page) -> list[dict]:
        """Run JS in browser to extract real post URLs from data-urn attributes."""
        try:
            urls = await page.evaluate(r"""() => {
                const results = [];
                const seen = new Set();
                const walker = document.createTreeWalker(document.body, 1, null, false);
                while (walker.nextNode()) {
                    const el = walker.currentNode;
                    const attr = el.getAttribute('data-urn') || el.getAttribute('data-id') || '';
                    const m = attr.match(/urn:li:activity:(\d+)/);
                    if (m && !seen.has(m[0])) {
                        seen.add(m[0]);
                        results.push('https://www.linkedin.com/feed/update/' + m[0] + '/');
                    }
                }
                return results;
            }""")
            return urls if isinstance(urls, list) else []
        except Exception as e:
            print(f"  JS post URL error: {e}")
            return []

    async def scrape_query(self, query: str, time_filter: str) -> list[dict]:
        """Scrape LinkedIn. DOM extraction + JS page_action for real post URLs."""
        url = self._build_url(query, time_filter)
        print(f"\n--- Scraping: {url}")

        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                collected_urls = []

                async def page_action(page, html=None):
                    urls = await self._extract_post_urls_js(page)
                    collected_urls.extend(urls)

                result = await session.fetch(
                    url,
                    load_dom=True,
                    network_idle=False,
                    wait=8000,
                    page_action=page_action,
                )

                if not result or result.status >= 400:
                    print(f"  HTTP {result.status if result else 'None'}")
                    await asyncio.sleep(2)
                    continue

                final_url = result.url.lower() if hasattr(result, 'url') else ""
                if "login" in final_url or "/auth/" in final_url:
                    print(f"  Redirected to login!")
                    await self._cleanup()
                    return []

                html = result.html_content if hasattr(result, 'html_content') else result.body.decode()
                print(f"  Got {len(html)} bytes HTML")

                raw = _extract_posts_from_dom(html)
                print(f"  DOM extracted {len(raw)} posts")
                print(f"  JS extracted {len(collected_urls)} post URLs")

                # Merge post URLs into raw_posts by position
                for i, rp in enumerate(raw):
                    if i < len(collected_urls) and collected_urls[i]:
                        rp["post_url"] = collected_urls[i]
                    else:
                        rp["post_url"] = ""

                return raw

            except Exception as e:
                print(f"  Attempt {attempt + 1} error: {e}")
                import traceback
                traceback.print_exc()
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(3)
                else:
                    return []
        return []

    async def _ai_extract(self, raw_posts: list[dict], query: str) -> list[Lead]:
        """Score posts with DeepSeek in parallel batches. Merge profile URLs from raw_posts by author_name."""
        if not raw_posts:
            return []
        if not self._ai_client:
            return [Lead(
                keyword=query, post_url="",
                post_text=p.get("raw_text", "")[:1000],
                author_name=p.get("author_name", "LinkedIn User"),
                author_profile=p.get("author_profile", ""),
                intent_score=0.5
            ) for p in raw_posts[:20]]

        leads = []
        batch_size = 10
        sem = asyncio.Semaphore(3)

        async def process_batch(batch: list[dict]) -> list[Lead]:
            async with sem:
                texts = "\n---\n".join(f"POST {i+1}: {p.get('raw_text','')[:2000]}" for i,p in enumerate(batch))
                try:
                    loop = asyncio.get_event_loop()
                    def call():
                        return self._ai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": AI_EXTRACT_PROMPT},
                                {"role": "user", "content": f"Find leads in these posts related to '{query}':\n\n{texts}"}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.1,
                        )
                    resp = await loop.run_in_executor(None, call)
                    content = resp.choices[0].message.content
                    result = json.loads(content)
                    if isinstance(result, list):
                        items = result
                    elif isinstance(result, dict) and result.get("leads"):
                        items = result["leads"]
                    elif isinstance(result, dict) and result.get("results"):
                        items = result["results"]
                    else:
                        items = [result]
                    if isinstance(items, dict):
                        items = [items]
                    results = []
                    for item in items:
                        if isinstance(item, dict) and item.get("post_text"):
                            confidence = float(item.get("confidence", 0.5))
                            qualified = item.get("qualified", True)
                            score = confidence if qualified else max(0.1, confidence * 0.5)
                            if score > 0.1:
                                results.append({
                                    "author_name": item.get("author_name", "LinkedIn User"),
                                    "post_text": item.get("post_text", "")[:2000],
                                    "score": score,
                                    "reason": item.get("reason", ""),
                                })
                    return results
                except Exception as e:
                    print(f"  Batch AI error: {e}")
                    return []

        # Run batches in parallel
        tasks = [process_batch(raw_posts[i:i+batch_size]) for i in range(0, len(raw_posts), batch_size)]
        batch_results = await asyncio.gather(*tasks)
        scored = []
        for br in batch_results:
            scored.extend(br)

        # Merge scored leads with raw_posts by matching author_name
        for s in scored:
            name = s["author_name"].lower().strip()
            matched = None
            for rp in raw_posts:
                rp_name = rp.get("author_name", "").lower().strip()
                if rp_name and rp_name == name:
                    matched = rp
                    break
            if not matched:
                # fallback: try to find by text overlap
                for rp in raw_posts:
                    if s["post_text"][:50].lower() in rp.get("raw_text", "").lower():
                        matched = rp
                        break

            leads.append(Lead(
                keyword=query,
                post_url=matched.get("post_url", "") if matched else "",
                post_text=s["post_text"],
                author_name=s["author_name"],
                author_profile=matched.get("author_profile", "") if matched else "",
                intent_score=s["score"],
                intent_reason=s["reason"],
            ))

        # If AI returned nothing, use raw_posts as fallback
        if not leads:
            print("  AI returned 0 leads, using raw posts as fallback")
            for rp in raw_posts[:20]:
                leads.append(Lead(
                    keyword=query,
                    post_url=rp.get("post_url", ""),
                    post_text=rp.get("raw_text", "")[:1000],
                    author_name=rp.get("author_name", "LinkedIn User"),
                    author_profile=rp.get("author_profile", ""),
                    intent_score=0.3,
                    intent_reason="raw post",
                ))

        leads.sort(key=lambda x: x.intent_score, reverse=True)
        if leads:
            print(f"  Qualified {len(leads)} leads (top score: {leads[0].intent_score:.2f} - {leads[0].author_name})")
        else:
            print("  Qualified 0 leads")
        return leads

    async def start_search(self, topic: str, time_filter: str) -> dict:
        session_id = uuid.uuid4().hex[:12]
        queries = await self.generate_queries(topic)
        print(f"\n=== Session {session_id} for '{topic}' ===")
        for i, q in enumerate(queries):
            print(f"  Q{i+1}: {q}")

        session = SearchSession(session_id, topic, queries, time_filter)
        self._sessions[session_id] = session

        raw = await self.scrape_query(queries[0], time_filter)
        leads = await self._ai_extract(raw, queries[0])
        session.store_results(leads)
        batch = session.get_next_batch()

        return {
            "session_id": session_id,
            "leads": batch or [],
            "has_more": len(leads) > 10 or len(queries) > 1,
        }

    async def load_more(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session expired", "leads": [], "has_more": False}

        batch = session.get_next_batch()
        if batch:
            return {"leads": batch, "has_more": True}

        next_query = session.advance_query()
        if next_query is None:
            return {"leads": [], "has_more": False}

        print(f"\n--- Query {session.current_query_index + 1}: '{next_query}' ---")
        raw = await self.scrape_query(next_query, session.time_filter)
        leads = await self._ai_extract(raw, next_query)
        session.store_results(leads)
        batch = session.get_next_batch()

        remaining = len(session.queries) - session.current_query_index - 1
        more_in_cache = session.offsets.get(session.current_query_index, 0) < len(session.cache.get(session.current_query_index, []))
        return {
            "leads": batch or [],
            "has_more": more_in_cache or remaining > 0,
        }

    async def _cleanup(self):
        if self._session:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None

    async def warmup(self):
        if self._warmed:
            return
        try:
            print("Pre-warming browser...")
            session = await self._get_session()
            await session.fetch("https://www.linkedin.com", load_dom=False, network_idle=False, wait=500)
            self._warmed = True
            print("Browser pre-warmed")
        except Exception as e:
            print(f"Warmup: {e}")
