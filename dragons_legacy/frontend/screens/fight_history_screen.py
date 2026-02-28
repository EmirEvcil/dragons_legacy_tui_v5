"""
Fight History screen for Legend of Dragon's Legacy.

Lists all past fight statistics with date, time, mob info, and outcome.
Clicking an entry opens the detailed Fight Statistics screen.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from dragons_legacy.frontend.api_client import APIClient


class FightHistoryScreen(Screen):
    """Screen listing all past fights for the player."""

    CSS = """
    FightHistoryScreen {
        background: $surface;
    }
    #fhist-layout {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    #fhist-top-bar {
        height: 3;
        width: 100%;
        background: #8B0000;
        align: center middle;
        padding: 0 2;
    }
    #fhist-top-title {
        color: white;
        text-style: bold;
        text-align: center;
        width: 1fr;
    }
    #fhist-content {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    #fhist-entries {
        width: 100%;
        height: auto;
    }
    #fhist-list-header {
        text-style: bold;
        color: $accent;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: solid $primary;
    }
    .fhist-entry-btn {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
        background: $surface;
        color: $text;
        border: solid $primary;
    }
    .fhist-entry-btn:hover {
        background: $primary;
        color: $surface;
    }
    .fhist-entry-btn:focus {
        background: $accent;
        color: $surface;
        border: solid $accent;
    }
    .fhist-victory {
        border: solid green;
        color: green;
    }
    .fhist-victory:hover {
        background: green;
        color: white;
        border: solid green;
    }
    .fhist-defeat {
        border: solid red;
        color: red;
    }
    .fhist-defeat:hover {
        background: red;
        color: white;
        border: solid red;
    }
    #fhist-empty {
        text-align: center;
        color: $text-muted;
        margin-top: 4;
        width: 100%;
    }
    #fhist-back-row {
        height: auto;
        width: 100%;
        padding: 1 2;
    }
    #fhist-back-row Button {
        width: 100%;
    }
    """

    def __init__(self, api_client: APIClient, email: str):
        super().__init__()
        self.api_client = api_client
        self.email = email
        self._fight_history: list[dict] = []

    def compose(self) -> ComposeResult:
        with Container(id="fhist-layout"):
            with Horizontal(id="fhist-top-bar"):
                yield Static("📜 FIGHT HISTORY", id="fhist-top-title")

            with VerticalScroll(id="fhist-content"):
                yield Static("⚔️ Past Battles", id="fhist-list-header")
                yield Vertical(id="fhist-entries")

            with Horizontal(id="fhist-back-row"):
                yield Button("← Back", variant="default", id="fhist_back")

    async def on_show(self) -> None:
        """Load fight history when the screen is shown."""
        await self._load_history()

    async def _load_history(self) -> None:
        """Fetch fight history from the API and populate the list."""
        try:
            self._fight_history = await self.api_client.get_fight_history(self.email)
        except Exception:
            self._fight_history = []

        container = self.query_one("#fhist-entries", Vertical)
        container.remove_children()

        if not self._fight_history:
            container.mount(Static("No fights recorded yet.", id="fhist-empty"))
            return

        for entry in self._fight_history:
            stat_id = entry.get("id", 0)
            fight_date = entry.get("fight_date", "")
            victory = entry.get("victory", False)
            mob_name = entry.get("mob_name", "Unknown")
            mob_level = entry.get("mob_level", 1)

            # Parse and format the date
            date_display = self._format_date(fight_date)
            outcome = "Victory" if victory else "Defeat"
            outcome_icon = "🏆" if victory else "💀"

            label = (
                date_display + "  |  "
                + outcome_icon + " " + outcome + "  |  "
                + mob_name + " [" + str(mob_level) + "]"
            )

            css_class = "fhist-entry-btn fhist-victory" if victory else "fhist-entry-btn fhist-defeat"
            btn = Button(
                label,
                variant="default",
                id="fhist_entry_" + str(stat_id),
                classes=css_class,
            )
            container.mount(btn)

    def _format_date(self, iso_date: str) -> str:
        """Format an ISO date string to a readable format."""
        try:
            from datetime import datetime
            # Handle ISO format with timezone info
            dt_str = iso_date.replace("T", " ")
            if "+" in dt_str:
                dt_str = dt_str.split("+")[0]
            if "." in dt_str:
                dt_str = dt_str.split(".")[0]
            dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return iso_date[:16] if len(iso_date) >= 16 else iso_date

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "fhist_back":
            self.app.pop_screen()
            return

        if button_id.startswith("fhist_entry_"):
            raw_id = button_id[len("fhist_entry_"):]
            try:
                stat_id = int(raw_id)
            except ValueError:
                return

            # Find the entry in the cached history
            entry = None
            for e in self._fight_history:
                if e.get("id") == stat_id:
                    entry = e
                    break

            if not entry:
                # Fallback: fetch from API
                try:
                    entry = await self.api_client.get_fight_stat_detail(self.email, stat_id)
                except Exception:
                    return

            if entry:
                from dragons_legacy.frontend.screens.fight_statistics_screen import FightStatisticsScreen
                self.app.push_screen(FightStatisticsScreen(entry, self.api_client))
