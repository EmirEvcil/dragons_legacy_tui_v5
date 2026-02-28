"""
Main FastAPI application for Legend of Dragon's Legacy
"""

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
import json
import random
import asyncio
import uuid

from dragons_legacy.database import get_database, init_database
from dragons_legacy.models.user import User
from dragons_legacy.models.security_question import SecurityQuestion, PREDEFINED_SECURITY_QUESTIONS
from dragons_legacy.utils.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user_by_email,
    verify_security_answer
)
from dragons_legacy.models.character import Character, RACE_STARTING_MAP, Race
from dragons_legacy.models.world_data import (
    get_connected_regions,
    is_valid_travel,
    get_travel_time,
    get_npcs_for_region,
    get_mobs_for_region,
    HUMAN_MAP_GRAPH,
    MOB_DEFINITIONS,
    format_currency_plain,
    exp_required_for_level,
    calculate_level_penalty,
)
from dragons_legacy.models.item_data import get_all_items, ITEMS_BY_ID
from dragons_legacy.models.inventory import InventoryItem
from dragons_legacy.models.fight_statistic import FightStatistic
from dragons_legacy.models.bag import BagSlot, BAG_SLOT_MAX, BAG_SLOT_COUNT, BAG_MOROK_SLOT_INDEX, BAG_MOROK_MAX
from dragons_legacy.models.combo import CharacterCombo, COMBO_DEFINITIONS, generate_random_combo_sequence, ZONE_SYMBOLS
from dragons_legacy.backend.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    SecurityQuestionResponse,
    PasswordReset,
    CharacterCreate,
    CharacterResponse,
    TravelRequest,
    TravelResponse,
    RegionResponse,
    NPCResponse,
    ItemResponse,
    InventoryItemResponse,
    AddInventoryItemRequest,
    DeleteInventoryItemRequest,
    EquipItemRequest,
    UnequipItemRequest,
    LogoutRequest,
    MobResponse,
)

app = FastAPI(title="Legend of Dragon's Legacy API", version="0.1.0")
security = HTTPBearer()

# Stat growth per level (base values at level 1)
BASE_STATS = {
    "health": 100,
    "mana": 50,
    "strength": 10,
    "dexterity": 10,
    "intelligence": 10,
}

# Stat increase per level (moderate growth)
STAT_GROWTH_PER_LEVEL = {
    "health": 10,  # +10 HP per level
    "mana": 5,     # +5 Mana per level
    "strength": 2,  # +2 Str per level
    "dexterity": 2, # +2 Dex per level
    "intelligence": 2, # +2 Int per level
}


def calculate_character_stats(character, equipped_items: list) -> dict:
    """Calculate character stats including base stats + level bonuses + item bonuses + set bonuses.
    
    Args:
        character: Character model instance
        equipped_items: List of equipped InventoryItem instances
    
    Returns:
        Dict with base_stats, bonus_stats, total_stats, combat_stats, and set_bonus
    """
    level = character.level
    
    # Calculate base stats from level
    base_health = BASE_STATS["health"] + (STAT_GROWTH_PER_LEVEL["health"] * (level - 1))
    base_mana = BASE_STATS["mana"] + (STAT_GROWTH_PER_LEVEL["mana"] * (level - 1))
    base_strength = BASE_STATS["strength"] + (STAT_GROWTH_PER_LEVEL["strength"] * (level - 1))
    base_dexterity = BASE_STATS["dexterity"] + (STAT_GROWTH_PER_LEVEL["dexterity"] * (level - 1))
    base_intelligence = BASE_STATS["intelligence"] + (STAT_GROWTH_PER_LEVEL["intelligence"] * (level - 1))
    
    # Calculate bonuses from equipped items
    bonus_health = 0
    bonus_mana = 0
    bonus_strength = 0
    bonus_dexterity = 0
    bonus_intelligence = 0
    damage = 0
    defense = 0
    crit_chance = 0
    evasion = 0
    block_chance = 0
    damage_reduction = 0
    
    # Track set pieces for set bonuses
    set_counts = {}  # {(set_name, rarity): count}
    
    for item in equipped_items:
        catalog = ITEMS_BY_ID.get(item.item_catalog_id, {})
        bonus_health += catalog.get("hp_bonus", 0)
        bonus_mana += catalog.get("mana_bonus", 0)
        damage += catalog.get("damage", 0)
        defense += catalog.get("defense", 0)
        crit_chance += catalog.get("crit_chance", 0)
        evasion += catalog.get("evasion", 0)
        block_chance += catalog.get("block_chance", 0)
        damage_reduction += catalog.get("damage_reduction", 0)
        
        # Track set pieces
        item_name = catalog.get("name", "")
        rarity = catalog.get("rarity", "")
        character_class = catalog.get("character_class", "")
        
        # Extract set name from item name (e.g., "Executioner Cuirass" -> "Executioner")
        set_name = None
        if "Executioner" in item_name:
            set_name = "Executioner"
        elif "Twilight" in item_name:
            set_name = "Twilight"
        elif "Mammoth" in item_name:
            set_name = "Mammoth"
        elif "Anger" in item_name and "Mysterious" not in item_name:
            set_name = "Anger"
        elif "North Wind" in item_name and "Mysterious" not in item_name:
            set_name = "North Wind"
        elif "Giant Slayer" in item_name and "Mysterious" not in item_name:
            set_name = "Giant Slayer"
        elif "Mysterious Anger" in item_name:
            set_name = "Mysterious Anger"
        elif "Mysterious North Wind" in item_name:
            set_name = "Mysterious North Wind"
        elif "Mysterious Giant Slayer" in item_name:
            set_name = "Mysterious Giant Slayer"
        
        if set_name and rarity in ("uncommon", "rare", "epic"):
            key = (set_name, rarity, character_class)
            set_counts[key] = set_counts.get(key, 0) + 1
    
    # Calculate set bonuses (full set = 7 pieces: weapon(s), cuirass, armor, shirt, boots, shoulder, helmet)
    set_bonus = None
    for (set_name, rarity, character_class), count in set_counts.items():
        if count >= 7:  # Full set bonus
            set_bonus = calculate_set_bonus(set_name, rarity, character_class)
            # Apply set bonus to stats
            if set_bonus:
                bonus_health += set_bonus.get("hp_bonus", 0)
                bonus_mana += set_bonus.get("mana_bonus", 0)
                bonus_strength += set_bonus.get("strength", 0)
                bonus_dexterity += set_bonus.get("dexterity", 0)
                bonus_intelligence += set_bonus.get("intelligence", 0)
                damage += set_bonus.get("damage", 0)
                defense += set_bonus.get("defense", 0)
                crit_chance += set_bonus.get("crit_chance", 0)
                evasion += set_bonus.get("evasion", 0)
                block_chance += set_bonus.get("block_chance", 0)
                damage_reduction += set_bonus.get("damage_reduction", 0)
            break  # Only apply one set bonus (highest rarity preferably)
    
    return {
        "base_stats": {
            "health": base_health,
            "mana": base_mana,
            "strength": base_strength,
            "dexterity": base_dexterity,
            "intelligence": base_intelligence,
        },
        "bonus_stats": {
            "health": bonus_health,
            "mana": bonus_mana,
            "strength": bonus_strength,
            "dexterity": bonus_dexterity,
            "intelligence": bonus_intelligence,
        },
        "total_stats": {
            "health": base_health + bonus_health,
            "mana": base_mana + bonus_mana,
            "strength": base_strength + bonus_strength,
            "dexterity": base_dexterity + bonus_dexterity,
            "intelligence": base_intelligence + bonus_intelligence,
        },
        "combat_stats": {
            "damage": damage,
            "defense": defense,
            "crit_chance": crit_chance,
            "evasion": evasion,
            "block_chance": block_chance,
            "damage_reduction": damage_reduction,
        },
        "set_bonus": set_bonus
    }


