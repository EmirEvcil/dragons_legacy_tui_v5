"""
Fight statistic model for Legend of Dragon's Legacy.

Each row represents the historical record of a single fight.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dragons_legacy.database import Base


class FightStatistic(Base):
    __tablename__ = "fight_statistics"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    # Fight metadata
    fight_date = Column(DateTime(timezone=True), server_default=func.now())
    victory = Column(Boolean, nullable=False)

    # Player info at time of fight
    player_name = Column(String(50), nullable=False)
    player_level = Column(Integer, nullable=False)

    # Mob info at time of fight
    mob_name = Column(String(100), nullable=False)
    mob_level = Column(Integer, nullable=False)

    # Damage statistics
    player_damage_dealt = Column(Integer, default=0)
    player_damage_taken = Column(Integer, default=0)
    mob_damage_dealt = Column(Integer, default=0)
    mob_damage_taken = Column(Integer, default=0)

    # Rewards
    exp_gained = Column(Integer, default=0)
    loot_copper = Column(Integer, default=0)

    # Relationships
    character = relationship("Character", backref="fight_statistics")

    def __repr__(self):
        result = "Victory" if self.victory else "Defeat"
        return (
            "<FightStatistic(id=" + str(self.id)
            + ", player=" + str(self.player_name)
            + " vs " + str(self.mob_name)
            + ", " + result + ")>"
        )
