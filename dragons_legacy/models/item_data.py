"""
Item data for Legend of Dragon's Legacy.

Defines all equipment items and consumables, organized by:
  - Character class: Generalist, Bonecrusher, Skirmisher, Heavyweight
  - Rarity / color: White (generalist), Green, Blue, Purple
  - Equipment slot: weapon, weapon_left, weapon_right, cuirass, armor, shirt,
                    boots, shoulder, helmet
  - Required level: 1-5
  - Inventory category: equipment, consumables, moroks_mount, quest, other, gifts

Class design philosophy:
  Bonecrusher  – low defense, slightly higher HP than Skirmisher,
                 slightly higher damage, high critical hit chance.
  Skirmisher   – balanced HP/damage/crit/defense, high evasion chance.
  Heavyweight  – low damage, high block chance, high HP, damage reduction.

Weapon types per class:
  Heavyweight  – Gauntlet (left hand) + Shield (right hand)
  Skirmisher   – Sword (left hand) + Dagger (right hand)
  Bonecrusher  – Two-Handed Axe

Set names:
  Green  – Executioner (Bonecrusher), Twilight (Skirmisher), Mammoth (Heavyweight)
  Blue   – Anger (Bonecrusher), North Wind (Skirmisher), Giant Slayer (Heavyweight)
  Purple – Mysterious Anger, Mysterious North Wind, Mysterious Giant Slayer
"""

from typing import Dict, List, Any

from dragons_legacy.models.world_data import MOB_DEFINITIONS


# ============================================================
# INVENTORY CATEGORIES
# ============================================================

INVENTORY_CATEGORIES = [
    "consumables",
    "equipment",
    "moroks_mount",
    "quest",
    "other",
    "gifts",
]

CATEGORY_DISPLAY = {
    "consumables": "🧪 Consumables",
    "equipment": "⚔️ Equipment",
    "moroks_mount": "🐴 Moroks & Mount",
    "quest": "📋 Quest",
    "other": "📦 Other",
    "gifts": "🎁 Gifts",
}


# ============================================================
# ITEM CATALOG
# ============================================================

_NEXT_ID = 0


def _id() -> int:
    global _NEXT_ID
    _NEXT_ID += 1
    return _NEXT_ID


def _item(
    name: str,
    slot: str,
    required_level: int,
    character_class: str,
    rarity: str,
    color: str,
    inventory_category: str = "equipment",
    damage: int = 0,
    defense: int = 0,
    hp_bonus: int = 0,
    mana_bonus: int = 0,
    crit_chance: int = 0,
    evasion: int = 0,
    block_chance: int = 0,
    damage_reduction: int = 0,
    description: str = "",
) -> Dict[str, Any]:
    return {
        "id": _id(),
        "name": name,
        "slot": slot,
        "required_level": required_level,
        "character_class": character_class,
        "rarity": rarity,
        "color": color,
        "inventory_category": inventory_category,
        "damage": damage,
        "defense": defense,
        "hp_bonus": hp_bonus,
        "mana_bonus": mana_bonus,
        "crit_chance": crit_chance,
        "evasion": evasion,
        "block_chance": block_chance,
        "damage_reduction": damage_reduction,
        "description": description,
    }


# ------------------------------------------------------------------
# CONSUMABLE items
# ------------------------------------------------------------------

CONSUMABLE_ITEMS: List[Dict[str, Any]] = [
    _item("HP Potion", "consumable", 1, "Generalist", "common", "white",
          inventory_category="consumables", hp_bonus=50,
          description="Restores 50 HP when consumed."),
    _item("Mana Potion", "consumable", 1, "Generalist", "common", "white",
          inventory_category="consumables", mana_bonus=30,
          description="Restores 30 Mana when consumed."),
    _item("Power Potion", "consumable", 1, "Generalist", "common", "white",
          inventory_category="consumables",
          description="Increases damage dealt by 35% for one turn."),
    _item("Bread", "consumable", 1, "Generalist", "common", "white",
          inventory_category="consumables", hp_bonus=30,
          description="A hearty loaf of bread. Restores 30 HP when eaten. Use directly from inventory."),
]

