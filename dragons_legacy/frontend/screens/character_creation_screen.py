"""
Character creation screen for Legend of Dragon's Legacy
"""

import re

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static
from textual.validation import ValidationResult, Validator

from dragons_legacy.frontend.api_client import APIClient


class NicknameValidator(Validator):
    """Validate character nickname."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate nickname format."""
        if not value:
            return self.failure("Nickname is required")
        
        if len(value) > 12:
            return self.failure("Nickname must be at most 12 characters")
        
        if " " in value:
            return self.failure("Nickname must not contain spaces")
        
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            return self.failure("Only letters and numbers are allowed")
        
        return self.success()


class CharacterCreationScreen(Screen):
    """Character creation screen with race, gender, and nickname selection."""
    
    CSS_PATH = None  # Will use main CSS
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.selected_race: str | None = None
        self.selected_gender: str | None = None
        self.is_loading = False
    
    def compose(self) -> ComposeResult:
        """Compose the character creation screen."""
        with Container(classes="container"):
            with Vertical(classes="form-container"):
                yield Static("⚔️ CHARACTER CREATION ⚔️", classes="title")
                yield Static("Forge your legend", classes="subtitle")
                
                # Race selection
                yield Label("Choose your Race:", classes="label")
                with Horizontal(classes="selection-row"):
                    yield Button("Magmar (Coming Soon)", variant="default", id="race_magmar", classes="race-btn race-disabled", disabled=True)
                    yield Button("Human", variant="default", id="race_human", classes="race-btn")
                
                # Gender selection
                yield Label("Choose your Gender:", classes="label")
                with Horizontal(classes="selection-row"):
                    yield Button("Female", variant="default", id="gender_female", classes="gender-btn")
                    yield Button("Male", variant="default", id="gender_male", classes="gender-btn")
                
                # Nickname input
                yield Label("Choose your Nickname:", classes="label")
                yield Input(
                    placeholder="Enter nickname (max 12 chars, no spaces or special chars)",
                    validators=[NicknameValidator()],
                    max_length=12,
                    id="nickname_input"
                )
                
                yield Button("Create Character", variant="primary", id="create_btn")
                yield Button("Back to Login", variant="default", id="back_btn")
                
                yield Static("", id="message", classes="")
    
    def on_mount(self) -> None:
        """Reset state when screen mounts."""
        self.reset_state()
    
    def on_show(self) -> None:
        """Reset state when screen is shown."""
        self.reset_state()
        self.query_one("#nickname_input", Input).focus()
    
    def reset_state(self):
        """Reset all selections and inputs."""
        self.selected_race = None
        self.selected_gender = None
        self.is_loading = False
        self.query_one("#nickname_input", Input).value = ""
        self.query_one("#message", Static).update("")
        self.query_one("#message", Static).set_classes("")
        self._update_race_buttons()
        self._update_gender_buttons()
    
    def _update_race_buttons(self):
        """Update race button styles based on selection."""
        magmar_btn = self.query_one("#race_magmar", Button)
        human_btn = self.query_one("#race_human", Button)
        
        # Magmar is always disabled (coming soon)
        magmar_btn.set_classes("race-btn race-disabled")
        magmar_btn.disabled = True
        
        if self.selected_race == "human":
            human_btn.set_classes("race-btn race-human-selected")
        else:
            human_btn.set_classes("race-btn")
    
    def _update_gender_buttons(self):
        """Update gender button styles based on selection."""
        female_btn = self.query_one("#gender_female", Button)
        male_btn = self.query_one("#gender_male", Button)
        
        if self.selected_gender == "female":
            female_btn.set_classes("gender-btn gender-selected")
            male_btn.set_classes("gender-btn")
        elif self.selected_gender == "male":
            female_btn.set_classes("gender-btn")
            male_btn.set_classes("gender-btn gender-selected")
        else:
            female_btn.set_classes("gender-btn")
            male_btn.set_classes("gender-btn")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if self.is_loading:
            return
        
        button_id = event.button.id
        
        # Race selection (Magmar is disabled/coming soon)
        if button_id == "race_human":
            self.selected_race = "human"
            self._update_race_buttons()
        
        # Gender selection
        elif button_id == "gender_female":
            self.selected_gender = "female"
            self._update_gender_buttons()
        elif button_id == "gender_male":
            self.selected_gender = "male"
            self._update_gender_buttons()
        
        # Create character
        elif button_id == "create_btn":
            await self.handle_create_character()
        
        # Back to login
        elif button_id == "back_btn":
            # Clear the screen stack and return to login
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            if not any(screen.name == "login" for screen in self.app.screen_stack):
                self.app.push_screen("login")
            login_screen = self.app.get_screen("login")
            if hasattr(login_screen, "clear_inputs"):
                login_screen.clear_inputs()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in nickname input."""
        if event.input.id == "nickname_input":
            await self.handle_create_character()
    
    async def handle_create_character(self) -> None:
        """Handle character creation."""
        if self.is_loading:
            return
        
        message_widget = self.query_one("#message", Static)
        nickname_input = self.query_one("#nickname_input", Input)
        
        # Validate race selection
        if not self.selected_race:
            message_widget.update("Please select a race")
            message_widget.set_classes("error")
            return
        
        # Validate gender selection
        if not self.selected_gender:
            message_widget.update("Please select a gender")
            message_widget.set_classes("error")
            return
        
        # Validate nickname
        nickname_valid = nickname_input.validate(nickname_input.value)
        if not nickname_valid.is_valid:
            error_msg = nickname_valid.failure_descriptions[0] if nickname_valid.failure_descriptions else "Invalid nickname"
            message_widget.update(f"Nickname: {error_msg}")
            message_widget.set_classes("error")
            return
        
        # Show loading state
        self.is_loading = True
        message_widget.update("Creating your character...")
        message_widget.set_classes("loading")
        
        try:
            # Attempt character creation
            result = await self.api_client.create_character(
                email=self.app.user_email,
                nickname=nickname_input.value,
                race=self.selected_race,
                gender=self.selected_gender
            )
            
            # Success
            race_display = self.selected_race.capitalize()
            self.app.show_toast(
                f"⚔️ {nickname_input.value} the {race_display} has entered the realm!",
                severity="information"
            )
            message_widget.update("")
            message_widget.set_classes("")
            
            # Transition to game screen
            self.set_timer(1.0, lambda: self.app.push_screen("game"))
            
        except Exception as e:
            error_msg = "Character creation failed. Please try again."
            error_str = str(e).lower()
            
            if "nickname already taken" in error_str:
                error_msg = "This nickname is already taken. Please choose a different one."
            elif "nickname" in error_str:
                error_msg = "Invalid nickname format"
            elif "network" in error_str or "connection" in error_str:
                error_msg = "Unable to connect to server. Please try again later."
            
            message_widget.update(error_msg)
            message_widget.set_classes("error")
            
        finally:
            self.is_loading = False