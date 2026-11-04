# ui/main_window.py
import os
import sys
import logging
import subprocess
import threading
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

from database import DataManager
from scraper import DatabaseSyncer
from config import AppConfig
from .backend_bridge import BackendBridge


class GuildWarsTracker(QMainWindow):
    game_exited_signal = Signal()

    def __init__(self, profile_name=None, auto_close=False):
        super().__init__()
        self.setWindowTitle(f"{AppConfig.APP_TITLE} v{AppConfig.APP_VERSION}")
        self.resize(AppConfig.WINDOW_WIDTH, AppConfig.WINDOW_HEIGHT)
        self.setMinimumSize(1180, 760)

        # App Icon
        icon_path = self._get_asset_path("GW_Icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.data = DataManager()
        self.syncer = DatabaseSyncer()
        self.bridge = BackendBridge(self.data, self.syncer, self)
        self._checking_game = False

        self.game_exited_signal.connect(self.close)

        # Game Auto-Close Timer (Non-blocking)
        self.game_check_timer = QTimer(self)
        self.game_check_timer.timeout.connect(self.check_game_running)
        saved_auto_close = self.data.get_preferences().get("auto_close", False)
        if auto_close or saved_auto_close:
            self.game_check_timer.start(AppConfig.AUTO_CLOSE_CHECK_INTERVAL_MS)

        self._setup_web_ui()

        if profile_name and profile_name in self.data.get_profiles():
            self.data.switch_profile(profile_name)

    def set_auto_close_enabled(self, enabled):
        if enabled:
            if not self.game_check_timer.isActive():
                self.game_check_timer.start(AppConfig.AUTO_CLOSE_CHECK_INTERVAL_MS)
        else:
            if self.game_check_timer.isActive():
                self.game_check_timer.stop()

    def _get_asset_path(self, relative_path):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
            path = os.path.join(base_dir, relative_path)
            if os.path.exists(path):
                return path
        return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path))

    def _get_html_path(self):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(sys.executable)))
            candidates = [
                os.path.join(base_dir, 'ui', 'web', 'index.html'),
                os.path.join(base_dir, 'web', 'index.html'),
                os.path.join(base_dir, 'index.html')
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c
        return os.path.abspath(os.path.join(os.path.dirname(__file__), 'web', 'index.html'))

    def _setup_web_ui(self):
        self.web_view = QWebEngineView(self)
        self.web_view.page().setBackgroundColor(QColor("#0C0D11"))

        # Configure WebEngine Settings for smooth rendering and local channels
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

        # QWebChannel setup
        self.channel = QWebChannel(self)
        self.channel.registerObject("pyBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Set central widget
        self.setCentralWidget(self.web_view)

        # Optimize memory allocation for WebEngine profile (cap HTTP cache at 50MB)
        try:
            self.web_view.page().profile().setHttpCacheMaximumSize(50 * 1024 * 1024)
        except Exception as e:
            logging.debug(f"Note setting http cache size: {e}")

        html_file = self._get_html_path()
        logging.info(f"Loading HTML5 UI from: {html_file}")
        self.web_view.setUrl(QUrl.fromLocalFile(html_file))

    def check_game_running(self):
        if self._checking_game:
            return
        self._checking_game = True

        def _worker():
            try:
                creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                res = subprocess.run(
                    ['tasklist', '/NH'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=creation_flags
                )
                tasks = res.stdout or ""
                running = any(proc.lower() in tasks.lower() for proc in AppConfig.GAME_PROCESS_NAMES)
                if not running:
                    logging.info("Game process not found. Closing application.")
                    self.game_exited_signal.emit()
            except Exception as e:
                logging.error(f"Error checking game process: {e}")
            finally:
                self._checking_game = False

        threading.Thread(target=_worker, daemon=True).start()

    def showEvent(self, event):
        super().showEvent(event)
        self._bind_screen_listener()

    def moveEvent(self, event):
        super().moveEvent(event)
        # Dynamically detect cross-monitor window movements (1080p, 1440p, 4K)
        screen = self.screen()
        if screen:
            self._handle_screen_change(screen)

    def _bind_screen_listener(self):
        handle = self.windowHandle()
        if handle:
            try:
                handle.screenChanged.connect(self._handle_screen_change)
            except Exception as e:
                logging.debug(f"Note binding screenChanged: {e}")
            self._handle_screen_change(handle.screen())

    def _handle_screen_change(self, screen):
        if not screen:
            return
        geo = screen.geometry()
        dpr = screen.devicePixelRatio()
        dpi = screen.logicalDotsPerInch()

        if geo.width() >= 3800 or geo.height() >= 2100:
            category = "4k"
        elif geo.width() >= 2500 or geo.height() >= 1400:
            category = "1440p"
        else:
            category = "1080p"

        js = f"""
        if (typeof window.onDisplayMetricsChanged === 'function') {{
            window.onDisplayMetricsChanged({{
                width: {geo.width()},
                height: {geo.height()},
                dpr: {dpr},
                dpi: {dpi},
                category: '{category}'
            }});
        }}
        """
        try:
            self.web_view.page().runJavaScript(js)
        except Exception:
            pass

    def closeEvent(self, event):
        if self.game_check_timer.isActive():
            self.game_check_timer.stop()
        if self.syncer.isRunning():
            self.syncer.requestInterruption()
            self.syncer.quit()
            self.syncer.wait()
        try:
            self.web_view.page().profile().clearHttpCache()
        except Exception as e:
            logging.error(f"Failed to clear WebEngine cache on close: {e}")
        event.accept()
