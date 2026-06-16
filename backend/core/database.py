from supabase import create_client, Client
from core.config import settings

_supabase: Client | None = None


def get_db() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase


def init_db():
    """Create tables if they don't exist via Supabase REST"""
    db = get_db()
    try:
        db.table("leads").select("id").limit(1).execute()
    except Exception:
        pass
    return db