def calculate_set_bonus(set_name: str, rarity: str, character_class: str) -> dict:
    """Calculate set bonus for a full set (7 pieces equipped).
    
    Set bonuses are class-appropriate:
    - Bonecrusher: High crit, damage focused
    - Skirmisher: Evasion, balanced stats
    - Heavyweight: Block chance, defense, HP
    """
    # Green (Uncommon) bonuses
    green_bonuses = {
        "Executioner": {  # Bonecrusher
            "crit_chance": 5,
            "damage": 10,
            "description": "+5% Crit Chance, +10 Damage"
        },
        "Twilight": {  # Skirmisher
            "evasion": 5,
            "crit_chance": 3,
            "description": "+5% Evasion, +3% Crit Chance"
        },
        "Mammoth": {  # Heavyweight
            "block_chance": 5,
            "hp_bonus": 50,
            "description": "+5% Block Chance, +50 HP"
        },
    }
    
    # Blue (Rare) bonuses
    blue_bonuses = {
        "Anger": {  # Bonecrusher
            "crit_chance": 8,
            "damage": 20,
            "strength": 5,
            "description": "+8% Crit Chance, +20 Damage, +5 Strength"
        },
        "North Wind": {  # Skirmisher
            "evasion": 8,
            "dexterity": 5,
            "crit_chance": 5,
            "description": "+8% Evasion, +5 Dexterity, +5% Crit Chance"
        },
        "Giant Slayer": {  # Heavyweight
            "block_chance": 8,
            "damage_reduction": 5,
            "hp_bonus": 100,
            "description": "+8% Block Chance, +5% Damage Reduction, +100 HP"
        },
    }
    
    # Purple (Epic) bonuses
    purple_bonuses = {
        "Mysterious Anger": {  # Bonecrusher
            "crit_chance": 12,
            "damage": 35,
            "strength": 10,
            "hp_bonus": 50,
            "description": "+12% Crit Chance, +35 Damage, +10 Strength, +50 HP"
        },
        "Mysterious North Wind": {  # Skirmisher
            "evasion": 12,
            "dexterity": 10,
            "crit_chance": 8,
            "damage": 15,
            "description": "+12% Evasion, +10 Dexterity, +8% Crit Chance, +15 Damage"
        },
        "Mysterious Giant Slayer": {  # Heavyweight
            "block_chance": 12,
            "damage_reduction": 8,
            "hp_bonus": 150,
            "defense": 20,
            "description": "+12% Block Chance, +8% Damage Reduction, +150 HP, +20 Defense"
        },
    }
    
    if rarity == "uncommon":
        return green_bonuses.get(set_name, {})
    elif rarity == "rare":
        return blue_bonuses.get(set_name, {})
    elif rarity == "epic":
        return purple_bonuses.get(set_name, {})
    
    return {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        for nickname, connections in list(self.user_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.user_connections[nickname]

    def register_user(self, nickname: str, websocket: WebSocket):
        if nickname not in self.user_connections:
            self.user_connections[nickname] = []
        if websocket not in self.user_connections[nickname]:
            self.user_connections[nickname].append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_to_users(self, message: str, nicknames: List[str]):
        for nickname in nicknames:
            for ws in self.user_connections.get(nickname, []):
                await ws.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Online players tracking: {email: {"nickname": str, "level": int, "map": str, "last_seen": datetime}}
online_players: Dict[str, dict] = {}


def update_online_player(email: str, nickname: str, level: int, current_map: str):
    """Update or add a player to the online players list."""
    from datetime import datetime, timezone
    online_players[email] = {
        "nickname": nickname,
        "level": level,
        "map": current_map,
        "last_seen": datetime.now(timezone.utc)
    }


def remove_online_player(email: str):
    """Remove a player from the online players list."""
    if email in online_players:
        del online_players[email]


def get_players_on_map(map_name: str) -> List[dict]:
    """Get list of players on a specific map."""
    from datetime import datetime, timezone
    current_time = datetime.now(timezone.utc)
    players = []
    for email, data in online_players.items():
        # Only include players who have been active in the last 5 minutes
        if data["map"] == map_name and (current_time - data["last_seen"]).total_seconds() < 300:
            players.append({
                "email": email,
                "nickname": data["nickname"],
                "level": data["level"]
            })
    return sorted(players, key=lambda p: p["nickname"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_database()
    
    # Initialize security questions if they don't exist
    async for db in get_database():
        result = await db.execute(select(SecurityQuestion))
        existing_questions = result.scalars().all()
        
        if not existing_questions:
            for question_text in PREDEFINED_SECURITY_QUESTIONS:
                question = SecurityQuestion(question_text=question_text)
                db.add(question)
            await db.commit()
        break


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Legend of Dragon's Legacy API"}


@app.get("/security-questions", response_model=List[SecurityQuestionResponse])
async def get_security_questions(db: AsyncSession = Depends(get_database)):
    """Get all available security questions."""
    result = await db.execute(select(SecurityQuestion).where(SecurityQuestion.is_active == True))
    questions = result.scalars().all()
    return questions


@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_database)):
    """Register a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verify security question exists
    result = await db.execute(
        select(SecurityQuestion).where(SecurityQuestion.id == user_data.security_question_id)
    )
    security_question = result.scalar_one_or_none()
    if not security_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid security question"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    hashed_answer = get_password_hash(user_data.security_answer.lower().strip())
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        security_question_id=user_data.security_question_id,
        security_answer_hash=hashed_answer
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=Token)
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_database)):
    """Authenticate user and return access token."""
    user = await authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user already has a character
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()

    user.is_active = True
    await db.commit()

    if character:
        update_online_player(user.email, character.nickname, character.level, character.current_map)

    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "has_character": character is not None
    }


@app.post("/logout")
async def logout_user(logout_data: LogoutRequest, db: AsyncSession = Depends(get_database)):
    """Logout user and mark them inactive."""
    user = await get_user_by_email(db, logout_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False
    await db.commit()
    remove_online_player(logout_data.email)

    return {"message": "Logged out"}


@app.post("/verify-security-answer")
async def verify_security_answer_endpoint(reset_data: PasswordReset, db: AsyncSession = Depends(get_database)):
    """Verify security answer without resetting password."""
    user = await get_user_by_email(db, reset_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify security answer
    if not await verify_security_answer(user, reset_data.security_answer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect security answer"
        )
    
    return {"message": "Security answer verified"}


@app.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: AsyncSession = Depends(get_database)):
    """Reset user password using security question."""
    user = await get_user_by_email(db, reset_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify security answer
    if not await verify_security_answer(user, reset_data.security_answer):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect security answer"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    await db.commit()
    
    return {"message": "Password reset successfully"}


@app.get("/user/{email}/security-question")
async def get_user_security_question(email: str, db: AsyncSession = Depends(get_database)):
    """Get user's security question for password reset."""
    from sqlalchemy.orm import selectinload
    
    # Load user with security question relationship
    result = await db.execute(
        select(User).options(selectinload(User.security_question)).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.security_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No security question set for this user"
        )
    
    return {"question": user.security_question.question_text}


@app.post("/characters", response_model=CharacterResponse)
async def create_character(character_data: CharacterCreate, db: AsyncSession = Depends(get_database)):
    """Create a new character for a user."""
    # Look up the user by email
    user = await get_user_by_email(db, character_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user already has a character
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    existing_for_user = result.scalar_one_or_none()
    if existing_for_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a character"
        )
    
    # Check if nickname is already taken
    result = await db.execute(
        select(Character).where(Character.nickname == character_data.nickname)
    )
    existing_character = result.scalar_one_or_none()
    if existing_character:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname already taken"
        )
    
    # Determine starting map based on race
    race_enum = Race(character_data.race)
    starting_map = RACE_STARTING_MAP.get(race_enum, "Settlement of Klesva")
    
    # Create the character with the correct user_id
    new_character = Character(
        user_id=user.id,
        nickname=character_data.nickname,
        race=character_data.race,
        gender=character_data.gender,
        current_map=starting_map
    )
    
    db.add(new_character)
    await db.commit()
    await db.refresh(new_character)

    # Generate random combos for the new character
    for combo_id, combo_def in COMBO_DEFINITIONS.items():
        seq = generate_random_combo_sequence(combo_def["sequence_length"])
        combo = CharacterCombo(
            character_id=new_character.id,
            combo_id=combo_id,
            sequence=seq,
            discovered=False,
        )
        db.add(combo)
    await db.commit()
    
    return new_character


@app.get("/characters/by-email/{email}")
async def get_character_by_email(email: str, db: AsyncSession = Depends(get_database)):
    """Get a user's character by their email address.
    
    Returns the character data with calculated total stats (including
    level bonuses and equipment bonuses) so the HUD shows correct
    max HP/Mana values.
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    user.is_active = True
    await db.commit()
    
    # Update online players tracking
    update_online_player(email, character.nickname, character.level, character.current_map)

    # Calculate total stats (level + equipment bonuses) for accurate HUD display
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.equipped_slot.is_not(None)
        )
    )
    equipped_items = result.scalars().all()
    stats = calculate_character_stats(character, equipped_items)

    # Build response with calculated totals overriding raw DB columns
    return {
        "id": character.id,
        "user_id": character.user_id,
        "nickname": character.nickname,
        "race": character.race,
        "gender": character.gender,
        "current_map": character.current_map,
        "cooldown_remaining": character.cooldown_remaining,
        "level": character.level,
        "experience": character.experience,
        "copper": character.copper or 0,
        "health": stats["total_stats"]["health"],  # Calculated max HP
        "current_hp": character.current_hp,
        "mana": stats["total_stats"]["mana"],  # Calculated max Mana
        "strength": stats["total_stats"]["strength"],
        "dexterity": stats["total_stats"]["dexterity"],
        "intelligence": stats["total_stats"]["intelligence"],
        "created_at": character.created_at.isoformat() if character.created_at else None,
    }


@app.get("/characters/by-email/{email}/stats")
async def get_character_stats(email: str, db: AsyncSession = Depends(get_database)):
    """Get a character's stats including base stats and item bonuses."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # Get equipped items
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.equipped_slot.is_not(None)
        )
    )
    equipped_items = result.scalars().all()
    
    # Calculate stats
    stats = calculate_character_stats(character, equipped_items)
    
    return {
        "level": character.level,
        "experience": character.experience,
        "base_stats": stats["base_stats"],
        "bonus_stats": stats["bonus_stats"],
        "total_stats": stats["total_stats"],
        "combat_stats": stats["combat_stats"],
        "set_bonus": stats.get("set_bonus"),
    }


@app.get("/world/players-on-map/{map_name}")
async def get_players_on_map_endpoint(map_name: str):
    """Get list of online players on a specific map."""
    players = get_players_on_map(map_name)
    return {"map": map_name, "players": players}


@app.get("/characters/view/{nickname}")
async def view_character_by_nickname(nickname: str, db: AsyncSession = Depends(get_database)):
    """View another player's character info by nickname."""
    result = await db.execute(
        select(Character).where(Character.nickname == nickname)
    )
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # Get equipped items
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.equipped_slot.is_not(None)
        )
    )
    equipped_items = result.scalars().all()
    
    # Calculate stats
    stats = calculate_character_stats(character, equipped_items)
    
    # Build equipped items list for response
    equipped_list = []
    for item in equipped_items:
        catalog = ITEMS_BY_ID.get(item.item_catalog_id, {})
        equipped_list.append({
            "slot": item.equipped_slot,
            "name": catalog.get("name", "Unknown"),
            "rarity": catalog.get("rarity", "common"),
        })
    
    return {
        "nickname": character.nickname,
        "race": character.race,
        "gender": character.gender,
        "level": character.level,
        "base_stats": stats["base_stats"],
        "bonus_stats": stats["bonus_stats"],
        "total_stats": stats["total_stats"],
        "combat_stats": stats["combat_stats"],
        "set_bonus": stats.get("set_bonus"),
        "equipped_items": equipped_list,
    }


@app.post("/characters/travel", response_model=TravelResponse)
async def travel_character(travel_data: TravelRequest, db: AsyncSession = Depends(get_database)):
    """Move a character to an adjacent region (instant move, server-side cooldown)."""
    from datetime import datetime as dt, timezone as tz, timedelta

    user = await get_user_by_email(db, travel_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    # --- Server-side cooldown enforcement ---
    if character.cooldown_remaining > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Travel cooldown active. "
                   + str(character.cooldown_remaining)
                   + "s remaining before you can travel again."
        )
    
    # Validate travel is allowed (adjacent region)
    if not is_valid_travel(character.current_map, travel_data.destination):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot travel from '"
                   + character.current_map
                   + "' to '"
                   + travel_data.destination
                   + "'. Regions are not connected."
        )
    
    # Calculate cooldown duration
    cooldown_seconds = get_travel_time(character.level)
    
    # Move immediately + set cooldown
    old_map = character.current_map
    character.current_map = travel_data.destination
    character.travel_cooldown_until = dt.now(tz.utc) + timedelta(seconds=cooldown_seconds)
    await db.commit()
    await db.refresh(character)
    
    # Update online player tracking with new map
    update_online_player(travel_data.email, character.nickname, character.level, travel_data.destination)
    
    return {
        "message": "Arrived at " + travel_data.destination + " from " + old_map,
        "destination": travel_data.destination,
        "cooldown_seconds": cooldown_seconds,
        "cooldown_remaining": character.cooldown_remaining,
        "current_map": character.current_map,
    }


@app.get("/world/regions/{region_name}", response_model=RegionResponse)
async def get_region_info(region_name: str):
    """Get region info including connected regions."""
    connected = get_connected_regions(region_name)
    if not connected and region_name not in HUMAN_MAP_GRAPH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_name}' not found"
        )
    return {"name": region_name, "connected_regions": connected}


@app.get("/world/npcs/{region_name}", response_model=List[NPCResponse])
async def get_region_npcs(region_name: str):
    """Get NPCs in a specific region."""
    if region_name not in HUMAN_MAP_GRAPH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_name}' not found"
        )
    return get_npcs_for_region(region_name)


@app.get("/world/mobs/{region_name}", response_model=List[MobResponse])
async def get_region_mobs(region_name: str):
    """Get mobs available in a specific region."""
    if region_name not in HUMAN_MAP_GRAPH:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_name}' not found"
        )
    return get_mobs_for_region(region_name)


@app.get("/items", response_model=List[ItemResponse])
async def list_all_items():
    """Return the complete item catalog."""
    return get_all_items()


def _merge_inventory_row(row: InventoryItem) -> dict:
    """Merge a DB inventory row with its catalog data."""
    catalog = ITEMS_BY_ID.get(row.item_catalog_id, {})
    return {
        "instance_id": row.id,
        "item_catalog_id": row.item_catalog_id,
        "quantity": row.quantity,
        "equipped_slot": row.equipped_slot,
        "name": catalog.get("name", "Unknown"),
        "slot": catalog.get("slot", ""),
        "required_level": catalog.get("required_level", 0),
        "character_class": catalog.get("character_class", ""),
        "rarity": catalog.get("rarity", "common"),
        "color": catalog.get("color", "white"),
        "inventory_category": catalog.get("inventory_category", "other"),
        "damage": catalog.get("damage", 0),
        "defense": catalog.get("defense", 0),
        "hp_bonus": catalog.get("hp_bonus", 0),
        "mana_bonus": catalog.get("mana_bonus", 0),
        "crit_chance": catalog.get("crit_chance", 0),
        "evasion": catalog.get("evasion", 0),
        "block_chance": catalog.get("block_chance", 0),
        "damage_reduction": catalog.get("damage_reduction", 0),
        "description": catalog.get("description", ""),
    }


