"""
Fight Statistics screen for Legend of Dragon's Legacy.

Shows detailed stats for a single fight in a table
divided into Players and Mobs sections.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static

from dragons_legacy.frontend.api_client import APIClient
from dragons_legacy.models.world_data import copper_to_parts


def _format_currency_rich(total_copper: int) -> str:
    """Format currency with Rich markup colors."""
    gold, silver, copper = copper_to_parts(total_copper)
    parts = []
    if gold > 0:
        parts.append("[white]" + str(gold) + "[/white][rgb(255,215,0)]g[/rgb(255,215,0)]")
    if silver > 0 or gold > 0:
        parts.append("[white]" + str(silver) + "[/white][rgb(192,192,192)]s[/rgb(192,192,192)]")
    parts.append("[white]" + str(copper) + "[/white][rgb(184,115,51)]c[/rgb(184,115,51)]")
    return " ".join(parts)


class FightStatisticsScreen(Screen):
    """Screen showing detailed fight statistics in a Players vs Mobs table."""

    CSS = """
    FightStatisticsScreen {
        background: $surface;
    }
    #fstats-layout {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    #fstats-top-bar {
        height: 3;
        width: 100%;
        background: #8B0000;
        align: center middle;
        padding: 0 2;
    }
    #fstats-top-title {
        color: white;
        text-style: bold;
        text-align: center;
        width: 1fr;
    }
    #fstats-content {
        width: 100%;
        height: 1fr;
        align: center middle;
        padding: 2;
    }
    #fstats-box {
        width: 80;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 2;
    }
    #fstats-result-label {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }
    .fstats-victory {
        color: green;
    }
    .fstats-defeat {
        color: red;
    }
    #fstats-table-container {
        width: 100%;
        height: auto;
        layout: horizontal;
    }
    .fstats-section {
        width: 1fr;
        height: auto;
        padding: 1;
    }
    .fstats-section-title {
        text-style: bold;
        text-align: center;
        color: $accent;
        width: 100%;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: solid $primary;
    }
    .fstats-divider {
        width: 1;
        height: auto;
        background: $primary;
    }
    .fstats-row {
        width: 100%;
        height: auto;
        margin: 0 0 0 0;
    }
    .fstats-label {
        color: $text-muted;
        width: 100%;
        margin: 0;
    }
    .fstats-value {
        color: $text;
        text-style: bold;
        width: 100%;
        margin: 0 0 1 0;
    }
    .fstats-name {
        color: $accent;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    .fstats-mob-name {
        color: red;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #fstats-rewards {
        width: 100%;
        height: auto;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary;
    }
    #fstats-rewards-title {
        text-style: bold;
        text-align: center;
        color: yellow;
        width: 100%;
        margin-bottom: 1;
    }
    .fstats-reward-line {
        text-align: center;
        width: 100%;
    }
    #fstats-close-row {
        layout: horizontal;
        width: 100%;
        margin-top: 2;
        height: auto;
    }
    #fstats-close-row Button {
        width: 1fr;
    }
    """

    def __init__(self, fight_stats: dict, api_client: APIClient = None):
        super().__init__()
        self._stats = fight_stats
        self.api_client = api_client

    def compose(self) -> ComposeResult:
        s = self._stats
        victory = s.get("victory", False)
        player_name = s.get("player_name", "Player")
        player_level = s.get("player_level", 1)
        mob_name = s.get("mob_name", "Mob")
        mob_level = s.get("mob_level", 1)
        player_dmg_dealt = s.get("player_damage_dealt", 0)
        player_dmg_taken = s.get("player_damage_taken", 0)
        mob_dmg_dealt = s.get("mob_damage_dealt", 0)
        mob_dmg_taken = s.get("mob_damage_taken", 0)
        exp_gained = s.get("exp_gained", 0)
        loot_copper = s.get("loot_copper", 0)

        result_text = "🏆 VICTORY" if victory else "💀 DEFEAT"
        result_class = "fstats-victory" if victory else "fstats-defeat"

        with Container(id="fstats-layout"):
            with Horizontal(id="fstats-top-bar"):
                yield Static("📊 FIGHT STATISTICS", id="fstats-top-title")

            with Container(id="fstats-content"):
                with Vertical(id="fstats-box"):
                    yield Static(result_text, id="fstats-result-label", classes=result_class)

                    with Horizontal(id="fstats-table-container"):
                        # Players section
                        with Vertical(classes="fstats-section"):
                            yield Static("⚔️ Players", classes="fstats-section-title")
                            yield Static(
                                "🛡️ " + player_name + " [" + str(player_level) + "]",
                                classes="fstats-name",
                            )
                            with Vertical(classes="fstats-row"):
                                yield Static("Damage Dealt:", classes="fstats-label")
                                yield Static(str(player_dmg_dealt), classes="fstats-value")
                            with Vertical(classes="fstats-row"):
                                yield Static("Damage Taken:", classes="fstats-label")
                                yield Static(str(player_dmg_taken), classes="fstats-value")
                            with Vertical(classes="fstats-row"):
                                yield Static("EXP Gained:", classes="fstats-label")
                                yield Static(
                                    "✨ +" + str(exp_gained) if exp_gained > 0 else "0",
                                    classes="fstats-value",
                                )

                        # Vertical divider
                        yield Static("", classes="fstats-divider")

                        # Mobs section
                        with Vertical(classes="fstats-section"):
                            yield Static("👹 Mobs", classes="fstats-section-title")
                            yield Static(
                                "👹 " + mob_name + " [" + str(mob_level) + "]",
                                classes="fstats-mob-name",
                            )
                            with Vertical(classes="fstats-row"):
                                yield Static("Damage Dealt:", classes="fstats-label")
                                yield Static(str(mob_dmg_dealt), classes="fstats-value")
                            with Vertical(classes="fstats-row"):
                                yield Static("Damage Taken:", classes="fstats-label")
                                yield Static(str(mob_dmg_taken), classes="fstats-value")
                            with Vertical(classes="fstats-row"):
                                yield Static("EXP Gained:", classes="fstats-label")
                                yield Static("—", classes="fstats-value")

                    # Rewards section
                    if victory and (exp_gained > 0 or loot_copper > 0):
                        with Vertical(id="fstats-rewards"):
                            yield Static("🎁 Rewards", id="fstats-rewards-title")
                            if exp_gained > 0:
                                yield Static(
                                    "✨ +" + str(exp_gained) + " EXP",
                                    classes="fstats-reward-line",
                                )
                            if loot_copper > 0:
                                yield Static(
                                    "💰 " + _format_currency_rich(loot_copper),
                                    classes="fstats-reward-line",
                                )

                    with Horizontal(id="fstats-close-row"):
                        yield Button("Close", variant="default", id="fstats_close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fstats_close":
            self.app.pop_screen()