# ------------------------------------------------------------------
# GENERALIST items (white) — levels 1-2 only
# ------------------------------------------------------------------

GENERALIST_ITEMS: List[Dict[str, Any]] = [
    # Level 1
    _item("Leather Armor", "armor", 1, "Generalist", "common", "white",
          defense=3, hp_bonus=5,
          description="Basic leather armor for new adventurers."),
    _item("Leather Cuirass", "cuirass", 1, "Generalist", "common", "white",
          defense=4, hp_bonus=8,
          description="A simple leather cuirass offering modest protection."),
    # Level 2
    _item("Iron Spear", "weapon", 2, "Generalist", "common", "white",
          damage=12, crit_chance=3,
          description="A sturdy iron spear, reliable in any hands."),
]

# ------------------------------------------------------------------
# BONECRUSHER items — Two-Handed Axe class
# Set names: Green=Executioner, Blue=Anger, Purple=Mysterious Anger
# ------------------------------------------------------------------

BONECRUSHER_ITEMS: List[Dict[str, Any]] = [
    # === GREEN (Executioner) ===
    # Level 3 — weapon, cuirass, armor, shirt, boots
    _item("Executioner Two-Handed Axe", "weapon", 3, "Bonecrusher", "uncommon", "green",
          damage=28, crit_chance=12,
          description="A massive axe that cleaves through bone with ease."),
    _item("Executioner Cuirass", "cuirass", 3, "Bonecrusher", "uncommon", "green",
          defense=8, hp_bonus=20, crit_chance=3,
          description="Dark iron cuirass forged for executioners."),
    _item("Executioner Armor", "armor", 3, "Bonecrusher", "uncommon", "green",
          defense=6, hp_bonus=15, crit_chance=2,
          description="Lightweight armor allowing swift deadly strikes."),
    _item("Executioner Shirt", "shirt", 3, "Bonecrusher", "uncommon", "green",
          defense=3, hp_bonus=10, crit_chance=2,
          description="A blood-stained shirt worn by executioners."),
    _item("Executioner Boots", "boots", 3, "Bonecrusher", "uncommon", "green",
          defense=4, hp_bonus=8, crit_chance=1,
          description="Heavy boots that leave deep tracks."),
    # Level 4 — shoulder
    _item("Executioner Shoulder", "shoulder", 4, "Bonecrusher", "uncommon", "green",
          defense=5, hp_bonus=12, crit_chance=2,
          description="Spiked shoulder guards of the executioner."),
    # Level 5 — helmet
    _item("Executioner Helmet", "helmet", 5, "Bonecrusher", "uncommon", "green",
          defense=6, hp_bonus=15, crit_chance=3,
          description="A fearsome helmet that strikes terror."),

    # === BLUE (Anger) ===
    _item("Anger Two-Handed Axe", "weapon", 3, "Bonecrusher", "rare", "blue",
          damage=35, crit_chance=15,
          description="An axe fueled by pure rage."),
    _item("Anger Cuirass", "cuirass", 3, "Bonecrusher", "rare", "blue",
          defense=10, hp_bonus=28, crit_chance=4,
          description="Cuirass forged in the fires of fury."),
    _item("Anger Armor", "armor", 3, "Bonecrusher", "rare", "blue",
          defense=8, hp_bonus=22, crit_chance=3,
          description="Armor pulsing with wrathful energy."),
    _item("Anger Shirt", "shirt", 3, "Bonecrusher", "rare", "blue",
          defense=5, hp_bonus=15, crit_chance=3,
          description="A shirt imbued with berserker fury."),
    _item("Anger Boots", "boots", 3, "Bonecrusher", "rare", "blue",
          defense=6, hp_bonus=12, crit_chance=2,
          description="Boots that carry the weight of anger."),
    _item("Anger Shoulder", "shoulder", 4, "Bonecrusher", "rare", "blue",
          defense=7, hp_bonus=18, crit_chance=3,
          description="Shoulder guards crackling with fury."),
    _item("Anger Helmet", "helmet", 5, "Bonecrusher", "rare", "blue",
          defense=8, hp_bonus=20, crit_chance=4,
          description="A helm that channels unbridled rage."),

    # === PURPLE (Mysterious Anger) ===
    _item("Mysterious Anger Two-Handed Axe", "weapon", 3, "Bonecrusher", "epic", "purple",
          damage=45, crit_chance=18,
          description="A legendary axe shrouded in dark mystery."),
    _item("Mysterious Anger Cuirass", "cuirass", 3, "Bonecrusher", "epic", "purple",
          defense=14, hp_bonus=35, crit_chance=5,
          description="An enigmatic cuirass radiating dark power."),
    _item("Mysterious Anger Armor", "armor", 3, "Bonecrusher", "epic", "purple",
          defense=11, hp_bonus=28, crit_chance=4,
          description="Armor infused with mysterious wrath."),
    _item("Mysterious Anger Shirt", "shirt", 3, "Bonecrusher", "epic", "purple",
          defense=7, hp_bonus=20, crit_chance=4,
          description="A shirt pulsing with arcane fury."),
    _item("Mysterious Anger Boots", "boots", 3, "Bonecrusher", "epic", "purple",
          defense=8, hp_bonus=16, crit_chance=3,
          description="Boots echoing with ancient rage."),
    _item("Mysterious Anger Shoulder", "shoulder", 4, "Bonecrusher", "epic", "purple",
          defense=10, hp_bonus=22, crit_chance=4,
          description="Shoulder guards veiled in dark mystery."),
    _item("Mysterious Anger Helmet", "helmet", 5, "Bonecrusher", "epic", "purple",
          defense=11, hp_bonus=25, crit_chance=5,
          description="A helm of unfathomable dark power."),
]

