"""
Game screen for Legend of Dragon's Legacy
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Static, Input
from textual.css.query import NoMatches
import asyncio
import websockets
import json


# ============================================================
# Character Detail Modal
# ============================================================

class CharacterDetailModal(ModalScreen):
    """Modal overlay showing character information and equipment."""

    CSS = """
    CharacterDetailModal {
        align: center middle;
    }
    #character-modal {
        width: 70;
        height: auto;
        max-height: 90vh;
        border: solid $accent;
        background: $surface;
        padding: 2;
        overflow-y: auto;
    }
    #character-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    #character-info {
        color: $text;
        margin: 1 0;
        width: 100%;
        height: auto;
    }
    #equipped-header {
        text-style: bold;
        color: $secondary;
        margin-top: 1;
    }
    .equipped-row {
        layout: horizontal;
        width: 100%;
        margin: 0 0 1 0;
        height: auto;
    }
    .equipped-label {
        width: 18;
        color: $accent;
    }
    .equipped-value {
        width: 1fr;
        color: $text;
    }
    #character-close-row {
        layout: horizontal;
        width: 100%;
        margin-top: 2;
        height: auto;
    }
    #character-close-row Button {
        width: 1fr;
    }
    """

    def __init__(self, character: dict, equipped_items: dict[str, dict], stats: dict = None):
        super().__init__()
        self.character = character
        self.equipped_items = equipped_items
        self.stats = stats or {}

    def compose(self) -> ComposeResult:
        char = self.character
        race = str(char.get("race", "")).capitalize()
        gender = str(char.get("gender", "")).capitalize()
        
        # Get stats data
        base_stats = self.stats.get("base_stats", {})
        bonus_stats = self.stats.get("bonus_stats", {})
        total_stats = self.stats.get("total_stats", {})
        combat_stats = self.stats.get("combat_stats", {})
        
        # Basic info
        char_level = self.stats.get("level", char.get("level", 1))
        char_exp = self.stats.get("experience", char.get("experience", 0))
        from dragons_legacy.models.world_data import exp_required_for_level as _exp_req
        exp_needed = _exp_req(char_level)
        lines = [
            "Nickname: " + str(char.get("nickname", "")),
            "Race: " + race,
            "Gender: " + gender,
            "Level: " + str(char_level),
            "EXP: " + str(char_exp) + " / " + str(exp_needed),
            "",
        ]
        
        # Stats section with base + bonus format
        lines.append("📊 STATS")
        lines.append("")
        
        # Helper to format stat with bonus
        def format_stat(name: str, base_key: str, bonus_key: str, total_key: str) -> str:
            base = base_stats.get(base_key, 0)
            bonus = bonus_stats.get(bonus_key, 0)
            total = total_stats.get(total_key, 0)
            if bonus > 0:
                return f"{name}: {total} (Base: {base} + Bonus: {bonus})"
            return f"{name}: {total}"
        
        lines.append(format_stat("❤️  HP", "health", "health", "health"))
        lines.append(format_stat("💧 Mana", "mana", "mana", "mana"))
        lines.append(format_stat("💪 Strength", "strength", "strength", "strength"))
        lines.append(format_stat("🎯 Dexterity", "dexterity", "dexterity", "dexterity"))
        lines.append(format_stat("🧠 Intelligence", "intelligence", "intelligence", "intelligence"))
        lines.append("")
        
        # Combat stats from items
        if combat_stats:
            lines.append("⚔️ COMBAT STATS")
            lines.append("")
            if combat_stats.get("damage", 0) > 0:
                lines.append(f"⚔️  Damage: {combat_stats['damage']}")
            if combat_stats.get("defense", 0) > 0:
                lines.append(f"🛡️  Defense: {combat_stats['defense']}")
            if combat_stats.get("crit_chance", 0) > 0:
                lines.append(f"💥 Crit Chance: {combat_stats['crit_chance']}%")
            if combat_stats.get("evasion", 0) > 0:
                lines.append(f"💨 Evasion: {combat_stats['evasion']}%")
            if combat_stats.get("block_chance", 0) > 0:
                lines.append(f"🔰 Block Chance: {combat_stats['block_chance']}%")
            if combat_stats.get("damage_reduction", 0) > 0:
                lines.append(f"🪨 Damage Reduction: {combat_stats['damage_reduction']}%")
            lines.append("")
        
        # Set bonus display
        set_bonus = self.stats.get("set_bonus")
        if set_bonus and set_bonus.get("description"):
            lines.append("🎁 SET BONUS (Full Set Equipped)")
            lines.append("")
            lines.append(f"✨ {set_bonus['description']}")
            lines.append("")

        equipped_lines = [
            ("Weapon", self._equipped_name("weapon")),
            ("Left Hand", self._equipped_name("weapon_left")),
            ("Right Hand", self._equipped_name("weapon_right")),
            ("Cuirass", self._equipped_name("cuirass")),
            ("Armor", self._equipped_name("armor")),
            ("Shirt", self._equipped_name("shirt")),
            ("Boots", self._equipped_name("boots")),
            ("Shoulder", self._equipped_name("shoulder")),
            ("Helmet", self._equipped_name("helmet")),
        ]

        with Container(id="character-modal"):
            yield Static("🧝 Character Sheet", id="character-title")
            yield Static("\n".join(lines), id="character-info")
            yield Static("⚔️ Equipped Items", id="equipped-header")
            for label, value in equipped_lines:
                with Horizontal(classes="equipped-row"):
                    yield Static(label + ":", classes="equipped-label")
                    yield Static(value, classes="equipped-value")
            with Horizontal(id="character-close-row"):
                yield Button("Close", variant="default", id="character_close")

    def _equipped_name(self, slot: str) -> str:
        item = self.equipped_items.get(slot)
        if not item:
            return "(None)"
        return item.get("name", "Unknown")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "character_close":
            self.dismiss(None)



from dragons_legacy.frontend.api_client import APIClient
from dragons_legacy.frontend.screens.fight_screen import FightScreen, _format_currency_rich
from dragons_legacy.models.world_data import copper_to_parts, exp_required_for_level

# Inventory category display names (keep in sync with item_data.py)
_CAT_DISPLAY = {
    "consumables": "🧪 Consumables",
    "equipment": "⚔️ Equipment",
    "moroks_mount": "🐴 Moroks & Mount",
    "quest": "📋 Quest",
    "other": "📦 Other",
    "gifts": "🎁 Gifts",
}

_CAT_ORDER = ["consumables", "equipment", "moroks_mount", "quest", "other", "gifts"]


def _sanitize_id(text: str) -> str:
    """Turn a display name into a safe widget-id fragment (no quotes, no spaces)."""
    return text.replace(" ", "_").replace("'", "")


# ============================================================
# Item Detail Modal (proper Textual ModalScreen)
# ============================================================

class ChatModal(ModalScreen):
    """Chat modal with channel tabs and message history."""

    CSS = """
    ChatModal {
        align: center middle;
    }
    #chat-modal {
        width: 90;
        height: auto;
        max-height: 95vh;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
        overflow-y: auto;
    }
    #chat-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    #chat-tabs {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }
    #chat-tabs Button {
        width: 1fr;
        margin: 0 1;
    }
    #chat-history {
        height: auto;
        min-height: 12;
        max-height: 20;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface-darken-1;
    }
    #chat-history-content {
        width: 100%;
        height: auto;
    }
    #chat-senders {
        height: auto;
        max-height: 6;
        width: 100%;
        border: solid $primary;
        padding: 1;
        margin-top: 1;
    }
    #chat-input-row {
        layout: horizontal;
        height: 3;
        width: 100%;
        margin-top: 1;
        align: left middle;
    }
    #chat-input {
        width: 1fr;
        height: 3;
    }
    .chat-send-btn {
        width: 10;
        height: 3;
        margin-left: 1;
    }
    #chat-close-row {
        layout: horizontal;
        height: 3;
        width: 100%;
        margin-top: 1;
        align: right middle;
    }
    #chat-close-row Button {
        width: 12;
        height: 3;
    }
    """

    def __init__(self, channel: str, history: list[dict], selected_targets: list[str]):
        super().__init__()
        self.channel = channel
        self.history = history
        self.selected_targets = selected_targets

    def compose(self) -> ComposeResult:
        with Container(id="chat-modal"):
            yield Static("💬 Realm Chat", id="chat-title")
            with Horizontal(id="chat-tabs"):
                yield Button("General", variant="success" if self.channel == "general" else "default", id="chat_tab_general")
                yield Button("Group", variant="success" if self.channel == "group" else "default", id="chat_tab_group")
                yield Button("Clan", variant="success" if self.channel == "clan" else "default", id="chat_tab_clan")
            with VerticalScroll(id="chat-history"):
                yield Static(self._format_history(), id="chat-history-content")
            with Vertical(id="chat-senders"):
                yield Static("Click a sender name below to whisper.", id="chat-senders-hint")
                yield Vertical(id="chat-senders-list")
            with Horizontal(id="chat-input-row"):
                yield Input(placeholder="Type a message...", id="chat-input")
                yield Button("Send", variant="success", id="chat_send", classes="chat-send-btn")
            with Horizontal(id="chat-close-row"):
                yield Button("Close", variant="default", id="chat_close")

    def _format_history(self) -> str:
        lines = []
        for entry in self.history:
            sender = entry.get("sender", "")
            message = entry.get("message", "")
            targets = entry.get("targets", [])
            is_private = entry.get("private", False)
            if is_private:
                targets_str = ", ".join(targets) if targets else ""
                # Red color for whisper messages
                lines.append(f"[red][Whisper] {sender} to {targets_str}: {message}[/red]")
            else:
                lines.append(f"{sender}: {message}")
        return "\n".join(lines) if lines else "No messages yet."

    def render_sender_buttons(self, container: Vertical) -> None:
        container.remove_children()
        senders = sorted({entry.get("sender") for entry in self.history if entry.get("sender")})
        if not senders:
            container.mount(Static("No senders yet.", id="chat-no-senders"))
            return
        for sender in senders:
            variant = "success" if sender in self.selected_targets else "default"
            container.mount(
                Button(sender, variant=variant, id=f"chat_sender_{sender}")
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        game_screen = self.app.get_screen("game")
        if event.button.id == "chat_close":
            game_screen = self.app.get_screen("game")
            if isinstance(game_screen, GameScreen):
                game_screen._chat_modal_opening = False
            self.app.pop_screen()
            return
        if event.button.id == "chat_send":
            if isinstance(game_screen, GameScreen):
                self.run_worker(game_screen._send_chat_message(self), exclusive=False)
            return
        if event.button.id.startswith("chat_tab_"):
            if isinstance(game_screen, GameScreen):
                channel = event.button.id[len("chat_tab_"):]
                game_screen._switch_chat_channel(channel, self)
            return
        if event.button.id.startswith("chat_sender_"):
            if isinstance(game_screen, GameScreen):
                sender = event.button.id[len("chat_sender_"):]
                game_screen._handle_sender_click(sender, self)
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            game_screen = self.app.get_screen("game")
            if isinstance(game_screen, GameScreen):
                self.run_worker(game_screen._send_chat_message(self), exclusive=False)


class UsePotionQuantityModal(ModalScreen):
    """Modal asking how many potions to add to a bag slot."""

    CSS = """
    UsePotionQuantityModal {
        align: center middle;
    }
    #use-qty-dialog {
        width: 50;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 2;
    }
    #use-qty-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    #use-qty-info {
        color: $text;
        text-align: center;
        margin: 1 0;
    }
    #use-qty-error {
        color: red;
        text-align: center;
        margin: 0 0 1 0;
        height: auto;
    }
    #use-qty-input {
        width: 100%;
        margin: 1 0;
    }
    .use-qty-slot-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin-top: 1;
    }
    .use-qty-slot-row Button {
        width: 1fr;
        margin: 0 1;
    }
    .use-qty-btn-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin-top: 1;
    }
    .use-qty-btn-row Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, item: dict, max_quantity: int, bag_slots: list[dict], is_morok: bool = False):
        super().__init__()
        self.item = item
        self.max_quantity = max_quantity
        self.bag_slots = bag_slots  # list of bag slot dicts
        self.is_morok = is_morok

    def compose(self) -> ComposeResult:
        item_name = self.item.get("name", "Unknown")
        available = self.item.get("stack_quantity", self.item.get("quantity", 1))

        # Filter slots based on item type
        if self.is_morok:
            relevant_slots = [s for s in self.bag_slots if s.get("slot_index") == 2]
        else:
            relevant_slots = [s for s in self.bag_slots if s.get("slot_index") != 2]

        # Build slot info
        slot_lines = []
        for s in relevant_slots:
            idx = s.get("slot_index", 0)
            s_name = s.get("item_name", "")
            s_qty = s.get("quantity", 0)
            label_prefix = "Moroks" if idx == 2 else f"Slot {idx + 1}"
            if s_name:
                slot_lines.append(f"{label_prefix}: {s_name} x{s_qty}")
            else:
                slot_lines.append(f"{label_prefix}: Empty")

        info_text = (
            f"Item: {item_name}\n"
            f"Available: {available}\n"
            f"Max per slot: {self.max_quantity}\n\n"
            + "\n".join(slot_lines)
            + "\n\nEnter quantity and select a slot:"
        )

        with Container(id="use-qty-dialog"):
            yield Static("🧪 Add to Bag", id="use-qty-title")
            yield Static(info_text, id="use-qty-info")
            yield Static("", id="use-qty-error")
            yield Input(placeholder="Enter quantity (1-" + str(self.max_quantity) + ")", id="use-qty-input")
            with Horizontal(classes="use-qty-slot-row"):
                for s in relevant_slots:
                    idx = s.get("slot_index", 0)
                    s_name = s.get("item_name", "")
                    s_qty = s.get("quantity", 0)
                    label_prefix = "Moroks" if idx == 2 else f"Slot {idx + 1}"
                    if s_name:
                        label = f"{label_prefix}: {s_name} x{s_qty}"
                    else:
                        label = f"{label_prefix}: Empty"
                    yield Button(label, variant="default", id=f"use_qty_slot_{idx}")
            with Horizontal(classes="use-qty-btn-row"):
                yield Button("Cancel", variant="default", id="use_qty_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "use_qty_cancel":
            self.dismiss(None)
            return

        if event.button.id.startswith("use_qty_slot_"):
            slot_idx = int(event.button.id.split("_")[-1])
            # Validate quantity input
            try:
                input_widget = self.query_one("#use-qty-input", Input)
                qty_str = input_widget.value.strip()
                if not qty_str:
                    self._show_error("Please enter a quantity.")
                    return
                qty = int(qty_str)
            except ValueError:
                self._show_error("Please enter a valid number.")
                return

            if qty < 1:
                self._show_error("Quantity must be at least 1.")
                return
            if qty > self.max_quantity:
                self._show_error(f"Maximum is {self.max_quantity}.")
                return

            available = self.item.get("stack_quantity", self.item.get("quantity", 1))
            if qty > available:
                self._show_error(f"Only {available} available in inventory.")
                return

            # Check if slot is compatible
            slot_data = None
            for s in self.bag_slots:
                if s.get("slot_index") == slot_idx:
                    slot_data = s
                    break

            if slot_data:
                s_name = slot_data.get("item_name", "")
                item_name = self.item.get("name", "")
                label_prefix = "Moroks" if slot_idx == 2 else f"Slot {slot_idx + 1}"
                if s_name and s_name != item_name:
                    self._show_error(f"{label_prefix} contains {s_name}. Empty it first.")
                    return
                current_qty = slot_data.get("quantity", 0) if s_name == item_name else 0
                if current_qty + qty > self.max_quantity:
                    self._show_error(f"Would exceed max. {label_prefix} has {current_qty}, max is {self.max_quantity}.")
                    return

            self.dismiss({"quantity": qty, "slot_index": slot_idx})

    def _show_error(self, msg: str) -> None:
        try:
            self.query_one("#use-qty-error", Static).update(msg)
        except Exception:
            pass


class ItemDetailModal(ModalScreen):
    """A true modal overlay showing item details with Close/Delete/Sell/Use."""

    CSS = """
    ItemDetailModal {
        align: center middle;
    }
    #modal-dialog {
        width: 60;
        max-height: 80%;
        border: solid $accent;
        background: $surface;
        padding: 2;
    }
    #modal-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    #modal-body {
        color: $text;
        margin: 1 0;
        width: 100%;
    }
    .modal-btn-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin-top: 1;
    }
    .modal-btn-row Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, item: dict, can_equip: bool = False, can_unequip: bool = False,
                 is_consumable: bool = False, is_bread: bool = False):
        super().__init__()
        self.item = item
        self.can_equip = can_equip
        self.can_unequip = can_unequip
        self.is_consumable = is_consumable
        self.is_bread = is_bread

    def compose(self) -> ComposeResult:
        item = self.item
        slot_display = (
            item.get("slot", "")
            .replace("weapon_left", "Left Hand")
            .replace("weapon_right", "Right Hand")
            .replace("consumable", "Consumable")
            .capitalize()
        )

        lines = [
            "Rarity: " + item.get("rarity", "").capitalize(),
            "Class: " + item.get("character_class", ""),
            "Slot: " + slot_display,
            "Required Level: " + str(item.get("required_level", 0)),
            "",
        ]

        stat_map = [
            ("damage", "⚔️  Damage"),
            ("defense", "🛡️  Defense"),
            ("hp_bonus", "❤️  HP Bonus"),
            ("mana_bonus", "💧 Mana Bonus"),
            ("crit_chance", "💥 Crit Chance"),
            ("evasion", "💨 Evasion"),
            ("block_chance", "🔰 Block Chance"),
            ("damage_reduction", "🪨 Damage Reduction"),
        ]
        for key, label in stat_map:
            val = item.get(key, 0)
            if val:
                suffix = "%" if key in ("crit_chance", "evasion", "block_chance", "damage_reduction") else ""
                lines.append(label + ": " + str(val) + suffix)

        if item.get("description"):
            lines.append("")
            lines.append(item["description"])

        with Container(id="modal-dialog"):
            yield Static("🎒 " + item.get("name", "Unknown"), id="modal-title")
            yield Static("\n".join(lines), id="modal-body")
            with Horizontal(classes="modal-btn-row"):
                yield Button("Close", variant="default", id="modal_close")
                # Show Equip button if can_equip, Unequip button if can_unequip, nothing if neither
                if self.can_equip:
                    yield Button("Equip", variant="success", id="modal_equip")
                elif self.can_unequip:
                    yield Button("Unequip", variant="warning", id="modal_unequip")
                yield Button("Delete", variant="error", id="modal_delete")
            with Horizontal(classes="modal-btn-row"):
                yield Button("Sell (TODO)", variant="default", id="modal_sell", disabled=True)
                if self.is_bread:
                    yield Button("🍞 Eat", variant="success", id="modal_eat")
                elif self.is_consumable:
                    yield Button("🧪 Use", variant="success", id="modal_use")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modal_close":
            self.dismiss(None)
        elif event.button.id == "modal_delete":
            self.dismiss("delete")
        elif event.button.id == "modal_equip":
            self.dismiss("equip")
        elif event.button.id == "modal_unequip":
            self.dismiss("unequip")
        elif event.button.id == "modal_use":
            self.dismiss("use")
        elif event.button.id == "modal_eat":
            self.dismiss("eat")
        elif event.button.id == "modal_sell":
            pass  # TODO


class GameScreen(Screen):
    """Main game screen with character HUD and action menu."""

    CSS_PATH = None  # Will use main CSS

    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.character_data = None
        # Cooldown display state — seeded from server, ticked locally for display
        self._cooldown_remaining: int = 0
        self._cooldown_timer = None
        self._current_npcs: dict = {}
        self._current_mobs: list[dict] = []
        # Server-side inventory (list of InventoryItemResponse dicts with instance_id)
        self._player_inventory: list[dict] = []
        # Cache of all catalog items (for debug add-item)
        self._all_items_cache: list[dict] = []
        # Timer for refreshing online players list
        self._online_players_timer = None
        self._chat_socket = None
        self._chat_listener_task = None
        self._chat_channel = "general"
        self._chat_modal_opening = False
        self._chat_history: dict[str, list[dict]] = {"general": [], "group": [], "clan": []}
        self._chat_known_senders: set[str] = set()
        self._chat_selected_targets: list[str] = []
        self._chat_initialized = False
        # HP regen timer (out-of-combat: +10% max_hp every 3 seconds)
        self._hp_regen_timer = None

    def compose(self) -> ComposeResult:
        """Compose the game screen."""
        with Container(classes="game-layout"):
            # Top bar: map name + logout + debug button
            with Horizontal(classes="game-top-bar"):
                yield Static("📍 Loading...", id="map_name", classes="game-map-name")
                yield Button("Chat", variant="default", id="chat_btn", classes="game-chat-btn")
                yield Button("Logout", variant="default", id="back_btn", classes="game-logout-btn")
                yield Button("+ Add Item", variant="default", id="btn_debug_add", classes="debug-add-btn")

            # Main content area
            with Horizontal(classes="game-main"):
                # Left panel: character stats + online players
                with Vertical(classes="game-stats-panel"):
                    yield Static("⚔️ CHARACTER", classes="game-panel-title")
                    yield Static("", id="char_nickname", classes="game-stat-name")
                    yield Static("", id="char_race_gender", classes="game-stat-detail")
                    yield Static("", classes="game-stat-separator")
                    yield Static("", id="char_level", classes="game-stat")
                    yield Static("", id="char_exp", classes="game-stat")
                    yield Static("", id="char_hp", classes="game-stat-hp")
                    yield Static("", id="char_mana", classes="game-stat-mana")
                    yield Static("", id="char_currency", classes="game-stat-currency")
                    yield Static("", classes="game-stat-separator")
                    yield Static("", id="char_cooldown", classes="game-stat-cooldown")
                    
                    # Online players section
                    yield Static("", classes="game-stat-separator")
                    yield Static("👥 ONLINE PLAYERS", classes="game-panel-title")
                    with Vertical(id="online_players_container", classes="game-online-players-container"):
                        yield Static("Loading...", id="online_players_list")

                # Center: main game area — dynamic content
                with Vertical(classes="game-center-panel"):
                    yield Static(
                        "🐉 LEGEND OF DRAGON'S LEGACY 🐉",
                        classes="game-center-title",
                    )
                    with VerticalScroll(classes="game-center-content"):
                        yield Static("", id="game_area_text", classes="game-area-text")
                        # Dynamic buttons / content mounted here at runtime
                        yield Vertical(id="dynamic_area")

                # Right panel: action menu
                with Vertical(classes="game-action-panel"):
                    yield Static("📜 ACTIONS", classes="game-panel-title")
                    yield Button("🎒 Inventory", variant="default", id="btn_inventory", classes="game-action-btn")
                    yield Button("🧝 Character", variant="default", id="btn_character", classes="game-action-btn")
                    yield Button("📍 Location", variant="default", id="btn_location", classes="game-action-btn")
                    yield Button("🎒 Bag", variant="default", id="btn_bag", classes="game-action-btn")
                    yield Button("⚔️ Hunt", variant="default", id="btn_hunt", classes="game-action-btn")
                    yield Button("📜 Fights", variant="default", id="btn_fights", classes="game-action-btn")
                    yield Button("📬 Mailbox", variant="default", id="btn_mailbox", classes="game-action-btn")
                    yield Button("📋 Quests", variant="default", id="btn_quests", classes="game-action-btn")
                    yield Button("🧙 NPC List", variant="default", id="btn_npc", classes="game-action-btn")

    # ----------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------

    async def on_show(self) -> None:
        """Load character data when screen is shown."""
        await self.load_character_data()
        if not self._chat_initialized:
            self._chat_history = {"general": [], "group": [], "clan": []}
            self._chat_known_senders = set()
            self._chat_selected_targets = []
            self._chat_initialized = True
        await self._connect_chat()
        # Start online players refresh timer
        if self._online_players_timer is None:
            self._online_players_timer = self.set_interval(10.0, self._refresh_online_players)
        await self._refresh_online_players()

        # Start HP regen timer (every 3 seconds)
        if self._hp_regen_timer is None:
            self._hp_regen_timer = self.set_interval(3.0, self._tick_hp_regen)

        # Check if the player is in an active fight — force them back to fight screen
        await self._check_active_fight()

    async def refresh_after_fight(self) -> None:
        """Explicitly refresh HUD data after returning from a fight."""
        await self.load_character_data()
        # Restart HP regen timer (player may be low HP after fight)
        if self._hp_regen_timer is None:
            self._hp_regen_timer = self.set_interval(3.0, self._tick_hp_regen)

    async def _check_active_fight(self) -> None:
        """Check if the player has an active fight and force them into the fight screen."""
        email = self.app.user_email
        if not email:
            return
        try:
            active = await self.api_client.get_active_fight(email)
            if active:
                # Player is in an active fight — push fight screen in rejoin mode
                fight_screen = FightScreen(self.api_client, email, rejoin=True)
                self.app.push_screen(fight_screen)
        except Exception:
            pass  # If the check fails, just continue normally

    async def on_hide(self) -> None:
        """Clean up timers when screen is hidden."""
        if self._online_players_timer:
            self._online_players_timer.stop()
            self._online_players_timer = None
        if self._hp_regen_timer:
            self._hp_regen_timer.stop()
            self._hp_regen_timer = None
        await self._disconnect_chat()

    async def _refresh_online_players(self) -> None:
        """Fetch and display online players on the current map."""
        if not self.character_data:
            return
        try:
            current_map = self.character_data.get("current_map")
            if not current_map:
                return
            result = await self.api_client.get_players_on_map(current_map)
            players = result.get("players", [])
            if not players and self.app.user_email:
                await self.api_client.get_character_by_email(self.app.user_email)
                result = await self.api_client.get_players_on_map(current_map)
                players = result.get("players", [])
            self._update_online_players_display(players)
        except Exception:
            self.query_one("#online_players_list", Static).update("Failed to load players")

    def _update_online_players_display(self, players: list) -> None:
        """Update the online players list widget with clickable buttons."""
        container = self.query_one("#online_players_container", Vertical)
        # Clear existing content except the static "Loading..." which we'll replace
        container.remove_children()
        
        other_players = [p for p in players if p.get("nickname") != self.character_data.get("nickname")]
        
        if not other_players:
            container.mount(Static("No other players on this map", id="online_players_list"))
            return
        
        for player in other_players:
            btn = Button(
                f"[Lv{player['level']}] {player['nickname']}",
                variant="default",
                id=f"player_{player['nickname']}",
                classes="game-player-btn"
            )
            container.mount(btn)

    def _open_player_profile(self, nickname: str) -> None:
        """Open another player's profile modal."""
        async def _load_and_show():
            try:
                player_data = await self.api_client.view_character_by_nickname(nickname)
                # Convert equipped_items list to dict for the modal
                equipped_dict = {}
                for item in player_data.get("equipped_items", []):
                    equipped_dict[item["slot"]] = {"name": item["name"], "rarity": item["rarity"]}
                
                # Build stats dict for the modal
                stats = {
                    "level": player_data["level"],
                    "base_stats": player_data["base_stats"],
                    "bonus_stats": player_data["bonus_stats"],
                    "total_stats": player_data["total_stats"],
                    "combat_stats": player_data["combat_stats"],
                    "set_bonus": player_data.get("set_bonus"),
                }
                
                # Create a character dict for the modal
                char_data = {
                    "nickname": player_data["nickname"],
                    "race": player_data["race"],
                    "gender": player_data["gender"],
                }
                
                self.app.push_screen(CharacterDetailModal(char_data, equipped_dict, stats))
            except Exception:
                self.app.show_toast("⚠️ Failed to load player profile", severity="warning")
        
        self.run_worker(_load_and_show())

    async def load_character_data(self) -> None:
        """Fetch and display character data from the API."""
        try:
            email = self.app.user_email
            if not email:
                self._show_text("⚠️ No user session found. Please log in again.")
                return
            self.character_data = await self.api_client.get_character_by_email(email)
            # Seed cooldown from server-authoritative value
            self._start_cooldown_display(self.character_data.get("cooldown_remaining", 0))
            self._update_hud()
        except Exception:
            self._show_text(
                "⚠️ Failed to load character data.\n"
                "Please try logging in again."
            )

    # ----------------------------------------------------------
    # HUD helpers
    # ----------------------------------------------------------

    def _update_hud(self) -> None:
        """Update all HUD elements with character data."""
        if not self.character_data:
            return
        data = self.character_data

        current_map = data["current_map"]
        nickname = data["nickname"]
        race_display = data["race"].capitalize()
        gender_display = data["gender"].capitalize()

        self.query_one("#map_name", Static).update("📍 " + current_map)
        self.query_one("#char_nickname", Static).update("🛡️ " + nickname)
        self.query_one("#char_race_gender", Static).update(
            race_display + " • " + gender_display
        )
        level = data["level"]
        exp = data["experience"]
        exp_req = exp_required_for_level(level)
        self.query_one("#char_level", Static).update("⭐ Level: " + str(level))
        self.query_one("#char_exp", Static).update("✨ EXP: " + str(exp) + " / " + str(exp_req))
        max_hp = data["health"]
        current_hp = data.get("current_hp")
        if current_hp is None:
            current_hp = max_hp
        # Clamp current_hp to max_hp (can exceed after unequipping items)
        current_hp = min(current_hp, max_hp)
        max_mana = str(data["mana"])
        self.query_one("#char_hp", Static).update("❤️  HP: " + str(current_hp) + " / " + str(max_hp))
        self.query_one("#char_mana", Static).update("💧 Mana: " + max_mana + " / " + max_mana)
        total_copper = data.get("copper", 0)
        self.query_one("#char_currency", Static).update("💰 " + _format_currency_rich(total_copper))
        self._update_cooldown_display()

        self._clear_dynamic()
        self._show_text(
            "Welcome to " + current_map + ", " + nickname + "!\n\n"
            "You stand at the heart of the settlement.\n"
            "Use the action menu on the right to explore."
        )

    def _update_cooldown_display(self) -> None:
        """Update the cooldown line in the left stats panel."""
        widget = self.query_one("#char_cooldown", Static)
        if self._cooldown_remaining > 0:
            widget.update("⏳ Cooldown: " + str(self._cooldown_remaining) + "s")
        else:
            widget.update("")

    def _start_cooldown_display(self, seconds: int) -> None:
        """Start (or restart) the local cooldown display timer from a server value."""
        # Stop any existing timer
        if self._cooldown_timer is not None:
            self._cooldown_timer.stop()
            self._cooldown_timer = None

        self._cooldown_remaining = max(0, seconds)
        self._update_cooldown_display()

        if self._cooldown_remaining > 0:
            self._cooldown_timer = self.set_interval(1.0, self._tick_cooldown)

    # ----------------------------------------------------------
    # Center panel helpers
    # ----------------------------------------------------------

    def _show_text(self, message: str) -> None:
        """Show a text message in the center panel."""
        self.query_one("#game_area_text", Static).update(message)

    def _clear_dynamic(self) -> None:
        """Remove all dynamically-mounted widgets from #dynamic_area."""
        container = self.query_one("#dynamic_area", Vertical)
        container.remove_children()

    def _mount_dynamic(self, *widgets) -> None:
        """Mount widgets into the dynamic area."""
        self._clear_dynamic()
        container = self.query_one("#dynamic_area", Vertical)
        container.mount_all(widgets)

    # ----------------------------------------------------------
    # Chat
    # ----------------------------------------------------------

    async def _connect_chat(self) -> None:
        if self._chat_socket or not self.character_data:
            return
        nickname = self.character_data.get("nickname") if self.character_data else None
        if not nickname:
            return
        try:
            self._chat_socket = await websockets.connect("ws://localhost:8000/ws")
            await self._chat_socket.send(json.dumps({"type": "identify", "nickname": nickname}))
            self._chat_listener_task = self.run_worker(self._listen_for_chat(), exclusive=False)
        except Exception:
            self._chat_socket = None
            self.app.show_toast("⚠️ Chat connection failed.", severity="warning")

    async def _disconnect_chat(self) -> None:
        if self._chat_listener_task:
            self._chat_listener_task.cancel()
            self._chat_listener_task = None
        if self._chat_socket:
            await self._chat_socket.close()
            self._chat_socket = None

    async def _listen_for_chat(self) -> None:
        if not self._chat_socket:
            return
        while True:
            try:
                data = await self._chat_socket.recv()
            except Exception:
                break
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                continue
            if message_data.get("type") in ("chat", "whisper"):
                channel = message_data.get("channel", "general")
                sender = message_data.get("sender", "")
                entry = {
                    "sender": sender,
                    "message": message_data.get("message", ""),
                    "private": message_data.get("type") == "whisper",
                    "targets": message_data.get("targets", []),
                }
                self._chat_history.setdefault(channel, []).append(entry)
                if sender:
                    self._chat_known_senders.add(sender)
                self.call_later(self._refresh_chat_modal)

    def _refresh_chat_modal(self) -> None:
        if not self.app.screen_stack:
            return
        current = self.app.screen_stack[-1]
        if not isinstance(current, ChatModal):
            return
        current.history = self._chat_history.get(self._chat_channel, [])
        current.selected_targets = list(self._chat_selected_targets)
        try:
            history_content = current.query_one("#chat-history-content", Static)
            history_content.update(current._format_history())
        except NoMatches:
            pass
        try:
            senders_container = current.query_one("#chat-senders-list", Vertical)
            current.render_sender_buttons(senders_container)
        except NoMatches:
            return
        self._update_chat_input_prefix(current)

    def _open_chat_modal(self) -> None:
        if self._chat_modal_opening:
            return
        self._chat_modal_opening = True
        history = self._chat_history.get(self._chat_channel, [])
        modal = ChatModal(self._chat_channel, history, list(self._chat_selected_targets))
        def _after_mount() -> None:
            try:
                senders_container = modal.query_one("#chat-senders-list", Vertical)
                modal.render_sender_buttons(senders_container)
                self._update_chat_input_prefix(modal)
            except NoMatches:
                pass
            self._chat_modal_opening = False
        self.app.push_screen(modal, callback=lambda _: None)
        self.call_later(_after_mount)

    def _update_chat_input_prefix(self, modal: ChatModal) -> None:
        input_widget = modal.query_one("#chat-input", Input)
        prefix = ""
        if self._chat_selected_targets:
            prefix = "/w " + " ".join(self._chat_selected_targets) + " "
        input_widget.value = prefix
        input_widget.cursor_position = len(prefix)

    async def _send_chat_message(self, modal: ChatModal) -> None:
        input_widget = modal.query_one("#chat-input", Input)
        raw_message = input_widget.value.strip()
        if not raw_message:
            return
        nickname = self.character_data.get("nickname") if self.character_data else None
        if not nickname or not self._chat_socket:
            return
        if raw_message.startswith("/w "):
            payload = self._build_whisper_payload(raw_message, nickname)
            if payload:
                await self._chat_socket.send(json.dumps(payload))
                input_widget.value = ""
            return
        else:
            payload = {
                "type": "chat",
                "channel": self._chat_channel,
                "sender": nickname,
                "message": raw_message,
            }
            await self._chat_socket.send(json.dumps(payload))
        input_widget.value = ""

    def _build_whisper_payload(self, raw_message: str, nickname: str) -> dict | None:
        parts = raw_message.split()
        if len(parts) < 3:
            return None
        targets = parts[1:-1]
        message = parts[-1] if len(parts) > 1 else ""
        targets = [t for t in targets if t]
        if not targets or not message:
            return None
        return {
            "type": "whisper",
            "channel": self._chat_channel,
            "sender": nickname,
            "targets": targets,
            "message": message,
        }

    def _handle_sender_click(self, sender: str, modal: ChatModal) -> None:
        input_widget = modal.query_one("#chat-input", Input)
        current_value = input_widget.value.strip()
        if current_value.startswith("/w "):
            new_value = current_value + " " + sender
        elif current_value == "":
            new_value = f"/w {sender} "
        else:
            new_value = f"/w {sender} "
        input_widget.value = new_value
        input_widget.cursor_position = len(new_value)
        
    def _toggle_chat_target(self, target: str, modal: ChatModal) -> None:
        if target in self._chat_selected_targets:
            self._chat_selected_targets.remove(target)
        else:
            self._chat_selected_targets.append(target)
        modal.selected_targets = list(self._chat_selected_targets)
        self._update_chat_input_prefix(modal)
        try:
            senders_container = modal.query_one("#chat-senders-list", Vertical)
        except NoMatches:
            return
        modal.render_sender_buttons(senders_container)

    def _switch_chat_channel(self, channel: str, modal: ChatModal) -> None:
        self._chat_channel = channel
        modal.channel = channel
        modal.history = self._chat_history.get(channel, [])
        try:
            history_content = modal.query_one("#chat-history-content", Static)
            history_content.update(modal._format_history())
        except NoMatches:
            pass
        try:
            senders_container = modal.query_one("#chat-senders-list", Vertical)
            modal.render_sender_buttons(senders_container)
        except NoMatches:
            pass
        self._update_chat_input_prefix(modal)
        self._refresh_chat_tabs(modal)

    def _refresh_chat_tabs(self, modal: ChatModal) -> None:
        modal.query_one("#chat_tab_general", Button).variant = "success" if modal.channel == "general" else "default"
        modal.query_one("#chat_tab_group", Button).variant = "success" if modal.channel == "group" else "default"
        modal.query_one("#chat_tab_clan", Button).variant = "success" if modal.channel == "clan" else "default"

    # ----------------------------------------------------------
    # Location panel
    # ----------------------------------------------------------

    async def _show_location(self) -> None:
        """Show current location and connected regions as travel buttons."""
        if not self.character_data:
            return

        current = self.character_data["current_map"]

        try:
            region_info = await self.api_client.get_region_info(current)
            connected = region_info.get("connected_regions", [])
        except Exception:
            connected = []

        if self._cooldown_remaining > 0:
            header = (
                "📍 LOCATION: " + current + "\n\n"
                "⏳ Travel cooldown active: " + str(self._cooldown_remaining) + "s remaining\n\n"
                "Accessible regions:"
            )
        else:
            header = (
                "📍 LOCATION: " + current + "\n\n"
                "Accessible regions:"
            )

        self._show_text(header)

        buttons = []
        for region in connected:
            btn_id = "travel_" + _sanitize_id(region)
            btn = Button(
                "🚶 Travel to " + region,
                variant="default",
                id=btn_id,
                classes="game-travel-btn",
            )
            buttons.append(btn)

        if not buttons:
            buttons.append(Static("No connected regions.", classes="game-area-text"))

        self._mount_dynamic(*buttons)

    # ----------------------------------------------------------
    # NPC list panel
    # ----------------------------------------------------------

    async def _show_npc_list(self) -> None:
        """Show NPCs in the current region."""
        if not self.character_data:
            return

        current = self.character_data["current_map"]

        try:
            npcs = await self.api_client.get_region_npcs(current)
        except Exception:
            npcs = []

        if not npcs:
            self._show_text(
                "🧙 NPCs in " + current + "\n\nNo NPCs found in this region."
            )
            self._clear_dynamic()
            return

        self._show_text("🧙 NPCs in " + current + "\n")

        widgets = []
        for npc in npcs:
            npc_name = npc["name"]
            npc_role = npc["role"]
            btn_id = "npc_" + _sanitize_id(npc_name)
            btn = Button(
                npc_name + " — " + npc_role,
                variant="default",
                id=btn_id,
                classes="game-npc-btn",
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)
        # Store NPC data for interaction look-ups
        self._current_npcs = {npc["name"]: npc for npc in npcs}

    # ----------------------------------------------------------
    # Hunt panel
    # ----------------------------------------------------------

    async def _show_hunt(self) -> None:
        """Show available mobs in the current region for hunting."""
        if not self.character_data:
            return

        current = self.character_data["current_map"]

        try:
            mobs = await self.api_client.get_region_mobs(current)
        except Exception:
            mobs = []

        self._current_mobs = mobs

        if not mobs:
            self._show_text(
                "⚔️ HUNT — " + current + "\n\nNo creatures found in this region."
            )
            self._clear_dynamic()
            return

        self._show_text(
            "⚔️ HUNT — " + current + "\n\n"
            "Select a creature to battle:"
        )

        widgets = []
        for mob in mobs:
            display_name = mob["display_name"]
            hp_info = "HP: " + str(mob["max_hp"])
            dmg_info = "DMG: " + str(mob["damage_min"]) + "-" + str(mob["damage_max"])
            label = "👹 " + display_name + "  (" + hp_info + " | " + dmg_info + ")"
            btn_id = "mob_" + _sanitize_id(mob["name"])
            btn = Button(
                label,
                variant="default",
                id=btn_id,
                classes="game-mob-btn",
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)

    def _start_fight(self, mob_name: str) -> None:
        """Push the fight screen to start a battle with the selected mob."""
        email = self.app.user_email
        if not email:
            self.app.show_toast("⚠️ No user session found.", severity="warning")
            return

        fight_screen = FightScreen(self.api_client, email, mob_name)
        self.app.push_screen(fight_screen)

    # ----------------------------------------------------------
    # Inventory panel (sectioned, server-side)
    # ----------------------------------------------------------

    async def _load_inventory_from_server(self) -> None:
        """Fetch inventory from the server."""
        try:
            email = self.app.user_email
            if email:
                self._player_inventory = await self.api_client.get_inventory(email)
        except Exception:
            pass  # keep whatever we had

    def _group_inventory(self, items: list[dict]) -> tuple[list[dict], list[dict]]:
        """Group identical items by catalog id, separating equipped items.
        
        Returns: (equipped_items, stacked_unequipped_items)
        """
        equipped = [i for i in items if i.get("equipped_slot")]
        unequipped = [i for i in items if not i.get("equipped_slot")]
        
        # Group unequipped items by catalog id
        grouped: dict[int, dict] = {}
        for item in unequipped:
            catalog_id = item.get("item_catalog_id")
            if catalog_id is None:
                continue
            if catalog_id not in grouped:
                grouped[catalog_id] = dict(item)
                grouped[catalog_id]["stack_quantity"] = int(item.get("quantity", 1))
                grouped[catalog_id]["stack_instances"] = [item]
            else:
                grouped[catalog_id]["stack_quantity"] += int(item.get("quantity", 1))
                grouped[catalog_id]["stack_instances"].append(item)
        return equipped, list(grouped.values())

    async def _show_inventory(self) -> None:
        """Show inventory category buttons."""
        await self._load_inventory_from_server()
        # Refresh character data to get latest currency
        await self.load_character_data()
        total_copper = self.character_data.get("copper", 0) if self.character_data else 0
        currency_display = _format_currency_rich(total_copper)
        self._show_text("🎒 INVENTORY\n\n💰 " + currency_display + "\n\nSelect a category:")

        buttons = []
        for cat_key in _CAT_ORDER:
            cat_label = _CAT_DISPLAY.get(cat_key, cat_key)
            items_in_cat = [i for i in self._player_inventory if i.get("inventory_category") == cat_key]
            equipped, stacked = self._group_inventory(items_in_cat)
            # Count: equipped items + stacks
            count = len(equipped) + len(stacked)
            label = cat_label + " (" + str(count) + ")"
            btn = Button(
                label,
                variant="default",
                id="invcat_" + cat_key,
                classes="game-action-btn",
            )
            buttons.append(btn)

        self._mount_dynamic(*buttons)

    def _show_inventory_category(self, category: str) -> None:
        """Show items in a specific inventory category."""
        cat_label = _CAT_DISPLAY.get(category, category)
        items = [i for i in self._player_inventory if i.get("inventory_category") == category]
        equipped_items, stacked_items = self._group_inventory(items)

        if not equipped_items and not stacked_items:
            self._show_text("🎒 " + cat_label + "\n\nNo items in this category.")
            widgets = [
                Button("← Back to Inventory", variant="default", id="btn_inv_back", classes="game-action-btn")
            ]
            self._mount_dynamic(*widgets)
            return

        self._show_text("🎒 " + cat_label + "\n")

        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}
        
        # Sort equipped items
        equipped_sorted = sorted(
            equipped_items,
            key=lambda i: (rarity_order.get(i.get("rarity", "common"), 0), i.get("required_level", 0), i.get("name", "")),
        )
        
        # Sort stacked items
        stacked_sorted = sorted(
            stacked_items,
            key=lambda i: (rarity_order.get(i.get("rarity", "common"), 0), i.get("required_level", 0), i.get("name", "")),
        )

        widgets = []
        widgets.append(
            Button("← Back to Inventory", variant="default", id="btn_inv_back", classes="game-action-btn")
        )
        
        # Show equipped items first
        for item in equipped_sorted:
            color = item.get("color", "white")
            slot_short = (
                item.get("slot", "")
                .replace("weapon_left", "L.Hand")
                .replace("weapon_right", "R.Hand")
                .replace("consumable", "Use")
                .capitalize()
            )
            label = (
                "[Lv" + str(item.get("required_level", 0)) + "] "
                + item.get("name", "Unknown")
                + " (" + slot_short + ")"
                + " [EQUIPPED]"
            )
            inst_id = item.get("instance_id", 0)
            btn = Button(
                label,
                variant="default",
                id="invitem_" + str(inst_id),
                classes="game-item-btn item-color-" + color,
            )
            widgets.append(btn)
        
        # Show stacked unequipped items
        for item in stacked_sorted:
            color = item.get("color", "white")
            slot_short = (
                item.get("slot", "")
                .replace("weapon_left", "L.Hand")
                .replace("weapon_right", "R.Hand")
                .replace("consumable", "Use")
                .capitalize()
            )
            stack_qty = item.get("stack_quantity", item.get("quantity", 1))
            qty_label = " x" + str(stack_qty) if stack_qty > 1 else ""
            label = (
                "[Lv" + str(item.get("required_level", 0)) + "] "
                + item.get("name", "Unknown")
                + " (" + slot_short + ")"
                + qty_label
            )
            # Use instance_id (unique DB PK) — never duplicates
            inst_id = item.get("instance_id", 0)
            btn = Button(
                label,
                variant="default",
                id="invitem_" + str(inst_id),
                classes="game-item-btn item-color-" + color,
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)

    def _open_item_modal(self, item: dict) -> None:
        """Open a proper Textual modal for item detail."""
        slot = item.get("slot")
        required_level = item.get("required_level", 0)
        character_level = self.character_data.get("level", 1) if self.character_data else 1
        
        # Check if item can be equipped (has slot, not consumable, meets level req)
        can_equip_slot = bool(slot) and slot not in ("consumable",)
        meets_level_req = character_level >= required_level
        is_equipped = bool(item.get("equipped_slot"))
        is_morok = slot == "morok"
        is_consumable = ((slot == "consumable") or is_morok) and not is_equipped
        is_bread = (item.get("name") == "Bread") and not is_equipped
        
        # Bread uses "Eat" button, not "Use" (bag) button
        if is_bread:
            is_consumable = False
        
        can_equip = can_equip_slot and meets_level_req and not is_equipped
        can_unequip = is_equipped

        def on_modal_result(result) -> None:
            if result == "delete":
                self._delete_item_from_inventory(item)
            elif result == "equip":
                self._equip_item(item)
            elif result == "unequip":
                self._unequip_item(item)
            elif result == "use":
                self._use_consumable_item(item)
            elif result == "eat":
                self._eat_bread(item)
        self.app.push_screen(
            ItemDetailModal(item, can_equip=can_equip, can_unequip=can_unequip,
                          is_consumable=is_consumable, is_bread=is_bread),
            callback=on_modal_result,
        )

    def _delete_item_from_inventory(self, item: dict) -> None:
        """Delete an item instance from the server and refresh."""
        inst_id = item.get("instance_id")
        if not inst_id:
            return

        async def _do_delete():
            try:
                email = self.app.user_email
                await self.api_client.delete_inventory_item(email, inst_id)
                self.app.show_toast("🗑️ Deleted: " + item.get("name", "Unknown"), severity="information")
                # Refresh the category view
                cat = item.get("inventory_category", "equipment")
                await self._load_inventory_from_server()
                self._show_inventory_category(cat)
            except Exception:
                self.app.show_toast("⚠️ Failed to delete item.", severity="warning")

        self.run_worker(_do_delete())

    def _equip_item(self, item: dict) -> None:
        """Equip an item via server API and refresh."""
        inst_id = item.get("instance_id")
        if not inst_id:
            return

        async def _do_equip():
            try:
                email = self.app.user_email
                result = await self.api_client.equip_item(email, inst_id)
                self.app.show_toast("✅ Equipped: " + result.get("name", "Unknown"), severity="information")
                # Refresh the category view
                cat = item.get("inventory_category", "equipment")
                await self._load_inventory_from_server()
                self._show_inventory_category(cat)
            except Exception as e:
                error_msg = str(e)
                if "Level" in error_msg:
                    self.app.show_toast("⚠️ " + error_msg, severity="warning")
                else:
                    self.app.show_toast("⚠️ Failed to equip item.", severity="warning")

        self.run_worker(_do_equip())

    def _unequip_item(self, item: dict) -> None:
        """Unequip an item via server API and refresh."""
        inst_id = item.get("instance_id")
        if not inst_id:
            return

        async def _do_unequip():
            try:
                email = self.app.user_email
                result = await self.api_client.unequip_item(email, inst_id)
                self.app.show_toast("🧳 Unequipped: " + result.get("name", "Unknown"), severity="information")
                # Refresh the category view
                cat = item.get("inventory_category", "equipment")
                await self._load_inventory_from_server()
                self._show_inventory_category(cat)
            except Exception:
                self.app.show_toast("⚠️ Failed to unequip item.", severity="warning")

        self.run_worker(_do_unequip())

    def _use_consumable_item(self, item: dict) -> None:
        """Open the Use Potion quantity modal to add consumable to bag."""
        from dragons_legacy.models.bag import BAG_SLOT_MAX, BAG_MOROK_MAX

        item_name = item.get("name", "")
        is_morok = item.get("slot") == "morok"
        max_qty = BAG_MOROK_MAX if is_morok else BAG_SLOT_MAX.get(item_name, 0)
        if max_qty == 0:
            self.app.show_toast("⚠️ This item cannot be placed in the bag.", severity="warning")
            return

        # For moroks, compute total available by summing quantities of matching entries
        if is_morok:
            catalog_id = item.get("item_catalog_id")
            total_available = sum(
                int(i.get("quantity", 1)) for i in self._player_inventory
                if i.get("item_catalog_id") == catalog_id and not i.get("equipped_slot")
            )
            item = dict(item)  # copy to avoid mutating original
            item["stack_quantity"] = total_available

        async def _load_and_show():
            try:
                email = self.app.user_email
                bag_slots = await self.api_client.get_bag(email)
            except Exception:
                bag_slots = [
                    {"slot_index": 0, "item_catalog_id": None, "item_name": "", "quantity": 0, "max_quantity": 0},
                    {"slot_index": 1, "item_catalog_id": None, "item_name": "", "quantity": 0, "max_quantity": 0},
                    {"slot_index": 2, "item_catalog_id": None, "item_name": "", "quantity": 0, "max_quantity": 0},
                ]

            def on_qty_result(result) -> None:
                if result is None:
                    return
                qty = result["quantity"]
                slot_index = result["slot_index"]
                self._do_add_to_bag(item, qty, slot_index)

            self.app.push_screen(
                UsePotionQuantityModal(item, max_qty, bag_slots, is_morok=is_morok),
                callback=on_qty_result,
            )

        self.run_worker(_load_and_show())

    def _eat_bread(self, item: dict) -> None:
        """Eat one Bread from inventory to restore +30 HP."""
        async def _do_eat():
            try:
                email = self.app.user_email
                result = await self.api_client.eat_bread(email)
                healed = result.get("healed", 0)
                remaining = result.get("bread_remaining", 0)
                current_hp = result.get("current_hp", 0)
                max_hp = result.get("max_hp", 0)
                self.app.show_toast(
                    f"🍞 Ate Bread! +{healed} HP ({current_hp}/{max_hp}). {remaining} left.",
                    severity="information",
                )
                # Update HUD
                try:
                    self.query_one("#char_hp", Static).update(
                        "❤️  HP: " + str(current_hp) + " / " + str(max_hp)
                    )
                except NoMatches:
                    pass
                if self.character_data:
                    self.character_data["current_hp"] = current_hp
                # Restart HP regen timer if it was stopped
                if self._hp_regen_timer is None and current_hp < max_hp:
                    self._hp_regen_timer = self.set_interval(3.0, self._tick_hp_regen)
                # Refresh inventory view
                cat = item.get("inventory_category", "consumables")
                await self._load_inventory_from_server()
                self._show_inventory_category(cat)
            except Exception as e:
                self.app.show_toast("⚠️ " + str(e), severity="warning")

        self.run_worker(_do_eat())

    def _do_add_to_bag(self, item: dict, quantity: int, slot_index: int) -> None:
        """Actually add consumable items to a bag slot via API."""
        async def _do():
            try:
                email = self.app.user_email
                catalog_id = item.get("item_catalog_id", 0)
                result = await self.api_client.add_to_bag(email, catalog_id, quantity, slot_index)
                self.app.show_toast("✅ " + result.get("message", "Added to bag"), severity="information")
                # Refresh inventory view
                cat = item.get("inventory_category", "consumables")
                await self._load_inventory_from_server()
                self._show_inventory_category(cat)
            except Exception as e:
                error_msg = str(e)
                self.app.show_toast("⚠️ " + error_msg, severity="warning")

        self.run_worker(_do())

    async def _show_bag(self) -> None:
        """Show the bag screen with 2 slots."""
        try:
            email = self.app.user_email
            bag_slots = await self.api_client.get_bag(email)
        except Exception:
            bag_slots = []

        lines = ["🎒 BAG\n"]
        for s in bag_slots:
            idx = s.get("slot_index", 0)
            s_name = s.get("item_name", "")
            s_qty = s.get("quantity", 0)
            label = "Moroks" if idx == 2 else f"Slot {idx + 1}"
            if s_name:
                lines.append(f"  {label}: {s_name} x{s_qty}")
            else:
                lines.append(f"  {label}: Empty")

        lines.append("\nClick a slot to remove its contents back to inventory.")
        self._show_text("\n".join(lines))

        widgets = []
        for s in bag_slots:
            idx = s.get("slot_index", 0)
            s_name = s.get("item_name", "")
            s_qty = s.get("quantity", 0)
            if idx == 2:
                slot_label = "Moroks"
                icon = "🐴"
            else:
                slot_label = f"Slot {idx + 1}"
                icon = "🧪"
            if s_name:
                label = f"{icon} {slot_label}: {s_name} x{s_qty} — [Remove]"
                btn = Button(label, variant="warning", id=f"bag_remove_{idx}", classes="game-action-btn")
            else:
                label = f"📦 {slot_label}: Empty"
                btn = Button(label, variant="default", id=f"bag_empty_{idx}", classes="game-action-btn", disabled=True)
            widgets.append(btn)

        self._mount_dynamic(*widgets)

    def _remove_from_bag(self, slot_index: int) -> None:
        """Remove all items from a bag slot back to inventory."""
        async def _do():
            try:
                email = self.app.user_email
                result = await self.api_client.remove_from_bag(email, slot_index)
                self.app.show_toast("✅ " + result.get("message", "Removed from bag"), severity="information")
                await self._show_bag()
            except Exception as e:
                self.app.show_toast("⚠️ " + str(e), severity="warning")

        self.run_worker(_do())

    def _open_character_modal(self) -> None:
        """Open a modal showing character info and equipped items."""
        if not self.character_data:
            return
        
        async def _load_and_show():
            try:
                email = self.app.user_email
                
                # First ensure inventory is loaded (for equipped items)
                await self._load_inventory_from_server()
                
                # Fetch character stats from server
                stats = await self.api_client.get_character_stats(email)
                
                # Build equipped items dict from inventory data
                equipped_items: dict[str, dict] = {}
                for item in self._player_inventory:
                    if item.get("equipped_slot"):
                        equipped_items[item["equipped_slot"]] = item
                
                self.app.push_screen(CharacterDetailModal(self.character_data, equipped_items, stats))
            except Exception as e:
                # Fallback to showing without stats
                equipped_items: dict[str, dict] = {}
                for item in self._player_inventory:
                    if item.get("equipped_slot"):
                        equipped_items[item["equipped_slot"]] = item
                self.app.push_screen(CharacterDetailModal(self.character_data, equipped_items))
        
        self.run_worker(_load_and_show())

    # ----------------------------------------------------------
    # Debug: Add Item panel
    # ----------------------------------------------------------

    async def _show_debug_add_item(self) -> None:
        """Show all catalog items so the user can add them to inventory (server-side)."""
        if not self._all_items_cache:
            try:
                self._all_items_cache = await self.api_client.get_all_items()
            except Exception:
                self._all_items_cache = []

        if not self._all_items_cache:
            self._show_text("⚠️ Could not load item catalog.")
            self._clear_dynamic()
            return

        self._show_text("🛠️ DEBUG: Add Item to Inventory\n\nClick an item to add it.\n")

        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}
        items_sorted = sorted(
            self._all_items_cache,
            key=lambda i: (
                i["character_class"],
                rarity_order.get(i["rarity"], 0),
                i["required_level"],
                i["slot"],
            ),
        )

        widgets = []
        current_group = ""
        for item in items_sorted:
            group_key = item["character_class"] + " — " + item["rarity"].capitalize()
            if group_key != current_group:
                current_group = group_key
                color = item["color"]
                widgets.append(Static(
                    "── " + group_key + " ──",
                    classes="item-group-header item-color-" + color,
                ))

            color = item["color"]
            slot_short = (
                item["slot"]
                .replace("weapon_left", "L.Hand")
                .replace("weapon_right", "R.Hand")
                .replace("consumable", "Use")
                .capitalize()
            )
            label = (
                "[Lv" + str(item["required_level"]) + "] "
                + item["name"]
                + " (" + slot_short + ")"
            )
            btn = Button(
                label,
                variant="default",
                id="dbgadd_" + str(item["id"]),
                classes="game-item-btn item-color-" + color,
            )
            widgets.append(btn)

        self._mount_dynamic(*widgets)

    async def _debug_add_item_to_inventory(self, item_catalog_id: str) -> None:
        """Add an item to inventory via the server."""
        try:
            email = self.app.user_email
            result = await self.api_client.add_inventory_item(email, int(item_catalog_id))
            cat = _CAT_DISPLAY.get(result.get("inventory_category", "other"), "Inventory")
            self.app.show_toast(
                "✅ Added: " + result.get("name", "Unknown") + " → " + cat,
                severity="information",
            )
        except Exception:
            self.app.show_toast("⚠️ Failed to add item.", severity="warning")

    # ----------------------------------------------------------
    # Travel + cooldown logic (server-authoritative)
    # ----------------------------------------------------------

    async def _initiate_travel(self, destination: str) -> None:
        """Travel immediately via the server; cooldown is enforced server-side."""
        # The server will reject if cooldown is still active, but we can
        # give instant client feedback too.
        if self._cooldown_remaining > 0:
            self._clear_dynamic()
            self._show_text(
                "⏳ Travel cooldown active!\n\n"
                "You must wait " + str(self._cooldown_remaining) + "s before traveling again."
            )
            return

        # Ask the server to travel (it enforces the cooldown authoritatively)
        try:
            result = await self.api_client.travel(
                email=self.app.user_email,
                destination=destination,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "cooldown" in error_str:
                # Server rejected — extract remaining seconds from error
                self._show_text(
                    "⏳ Travel cooldown active!\n\n"
                    "The server says you must wait before traveling again."
                )
            elif "not connected" in error_str:
                self._show_text("❌ Cannot travel there — regions are not connected.")
            else:
                self._show_text("❌ Travel failed. Please try again.")
            self._clear_dynamic()
            return

        # --- Arrived immediately (server confirmed) ---
        cooldown_seconds = result["cooldown_seconds"]
        self.character_data["current_map"] = result["current_map"]

        # Update top bar right away
        self.query_one("#map_name", Static).update("📍 " + destination)

        self.app.show_toast("📍 Arrived at " + destination + "!", severity="information")

        # Start cooldown display from server value
        self._start_cooldown_display(result["cooldown_remaining"])

        self._clear_dynamic()
        self._show_text(
            "✅ You have arrived at " + destination + "!\n\n"
            "⏳ Travel cooldown: " + str(cooldown_seconds) + "s\n"
            "You can explore this area, but cannot travel\n"
            "to another region until the cooldown expires."
        )

    def _tick_cooldown(self) -> None:
        """Called every second to decrement the local cooldown display."""
        self._cooldown_remaining = max(0, self._cooldown_remaining - 1)
        self._update_cooldown_display()

        if self._cooldown_remaining <= 0:
            if self._cooldown_timer is not None:
                self._cooldown_timer.stop()
                self._cooldown_timer = None
            self.app.show_toast("✅ Travel cooldown expired — you may travel again!", severity="information")

    def _tick_hp_regen(self) -> None:
        """Called every 3 seconds to apply out-of-combat HP regen."""
        async def _do_regen():
            email = self.app.user_email
            if not email or not self.character_data:
                return
            try:
                result = await self.api_client.hp_regen_tick(email)
                healed = result.get("healed", 0)
                if healed > 0:
                    current_hp = result["current_hp"]
                    max_hp = result["max_hp"]
                    # Update HUD
                    try:
                        self.query_one("#char_hp", Static).update(
                            "❤️  HP: " + str(current_hp) + " / " + str(max_hp)
                        )
                    except NoMatches:
                        pass
                    # Update character_data cache
                    if self.character_data:
                        self.character_data["current_hp"] = current_hp
                elif result.get("current_hp", 0) >= result.get("max_hp", 0):
                    # At full HP — stop the timer to save resources
                    if self._hp_regen_timer:
                        self._hp_regen_timer.stop()
                        self._hp_regen_timer = None
            except Exception:
                pass  # Silently ignore regen errors

        self.run_worker(_do_regen(), exclusive=False)

    # ----------------------------------------------------------
    # NPC Interaction + Quests
    # ----------------------------------------------------------

    async def _interact_with_npc(self, npc_data: dict) -> None:
        """Interact with an NPC — show dialogue and available quests."""
        npc_name = npc_data["name"]
        npc_role = npc_data["role"]
        npc_desc = npc_data["description"]

        # Check for available quests from this NPC
        email = self.app.user_email
        available_quests = []
        if email:
            try:
                available_quests = await self.api_client.get_available_quests(email, npc_name)
            except Exception:
                pass

        lines = [
            "🧙 " + npc_name,
            "Role: " + npc_role,
            "",
            npc_desc,
        ]

        if available_quests:
            lines.append("")
            lines.append("📋 Available Quests:")

        self._show_text("\n".join(lines))

        widgets = []
        for q in available_quests:
            action = q.get("action", "")
            quest_id = q.get("quest_id", "")
            quest_name = q.get("name", "Unknown")
            quest_level = q.get("level", 1)

            if action == "accept":
                label = f"📋 [Lv{quest_level}] {quest_name} — Accept Quest"
                btn = Button(
                    label, variant="success",
                    id="quest_accept_" + quest_id,
                    classes="game-action-btn",
                )
                widgets.append(btn)
                # Show quest details
                desc = q.get("description", "")
                obj = q.get("objective_text", "")
                reward = q.get("reward_text", "")
                widgets.append(Static(
                    f"  {desc}\n  Objective: {obj}\n  Rewards: {reward}",
                    classes="game-area-text",
                ))
            elif action == "complete":
                progress = q.get("progress", 0)
                obj_count = q.get("objective_count", 0)
                label = f"✅ [Lv{quest_level}] {quest_name} — Turn In ({progress}/{obj_count})"
                btn = Button(
                    label, variant="warning",
                    id="quest_complete_" + quest_id,
                    classes="game-action-btn",
                )
                widgets.append(btn)
                reward = q.get("reward_text", "")
                widgets.append(Static(
                    f"  Rewards: {reward}",
                    classes="game-area-text",
                ))

        if not available_quests:
            widgets.append(Static(
                "\nNo quests available from this NPC.",
                classes="game-area-text",
            ))

        self._mount_dynamic(*widgets)

    async def _accept_quest(self, quest_id: str) -> None:
        """Accept a quest from an NPC."""
        email = self.app.user_email
        if not email:
            return
        try:
            result = await self.api_client.accept_quest(email, quest_id)
            self.app.show_toast("📋 " + result.get("message", "Quest accepted!"), severity="information")
            self._clear_dynamic()
            self._show_text("📋 Quest accepted! Check your quest log for details.")
        except Exception as e:
            self.app.show_toast("⚠️ " + str(e), severity="warning")

    async def _complete_quest(self, quest_id: str) -> None:
        """Complete a quest and claim rewards."""
        email = self.app.user_email
        if not email:
            return
        try:
            result = await self.api_client.complete_quest(email, quest_id)
            reward_text = result.get("reward_text", "")
            self.app.show_toast("🎉 " + result.get("message", "Quest completed!"), severity="information")
            self._clear_dynamic()
            self._show_text(
                "🎉 QUEST COMPLETED!\n\n"
                + result.get("message", "") + "\n\n"
                "Rewards: " + reward_text
            )
            # Refresh character data (copper may have changed)
            await self.load_character_data()
        except Exception as e:
            self.app.show_toast("⚠️ " + str(e), severity="warning")

    async def _show_quests(self) -> None:
        """Show the player's quest log."""
        email = self.app.user_email
        if not email:
            self._show_text("📋 QUESTS\n\nNo user session found.")
            self._clear_dynamic()
            return

        try:
            quests = await self.api_client.get_quests(email)
        except Exception:
            quests = []

        active_quests = [q for q in quests if q.get("status") == "active"]
        completed_quests = [q for q in quests if q.get("status") == "completed"]

        if not quests:
            self._show_text(
                "📋 QUESTS\n\n"
                "No quests yet.\n\n"
                "Talk to NPCs to find available quests!"
            )
            self._clear_dynamic()
            return

        lines = ["📋 QUESTS\n"]

        if active_quests:
            lines.append("⚔️ Active Quests:")
            lines.append("")
            for q in active_quests:
                progress = q.get("progress", 0)
                obj_count = q.get("objective_count", 0)
                name = q.get("name", "Unknown")
                level = q.get("level", 1)
                obj_text = q.get("objective_text", "")
                turn_in = q.get("turn_in_npc", "")
                turn_in_region = q.get("turn_in_region", "")
                lines.append(f"  [Lv{level}] {name}")
                lines.append(f"    {obj_text}: {progress}/{obj_count}")
                if progress >= obj_count:
                    lines.append(f"    ✅ Complete! Report to {turn_in} in {turn_in_region}")
                else:
                    lines.append(f"    Turn in: {turn_in} in {turn_in_region}")
                lines.append("")

        if completed_quests:
            lines.append("")
            lines.append("✅ Completed Quests:")
            lines.append("")
            for q in completed_quests:
                name = q.get("name", "Unknown")
                level = q.get("level", 1)
                lines.append(f"  [Lv{level}] {name} — Completed")

        self._show_text("\n".join(lines))
        self._clear_dynamic()

    # ----------------------------------------------------------
    # Fight History
    # ----------------------------------------------------------

    def _open_fight_history(self) -> None:
        """Push the Fight History screen."""
        email = self.app.user_email
        if not email:
            self.app.show_toast("⚠️ No user session found.", severity="warning")
            return
        from dragons_legacy.frontend.screens.fight_history_screen import FightHistoryScreen
        self.app.push_screen(FightHistoryScreen(self.api_client, email))

    # ----------------------------------------------------------
    # Logout
    # ----------------------------------------------------------

    async def _handle_logout(self) -> None:
        if self._cooldown_timer is not None:
            self._cooldown_timer.stop()
            self._cooldown_timer = None
        self._cooldown_remaining = 0
        email = self.app.user_email
        if email:
            try:
                await self.api_client.logout_user(email)
            except Exception:
                pass
        self._chat_initialized = False
        self._chat_history = {"general": [], "group": [], "clan": []}
        self._chat_known_senders = set()
        self._chat_selected_targets = []
        await self._disconnect_chat()
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        if not any(screen.name == "login" for screen in self.app.screen_stack):
            self.app.push_screen("login")
        login_screen = self.app.get_screen("login")
        if hasattr(login_screen, "clear_inputs"):
            login_screen.clear_inputs()

    # ----------------------------------------------------------
    # Button handler
    # ----------------------------------------------------------

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # --- Logout ---
        if button_id == "back_btn":
            await self._handle_logout()
            return

        # --- Chat ---
        if button_id == "chat_btn":
            self._open_chat_modal()
            return

        # --- Action buttons ---
        if button_id == "btn_inventory":
            await self._show_inventory()

        elif button_id == "btn_character":
            self._open_character_modal()

        elif button_id == "btn_inv_back":
            await self._show_inventory()

        elif button_id == "btn_location":
            await self._show_location()

        elif button_id == "btn_bag":
            await self._show_bag()

        elif button_id == "btn_hunt":
            await self._show_hunt()

        elif button_id == "btn_fights":
            self._open_fight_history()

        elif button_id == "btn_mailbox":
            self._clear_dynamic()
            self._show_text(
                "📬 MAILBOX\n\n"
                "🚧 Coming Soon 🚧\n\n"
                "Send and receive messages from other\n"
                "adventurers in the realm."
            )

        elif button_id == "btn_quests":
            await self._show_quests()

        elif button_id == "btn_npc":
            await self._show_npc_list()

        elif button_id == "btn_debug_add":
            await self._show_debug_add_item()

        # --- Player list buttons (player_<nickname>) ---
        elif button_id.startswith("player_"):
            nickname = button_id[len("player_"):]
            self._open_player_profile(nickname)

        # --- Inventory category buttons (invcat_<category>) ---
        elif button_id.startswith("invcat_"):
            cat = button_id[len("invcat_"):]
            self._show_inventory_category(cat)

        # --- Inventory item buttons (invitem_<instance_id>) — open real modal ---
        elif button_id.startswith("invitem_"):
            raw = button_id[len("invitem_"):]
            for itm in self._player_inventory:
                if str(itm.get("instance_id")) == raw:
                    self._open_item_modal(itm)
                    break

        # --- Debug add item buttons (dbgadd_<catalog_id>) ---
        elif button_id.startswith("dbgadd_"):
            raw = button_id[len("dbgadd_"):]
            await self._debug_add_item_to_inventory(raw)

        # --- Dynamic travel buttons (id starts with "travel_") ---
        elif button_id.startswith("travel_"):
            raw = button_id[len("travel_"):]
            if self.character_data:
                current_map = self.character_data["current_map"]
                try:
                    region_info = await self.api_client.get_region_info(current_map)
                    connected = region_info.get("connected_regions", [])
                    for region in connected:
                        if _sanitize_id(region) == raw:
                            await self._initiate_travel(region)
                            return
                except Exception:
                    pass
            self._show_text("❌ Travel failed. Please try again.")
            self._clear_dynamic()

        # --- Dynamic NPC buttons (id starts with "npc_") ---
        elif button_id.startswith("npc_"):
            raw = button_id[len("npc_"):]
            npc_data = None
            for name, data in self._current_npcs.items():
                if _sanitize_id(name) == raw:
                    npc_data = data
                    break
            if npc_data:
                await self._interact_with_npc(npc_data)
            else:
                self._clear_dynamic()
                self._show_text("🧙 NPC not found.")

        # --- Quest buttons ---
        elif button_id.startswith("quest_accept_"):
            quest_id = button_id[len("quest_accept_"):]
            await self._accept_quest(quest_id)

        elif button_id.startswith("quest_complete_"):
            quest_id = button_id[len("quest_complete_"):]
            await self._complete_quest(quest_id)

        # --- Bag remove buttons (bag_remove_<slot_index>) ---
        elif button_id.startswith("bag_remove_"):
            raw = button_id[len("bag_remove_"):]
            try:
                slot_idx = int(raw)
                self._remove_from_bag(slot_idx)
            except ValueError:
                pass

        # --- Mob hunt buttons (id starts with "mob_") ---
        elif button_id.startswith("mob_"):
            raw = button_id[len("mob_"):]
            # raw is the sanitized mob name
            mob_name = None
            for mob in self._current_mobs:
                if _sanitize_id(mob["name"]) == raw:
                    mob_name = mob["name"]
                    break
            if mob_name:
                self._start_fight(mob_name)