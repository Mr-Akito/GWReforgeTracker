# updater.py
import os
import requests
import tempfile
import logging
from PySide6.QtCore import QThread, Signal
from config import AppConfig

class UpdateChecker(QThread):
    """
    Checks for updates against the GitHub API without freezing the UI.
    Returns: (has_update, download_url, tag_name, error_message)
    """
    result_ready = Signal(bool, str, str, str)

    def run(self):
        try:
            # Fetch latest release data
            response = requests.get(
                AppConfig.GITHUB_API_LATEST, 
                timeout=AppConfig.REQUEST_TIMEOUT,
                headers={'User-Agent': AppConfig.USER_AGENT}
            )
            
            if response.status_code != 200:
                self.result_ready.emit(False, "", "", f"GitHub API Error: {response.status_code}")
                return

            data = response.json()
            latest_tag = data.get("tag_name", "").strip().lstrip("v")
            current_ver = AppConfig.APP_VERSION.strip().lstrip("v")
            
            # Compare release versions
            if self._is_newer(latest_tag, current_ver):
                assets = data.get("assets", [])
                download_url = ""
                for asset in assets:
                    if asset["name"].endswith(".exe"):
                        download_url = asset["browser_download_url"]
                        break
                
                if download_url:
                    self.result_ready.emit(True, download_url, f"v{latest_tag}", "")
                else:
                    self.result_ready.emit(False, "", "", "No executable found in release.")
            else:
                self.result_ready.emit(False, "", "", "")

        except requests.RequestException as e:
            self.result_ready.emit(False, "", "", "Network unreachable.")
        except Exception as e:
            logging.error(f"Update Check Failed: {e}")
            self.result_ready.emit(False, "", "", str(e))

    def _is_newer(self, remote_ver, local_ver):
        try:
            r_parts = [int(x) for x in remote_ver.split(".")]
            l_parts = [int(x) for x in local_ver.split(".")]
            return r_parts > l_parts
        except ValueError:
            return False

class UpdateDownloader(QThread):
    """
    Downloads the update file in chunks to ensure the UI remains responsive
    and provides smooth progress bar updates.
    """
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._is_cancelled = False

    def requestInterruption(self):
        self._is_cancelled = True
        super().requestInterruption()

    def run(self):
        try:
            with requests.get(self.url, stream=True, timeout=30, headers={'User-Agent': AppConfig.USER_AGENT}) as r:
                r.raise_for_status()
                
                total_length = r.headers.get('content-length')
                
                fd, save_path = tempfile.mkstemp(suffix=".exe")
                os.close(fd)

                with open(save_path, 'wb') as f:
                    if total_length is None:
                        f.write(r.content)
                        self.progress.emit(100)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for chunk in r.iter_content(chunk_size=8192):
                            if self._is_cancelled:
                                f.close()
                                os.remove(save_path)
                                return
                            
                            if chunk:
                                dl += len(chunk)
                                f.write(chunk)
                                percent = int(100 * dl / total_length)
                                self.progress.emit(percent)

            if not self._is_cancelled:
                self.finished.emit(save_path)

        except Exception as e:
            logging.error(f"Download Error: {e}")
            self.error.emit(str(e))