# ------------------------------------------------------------------
# SKIRMISHER items — Dual Swords class
# Set names: Green=Twilight, Blue=North Wind, Purple=Mysterious North Wind
# ------------------------------------------------------------------

SKIRMISHER_ITEMS: List[Dict[str, Any]] = [
    # === GREEN (Twilight) ===
    _item("Twilight Sword", "weapon_left", 3, "Skirmisher", "uncommon", "green",
          damage=14, crit_chance=5, evasion=4,
          description="A swift blade that dances like a shadow at dusk."),
    _item("Twilight Dagger", "weapon_right", 3, "Skirmisher", "uncommon", "green",
          damage=10, crit_chance=4, evasion=5,
          description="A keen dagger that strikes from the twilight."),
    _item("Twilight Cuirass", "cuirass", 3, "Skirmisher", "uncommon", "green",
          defense=7, hp_bonus=15, evasion=5,
          description="A sleek cuirass designed for agile fighters."),
    _item("Twilight Armor", "armor", 3, "Skirmisher", "uncommon", "green",
          defense=5, hp_bonus=12, evasion=4,
          description="Light armor that moves with the wearer."),
    _item("Twilight Shirt", "shirt", 3, "Skirmisher", "uncommon", "green",
          defense=3, hp_bonus=8, evasion=3,
          description="A dark shirt woven for silent movement."),
    _item("Twilight Boots", "boots", 3, "Skirmisher", "uncommon", "green",
          defense=4, hp_bonus=6, evasion=4,
          description="Soft-soled boots for swift footwork."),
    _item("Twilight Shoulder", "shoulder", 4, "Skirmisher", "uncommon", "green",
          defense=4, hp_bonus=10, evasion=3,
          description="Shoulder pads that don't restrict movement."),
    _item("Twilight Helmet", "helmet", 5, "Skirmisher", "uncommon", "green",
          defense=5, hp_bonus=12, evasion=4,
          description="A lightweight helm with excellent visibility."),

    # === BLUE (North Wind) ===
    _item("North Wind Sword", "weapon_left", 3, "Skirmisher", "rare", "blue",
          damage=18, crit_chance=6, evasion=5,
          description="A blade as swift and cold as the northern gale."),
    _item("North Wind Dagger", "weapon_right", 3, "Skirmisher", "rare", "blue",
          damage=13, crit_chance=5, evasion=6,
          description="A frost-kissed dagger that bites like winter wind."),
    _item("North Wind Cuirass", "cuirass", 3, "Skirmisher", "rare", "blue",
          defense=9, hp_bonus=22, evasion=7,
          description="Cuirass infused with the chill of the north."),
    _item("North Wind Armor", "armor", 3, "Skirmisher", "rare", "blue",
          defense=7, hp_bonus=18, evasion=6,
          description="Armor blessed by winter winds."),
    _item("North Wind Shirt", "shirt", 3, "Skirmisher", "rare", "blue",
          defense=5, hp_bonus=12, evasion=5,
          description="A frost-touched shirt of the north."),
    _item("North Wind Boots", "boots", 3, "Skirmisher", "rare", "blue",
          defense=6, hp_bonus=10, evasion=6,
          description="Boots that glide like wind over snow."),
    _item("North Wind Shoulder", "shoulder", 4, "Skirmisher", "rare", "blue",
          defense=6, hp_bonus=15, evasion=5,
          description="Shoulder guards kissed by frost."),
    _item("North Wind Helmet", "helmet", 5, "Skirmisher", "rare", "blue",
          defense=7, hp_bonus=18, evasion=6,
          description="A helm that whispers with the northern wind."),

    # === PURPLE (Mysterious North Wind) ===
    _item("Mysterious North Wind Sword", "weapon_left", 3, "Skirmisher", "epic", "purple",
          damage=23, crit_chance=8, evasion=7,
          description="A legendary blade from beyond the frozen veil."),
    _item("Mysterious North Wind Dagger", "weapon_right", 3, "Skirmisher", "epic", "purple",
          damage=16, crit_chance=6, evasion=8,
          description="An enigmatic dagger shimmering with arcane frost."),
    _item("Mysterious North Wind Cuirass", "cuirass", 3, "Skirmisher", "epic", "purple",
          defense=12, hp_bonus=30, evasion=9,
          description="A cuirass of otherworldly frost."),
    _item("Mysterious North Wind Armor", "armor", 3, "Skirmisher", "epic", "purple",
          defense=10, hp_bonus=24, evasion=8,
          description="Armor shimmering with arcane ice."),
    _item("Mysterious North Wind Shirt", "shirt", 3, "Skirmisher", "epic", "purple",
          defense=7, hp_bonus=16, evasion=7,
          description="A shirt woven from frozen starlight."),
    _item("Mysterious North Wind Boots", "boots", 3, "Skirmisher", "epic", "purple",
          defense=8, hp_bonus=14, evasion=8,
          description="Boots that leave frost in their wake."),
    _item("Mysterious North Wind Shoulder", "shoulder", 4, "Skirmisher", "epic", "purple",
          defense=9, hp_bonus=20, evasion=7,
          description="Shoulder guards of eternal winter."),
    _item("Mysterious North Wind Helmet", "helmet", 5, "Skirmisher", "epic", "purple",
          defense=10, hp_bonus=22, evasion=8,
          description="A helm of mysterious arctic power."),
]

