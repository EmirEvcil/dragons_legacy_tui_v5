"""
World data for Legend of Dragon's Legacy.

Defines the map graph (node connections), NPCs per region,
and travel time calculations.
"""

from typing import Dict, List, Set


# ============================================================
# HUMAN RACE MAP GRAPH (node structure)
# Settlement of Klesva -> Baurwill Town -> King's Tomb
#   -> Light Square -> O'Delvays City Center
# ============================================================

HUMAN_MAP_GRAPH: Dict[str, List[str]] = {
    "Settlement of Klesva": ["Baurwill Town"],
    "Baurwill Town": ["Settlement of Klesva", "King's Tomb"],
    "King's Tomb": ["Baurwill Town", "Light Square"],
    "Light Square": ["King's Tomb", "O'Delvays City Center"],
    "O'Delvays City Center": ["Light Square"],
}

# All valid human region names (for validation)
HUMAN_REGIONS: Set[str] = set(HUMAN_MAP_GRAPH.keys())


# ============================================================
# NPCs PER REGION
# ============================================================

REGION_NPCS: Dict[str, List[Dict[str, str]]] = {
    "Settlement of Klesva": [
        {"name": "Elder Mirwen", "role": "Village Elder", "description": "A wise old woman who guides newcomers."},
        {"name": "Torvak the Smith", "role": "Blacksmith", "description": "Forges basic weapons and armor for adventurers."},
        {"name": "Lina", "role": "Herbalist", "description": "Sells potions and healing herbs."},
    ],
    "Baurwill Town": [
        {"name": "Captain Roderick", "role": "Guard Captain", "description": "Maintains order in the town and offers bounty quests."},
        {"name": "Mara the Merchant", "role": "General Merchant", "description": "Buys and sells a variety of goods."},
        {"name": "Old Gregor", "role": "Tavern Keeper", "description": "Runs the local tavern; a good source of rumors."},
        {"name": "Sister Alia", "role": "Healer", "description": "Provides healing services to weary travelers."},
    ],
    "King's Tomb": [
        {"name": "Warden Duskhelm", "role": "Tomb Guardian", "description": "Guards the ancient tomb and warns of dangers within."},
        {"name": "Spirit of King Aldric", "role": "Ancient Spirit", "description": "The restless spirit of the fallen king, seeking peace."},
    ],
    "Light Square": [
        {"name": "Archmage Solenne", "role": "Magic Instructor", "description": "Teaches the arcane arts to those with potential."},
        {"name": "Trader Fenwick", "role": "Rare Goods Merchant", "description": "Deals in rare and enchanted items."},
        {"name": "Bard Elowen", "role": "Bard", "description": "Sings tales of old and shares news from distant lands."},
    ],
    "O'Delvays City Center": [
        {"name": "King Aldenvale III", "role": "King", "description": "The ruler of the human realm, seated on his throne."},
        {"name": "Chancellor Voss", "role": "Royal Advisor", "description": "The king's trusted advisor on matters of state."},
        {"name": "Guildmaster Theron", "role": "Adventurer's Guild", "description": "Manages the adventurer's guild and assigns high-level quests."},
        {"name": "Master Armorer Kael", "role": "Master Blacksmith", "description": "Crafts the finest weapons and armor in the realm."},
        {"name": "Sage Orinthal", "role": "Lorekeeper", "description": "Keeper of ancient knowledge and forgotten histories."},
    ],
}


# ============================================================
# TRAVEL TIME CALCULATION
# Max level: 10
# Level 1: 10 seconds base
# Levels 2-5: +15 seconds per level
# Levels 6-10: +10 seconds per level
# ============================================================

MAX_LEVEL = 10


def get_travel_time(level: int) -> int:
    """
    Calculate travel time in seconds based on character level.

    Level 1:  10s
    Level 2:  25s  (10 + 15)
    Level 3:  40s  (10 + 30)
    Level 4:  55s  (10 + 45)
    Level 5:  70s  (10 + 60)
    Level 6:  80s  (70 + 10)
    Level 7:  90s  (70 + 20)
    Level 8:  100s (70 + 30)
    Level 9:  110s (70 + 40)
    Level 10: 120s (70 + 50)
    """
    clamped_level = max(1, min(level, MAX_LEVEL))

    base = 10  # level 1

    if clamped_level <= 5:
        return base + (clamped_level - 1) * 15
    else:
        # levels 2-5 contribute 4 * 15 = 60
        return base + 60 + (clamped_level - 5) * 10


def get_connected_regions(current_map: str) -> List[str]:
    """Return the list of regions directly connected to the given map."""
    return HUMAN_MAP_GRAPH.get(current_map, [])


def is_valid_travel(current_map: str, destination: str) -> bool:
    """Check if travel from current_map to destination is valid (adjacent)."""
    return destination in HUMAN_MAP_GRAPH.get(current_map, [])


