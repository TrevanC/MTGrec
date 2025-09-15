from sqlalchemy.orm import Session
from datetime import datetime
from app.models.stats import Interaction
import uuid

class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    async def record_interaction(self, card_id: str, action: str):
        """Record a user interaction with a card"""

        # Validate action
        valid_actions = ['clicked', 'added', 'hidden', 'purchased']
        if action not in valid_actions:
            raise ValueError(f"Invalid action: {action}")

        # Create interaction record
        interaction = Interaction(
            id=uuid.uuid4(),
            card_id=uuid.UUID(card_id),
            action=action,
            ts=datetime.now().date()
        )

        self.db.add(interaction)
        self.db.commit()

        return True