from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.inference import set_inference_recommender, get_inference_recommender
from app.mrec.inference import InferenceRecommender
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    try:
        logging.info("Initializing InferenceRecommender...")
        inference_recommender = InferenceRecommender(
            dataset_path=settings.DATASET_PATH,
            similarity_cache=settings.SIMILARITY_MODEL_PATH,
            refresh_cache=False,
            verbose=settings.DEBUG
        )
        set_inference_recommender(inference_recommender)
        logging.info("InferenceRecommender initialized successfully")
        
        # Dump initialization details in debug mode
        if settings.DEBUG:
            import json
            from datetime import datetime
            
            init_data = {
                "timestamp": datetime.now().isoformat(),
                "dataset_path": settings.DATASET_PATH,
                "similarity_model_path": settings.SIMILARITY_MODEL_PATH,
                "dataset_cards_count": len(inference_recommender.dataset.cards),
                "dataset_decks_count": len(inference_recommender.dataset.decks),
                "commander_profiles_count": len(inference_recommender.dataset.commander_profiles),
                "ban_list_count": len(inference_recommender.dataset.ban_list),
                "similarity_model_compatible": True,
                "matrix_bundle_card_totals_count": len(inference_recommender.bundle.card_totals),
                "matrix_bundle_card_index_count": len(inference_recommender.bundle.card_index)
            }
            
            # Create debug directory if it doesn't exist
            import os
            debug_dir = "debug"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            # Dump initialization data
            debug_file = os.path.join(debug_dir, f"inference_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(debug_file, 'w') as f:
                json.dump(init_data, f, indent=2, default=str)
            
            logging.info(f"InferenceRecommender debug data dumped to: {debug_file}")
            
    except Exception as e:
        logging.error(f"Failed to initialize InferenceRecommender: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        inference_recommender = get_inference_recommender()
        if inference_recommender:
            logging.info("Cleaning up InferenceRecommender...")
            set_inference_recommender(None)
            logging.info("InferenceRecommender cleaned up")
    except RuntimeError:
        # Already cleaned up or never initialized
        pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "MTG EDH Recommender API", "version": settings.VERSION}

@app.get("/health")
async def health_check():
    return {"status": "ok"}