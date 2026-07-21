# Automation module
from app.automation.app_control import AppController
from app.automation.browser import BrowserController
from app.automation.system import SystemController
from app.automation.utilities import UtilityController
from app.automation.file_manager import FileManager
from app.automation.email_service import EmailController
from app.automation.media import MediaController
from app.automation.productivity import ProductivityManager
from app.automation.workflows import WorkflowEngine

__all__ = [
    "AppController",
    "BrowserController",
    "SystemController",
    "UtilityController",
    "FileManager",
    "EmailController",
    "MediaController",
    "ProductivityManager",
    "WorkflowEngine",
]
