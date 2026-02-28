"""
Character model for Legend of Dragon's Legacy
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dragons_legacy.database import Base
import enum


class Race(str, enum.Enum):
    """Available character races."""
    MAGMAR = "magmar"
    HUMAN = "human"


class Gender(str, enum.Enum):
    """Available character genders."""
    FEMALE = "female"
    MALE = "male"


# Starting maps per race
RACE_STARTING_MAP = {
    Race.HUMAN: "Settlement of Klesva",
    Race.MAGMAR: "Settlement of Klesva",  # TODO: Set Magmar starting map when implemented
}


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nickname = Column(String(12), nullable=False, unique=True, index=True)
    race = Column(String(20), nullable=False)
    gender = Column(String(10), nullable=False)
    current_map = Column(String(100), nullable=False, default="Settlement of Klesva")
    # UTC timestamp until which travel is blocked (None / past = no cooldown)
    travel_cooldown_until = Column(DateTime(timezone=True), nullable=True, default=None)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    # Currency stored as total copper (100 copper = 1 silver, 10000 copper = 1 gold)
    copper = Column(Integer, default=0)
    health = Column(Integer, default=100)
    current_hp = Column(Integer, nullable=True, default=None)  # None means full HP
    mana = Column(Integer, default=50)
    strength = Column(Integer, default=10)
    dexterity = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="characters")
    inventory_items = relationship("InventoryItem", back_populates="character", cascade="all, delete-orphan")
    bag_slots = relationship("BagSlot", back_populates="character", cascade="all, delete-orphan")
    combos = relationship("CharacterCombo", back_populates="character", cascade="all, delete-orphan")

    @property
    def cooldown_remaining(self) -> int:
        """Seconds of travel cooldown remaining. 0 if no cooldown."""
        if self.travel_cooldown_until is None:
            return 0
        now = datetime.now(timezone.utc)
        # Ensure the stored value is timezone-aware
        cd = self.travel_cooldown_until
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        remaining = (cd - now).total_seconds()
        return max(0, int(remaining))

    def __repr__(self):
        return (
            "<Character(id=" + str(self.id)
            + ", nickname='" + str(self.nickname)
            + "', race='" + str(self.race)
            + "', map='" + str(self.current_map)
            + "', level=" + str(self.level) + ")>"
        )