@app.get("/inventory/{email}", response_model=List[InventoryItemResponse])
async def get_inventory(email: str, db: AsyncSession = Depends(get_database)):
    """Get all inventory items for a character by email."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(InventoryItem).where(InventoryItem.character_id == character.id)
    )
    rows = result.scalars().all()
    return [_merge_inventory_row(r) for r in rows]


@app.post("/inventory/add", response_model=InventoryItemResponse)
async def add_inventory_item(req: AddInventoryItemRequest, db: AsyncSession = Depends(get_database)):
    """Add an item to a character's inventory.
    
    For consumables: stacks with existing unequipped consumable of same type.
    For equipment: always creates new row (equippable items don't stack).
    """
    if req.item_catalog_id not in ITEMS_BY_ID:
        raise HTTPException(status_code=400, detail="Invalid item catalog ID")

    catalog_item = ITEMS_BY_ID[req.item_catalog_id]
    is_consumable = catalog_item.get("inventory_category") == "consumables"

    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # For consumables, try to find existing unequipped stack
    if is_consumable:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.character_id == character.id,
                InventoryItem.item_catalog_id == req.item_catalog_id,
                InventoryItem.equipped_slot.is_(None),  # Not equipped
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.quantity += 1
            await db.commit()
            await db.refresh(existing)
            return _merge_inventory_row(existing)

    # For equipment or no existing consumable stack, create new row
    new_row = InventoryItem(
        character_id=character.id,
        item_catalog_id=req.item_catalog_id,
        quantity=1,
    )
    db.add(new_row)
    await db.commit()
    await db.refresh(new_row)
    return _merge_inventory_row(new_row)


@app.post("/inventory/delete")
async def delete_inventory_item(req: DeleteInventoryItemRequest, db: AsyncSession = Depends(get_database)):
    """Delete an item instance from a character's inventory.
    
    For stacked consumables (quantity > 1), decrements quantity instead of deleting.
    """
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == req.instance_id,
            InventoryItem.character_id == character.id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found in inventory")

    # For stacked items, decrement quantity instead of deleting
    if row.quantity > 1:
        row.quantity -= 1
        await db.commit()
        return {"message": "Item quantity reduced", "quantity": row.quantity}
    else:
        await db.delete(row)
        await db.commit()
        return {"message": "Item deleted"}


@app.post("/inventory/equip", response_model=InventoryItemResponse)
async def equip_item(req: EquipItemRequest, db: AsyncSession = Depends(get_database)):
    """Equip an item to the character. Unequips any existing item in that slot."""
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Get the item to equip
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == req.instance_id,
            InventoryItem.character_id == character.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in inventory")

    # Get catalog data for level check
    catalog = ITEMS_BY_ID.get(item.item_catalog_id, {})
    required_level = catalog.get("required_level", 0)
    item_slot = catalog.get("slot", "")

    # Check level requirement
    if character.level < required_level:
        raise HTTPException(
            status_code=400,
            detail=f"Level {required_level} required to equip this item"
        )

    if item_slot == "morok":
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.character_id == character.id,
                InventoryItem.equipped_slot == item_slot,
            )
        )
        equipped_moroks = result.scalars().all()
        if len(equipped_moroks) >= 5:
            raise HTTPException(status_code=400, detail="You can equip up to 5 moroks")
    else:
        # Unequip any existing item in this slot
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.character_id == character.id,
                InventoryItem.equipped_slot == item_slot,
            )
        )
        existing_equipped = result.scalars().all()
        for eq_item in existing_equipped:
            eq_item.equipped_slot = None

    # Equip the new item
    item.equipped_slot = item_slot
    await db.commit()
    await db.refresh(item)
    return _merge_inventory_row(item)


@app.post("/inventory/unequip", response_model=InventoryItemResponse)
async def unequip_item(req: UnequipItemRequest, db: AsyncSession = Depends(get_database)):
    """Unequip an item from the character."""
    user = await get_user_by_email(db, req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == req.instance_id,
            InventoryItem.character_id == character.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in inventory")

    if not item.equipped_slot:
        raise HTTPException(status_code=400, detail="Item is not equipped")

    item.equipped_slot = None
    await db.commit()
    await db.refresh(item)
    return _merge_inventory_row(item)


# ============================================================
# BAG SYSTEM
# ============================================================


async def _ensure_bag_slots(character_id: int, db: AsyncSession):
    """Ensure a character has exactly 3 bag slot rows."""
    result = await db.execute(
        select(BagSlot).where(BagSlot.character_id == character_id).order_by(BagSlot.slot_index)
    )
    existing = result.scalars().all()
    existing_indices = {s.slot_index for s in existing}
    for idx in range(BAG_SLOT_COUNT):
        if idx not in existing_indices:
            db.add(BagSlot(character_id=character_id, slot_index=idx, item_catalog_id=None, quantity=0))
    if len(existing_indices) < BAG_SLOT_COUNT:
        await db.commit()


def _bag_slot_to_dict(slot: BagSlot) -> dict:
    """Convert a BagSlot row to a response dict."""
    item_name = ""
    if slot.item_catalog_id is not None:
        catalog = ITEMS_BY_ID.get(slot.item_catalog_id, {})
        item_name = catalog.get("name", "Unknown")
    if slot.slot_index == BAG_MOROK_SLOT_INDEX:
        max_quantity = BAG_MOROK_MAX
    else:
        max_quantity = BAG_SLOT_MAX.get(item_name, 0) if item_name else 0
    return {
        "slot_index": slot.slot_index,
        "item_catalog_id": slot.item_catalog_id,
        "item_name": item_name,
        "quantity": slot.quantity if slot.item_catalog_id is not None else 0,
        "max_quantity": max_quantity,
    }


@app.get("/bag/{email}")
async def get_bag(email: str, db: AsyncSession = Depends(get_database)):
    """Get the character's bag (2 slots)."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    await _ensure_bag_slots(character.id, db)
    result = await db.execute(
        select(BagSlot).where(BagSlot.character_id == character.id).order_by(BagSlot.slot_index)
    )
    slots = result.scalars().all()
    return [_bag_slot_to_dict(s) for s in slots]


@app.post("/bag/add")
async def add_to_bag(
    email: str,
    item_catalog_id: int,
    quantity: int,
    slot_index: int,
    db: AsyncSession = Depends(get_database),
):
    """Move consumable items from inventory into a bag slot.

    Rules:
    - HP/Mana Potion: max 12 per slot
    - Power Potion: max 7 per slot
    - Morok slot (index 2): max 5, single type
    - Slot must be empty or contain the same item type
    - Quantity is deducted from inventory
    """
    if item_catalog_id not in ITEMS_BY_ID:
        raise HTTPException(status_code=400, detail="Invalid item")
    catalog = ITEMS_BY_ID[item_catalog_id]
    item_name = catalog.get("name", "")
    is_morok = catalog.get("slot") == "morok"

    if slot_index < 0 or slot_index >= BAG_SLOT_COUNT:
        raise HTTPException(status_code=400, detail="Invalid slot index")

    if slot_index == BAG_MOROK_SLOT_INDEX:
        if not is_morok:
            raise HTTPException(status_code=400, detail="Only moroks can be placed in the morok slot")
        max_qty = BAG_MOROK_MAX
    else:
        if catalog.get("inventory_category") != "consumables":
            raise HTTPException(status_code=400, detail="Only consumable items can be placed in the bag")
        max_qty = BAG_SLOT_MAX.get(item_name, 0)
        if max_qty == 0:
            raise HTTPException(status_code=400, detail="This item cannot be placed in the bag")

    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    if quantity > max_qty:
        raise HTTPException(status_code=400, detail=f"Maximum {max_qty} of {item_name} per slot")

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    await _ensure_bag_slots(character.id, db)

    # Get the target bag slot
    result = await db.execute(
        select(BagSlot).where(
            BagSlot.character_id == character.id,
            BagSlot.slot_index == slot_index,
        )
    )
    bag_slot = result.scalar_one_or_none()
    if not bag_slot:
        raise HTTPException(status_code=404, detail="Bag slot not found")

    # Check slot is empty or same item
    if bag_slot.item_catalog_id is not None and bag_slot.item_catalog_id != item_catalog_id:
        raise HTTPException(status_code=400, detail="Slot already contains a different item. Empty it first.")

    # Check capacity
    current_in_slot = bag_slot.quantity if bag_slot.item_catalog_id == item_catalog_id else 0
    if current_in_slot + quantity > max_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot exceed {max_qty}. Currently {current_in_slot} in slot."
        )

    # Check inventory has enough
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.item_catalog_id == item_catalog_id,
            InventoryItem.equipped_slot.is_(None),
        )
    )
    # Get all matching items and sum their quantities (for non-stacking items like moroks)
    inv_items = result.scalars().all()
    total_available = sum(i.quantity for i in inv_items)
    if not inv_items or total_available < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough in inventory. Have {total_available}, need {quantity}."
        )

    # Deduct from inventory - take from first items until quantity is satisfied
    remaining_to_deduct = quantity
    for inv_item in inv_items:
        if remaining_to_deduct <= 0:
            break
        deduct = min(inv_item.quantity, remaining_to_deduct)
        inv_item.quantity -= deduct
        remaining_to_deduct -= deduct
        if inv_item.quantity <= 0:
            await db.delete(inv_item)

    # Add to bag slot
    bag_slot.item_catalog_id = item_catalog_id
    bag_slot.quantity = current_in_slot + quantity

    await db.commit()
    return {"message": f"Added {quantity}x {item_name} to bag slot {slot_index + 1}"}


@app.post("/bag/remove")
async def remove_from_bag(
    email: str,
    slot_index: int,
    db: AsyncSession = Depends(get_database),
):
    """Remove all items from a bag slot back to inventory."""
    if slot_index < 0 or slot_index >= BAG_SLOT_COUNT:
        raise HTTPException(status_code=400, detail="Invalid slot index")

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    await _ensure_bag_slots(character.id, db)

    result = await db.execute(
        select(BagSlot).where(
            BagSlot.character_id == character.id,
            BagSlot.slot_index == slot_index,
        )
    )
    bag_slot = result.scalar_one_or_none()
    if not bag_slot or bag_slot.item_catalog_id is None:
        raise HTTPException(status_code=400, detail="Slot is already empty")

    item_catalog_id = bag_slot.item_catalog_id
    qty = bag_slot.quantity

    # Return items to inventory (stack with existing if possible)
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.item_catalog_id == item_catalog_id,
            InventoryItem.equipped_slot.is_(None),
        )
    )
    inv_items = result.scalars().all()
    if inv_items:
        # Add all quantity to first available stack
        inv_items[0].quantity += qty
    else:
        new_row = InventoryItem(
            character_id=character.id,
            item_catalog_id=item_catalog_id,
            quantity=qty,
        )
        db.add(new_row)

    # Clear the bag slot
    item_name = ITEMS_BY_ID.get(item_catalog_id, {}).get("name", "Unknown")
    bag_slot.item_catalog_id = None
    bag_slot.quantity = 0

    await db.commit()
    return {"message": f"Removed {qty}x {item_name} from bag slot {slot_index + 1}"}


@app.post("/bag/use-in-fight")
async def use_bag_item_in_fight(
    email: str,
    slot_index: int,
    db: AsyncSession = Depends(get_database),
):
    """Use one charge of a bag slot item during a fight.

    Decrements quantity by 1. If quantity reaches 0, empties the slot.
    Returns the item info so the fight system can apply the effect.
    """
    if slot_index < 0 or slot_index >= BAG_SLOT_COUNT:
        raise HTTPException(status_code=400, detail="Invalid slot index")
    if slot_index == BAG_MOROK_SLOT_INDEX:
        raise HTTPException(status_code=400, detail="Moroks cannot be used in fights")

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(BagSlot).where(
            BagSlot.character_id == character.id,
            BagSlot.slot_index == slot_index,
        )
    )
    bag_slot = result.scalar_one_or_none()
    if not bag_slot or bag_slot.item_catalog_id is None or bag_slot.quantity <= 0:
        raise HTTPException(status_code=400, detail="Slot is empty")

    item_catalog_id = bag_slot.item_catalog_id
    item_name = ITEMS_BY_ID.get(item_catalog_id, {}).get("name", "Unknown")

    bag_slot.quantity -= 1
    remaining = bag_slot.quantity
    if bag_slot.quantity <= 0:
        bag_slot.item_catalog_id = None
        bag_slot.quantity = 0

    await db.commit()
    return {
        "item_catalog_id": item_catalog_id,
        "item_name": item_name,
        "remaining": remaining,
        "slot_index": slot_index,
    }


# ============================================================
# COMBO SYSTEM
# ============================================================


