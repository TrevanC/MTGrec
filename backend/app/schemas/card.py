from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
import uuid

class ScryfallCardBase(BaseModel):
    id: str
    oracle_id: Optional[str] = None
    name: str
    released_at: Optional[date] = None
    set: Optional[str] = None
    set_name: Optional[str] = None
    collector_number: Optional[str] = None
    lang: Optional[str] = None
    cmc: Optional[float] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = None
    color_identity: List[str]
    keywords: Optional[List[str]] = None
    legalities: Dict[str, str]
    image_uris: Optional[Dict[str, str]] = None
    card_faces: Optional[List[Dict[str, Any]]] = None
    prices: Optional[Dict[str, Optional[str]]] = None
    edhrec_rank: Optional[int] = None

class ScryfallCard(ScryfallCardBase):
    """Full Scryfall card response"""
    pass

class ScryfallCardInDB(ScryfallCardBase):
    """Card as stored in database"""
    data: Dict[str, Any]  # Full Scryfall Card object

    class Config:
        from_attributes = True

class CardSearchResponse(BaseModel):
    items: List[ScryfallCard]
    next_cursor: Optional[str] = None

class CardSearchParams(BaseModel):
    q: Optional[str] = None
    types: Optional[str] = None
    color_identity: Optional[str] = None
    only_commanders: Optional[bool] = False
    limit: Optional[int] = 20
    cursor: Optional[str] = None