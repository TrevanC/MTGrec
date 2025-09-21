from typing import List, Optional
from pydantic_settings import BaseSettings
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MTG EDH Recommender"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/mtg_recommender"
    )

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Development
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Inference Recommender Configuration
    DATASET_PATH: str = os.getenv(
        "DATASET_PATH",
        str(Path(__file__).parent.parent.parent / "data" / "processed" / "compact_dataset.json.gz")
    )
    SIMILARITY_MODEL_PATH: str = os.getenv(
        "SIMILARITY_MODEL_PATH", 
        str(Path(__file__).parent.parent.parent / "data" / "processed" / "similarity_model.pkl")
    )

    class Config:
        case_sensitive = True

settings = Settings()