@app.get("/combos/{email}")
async def get_character_combos(email: str, db: AsyncSession = Depends(get_database)):
    """Get all combos for a character.
    
    Returns combo info with sequences hidden (shown as '?') if not yet discovered,
    unless the character hasn't reached the required level (in which case the combo
    is not returned at all... actually, we return it but mark it locked).
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(CharacterCombo).where(CharacterCombo.character_id == character.id)
    )
    combos = result.scalars().all()

    # If character has no combos yet (old character), generate them
    if not combos:
        for combo_id, combo_def in COMBO_DEFINITIONS.items():
            seq = generate_random_combo_sequence(combo_def["sequence_length"])
            combo = CharacterCombo(
                character_id=character.id,
                combo_id=combo_id,
                sequence=seq,
                discovered=False,
            )
            db.add(combo)
        await db.commit()
        result = await db.execute(
            select(CharacterCombo).where(CharacterCombo.character_id == character.id)
        )
        combos = result.scalars().all()

    combo_list = []
    for c in combos:
        cdef = COMBO_DEFINITIONS.get(c.combo_id, {})
        required_level = cdef.get("required_level", 1)
        unlocked = character.level >= required_level

        # Build sequence display
        seq_zones = c.sequence.split(",") if c.sequence else []
        if c.discovered:
            display_sequence = [ZONE_SYMBOLS.get(z, "?") for z in seq_zones]
        else:
            display_sequence = ["?" for _ in seq_zones]

        combo_list.append({
            "combo_id": c.combo_id,
            "name": cdef.get("name", c.combo_id),
            "required_level": required_level,
            "unlocked": unlocked,
            "discovered": c.discovered,
            "sequence_length": len(seq_zones),
            "display_sequence": display_sequence,
            "description": cdef.get("description", ""),
            "effect": cdef.get("effect", ""),
        })

    return combo_list


# ============================================================
# FIGHT SYSTEM
# ============================================================

class FightInstance:
    """Represents a single fight between a player and a mob."""

    def __init__(self, fight_id: str, player_data: dict, mob_data: dict, websocket: WebSocket, email: str = ""):
        self.fight_id = fight_id
        self.email = email  # Player email for currency awards
        self.player_level = player_data.get("level", 1)  # Player level for EXP/loot scaling
        self.websocket = websocket  # Can be None when player is disconnected
        # Use persisted current_hp if available, otherwise full HP
        starting_hp = player_data.get("current_hp", player_data["total_stats"]["health"])
        self.player = {
            "nickname": player_data["nickname"],
            "max_hp": player_data["total_stats"]["health"],
            "hp": starting_hp,
            "max_mana": player_data["total_stats"]["mana"],
            "mana": player_data["total_stats"]["mana"],
            "strength": player_data["total_stats"]["strength"],
            "dexterity": player_data["total_stats"]["dexterity"],
            "intelligence": player_data["total_stats"]["intelligence"],
            "damage": player_data["combat_stats"]["damage"],
            "defense": player_data["combat_stats"]["defense"],
            "crit_chance": player_data["combat_stats"]["crit_chance"],
            "evasion": player_data["combat_stats"]["evasion"],
            "block_chance": player_data["combat_stats"]["block_chance"],
            "damage_reduction": player_data["combat_stats"]["damage_reduction"],
        }
        self.mob = {
            "name": mob_data["name"],
            "display_name": mob_data["display_name"],
            "level": mob_data["level"],
            "max_hp": mob_data["max_hp"],
            "hp": mob_data["max_hp"],
            "mana": 0,
            "max_mana": 0,
            "damage_min": mob_data["damage_min"],
            "damage_max": mob_data["damage_max"],
            "crit_chance": mob_data.get("crit_chance", 15),
            "block_chance": mob_data.get("block_chance", 15),
            "evasion_chance": mob_data.get("evasion_chance", 15),
            "loot_copper_min": mob_data.get("loot_copper_min", 0),
            "loot_copper_max": mob_data.get("loot_copper_max", 0),
        }
        self.turn = "player"  # "player" or "mob"
        self.is_active = True
        self._turn_timer_task = None
        # Fight log history for reconnecting clients
        self.fight_log: list[str] = []
        # Damage tracking for fight statistics
        self.player_damage_dealt: int = 0
        self.player_damage_taken: int = 0
        self.mob_damage_dealt: int = 0
        self.mob_damage_taken: int = 0
        # Combo system
        self.combos: list[dict] = player_data.get("combos", [])
        # Recent attack history for combo detection (list of zone strings)
        self.attack_history: list[str] = []
        # Active bleeding effects on mob: list of {"ticks_left": int, "damage_per_tick": int}
        self.mob_bleedings: list[dict] = []
        # Bleeding tick timer task
        self._bleeding_timer_task = None
        # Server-side regen effects tracking (persists across reconnections)
        # list of {"type": "hp"|"mana", "ticks_left": int, "seconds_until_next": int}
        self.active_regen_effects: list[dict] = []
        self._regen_timer_task = None
        # Power potion: one-time use per fight
        self.power_used: bool = False
        # Item-type cooldowns: {"HP Potion": seconds_remaining, "Mana Potion": seconds_remaining}
        self.item_cooldowns: dict[str, int] = {}
        self._cooldown_timer_task = None
        # Summoned moroks: list of morok dicts with stats
        self.summoned_moroks: list[dict] = []
        # Morok attack timers (legacy, no longer used in turn-based flow)
        self._morok_timer_tasks: list[asyncio.Task] = []
        # Current mob target ("player" or "morok")
        self.current_mob_target: str = "player"
        self.current_morok_id: str | None = None

    def summon_morok(self, morok_data: dict) -> dict:
        """Summon a morok to assist in battle.
        
        Args:
            morok_data: Dict with name, damage, hp_bonus from the morok item
        
        Returns:
            Dict with summoned morok info
        """
        # Find the base mob data to calculate 70% stats
        from dragons_legacy.models.world_data import MOB_DEFINITIONS
        
        # Extract mob name from morok name (e.g., "Krets Morok - Medallion" -> "Krets")
        morok_name = morok_data.get("name", "Unknown Morok")
        mob_name = morok_name.replace(" Morok - Medallion", "").replace("[Lv1] ", "").replace("[Lv2] ", "").replace("[Lv3] ", "").strip()
        
        mob_def = MOB_DEFINITIONS.get(mob_name, {})
        if not mob_def:
            # Fallback to using the morok item stats directly
            max_hp = morok_data.get("hp_bonus", 50)
            damage_min = max(1, morok_data.get("damage", 10) // 2)
            damage_max = morok_data.get("damage", 10)
        else:
            # Calculate 70% of mob stats
            max_hp = max(1, int(mob_def.get("max_hp", 50) * 0.7))
            damage_min = max(1, int(mob_def.get("damage_min", 2) * 0.7))
            damage_max = max(1, int(mob_def.get("damage_max", 6) * 0.7))
        
        morok_id = morok_data.get("id") or f"morok_{len(self.summoned_moroks)}"
        morok = {
            "id": morok_id,
            "name": morok_name,
            "display_name": morok_name.split(" - ")[0],
            "max_hp": max_hp,
            "hp": max_hp,
            "damage_min": damage_min,
            "damage_max": damage_max,
            "crit_chance": mob_def.get("crit_chance", 15),
            "block_chance": mob_def.get("block_chance", 15),
            "evasion_chance": mob_def.get("evasion_chance", 15),
            "damage_dealt": 0,
            "damage_taken": 0,
        }
        self.summoned_moroks.append(morok)
        return morok

    def get_all_fighters(self) -> list[dict]:
        """Get all fighters on the player's side (player + moroks)."""
        fighters = [{"type": "player", "data": self.player}]
        for morok in self.summoned_moroks:
            fighters.append({"type": "morok", "data": morok})
        return fighters

    def get_random_target(self) -> tuple[str, dict]:
        """Get a random target for the mob to attack.
        
        Returns:
            Tuple of (target_type, target_data) where target_type is "player" or "morok"
        """
        fighters = self.get_all_fighters()
        # Filter out dead fighters
        alive_fighters = []
        for f in fighters:
            if f["type"] == "player" and self.player["hp"] > 0:
                alive_fighters.append(f)
            elif f["type"] == "morok" and f["data"]["hp"] > 0:
                alive_fighters.append(f)
        
        if not alive_fighters:
            return "player", self.player
        
        target = random.choice(alive_fighters)
        return target["type"], target["data"]

    def process_morok_attack(self, morok: dict) -> dict:
        """Process a morok's attack on the mob."""
        if not self.is_active or self.turn != "morok" or self.mob["hp"] <= 0:
            return {"error": "Not morok's turn"}

        if self.current_morok_id and morok.get("id") != self.current_morok_id:
            return {"error": "Not this morok's turn"}
        
        result = {"attacker": "morok", "morok_id": morok["id"], "events": []}
        
        # Calculate damage
        base_damage = random.randint(morok["damage_min"], morok["damage_max"])
        
        # Check mob evasion
        evasion_roll = random.randint(1, 100)
        if evasion_roll <= self.mob["evasion_chance"]:
            result["damage"] = 0
            result["events"].append("dodge")
            result["log"] = f"{self.mob['display_name']} dodged {morok['display_name']}'s attack!"
            return result
        
        # Check morok critical hit
        crit_roll = random.randint(1, 100)
        if crit_roll <= morok["crit_chance"]:
            crit_damage = int(base_damage * 1.5)
            result["damage"] = crit_damage
            result["events"].append("critical")
            self.mob["hp"] = max(0, self.mob["hp"] - crit_damage)
            result["log"] = f"CRITICAL! {morok['display_name']} deals {crit_damage} damage to {self.mob['display_name']}!"
        else:
            result["damage"] = base_damage
            self.mob["hp"] = max(0, self.mob["hp"] - base_damage)
            result["log"] = f"{morok['display_name']} deals {base_damage} damage to {self.mob['display_name']}."
        
        # Track damage
        morok["damage_dealt"] += result["damage"]
        self.mob_damage_taken += result["damage"]
        
        if self.mob["hp"] <= 0:
            self.is_active = False
            result["fight_over"] = True
            result["winner"] = "player"
        else:
            self.turn = "mob"

        # If it is still the player's turn, mark the current target as player
        if self.turn == "player":
            self.current_mob_target = "player"
            self.current_morok_id = None
        
        return result

    def process_mob_attack_on_target(self, target_type: str, target_data: dict) -> dict:
        """Process a mob attack on a specific target (player or morok)."""
        result = {"attacker": "mob", "target": target_type, "events": []}
        
        base_damage = self._calc_mob_base_damage()
        
        # Get target stats
        if target_type == "player":
            evasion = target_data["evasion"]
            block_chance = target_data["block_chance"]
            defense = target_data["defense"]
            damage_reduction = target_data["damage_reduction"]
            target_name = target_data["nickname"]
        else:  # morok
            evasion = target_data["evasion_chance"]
            block_chance = target_data["block_chance"]
            defense = 0  # Moroks don't have defense stat
            damage_reduction = 0
            target_name = target_data["display_name"]
        
        # Check target evasion
        evasion_roll = random.randint(1, 100)
        if evasion_roll <= evasion:
            result["damage"] = 0
            result["events"].append("dodge")
            result["log"] = f"{target_name} dodged the attack!"
            return result
        
        # Check target block
        block_roll = random.randint(1, 100)
        if block_roll <= block_chance:
            blocked_damage = max(1, base_damage // 2)
            if damage_reduction > 0:
                blocked_damage = max(1, int(blocked_damage * (1 - damage_reduction / 100)))
            result["damage"] = blocked_damage
            result["events"].append("block")
            target_data["hp"] = max(0, target_data["hp"] - blocked_damage)
            result["log"] = f"{target_name} blocked! Reduced damage: {blocked_damage}"
        else:
            # Check mob critical hit
            crit_roll = random.randint(1, 100)
            if crit_roll <= self.mob["crit_chance"]:
                crit_damage = int(base_damage * 1.5)
                # Apply defense mitigation
                if target_type == "player":
                    crit_damage = max(1, crit_damage - defense // 3)
                    if damage_reduction > 0:
                        crit_damage = max(1, int(crit_damage * (1 - damage_reduction / 100)))
                result["damage"] = crit_damage
                result["events"].append("critical")
                target_data["hp"] = max(0, target_data["hp"] - crit_damage)
                result["log"] = f"CRITICAL HIT! {self.mob['display_name']} deals {crit_damage} damage to {target_name}!"
            else:
                # Normal attack with defense mitigation
                final_damage = max(1, base_damage - defense // 4)
                if damage_reduction > 0:
                    final_damage = max(1, int(final_damage * (1 - damage_reduction / 100)))
                result["damage"] = final_damage
                target_data["hp"] = max(0, target_data["hp"] - final_damage)
                result["log"] = f"{self.mob['display_name']} deals {final_damage} damage to {target_name}."
        
        # Track damage
        dmg = result.get("damage", 0)
        self.mob_damage_dealt += dmg
        if target_type == "player":
            self.player_damage_taken += dmg
        else:
            target_data["damage_taken"] += dmg
        
        return result

    async def safe_send(self, data: dict) -> None:
        """Send a message to the connected client, if any. Silently ignores if disconnected."""
        if self.websocket is not None:
            try:
                await self.websocket.send_text(json.dumps(data))
            except Exception:
                self.websocket = None  # Mark as disconnected

    def start_regen_effect(self, regen_type: str) -> None:
        """Start a server-side regen effect: 10% every 4s for 20s (5 ticks).
        
        This persists across client reconnections.
        """
        self.active_regen_effects.append({
            "type": regen_type,
            "ticks_left": 5,
            "seconds_until_next": 4,
        })
        # Start the server-side regen timer if not already running
        if self._regen_timer_task is None or self._regen_timer_task.done():
            self._regen_timer_task = asyncio.create_task(
                _server_regen_tick_loop(self)
            )

    def _calc_player_base_damage(self) -> int:
        """Calculate base damage for a player attack."""
        # Base damage from strength + weapon damage
        str_bonus = self.player["strength"] // 5
        weapon_dmg = self.player["damage"]
        base = str_bonus + weapon_dmg
        if base < 1:
            base = 1
        # Add some randomness (+/- 20%)
        low = max(1, int(base * 0.8))
        high = max(low + 1, int(base * 1.2))
        return random.randint(low, high)

    def _calc_mob_base_damage(self) -> int:
        """Calculate base damage for a mob attack."""
        return random.randint(self.mob["damage_min"], self.mob["damage_max"])

    def process_player_attack(self, attack_type: str, power_boost: bool = False) -> dict:
        """Process a player attack. attack_type: head, chest, legs, plain"""
        if not self.is_active or self.turn != "player":
            return {"error": "Not your turn"}

        result = {"attacker": "player", "attack_type": attack_type, "events": [], "power_bonus_damage": 0}

        base_damage = self._calc_player_base_damage()

        # Apply attack type multipliers
        if attack_type == "head":
            # Head: higher damage, lower accuracy
            base_damage = int(base_damage * 1.2)
            miss_bonus = 10  # +10% chance to be evaded
        elif attack_type == "chest":
            # Chest: balanced
            miss_bonus = 0
        elif attack_type == "legs":
            # Legs: lower damage, higher accuracy
            base_damage = int(base_damage * 0.85)
            miss_bonus = -5  # -5% chance to be evaded (more accurate)
        else:
            # Plain attack (auto-attack, 50% less damage)
            base_damage = int(base_damage * 0.5)
            miss_bonus = 0

        # Apply power boost (35% damage increase)
        power_bonus = 0
        if power_boost:
            power_bonus = int(base_damage * 0.35)
            base_damage += power_bonus
            result["events"].append("power_boost")

        # Check mob evasion (dodge)
        evasion_roll = random.randint(1, 100)
        effective_evasion = self.mob["evasion_chance"] + miss_bonus
        if evasion_roll <= effective_evasion:
            result["damage"] = 0
            result["power_bonus_damage"] = 0
            result["events"].append("dodge")
            result["log"] = f"{self.mob['display_name']} dodged the attack!"
            self.turn = "mob"
            return result

        # Check mob block
        block_roll = random.randint(1, 100)
        if block_roll <= self.mob["block_chance"]:
            blocked_damage = max(1, base_damage // 2)
            result["damage"] = blocked_damage
            result["power_bonus_damage"] = power_bonus
            result["events"].append("block")
            self.mob["hp"] = max(0, self.mob["hp"] - blocked_damage)
            result["log"] = f"{self.mob['display_name']} blocked! Reduced damage: {blocked_damage}"
        else:
            # Check player critical hit
            crit_roll = random.randint(1, 100)
            if crit_roll <= self.player["crit_chance"]:
                crit_damage = int(base_damage * 1.5)
                result["damage"] = crit_damage
                result["power_bonus_damage"] = power_bonus
                result["events"].append("critical")
                self.mob["hp"] = max(0, self.mob["hp"] - crit_damage)
                result["log"] = f"CRITICAL HIT! {self.player['nickname']} deals {crit_damage} damage to {self.mob['display_name']}!"
            else:
                result["damage"] = base_damage
                result["power_bonus_damage"] = power_bonus
                self.mob["hp"] = max(0, self.mob["hp"] - base_damage)
                result["log"] = f"{self.player['nickname']} deals {base_damage} damage to {self.mob['display_name']}."

        # Track damage dealt by player (= damage taken by mob)
        dmg = result.get("damage", 0)
        self.player_damage_dealt += dmg
        self.mob_damage_taken += dmg

        if self.mob["hp"] <= 0:
            self.is_active = False
            result["fight_over"] = True
            result["winner"] = "player"
        else:
            self.turn = "mob"

        return result

    def process_mob_attack(self) -> dict:
        """Process a mob attack on a random target (player or morok)."""
        if not self.is_active or self.turn != "mob":
            return {"error": "Not mob's turn"}

        # Get random target
        target_type, target_data = self.get_random_target()
        self.current_mob_target = target_type
        if target_type == "morok":
            self.current_morok_id = target_data.get("id")
        else:
            self.current_morok_id = None
        
        # Process attack on target
        result = self.process_mob_attack_on_target(target_type, target_data)
        
        # Check if target died
        if target_type == "player" and self.player["hp"] <= 0:
            self.is_active = False
            result["fight_over"] = True
            result["winner"] = "mob"
        elif target_type == "morok" and target_data["hp"] <= 0:
            # Morok died, check if all fighters are dead
            alive_fighters = []
            if self.player["hp"] > 0:
                alive_fighters.append(("player", self.player))
            for m in self.summoned_moroks:
                if m["hp"] > 0:
                    alive_fighters.append(("morok", m))
            
            if not alive_fighters:
                self.is_active = False
                result["fight_over"] = True
                result["winner"] = "mob"
            else:
                # Morok died, return turn to player
                self.turn = "player"
                self.current_mob_target = "player"
                self.current_morok_id = None
        else:
            self.turn = self.current_mob_target

        # If current target is morok, ensure the ID is set
        if self.turn == "morok" and not self.current_morok_id:
            self.current_morok_id = target_data.get("id")

        return result

    def get_state(self) -> dict:
        """Get current fight state for sending to client."""
        # Calculate bleeding remaining seconds: ticks_left * 5 seconds per tick
        bleed_seconds = 0
        if self.mob_bleedings:
            bleed_seconds = sum(b["ticks_left"] for b in self.mob_bleedings) * 5

        # Calculate regen effects remaining
        regen_effects = []
        for eff in self.active_regen_effects:
            regen_effects.append({
                "type": eff["type"],
                "ticks_left": eff["ticks_left"],
                "seconds_until_next": eff["seconds_until_next"],
            })

        # Build moroks state (only alive ones)
        moroks_state = []
        for morok in self.summoned_moroks:
            moroks_state.append({
                "id": morok["id"],
                "display_name": morok["display_name"],
                "hp": morok["hp"],
                "max_hp": morok["max_hp"],
            })

        return {
            "fight_id": self.fight_id,
            "is_active": self.is_active,
            "turn": self.turn,
            "current_mob_target": self.current_mob_target,
            "current_morok_id": self.current_morok_id,
            "player": {
                "nickname": self.player["nickname"],
                "hp": self.player["hp"],
                "max_hp": self.player["max_hp"],
                "mana": self.player["mana"],
                "max_mana": self.player["max_mana"],
            },
            "mob": {
                "display_name": self.mob["display_name"],
                "hp": self.mob["hp"],
                "max_hp": self.mob["max_hp"],
                "mana": self.mob["mana"],
                "max_mana": self.mob["max_mana"],
            },
            "moroks": moroks_state,
            "bleed_seconds": bleed_seconds,
            "regen_effects": regen_effects,
            "power_used": self.power_used,
            "item_cooldowns": dict(self.item_cooldowns),
        }

    def check_combo(self, zone: str, damage_dealt: int) -> list[dict]:
        """Check if the latest attack completes a combo.
        
        Args:
            zone: The attack zone just used (head/chest/legs).
            damage_dealt: The actual damage dealt by this attack.
        
        Returns:
            List of triggered combo dicts: [{"combo_id": ..., "name": ..., "newly_discovered": bool, ...}]
        """
        # Add to attack history
        self.attack_history.append(zone)

        triggered = []
        for combo in self.combos:
            if not combo.get("unlocked"):
                continue
            seq = combo.get("sequence", [])
            seq_len = len(seq)
            if seq_len == 0:
                continue

            # Check if the last N attacks match this combo's sequence
            if len(self.attack_history) < seq_len:
                continue

            recent = self.attack_history[-seq_len:]
            if recent == seq:
                newly_discovered = not combo.get("discovered", False)
                if newly_discovered:
                    combo["discovered"] = True

                combo_info = {
                    "combo_id": combo["combo_id"],
                    "name": combo.get("name", combo["combo_id"]),
                    "newly_discovered": newly_discovered,
                    "sequence": seq,
                    "damage_dealt": damage_dealt,
                }

                # Apply combo effects
                if combo["combo_id"] == "deep_strike":
                    # Bleeding: 5% of mob max_hp every 5 seconds for 20 seconds (4 ticks)
                    # Replace any existing bleeding (reset duration, don't stack)
                    bleed_dmg = max(1, int(self.mob["max_hp"] * 0.05))
                    self.mob_bleedings.clear()
                    self.mob_bleedings.append({
                        "ticks_left": 4,
                        "damage_per_tick": bleed_dmg,
                    })
                    # Reset the bleeding timer so it starts fresh
                    if self._bleeding_timer_task and not self._bleeding_timer_task.done():
                        self._bleeding_timer_task.cancel()
                    self._bleeding_timer_task = None
                    combo_info["effect_type"] = "bleeding"
                    combo_info["bleed_damage"] = bleed_dmg

                elif combo["combo_id"] == "blood_worm":
                    # Lifesteal: 20% of the damage dealt on this hit
                    lifesteal = max(1, int(damage_dealt * 0.20))
                    self.player["hp"] = min(self.player["max_hp"], self.player["hp"] + lifesteal)
                    combo_info["effect_type"] = "lifesteal"
                    combo_info["lifesteal_amount"] = lifesteal

                triggered.append(combo_info)

                # Clear attack history after combo triggers to prevent
                # the same attacks from triggering again
                self.attack_history.clear()
                break  # Only one combo per attack

        # Keep attack history manageable (max 10 entries)
        if len(self.attack_history) > 10:
            self.attack_history = self.attack_history[-10:]

        return triggered


# Active fights: {fight_id: FightInstance}
active_fights: Dict[str, FightInstance] = {}
# Map email to fight_id for quick lookup
player_fights: Dict[str, str] = {}


async def _get_player_fight_data(email: str) -> dict:
    """Get player data needed for a fight (stats + character info)."""
    async for db in get_database():
        user = await get_user_by_email(db, email)
        if not user:
            return None
        result = await db.execute(
            select(Character).where(Character.user_id == user.id)
        )
        character = result.scalar_one_or_none()
        if not character:
            return None

        # Get equipped items
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.character_id == character.id,
                InventoryItem.equipped_slot.is_not(None)
            )
        )
        equipped_items = result.scalars().all()

        # Calculate stats
        stats = calculate_character_stats(character, equipped_items)

        # Determine current HP: use persisted current_hp if set, else max
        max_hp = stats["total_stats"]["health"]
        current_hp = character.current_hp if character.current_hp is not None else max_hp
        # Clamp to max
        current_hp = min(current_hp, max_hp)

        # Load combos for the fight
        result = await db.execute(
            select(CharacterCombo).where(CharacterCombo.character_id == character.id)
        )
        db_combos = result.scalars().all()

        # If character has no combos yet (old character), generate them
        if not db_combos:
            for combo_id, combo_def in COMBO_DEFINITIONS.items():
                seq = generate_random_combo_sequence(combo_def["sequence_length"])
                c = CharacterCombo(
                    character_id=character.id,
                    combo_id=combo_id,
                    sequence=seq,
                    discovered=False,
                )
                db.add(c)
            await db.commit()
            result = await db.execute(
                select(CharacterCombo).where(CharacterCombo.character_id == character.id)
            )
            db_combos = result.scalars().all()

        combos = []
        for c in db_combos:
            cdef = COMBO_DEFINITIONS.get(c.combo_id, {})
            required_level = cdef.get("required_level", 1)
            combos.append({
                "combo_id": c.combo_id,
                "name": cdef.get("name", c.combo_id),
                "sequence": c.sequence.split(",") if c.sequence else [],
                "discovered": c.discovered,
                "unlocked": character.level >= required_level,
                "required_level": required_level,
            })

        return {
            "nickname": character.nickname,
            "level": character.level,
            "total_stats": stats["total_stats"],
            "combat_stats": stats["combat_stats"],
            "current_hp": current_hp,
            "combos": combos,
        }


@app.get("/fight/active/{email}")
async def get_active_fight(email: str):
    """Check if a player has an active fight. Returns fight info or 404."""
    fight_id = player_fights.get(email)
    if not fight_id:
        raise HTTPException(status_code=404, detail="No active fight")
    fight = active_fights.get(fight_id)
    if not fight or not fight.is_active:
        # Clean up stale mapping
        player_fights.pop(email, None)
        raise HTTPException(status_code=404, detail="No active fight")
    return {
        "fight_id": fight.fight_id,
        "mob_name": fight.mob["name"],
        "mob_display_name": fight.mob["display_name"],
        "state": fight.get_state(),
    }


@app.get("/fight-history/{email}")
async def get_fight_history(email: str, db: AsyncSession = Depends(get_database)):
    """Get all fight statistics for a character, ordered by date descending."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(FightStatistic)
        .where(FightStatistic.character_id == character.id)
        .order_by(FightStatistic.fight_date.desc())
    )
    stats = result.scalars().all()

    return [
        {
            "id": s.id,
            "fight_date": s.fight_date.isoformat() if s.fight_date else "",
            "victory": s.victory,
            "player_name": s.player_name,
            "player_level": s.player_level,
            "mob_name": s.mob_name,
            "mob_level": s.mob_level,
            "player_damage_dealt": s.player_damage_dealt,
            "player_damage_taken": s.player_damage_taken,
            "mob_damage_dealt": s.mob_damage_dealt,
            "mob_damage_taken": s.mob_damage_taken,
            "exp_gained": s.exp_gained,
            "loot_copper": s.loot_copper,
        }
        for s in stats
    ]


@app.get("/fight-history/{email}/{stat_id}")
async def get_fight_stat_detail(email: str, stat_id: int, db: AsyncSession = Depends(get_database)):
    """Get a single fight statistic by ID."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(Character).where(Character.user_id == user.id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(FightStatistic).where(
            FightStatistic.id == stat_id,
            FightStatistic.character_id == character.id,
        )
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Fight statistic not found")

    return {
        "id": s.id,
        "fight_date": s.fight_date.isoformat() if s.fight_date else "",
        "victory": s.victory,
        "player_name": s.player_name,
        "player_level": s.player_level,
        "mob_name": s.mob_name,
        "mob_level": s.mob_level,
        "player_damage_dealt": s.player_damage_dealt,
        "player_damage_taken": s.player_damage_taken,
        "mob_damage_dealt": s.mob_damage_dealt,
        "mob_damage_taken": s.mob_damage_taken,
        "exp_gained": s.exp_gained,
        "loot_copper": s.loot_copper,
    }


@app.websocket("/ws/fight")
async def fight_websocket(websocket: WebSocket):
    """WebSocket endpoint for fight system.
    
    Protocol:
    1. Client sends: {"type": "start_fight", "email": "...", "mob_name": "..."}
       OR {"type": "rejoin_fight", "email": "..."} to reconnect to an active fight
    2. Server responds with fight_state
    3. Client sends: {"type": "attack", "fight_id": "...", "attack_type": "head|chest|legs"}
    4. Server processes player attack, then mob attack, sends results
    5. On fight end, server sends result with winner
    """
    await websocket.accept()
    current_fight_id = None
    current_email = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "rejoin_fight":
                email = message.get("email")
                current_email = email

                fight_id = player_fights.get(email)
                fight = active_fights.get(fight_id) if fight_id else None

                if not fight or not fight.is_active:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No active fight to rejoin"
                    }))
                    continue

                # Reconnect the WebSocket to the existing fight
                fight.websocket = websocket
                current_fight_id = fight_id

                # Send full fight state + log history to the reconnecting client
                await websocket.send_text(json.dumps({
                    "type": "fight_rejoined",
                    "state": fight.get_state(),
                    "log_history": fight.fight_log,
                    "log": "⚡ Reconnected to battle!",
                }))

                # If it's the player's turn, restart the turn timer
                if fight.turn == "player":
                    if fight._turn_timer_task and not fight._turn_timer_task.done():
                        fight._turn_timer_task.cancel()
                    fight._turn_timer_task = asyncio.create_task(
                        _player_turn_timeout(fight)
                    )
                continue

            if msg_type == "start_fight":
                email = message.get("email")
                mob_name = message.get("mob_name")
                current_email = email

                # Check if already in a fight — reject starting a new one
                if email in player_fights:
                    old_fight_id = player_fights[email]
                    old_fight = active_fights.get(old_fight_id)
                    if old_fight and old_fight.is_active:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Already in an active fight. Rejoin instead."
                        }))
                        continue
                    # Old fight is finished, clean up
                    active_fights.pop(old_fight_id, None)
                    player_fights.pop(email, None)

                # Get player data
                player_data = await _get_player_fight_data(email)
                if not player_data:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Character not found"
                    }))
                    continue

                # Get mob data
                mob_data = MOB_DEFINITIONS.get(mob_name)
                if not mob_data:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Mob not found"
                    }))
                    continue

                # Create fight instance
                fight_id = str(uuid.uuid4())[:8]
                fight = FightInstance(fight_id, player_data, mob_data, websocket, email=email)
                active_fights[fight_id] = fight
                player_fights[email] = fight_id
                current_fight_id = fight_id

                start_log = f"Battle begins! {player_data['nickname']} vs {mob_data['display_name']}!"
                fight.fight_log.append(start_log)

                # Send initial fight state
                await websocket.send_text(json.dumps({
                    "type": "fight_started",
                    "state": fight.get_state(),
                    "log": start_log,
                }))

                # Start the player turn timer (10 seconds)
                fight._turn_timer_task = asyncio.create_task(
                    _player_turn_timeout(fight)
                )
                continue

            if msg_type == "consumable_regen":
                # Legacy client-side regen tick — ignored; regen is now server-driven
                continue

            if msg_type == "start_regen":
                # Client tells server to start a regen effect (potion was used)
                fight_id = message.get("fight_id")
                regen_type = message.get("regen_type", "")  # "hp" or "mana"
                item_name = message.get("item_name", "")

                fight = active_fights.get(fight_id)
                if not fight or not fight.is_active:
                    continue

                # Track item cooldown server-side
                if item_name in ("HP Potion", "Mana Potion"):
                    fight.item_cooldowns[item_name] = 40
                    if fight._cooldown_timer_task is None or fight._cooldown_timer_task.done():
                        fight._cooldown_timer_task = asyncio.create_task(
                            _server_cooldown_tick_loop(fight)
                        )
                elif item_name == "Power Potion":
                    fight.power_used = True

                # Start server-side regen
                if regen_type in ("hp", "mana"):
                    fight.start_regen_effect(regen_type)
                continue

            if msg_type == "attack":
                fight_id = message.get("fight_id")
                attack_type = message.get("attack_type", "chest")
                power_boost = message.get("power_boost", False)

                fight = active_fights.get(fight_id)
                if not fight or not fight.is_active:
                    # Fight may have ended from bleeding — silently ignore
                    # rather than sending a confusing error
                    continue

                if fight.turn != "player":
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Not your turn"
                    }))
                    continue

                # Cancel the turn timer
                if fight._turn_timer_task and not fight._turn_timer_task.done():
                    fight._turn_timer_task.cancel()

                # Process player attack
                player_result = fight.process_player_attack(attack_type, power_boost=power_boost)
                fight.fight_log.append(player_result.get("log", ""))

                # Check for combo activation (only for targeted attacks, not plain)
                combo_results = []
                if attack_type in ("head", "chest", "legs"):
                    actual_damage = player_result.get("damage", 0)
                    combo_results = fight.check_combo(attack_type, actual_damage)

                # Send player attack result
                response = {
                    "type": "player_attack_result",
                    "result": player_result,
                    "state": fight.get_state(),
                }
                await fight.safe_send(response)

                # If power boost was used, send confirmation
                if power_boost and player_result.get("damage", 0) > 0:
                    bonus_dmg = player_result.get("power_bonus_damage", 0)
                    if bonus_dmg > 0:
                        await fight.safe_send({
                            "type": "power_boost_applied",
                            "bonus_damage": bonus_dmg,
                        })

                # Send combo activation messages
                for combo_info in combo_results:
                    combo_msg = {
                        "type": "combo_triggered",
                        "combo_id": combo_info["combo_id"],
                        "name": combo_info["name"],
                        "newly_discovered": combo_info["newly_discovered"],
                        "effect_type": combo_info.get("effect_type", ""),
                        "state": fight.get_state(),
                    }
                    if combo_info.get("effect_type") == "bleeding":
                        combo_msg["bleed_damage"] = combo_info.get("bleed_damage", 0)
                    elif combo_info.get("effect_type") == "lifesteal":
                        combo_msg["lifesteal_amount"] = combo_info.get("lifesteal_amount", 0)
                    await fight.safe_send(combo_msg)

                    # Persist combo discovery to database
                    if combo_info["newly_discovered"]:
                        await _persist_combo_discovery(fight.email, combo_info["combo_id"])

                    # Start bleeding timer if needed
                    if combo_info.get("effect_type") == "bleeding" and fight.mob_bleedings:
                        if fight._bleeding_timer_task is None or fight._bleeding_timer_task.done():
                            fight._bleeding_timer_task = asyncio.create_task(
                                _bleeding_tick_loop(fight)
                            )

                # Check if fight is over
                if player_result.get("fight_over"):
                    await _end_fight(fight, player_result["winner"])
                    continue

                # Mob's turn - wait 1-4 seconds then attack
                await _mob_turn(fight)
                continue

            if msg_type == "summon_morok":
                fight_id = message.get("fight_id")
                morok_data = message.get("morok_data", {})

                fight = active_fights.get(fight_id)
                if not fight or not fight.is_active:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No active fight"
                    }))
                    continue

                morok = None
                # Deduct morok from bag slot
                async for db in get_database():
                    user = await get_user_by_email(db, fight.email)
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "User not found"
                        }))
                        break
                    result = await db.execute(select(Character).where(Character.user_id == user.id))
                    character = result.scalar_one_or_none()
                    if not character:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Character not found"
                        }))
                        break

                    await _ensure_bag_slots(character.id, db)
                    result = await db.execute(
                        select(BagSlot).where(
                            BagSlot.character_id == character.id,
                            BagSlot.slot_index == BAG_MOROK_SLOT_INDEX,
                        )
                    )
                    bag_slot = result.scalar_one_or_none()
                    if not bag_slot or bag_slot.item_catalog_id is None or bag_slot.quantity <= 0:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "No moroks available"
                        }))
                        break

                    item_catalog_id = bag_slot.item_catalog_id
                    item_def = ITEMS_BY_ID.get(item_catalog_id, {})
                    morok_name = item_def.get("name", morok_data.get("name", "Unknown Morok"))

                    bag_slot.quantity -= 1
                    if bag_slot.quantity <= 0:
                        bag_slot.item_catalog_id = None
                        bag_slot.quantity = 0

                    await db.commit()

                    # Summon the morok with stable ID based on item catalog + count
                    morok_payload = {
                        "id": f"morok_{item_catalog_id}_{len(fight.summoned_moroks)}",
                        "name": morok_name,
                    }
                    morok = fight.summon_morok(morok_payload)
                    break

                if not morok:
                    continue

                # Send summon confirmation
                await fight.safe_send({
                    "type": "morok_summoned",
                    "morok": {
                        "id": morok["id"],
                        "display_name": morok["display_name"],
                        "hp": morok["hp"],
                        "max_hp": morok["max_hp"],
                    },
                    "state": fight.get_state(),
                    "log": f"🐴 {morok['display_name']} has been summoned to assist!",
                })

                # Morok is summoned and will attack when targeted by the mob
                continue

            if msg_type == "leave_fight":
                fight_id = message.get("fight_id")
                fight = active_fights.get(fight_id)
                if fight:
                    if fight._turn_timer_task and not fight._turn_timer_task.done():
                        fight._turn_timer_task.cancel()
                    fight.is_active = False
                    if fight_id in active_fights:
                        del active_fights[fight_id]
                if current_email and current_email in player_fights:
                    del player_fights[current_email]
                await websocket.send_text(json.dumps({
                    "type": "fight_left",
                    "message": "You left the fight."
                }))
                continue

    except WebSocketDisconnect:
        # Player disconnected — fight continues without them
        if current_fight_id and current_fight_id in active_fights:
            fight = active_fights[current_fight_id]
            fight.websocket = None  # Mark as disconnected, fight continues
            # If it's player's turn, the existing timer will auto-attack
            # If it's mob's turn, the mob attack task is already running
    except Exception:
        if current_fight_id and current_fight_id in active_fights:
            fight = active_fights[current_fight_id]
            fight.websocket = None  # Mark as disconnected, fight continues