# ------------------------------------------------------------------
# HEAVYWEIGHT items — Gauntlet + Shield class
# Set names: Green=Mammoth, Blue=Giant Slayer, Purple=Mysterious Giant Slayer
# ------------------------------------------------------------------

HEAVYWEIGHT_ITEMS: List[Dict[str, Any]] = [
    # === GREEN (Mammoth) ===
    _item("Mammoth Gauntlet", "weapon_left", 3, "Heavyweight", "uncommon", "green",
          damage=10, defense=6, block_chance=5, hp_bonus=15,
          description="A massive gauntlet that crushes foes."),
    _item("Mammoth Shield", "weapon_right", 3, "Heavyweight", "uncommon", "green",
          defense=12, block_chance=10, hp_bonus=20, damage_reduction=3,
          description="An immovable shield of mammoth bone."),
    _item("Mammoth Cuirass", "cuirass", 3, "Heavyweight", "uncommon", "green",
          defense=12, hp_bonus=30, block_chance=3, damage_reduction=2,
          description="A thick cuirass built to absorb punishment."),
    _item("Mammoth Armor", "armor", 3, "Heavyweight", "uncommon", "green",
          defense=10, hp_bonus=25, block_chance=2, damage_reduction=1,
          description="Heavy armor forged from mammoth iron."),
    _item("Mammoth Shirt", "shirt", 3, "Heavyweight", "uncommon", "green",
          defense=5, hp_bonus=18, damage_reduction=1,
          description="A reinforced shirt of mammoth hide."),
    _item("Mammoth Boots", "boots", 3, "Heavyweight", "uncommon", "green",
          defense=6, hp_bonus=15, block_chance=2,
          description="Boots that anchor the wearer to the ground."),
    _item("Mammoth Shoulder", "shoulder", 4, "Heavyweight", "uncommon", "green",
          defense=8, hp_bonus=20, block_chance=3, damage_reduction=1,
          description="Massive shoulder plates of mammoth bone."),
    _item("Mammoth Helmet", "helmet", 5, "Heavyweight", "uncommon", "green",
          defense=9, hp_bonus=22, block_chance=3, damage_reduction=2,
          description="A towering helm of mammoth ivory."),

    # === BLUE (Giant Slayer) ===
    _item("Giant Slayer Gauntlet", "weapon_left", 3, "Heavyweight", "rare", "blue",
          damage=14, defense=8, block_chance=7, hp_bonus=22,
          description="A gauntlet forged to fell giants."),
    _item("Giant Slayer Shield", "weapon_right", 3, "Heavyweight", "rare", "blue",
          defense=16, block_chance=14, hp_bonus=28, damage_reduction=4,
          description="A shield that has turned aside giant blows."),
    _item("Giant Slayer Cuirass", "cuirass", 3, "Heavyweight", "rare", "blue",
          defense=16, hp_bonus=40, block_chance=4, damage_reduction=3,
          description="Cuirass reinforced with giant-slaying runes."),
    _item("Giant Slayer Armor", "armor", 3, "Heavyweight", "rare", "blue",
          defense=13, hp_bonus=32, block_chance=3, damage_reduction=2,
          description="Armor etched with tales of fallen giants."),
    _item("Giant Slayer Shirt", "shirt", 3, "Heavyweight", "rare", "blue",
          defense=7, hp_bonus=24, damage_reduction=2,
          description="A shirt woven with giant-hair thread."),
    _item("Giant Slayer Boots", "boots", 3, "Heavyweight", "rare", "blue",
          defense=8, hp_bonus=20, block_chance=3,
          description="Boots that shake the earth with each step."),
    _item("Giant Slayer Shoulder", "shoulder", 4, "Heavyweight", "rare", "blue",
          defense=11, hp_bonus=26, block_chance=4, damage_reduction=2,
          description="Shoulder guards carved from giant bone."),
    _item("Giant Slayer Helmet", "helmet", 5, "Heavyweight", "rare", "blue",
          defense=12, hp_bonus=28, block_chance=4, damage_reduction=3,
          description="A helm crowned with a giant's tooth."),

    # === PURPLE (Mysterious Giant Slayer) ===
    _item("Mysterious Giant Slayer Gauntlet", "weapon_left", 3, "Heavyweight", "epic", "purple",
          damage=18, defense=11, block_chance=9, hp_bonus=30,
          description="A gauntlet pulsing with ancient giant-slaying magic."),
    _item("Mysterious Giant Slayer Shield", "weapon_right", 3, "Heavyweight", "epic", "purple",
          defense=20, block_chance=18, hp_bonus=35, damage_reduction=6,
          description="A legendary shield of unfathomable resilience."),
    _item("Mysterious Giant Slayer Cuirass", "cuirass", 3, "Heavyweight", "epic", "purple",
          defense=20, hp_bonus=50, block_chance=5, damage_reduction=4,
          description="An enigmatic cuirass of titanic fortitude."),
    _item("Mysterious Giant Slayer Armor", "armor", 3, "Heavyweight", "epic", "purple",
          defense=16, hp_bonus=40, block_chance=4, damage_reduction=3,
          description="Armor steeped in mysterious giant-slaying lore."),
    _item("Mysterious Giant Slayer Shirt", "shirt", 3, "Heavyweight", "epic", "purple",
          defense=10, hp_bonus=30, damage_reduction=3,
          description="A shirt infused with arcane resilience."),
    _item("Mysterious Giant Slayer Boots", "boots", 3, "Heavyweight", "epic", "purple",
          defense=11, hp_bonus=25, block_chance=4,
          description="Boots of mysterious immovable force."),
    _item("Mysterious Giant Slayer Shoulder", "shoulder", 4, "Heavyweight", "epic", "purple",
          defense=14, hp_bonus=32, block_chance=5, damage_reduction=3,
          description="Shoulder guards of enigmatic giant power."),
    _item("Mysterious Giant Slayer Helmet", "helmet", 5, "Heavyweight", "epic", "purple",
          defense=15, hp_bonus=35, block_chance=5, damage_reduction=4,
          description="A helm of mysterious titanic authority."),
]


