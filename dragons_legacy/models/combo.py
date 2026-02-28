"""
Combo model for Legend of Dragon's Legacy.

Each character has randomly generated combos that are discovered through gameplay.
Combos are generated at character creation and are unique per player.

Combo definitions:
  - Level 1 "Deep Strike": 2 consecutive attacks. Effect: Bleeding (5% max_hp every 5s for 20s).
  - Level 2 "Blood Worm": 3 consecutive attacks. Effect: 20% of damage dealt as HP lifesteal.

Attack zones: head, chest, legs
"""

import random

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from dragons_legacy.database import Base


COMBO_DEFINITIONS = {
    "deep_strike": {
        "name": "Deep Strike",
        "required_level": 1,
        "sequence_length": 2,
        "description": "A precise combination that causes deep bleeding wounds.",
        "effect": "Bleeding: enemy loses 5% of max HP every 5 seconds for 20 seconds.",
    },
    "blood_worm": {
        "name": "Blood Worm",
        "required_level": 2,
        "sequence_length": 3,
        "description": "A parasitic strike that drains the enemy's life force.",
        "effect": "Lifesteal: 20% of the damage dealt on the final hit is restored as HP.",
    },
}

ATTACK_ZONES = ["head", "chest", "legs"]

ZONE_SYMBOLS = {
    "head": "⬈",
    "chest": "⮕",
    "legs": "⬊",
}


def generate_random_combo_sequence(length: int) -> str:
    """Generate a random combo sequence of the given length.
    
    Returns a comma-separated string of zones, e.g. "head,chest" or "legs,head,chest".
    """
    zones = [random.choice(ATTACK_ZONES) for _ in range(length)]
    return ",".join(zones)


class CharacterCombo(Base):
    __tablename__ = "character_combos"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    combo_id = Column(String(50), nullable=False)  # "deep_strike" or "blood_worm"
    sequence = Column(String(100), nullable=False)  # comma-separated zones, e.g. "head,chest"
    discovered = Column(Boolean, default=False)  # Whether the player has found this combo

    # Relationships
    character = relationship("Character", back_populates="combos")

    @property
    def sequence_list(self) -> list[str]:
        """Return the sequence as a list of zone strings."""
        return self.sequence.split(",") if self.sequence else []

    def __repr__(self):
        return (
            "<CharacterCombo(id=" + str(self.id)
            + ", character_id=" + str(self.character_id)
            + ", combo=" + str(self.combo_id)
            + ", seq=" + str(self.sequence)
            + ", discovered=" + str(self.discovered) + ")>"
        )
