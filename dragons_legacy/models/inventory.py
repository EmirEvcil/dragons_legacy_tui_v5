"""
Inventory model for Legend of Dragon's Legacy.

Each row represents one item instance owned by a character.
The item_catalog_id references the static item catalog in item_data.py.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from dragons_legacy.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    item_catalog_id = Column(Integer, nullable=False)  # references item_data.py id
    quantity = Column(Integer, default=1)
    equipped_slot = Column(String(20), nullable=True, default=None)  # slot name if equipped
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    character = relationship("Character", back_populates="inventory_items")

    def __repr__(self):
        return (
            "<InventoryItem(id=" + str(self.id)
            + ", character_id=" + str(self.character_id)
            + ", item_catalog_id=" + str(self.item_catalog_id)
            + ", qty=" + str(self.quantity)
            + ", equipped=" + str(self.equipped_slot) + ")>"
        )