# ------------------------------------------------------------------
# MOROKS (70% mob power, Generalist category)
# ------------------------------------------------------------------

MOROK_ITEMS: List[Dict[str, Any]] = []
for mob in MOB_DEFINITIONS.values():
    level = int(mob.get("level", 1))
    name = mob.get("name", "Unknown")
    display_name = f"{name} Morok - Medallion"
    max_hp = max(1, int(mob.get("max_hp", 1) * 0.7))
    damage_min = max(1, int(mob.get("damage_min", 1) * 0.7))
    damage_max = max(damage_min, int(mob.get("damage_max", 1) * 0.7))
    MOROK_ITEMS.append(
        _item(
            display_name,
            "morok",
            level,
            "Generalist",
            "common",
            "white",
            inventory_category="moroks_mount",
            damage=damage_max,
            defense=0,
            hp_bonus=max_hp,
            description=f"A loyal morok bound to {name}. Its strength mirrors 70% of the {name}.",
        )
    )


# ------------------------------------------------------------------
# COMBINED CATALOG
# ------------------------------------------------------------------

ALL_ITEMS: List[Dict[str, Any]] = (
    CONSUMABLE_ITEMS
    + GENERALIST_ITEMS
    + BONECRUSHER_ITEMS
    + SKIRMISHER_ITEMS
    + HEAVYWEIGHT_ITEMS
    + MOROK_ITEMS
)

