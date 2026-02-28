"""
Quest model and quest definitions for Legend of Dragon's Legacy.

Quests are defined statically in QUEST_DEFINITIONS. Player progress is tracked
in the CharacterQuest database table.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dragons_legacy.database import Base
from typing import Dict, List, Any


class CharacterQuest(Base):
    """Tracks a character's progress on a quest."""
    __tablename__ = "character_quests"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    quest_id = Column(String(50), nullable=False)  # references QUEST_DEFINITIONS key
    status = Column(String(20), nullable=False, default="active")  # active, completed
    progress = Column(Integer, default=0)  # e.g. number of mobs killed
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    character = relationship("Character")

    def __repr__(self):
        return (
            "<CharacterQuest(id=" + str(self.id)
            + ", character_id=" + str(self.character_id)
            + ", quest_id='" + str(self.quest_id)
            + "', status='" + str(self.status)
            + "', progress=" + str(self.progress) + ")>"
        )


# ============================================================
# QUEST DEFINITIONS (static data)
# ============================================================

QUEST_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "krets_hunt": {
        "id": "krets_hunt",
        "name": "Krets Infestation",
        "level": 1,
        "quest_giver_npc": "Elder Mirwen",
        "quest_giver_region": "Settlement of Klesva",
        "turn_in_npc": "Captain Roderick",
        "turn_in_region": "Baurwill Town",
        "description": (
            "Elder Mirwen has asked you to help protect the settlement. "
            "Dangerous Krets have been spotted nearby and threaten the villagers. "
            "Kill 10 Krets and report to Captain Roderick in Baurwill Town."
        ),
        "objective_type": "kill",  # "kill" type quest
        "objective_target": "Krets",  # mob name to kill
        "objective_count": 10,  # number to kill
        "objective_text": "Kill 10 Krets",
        "rewards": {
            "copper": 11000,  # 1 gold 10 silver = 10000 + 1000
            "items": [
                # (item_name, quantity) — will be resolved to catalog IDs at reward time
                ("HP Potion", 10),
                ("Power Potion", 10),
                ("Leather Armor", 1),
                ("Leather Cuirass", 1),
            ],
        },
        "reward_text": "1 Gold 10 Silver, 10x HP Potion, 10x Power Potion, Leather Armor, Leather Cuirass",
    },
}


def get_quests_for_npc(npc_name: str) -> List[Dict[str, Any]]:
    """Return quest definitions available from a specific NPC."""
    return [q for q in QUEST_DEFINITIONS.values() if q["quest_giver_npc"] == npc_name]


def get_turn_in_quests_for_npc(npc_name: str) -> List[Dict[str, Any]]:
    """Return quest definitions that can be turned in to a specific NPC."""
    return [q for q in QUEST_DEFINITIONS.values() if q["turn_in_npc"] == npc_name]
