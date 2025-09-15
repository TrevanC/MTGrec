from pydantic import BaseModel
from typing import Optional

class ApiError(BaseModel):
    error: dict[str, str]

class HealthResponse(BaseModel):
    status: str

class VersionResponse(BaseModel):
    version: str
    git_sha: Optional[str] = None
    build_date: Optional[str] = None

class FeedbackRequest(BaseModel):
    card_id: str
    action: str  # 'clicked', 'added', 'hidden', 'purchased'

class FeedbackResponse(BaseModel):
    ok: bool