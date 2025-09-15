from fastapi import APIRouter
from app.schemas.common import HealthResponse, VersionResponse
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.get("/version", response_model=VersionResponse)
async def version():
    """Version information endpoint"""
    return {
        "version": settings.VERSION,
        "git_sha": None,  # Could be populated from build process
        "build_date": None,  # Could be populated from build process
    }