async def _persist_combo_discovery(email: str, combo_id: str):
    """Persist a combo discovery to the database."""
    try:
        async for db in get_database():
            user = await get_user_by_email(db, email)
            if user:
                result = await db.execute(
                    select(Character).where(Character.user_id == user.id)
                )
                character = result.scalar_one_or_none()
                if character:
                    result = await db.execute(
                        select(CharacterCombo).where(
                            CharacterCombo.character_id == character.id,
                            CharacterCombo.combo_id == combo_id,
                        )
                    )
                    combo = result.scalar_one_or_none()
                    if combo:
                        combo.discovered = True
                        await db.commit()
            break
    except Exception:
        pass  # Don't fail the fight over a discovery persistence error


async def _server_cooldown_tick_loop(fight: FightInstance):
    """Server-side cooldown timer: decrements item cooldowns every second."""
    try:
        while fight.is_active and fight.item_cooldowns:
            await asyncio.sleep(1)
            if not fight.is_active:
                break
            expired = []
            for item_name in list(fight.item_cooldowns.keys()):
                fight.item_cooldowns[item_name] -= 1
                if fight.item_cooldowns[item_name] <= 0:
                    expired.append(item_name)
            for item_name in expired:
                del fight.item_cooldowns[item_name]
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


async def _server_regen_tick_loop(fight: FightInstance):
    """Server-side regen timer: processes HP/Mana regen every second.
    
    Persists across client reconnections since it runs on the server.
    """
    try:
        while fight.is_active and fight.active_regen_effects:
            await asyncio.sleep(1)
            if not fight.is_active or not fight.active_regen_effects:
                break

            effects_to_remove = []
            for effect in fight.active_regen_effects:
                effect["seconds_until_next"] -= 1
                if effect["seconds_until_next"] <= 0:
                    # Apply regen tick
                    regen_type = effect["type"]
                    amount = 0
                    if regen_type == "hp":
                        max_hp = fight.player["max_hp"]
                        amount = max(1, int(max_hp * 0.10))
                        fight.player["hp"] = min(max_hp, fight.player["hp"] + amount)
                    elif regen_type == "mana":
                        max_mana = fight.player["max_mana"]
                        amount = max(1, int(max_mana * 0.10))
                        fight.player["mana"] = min(max_mana, fight.player["mana"] + amount)

                    if amount > 0:
                        await fight.safe_send({
                            "type": "regen_tick",
                            "regen_type": regen_type,
                            "amount": amount,
                            "state": fight.get_state(),
                        })

                    effect["ticks_left"] -= 1
                    effect["seconds_until_next"] = 4

                    if effect["ticks_left"] <= 0:
                        effects_to_remove.append(effect)

            for e in effects_to_remove:
                fight.active_regen_effects.remove(e)
                regen_type = e["type"]
                if regen_type == "hp":
                    end_log = "💚 HP regeneration effect ended."
                else:
                    end_log = "💙 Mana regeneration effect ended."
                fight.fight_log.append(end_log)
                await fight.safe_send({
                    "type": "regen_ended",
                    "regen_type": regen_type,
                    "log": end_log,
                    "state": fight.get_state(),
                })

            if not fight.active_regen_effects:
                break
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


