#!/usr/bin/env python3
"""
Script to import Scryfall bulk data into the database.
Downloads the latest bulk data from Scryfall and imports it into PostgreSQL.
"""

import sys
import os
import json
import gzip
import requests
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add parent directory to path to import our app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.models.card import ScryfallCard

@dataclass
class BulkDataInfo:
    """Information about a Scryfall bulk data file"""
    type: str
    name: str
    description: str
    download_uri: str
    updated_at: str
    size: int
    content_type: str
    content_encoding: str

class ScryfallImporter:
    """Handles importing Scryfall bulk data into the database"""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create database tables"""
        print("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        print("Database tables created.")

    def get_bulk_data_info(self) -> Dict[str, BulkDataInfo]:
        """Fetch information about available bulk data files from Scryfall API"""
        print("Fetching bulk data information from Scryfall...")

        response = requests.get("https://api.scryfall.com/bulk-data")
        response.raise_for_status()

        bulk_data = {}
        for item in response.json()["data"]:
            bulk_data[item["type"]] = BulkDataInfo(
                type=item["type"],
                name=item["name"],
                description=item["description"],
                download_uri=item["download_uri"],
                updated_at=item["updated_at"],
                size=item["size"],
                content_type=item["content_type"],
                content_encoding=item["content_encoding"]
            )

        return bulk_data

    def download_bulk_data(self, bulk_info: BulkDataInfo, output_path: Path) -> Path:
        """Download bulk data file"""
        print(f"Downloading {bulk_info.name} from {bulk_info.download_uri}")
        print(f"File size: {bulk_info.size / 1024 / 1024:.1f} MB")

        response = requests.get(bulk_info.download_uri, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded to {output_path}")
        return output_path

    def process_card_data(self, card_data: Dict[str, Any]) -> Optional[ScryfallCard]:
        """Convert Scryfall card data to our database model"""
        try:
            # Parse date
            released_at = None
            if card_data.get("released_at"):
                released_at = datetime.strptime(card_data["released_at"], "%Y-%m-%d").date()

            # Create card object
            card = ScryfallCard(
                id=card_data["id"],
                oracle_id=card_data.get("oracle_id"),
                name=card_data["name"],
                released_at=released_at,
                set=card_data.get("set"),
                set_name=card_data.get("set_name"),
                collector_number=card_data.get("collector_number"),
                lang=card_data.get("lang"),
                cmc=card_data.get("cmc"),
                type_line=card_data.get("type_line"),
                oracle_text=card_data.get("oracle_text"),
                colors=card_data.get("colors"),
                color_identity=card_data.get("color_identity", []),
                keywords=card_data.get("keywords"),
                legalities=card_data.get("legalities", {}),
                image_uris=card_data.get("image_uris"),
                card_faces=card_data.get("card_faces"),
                prices=card_data.get("prices"),
                edhrec_rank=card_data.get("edhrec_rank"),
                data=card_data  # Store full Scryfall data
            )

            return card

        except Exception as e:
            print(f"Error processing card {card_data.get('name', 'Unknown')}: {e}")
            return None

    def import_cards(self, file_path: Path, batch_size: int = 1000) -> int:
        """Import cards from a bulk data file"""
        print(f"Importing cards from {file_path}")

        imported_count = 0
        batch = []

        # Clear existing data
        with self.SessionLocal() as db:
            print("Clearing existing card data...")
            db.execute(text("TRUNCATE TABLE scryfall_cards CASCADE"))
            db.commit()

        # Import new data - check if file is actually gzipped
        try:
            # Try to open as gzipped file first
            f = gzip.open(file_path, 'rt', encoding='utf-8')
            f.read(1)  # Try to read one byte to test if it's gzipped
            f.seek(0)  # Reset to beginning
        except (OSError, gzip.BadGzipFile):
            # If not gzipped, open as regular file
            f = open(file_path, 'r', encoding='utf-8')
        
        try:
            # Read the entire file as a single JSON array
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Expected JSON array")
            
            for line_num, card_data in enumerate(data, 1):
                try:
                    card = self.process_card_data(card_data)

                    if card:
                        batch.append(card)

                    # Process batch
                    if len(batch) >= batch_size:
                        self._insert_batch(batch)
                        imported_count += len(batch)
                        batch = []

                        if imported_count % 10000 == 0:
                            print(f"Imported {imported_count} cards...")

                except Exception as e:
                    print(f"Error on line {line_num}: {e}")
                    continue

            # Process remaining batch
            if batch:
                self._insert_batch(batch)
                imported_count += len(batch)

            print(f"Successfully imported {imported_count} cards")
            return imported_count
        finally:
            f.close()

    def _insert_batch(self, cards):
        """Insert a batch of cards into the database"""
        with self.SessionLocal() as db:
            try:
                db.add_all(cards)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error inserting batch: {e}")
                raise

    def create_indexes(self):
        """Create database indexes for performance"""
        print("Creating database indexes...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_cards_name_trgm ON scryfall_cards USING gin (name gin_trgm_ops)",
            "CREATE INDEX IF NOT EXISTS idx_cards_oracle_text_gin ON scryfall_cards USING gin (to_tsvector('english', coalesce(oracle_text,'')))",
            "CREATE INDEX IF NOT EXISTS idx_cards_color_identity ON scryfall_cards USING gin (color_identity)",
            "CREATE INDEX IF NOT EXISTS idx_cards_type_line ON scryfall_cards USING gin (to_tsvector('english', coalesce(type_line,'')))",
            "CREATE INDEX IF NOT EXISTS idx_cards_legalities ON scryfall_cards USING gin ((legalities::jsonb) jsonb_ops)",
        ]

        with self.engine.connect() as conn:
            for index_sql in indexes:
                try:
                    print(f"Creating index: {index_sql[:50]}...")
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    print(f"Error creating index: {e}")

def main():
    """Main import function"""
    print("Starting Scryfall data import...")
    print(f"Database URL: {settings.DATABASE_URL}")

    importer = ScryfallImporter(settings.DATABASE_URL)

    try:
        # Create tables
        importer.create_tables()

        # Get bulk data info
        bulk_data = importer.get_bulk_data_info()

        # We want the "default_cards" bulk data
        if "default_cards" not in bulk_data:
            print("Error: default_cards bulk data not found")
            return 1

        default_cards_info = bulk_data["default_cards"]
        print(f"Found bulk data: {default_cards_info.name}")
        print(f"Description: {default_cards_info.description}")
        print(f"Updated: {default_cards_info.updated_at}")

        # Download data
        data_dir = Path(__file__).parent / "data"
        data_dir.mkdir(exist_ok=True)

        download_path = data_dir / "default_cards.json.gz"
        importer.download_bulk_data(default_cards_info, download_path)

        # Import data
        imported_count = importer.import_cards(download_path)

        # Create indexes
        importer.create_indexes()

        # Cleanup
        # download_path.unlink()  # Commented out to examine file format

        print(f"Import completed successfully! Imported {imported_count} cards.")
        return 0

    except Exception as e:
        print(f"Import failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())