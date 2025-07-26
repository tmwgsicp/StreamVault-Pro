import os
import time

import flet as ft

from . import InstallationManager, execute_dir
from .core.config_manager import ConfigManager
from .core.language_manager import LanguageManager
from .core.record_manager import RecordingManager
from .core.update_checker import UpdateChecker
from .process_manager import AsyncProcessManager
from .ui.components.recording_card import RecordingCardManager
from .ui.components.show_snackbar import ShowSnackBar
from .ui.navigation.sidebar import LeftNavigationMenu, NavigationSidebar
from .ui.views.about_view import AboutPage
from .ui.views.home_view import HomePage
from .ui.views.settings_view import SettingsPage
from .ui.views.storage_view import StoragePage
from .ui.views.transcripts_view import TranscriptsPage
from .ui.views.license_view import LicenseView
from .utils import utils
from .utils.logger import logger


class App:
    def __init__(self, page: ft.Page, is_web: bool = False):
        self.install_progress = None
        self.page = page
        self.is_web = is_web
        self.run_path = execute_dir
        self.assets_dir = os.path.join(execute_dir, "assets")
        self.process_manager = AsyncProcessManager()
        self.config_manager = ConfigManager(self.run_path)
        self.content_area = ft.Column(
            controls=[],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        self.settings = SettingsPage(self)
        self.language_manager = LanguageManager(self)
        self.about = AboutPage(self)
        self.home = HomePage(self)
        self.pages = self.initialize_pages()
        self.language_code = self.settings.language_code
        self.sidebar = NavigationSidebar(self)
        self.left_navigation_menu = LeftNavigationMenu(self)

        self.page.snack_bar_area = ft.Container()
        self.dialog_area = ft.Container()
        self.complete_page = ft.Row(
            expand=True,
            controls=[
                self.left_navigation_menu,
                ft.VerticalDivider(width=1),
                self.content_area,
                self.dialog_area,
                self.page.snack_bar_area,
            ]
        )
        self.page.add(self.complete_page)
        self.snack_bar = ShowSnackBar(self.page)
        self.subprocess_start_up_info = utils.get_startup_info()
        self.record_card_manager = RecordingCardManager(self)
        self.record_manager = RecordingManager(self)
        self.current_page = None
        self._loading_page = False
        self.recording_enabled = True
        self.install_manager = InstallationManager(self)
        self.update_checker = UpdateChecker(self)
        self.page.run_task(self.install_manager.check_env)
        self.page.run_task(self.record_manager.check_free_space)
        self.page.run_task(self._check_for_updates)

    def initialize_pages(self):
        return {
            "settings": self.settings,
            "home": HomePage(self),
            "storage": StoragePage(self),
            "transcripts": TranscriptsPage(self),
            "license": LicenseView(self),
            "about": AboutPage(self),
        }

    async def switch_page(self, page_name):
        if self._loading_page:
            return

        self._loading_page = True

        try:
            await self.clear_content_area()
            if page := self.pages.get(page_name):
                await self.settings.is_changed()
                self.current_page = page
                await page.load()
        except Exception as e:
            logger.error(f"Error switching to page {page_name}: {e}")
        finally:
            self._loading_page = False

    async def clear_content_area(self):
        self.content_area.clean()
        self.content_area.update()

    async def cleanup(self):
        try:
            await self.process_manager.cleanup()
        except ConnectionError:
            logger.warning("Connection lost, process may have terminated")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def add_ffmpeg_process(self, process):
        self.process_manager.add_process(process)

    async def _check_for_updates(self):
        """Check for updates when the application starts"""
        try:
            if not self.update_checker.update_config["auto_check"]:
                return
                
            last_check_time = self.settings.default_config.get("last_update_check", 0)
            current_time = time.time()
            check_interval = self.update_checker.update_config["check_interval"]
            
            if current_time - last_check_time >= check_interval:
                update_info = await self.update_checker.check_for_updates()
                self.settings.default_config["last_update_check"] = current_time
                await self.config_manager.save_user_config(self.settings.default_config)

                if update_info.get("has_update", False):
                    await self.update_checker.show_update_dialog(update_info)
        except Exception as e:
            logger.error(f"Update check failed: {e}")