async def _bleeding_tick_loop(fight: FightInstance):
    """Process bleeding damage on the mob every 5 seconds."""
    try:
        while fight.is_active and fight.mob_bleedings:
            await asyncio.sleep(5)
            if not fight.is_active or not fight.mob_bleedings:
                break

            total_bleed = 0
            expired = []
            for bleed in fight.mob_bleedings:
                bleed_dmg = bleed["damage_per_tick"]
                fight.mob["hp"] = max(0, fight.mob["hp"] - bleed_dmg)
                total_bleed += bleed_dmg
                bleed["ticks_left"] -= 1
                if bleed["ticks_left"] <= 0:
                    expired.append(bleed)

            for e in expired:
                fight.mob_bleedings.remove(e)

            # Track damage
            fight.player_damage_dealt += total_bleed
            fight.mob_damage_taken += total_bleed

            bleed_log = f"🩸 {fight.mob['display_name']} bleeds for {total_bleed} damage!"
            fight.fight_log.append(bleed_log)

            # Check if mob died from bleeding
            if fight.mob["hp"] <= 0:
                # Send the bleeding tick BEFORE ending the fight so client
                # sees the final damage, then immediately end the fight.
                await fight.safe_send({
                    "type": "bleeding_tick",
                    "damage": total_bleed,
                    "state": fight.get_state(),
                    "log": bleed_log,
                })
                # Cancel the turn timer so no auto-attack fires during _end_fight
                if fight._turn_timer_task and not fight._turn_timer_task.done():
                    fight._turn_timer_task.cancel()
                await _end_fight(fight, "player")
                return  # Exit the loop entirely

            await fight.safe_send({
                "type": "bleeding_tick",
                "damage": total_bleed,
                "state": fight.get_state(),
                "log": bleed_log,
            })

            if not fight.mob_bleedings:
                end_log = "🩸 Bleeding effect has ended."
                fight.fight_log.append(end_log)
                await fight.safe_send({
                    "type": "bleeding_ended",
                    "log": end_log,
                    "state": fight.get_state(),
                })
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


