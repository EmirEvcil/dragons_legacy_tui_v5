"""
Forgot password screen for Legend of Dragon's Legacy
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static
from textual.validation import ValidationResult, Validator

from dragons_legacy.frontend.api_client import APIClient
from dragons_legacy.frontend.screens.login_screen import EmailValidator, PasswordValidator


class ForgotPasswordScreen(Screen):
    """Forgot password screen with security question verification."""
    
    CSS_PATH = None  # Will use main CSS
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.is_loading = False
        self.step = 1  # 1: Enter email, 2: Answer security question, 3: Set new password
        self.user_email = ""
        self.security_question = ""
    
    def reset_screen_state(self):
        """Reset the screen to initial state."""
        self.is_loading = False
        self.step = 1
        self.user_email = ""
        self.security_question = ""
        self.clear_inputs()
    
    def clear_inputs(self):
        """Clear all input fields."""
        self.query_one("#email_input", Input).value = ""
        self.query_one("#answer_input", Input).value = ""
        self.query_one("#new_password_input", Input).value = ""
        self.query_one("#confirm_password_input", Input).value = ""
        self.query_one("#message", Static).update("")
        self.query_one("#message", Static).set_classes("")
        self.query_one("#question_label", Label).update("")
    
    def compose(self) -> ComposeResult:
        """Compose the forgot password screen."""
        with Container(classes="container"):
            with Vertical(classes="form-container"):
                yield Static("🔐 RESET YOUR PASSWORD 🔐", classes="title")
                yield Static("Recover access to your adventure", classes="subtitle")
                
                # Step 1: Email input
                yield Label("Email:", classes="label", id="email_label")
                yield Input(
                    placeholder="Enter your email address",
                    validators=[EmailValidator()],
                    id="email_input"
                )
                
                # Step 2: Security question (hidden initially)
                yield Label("", classes="label", id="question_label")
                yield Input(
                    placeholder="",
                    id="answer_input",
                    disabled=True
                )
                
                # Step 3: New password (hidden initially)
                yield Label("", classes="label", id="new_password_label")
                yield Input(
                    placeholder="",
                    password=True,
                    validators=[PasswordValidator()],
                    id="new_password_input",
                    disabled=True
                )
                
                yield Label("", classes="label", id="confirm_password_label")
                yield Input(
                    placeholder="",
                    password=True,
                    id="confirm_password_input",
                    disabled=True
                )
                
                yield Button("Continue", variant="primary", id="continue_btn")
                yield Button("Back to Login", variant="default", id="back_btn")
                
                yield Static("", id="message", classes="")
    
    def on_mount(self) -> None:
        """Focus email input when screen mounts."""
        self.reset_screen_state()
        self.query_one("#email_input", Input).focus()
        self.update_step_display()
    
    def on_show(self) -> None:
        """Reset state when screen is shown."""
        self.reset_screen_state()
        self.query_one("#email_input", Input).focus()
        self.update_step_display()
    
    def update_step_display(self) -> None:
        """Update the display based on current step."""
        email_input = self.query_one("#email_input", Input)
        question_label = self.query_one("#question_label", Label)
        answer_input = self.query_one("#answer_input", Input)
        new_password_label = self.query_one("#new_password_label", Label)
        new_password_input = self.query_one("#new_password_input", Input)
        confirm_password_label = self.query_one("#confirm_password_label", Label)
        confirm_password_input = self.query_one("#confirm_password_input", Input)
        continue_btn = self.query_one("#continue_btn", Button)
        
        if self.step == 1:
            # Show only email input
            email_input.disabled = False
            email_input.display = True
            
            # Hide other fields
            question_label.update("")
            question_label.display = False
            answer_input.disabled = True
            answer_input.display = False
            answer_input.placeholder = ""
            
            new_password_label.update("")
            new_password_label.display = False
            new_password_input.disabled = True
            new_password_input.display = False
            new_password_input.placeholder = ""
            
            confirm_password_label.update("")
            confirm_password_label.display = False
            confirm_password_input.disabled = True
            confirm_password_input.display = False
            confirm_password_input.placeholder = ""
            
            continue_btn.label = "Get Security Question"
            
        elif self.step == 2:
            # Show security question
            email_input.disabled = True
            
            question_label.update(f"Security Question:\n{self.security_question}")
            question_label.set_classes("security-question")
            question_label.display = True
            answer_input.disabled = False
            answer_input.display = True
            answer_input.placeholder = "Enter your security answer"
            
            # Hide password fields
            new_password_label.update("")
            new_password_label.display = False
            new_password_input.disabled = True
            new_password_input.display = False
            new_password_input.placeholder = ""
            
            confirm_password_label.update("")
            confirm_password_label.display = False
            confirm_password_input.disabled = True
            confirm_password_input.display = False
            confirm_password_input.placeholder = ""
            
            continue_btn.label = "Verify Answer"
            answer_input.focus()
            
        elif self.step == 3:
            # Show new password inputs
            email_input.disabled = True
            
            # Hide security question fields
            question_label.update("")
            question_label.display = False
            answer_input.disabled = True
            answer_input.display = False
            answer_input.placeholder = ""
            
            # Show password fields
            new_password_label.update("New Password:")
            new_password_label.display = True
            new_password_input.disabled = False
            new_password_input.display = True
            new_password_input.placeholder = "Enter your new password (min 6 characters)"
            
            confirm_password_label.update("Confirm New Password:")
            confirm_password_label.display = True
            confirm_password_input.disabled = False
            confirm_password_input.display = True
            confirm_password_input.placeholder = "Confirm your new password"
            
            continue_btn.label = "Reset Password"
            new_password_input.focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if self.is_loading:
            return
            
        if event.button.id == "continue_btn":
            await self.handle_continue()
        elif event.button.id == "back_btn":
            self.app.pop_screen()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in inputs."""
        if not event.input.disabled:
            await self.handle_continue()
    
    async def handle_continue(self) -> None:
        """Handle continue button based on current step."""
        if self.is_loading:
            return
            
        if self.step == 1:
            await self.handle_email_step()
        elif self.step == 2:
            await self.handle_security_step()
        elif self.step == 3:
            await self.handle_password_step()
    
    async def handle_email_step(self) -> None:
        """Handle email verification step."""
        email_input = self.query_one("#email_input", Input)
        message_widget = self.query_one("#message", Static)
        
        # Validate email
        email_valid = email_input.validate(email_input.value)
        if not email_valid.is_valid:
            message_widget.update("Please enter a valid email address")
            message_widget.set_classes("error")
            return
        
        # Show loading state
        self.is_loading = True
        message_widget.update("Looking up your security question...")
        message_widget.set_classes("loading")
        
        try:
            # Get user's security question
            result = await self.api_client.get_user_security_question(email_input.value)
            
            self.user_email = email_input.value
            self.security_question = result["question"]
            self.step = 2
            
            self.app.show_toast("✓ Security question found! Please answer it below.", severity="information")
            message_widget.update("")
            message_widget.set_classes("")
            
            self.update_step_display()
            
        except Exception as e:
            error_msg = "User not found or no security question set"
            if "network" in str(e).lower() or "connection" in str(e).lower():
                error_msg = "Unable to connect to server. Please try again later."
            
            message_widget.update(error_msg)
            message_widget.set_classes("error")
            
        finally:
            self.is_loading = False
    
    async def handle_security_step(self) -> None:
        """Handle security question verification step."""
        if self.is_loading:
            return
            
        answer_input = self.query_one("#answer_input", Input)
        message_widget = self.query_one("#message", Static)
        
        if not answer_input.value.strip():
            message_widget.update("Please enter your security answer")
            message_widget.set_classes("error")
            return
        
        # Show loading state
        self.is_loading = True
        message_widget.update("Verifying your answer...")
        message_widget.set_classes("loading")
        
        try:
            # Verify security answer
            await self.api_client.verify_security_answer(
                email=self.user_email,
                security_answer=answer_input.value
            )
            
            # Move to password step
            self.step = 3
            self.app.show_toast("✓ Answer accepted! Now set your new password.", severity="information")
            message_widget.update("")
            message_widget.set_classes("")
            
            self.update_step_display()
            
        except Exception as e:
            error_msg = "Incorrect security answer. Please try again."
            if "network" in str(e).lower() or "connection" in str(e).lower():
                error_msg = "Unable to connect to server. Please try again later."
            
            message_widget.update(error_msg)
            message_widget.set_classes("error")
            
        finally:
            self.is_loading = False
    
    async def handle_password_step(self) -> None:
        """Handle new password setting step."""
        answer_input = self.query_one("#answer_input", Input)
        new_password_input = self.query_one("#new_password_input", Input)
        confirm_password_input = self.query_one("#confirm_password_input", Input)
        message_widget = self.query_one("#message", Static)
        
        # Validate new password
        password_valid = new_password_input.validate(new_password_input.value)
        if not password_valid.is_valid:
            message_widget.update("Password must be at least 6 characters")
            message_widget.set_classes("error")
            return
        
        # Check password confirmation
        if new_password_input.value != confirm_password_input.value:
            message_widget.update("Passwords do not match")
            message_widget.set_classes("error")
            return
        
        # Show loading state
        self.is_loading = True
        message_widget.update("Resetting your password...")
        message_widget.set_classes("loading")
        
        try:
            # Reset password
            await self.api_client.reset_password(
                email=self.user_email,
                security_answer=answer_input.value,
                new_password=new_password_input.value
            )
            
            # Success - show toast and return to login
            self.app.show_toast("🔐 Password reset successfully! You can now log in with your new password.", severity="information")
            message_widget.update("")
            message_widget.set_classes("")
            
            # Return to login after a brief moment
            self.set_timer(1.5, lambda: self.app.pop_screen())
            
        except Exception as e:
            error_msg = "Password reset failed. Please check your security answer and try again."
            error_str = str(e).lower()
            
            if "incorrect security answer" in error_str:
                error_msg = "Incorrect security answer. Please try again."
            elif "network" in error_str or "connection" in error_str:
                error_msg = "Unable to connect to server. Please try again later."
            
            message_widget.update(error_msg)
            message_widget.set_classes("error")
            
        finally:
            self.is_loading = False