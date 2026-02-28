"""
Registration screen for Legend of Dragon's Legacy
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static, Select
from textual.validation import ValidationResult, Validator
import re

from dragons_legacy.frontend.api_client import APIClient
from dragons_legacy.frontend.screens.login_screen import EmailValidator, PasswordValidator


class ConfirmPasswordValidator(Validator):
    """Validate password confirmation."""
    
    def __init__(self, password_input_id: str):
        super().__init__()
        self.password_input_id = password_input_id
    
    def validate(self, value: str) -> ValidationResult:
        """Validate password confirmation."""
        if not value:
            return self.failure("Please confirm your password")
        
        # Get the original password from the form
        # This will be handled in the screen's validation logic
        return self.success()


class SecurityAnswerValidator(Validator):
    """Validate security answer."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate security answer."""
        if not value:
            return self.failure("Security answer is required")
        
        if len(value.strip()) < 2:
            return self.failure("Security answer must be at least 2 characters")
        
        return self.success()


class RegistrationScreen(Screen):
    """Registration screen with security question selection."""
    
    CSS_PATH = None  # Will use main CSS
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.is_loading = False
        self.security_questions = []
    
    def compose(self) -> ComposeResult:
        """Compose the registration screen."""
        with Container(classes="container"):
            with Vertical(classes="form-container"):
                yield Static("🐉 CREATE YOUR LEGEND 🐉", classes="title")
                yield Static("Join the adventure and create your account", classes="subtitle")
                
                yield Label("Email:", classes="label")
                yield Input(
                    placeholder="Enter your email",
                    validators=[EmailValidator()],
                    id="email_input"
                )
                
                yield Label("Password:", classes="label")
                yield Input(
                    placeholder="Enter your password (min 6 characters)",
                    password=True,
                    validators=[PasswordValidator()],
                    id="password_input"
                )
                
                yield Label("Confirm Password:", classes="label")
                yield Input(
                    placeholder="Confirm your password",
                    password=True,
                    validators=[ConfirmPasswordValidator("password_input")],
                    id="confirm_password_input"
                )
                
                yield Label("Security Question:", classes="label")
                yield Select(
                    options=[],
                    prompt="Choose a security question...",
                    id="security_question_select"
                )
                
                yield Label("Security Answer:", classes="label")
                yield Input(
                    placeholder="Enter your security answer",
                    validators=[SecurityAnswerValidator()],
                    id="security_answer_input"
                )
                
                yield Button("Create Account", variant="primary", id="register_btn")
                yield Button("Back to Login", variant="default", id="back_btn")
                
                yield Static("", id="message", classes="")
    
    async def on_mount(self) -> None:
        """Load security questions when screen mounts."""
        self.clear_inputs()
        await self.load_security_questions()
        self.query_one("#email_input", Input).focus()
    
    def on_show(self) -> None:
        """Reset state when screen is shown."""
        self.clear_inputs()
        self.query_one("#email_input", Input).focus()
    
    def clear_inputs(self):
        """Clear all input fields."""
        self.query_one("#email_input", Input).value = ""
        self.query_one("#password_input", Input).value = ""
        self.query_one("#confirm_password_input", Input).value = ""
        self.query_one("#security_answer_input", Input).value = ""
        self.query_one("#message", Static).update("")
        self.query_one("#message", Static).set_classes("")
        # Reset security question select if present
        select_widget = self.query_one("#security_question_select", Select)
        if hasattr(select_widget, 'value'):
            select_widget.value = Select.BLANK
    
    async def load_security_questions(self) -> None:
        """Load security questions from the API."""
        try:
            self.security_questions = await self.api_client.get_security_questions()
            
            select_widget = self.query_one("#security_question_select", Select)
            options = [(q["question_text"], q["id"]) for q in self.security_questions]
            select_widget.set_options(options)
            
        except Exception as e:
            message_widget = self.query_one("#message", Static)
            message_widget.update("Failed to load security questions. Please try again.")
            message_widget.set_classes("error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if self.is_loading:
            return
            
        if event.button.id == "register_btn":
            await self.handle_registration()
        elif event.button.id == "back_btn":
            self.app.pop_screen()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in inputs."""
        if event.input.id == "email_input":
            self.query_one("#password_input", Input).focus()
        elif event.input.id == "password_input":
            self.query_one("#confirm_password_input", Input).focus()
        elif event.input.id == "confirm_password_input":
            self.query_one("#security_question_select", Select).focus()
        elif event.input.id == "security_answer_input":
            await self.handle_registration()
    
    async def handle_registration(self) -> None:
        """Handle registration attempt."""
        if self.is_loading:
            return
            
        email_input = self.query_one("#email_input", Input)
        password_input = self.query_one("#password_input", Input)
        confirm_password_input = self.query_one("#confirm_password_input", Input)
        security_question_select = self.query_one("#security_question_select", Select)
        security_answer_input = self.query_one("#security_answer_input", Input)
        message_widget = self.query_one("#message", Static)
        
        # Validate all inputs
        email_valid = email_input.validate(email_input.value)
        password_valid = password_input.validate(password_input.value)
        answer_valid = security_answer_input.validate(security_answer_input.value)
        
        # Check password confirmation
        if password_input.value != confirm_password_input.value:
            message_widget.update("Passwords do not match")
            message_widget.set_classes("error")
            return
        
        # Check security question selection
        if security_question_select.value == Select.BLANK:
            message_widget.update("Please select a security question")
            message_widget.set_classes("error")
            return
        
        if not email_valid.is_valid or not password_valid.is_valid or not answer_valid.is_valid:
            error_messages = []
            if not email_valid.is_valid:
                error_messages.append(f"Email: {email_valid.failure_descriptions[0] if email_valid.failure_descriptions else 'Invalid'}")
            if not password_valid.is_valid:
                error_messages.append(f"Password: {password_valid.failure_descriptions[0] if password_valid.failure_descriptions else 'Invalid'}")
            if not answer_valid.is_valid:
                error_messages.append(f"Security Answer: {answer_valid.failure_descriptions[0] if answer_valid.failure_descriptions else 'Invalid'}")
            
            message_widget.update(" • ".join(error_messages))
            message_widget.set_classes("error")
            return
        
        # Show loading state
        self.is_loading = True
        message_widget.update("Creating your account...")
        message_widget.set_classes("loading")
        
        try:
            # Attempt registration
            result = await self.api_client.register_user(
                email=email_input.value,
                password=password_input.value,
                security_question_id=security_question_select.value,
                security_answer=security_answer_input.value
            )
            
            # Success - show toast and transition to character creation
            self.app.show_toast("🐉 Account created successfully! Welcome to the realm!", severity="information")
            message_widget.update("")
            message_widget.set_classes("")
            
            # Store user email for later use
            self.app.user_email = email_input.value
            
            # Transition to character creation after a brief moment
            self.set_timer(1.0, lambda: self.app.push_screen("character_creation"))
            
        except Exception as e:
            # Handle registration failure
            error_msg = "Registration failed. Please try again."
            error_str = str(e).lower()
            
            if "email already registered" in error_str:
                error_msg = "This email is already registered. Please use a different email or try logging in."
            elif "email" in error_str:
                error_msg = "Invalid email format"
            elif "password" in error_str:
                error_msg = "Password does not meet requirements"
            elif "network" in error_str or "connection" in error_str:
                error_msg = "Unable to connect to server. Please try again later."
            
            message_widget.update(error_msg)
            message_widget.set_classes("error")
            
        finally:
            self.is_loading = False