async def _player_turn_timeout(fight: FightInstance):
    """Auto-attack after 10 seconds if player doesn't act."""
    try:
        await asyncio.sleep(10)
        if not fight.is_active or fight.turn != "player":
            return

        # Auto plain attack (50% less damage)
        player_result = fight.process_player_attack("plain")
        fight.fight_log.append("⏰ [Auto] " + player_result.get("log", ""))

        await fight.safe_send({
            "type": "player_attack_result",
            "result": player_result,
            "state": fight.get_state(),
            "auto_attack": True,
        })

        if player_result.get("fight_over"):
            await _end_fight(fight, player_result["winner"])
            return

        # Mob's turn
        await _mob_turn(fight)

    except asyncio.CancelledError:
        pass  # Timer was cancelled because player attacked
    except Exception:
        pass  # WebSocket may have closed


async def _mob_turn(fight: FightInstance):
    """Execute the mob's turn after a random delay."""
    if not fight.is_active:
        return

    # Random delay 1-4 seconds
    delay = random.uniform(1.0, 4.0)
    await asyncio.sleep(delay)

    if not fight.is_active or fight.turn != "mob":
        return

    mob_result = fight.process_mob_attack()
    fight.fight_log.append(mob_result.get("log", ""))

    await fight.safe_send({
        "type": "mob_attack_result",
        "result": mob_result,
        "state": fight.get_state(),
    })

    if mob_result.get("fight_over"):
        await _end_fight(fight, mob_result["winner"])
        return

    # Start next turn based on target
    if fight.turn == "player":
        fight._turn_timer_task = asyncio.create_task(
            _player_turn_timeout(fight)
        )
    elif fight.turn == "morok":
        morok = next((m for m in fight.summoned_moroks if m.get("id") == fight.current_morok_id), None)
        if morok:
            await _morok_turn(fight, morok)


async def _morok_turn(fight: FightInstance, morok: dict):
    """Execute a morok's counter-attack after a random delay."""
    if not fight.is_active or fight.turn != "morok":
        return

    # Random delay 1-4 seconds
    delay = random.uniform(1.0, 4.0)
    await asyncio.sleep(delay)

    if not fight.is_active or fight.turn != "morok" or morok["hp"] <= 0:
        return

    # Process morok attack
    result = fight.process_morok_attack(morok)
    if "error" in result:
        return

    # Send morok attack result (not added to fight_log to keep it hidden)
    await fight.safe_send({
        "type": "morok_attack_result",
        "morok_id": morok["id"],
        "result": result,
        "state": fight.get_state(),
    })

    # Check if fight ended
    if result.get("fight_over"):
        await _end_fight(fight, result["winner"])
        return

    # If still active, move turn back to player
    fight.turn = "player"
    fight.current_mob_target = "player"
    fight.current_morok_id = None

    if fight._turn_timer_task and not fight._turn_timer_task.done():
        fight._turn_timer_task.cancel()
    fight._turn_timer_task = asyncio.create_task(
        _player_turn_timeout(fight)
    )


async def _end_fight(fight: FightInstance, winner: str):
    """Clean up a finished fight and notify the client."""
    fight.is_active = False

    # Cancel bleeding timer if running
    if fight._bleeding_timer_task and not fight._bleeding_timer_task.done():
        fight._bleeding_timer_task.cancel()
    # Cancel regen timer if running
    if fight._regen_timer_task and not fight._regen_timer_task.done():
        fight._regen_timer_task.cancel()
    # Cancel cooldown timer if running
    if fight._cooldown_timer_task and not fight._cooldown_timer_task.done():
        fight._cooldown_timer_task.cancel()
    # Cancel all morok timer tasks (skip current task)
    current_task = asyncio.current_task()
    for task in fight._morok_timer_tasks:
        if task and not task.done() and task is not current_task:
            task.cancel()
    fight._morok_timer_tasks.clear()

    loot_copper = 0
    exp_gained = 0
    leveled_up = False
    new_level = 0

    if winner == "player":
        mob_level = fight.mob.get("level", 1)
        player_level = fight.player_level

        # Calculate level penalty multiplier
        penalty = calculate_level_penalty(player_level, mob_level)

        # Roll loot drop (scaled by penalty)
        loot_min = fight.mob.get("loot_copper_min", 0)
        loot_max = fight.mob.get("loot_copper_max", 0)
        if loot_max > 0 and penalty > 0:
            raw_loot = random.randint(loot_min, loot_max)
            loot_copper = max(0, int(raw_loot * penalty))

        # Calculate EXP (scaled by penalty)
        # Look up base_exp from the original mob definition
        mob_name_key = fight.mob.get("name", "")
        mob_def = MOB_DEFINITIONS.get(mob_name_key, {})
        base_exp = mob_def.get("base_exp", 0)
        if base_exp > 0 and penalty > 0:
            exp_gained = max(0, int(base_exp * penalty))

    # Persist current HP + award loot/exp regardless of winner
    # (HP is persisted for both victory and defeat)
    if fight.email:
        try:
            async for db in get_database():
                user = await get_user_by_email(db, fight.email)
                if user:
                    result = await db.execute(
                        select(Character).where(Character.user_id == user.id)
                    )
                    character = result.scalar_one_or_none()
                    if character:
                        if loot_copper > 0:
                            character.copper = (character.copper or 0) + loot_copper
                        if exp_gained > 0:
                            character.experience = (character.experience or 0) + exp_gained
                            # Check for level up (possibly multiple levels)
                            while True:
                                required = exp_required_for_level(character.level)
                                if character.experience >= required:
                                    character.experience -= required
                                    character.level += 1
                                    leveled_up = True
                                    new_level = character.level
                                else:
                                    break
                        # Persist current HP from the fight (don't reset to max!)
                        # On defeat, player survives with at least 1 HP.
                        character.current_hp = max(1, fight.player["hp"])
                        # Update the fight instance's player_level for consistency
                        fight.player_level = character.level
                        await db.commit()
                break
        except Exception:
            pass  # Don't fail the fight over a currency/exp error

    if winner == "player":
        # Update quest progress for kill quests
        quest_progress_msg = ""
        if fight.email:
            try:
                async for db in get_database():
                    user = await get_user_by_email(db, fight.email)
                    if user:
                        result = await db.execute(
                            select(Character).where(Character.user_id == user.id)
                        )
                        character = result.scalar_one_or_none()
                        if character:
                            # Find active kill quests matching this mob
                            result = await db.execute(
                                select(CharacterQuest).where(
                                    CharacterQuest.character_id == character.id,
                                    CharacterQuest.status == "active",
                                )
                            )
                            active_quests = result.scalars().all()
                            mob_name = fight.mob.get("name", "")
                            for cq in active_quests:
                                qdef = QUEST_DEFINITIONS.get(cq.quest_id, {})
                                if (qdef.get("objective_type") == "kill"
                                        and qdef.get("objective_target") == mob_name
                                        and cq.progress < qdef.get("objective_count", 0)):
                                    cq.progress += 1
                                    await db.commit()
                                    quest_progress_msg = (
                                        f"📋 Quest: {qdef['name']} — "
                                        f"{cq.progress}/{qdef['objective_count']}"
                                    )
                                    if cq.progress >= qdef["objective_count"]:
                                        quest_progress_msg += " ✅ Complete! Report to " + qdef.get("turn_in_npc", "")
                    break
            except Exception:
                pass

        if loot_copper > 0:
            loot_text = format_currency_plain(loot_copper)
            message = "🏆 Victorious! You defeated " + fight.mob["display_name"] + "! Loot: 💰 " + loot_text
        else:
            message = "🏆 Victorious! You defeated " + fight.mob["display_name"] + "!"
        if quest_progress_msg:
            message += "\n" + quest_progress_msg
    else:
        message = "💀 Defeat! You were slain by " + fight.mob["display_name"] + "!"

    fight.fight_log.append(message)

    # Save fight statistics to the database
    fight_stat_id = None
    if fight.email:
        try:
            async for db in get_database():
                user = await get_user_by_email(db, fight.email)
                if user:
                    result_q = await db.execute(
                        select(Character).where(Character.user_id == user.id)
                    )
                    character = result_q.scalar_one_or_none()
                    if character:
                        mob_level = fight.mob.get("level", 1)
                        stat = FightStatistic(
                            character_id=character.id,
                            victory=(winner == "player"),
                            player_name=fight.player["nickname"],
                            player_level=fight.player_level,
                            mob_name=fight.mob["name"],
                            mob_level=mob_level,
                            player_damage_dealt=fight.player_damage_dealt,
                            player_damage_taken=fight.player_damage_taken,
                            mob_damage_dealt=fight.mob_damage_dealt,
                            mob_damage_taken=fight.mob_damage_taken,
                            exp_gained=exp_gained,
                            loot_copper=loot_copper,
                        )
                        db.add(stat)
                        await db.commit()
                        await db.refresh(stat)
                        fight_stat_id = stat.id
                break
        except Exception:
            pass  # Don't fail the fight over a stats save error

    await fight.safe_send({
        "type": "fight_over",
        "winner": winner,
        "message": message,
        "loot_copper": loot_copper,
        "exp_gained": exp_gained,
        "leveled_up": leveled_up,
        "new_level": new_level,
        "state": fight.get_state(),
        "fight_stat_id": fight_stat_id,
        "fight_stats": {
            "player_name": fight.player["nickname"],
            "player_level": fight.player_level,
            "mob_name": fight.mob["name"],
            "mob_level": fight.mob.get("level", 1),
            "player_damage_dealt": fight.player_damage_dealt,
            "player_damage_taken": fight.player_damage_taken,
            "mob_damage_dealt": fight.mob_damage_dealt,
            "mob_damage_taken": fight.mob_damage_taken,
            "exp_gained": exp_gained,
            "loot_copper": loot_copper,
            "victory": (winner == "player"),
        },
    })

    # Clean up
    fight_id = fight.fight_id
    if fight_id in active_fights:
        del active_fights[fight_id]
    # Clean up player_fights mapping
    for email, fid in list(player_fights.items()):
        if fid == fight_id:
            del player_fights[email]
            break


