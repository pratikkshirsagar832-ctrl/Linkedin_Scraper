from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Lead(BaseModel):
    id: str = ""
    keyword: str
    post_url: str
    post_text: str
    author_name: str
    author_profile: str
    top_comment: Optional[str] = ""
    timestamp: str = ""
    intent_score: float = 0.0
    intent_reason: str = ""
    source: str = "linkedin"

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        if not d.get("id"):
            from uuid import uuid4
            d["id"] = uuid4().hex[:12]
        if not d.get("timestamp"):
            d["timestamp"] = datetime.utcnow().isoformat()
        return d


class SearchRequest(BaseModel):
    keyword: str
    time_filter: str = "latest"


class SearchResponse(BaseModel):
    leads: list[Lead]
    total_found: int
    session_valid: bool = True


class LoadMoreRequest(BaseModel):
    keyword: str
    time_filter: str = "latest"
    page: int = 2


class LoadMoreResponse(BaseModel):
    leads: list[Lead]
    page: int
    has_more: bool
    session_valid: bool = True
