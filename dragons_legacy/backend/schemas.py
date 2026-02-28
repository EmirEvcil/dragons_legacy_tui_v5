"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    security_question_id: int
    security_answer: str


class UserLogin(UserBase):
    password: str


class PasswordReset(UserBase):
    security_answer: str
    new_password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    has_character: bool


class LogoutRequest(BaseModel):
    email: str


class SecurityQuestionResponse(BaseModel):
    id: int
    question_text: str
    
    class Config:
        from_attributes = True


class CharacterCreate(BaseModel):
    email: str
    nickname: str
    race: str
    gender: str

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Nickname is required")
        if len(v) > 12:
            raise ValueError("Nickname must be at most 12 characters")
        if " " in v:
            raise ValueError("Nickname must not contain spaces")
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError("Nickname must contain only letters and numbers")
        return v

    @field_validator("race")
    @classmethod
    def validate_race(cls, v: str) -> str:
        if v not in ("human",):
            raise ValueError("Only Human race is available at this time")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in ("female", "male"):
            raise ValueError("Gender must be 'female' or 'male'")
        return v


class CharacterResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    race: str
    gender: str
    current_map: str
    cooldown_remaining: int = 0
    level: int
    experience: int
    copper: int = 0
    health: int
    current_hp: Optional[int] = None  # None means full HP
    mana: int
    strength: int
    dexterity: int
    intelligence: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TravelRequest(BaseModel):
    email: str
    destination: str


class TravelResponse(BaseModel):
    message: str
    destination: str
    cooldown_seconds: int
    cooldown_remaining: int
    current_map: str


class RegionResponse(BaseModel):
    name: str
    connected_regions: list[str]


class NPCResponse(BaseModel):
    name: str
    role: str
    description: str


class ItemResponse(BaseModel):
    id: int
    name: str
    slot: str
    required_level: int
    character_class: str
    rarity: str
    color: str
    inventory_category: str = "equipment"
    damage: int = 0
    defense: int = 0
    hp_bonus: int = 0
    mana_bonus: int = 0
    crit_chance: int = 0
    evasion: int = 0
    block_chance: int = 0
    damage_reduction: int = 0
    description: str = ""


class InventoryItemResponse(BaseModel):
    """An item instance in the player's inventory (DB row + catalog data merged)."""
    instance_id: int  # DB primary key — unique per instance
    item_catalog_id: int
    quantity: int
    equipped_slot: Optional[str] = None  # slot name if equipped
    # Catalog fields merged in
    name: str
    slot: str
    required_level: int
    character_class: str
    rarity: str
    color: str
    inventory_category: str = "equipment"
    damage: int = 0
    defense: int = 0
    hp_bonus: int = 0
    mana_bonus: int = 0
    crit_chance: int = 0
    evasion: int = 0
    block_chance: int = 0
    damage_reduction: int = 0
    description: str = ""


class EquipItemRequest(BaseModel):
    email: str
    instance_id: int


class UnequipItemRequest(BaseModel):
    email: str
    instance_id: int


class AddInventoryItemRequest(BaseModel):
    email: str
    item_catalog_id: int


class DeleteInventoryItemRequest(BaseModel):
    email: str
    instance_id: int


class MobResponse(BaseModel):
    """Mob data for the hunt panel."""
    name: str
    level: int
    display_name: str
    max_hp: int
    damage_min: int
    damage_max: int


class StartFightRequest(BaseModel):
    """Request to start a fight via WebSocket."""
    email: str
    mob_name: str


class CharacterStatsResponse(BaseModel):
    """Character stats with base values and item bonuses."""
    # Base stats (from character level)
    base_health: int
    base_mana: int
    base_strength: int
    base_dexterity: int
    base_intelligence: int
    
    # Bonus stats (from equipped items)
    bonus_health: int
    bonus_mana: int
    bonus_strength: int
    bonus_dexterity: int
    bonus_intelligence: int
    
    # Total stats (base + bonus)
    total_health: int
    total_mana: int
    total_strength: int
    total_dexterity: int
    total_intelligence: int
    
    # Other combat stats from items
    damage: int
    defense: int
    crit_chance: int
    evasion: int
    block_chance: int
    damage_reduction: int