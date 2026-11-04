# main.py
import sys
import os
import argparse
import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from config import AppConfig
from ui.main_window import GuildWarsTracker

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # High-DPI display scaling configuration
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Chromium WebEngine configuration flags
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--enable-features=UseZoomForDSF,HighDpiSupport "
        "--high-dpi-support=1 "
        "--force-color-profile=srgb "
        "--enable-font-antialiasing "
        "--disable-gpu-shader-disk-cache "
        "--js-flags=--max-old-space-size=256 "
        "--disable-renderer-backgrounding "
        "--disk-cache-size=104857600 "
        "--media-cache-size=20971520"
    )

    parser = argparse.ArgumentParser(description=AppConfig.APP_TITLE)
    parser.add_argument("--profile", type=str, help="Name of the profile to load on startup")
    parser.add_argument("--auto-close", action="store_true", help="Close application when Guild Wars exits")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    tracker_window = GuildWarsTracker(profile_name=args.profile, auto_close=args.auto_close)
    tracker_window.show()
    sys.exit(app.exec())
