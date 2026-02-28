# Legend of Dragon's Legacy - Development Log

## Project Overview

**Legend of Dragon's Legacy** is a turn-based, TUI (Terminal User Interface) multiplayer RPG game built with Python. The game features a modern, beautiful interface using Textual, a FastAPI backend with WebSocket support, and local SQLite database storage.

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI** for REST API endpoints
- **WebSocket** support for real-time multiplayer features
- **SQLAlchemy** with async SQLite for database operations
- **JWT authentication** with secure password hashing
- **Security questions** for password recovery

### Frontend (Textual TUI)
- **Textual** for modern terminal user interface
- **Custom CSS styling** for beautiful appearance
- **Form validation** with real-time feedback
- **Async HTTP client** for API communication
- **Screen-based navigation** system

### Database
- **SQLite** with async operations
- **User management** with email/password authentication
- **Security questions** system for password recovery
- **Character data** storage (expandable for game features)

## 📁 Project Structure

```
dragons_legacy/
├── __init__.py
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   └── schemas.py           # Pydantic models
├── database/
│   ├── __init__.py
│   └── database.py          # Database configuration
├── models/
│   ├── __init__.py
│   ├── user.py              # User model
│   ├── security_question.py # Security question model
│   ├── character.py         # Character model
│   ├── world_data.py        # Map graph, NPCs, travel time
│   ├── item_data.py         # Item catalog (classes, rarities, stats)
│   └── inventory.py         # InventoryItem DB model
├── utils/
│   ├── __init__.py
│   └── auth.py              # Authentication utilities
└── frontend/
    ├── __init__.py
    ├── app.py               # Main Textual application
    ├── api_client.py        # HTTP client for API
    ├── styles.py            # CSS styles
    └── screens/
        ├── __init__.py
        ├── login_screen.py           # Login interface
        ├── registration_screen.py    # Registration interface
        ├── forgot_password_screen.py # Password reset interface
        ├── character_creation_screen.py # Character creation (race, gender, nickname)
        └── game_screen.py            # Game screen (HUD, location, NPCs, travel)
```

## 🚀 Features Implemented

### ✅ Authentication System
- **User Registration**
  - Email validation
  - Password strength requirements (minimum 6 characters)
  - Password confirmation
  - Security question selection from 5 predefined options
  - Secure password hashing with bcrypt
  - Email uniqueness validation

- **User Login**
  - Email/password authentication
  - JWT token generation
  - Input validation with real-time feedback
  - Error handling for invalid credentials

- **Password Recovery**
  - Email-based user lookup
  - Security question verification
  - New password setting with confirmation
  - Multi-step process with clear progression

### ✅ Modern TUI Interface
- **Beautiful Design**
  - Dragon-themed styling with emojis
  - Modern color scheme with CSS variables
  - Responsive form layouts
  - Hover and focus states
  - Loading indicators

- **User Experience**
  - Keyboard navigation (Tab, Enter)
  - Real-time form validation
  - Clear error and success messages
  - Intuitive button placement
  - Screen transitions

### ✅ Backend API
- **RESTful Endpoints**
  - `POST /register` - User registration
  - `POST /login` - User authentication
  - `GET /security-questions` - Get available security questions
  - `GET /user/{email}/security-question` - Get user's security question
  - `POST /reset-password` - Password reset
  - `POST /characters` - Character creation (nickname, race, gender)
  - `GET /characters/by-email/{email}` - Get user's character data
  - `POST /characters/travel` - Travel to an adjacent region
  - `GET /world/regions/{name}` - Get region info and connected regions
  - `GET /world/npcs/{name}` - Get NPCs in a region
  - `GET /items` - Get the complete item catalog
  - `GET /inventory/{email}` - Get player's inventory (server-side)
  - `POST /inventory/add` - Add item to inventory
  - `POST /inventory/delete` - Delete item from inventory
  - `WebSocket /ws` - Real-time communication (ready for game features)

- **Database Integration**
  - Async SQLite operations
  - Automatic table creation
  - Relationship management
  - Data validation

### ✅ Security Features
- **Password Security**
  - Bcrypt hashing
  - Secure salt generation
  - Password strength validation

- **JWT Authentication**
  - Token-based authentication
  - Configurable expiration times
  - Secure secret key management