def get_npcs_for_region(region: str) -> List[Dict[str, str]]:
    """Return the list of NPCs in the given region."""
    return REGION_NPCS.get(region, [])


# ============================================================
# MOB DATA PER REGION
# ============================================================

MOB_DEFINITIONS: Dict[str, Dict] = {
    "Krets": {
        "name": "Krets",
        "level": 1,
        "display_name": "Krets [1]",
        "max_hp": 55,
        "damage_min": 2,
        "damage_max": 6,
        "crit_chance": 15,     # 15% base for level 1
        "block_chance": 15,
        "evasion_chance": 15,
        "loot_copper_min": 40,   # 40 copper
        "loot_copper_max": 112,  # 1 silver 12 copper
        "base_exp": 5,           # EXP awarded on kill
    },
    "Aggressive Krets": {
        "name": "Aggressive Krets",
        "level": 2,
        "display_name": "Aggressive Krets [2]",
        "max_hp": 70,
        "damage_min": 4,
        "damage_max": 8,
        "crit_chance": 17,     # 15 + 2*(2-1) = 17%
        "block_chance": 17,
        "evasion_chance": 17,
        "loot_copper_min": 100,  # 1 silver
        "loot_copper_max": 180,  # 1 silver 80 copper
        "base_exp": 10,          # EXP awarded on kill
    },
    "Skeleton": {
        "name": "Skeleton",
        "level": 3,
        "display_name": "Skeleton [3]",
        "max_hp": 90,
        "damage_min": 6,
        "damage_max": 10,
        "crit_chance": 19,     # 15 + 2*(3-1) = 19%
        "block_chance": 19,
        "evasion_chance": 19,
        "loot_copper_min": 300,  # 3 silver
        "loot_copper_max": 700,  # 7 silver
        "base_exp": 25,          # EXP awarded on kill
    },
}


# Which mobs appear in each region
REGION_MOBS: Dict[str, List[str]] = {
    "Settlement of Klesva": ["Krets"],
    "Baurwill Town": ["Aggressive Krets", "Skeleton"],
    "King's Tomb": ["Aggressive Krets", "Skeleton"],
    "Light Square": ["Aggressive Krets", "Skeleton"],
    "O'Delvays City Center": ["Aggressive Krets", "Skeleton"],
}


def get_mobs_for_region(region: str) -> List[Dict]:
    """Return the list of mob definitions available in the given region."""
    mob_names = REGION_MOBS.get(region, [])
    return [MOB_DEFINITIONS[name] for name in mob_names if name in MOB_DEFINITIONS]


# ============================================================
# CURRENCY HELPERS
# 100 copper = 1 silver, 100 silver = 1 gold (10000 copper = 1 gold)
# ============================================================

def copper_to_parts(total_copper: int) -> tuple:
    """Convert total copper to (gold, silver, copper) tuple."""
    total_copper = max(0, total_copper)
    gold = total_copper // 10000
    remainder = total_copper % 10000
    silver = remainder // 100
    copper = remainder % 100
    return gold, silver, copper


# ============================================================
# LEVELING HELPERS
# EXP required to level up:
#   Level 1 -> 2: 100 EXP
#   Level 2 -> 3: 200 EXP
#   Level 3 -> 4: 400 EXP
#   Formula: 100 * 2^(level-1)
# EXP resets to 0 after each level up.
# ============================================================

def exp_required_for_level(level: int) -> int:
    """Return the EXP required to advance from the given level to the next.

    Level 1 -> 100, Level 2 -> 200, Level 3 -> 400, etc.
    (doubles each level)
    """
    return 100 * (2 ** (level - 1))


def calculate_level_penalty(player_level: int, mob_level: int) -> float:
    """Return a multiplier (0.0 – 1.0) for EXP and loot based on level difference.

    Rules:
    - If the player level exceeds the mob level by more than 3 -> 0.0 (no rewards)
    - Otherwise, 30% reduction per level above the mob:
        same level = 1.0
        +1 above   = 0.7
        +2 above   = 0.4
        +3 above   = 0.1
    - If the player is below or equal to the mob level -> 1.0 (full rewards)
    """
    diff = player_level - mob_level
    if diff <= 0:
        return 1.0
    if diff > 3:
        return 0.0
    return max(0.0, 1.0 - diff * 0.3)


def format_currency_plain(total_copper: int) -> str:
    """Format currency as plain text: Xg Ys Zc (omit zero-value currencies except copper)."""
    gold, silver, copper = copper_to_parts(total_copper)
    parts = []
    if gold > 0:
        parts.append(str(gold) + "g")
    if silver > 0 or gold > 0:
        parts.append(str(silver) + "s")
    parts.append(str(copper) + "c")
    return " ".join(parts)