from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService

router = APIRouter()

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit user interaction feedback"""
    try:
        feedback_service = FeedbackService(db)
        await feedback_service.record_interaction(request.card_id, request.action)
        return {"ok": True}
    except Exception as e:
        # Don't fail the request for feedback issues
        print(f"Feedback error: {e}")
        return {"ok": False}