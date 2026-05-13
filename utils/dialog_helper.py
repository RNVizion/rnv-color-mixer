"""
Consistent dialog interface for the RNV Color Mixer.

Standardizes QMessageBox calls across the application with a small set of
helpers (show_error, show_warning, show_info, show_question, and
show_about) so every dialog has the same style, icon set, and button
layout regardless of which module raises it.

Usage Examples:
    # Show error
    DialogHelper.show_error(self, "Failed to load file!")
    
    # Show warning
    DialogHelper.show_warning(self, "Color values out of range")
    
    # Show info
    DialogHelper.show_info(self, "Settings saved successfully")
    
    # Confirm action
    if DialogHelper.confirm(self, "Delete this color?"):
        delete_color()
    
    # Ask yes/no/cancel
    result = DialogHelper.ask_yes_no_cancel(self, "Save changes?")
    if result == DialogResult.YES:
        save()
"""

from PyQt6.QtWidgets import QMessageBox, QWidget
from enum import Enum

# Import logger
try:
    from utils.logger import Logger
    logger = Logger("DialogHelper")
except ImportError:
    logger = None


class DialogResult(Enum):
    """Dialog result options."""
    YES = 1
    NO = 2
    CANCEL = 3
    OK = 4


class DialogHelper:
    """
    Centralized dialog management for consistent UX.
    
    Benefits:
    - Consistent styling across all dialogs
    - Theme-aware dialogs
    - Less code duplication
    - Single point to customize all dialogs
    """
    
    # Default window titles
    DEFAULT_ERROR_TITLE = "Error"
    DEFAULT_WARNING_TITLE = "Warning"
    DEFAULT_INFO_TITLE = "Information"
    DEFAULT_CONFIRM_TITLE = "Confirm"
    
    # Theme support (can be customized)
    USE_THEMED_DIALOGS = True
    
    @staticmethod
    def show_error(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show error dialog.
        
        Args:
            parent: Parent widget
            message: Error message to display
            title: Optional custom title (default: "Error")
            detailed_text: Optional detailed error info
        
        Example:
            DialogHelper.show_error(self, "Failed to load image!")
            DialogHelper.show_error(self, "File not found", detailed_text=str(exception))
        """
        title = title or DialogHelper.DEFAULT_ERROR_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_warning(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show warning dialog.
        
        Args:
            parent: Parent widget
            message: Warning message to display
            title: Optional custom title (default: "Warning")
            detailed_text: Optional detailed warning info
        
        Example:
            DialogHelper.show_warning(self, "Color values will be clamped to 0-255")
        """
        title = title or DialogHelper.DEFAULT_WARNING_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def show_info(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        detailed_text: str | None = None
    ) -> None:
        """
        Show information dialog.
        
        Args:
            parent: Parent widget
            message: Information message to display
            title: Optional custom title (default: "Information")
            detailed_text: Optional detailed info
        
        Example:
            DialogHelper.show_info(self, "Settings saved successfully!")
        """
        title = title or DialogHelper.DEFAULT_INFO_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    @staticmethod
    def confirm(
        parent: QWidget | None,
        message: str,
        title: str | None = None,
        default_yes: bool = False
    ) -> bool:
        """
        Show yes/no confirmation dialog.
        
        Args:
            parent: Parent widget
            message: Question to ask
            title: Optional custom title (default: "Confirm")
            default_yes: If True, Yes is default button
        
        Returns:
            True if user clicked Yes, False if No
        
        Example:
            if DialogHelper.confirm(self, "Delete this color?"):
                delete_color()
        """
        title = title or DialogHelper.DEFAULT_CONFIRM_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if default_yes:
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        else:
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def ask_yes_no_cancel(
        parent: QWidget | None,
        message: str,
        title: str | None = None
    ) -> DialogResult:
        """
        Show yes/no/cancel dialog.
        
        Args:
            parent: Parent widget
            message: Question to ask
            title: Optional custom title (default: "Confirm")
        
        Returns:
            DialogResult.YES, DialogResult.NO, or DialogResult.CANCEL
        
        Example:
            result = DialogHelper.ask_yes_no_cancel(self, "Save changes before closing?")
            if result == DialogResult.YES:
                save_and_close()
            elif result == DialogResult.NO:
                close_without_saving()
            # CANCEL = do nothing
        """
        title = title or DialogHelper.DEFAULT_CONFIRM_TITLE
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No | 
            QMessageBox.StandardButton.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        
        result = msg_box.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            return DialogResult.YES
        elif result == QMessageBox.StandardButton.No:
            return DialogResult.NO
        else:
            return DialogResult.CANCEL
    
    @staticmethod
    def show_about(
        parent: QWidget | None,
        app_name: str,
        version: str,
        description: str,
        copyright_info: str | None = None
    ) -> None:
        """
        Show about dialog.
        
        Args:
            parent: Parent widget
            app_name: Application name
            version: Version string
            description: Application description
            copyright_info: Optional copyright information
        
        Example:
            DialogHelper.show_about(
                self,
                "Color Mixer",
                "2.6",
                "Professional color mixing application",
                "© 2026 Your Name"
            )
        """
        # Use list join instead of string concatenation
        parts = [
            f"<h2>{app_name}</h2>",
            f"<p><b>Version:</b> {version}</p>",
            f"<p>{description}</p>"
        ]
        
        if copyright_info:
            parts.append(f"<p><i>{copyright_info}</i></p>")
        
        message = "".join(parts)
        QMessageBox.about(parent, f"About {app_name}", message)
    
    @staticmethod
    def show_custom(
        parent: QWidget | None,
        title: str,
        message: str,
        icon: QMessageBox.Icon = QMessageBox.Icon.Information,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        default_button: QMessageBox.StandardButton | None = None,
        detailed_text: str | None = None
    ) -> QMessageBox.StandardButton:
        """
        Show custom dialog with full control.
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            icon: Icon type
            buttons: Button combination
            default_button: Default button
            detailed_text: Optional detailed info
        
        Returns:
            The button that was clicked
        
        Example:
            result = DialogHelper.show_custom(
                self,
                "Custom Dialog",
                "Choose an option",
                icon=QMessageBox.Icon.Question,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(buttons)
        
        if default_button:
            msg_box.setDefaultButton(default_button)
        
        if detailed_text:
            msg_box.setDetailedText(detailed_text)
        
        return msg_box.exec()


# Convenience aliases for shorter code
def error(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_error()"""
    DialogHelper.show_error(parent, message, title)

def warning(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_warning()"""
    DialogHelper.show_warning(parent, message, title)

def info(parent: QWidget | None, message: str, title: str | None = None) -> None:
    """Shorthand for DialogHelper.show_info()"""
    DialogHelper.show_info(parent, message, title)

def confirm(parent: QWidget | None, message: str, title: str | None = None) -> bool:
    """Shorthand for DialogHelper.confirm()"""
    return DialogHelper.confirm(parent, message, title)


# Example usage patterns
"""
USAGE EXAMPLES:

1. SIMPLE ERROR:
   DialogHelper.show_error(self, "Failed to load file!")
   
2. ERROR WITH DETAILS:
   try:
       load_file()
   except Exception as e:
       DialogHelper.show_error(
           self,
           "Failed to load file",
           detailed_text=str(e)
       )

3. WARNING:
   DialogHelper.show_warning(self, "Color values out of range")

4. SUCCESS MESSAGE:
   DialogHelper.show_info(self, "Settings saved successfully!")

5. YES/NO CONFIRMATION:
   if DialogHelper.confirm(self, "Delete this color?"):
       delete_color()

6. YES/NO/CANCEL:
   result = DialogHelper.ask_yes_no_cancel(self, "Save changes?")
   if result == DialogResult.YES:
       save()
   elif result == DialogResult.NO:
       pass  # Don't save
   # DialogResult.CANCEL = do nothing

7. SHORTHAND (imported at top):
   from dialog_helper import error, warning, info, confirm
   
   error(self, "Something went wrong!")
   warning(self, "Be careful!")
   info(self, "All done!")
   if confirm(self, "Continue?"):
       proceed()

8. ABOUT DIALOG:
   DialogHelper.show_about(
       self,
       "Color Mixer",
       "2.6",
       "Professional color mixing",
       "© 2026"
   )
"""