"""
Fight screen for Legend of Dragon's Legacy.

Displays a turn-based battle between the player and a mob,
connected via WebSocket to the backend fight system.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Static
from textual.css.query import NoMatches
from textual.binding import Binding
import websockets
import json
import asyncio

from dragons_legacy.frontend.api_client import APIClient
from dragons_legacy.models.world_data import copper_to_parts


def _format_currency_rich(total_copper: int) -> str:
    """Format currency with Rich markup colors: gold=gold, silver=silver, copper=copper, amounts=white."""
    gold, silver, copper = copper_to_parts(total_copper)
    parts = []
    if gold > 0:
        parts.append("[white]" + str(gold) + "[/white][rgb(255,215,0)]g[/rgb(255,215,0)]")
    if silver > 0 or gold > 0:
        parts.append("[white]" + str(silver) + "[/white][rgb(192,192,192)]s[/rgb(192,192,192)]")
    parts.append("[white]" + str(copper) + "[/white][rgb(184,115,51)]c[/rgb(184,115,51)]")
    return " ".join(parts)


# ============================================================
# Fight Result Modal (Victory / Defeat)
# ============================================================

class FightResultModal(ModalScreen):
    """Modal overlay showing fight result (Victory or Defeat)."""

    CSS = """
    FightResultModal {
        align: center middle;
    }
    #fight-result-modal {
        width: 50;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 2 4;
    }
    #fight-result-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
        width: 100%;
    }
    .fight-result-victory {
        color: green;
    }
    .fight-result-defeat {
        color: red;
    }
    #fight-result-message {
        text-align: center;
        color: $text;
        margin: 1 0;
        width: 100%;
    }
    #fight-result-loot {
        text-align: center;
        margin: 1 0;
        width: 100%;
    }
    #fight-result-exp {
        text-align: center;
        color: yellow;
        text-style: bold;
        margin: 0 0 1 0;
        width: 100%;
    }
    #fight-result-levelup {
        text-align: center;
        color: cyan;
        text-style: bold;
        margin: 0 0 1 0;
        width: 100%;
    }
    #fight-result-close-row {
        layout: horizontal;
        width: 100%;
        margin-top: 2;
        height: auto;
    }
    #fight-result-close-row Button {
        width: 1fr;
        margin: 0 1;
    }
    """

    def __init__(self, winner: str, message: str, loot_copper: int = 0,
                 exp_gained: int = 0, leveled_up: bool = False, new_level: int = 0,
                 fight_stats: dict = None):
        super().__init__()
        self.winner = winner
        self.result_message = message
        self.loot_copper = loot_copper
        self.exp_gained = exp_gained
        self.leveled_up = leveled_up
        self.new_level = new_level
        self.fight_stats = fight_stats

    def compose(self) -> ComposeResult:
        with Container(id="fight-result-modal"):
            if self.winner == "player":
                yield Static("🏆 VICTORIOUS 🏆", id="fight-result-title", classes="fight-result-victory")
            else:
                yield Static("💀 DEFEAT 💀", id="fight-result-title", classes="fight-result-defeat")
            yield Static(self.result_message, id="fight-result-message")
            if self.loot_copper > 0:
                yield Static("💰 " + _format_currency_rich(self.loot_copper), id="fight-result-loot")
            if self.exp_gained > 0:
                yield Static("✨ +" + str(self.exp_gained) + " EXP", id="fight-result-exp")
            if self.leveled_up:
                yield Static("🎉 LEVEL UP! You are now Level " + str(self.new_level) + "!", id="fight-result-levelup")
            with Horizontal(id="fight-result-close-row"):
                yield Button("Close", variant="default", id="fight_result_close")
                yield Button("📊 Statistics", variant="default", id="fight_result_stats")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fight_result_close":
            self.dismiss("close")
        elif event.button.id == "fight_result_stats":
            self.dismiss("statistics")


# ============================================================
# Fight Screen
# ============================================================

class FightScreen(Screen):
    """Full-screen fight interface with attack options, fight log, and participant panels."""

    # Override escape binding to prevent leaving during active fight
    BINDINGS = [
        Binding("escape", "try_leave", "Leave", show=False),
    ]

    CSS = """
    FightScreen {
        background: $surface;
    }
    .fight-layout {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    .fight-top-bar {
        height: 3;
        width: 100%;
        background: #8B0000;
        align: center middle;
        padding: 0 2;
    }
    .fight-top-title {
        color: white;
        text-style: bold;
        text-align: center;
        width: 1fr;
    }
    .fight-chat-btn {
        width: auto;
        min-width: 12;
        height: 3;
        background: $surface;
        color: $text;
        border: solid $primary;
        margin: 0;
    }
    .fight-chat-btn:hover {
        background: $accent;
        color: $surface;
        border: solid $accent;
    }
    .fight-main {
        height: 1fr;
        width: 100%;
        layout: horizontal;
    }

    /* Left panel: attack options + fight log */
    .fight-left-panel {
        width: 1fr;
        height: 100%;
        layout: vertical;
        padding: 1;
        border-right: solid #8B0000;
    }
    .fight-section-title {
        text-style: bold;
        color: #FF4444;
        text-align: center;
        margin-bottom: 1;
        padding: 0 0 1 0;
        border-bottom: solid #8B0000;
    }
    .fight-attack-panel {
        height: auto;
        width: 100%;
        padding: 0 1;
    }
    .fight-attack-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin: 0 0 1 0;
    }
    .fight-attack-btn {
        width: 1fr;
        height: 3;
        margin: 0 1;
        background: $surface;
        color: $text;
        border: solid #8B0000;
    }
    .fight-attack-btn:hover {
        background: #8B0000;
        color: white;
        border: solid #8B0000;
    }
    .fight-attack-btn:focus {
        background: #8B0000;
        color: white;
        border: solid #FF4444;
    }
    .fight-attack-btn:disabled {
        opacity: 0.4;
        background: $surface;
        color: grey;
        border: solid grey;
    }
    .fight-timer-label {
        text-align: center;
        color: yellow;
        text-style: bold;
        margin: 0 0 1 0;
        height: 1;
    }
    .fight-turn-label {
        text-align: center;
        color: $accent;
        text-style: bold;
        margin: 0 0 1 0;
        height: 1;
    }
    .fight-log-panel {
        height: 1fr;
        width: 100%;
        border: solid #8B0000;
        padding: 1;
        background: $surface-darken-1;
    }
    #fight-log-content {
        width: 100%;
        height: auto;
        color: $text;
    }

    /* Right panel: battle participants */
    .fight-right-panel {
        width: 40;
        height: 100%;
        layout: vertical;
        padding: 1;
    }
    .fight-participants-panel {
        height: 1fr;
        width: 100%;
        layout: horizontal;
    }

    /* Player side of participants */
    .fight-player-side {
        width: 1fr;
        height: 100%;
        padding: 1;
        border-right: dashed #8B0000;
    }
    .fight-player-name {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    .fight-player-hp {
        color: red;
        text-style: bold;
        text-align: center;
        margin: 0;
    }
    .fight-player-mana {
        color: dodgerblue;
        text-style: bold;
        text-align: center;
        margin: 0;
    }

    /* Mob side of participants */
    .fight-mob-side {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    .fight-mob-name {
        text-style: bold;
        color: red;
        text-align: center;
        margin-bottom: 1;
    }
    .fight-mob-hp {
        color: red;
        text-style: bold;
        text-align: center;
        margin: 0;
    }
    .fight-mob-mana {
        color: dodgerblue;
        text-style: bold;
        text-align: center;
        margin: 0;
    }

    /* Bag slots panel in fight */
    .fight-bag-panel {
        height: auto;
        width: 100%;
        padding: 0 1;
        margin-top: 1;
        border-top: dashed #8B0000;
    }
    .fight-bag-title {
        text-style: bold;
        color: #FF4444;
        text-align: center;
        margin: 1 0 0 0;
    }
    .fight-bag-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin: 0 0 1 0;
    }
    .fight-bag-btn {
        width: 1fr;
        height: 3;
        margin: 0 1;
        background: $surface;
        color: $text;
        border: solid #8B0000;
        text-style: bold;
    }
    .fight-bag-btn:hover {
        background: #8B0000;
        color: white;
        border: solid #8B0000;
    }
    .fight-bag-btn:focus {
        background: #8B0000;
        color: white;
        border: solid #FF4444;
    }
    .fight-bag-btn:disabled {
        opacity: 0.4;
        background: $surface;
        color: grey;
        border: solid grey;
        text-style: none;
    }
    .fight-regen-label {
        text-align: center;
        color: green;
        text-style: bold;
        margin: 0;
        height: auto;
    }

    /* Combo panel */
    .fight-combo-panel {
        height: auto;
        width: 100%;
        padding: 0 1;
        margin-top: 1;
        border-top: dashed #8B0000;
    }
    .fight-combo-title {
        text-style: bold;
        color: #FF4444;
        text-align: center;
        margin: 1 0 0 0;
    }
    .fight-combo-selector-row {
        layout: horizontal;
        height: auto;
        width: 100%;
        margin: 0;
        align: center middle;
    }
    .fight-combo-nav-btn {
        width: 5;
        height: 3;
        margin: 0;
        background: $surface;
        color: $text;
        border: solid #8B0000;
    }
    .fight-combo-nav-btn:hover {
        background: #8B0000;
        color: white;
    }
    .fight-combo-name-label {
        width: 1fr;
        text-align: center;
        text-style: bold;
        color: $accent;
        height: 3;
        content-align: center middle;
    }
    .fight-combo-indicator {
        text-align: center;
        color: yellow;
        text-style: bold;
        margin: 0 0 1 0;
        height: auto;
    }
    .fight-combo-effect-label {
        text-align: center;
        color: #AAAAAA;
        margin: 0 0 1 0;
        height: auto;
    }
    """

    def __init__(self, api_client: APIClient, email: str, mob_name: str = "", rejoin: bool = False):
        super().__init__()
        self.api_client = api_client
        self.email = email
        self.mob_name = mob_name
        self._rejoin = rejoin
        self._fight_socket = None
        self._fight_listener_task = None
        self._fight_id = None
        self._fight_log: list[str] = []
        self._turn_timer = None
        self._turn_seconds_left = 0
        self._is_player_turn = False
        self._fight_active = False
        # Bag slots cached from server
        self._bag_slots: list[dict] = []
        # Active regen effects: list of {"item_name": str, "ticks_left": int, "max_hp": int, "max_mana": int}
        self._regen_effects: list[dict] = []
        self._regen_timer = None
        # Power boost: applies 35% extra damage on the next player attack
        self._power_boost_active = False
        # Cooldown system
        self._power_used = False  # Power potion: one-time use per fight
        # Item-type cooldowns: {"HP Potion": seconds, "Mana Potion": seconds}
        self._item_type_cooldowns: dict[str, int] = {}
        self._cooldown_timer = None
        # Combo system
        self._combos: list[dict] = []  # Loaded from API
        self._selected_combo_index: int = 0  # Currently selected combo in dropdown

    def compose(self) -> ComposeResult:
        with Container(classes="fight-layout"):
            # Top bar
            with Horizontal(classes="fight-top-bar"):
                yield Static("⚔️ BATTLE ⚔️", classes="fight-top-title")
                yield Button("💬 Chat", variant="default", id="fight_chat_btn", classes="fight-chat-btn")

            # Main content
            with Horizontal(classes="fight-main"):
                # Left panel: attack options + fight log
                with Vertical(classes="fight-left-panel"):
                    yield Static("⚔️ ATTACK OPTIONS", classes="fight-section-title")
                    yield Static("", id="fight-turn-label", classes="fight-turn-label")
                    yield Static("", id="fight-timer-label", classes="fight-timer-label")
                    with Vertical(classes="fight-attack-panel"):
                        with Horizontal(classes="fight-attack-row"):
                            yield Button("🎯 Head", variant="default", id="attack_head", classes="fight-attack-btn", disabled=True)
                            yield Button("🫁 Chest", variant="default", id="attack_chest", classes="fight-attack-btn", disabled=True)
                            yield Button("🦵 Legs", variant="default", id="attack_legs", classes="fight-attack-btn", disabled=True)

                    # Bag slots
                    with Vertical(classes="fight-bag-panel"):
                        yield Static("🎒 BAG", classes="fight-bag-title")
                        with Horizontal(classes="fight-bag-row"):
                            yield Button("Slot 1: Empty", variant="default", id="fight_bag_0", classes="fight-bag-btn", disabled=True)
                            yield Button("Slot 2: Empty", variant="default", id="fight_bag_1", classes="fight-bag-btn", disabled=True)
                            yield Button("Moroks: Empty", variant="default", id="fight_bag_2", classes="fight-bag-btn", disabled=True)
                        yield Static("", id="fight-regen-label", classes="fight-regen-label")

                    yield Static("📜 FIGHT LOG", classes="fight-section-title")
                    with VerticalScroll(classes="fight-log-panel"):
                        yield Static("Connecting to battle server...", id="fight-log-content")

                # Right panel: battle participants + combo indicator
                with Vertical(classes="fight-right-panel"):
                    yield Static("👥 BATTLE PARTICIPANTS", classes="fight-section-title")
                    with Horizontal(classes="fight-participants-panel"):
                        # Player + moroks side
                        with VerticalScroll(classes="fight-player-side"):
                            with Vertical(classes="fight-player-info"):
                                yield Static("...", id="fight-player-name", classes="fight-player-name")
                                yield Static("HP: -/-", id="fight-player-hp", classes="fight-player-hp")
                                yield Static("Mana: -/-", id="fight-player-mana", classes="fight-player-mana")
                            # Moroks container
                            with Vertical(id="fight-moroks-container", classes="fight-moroks-container"):
                                pass  # Moroks will be added dynamically
                        # Mob side
                        with Vertical(classes="fight-mob-side"):
                            yield Static("...", id="fight-mob-name", classes="fight-mob-name")
                            yield Static("HP: -/-", id="fight-mob-hp", classes="fight-mob-hp")
                            yield Static("Mana: -/-", id="fight-mob-mana", classes="fight-mob-mana")

                    # Combo indicator panel
                    with Vertical(classes="fight-combo-panel"):
                        yield Static("⚡ COMBOS", classes="fight-combo-title")
                        with Horizontal(classes="fight-combo-selector-row"):
                            yield Button("◀", variant="default", id="combo_prev", classes="fight-combo-nav-btn")
                            yield Static("Loading...", id="fight-combo-name", classes="fight-combo-name-label")
                            yield Button("▶", variant="default", id="combo_next", classes="fight-combo-nav-btn")
                        yield Static("", id="fight-combo-indicator", classes="fight-combo-indicator")
                        yield Static("", id="fight-combo-effect", classes="fight-combo-effect-label")

    async def on_show(self) -> None:
        """Connect to fight WebSocket and start the fight."""
        await self._load_bag_slots()
        await self._load_combos()
        await self._connect_fight()

    async def on_hide(self) -> None:
        """Clean up when leaving the fight screen."""
        self._stop_turn_timer()
        self._stop_regen_timer()
        self._stop_cooldown_timer()
        await self._disconnect_fight()

    def action_try_leave(self) -> None:
        """Handle escape key — only allow leaving if fight is over."""
        if self._fight_active:
            # Fight is still active — do not allow leaving
            self._add_log("⚠️ You cannot leave during an active battle!")
            return
        # Fight is over, allow leaving
        self.app.pop_screen()

    # ----------------------------------------------------------
    # WebSocket connection
    # ----------------------------------------------------------

    async def _connect_fight(self) -> None:
        """Connect to the fight WebSocket and start or rejoin a fight."""
        try:
            self._fight_socket = await websockets.connect("ws://localhost:8000/ws/fight")
            if self._rejoin:
                # Rejoin existing fight
                await self._fight_socket.send(json.dumps({
                    "type": "rejoin_fight",
                    "email": self.email,
                }))
            else:
                # Start new fight
                await self._fight_socket.send(json.dumps({
                    "type": "start_fight",
                    "email": self.email,
                    "mob_name": self.mob_name,
                }))
            # Start listener
            self._fight_listener_task = self.run_worker(self._listen_for_fight(), exclusive=False)
        except Exception:
            self._add_log("⚠️ Failed to connect to battle server.")

    async def _disconnect_fight(self) -> None:
        """Disconnect from fight WebSocket without ending the fight.
        
        The fight continues server-side. The player can rejoin later.
        We do NOT send leave_fight — that would end the battle.
        """
        if self._fight_listener_task:
            self._fight_listener_task.cancel()
            self._fight_listener_task = None
        if self._fight_socket:
            try:
                await self._fight_socket.close()
            except Exception:
                pass
            self._fight_socket = None

    async def _listen_for_fight(self) -> None:
        """Listen for fight WebSocket messages."""
        if not self._fight_socket:
            return
        while True:
            try:
                data = await self._fight_socket.recv()
            except Exception:
                self._add_log("⚠️ Connection to battle server lost.")
                break
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = message.get("type")

            if msg_type == "fight_started":
                self._fight_id = message["state"]["fight_id"]
                self._fight_active = True
                self._add_log(message.get("log", "Battle begins!"))
                self._update_participants(message["state"])
                self._update_moroks_display(message.get("state", {}))
                if message["state"].get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")
                self._update_bag_slot_buttons()
                # Schedule a second update to guarantee buttons are enabled
                # after the DOM has fully settled from the initial render.
                self.call_later(self._update_bag_slot_buttons)

            elif msg_type == "fight_rejoined":
                self._fight_id = message["state"]["fight_id"]
                self._fight_active = True
                # Restore fight log history
                log_history = message.get("log_history", [])
                for log_line in log_history:
                    self._add_log(log_line)
                self._add_log(message.get("log", "⚡ Reconnected!"))
                self._update_participants(message["state"])
                # Restore turn state
                if message["state"].get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")

                # Restore server-side state: regen effects, cooldowns, power_used
                state = message["state"]

                # Restore power_used
                self._power_used = state.get("power_used", False)

                # Restore item-type cooldowns from server
                server_cooldowns = state.get("item_cooldowns", {})
                self._item_type_cooldowns = {}
                for item_name, secs in server_cooldowns.items():
                    if secs > 0:
                        self._item_type_cooldowns[item_name] = secs
                if self._item_type_cooldowns:
                    self._ensure_cooldown_timer()

                # Restore regen effects from server state
                server_regen = state.get("regen_effects", [])
                self._regen_effects = []
                for eff in server_regen:
                    self._regen_effects.append({
                        "type": eff["type"],
                        "ticks_left": eff["ticks_left"],
                        "seconds_until_next": eff["seconds_until_next"],
                    })
                if self._regen_effects:
                    # Start client-side display timer (server drives actual regen)
                    if self._regen_timer is None:
                        self._regen_timer = self.set_interval(1.0, self._tick_regen)
                    self._update_regen_label()

                self._update_bag_slot_buttons()
                self.call_later(self._update_bag_slot_buttons)

            elif msg_type == "player_attack_result":
                result = message.get("result", {})
                is_auto = message.get("auto_attack", False)
                log_text = result.get("log", "")
                if is_auto:
                    log_text = "⏰ [Auto] " + log_text
                # Highlight events
                events = result.get("events", [])
                if "power_boost" in events:
                    log_text = "⚡ " + log_text
                if "critical" in events:
                    log_text = "💥 " + log_text
                elif "dodge" in events:
                    log_text = "💨 " + log_text
                elif "block" in events:
                    log_text = "🔰 " + log_text
                self._add_log(log_text)
                self._update_participants(message["state"])
                self._update_moroks_display(message.get("state", {}))

                if result.get("fight_over"):
                    # Fight over handled by fight_over message
                    pass
                else:
                    # Waiting for mob or morok turn
                    self._set_player_turn(False, message.get("state", {}))
                    self._stop_turn_timer()
                    self._update_timer_label("")

            elif msg_type == "mob_attack_result":
                result = message.get("result", {})
                log_text = result.get("log", "")
                events = result.get("events", [])
                target = result.get("target", "player")
                
                # Only add to fight log if attacking player
                if target == "player":
                    if "critical" in events:
                        log_text = "💥 " + log_text
                    elif "dodge" in events:
                        log_text = "💨 " + log_text
                    elif "block" in events:
                        log_text = "🔰 " + log_text
                    self._add_log(log_text)
                
                self._update_participants(message["state"])
                self._update_moroks_display(message.get("state", {}))

                if result.get("fight_over"):
                    pass
                else:
                    state = message.get("state", {})
                    turn = state.get("turn")
                    if turn == "player":
                        self._set_player_turn(True)
                        self._start_turn_timer()
                    else:
                        self._set_player_turn(False, state)
                        self._update_timer_label("")

            elif msg_type == "morok_summoned":
                morok = message.get("morok", {})
                log_text = message.get("log", "")
                self._add_log(log_text)
                self._update_participants(message.get("state", {}))
                # Update moroks display
                self._update_moroks_display(message.get("state", {}))

            elif msg_type == "morok_attack_result":
                # Morok attack result - update UI but don't add to fight log
                result = message.get("result", {})
                state = message.get("state", {})
                self._update_participants(state)
                self._update_moroks_display(state)
                
                # Check if fight ended
                if result.get("fight_over"):
                    pass  # Fight end will be handled by fight_over message
                else:
                    turn = state.get("turn")
                    if turn == "player":
                        self._set_player_turn(True)
                        self._start_turn_timer()
                    else:
                        self._set_player_turn(False, state)
                        self._update_timer_label("")

            elif msg_type == "regen_tick":
                # Server applied a regen tick — update UI
                regen_type = message.get("regen_type", "")
                amount = message.get("amount", 0)
                if regen_type == "hp" and amount > 0:
                    self._add_log(f"💚 HP +{amount} (potion regen)")
                elif regen_type == "mana" and amount > 0:
                    self._add_log(f"💙 Mana +{amount} (potion regen)")
                self._update_participants(message["state"])
                self._update_moroks_display(message.get("state", {}))
                if message.get("state", {}).get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")

            elif msg_type == "power_boost_applied":
                # Server confirms power boost was consumed on this attack
                bonus_dmg = message.get("bonus_damage", 0)
                if bonus_dmg > 0:
                    self._add_log(f"⚡ Power boost: +{bonus_dmg} bonus damage!")

            elif msg_type == "combo_triggered":
                combo_name = message.get("name", "")
                effect_type = message.get("effect_type", "")
                newly_discovered = message.get("newly_discovered", False)
                combo_id = message.get("combo_id", "")

                if newly_discovered:
                    self._add_log(f"🔓 COMBO DISCOVERED: {combo_name}!")
                    # Reload combos from server to get revealed sequence symbols
                    self.run_worker(self._load_combos(), exclusive=False)

                if effect_type == "bleeding":
                    bleed_dmg = message.get("bleed_damage", 0)
                    self._add_log(f"🩸 COMBO: {combo_name}! Enemy is bleeding ({bleed_dmg} dmg every 5s)!")
                elif effect_type == "lifesteal":
                    lifesteal = message.get("lifesteal_amount", 0)
                    self._add_log(f"🧛 COMBO: {combo_name}! Drained {lifesteal} HP from the enemy!")

                self._update_participants(message.get("state", {}))
                self._update_moroks_display(message.get("state", {}))
                if message.get("state", {}).get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")

            elif msg_type == "regen_ended":
                regen_type = message.get("regen_type", "")
                regen_log = message.get("log", "")
                if regen_log:
                    self._add_log(regen_log)
                # Remove matching client-side regen effect
                self._regen_effects = [e for e in self._regen_effects if e["type"] != regen_type]
                if not self._regen_effects:
                    self._stop_regen_timer()
                else:
                    self._update_regen_label()
                self._update_participants(message.get("state", {}))
                self._update_moroks_display(message.get("state", {}))
                if message.get("state", {}).get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")

            elif msg_type == "bleeding_tick":
                bleed_log = message.get("log", "")
                if bleed_log:
                    self._add_log(bleed_log)
                self._update_participants(message.get("state", {}))
                self._update_moroks_display(message.get("state", {}))
                if message.get("state", {}).get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")

            elif msg_type == "bleeding_ended":
                bleed_log = message.get("log", "")
                if bleed_log:
                    self._add_log(bleed_log)
                self._update_participants(message.get("state", {}))
                self._update_moroks_display(message.get("state", {}))
                if message.get("state", {}).get("turn") == "player":
                    self._set_player_turn(True)
                    self._start_turn_timer()
                else:
                    self._set_player_turn(False, message["state"])
                    self._update_timer_label("")

            elif msg_type == "fight_over":
                self._fight_active = False
                self._stop_turn_timer()
                self._stop_regen_timer()
                self._stop_cooldown_timer()
                self._set_player_turn(False, message.get("state", {}))
                winner = message.get("winner", "")
                result_msg = message.get("message", "")
                loot_copper = message.get("loot_copper", 0)
                exp_gained = message.get("exp_gained", 0)
                leveled_up = message.get("leveled_up", False)
                new_level = message.get("new_level", 0)
                fight_stats = message.get("fight_stats", {})
                self._add_log(result_msg)
                if loot_copper > 0:
                    self._add_log("💰 Loot: " + _format_currency_rich(loot_copper))
                if exp_gained > 0:
                    self._add_log("✨ +" + str(exp_gained) + " EXP")
                if leveled_up:
                    self._add_log("🎉 LEVEL UP! Now Level " + str(new_level) + "!")
                self._update_participants(message["state"])
                self._update_moroks_display(message.get("state", {}))
                self._update_turn_label("Fight Over!")
                self._update_timer_label("")
                # Show result modal
                self.call_later(lambda: self._show_result_modal(
                    winner, result_msg, loot_copper, exp_gained, leveled_up, new_level,
                    fight_stats
                ))

            elif msg_type == "error":
                self._add_log("⚠️ " + message.get("message", "Error"))

            elif msg_type == "fight_left":
                self._fight_active = False
                self._stop_turn_timer()
                self._stop_cooldown_timer()

    # ----------------------------------------------------------
    # UI update helpers
    # ----------------------------------------------------------

    def _add_log(self, text: str) -> None:
        """Add a line to the fight log."""
        self._fight_log.append(text)
        # Keep last 50 lines
        if len(self._fight_log) > 50:
            self._fight_log = self._fight_log[-50:]
        try:
            log_widget = self.query_one("#fight-log-content", Static)
            log_widget.update("\n".join(self._fight_log))
        except NoMatches:
            pass

    def _update_participants(self, state: dict) -> None:
        """Update the participant panels with current HP/Mana."""
        player = state.get("player", {})
        mob = state.get("mob", {})
        try:
            self.query_one("#fight-player-name", Static).update(
                "🛡️ " + player.get("nickname", "Player")
            )
            self.query_one("#fight-player-hp", Static).update(
                "❤️ " + str(player.get("hp", 0)) + "/" + str(player.get("max_hp", 0))
            )
            self.query_one("#fight-player-mana", Static).update(
                "💧 " + str(player.get("mana", 0)) + "/" + str(player.get("max_mana", 0))
            )
            self.query_one("#fight-mob-name", Static).update(
                "👹 " + mob.get("display_name", "Mob")
            )
            mob_hp_text = "❤️ " + str(mob.get("hp", 0)) + "/" + str(mob.get("max_hp", 0))
            bleed_secs = state.get("bleed_seconds", 0)
            if bleed_secs > 0:
                mob_hp_text += f"\n🩸 Bleeding: {bleed_secs}s"
            self.query_one("#fight-mob-hp", Static).update(mob_hp_text)
            self.query_one("#fight-mob-mana", Static).update(
                "💧 " + str(mob.get("mana", 0)) + "/" + str(mob.get("max_mana", 0))
            )
        except NoMatches:
            pass

    def _update_moroks_display(self, state: dict) -> None:
        """Update the moroks display in the participants panel."""
        moroks = state.get("moroks", [])
        try:
            container = self.query_one("#fight-moroks-container", Vertical)
            # Clear existing morok displays
            container.remove_children()
            
            # Add morok displays for alive moroks
            for morok in moroks:
                if morok.get("hp", 0) > 0:
                    morok_name = morok.get("display_name", "Morok")
                    morok_hp = morok.get("hp", 0)
                    morok_max_hp = morok.get("max_hp", 1)
                    
                    # Create morok widget with nested Static widgets
                    from textual.widgets import Static
                    name_label = Static(f"🐴 {morok_name}", classes="fight-morok-name")
                    hp_label = Static(f"❤️ {morok_hp}/{morok_max_hp}", classes="fight-morok-hp")
                    
                    morok_widget = Vertical(name_label, hp_label, classes="fight-morok-entry")
                    container.mount(morok_widget)
        except NoMatches:
            pass

    def _set_player_turn(self, is_player: bool, state: dict | None = None) -> None:
        """Enable/disable attack buttons based on whose turn it is."""
        self._is_player_turn = is_player
        try:
            self.query_one("#attack_head", Button).disabled = not is_player
            self.query_one("#attack_chest", Button).disabled = not is_player
            self.query_one("#attack_legs", Button).disabled = not is_player
        except NoMatches:
            pass

        if is_player:
            self._update_turn_label("⚔️ Your turn! Choose an attack:")
        else:
            self._update_turn_label_from_state(state or {})

    def _update_turn_label_from_state(self, state: dict) -> None:
        """Update the turn label based on current fight state."""
        turn = state.get("turn")
        target = state.get("current_mob_target")
        if turn == "mob":
            if target == "morok":
                label = "👹 Mob attacks morok..."
            else:
                label = "👹 Mob's turn..."
        elif turn == "morok":
            label = "🐴 Morok's turn..."
        elif turn == "player":
            label = "⚔️ Your turn! Choose an attack:"
        else:
            label = "Waiting..."
        self._update_turn_label(label)

    def _update_turn_label(self, text: str) -> None:
        """Update the turn indicator label."""
        try:
            self.query_one("#fight-turn-label", Static).update(text)
        except NoMatches:
            pass

    def _update_timer_label(self, text: str) -> None:
        """Update the timer label."""
        try:
            self.query_one("#fight-timer-label", Static).update(text)
        except NoMatches:
            pass

    # ----------------------------------------------------------
    # Turn timer (10 second countdown)
    # ----------------------------------------------------------

    def _start_turn_timer(self) -> None:
        """Start the 10-second turn timer."""
        self._stop_turn_timer()
        self._turn_seconds_left = 10
        self._update_timer_label("⏱️ " + str(self._turn_seconds_left) + "s")
        self._turn_timer = self.set_interval(1.0, self._tick_turn_timer)

    def _stop_turn_timer(self) -> None:
        """Stop the turn timer."""
        if self._turn_timer:
            self._turn_timer.stop()
            self._turn_timer = None

    def _tick_turn_timer(self) -> None:
        """Called every second to decrement the turn timer."""
        self._turn_seconds_left = max(0, self._turn_seconds_left - 1)
        if self._turn_seconds_left > 0:
            self._update_timer_label("⏱️ " + str(self._turn_seconds_left) + "s")
        else:
            self._update_timer_label("⏰ Auto-attacking...")
            self._stop_turn_timer()

    # ----------------------------------------------------------
    # Bag slots in fight
    # ----------------------------------------------------------

    async def _load_bag_slots(self) -> None:
        """Load bag slot data from server and update UI."""
        try:
            self._bag_slots = await self.api_client.get_bag(self.email)
        except Exception:
            self._bag_slots = []
        self._update_bag_slot_buttons()

    def _update_bag_slot_buttons(self) -> None:
        """Update the bag slot button labels and enabled state."""
        for idx in range(3):
            btn_id = f"fight_bag_{idx}"
            try:
                btn = self.query_one(f"#{btn_id}", Button)
            except NoMatches:
                continue

            slot = None
            for s in self._bag_slots:
                if s.get("slot_index") == idx:
                    slot = s
                    break

            slot_label = "Moroks" if idx == 2 else f"Slot {idx + 1}"
            if slot and slot.get("item_name") and slot.get("quantity", 0) > 0:
                item_name = slot["item_name"]
                base_label = f"{slot_label}: {item_name} x{slot['quantity']}"

                # Morok slot - enable for summoning when fight is active
                if idx == 2:
                    btn.label = f"🐴 {base_label}"
                    # Enable morok slot for summoning when fight is active
                    should_disable = not self._fight_active
                # Check item-type cooldown (HP Potion / Mana Potion share cooldown by type)
                elif item_name in self._item_type_cooldowns:
                    cd = self._item_type_cooldowns.get(item_name, 0)
                    if cd > 0:
                        btn.label = f"{base_label} ⏳{cd}s"
                        should_disable = True
                    elif item_name == "Power Potion" and self._power_used:
                        btn.label = f"{slot_label}: {item_name} x{slot['quantity']} (Used)"
                        should_disable = True
                    else:
                        btn.label = base_label
                        should_disable = not self._fight_active
                elif item_name == "Power Potion" and self._power_used:
                    btn.label = f"{slot_label}: {item_name} x{slot['quantity']} (Used)"
                    should_disable = True
                else:
                    btn.label = base_label
                    should_disable = not self._fight_active
            else:
                btn.label = f"{slot_label}: Empty"
                should_disable = True

            # Force-update the disabled state and trigger a refresh so the
            # Textual renderer picks up the change even when called from a
            # background worker (WebSocket listener).
            if btn.disabled != should_disable:
                btn.disabled = should_disable
            else:
                # Even if the value is the same, explicitly set it so the
                # widget re-validates its visual state after mount/show.
                btn.disabled = should_disable
            btn.refresh()

    async def _use_bag_slot(self, slot_index: int) -> None:
        """Use a consumable from a bag slot during fight."""
        if not self._fight_active:
            return

        # Find the slot data
        slot = None
        for s in self._bag_slots:
            if s.get("slot_index") == slot_index:
                slot = s
                break
        if not slot or not slot.get("item_name") or slot.get("quantity", 0) <= 0:
            self._add_log("⚠️ Slot is empty.")
            return

        item_name = slot["item_name"]

        # Check item-type cooldown (HP Potion / Mana Potion)
        cd = self._item_type_cooldowns.get(item_name, 0)
        if cd > 0:
            self._add_log(f"⚠️ {item_name} cooldown active: {cd}s remaining.")
            return

        # Check if power potion was already used this fight
        if item_name == "Power Potion" and self._power_used:
            self._add_log("⚠️ Power Potion can only be used once per fight!")
            return

        try:
            result = await self.api_client.use_bag_item_in_fight(self.email, slot_index)
        except Exception as e:
            self._add_log("⚠️ Failed to use item: " + str(e))
            return

        remaining = result.get("remaining", 0)
        used_item_name = result.get("item_name", item_name)

        # Update local cache
        if remaining <= 0:
            slot["item_name"] = ""
            slot["item_catalog_id"] = None
            slot["quantity"] = 0
        else:
            slot["quantity"] = remaining

        if used_item_name == "HP Potion":
            self._add_log("🧪 Used HP Potion! Regenerating HP over 20 seconds...")
            self._start_regen_effect("hp")
            # Notify server to start server-side regen + cooldown tracking
            await self._send_start_regen("hp", "HP Potion")
            # Start 40-second cooldown from the moment of use (per item type)
            self._item_type_cooldowns["HP Potion"] = 40
            self._ensure_cooldown_timer()
        elif used_item_name == "Mana Potion":
            self._add_log("🧪 Used Mana Potion! Regenerating Mana over 20 seconds...")
            self._start_regen_effect("mana")
            await self._send_start_regen("mana", "Mana Potion")
            # Start 40-second cooldown from the moment of use (per item type)
            self._item_type_cooldowns["Mana Potion"] = 40
            self._ensure_cooldown_timer()
        elif used_item_name == "Power Potion":
            self._add_log("⚡ Used Power Potion! Next attack deals 35% more damage!")
            self._power_boost_active = True
            self._power_used = True
            await self._send_start_regen("", "Power Potion")
        else:
            self._add_log(f"🧪 Used {used_item_name}.")

        self._update_bag_slot_buttons()

    async def _summon_morok_from_slot(self) -> None:
        """Summon a morok from the morok bag slot."""
        if not self._fight_active or not self._fight_id:
            return

        # Find the morok slot
        morok_slot = None
        for s in self._bag_slots:
            if s.get("slot_index") == 2:
                morok_slot = s
                break
        
        if not morok_slot or not morok_slot.get("item_name") or morok_slot.get("quantity", 0) <= 0:
            self._add_log("⚠️ No moroks available to summon.")
            return

        # Get morok data from the slot
        morok_name = morok_slot["item_name"]
        
        # Build morok data for the server
        morok_data = {
            "name": morok_name,
        }

        # Send summon request to server
        try:
            await self._fight_socket.send(json.dumps({
                "type": "summon_morok",
                "fight_id": self._fight_id,
                "morok_data": morok_data,
            }))
        except Exception as e:
            self._add_log(f"⚠️ Failed to summon morok: {e}")
            return

        # Decrement local quantity (server will also decrement)
        morok_slot["quantity"] -= 1
        if morok_slot["quantity"] <= 0:
            morok_slot["item_name"] = ""
            morok_slot["item_catalog_id"] = None
            morok_slot["quantity"] = 0
        
        self._update_bag_slot_buttons()

    def _start_regen_effect(self, regen_type: str) -> None:
        """Start a timed regen effect: 10% every 4s for 20s (5 ticks)."""
        self._regen_effects.append({
            "type": regen_type,  # "hp" or "mana"
            "ticks_left": 5,  # 5 ticks × 4 seconds = 20 seconds
            "seconds_until_next": 4,
        })
        # Ensure the regen timer is running
        if self._regen_timer is None:
            self._regen_timer = self.set_interval(1.0, self._tick_regen)
        self._update_regen_label()

    def _tick_regen(self) -> None:
        """Called every second to process regen effects."""
        if not self._regen_effects or not self._fight_active:
            self._stop_regen_timer()
            return

        effects_to_remove = []
        for effect in self._regen_effects:
            effect["seconds_until_next"] -= 1
            if effect["seconds_until_next"] <= 0:
                # Apply regen tick
                self._apply_regen_tick(effect)
                effect["ticks_left"] -= 1
                effect["seconds_until_next"] = 4

                if effect["ticks_left"] <= 0:
                    effects_to_remove.append(effect)

        for e in effects_to_remove:
            self._regen_effects.remove(e)
            regen_type = e["type"]
            if regen_type == "hp":
                self._add_log("💚 HP regeneration effect ended.")
            elif regen_type == "mana":
                self._add_log("💙 Mana regeneration effect ended.")

        if not self._regen_effects:
            self._stop_regen_timer()

        self._update_regen_label()

    def _apply_regen_tick(self, effect: dict) -> None:
        """Process one tick of regen for display purposes.
        
        The actual HP/Mana change is driven by the server-side regen loop.
        This method only exists to update the client-side display timer.
        """
        pass  # Server drives the actual regen; client just tracks display

    async def _send_start_regen(self, regen_type: str, item_name: str) -> None:
        """Notify the server to start a server-side regen effect and track cooldowns."""
        if not self._fight_socket or not self._fight_id:
            return
        try:
            await self._fight_socket.send(json.dumps({
                "type": "start_regen",
                "fight_id": self._fight_id,
                "regen_type": regen_type,
                "item_name": item_name,
            }))
        except Exception:
            pass

    def _stop_regen_timer(self) -> None:
        """Stop the regen timer."""
        if self._regen_timer:
            self._regen_timer.stop()
            self._regen_timer = None
        self._regen_effects.clear()
        self._update_regen_label()

    def _update_regen_label(self) -> None:
        """Update the regen status label."""
        try:
            label = self.query_one("#fight-regen-label", Static)
        except NoMatches:
            return

        if not self._regen_effects:
            label.update("")
            return

        parts = []
        for e in self._regen_effects:
            regen_type = e["type"]
            ticks = e["ticks_left"]
            secs = e["seconds_until_next"] + (ticks - 1) * 4
            if regen_type == "hp":
                parts.append(f"💚 HP regen: {secs}s left")
            elif regen_type == "mana":
                parts.append(f"💙 Mana regen: {secs}s left")
        label.update(" | ".join(parts))

    # ----------------------------------------------------------
    # Cooldown timer
    # ----------------------------------------------------------

    def _ensure_cooldown_timer(self) -> None:
        """Start the cooldown timer if not already running."""
        if self._cooldown_timer is None:
            self._cooldown_timer = self.set_interval(1.0, self._tick_cooldown)

    def _tick_cooldown(self) -> None:
        """Called every second to decrement item-type cooldowns."""
        if not self._item_type_cooldowns:
            self._stop_cooldown_timer()
            return

        expired = []
        for item_name in list(self._item_type_cooldowns.keys()):
            self._item_type_cooldowns[item_name] -= 1
            if self._item_type_cooldowns[item_name] <= 0:
                expired.append(item_name)

        for item_name in expired:
            del self._item_type_cooldowns[item_name]

        self._update_bag_slot_buttons()

        if not self._item_type_cooldowns:
            self._stop_cooldown_timer()

    def _stop_cooldown_timer(self) -> None:
        """Stop the cooldown timer."""
        if self._cooldown_timer:
            self._cooldown_timer.stop()
            self._cooldown_timer = None

    # ----------------------------------------------------------
    # Combo system
    # ----------------------------------------------------------

    async def _load_combos(self) -> None:
        """Load combo data from server."""
        try:
            self._combos = await self.api_client.get_combos(self.email)
        except Exception:
            self._combos = []
        self._selected_combo_index = 0
        self._update_combo_display()

    def _update_combo_display(self) -> None:
        """Update the combo indicator panel based on current selection."""
        try:
            name_label = self.query_one("#fight-combo-name", Static)
            indicator_label = self.query_one("#fight-combo-indicator", Static)
            effect_label = self.query_one("#fight-combo-effect", Static)
        except NoMatches:
            return

        if not self._combos:
            name_label.update("No combos available")
            indicator_label.update("")
            effect_label.update("")
            return

        # Clamp index
        if self._selected_combo_index >= len(self._combos):
            self._selected_combo_index = 0
        if self._selected_combo_index < 0:
            self._selected_combo_index = len(self._combos) - 1

        combo = self._combos[self._selected_combo_index]
        combo_name = combo.get("name", "Unknown")
        unlocked = combo.get("unlocked", False)
        required_level = combo.get("required_level", 1)

        if not unlocked:
            name_label.update(f"🔒 {combo_name} (Lv.{required_level})")
            indicator_label.update("? ? ?")
            effect_label.update("Unlock at level " + str(required_level))
            return

        # Show combo name
        name_label.update(f"⚡ {combo_name}")

        # Show sequence indicator
        display_seq = combo.get("display_sequence", [])
        indicator_text = "  ".join(display_seq) if display_seq else "?"
        indicator_label.update(indicator_text)

        # Show effect description
        effect = combo.get("effect", "")
        effect_label.update(effect)

    def _cycle_combo(self, direction: int) -> None:
        """Cycle through combos. direction: +1 for next, -1 for previous."""
        if not self._combos:
            return
        self._selected_combo_index = (self._selected_combo_index + direction) % len(self._combos)
        self._update_combo_display()

    # ----------------------------------------------------------
    # Fight result modal
    # ----------------------------------------------------------

    def _show_result_modal(self, winner: str, message: str, loot_copper: int = 0,
                           exp_gained: int = 0, leveled_up: bool = False, new_level: int = 0,
                           fight_stats: dict = None) -> None:
        """Show the fight result modal."""
        captured_stats = fight_stats

        def on_result(result):
            # When modal is closed, go back to game screen and refresh HUD
            from dragons_legacy.frontend.screens.game_screen import GameScreen
            # Find the GameScreen on the stack so we can refresh it after popping
            game_screen = None
            for screen in self.app.screen_stack:
                if isinstance(screen, GameScreen):
                    game_screen = screen
                    break

            if result == "statistics" and captured_stats:
                # Pop fight screen first, then push statistics screen
                self.app.pop_screen()
                # Explicitly refresh the game screen HUD
                if game_screen is not None:
                    self.app.call_later(lambda: game_screen.run_worker(game_screen.refresh_after_fight()))
                # Push the fight statistics screen
                from dragons_legacy.frontend.screens.fight_statistics_screen import FightStatisticsScreen
                self.app.push_screen(FightStatisticsScreen(captured_stats, self.api_client))
            else:
                self.app.pop_screen()
                # Explicitly refresh the game screen HUD
                if game_screen is not None:
                    self.app.call_later(lambda: game_screen.run_worker(game_screen.refresh_after_fight()))

        self.app.push_screen(
            FightResultModal(winner, message, loot_copper, exp_gained, leveled_up, new_level,
                             fight_stats=fight_stats),
            callback=on_result,
        )

    # ----------------------------------------------------------
    # Button handler
    # ----------------------------------------------------------

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle attack button presses."""
        button_id = event.button.id

        if button_id == "fight_chat_btn":
            # Delegate chat to the GameScreen which is still on the screen stack
            from dragons_legacy.frontend.screens.game_screen import GameScreen
            for screen in self.app.screen_stack:
                if isinstance(screen, GameScreen):
                    screen._open_chat_modal()
                    return
            return

        # Combo navigation buttons
        if button_id == "combo_prev":
            self._cycle_combo(-1)
            return
        if button_id == "combo_next":
            self._cycle_combo(1)
            return

        # Bag slot buttons
        if button_id.startswith("fight_bag_"):
            raw = button_id[len("fight_bag_"):]
            try:
                slot_idx = int(raw)
                # Morok slot (index 2) - summon morok
                if slot_idx == 2:
                    await self._summon_morok_from_slot()
                    return
                await self._use_bag_slot(slot_idx)
            except ValueError:
                pass
            return

        if button_id in ("attack_head", "attack_chest", "attack_legs"):
            if not self._fight_socket or not self._fight_id or not self._is_player_turn:
                return

            attack_type = button_id.replace("attack_", "")

            # Stop timer
            self._stop_turn_timer()

            # Disable buttons immediately
            self._set_player_turn(False)

            # Check for power boost
            power_boost = self._power_boost_active
            if power_boost:
                self._power_boost_active = False

            # Send attack
            try:
                await self._fight_socket.send(json.dumps({
                    "type": "attack",
                    "fight_id": self._fight_id,
                    "attack_type": attack_type,
                    "power_boost": power_boost,
                }))
            except Exception:
                self._add_log("⚠️ Failed to send attack.")