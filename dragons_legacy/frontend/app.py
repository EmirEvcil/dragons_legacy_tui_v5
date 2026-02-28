"""
Main Textual application for Legend of Dragon's Legacy
"""

from textual.app import App
from textual.driver import Driver

from dragons_legacy.frontend.api_client import APIClient
from dragons_legacy.frontend.styles import MAIN_CSS
from dragons_legacy.frontend.screens import (
    LoginScreen,
    RegistrationScreen,
    ForgotPasswordScreen,
    CharacterCreationScreen,
    GameScreen
)


class DragonsLegacyApp(App):
    """Main application for Legend of Dragon's Legacy."""
    
    CSS = MAIN_CSS
    TITLE = "Legend of Dragon's Legacy"
    
    def __init__(self, driver_class: Driver = None, css_path: str = None, watch_css: bool = False):
        super().__init__(driver_class, css_path, watch_css)
        self.api_client = APIClient()
        self.user_email = None
        
    def show_toast(self, message: str, severity: str = "information"):
        """Show a toast notification."""
        self.notify(message, severity=severity)
        
    def on_mount(self) -> None:
        """Initialize the application."""
        # Install all screens
        self.install_screen(LoginScreen(self.api_client), name="login")
        self.install_screen(RegistrationScreen(self.api_client), name="registration")
        self.install_screen(ForgotPasswordScreen(self.api_client), name="forgot_password")
        self.install_screen(CharacterCreationScreen(self.api_client), name="character_creation")
        self.install_screen(GameScreen(self.api_client), name="game")
        
        # Start with login screen
        self.push_screen("login")


def main():
    """Main entry point for the application."""
    app = DragonsLegacyApp()
    app.run()


if __name__ == "__main__":
    main()