# Quick lookup by id
ITEMS_BY_ID: Dict[int, Dict[str, Any]] = {item["id"]: item for item in ALL_ITEMS}


def get_all_items() -> List[Dict[str, Any]]:
    """Return the full item catalog."""
    return ALL_ITEMS


def get_items_by_class(character_class: str) -> List[Dict[str, Any]]:
    """Return items for a specific character class."""
    return [i for i in ALL_ITEMS if i["character_class"] == character_class]


def get_items_by_level(max_level: int) -> List[Dict[str, Any]]:
    """Return items up to a given required level."""
    return [i for i in ALL_ITEMS if i["required_level"] <= max_level]


# ------------------------------------------------------------------
# RARITY ORDERING (for display sorting)
# ------------------------------------------------------------------

RARITY_ORDER = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}

# ------------------------------------------------------------------
# SLOT DISPLAY NAMES
# ------------------------------------------------------------------

SLOT_DISPLAY = {
    "weapon": "Weapon",
    "weapon_left": "Left Hand",
    "weapon_right": "Right Hand",
    "cuirass": "Cuirass",
    "armor": "Armor",
    "shirt": "Shirt",
    "boots": "Boots",
    "shoulder": "Shoulder",
    "helmet": "Helmet",
    "morok": "Morok",
}