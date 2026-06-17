from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from scraper.linkedin_search import LinkedInSearchEngine
from core.database import get_db

router = APIRouter()
search_engine = LinkedInSearchEngine()


class SearchRequest(BaseModel):
    keyword: str
    time_filter: str = "latest"


class SearchResponse(BaseModel):
    leads: list[dict]
    session_id: str
    total_found: int
    session_valid: bool = True
    has_more: bool = True


class LoadMoreRequest(BaseModel):
    session_id: str


class LoadMoreResponse(BaseModel):
    leads: list[dict]
    has_more: bool
    session_valid: bool = True


def _save_leads(leads: list) -> list[dict]:
    """Convert Lead objects to dicts, save to Supabase, return serializable dicts."""
    result = []
    try:
        db = get_db()
    except Exception as e:
        print(f"DB connection error: {e}")
        db = None

    for lead in leads:
        d = lead.dict()

        # Generate a unique post_url placeholder if empty (Supabase has UNIQUE constraint)
        if not d.get("post_url"):
            d["post_url"] = f"https://linkedin.com/feed/update/activity-{uuid4().hex[:12]}/"

        result.append(d)

        # Save to Supabase: remove id (let DB auto-generate UUID) and post_url dupe handling
        if db:
            try:
                db_row = {k: v for k, v in d.items() if k != "id"}
                db.table("leads").insert(db_row).execute()
            except Exception as e:
                err_str = str(e).lower()
                if "duplicate" not in err_str and "unique" not in err_str:
                    print(f"DB insert error: {e}")

    return result


@router.post("/search")
async def search_leads(req: SearchRequest):
    try:
        result = await search_engine.start_search(req.keyword, req.time_filter)
        if result.get("error"):
            return SearchResponse(leads=[], session_id="", total_found=0, session_valid=False)

        leads_data = _save_leads(result["leads"])

        return SearchResponse(
            leads=leads_data,
            session_id=result["session_id"],
            total_found=len(leads_data),
            has_more=result["has_more"],
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-more")
async def load_more(req: LoadMoreRequest):
    try:
        result = await search_engine.load_more(req.session_id)
        if result.get("error"):
            return LoadMoreResponse(leads=[], has_more=False)

        leads_data = _save_leads(result["leads"])

        return LoadMoreResponse(
            leads=leads_data,
            has_more=result["has_more"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/status")
async def session_status():
    from scraper.session_manager import LinkedInSessionManager
    mgr = LinkedInSessionManager()
    return {
        "logged_in": mgr.is_logged_in(),
        "session_file_exists": mgr.session_file.exists(),
    }


import asyncio

_login_task = None

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/session/login")
async def session_login(req: LoginRequest):
    global _login_task
    from scraper.session_manager import LinkedInSessionManager
    mgr = LinkedInSessionManager()

    if _login_task and not _login_task.done():
        return {"success": False, "message": "Login already in progress"}

    async def run_login():
        return await mgr.login_flow(req.email, req.password)

    _login_task = asyncio.create_task(run_login())
    return {"success": True, "message": "Login started."}


class CookieImportRequest(BaseModel):
    cookies: list[dict]

SAMESITE_MAP = {"no_restriction": "None", "unspecified": "Lax", "none": "None", "lax": "Lax", "strict": "Strict"}

def _sanitize_cookies(cookies: list[dict]) -> list[dict]:
    sanitized = []
    for c in cookies:
        samesite = c.get("sameSite", "")
        if samesite and samesite.lower() in SAMESITE_MAP:
            c["sameSite"] = SAMESITE_MAP[samesite.lower()]
        elif not samesite or samesite.lower() not in ("lax", "strict", "none"):
            c["sameSite"] = "Lax"
        sanitized.append(c)
    return sanitized

@router.post("/session/import-cookies")
async def import_cookies(req: CookieImportRequest):
    from scraper.session_manager import LinkedInSessionManager
    mgr = LinkedInSessionManager()
    sanitized = _sanitize_cookies(req.cookies)
    mgr.save_cookies(sanitized)
    valid = any(c.get("name") == "li_at" for c in sanitized)
    return {"success": valid, "message": "Cookies imported." if valid else "li_at cookie not found."}


@router.get("/session/login-status")
async def session_login_status():
    global _login_task
    if not _login_task:
        return {"running": False, "done": False, "success": None}
    if _login_task.done():
        try:
            result = _login_task.result()
            return {"running": False, "done": True, "success": result}
        except Exception as e:
            return {"running": False, "done": True, "success": False, "error": str(e)}
    return {"running": True, "done": False, "success": None}


@router.get("/leads/history")
async def lead_history(limit: int = 50):
    try:
        db = get_db()
        result = db.table("leads").select("*").order("timestamp", desc=True).limit(limit).execute()
        return {"leads": result.data if result.data else []}
    except Exception as e:
        print(f"History error: {e}")
        return {"leads": []}


@router.get("/stats")
async def get_stats():
    try:
        db = get_db()
        result = db.table("leads").select("*").execute()
        all_leads = result.data if result.data else []
        keywords = {}
        for l in all_leads:
            k = l.get("keyword", "unknown")
            keywords[k] = keywords.get(k, 0) + 1
        return {
            "total_leads": len(all_leads),
            "unique_keywords": len(keywords),
            "keyword_breakdown": keywords,
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"total_leads": 0, "unique_keywords": 0, "keyword_breakdown": {}, "last_updated": datetime.utcnow().isoformat()}