- **Security Questions**
  - 5 predefined questions:
    1. "What was the name of your first pet?"
    2. "What is your mother's maiden name?"
    3. "What was the name of your first school?"
    4. "What city were you born in?"
    5. "What is your favorite childhood memory location?"
  - Case-insensitive answer matching
  - Secure answer hashing

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
textual==0.45.1
sqlalchemy==2.0.23
aiosqlite==0.19.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
email-validator==2.1.0
httpx==0.25.2
```

### Installation Steps
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the backend server:**
   ```bash
   python main.py backend
   ```
   - API available at: http://localhost:8000
   - API documentation at: http://localhost:8000/docs

3. **Start the TUI client (in another terminal):**
   ```bash
   python main.py frontend
   ```

## 🎮 How to Use

### Starting the Game
1. Run `python main.py` for usage instructions
2. Start the backend server first
3. Start the frontend client in another terminal

### User Registration
1. Click "Register" on the login screen
2. Enter email and password
3. Confirm password
4. Select a security question
5. Provide security answer
6. Account created successfully

### User Login
1. Enter email and password on login screen
2. Click "Login" or press Enter
3. Successful login redirects to character creation

### Password Recovery
1. Click "Forgot Password?" on login screen
2. Enter your email address
3. Answer your security question
4. Set new password
5. Return to login with new credentials

## ✅ Character Creation Screen

The character creation screen has been fully implemented with the following features:

### Implemented Features:
- **Race Selection** - Two races defined:
  - **Magmar** - Displayed with red styling (🚧 **Coming Soon** — disabled, not selectable)
  - **Human** - Displayed with green styling when selected (✅ **Available**)
- **Gender Selection** - Two options:
  - **Female**
  - **Male**
- **Nickname Entry** - With strict validation rules:
  - Maximum 12 characters
  - No spaces allowed
  - No special characters allowed (only letters and numbers)
  - Unique nickname enforcement (server-side)

### Flow:
- After successful registration → redirected to Character Creation screen (new user, no character yet)
- After successful login:
  - If the user **has a character** → redirected directly to Game screen
  - If the user **does not have a character** → redirected to Character Creation screen
- After character creation → redirected to Game screen

### Technical Details:
- `NicknameValidator` class for client-side nickname validation
- Race and gender selection via toggle buttons with visual feedback
- `POST /characters` API endpoint for character creation with server-side validation
- `CharacterCreate` Pydantic schema with `field_validator` for nickname, race, and gender
- Character model updated with `nickname`, `race`, `gender`, and `current_map` fields
- Nickname uniqueness enforced at database level (unique constraint + API check)
- Login response (`Token` schema) includes `has_character` boolean flag to enable smart routing
- The `/login` endpoint queries the `characters` table to determine if the authenticated user has an existing character
- Starting map is automatically assigned based on race (`RACE_STARTING_MAP` dictionary)
- Magmar race creation is blocked on both frontend (disabled button) and backend (schema validation)

## ✅ Game Screen (HUD & Action Menu)

The game screen features a full 3-panel layout with a character HUD and action menu:

### Layout:
- **Top Bar** — Displays the current map name (e.g., "📍 Settlement of Klesva")
- **Left Panel (Character Stats)** — Shows:
  - Character nickname
  - Race & Gender
  - Level
  - Experience (EXP)
  - HP (red, bold)
  - Mana (blue, bold)
- **Center Panel (Game Area)** — Dynamic content area that shows:
  - Welcome message on login
  - Location panel with travel buttons
  - NPC list with interaction buttons
  - Travel countdown timer
  - TODO placeholders for other features
- **Right Panel (Actions)** — Six action buttons:
  - 🎒 Inventory (TODO)
  - 📍 Location (✅ Implemented — shows connected regions, travel)
  - ⚔️ Hunt (TODO)
  - 📬 Mailbox (TODO)
  - 📋 Quests (TODO)
  - 🧙 NPC List (✅ Implemented — shows region NPCs)
- **Bottom Bar** — Logout button

### Maps:
- **Human Starting Map:** Settlement of Klesva
- **Magmar Starting Map:** TBD (race not yet playable)

### Technical Details:
- Character data is fetched via `GET /characters/by-email/{email}` on screen show
- HUD dynamically updates all stat widgets from API response
- `current_map` field added to Character model and `CharacterResponse` schema
- `RACE_STARTING_MAP` dictionary in character model maps races to starting locations
- Center panel uses a `#dynamic_area` container for mounting/unmounting travel and NPC buttons at runtime

## ✅ Location & Travel System

Regions are connected in a node (graph) structure. Clicking "📍 Location" shows the accessible adjacent regions as travel buttons.

### Human Race Map Path:
```
Settlement of Klesva ↔ Baurwill Town ↔ King's Tomb ↔ Light Square ↔ O'Delvays City Center
```

### Travel Mechanics:
- Clicking a region button **moves you there immediately** — the map, top bar, and NPC list update instantly
- After arriving, a **travel cooldown** starts — this blocks only the next travel, not any other action
- The cooldown countdown is displayed in **real time** in the left stats panel (`⏳ Cooldown: Xs`)
- The Location panel also shows the remaining cooldown when opened during an active cooldown
- When the cooldown expires, a toast notification appears and you may travel again
- If you try to travel while the cooldown is active, a warning message is shown

### Travel Time Formula (by character level):
| Level | Time (seconds) | Calculation |
|-------|---------------|-------------|
| 1     | 10s           | Base        |
| 2     | 25s           | 10 + 15     |
| 3     | 40s           | 10 + 30     |
| 4     | 55s           | 10 + 45     |
| 5     | 70s           | 10 + 60     |
| 6     | 80s           | 70 + 10     |
| 7     | 90s           | 70 + 20     |
| 8     | 100s          | 70 + 30     |
| 9     | 110s          | 70 + 40     |
| 10    | 120s          | 70 + 50     |

- **Levels 1–5:** +15 seconds per level
- **Levels 6–10:** +10 seconds per level
- **Max level:** 10

### Technical Details:
- `world_data.py` module contains `HUMAN_MAP_GRAPH`, `REGION_NPCS`, and `get_travel_time()` function
- `POST /characters/travel` endpoint validates adjacency, **enforces cooldown server-side**, updates `current_map`, sets `travel_cooldown_until` in DB, returns `cooldown_remaining`
- `GET /world/regions/{name}` returns connected regions
- **Server-authoritative cooldown:** The `travel_cooldown_until` UTC timestamp is stored in the `characters` table — logging out and back in, or restarting the client, does **not** bypass the cooldown
- `CharacterResponse` includes a computed `cooldown_remaining` field (seconds) derived from the DB timestamp
- The `Character` model has a `cooldown_remaining` property that computes seconds from `travel_cooldown_until` vs. `datetime.now(UTC)`
- Frontend seeds its display timer from the server's `cooldown_remaining` value on login and after travel
- Frontend uses `set_interval(1.0, ...)` for the visual countdown tick (display only — server is the authority)
- `_sanitize_id()` helper converts region/NPC names to safe widget IDs
- Cooldown is displayed in the left stats panel via `#char_cooldown` widget (yellow, bold)

## ✅ NPC System

Each region has NPCs that appear in the NPC List. Clicking an NPC shows their name, role, and description. Interaction (trading, quests, dialogue) is TODO.

### NPCs by Region:

**Settlement of Klesva:**
- Elder Mirwen (Village Elder)
- Torvak the Smith (Blacksmith)
- Lina (Herbalist)

**Baurwill Town:**
- Captain Roderick (Guard Captain)
- Mara the Merchant (General Merchant)
- Old Gregor (Tavern Keeper)
- Sister Alia (Healer)

**King's Tomb:**
- Warden Duskhelm (Tomb Guardian)
- Spirit of King Aldric (Ancient Spirit)

