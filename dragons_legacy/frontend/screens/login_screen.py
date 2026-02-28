"""
Login screen for Legend of Dragon's Legacy
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static
from textual.validation import Function, ValidationResult, Validator
import re

from dragons_legacy.frontend.api_client import APIClient


class EmailValidator(Validator):
    """Validate email format."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate email format."""
        if not value:
            return self.failure("Email is required")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return self.failure("Invalid email format")
        
        return self.success()


class PasswordValidator(Validator):
    """Validate password."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate password."""
        if not value:
            return self.failure("Password is required")
        
        if len(value) < 6:
            return self.failure("Password must be at least 6 characters")
        
        return self.success()


class LoginScreen(Screen):
    """Login screen with email/password and forgot password option."""
    
    CSS_PATH = None  # Will use main CSS
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.is_loading = False
    
    def compose(self) -> ComposeResult:
        """Compose the login screen."""
        with Container(classes="container"):
            with Vertical(classes="form-container"):
                yield Static("🐉 LEGEND OF DRAGON'S LEGACY 🐉", classes="title")
                yield Static("Enter the realm of adventure", classes="subtitle")
                
                yield Label("Email:", classes="label")
                yield Input(
                    placeholder="Enter your email",
                    validators=[EmailValidator()],
                    id="email_input"
                )
                
                yield Label("Password:", classes="label")
                yield Input(
                    placeholder="Enter your password",
                    password=True,
                    validators=[PasswordValidator()],
                    id="password_input"
                )
                
                yield Button("Login", variant="primary", id="login_btn")
                yield Button("Register", variant="default", id="register_btn")
                yield Button("Forgot Password?", variant="default", id="forgot_btn")
                
                yield Static("", id="message", classes="")
    
    def on_mount(self) -> None:
        """Focus email input when screen mounts."""
        self.clear_inputs()
        self.query_one("#email_input", Input).focus()
    
    def on_show(self) -> None:
        """Reset state when screen is shown."""
        self.clear_inputs()
        self.query_one("#email_input", Input).focus()
    
    def clear_inputs(self):
        """Clear all input fields."""
        self.query_one("#email_input", Input).value = ""
        self.query_one("#password_input", Input).value = ""
        self.query_one("#message", Static).update("")
        self.query_one("#message", Static).set_classes("")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if self.is_loading:
            return
            
        if event.button.id == "login_btn":
            await self.handle_login()
        elif event.button.id == "register_btn":
            self.app.push_screen("registration")
        elif event.button.id == "forgot_btn":
            self.app.push_screen("forgot_password")
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in inputs."""
        if event.input.id == "email_input":
            self.query_one("#password_input", Input).focus()
        elif event.input.id == "password_input":
            await self.handle_login()
    
    async def handle_login(self) -> None:
        """Handle login attempt."""
        if self.is_loading:
            return
            
        email_input = self.query_one("#email_input", Input)
        password_input = self.query_one("#password_input", Input)
        message_widget = self.query_one("#message", Static)
        
        # Validate inputs
        email_valid = email_input.validate(email_input.value)
        password_valid = password_input.validate(password_input.value)
        
        if not email_valid.is_valid or not password_valid.is_valid:
            error_messages = []
            if not email_valid.is_valid:
                error_messages.append(f"Email: {email_valid.failure_descriptions[0] if email_valid.failure_descriptions else 'Invalid'}")
            if not password_valid.is_valid:
                error_messages.append(f"Password: {password_valid.failure_descriptions[0] if password_valid.failure_descriptions else 'Invalid'}")
            
            message_widget.update(" • ".join(error_messages))
            message_widget.set_classes("error")
            return
        
        # Show loading state
        self.is_loading = True
        message_widget.update("Logging in...")
        message_widget.set_classes("loading")
        
        try:
            # Attempt login
            result = await self.api_client.login_user(
                email_input.value,
                password_input.value
            )
            
            # Success - show toast and transition based on character existence
            self.app.show_toast("🐉 Login successful! Welcome back, adventurer!", severity="information")
            message_widget.update("")
            message_widget.set_classes("")
            
            # Store user email for later use
            self.app.user_email = email_input.value
            
            # Route based on whether the user already has a character
            has_character = result.get("has_character", False)
            if has_character:
                self.set_timer(1.0, lambda: self.app.push_screen("game"))
            else:
                self.set_timer(1.0, lambda: self.app.push_screen("character_creation"))
            
        except Exception as e:
            # Handle login failure
            error_msg = "Invalid email or password"
            if "email" in str(e).lower():
                error_msg = "Invalid email format"
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                error_msg = "Unable to connect to server. Please try again later."
            
            message_widget.update(error_msg)
            message_widget.set_classes("error")
            
        finally:
            self.is_loading = False