# ============================================================
# QUEST SYSTEM
# ============================================================

from dragons_legacy.models.quest import CharacterQuest, QUEST_DEFINITIONS, get_quests_for_npc, get_turn_in_quests_for_npc


@app.get("/quests/available/{email}")
async def get_available_quests(email: str, npc_name: str, db: AsyncSession = Depends(get_database)):
    """Get quests available from a specific NPC for a character."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Get quests this NPC gives
    npc_quests = get_quests_for_npc(npc_name)

    # Get quests this NPC accepts turn-ins for
    turn_in_quests = get_turn_in_quests_for_npc(npc_name)

    # Get character's existing quests
    result = await db.execute(
        select(CharacterQuest).where(CharacterQuest.character_id == character.id)
    )
    existing = {cq.quest_id: cq for cq in result.scalars().all()}

    available = []

    # Quests that can be accepted from this NPC
    for qdef in npc_quests:
        qid = qdef["id"]
        if qid not in existing:
            # Quest not yet accepted — offer it
            available.append({
                "quest_id": qid,
                "name": qdef["name"],
                "description": qdef["description"],
                "objective_text": qdef["objective_text"],
                "reward_text": qdef["reward_text"],
                "level": qdef["level"],
                "action": "accept",
            })

    # Quests that can be turned in to this NPC
    for qdef in turn_in_quests:
        qid = qdef["id"]
        if qid in existing:
            cq = existing[qid]
            if cq.status == "active" and cq.progress >= qdef["objective_count"]:
                available.append({
                    "quest_id": qid,
                    "name": qdef["name"],
                    "description": "Quest complete! Claim your rewards.",
                    "objective_text": qdef["objective_text"],
                    "progress": cq.progress,
                    "objective_count": qdef["objective_count"],
                    "reward_text": qdef["reward_text"],
                    "level": qdef["level"],
                    "action": "complete",
                })

    return available


@app.get("/quests/{email}")
async def get_player_quests(email: str, db: AsyncSession = Depends(get_database)):
    """Get all quests for a character (active and completed)."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    result = await db.execute(
        select(CharacterQuest).where(CharacterQuest.character_id == character.id)
    )
    quests = result.scalars().all()

    quest_list = []
    for cq in quests:
        qdef = QUEST_DEFINITIONS.get(cq.quest_id, {})
        quest_list.append({
            "quest_id": cq.quest_id,
            "name": qdef.get("name", "Unknown"),
            "description": qdef.get("description", ""),
            "objective_text": qdef.get("objective_text", ""),
            "objective_count": qdef.get("objective_count", 0),
            "progress": cq.progress,
            "status": cq.status,
            "turn_in_npc": qdef.get("turn_in_npc", ""),
            "turn_in_region": qdef.get("turn_in_region", ""),
            "reward_text": qdef.get("reward_text", ""),
            "level": qdef.get("level", 1),
        })

    return quest_list


@app.post("/quests/accept")
async def accept_quest(email: str, quest_id: str, db: AsyncSession = Depends(get_database)):
    """Accept a quest."""
    if quest_id not in QUEST_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Quest not found")

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Check if already accepted
    result = await db.execute(
        select(CharacterQuest).where(
            CharacterQuest.character_id == character.id,
            CharacterQuest.quest_id == quest_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Quest already accepted")

    cq = CharacterQuest(
        character_id=character.id,
        quest_id=quest_id,
        status="active",
        progress=0,
    )
    db.add(cq)
    await db.commit()

    qdef = QUEST_DEFINITIONS[quest_id]
    return {"message": f"Quest accepted: {qdef['name']}", "quest_id": quest_id}


@app.post("/quests/complete")
async def complete_quest(email: str, quest_id: str, db: AsyncSession = Depends(get_database)):
    """Complete a quest and award rewards."""
    if quest_id not in QUEST_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Quest not found")
    qdef = QUEST_DEFINITIONS[quest_id]

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Get the quest progress
    result = await db.execute(
        select(CharacterQuest).where(
            CharacterQuest.character_id == character.id,
            CharacterQuest.quest_id == quest_id,
        )
    )
    cq = result.scalar_one_or_none()
    if not cq:
        raise HTTPException(status_code=400, detail="Quest not accepted")
    if cq.status == "completed":
        raise HTTPException(status_code=400, detail="Quest already completed")
    if cq.progress < qdef["objective_count"]:
        raise HTTPException(
            status_code=400,
            detail=f"Quest not finished. Progress: {cq.progress}/{qdef['objective_count']}"
        )

    # Mark quest as completed
    from datetime import datetime, timezone
    cq.status = "completed"
    cq.completed_at = datetime.now(timezone.utc)

    # Award rewards
    rewards = qdef.get("rewards", {})

    # Award copper
    copper_reward = rewards.get("copper", 0)
    if copper_reward > 0:
        character.copper = (character.copper or 0) + copper_reward

    # Award items
    item_rewards = rewards.get("items", [])
    # Build name -> catalog_id lookup
    name_to_id = {}
    for item_id, item in ITEMS_BY_ID.items():
        name_to_id[item["name"]] = item_id

    for item_name, qty in item_rewards:
        catalog_id = name_to_id.get(item_name)
        if not catalog_id:
            continue

        catalog = ITEMS_BY_ID[catalog_id]
        is_consumable = catalog.get("inventory_category") == "consumables"

        if is_consumable:
            # Stack with existing
            result = await db.execute(
                select(InventoryItem).where(
                    InventoryItem.character_id == character.id,
                    InventoryItem.item_catalog_id == catalog_id,
                    InventoryItem.equipped_slot.is_(None),
                )
            )
            existing_inv = result.scalar_one_or_none()
            if existing_inv:
                existing_inv.quantity += qty
            else:
                db.add(InventoryItem(
                    character_id=character.id,
                    item_catalog_id=catalog_id,
                    quantity=qty,
                ))
        else:
            # Equipment: create individual rows
            for _ in range(qty):
                db.add(InventoryItem(
                    character_id=character.id,
                    item_catalog_id=catalog_id,
                    quantity=1,
                ))

    await db.commit()

    return {
        "message": f"Quest completed: {qdef['name']}! Rewards claimed.",
        "quest_id": quest_id,
        "reward_text": qdef.get("reward_text", ""),
    }


# ============================================================
# HP REGENERATION (out-of-combat)
# ============================================================

@app.post("/characters/hp-regen")
async def hp_regen_tick(email: str, db: AsyncSession = Depends(get_database)):
    """Apply one out-of-combat HP regen tick: +10% of max HP.
    
    Returns the new current_hp and max_hp so the client can update the HUD.
    Does NOT regen if the player is at full HP already.
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Get equipped items for max HP calculation
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.equipped_slot.is_not(None)
        )
    )
    equipped_items = result.scalars().all()
    stats = calculate_character_stats(character, equipped_items)
    max_hp = stats["total_stats"]["health"]

    current_hp = character.current_hp if character.current_hp is not None else max_hp
    current_hp = min(current_hp, max_hp)

    if current_hp >= max_hp:
        return {"current_hp": max_hp, "max_hp": max_hp, "healed": 0}

    regen_amount = max(1, int(max_hp * 0.10))
    new_hp = min(max_hp, current_hp + regen_amount)
    actual_healed = new_hp - current_hp

    character.current_hp = new_hp
    await db.commit()

    return {"current_hp": new_hp, "max_hp": max_hp, "healed": actual_healed}


@app.post("/characters/eat-bread")
async def eat_bread(email: str, db: AsyncSession = Depends(get_database)):
    """Eat one Bread from inventory: +30 HP to current_hp, remove 1 from stack."""
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(select(Character).where(Character.user_id == user.id))
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Find Bread item catalog ID
    bread_id = None
    for item_id, item in ITEMS_BY_ID.items():
        if item.get("name") == "Bread":
            bread_id = item_id
            break
    if bread_id is None:
        raise HTTPException(status_code=400, detail="Bread item not found in catalog")

    # Find bread in inventory
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.item_catalog_id == bread_id,
            InventoryItem.equipped_slot.is_(None),
        )
    )
    inv_item = result.scalar_one_or_none()
    if not inv_item or inv_item.quantity <= 0:
        raise HTTPException(status_code=400, detail="No Bread in inventory")

    # Get max HP
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.character_id == character.id,
            InventoryItem.equipped_slot.is_not(None)
        )
    )
    equipped_items = result.scalars().all()
    stats = calculate_character_stats(character, equipped_items)
    max_hp = stats["total_stats"]["health"]

    current_hp = character.current_hp if character.current_hp is not None else max_hp
    current_hp = min(current_hp, max_hp)

    # Apply +30 HP
    new_hp = min(max_hp, current_hp + 30)
    actual_healed = new_hp - current_hp
    character.current_hp = new_hp

    # Consume 1 bread
    inv_item.quantity -= 1
    remaining = inv_item.quantity
    if inv_item.quantity <= 0:
        await db.delete(inv_item)

    await db.commit()

    return {
        "current_hp": new_hp,
        "max_hp": max_hp,
        "healed": actual_healed,
        "bread_remaining": max(0, remaining),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time game communication."""
    await manager.connect(websocket)
    nickname = None
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")

            if message_type == "identify":
                nickname = message_data.get("nickname")
                if nickname:
                    manager.register_user(nickname, websocket)
                    await manager.send_personal_message(
                        json.dumps({"type": "identified", "nickname": nickname}),
                        websocket
                    )
                else:
                    await manager.send_personal_message(
                        json.dumps({"type": "error", "message": "Nickname required"}),
                        websocket
                    )
                continue

            if message_type == "chat":
                payload = {
                    "type": "chat",
                    "channel": message_data.get("channel", "general"),
                    "sender": message_data.get("sender"),
                    "message": message_data.get("message", "")
                }
                await manager.broadcast(json.dumps(payload))
                continue

            if message_type == "whisper":
                targets = message_data.get("targets", [])
                payload = {
                    "type": "whisper",
                    "channel": message_data.get("channel", "general"),
                    "sender": message_data.get("sender"),
                    "targets": targets,
                    "message": message_data.get("message", "")
                }
                await manager.send_to_users(json.dumps(payload), targets)
                await manager.send_personal_message(json.dumps(payload), websocket)
                continue

            await manager.send_personal_message(
                json.dumps({"type": "echo", "data": message_data}),
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)