**Light Square:**
- Archmage Solenne (Magic Instructor)
- Trader Fenwick (Rare Goods Merchant)
- Bard Elowen (Bard)

**O'Delvays City Center:**
- King Aldenvale III (King)
- Chancellor Voss (Royal Advisor)
- Guildmaster Theron (Adventurer's Guild)
- Master Armorer Kael (Master Blacksmith)
- Sage Orinthal (Lorekeeper)

### Technical Details:
- `GET /world/npcs/{region_name}` returns NPC list for a region
- NPC data is defined in `REGION_NPCS` dictionary in `world_data.py`
- NPC buttons are dynamically mounted in the center panel
- Clicking an NPC shows their info card; interaction is TODO

## 🚧 TODO: Magmar Race

The Magmar race is defined in the system but not yet playable:

### What's in place:
- `Race.MAGMAR` enum value exists in the character model
- Magmar button appears on character creation screen (disabled, "Coming Soon")
- Backend schema validation rejects Magmar race creation
- `RACE_STARTING_MAP` has a placeholder entry for Magmar

### What's needed:
- Magmar-specific starting map and map graph
- Magmar-specific NPCs and content
- Enable Magmar selection in frontend and backend
- Separate map system for Magmar vs Human races

## ✅ Item & Equipment System

A complete item catalog with 3 character classes, 4 rarities, consumables, and items spanning levels 1–5.

### Character Classes:
| Class | Weapon Type | Strengths |
|-------|------------|-----------|
| **Bonecrusher** | Two-Handed Axe | Low defense, high damage, high crit chance |
| **Skirmisher** | Sword (L) + Dagger (R) | Balanced stats, high evasion |
| **Heavyweight** | Gauntlet (L) + Shield (R) | High HP, high block, damage reduction |
| **Generalist** | Iron Spear (Lv2 only) | Basic starter gear (levels 1–2 only) |

### Equipment Slots by Level:
| Level | Available Slots |
|-------|----------------|
| 1 | Armor, Cuirass (Generalist only) |
| 2 | Weapon (Generalist only) |
| 3 | Weapon(s), Cuirass, Armor, Shirt, Boots |
| 4 | + Shoulder |
| 5 | + Helmet |

### Item Sets by Rarity:
| Color | Rarity | Bonecrusher | Skirmisher | Heavyweight |
|-------|--------|-------------|------------|-------------|
| 🟢 Green | Uncommon | Executioner | Twilight | Mammoth |
| 🔵 Blue | Rare | Anger | North Wind | Giant Slayer |
| 🟣 Purple | Epic | Mysterious Anger | Mysterious North Wind | Mysterious Giant Slayer |
| ⚪ White | Common | — | — | — (Generalist only) |

### Consumables:
- **HP Potion** — Restores 50 HP
- **Mana Potion** — Restores 30 Mana

### Inventory UI:
The inventory is divided into **6 sections** (categories):
1. 🧪 **Consumables** — Potions and usable items
2. ⚔️ **Equipment** — Weapons, armor, and accessories
3. 🐴 **Moroks & Mount** — Mount items (TODO)
4. 📋 **Quest** — Quest-related items (TODO)
5. 📦 **Other** — Miscellaneous items (TODO)
6. 🎁 **Gifts** — Gift items (TODO)

- Clicking 🎒 Inventory shows category buttons with item counts
- Clicking a category shows items in that section, color-coded by rarity
- Clicking an item opens a **proper Textual ModalScreen** overlay with full stats
- Modal has **Close**, **Delete**, and **Sell (TODO)** buttons
- Delete removes the item from the server-side inventory and refreshes the view
- Inventory **persists across sessions** — logging out and back in retains all items

### Debug: Add Item Button
- A yellow **"+ Add Item"** button in the top-right corner of the game screen
- Opens a panel listing all items from the database catalog
- Clicking an item adds it to the character's **server-side inventory**
- Items go to their correct category (equipment, consumables, etc.)
- This button is **temporary for testing** and will be removed later

### Technical Details:
- `InventoryItem` SQLAlchemy model in `inventory.py` — each row is one item instance owned by a character
- Each instance has a unique `id` (DB primary key) used as `instance_id` — prevents duplicate widget ID crashes when owning multiple copies of the same item
- Server endpoints: `GET /inventory/{email}`, `POST /inventory/add`, `POST /inventory/delete`
- `InventoryItemResponse` schema merges DB row with catalog data (name, stats, etc.)
- `ItemDetailModal` is a proper `ModalScreen` subclass with its own CSS
- Player inventory is fetched from server on every inventory open
- CSS classes for rarity colors: `.item-color-white/green/blue/purple`

## ✅ Character Sheet & Inventory Enhancements

The game screen now includes a character sheet modal and upgraded inventory behavior.

### Implemented Features:
- Added a **🧝 Character** action button next to Inventory and Location.
- Character modal shows core stats plus equipped items, with a dedicated **Close** button.
- Inventory items now **stack by catalog item**, showing quantities in the list.
- Item detail modal now includes **Equip/Unequip** actions, with toasts for feedback.

### Technical Details:
- Added `CharacterDetailModal` for character stats + equipped item display in `game_screen.py`.
- Inventory grouping is handled client-side via `_group_inventory()` and displayed with `xN` quantities.
- Item detail modal supports equip/unequip actions with updated button logic.

## ✅ Equipment System (Server-Side Persistence)

The equipment system now has full server-side persistence with level requirements.

### Implemented Features:
- **Level Requirements**: Items cannot be equipped if the character's level is below the item's required level.
- **Equipped Item Indicator**: Equipped items appear separately in inventory with `[EQUIPPED]` label, unequipped items stack together.
- **Character Modal**: Shows currently equipped items for each slot (Weapon, Left Hand, Right Hand, Cuirass, Armor, Shirt, Boots, Shoulder, Helmet).
- **Close Button**: Character modal has a working Close button to return to the game screen.
- **Persistence**: Equipped items are stored in the database and persist across sessions.

### API Endpoints:
- `POST /inventory/equip` - Equip an item (with level check, auto-unequips existing item in slot)
- `POST /inventory/unequip` - Unequip an item

### Database Changes:
- Added `equipped_slot` column to `inventory_items` table (nullable string)

### Technical Details:
- `InventoryItemResponse` now includes `equipped_slot` field
- Equip action checks character level against item's `required_level`
- Equipping an item automatically unequips any existing item in that slot
- Inventory display separates equipped items (shown first with [EQUIPPED] label) from stacked unequipped items
- Character modal builds equipped items dict from inventory data on-the-fly

## ✅ Consumable Stacking

Consumable items now properly stack in the database.

### Implemented Features:
- **Adding Consumables**: When adding a consumable item, if an unequipped stack already exists, the quantity is incremented instead of creating a new row.
- **Deleting Consumables**: When deleting a consumable with quantity > 1, the quantity is decremented instead of deleting the row.
- **Equipment Unchanged**: Equipment items still create new rows (they don't stack) since each piece can be equipped individually.

### Technical Details:
- `POST /inventory/add` checks if item is a consumable and stacks accordingly
- `POST /inventory/delete` decrements quantity for stacked items
- Equipment items bypass stacking logic and always create new database rows

## ✅ Character Stats System

Character stats now properly scale with level and equipped items.

### Implemented Features:
- **Base Stats by Level**: Stats increase automatically as character levels up
  - HP: 100 base + 10 per level
  - Mana: 50 base + 5 per level
  - Strength: 10 base + 2 per level
  - Dexterity: 10 base + 2 per level
  - Intelligence: 10 base + 2 per level
- **Item Bonuses**: Equipped items provide stat bonuses that are added to base stats
- **Character Modal**: Shows both base stats and item bonuses (e.g., "HP: 120 (Base: 100 + Bonus: 20)")
- **Combat Stats**: Displays damage, defense, crit chance, evasion, block chance, and damage reduction from equipped items

### API Endpoints:
- `GET /characters/by-email/{email}/stats` - Returns complete character stats including base, bonus, and total values

### Technical Details:
- `calculate_character_stats()` function computes stats dynamically based on level and equipped items
- Stats are not stored in database; they are calculated on-the-fly from base values + item bonuses
- Character modal fetches stats from API and displays them with breakdown

## ✅ Set Bonuses

Equipping a full set of green, blue, or purple items from the same set grants powerful set bonuses.

### Set Bonus Tiers:

**Green (Uncommon) Sets:**
- **Executioner** (Bonecrusher): +5% Crit Chance, +10 Damage
- **Twilight** (Skirmisher): +5% Evasion, +3% Crit Chance
- **Mammoth** (Heavyweight): +5% Block Chance, +50 HP

**Blue (Rare) Sets:**
- **Anger** (Bonecrusher): +8% Crit Chance, +20 Damage, +5 Strength
- **North Wind** (Skirmisher): +8% Evasion, +5 Dexterity, +5% Crit Chance
- **Giant Slayer** (Heavyweight): +8% Block Chance, +5% Damage Reduction, +100 HP

**Purple (Epic) Sets:**
- **Mysterious Anger** (Bonecrusher): +12% Crit Chance, +35 Damage, +10 Strength, +50 HP
- **Mysterious North Wind** (Skirmisher): +12% Evasion, +10 Dexterity, +8% Crit Chance, +15 Damage
- **Mysterious Giant Slayer** (Heavyweight): +12% Block Chance, +8% Damage Reduction, +150 HP, +20 Defense

### Technical Details:
- Set bonuses are class-appropriate (Bonecrusher = crit/damage, Skirmisher = evasion, Heavyweight = block/defense)
- Full set requires 7 pieces: weapon(s), cuirass, armor, shirt, boots, shoulder, helmet
- Set bonus is displayed in character modal when active

## ✅ Online Players List

Players can now see and interact with other players on the same map.

### Implemented Features:
- **Online Players Panel**: Located in the bottom left of the left stats panel
- **Auto-Refresh**: List refreshes every 10 seconds
- **Player Info**: Shows level and nickname for each player (e.g., "[Lv5] PlayerName")
- **Click to View**: Clicking a player opens their character modal showing:
  - Basic info (nickname, race, gender, level)
  - Stats (base + bonus breakdown)
  - Combat stats
  - Equipped items
  - Set bonus (if active)

### API Endpoints:
- `GET /world/players-on-map/{map_name}` - Returns list of online players on a map
- `GET /characters/view/{nickname}` - Returns detailed character info for viewing another player

### Technical Details:
- Online players are tracked in-memory with 5-minute timeout
- Player location updates when traveling
- Logout button moved to top bar next to "+ Add Item" button

## ✅ Logout Status Tracking

Logout now properly marks users inactive and login marks them active.

### Implemented Features:
- **Active status updates**: Login sets `users.is_active = True`, logout sets `users.is_active = False`
- **Logout endpoint**: Added `POST /logout` to mark users inactive and remove them from the online list
- **Client logout flow**: Game screen calls the logout endpoint before returning to the login screen

### API Endpoints:
- `POST /logout` - Marks user inactive and clears online player tracking

### Technical Details:
- `LogoutRequest` schema added for logout payloads
- Logout clears chat state to ensure history resets on the next login

## ✅ Real-time Chat Modal

Added a chat modal with tabs, message history, and whisper targeting.

### Implemented Features:
- **Chat button**: Added to the top bar (left of Logout)
- **Modal chat UI**: 3 tabs (General, Group, Clan), Close button, and sender list buttons
- **Chat history**: Messages persist while the player remains logged in; resets after logout/login
- **Whisper targeting**: Clicking sender names appends `/w name1 name2 ...` to the input field
- **Private messaging**: Supports whispering to multiple players at once
- **Keyboard send**: Pressing Enter in chat input sends the message

### API Endpoints:
- `WebSocket /ws` - Handles chat broadcast, whispers, and player identification

### Technical Details:
- WebSocket manager tracks sockets per nickname for targeted whispers
- Chat history stored client-side per channel and shared across modal opens
- Whisper formatting uses `/w name1 name2 ... message` syntax
- Chat modal guards sender list updates to avoid mount timing NoMatches
- Chat layout updated with fixed input height, smaller send/close buttons, and larger history area
- Chat listener now uses `call_later` to update the modal instead of `call_from_thread`
- Fixed CSS placeholder error by removing unsupported `::placeholder` selector
- Chat history now uses `VerticalScroll` for scrollable message viewing
- Whisper display format: "[Whisper] sender to target1, target2: message" with red text support
- Sender click behavior improved: appends to existing `/w` command or creates new one
- Layout stabilized with proper widget IDs (`chat-history-content`)

## ✅ Online Player Refresh Fixes

Relogging and toggling clients now repopulates online players correctly.

### Implemented Features:
- **Login refresh**: Login updates online player tracking immediately when a character exists
- **Character fetch refresh**: Online player refresh retries by re-fetching the character to re-register the player

### Technical Details:
- `POST /login` now updates online players when a character exists
- Online player refresh triggers `GET /characters/by-email/{email}` when no players are returned

## ✅ Fight / Hunt System

A complete turn-based fight system has been implemented, running over WebSocket for multiplayer-ready architecture.

### Mob Definitions

Mobs are defined per region in `world_data.py`:

| Mob | Level | Display Name | HP | Damage | Region |
|-----|-------|--------------|----|--------|--------|
| Krets | 1 | Krets [1] | 55 | 2-6 | Settlement of Klesva |
| Aggressive Krets | 2 | Aggressive Krets [2] | 70 | 4-8 | Baurwill Town, King's Tomb, Light Square, O'Delvays City Center |
| Skeleton | 3 | Skeleton [3] | 90 | 6-10 | Baurwill Town, King's Tomb, Light Square, O'Delvays City Center |

- Mobs are **unlimited** — they always appear in the hunt panel and can be fought repeatedly
- Mob abilities (crit, block, evasion): 15% base at level 1, +2% per subsequent level
  - Level 1: 15% each
  - Level 2: 17% each
  - Level 3: 19% each

### Hunt Panel

- Clicking **⚔️ Hunt** in the action menu shows available mobs for the current region
- Each mob button displays: name, level, HP, and damage range
- Clicking a mob starts a battle by pushing the Fight screen

### Fight Screen Layout

The fight screen is divided into **2 main sections**:

**Left Panel — Attack Options & Fight Log:**
- **Turn indicator** — Shows whose turn it is
- **Timer** — 10-second countdown for player's turn
- **3 Attack buttons** — Head (🎯), Chest (🫁), Legs (🦵)
  - **Head**: +20% damage, +10% chance to be evaded
  - **Chest**: Balanced (no modifiers)
  - **Legs**: -15% damage, -5% chance to be evaded (more accurate)
- **Fight log** — Scrollable log showing all battle events

**Right Panel — Battle Participants:**
- Divided vertically into **Player** (left) and **Mob** (right, in red)
- Each side shows: Name, HP/Max HP, Mana/Max Mana (stacked vertically)

### Turn-Based Combat Mechanics

- **Player's turn**: Must attack within **10 seconds**
  - If time runs out, an **automatic plain attack** is executed (50% less damage)
  - Plain attack is not head/chest/legs — it's a separate "plain" attack type
- **Mob's turn**: Attacks after a random **1-4 second** delay
- Combat is fully **server-authoritative** via WebSocket (`/ws/fight`)

### Combat Calculations

**Player Attack:**
1. Base damage = (Strength / 5) + Weapon Damage, with ±20% randomness
2. Attack type multiplier applied (head: 1.2x, chest: 1.0x, legs: 0.85x, plain: 0.5x)
3. Check mob evasion (dodge) — if dodged, 0 damage
4. Check mob block — if blocked, 50% damage
5. Check player critical hit — if crit, 150% damage

**Mob Attack:**
1. Base damage = random between damage_min and damage_max
2. Check player evasion (dodge) — if dodged, 0 damage
3. Check player block — if blocked, 50% damage with damage reduction applied
4. Check mob critical hit — if crit, 150% damage with defense mitigation
5. Normal attack: damage reduced by defense/4 and damage reduction %

### Special Events (shown in fight log)

- 💥 **Critical Hit** — 150% damage (player: from crit_chance stat; mob: from level-based chance)
- 💨 **Dodge/Evasion** — Attack completely avoided (player: from evasion stat; mob: from level-based chance)
- 🔰 **Block** — Damage reduced by 50% (player: from block_chance stat; mob: from level-based chance)
- ⏰ **Auto-Attack** — Triggered when player doesn't act within 10 seconds

### Fight Result

- **Victory** — "🏆 VICTORIOUS" message box with Close button
- **Defeat** — "💀 DEFEAT" message box with Close button
- Closing the result modal returns to the game screen

### API Endpoints

- `GET /world/mobs/{region_name}` — Returns list of mobs available in a region
- `WebSocket /ws/fight` — Real-time fight communication
  - `start_fight` — Initiates a fight with a specific mob
  - `attack` — Player attacks with head/chest/legs
  - `leave_fight` — Player leaves the fight

### Technical Details

- `FightInstance` class in `backend/main.py` manages individual fight state
- `FightScreen` in `frontend/screens/fight_screen.py` is a full-screen Textual Screen
- `FightResultModal` is a ModalScreen for victory/defeat display
- Fight WebSocket auto-cleans up on disconnect
- Turn timer runs server-side (10s auto-attack) with client-side visual countdown
- Mob data defined in `MOB_DEFINITIONS` dict in `world_data.py`
- `REGION_MOBS` maps regions to available mob names
- Player combat stats (crit, evasion, block, damage, defense, damage_reduction) come from equipped items and set bonuses
- Fight screen uses its own CSS embedded in the Screen class

### Files Modified/Created

- **Created:** `dragons_legacy/frontend/screens/fight_screen.py` — Fight screen UI + result modal
- **Modified:** `dragons_legacy/models/world_data.py` — Added mob definitions and region mob mappings
- **Modified:** `dragons_legacy/backend/main.py` — Added fight WebSocket endpoint, FightInstance class, mob API endpoint
- **Modified:** `dragons_legacy/backend/schemas.py` — Added MobResponse, StartFightRequest schemas
- **Modified:** `dragons_legacy/frontend/api_client.py` — Added `get_region_mobs()` method
- **Modified:** `dragons_legacy/frontend/screens/game_screen.py` — Added hunt panel, mob buttons, fight screen integration
- **Modified:** `dragons_legacy/frontend/screens/__init__.py` — Exported FightScreen
- **Modified:** `dragons_legacy/frontend/styles.py` — Added mob button styles

## ✅ Fight Screen Chat Button

Added a chat button to the fight screen so players can access chat during battle.

### Implemented Features:
- **💬 Chat button** in the top-right corner of the fight screen's top bar
- Opens the same ChatModal used in the game screen
- Delegates chat functionality to the GameScreen instance (which remains on the screen stack underneath)
- Styled consistently with the game screen's chat button

### Technical Details:
- Chat button added to the fight screen's top bar (`fight-chat-btn` CSS class)
- Button handler searches the screen stack for the `GameScreen` instance and calls `_open_chat_modal()`
- No duplicate chat WebSocket connection — reuses the game screen's existing chat connection

### Files Modified:
- **Modified:** `dragons_legacy/frontend/screens/fight_screen.py` — Added chat button to compose, button handler, and CSS

## ✅ Fight Persistence & Reconnection

Battles now persist on the server when a player disconnects (logout, close, crash). When re-entering the game, players are forced back into their active fight.

### Implemented Features:
- **Fight persistence**: When a player disconnects during a battle, the fight continues server-side
  - The mob keeps attacking the player via auto-attacks
  - The player's turn timer still triggers auto-attacks at 50% damage
  - The fight only ends when one side's HP reaches 0
- **Fight reconnection**: When a player logs back in while in an active fight:
  - The game screen automatically detects the active fight via REST API
  - The fight screen is pushed immediately in "rejoin" mode
  - Full fight state is restored: HP, mana, turn state, and complete fight log history
  - The player can continue fighting from where they left off
- **Escape prevention**: Players cannot leave the fight screen while a battle is active
  - Pressing Escape during an active fight shows a warning in the fight log
  - The fight screen can only be exited after the fight ends (victory or defeat)
  - The fight result modal's Close button pops the fight screen as before

### API Endpoints:
- `GET /fight/active/{email}` — Check if a player has an active fight (returns fight state or 404)
- `WebSocket /ws/fight` — New `rejoin_fight` message type for reconnecting to an existing fight

### WebSocket Protocol Changes:
- **New message type: `rejoin_fight`**
  - Client sends: `{"type": "rejoin_fight", "email": "..."}`
  - Server responds: `{"type": "fight_rejoined", "state": {...}, "log_history": [...], "log": "⚡ Reconnected!"}`
- **`start_fight` now rejects** if the player already has an active fight (must rejoin instead)
- **Disconnect behavior**: Server sets `websocket = None` on the fight instance instead of deleting it
- **`safe_send()` method**: All fight messages use `fight.safe_send()` which silently handles disconnected clients
- **Fight log history**: All fight events are stored in `fight.fight_log` for replay on reconnection

### Technical Details:
- `FightInstance.websocket` can be `None` when player is disconnected
- `FightInstance.safe_send()` wraps all WebSocket sends with error handling
- `FightInstance.fight_log` stores all battle event messages for reconnection replay
- `_player_turn_timeout()` and `_mob_turn()` no longer take a `websocket` parameter — they use `fight.safe_send()` instead
- `_end_fight()` no longer takes a `websocket` parameter — uses `fight.safe_send()` for the fight_over message
- `FightScreen.__init__` accepts optional `rejoin=True` parameter to skip `start_fight` and send `rejoin_fight` instead
- `FightScreen._disconnect_fight()` no longer sends `leave_fight` — the fight persists server-side
- `FightScreen.action_try_leave()` blocks escape key while `_fight_active` is True
- `GameScreen._check_active_fight()` queries `GET /fight/active/{email}` on every `on_show` and pushes FightScreen in rejoin mode if active
- `APIClient.get_active_fight()` method added for the active fight check

### Files Modified:
- **Modified:** `dragons_legacy/backend/main.py` — Fight persistence, `safe_send()`, `rejoin_fight`, active fight endpoint, disconnect handling
- **Modified:** `dragons_legacy/frontend/screens/fight_screen.py` — Rejoin mode, escape prevention, disconnect without leave
- **Modified:** `dragons_legacy/frontend/screens/game_screen.py` — Active fight check on `on_show`
- **Modified:** `dragons_legacy/frontend/api_client.py` — Added `get_active_fight()` method

## ✅ Currency System & Mob Loot Drops

A complete currency system has been implemented with gold, silver, and copper, along with mob loot drops on victory.

### Currency Tiers:
| Currency | Value | Color |
|----------|-------|-------|
| **Gold (g)** | 1 gold = 100 silver = 10,000 copper | Gold (rgb 255,215,0) |
| **Silver (s)** | 1 silver = 100 copper | Silver (rgb 192,192,192) |
| **Copper (c)** | Base currency | Copper (rgb 184,115,51) |

### Display Format:
- Currency is displayed as `Xg Ys Zc` with colored letters (g=gold, s=silver, c=copper) and white amounts
- Zero-value currencies are hidden **except copper** (which is always shown)
- Examples: `5s 0c`, `1g 5s 0c`, `0c`, `5g 3s 55c`

### Mob Loot Drops:
| Mob | Level | Loot Range |
|-----|-------|------------|
| Krets | 1 | 40c – 1s 12c (40–112 copper) |
| Aggressive Krets | 2 | 1s 0c – 1s 80c (100–180 copper) |
| Skeleton | 3 | 3s 0c – 7s 0c (300–700 copper) |

### Where Currency is Displayed:
1. **HUD (Left Panel)** — `💰 Xg Ys Zc` shown below Mana in the character stats panel
2. **Inventory Screen** — `💰 Xg Ys Zc` shown at the top of the inventory view
3. **Fight Log** — `💰 Loot: Xg Ys Zc` logged when a fight ends in victory
4. **Fight Result Modal** — `💰 Xg Ys Zc` shown below the victory message

### Technical Details:
- Currency stored as a single `copper` integer column on the `characters` table (all conversions are computed)
- `copper_to_parts(total_copper)` converts total copper to `(gold, silver, copper)` tuple
- `format_currency_plain(total_copper)` returns plain text format (e.g., "5s 0c")
- `_format_currency_rich(total_copper)` returns Rich markup with colored letters for Textual display
- `CharacterResponse` schema includes `copper` field
- `_end_fight()` rolls loot from `loot_copper_min`/`loot_copper_max` on mob definition and awards it to the character in DB
- `FightResultModal` accepts optional `loot_copper` parameter to display loot in the result overlay
- `fight_over` WebSocket message includes `loot_copper` field

### Files Modified/Created:
- **Modified:** `dragons_legacy/models/character.py` — Added `copper` column
- **Modified:** `dragons_legacy/models/world_data.py` — Added `loot_copper_min`/`loot_copper_max` to mob definitions, added `copper_to_parts()` and `format_currency_plain()` helpers
- **Modified:** `dragons_legacy/backend/schemas.py` — Added `copper` field to `CharacterResponse`
- **Modified:** `dragons_legacy/backend/main.py` — Loot rolling + currency award in `_end_fight()`, `FightInstance.email` tracking
- **Modified:** `dragons_legacy/frontend/screens/fight_screen.py` — `_format_currency_rich()` helper, loot display in fight log + result modal
- **Modified:** `dragons_legacy/frontend/screens/game_screen.py` — Currency display in HUD and inventory
- **Modified:** `dragons_legacy/frontend/styles.py` — Added `.game-stat-currency` CSS class

## ✅ Level & EXP System

A complete leveling system with EXP rewards from combat, level-based scaling, and automatic level-up.

### EXP Requirements (per level, resets to 0 after each level-up):
| Level | EXP to Next Level | Formula |
|-------|------------------|---------|
| 1 | 100 | 100 × 2^0 |
| 2 | 200 | 100 × 2^1 |
| 3 | 400 | 100 × 2^2 |
| 4 | 800 | 100 × 2^3 |
| 5 | 1,600 | 100 × 2^4 |
| ... | ... | 100 × 2^(level-1) |

### Base EXP from Mobs:
| Mob | Level | Base EXP |
|-----|-------|----------|
| Krets | 1 | 5 EXP |
| Aggressive Krets | 2 | 10 EXP |
| Skeleton | 3 | 25 EXP |

### Level Difference Scaling:
Both EXP and loot are scaled based on the difference between player level and mob level:
- **Player at or below mob level**: 100% EXP and loot
- **Player 1 level above mob**: 70% EXP and loot
- **Player 2 levels above mob**: 40% EXP and loot
- **Player 3 levels above mob**: 10% EXP and loot
- **Player 4+ levels above mob**: 0% — no EXP or loot at all

### Level-Up Mechanics:
- EXP is awarded on victory only (defeat gives nothing)
- EXP resets to 0 after each level-up (excess carries over)
- Multiple level-ups can occur from a single fight if EXP is sufficient
- Level-up notification appears in fight log and fight result modal

### Where EXP is Displayed:
1. **HUD (Left Panel)** — `✨ EXP: X / Y` where Y is the EXP required for next level
2. **Character Modal** — `EXP: X / Y` in the character info section
3. **Fight Log** — `✨ +X EXP` logged when a fight ends in victory
4. **Fight Result Modal** — `✨ +X EXP` shown below loot, plus `🎉 LEVEL UP!` if applicable

### Technical Details:
- `exp_required_for_level(level)` helper in `world_data.py` — returns `100 * 2^(level-1)`
- `calculate_level_penalty(player_level, mob_level)` helper — returns multiplier 0.0–1.0
- `base_exp` field added to each mob definition in `MOB_DEFINITIONS`
- `_end_fight()` calculates scaled EXP and loot, awards to DB, handles level-up loop
- `FightInstance.player_level` tracks player level for penalty calculations
- `fight_over` WebSocket message includes `exp_gained`, `leveled_up`, `new_level` fields
- `FightResultModal` accepts and displays EXP gained and level-up info
- HUD shows `EXP: current / required` format

### HUD Refresh Fix:
- When returning from a fight (closing the fight result modal), the game screen HUD now explicitly refreshes
- `refresh_after_fight()` method added to `GameScreen` for explicit post-fight data reload
- Fight result modal's close callback finds the `GameScreen` on the stack and triggers `refresh_after_fight()`
- This ensures currency, EXP, and level display are always up-to-date after combat

### Files Modified:
- **Modified:** `dragons_legacy/models/world_data.py` — Added `base_exp` to mob definitions, added `exp_required_for_level()` and `calculate_level_penalty()` helpers
- **Modified:** `dragons_legacy/backend/main.py` — EXP/loot scaling in `_end_fight()`, level-up logic, `FightInstance.player_level`, new imports
- **Modified:** `dragons_legacy/frontend/screens/fight_screen.py` — EXP display in fight log, `FightResultModal` shows EXP + level-up, post-fight HUD refresh callback
- **Modified:** `dragons_legacy/frontend/screens/game_screen.py` — HUD shows `EXP: X / Y`, character modal shows `EXP: X / Y`, `refresh_after_fight()` method, import `exp_required_for_level`

## ✅ Morok System

Added morok inventory items, equip limits, and a dedicated morok bag slot to improve playability.

### Implemented Features:
- **Morok catalog items**: Moroks are auto-generated from mob definitions at 70% of the mob's power.
- **Inventory category**: Moroks appear under the existing 🐴 Moroks & Mount category.
- **Equip limit**: Players can equip up to 5 moroks (equipping moroks no longer unequips existing moroks).
- **Morok bag slot**: Added a dedicated morok slot (index 2) that only accepts a single morok type, max 5.
- **UI updates**: Bag screens and add-to-bag modal now label the morok slot and handle its capacity.

### Technical Details:
- `item_data.py` now builds `MOROK_ITEMS` from `MOB_DEFINITIONS` with the `[LvX] <Mob> Morok - Medallion` naming convention.
- `inventory/equip` allows up to 5 equipped moroks while keeping existing equipment equip behavior for other slots.
- Bag logic enforces the morok-only slot and prevents moroks from being used in fights.
- Bag slot metadata now reports max quantity for the morok slot.

### Files Modified:
- **Modified:** `dragons_legacy/models/item_data.py` — Added morok catalog generation.
- **Modified:** `dragons_legacy/backend/main.py` — Enforced morok equip limit and morok bag slot rules.
- **Modified:** `dragons_legacy/models/bag.py` — Added morok slot constants and updated slot count.
- **Modified:** `dragons_legacy/frontend/screens/game_screen.py` — Morok use button + bag UI updates.
- **Modified:** `dragons_legacy/frontend/screens/fight_screen.py` — Added morok slot to fight screen bag panel.

### Follow-up Fixes:
- Removed duplicate level prefix from morok names (was `[Lv1] [Lv1] Krets Morok...`, now `[Lv1] Krets Morok...`).
- Fixed available quantity display for moroks in the use modal by computing stack quantity from inventory instances.
- Modal now shows only the morok slot when using moroks, and only consumable slots when using potions.
- Added morok slot (read-only) to the fight screen bag panel for future morok summoning support.

## 🚧 TODO: Game Features

The following features are not yet implemented:

- **Item Selling** — Sell button in modal (currently disabled/TODO)
- **Mailbox** — Player-to-player messaging system
- **Quests** — NPC quest acceptance, tracking, and rewards
- **NPC Interaction** — Trading, dialogue, and quest assignment with NPCs

## 🎯 Future Enhancements

### Game Features
- **Turn-based Combat System**
- **Inventory Management**
- **Quest System**
- **Character Progression**
- **Multiplayer Interactions**
- **Real-time Chat**

### Technical Improvements
- **Configuration Management** - Environment-based settings
- **Logging System** - Comprehensive application logging
- **Error Handling** - More robust error management
- **Testing Suite** - Unit and integration tests
- **Docker Support** - Containerization for easy deployment
- **Database Migrations** - Alembic integration

### UI/UX Enhancements
- **Sound Effects** - Terminal bell integration
- **Animations** - Smooth transitions and effects
- **Themes** - Multiple color schemes
- **Accessibility** - Screen reader support
- **Mobile Support** - Responsive design considerations

## 🔒 Security Considerations

### Current Security Measures
- Password hashing with bcrypt
- JWT token authentication
- Input validation and sanitization
- SQL injection prevention through SQLAlchemy
- HTTPS ready (requires SSL certificate in production)

### Production Recommendations
- Change default JWT secret key
- Implement rate limiting
- Add CORS configuration
- Use environment variables for sensitive data
- Implement proper logging and monitoring
- Add database backup strategies

## 🐛 Known Issues

### Current Limitations
- Game action buttons (Mailbox, Quests) show TODO placeholders
- NPC interaction (trading, quests, dialogue) is TODO
- Magmar race is not yet playable (disabled in character creation)
- Fights now award EXP and loot (with level-based scaling)
- No user session persistence
- Limited error handling in some edge cases

### Development Notes
- Database file (`dragons_legacy.db`) is created automatically
- API server must be running before starting TUI client
- All passwords are hashed and cannot be recovered (only reset)
- Security answers are case-insensitive but stored hashed

## 📊 Database Schema

### Users Table
- `id` (Primary Key)
- `email` (Unique, Indexed)
- `hashed_password`
- `is_active`
- `created_at`
- `updated_at`
- `security_question_id` (Foreign Key)
- `security_answer_hash`

### Security Questions Table
- `id` (Primary Key)
- `question_text`
- `is_active`

### Characters Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `nickname` (Unique, max 12 chars)
- `race` (magmar / human)
- `gender` (female / male)
- `current_map` (starting map assigned by race)
- `travel_cooldown_until` (UTC timestamp, nullable — server-side cooldown)
- `level` (default 1, auto-increments on level-up)
- `experience` (default 0, resets to 0 after each level-up)
- `copper` (default 0, total copper currency)
- `health`
- `mana`
- `strength`
- `dexterity`
- `intelligence`
- `created_at`
- `updated_at`

## 🎨 Design Philosophy

### User Interface
- **Simplicity** - Clean, uncluttered design
- **Accessibility** - Keyboard-friendly navigation
- **Feedback** - Clear visual feedback for all actions
- **Consistency** - Uniform styling across all screens
- **Fantasy Theme** - Dragon and medieval RPG aesthetics

### Code Architecture
- **Modularity** - Separate concerns with clear boundaries
- **Async/Await** - Non-blocking operations throughout
- **Type Hints** - Clear type annotations for maintainability
- **Documentation** - Comprehensive docstrings and comments
- **Error Handling** - Graceful degradation and user feedback

## 🏆 Achievements

This project successfully demonstrates:

1. **Full-Stack Development** - Complete backend and frontend implementation
2. **Modern Python Practices** - Async/await, type hints, modern libraries
3. **Security Implementation** - Authentication, authorization, and data protection
4. **User Experience Design** - Intuitive and beautiful terminal interface
5. **API Design** - RESTful endpoints with proper HTTP status codes
6. **Database Design** - Normalized schema with relationships
7. **Error Handling** - Comprehensive error management and user feedback
8. **Documentation** - Clear and detailed project documentation

---

**Legend of Dragon's Legacy** - *Where your adventure begins in the terminal!* 🐉⚔️