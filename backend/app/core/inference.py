"""Global InferenceRecommender instance management."""

from typing import Optional
from app.mrec.inference import InferenceRecommender

# Global InferenceRecommender instance
_inference_recommender: Optional[InferenceRecommender] = None

def set_inference_recommender(recommender: InferenceRecommender) -> None:
    """Set the global InferenceRecommender instance."""
    global _inference_recommender
    _inference_recommender = recommender

def get_inference_recommender() -> InferenceRecommender:
    """Get the global InferenceRecommender instance."""
    if _inference_recommender is None:
        raise RuntimeError("InferenceRecommender not initialized")
    return _inference_recommender

def is_inference_recommender_initialized() -> bool:
    """Check if InferenceRecommender is initialized."""
    return _inference_recommender is not None
