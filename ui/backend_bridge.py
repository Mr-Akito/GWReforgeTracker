# ui/backend_bridge.py
import json
import logging
import re
import socket
import threading
import uuid
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
import requests
from bs4 import BeautifulSoup
from PySide6.QtCore import QObject, Slot, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from config import AppConfig, QuestStatus, ColorSchemeMode, Professions, MUTUALLY_EXCLUSIVE_QUESTS


class BackendBridge(QObject):
    data_changed = Signal(str)
    quest_status_updated = Signal(str)
    preferences_updated = Signal(str)
    sync_progress = Signal(int, str)
    sync_finished = Signal(bool, str)
    wiki_content_ready = Signal(str, str, str)  # (title, clean_html, url)
    update_check_result = Signal(str)           # JSON string with update check result
    export_progression_ready = Signal(str)      # JSON string of exported data
    import_progression_finished = Signal(bool, str)

    def __init__(self, data_manager, syncer, parent=None):
        super().__init__(parent)
        self.data = data_manager
        self.syncer = syncer
        self.main_window = parent
        self.companion_port = 8848
        self.companion_room = f"GW-{str(uuid.uuid4())[:4].upper()}"
        if self.syncer is not None:
            self.syncer.progress_updated.connect(lambda p, m: self.sync_progress.emit(p, m))
            self.syncer.sync_finished.connect(self._on_sync_done)
        self._start_companion_server()

    def get_full_state_dict(self):
        current_prof = self.data.get_profile_profession()
        prefs = self.data.get_preferences()
        return {
            "current_profile": self.data.current_profile_name,
            "profiles": self.data.get_profiles(),
            "profession": current_prof,
            "color_scheme": prefs["color_scheme"],
            "dark_mode": prefs["dark_mode"],
            "preferences": prefs,
            "is_first_run": self.data.is_first_run(),
            "quest_db": self.data.quest_db,
            "quest_meta": self.data.quest_metadata,
            "quest_status": self.data.get_current_quests(),
            "locked_quests": list(self.data.get_locked_quests())
        }

    def emit_state_update(self):
        state_json = json.dumps(self.get_full_state_dict())
        self.data_changed.emit(state_json)

    def emit_quest_status_delta(self, quest_name=""):
        payload = {
            "quest_name": quest_name,
            "quest_status": self.data.get_current_quests(),
            "locked_quests": list(self.data.get_locked_quests())
        }
        self.quest_status_updated.emit(json.dumps(payload))

    @Slot()
    def request_initial_data(self):
        self.emit_state_update()

    @Slot()
    def complete_first_run(self):
        self.data.complete_first_run()

    @Slot(str, int)
    def set_quest_status(self, quest_name, status):
        self.data.set_status(quest_name, status)
        self.emit_quest_status_delta(quest_name)

    @Slot(str, bool)
    def set_quest_hidden(self, quest_name, is_hidden):
        self.data.set_quest_hidden(quest_name, is_hidden)
        self.emit_quest_status_delta(quest_name)

    @Slot()
    def unhide_all_quests(self):
        self.data.unhide_all_quests()
        self.emit_quest_status_delta("")

    @Slot(str)
    def switch_profile(self, profile_name):
        self.data.switch_profile(profile_name)
        self.emit_state_update()

    @Slot(str, str)
    def create_profile(self, profile_name, profession):
        if self.data.create_profile(profile_name, profession):
            self.emit_state_update()

    @Slot(str, str, str)
    def rename_profile(self, old_name, new_name, profession):
        if self.data.rename_profile(old_name, new_name, profession):
            self.emit_state_update()

    @Slot(str)
    def set_profile_profession(self, profession):
        self.data.set_profile_profession(profession)
        self.emit_state_update()

    @Slot(str)
    def delete_profile(self, profile_name):
        if self.data.delete_profile(profile_name):
            self.emit_state_update()

    @Slot(str, bool, bool)
    def save_settings(self, color_scheme, dark_mode, show_hidden):
        prefs = self.data.get_preferences()
        prefs["color_scheme"] = color_scheme
        prefs["dark_mode"] = dark_mode
        prefs["show_hidden"] = show_hidden
        self.data.save_preferences(prefs)
        self.preferences_updated.emit(json.dumps(prefs))

    @Slot(str)
    def save_preferences_json(self, prefs_json):
        try:
            new_prefs = json.loads(prefs_json)
            self.data.save_preferences(new_prefs)
            saved_prefs = self.data.get_preferences()
            if self.main_window and hasattr(self.main_window, "set_auto_close_enabled"):
                self.main_window.set_auto_close_enabled(saved_prefs.get("auto_close", False))
            self.preferences_updated.emit(json.dumps(saved_prefs))
        except Exception as e:
            logging.error(f"Error saving preferences JSON: {e}")

    @Slot(bool)
    def set_theme(self, is_dark):
        self.data.set_theme(is_dark)
        prefs = self.data.get_preferences()
        self.preferences_updated.emit(json.dumps(prefs))

    @Slot(bool)
    def set_auto_close(self, enabled):
        prefs = self.data.get_preferences()
        prefs["auto_close"] = bool(enabled)
        self.data.save_preferences(prefs)
        if self.main_window and hasattr(self.main_window, "set_auto_close_enabled"):
            self.main_window.set_auto_close_enabled(bool(enabled))
        self.preferences_updated.emit(json.dumps(prefs))

    @Slot()
    def clear_wiki_cache(self):
        self.data.clear_wiki_cache()

    @Slot(str)
    def reset_campaign(self, campaign_name):
        self.data.reset_campaign(campaign_name)
        self.emit_quest_status_delta("")

    @Slot()
    def start_sync(self):
        if self.syncer.isRunning():
            return
        self.syncer.set_current_data(self.data.quest_db, self.data.quest_metadata)
        self.syncer.start()

    def _on_sync_done(self, new_db, new_meta, errors):
        if new_db:
            self.data.update_quest_db(new_db, new_meta)
            self.emit_state_update()
            if errors:
                self.sync_finished.emit(True, "Sync finished with warnings (offline data preserved).")
            else:
                self.sync_finished.emit(True, "Sync complete! Quest database successfully updated.")
        else:
            self.sync_finished.emit(False, "Sync could not reach the wiki. Offline data preserved.")

    @Slot(str)
    def request_wiki_html(self, quest_name):
        url = self.data.get_wiki_url(quest_name)
        self.request_wiki_page(url, quest_name)

    @Slot(str, str)
    def request_wiki_page(self, url_or_target, page_title=""):
        if not url_or_target:
            return

        # Resolve URL and Title
        if url_or_target.startswith('http://') or url_or_target.startswith('https://'):
            url = url_or_target
            title = page_title or unquote(url.split('/')[-1]).replace('_', ' ')
        elif url_or_target.startswith('/wiki/'):
            url = f"https://wiki.guildwars.com{url_or_target}"
            title = page_title or unquote(url_or_target.replace('/wiki/', '')).replace('_', ' ')
        else:
            # It's a quest name
            url = self.data.get_wiki_url(url_or_target)
            title = url_or_target

        # Check resilient disk cache first
        cached_html = self.data.get_cached_content(url)
        if cached_html:
            clean = self._clean_wiki_html(cached_html, title, is_cached=True)
            self.wiki_content_ready.emit(title, clean, url)
            return

        # Fetch in background daemon thread
        def _fetch_worker():
            try:
                r = requests.get(
                    url,
                    headers={'User-Agent': AppConfig.USER_AGENT},
                    timeout=AppConfig.REQUEST_TIMEOUT
                )
                if r.status_code == 200 and r.text:
                    self.data.cache.set(url, r.text)
                    clean_html = self._clean_wiki_html(r.text, title)
                    self.wiki_content_ready.emit(title, clean_html, url)
                else:
                    # Check stale cache on HTTP error
                    stale = self.data.cache.get(url, allow_stale=True)
                    if stale:
                        clean_html = self._clean_wiki_html(stale, title, is_offline_fallback=True)
                    elif title in self.data.quest_metadata:
                        clean_html = self._get_offline_quest_card(title)
                    else:
                        clean_html = self._get_offline_article_card(title, url)
                    self.wiki_content_ready.emit(title, clean_html, url)
            except Exception as e:
                logging.warning(f"Failed to fetch wiki page '{title}' ({url}): {e}")
                stale = self.data.cache.get(url, allow_stale=True)
                if stale:
                    clean_html = self._clean_wiki_html(stale, title, is_offline_fallback=True)
                elif title in self.data.quest_metadata:
                    clean_html = self._get_offline_quest_card(title)
                else:
                    clean_html = self._get_offline_article_card(title, url)
                self.wiki_content_ready.emit(title, clean_html, url)

        threading.Thread(target=_fetch_worker, daemon=True).start()

    def _clean_wiki_html(self, raw_html, page_title, is_cached=False, is_offline_fallback=False):
        try:
            soup = BeautifulSoup(raw_html, 'html.parser')
            # Remove scripts, styles, navbars, footers, search, notices, edit links
            for selector in [
                'script', 'style', 'noscript', '#mw-navigation', '#footer',
                '.mw-editsection', '#siteNotice', '#column-one', '#p-personal',
                '#p-logo', '#p-search', '#catlinks', '.magnify', '.printfooter',
                '#toc', '.toc', '.patrollink'
            ]:
                for tag in soup.select(selector):
                    tag.decompose()

            content = soup.find('div', {'id': 'mw-content-text'}) or soup.find('div', {'id': 'bodyContent'})
            if content:
                # Strip inline color/background/opacity styles that impair legibility
                style_strip_re = re.compile(
                    r'(^|;)\s*(background(-color|-image)?|color|opacity|border(-color)?|text-shadow)\s*:[^;]+',
                    re.IGNORECASE
                )
                for tag in content.find_all(True):
                    for attr in ['bgcolor', 'color', 'text', 'link', 'vlink', 'alink']:
                        if tag.has_attr(attr):
                            del tag[attr]
                    if tag.has_attr('style'):
                        cleaned_style = style_strip_re.sub('', tag['style']).strip(' ;')
                        if cleaned_style:
                            tag['style'] = cleaned_style
                        else:
                            del tag['style']
                    if tag.name == 'img':
                        src = tag.get('src', '')
                        if src.startswith('//'):
                            tag['src'] = 'https:' + src
                        elif src.startswith('/'):
                            tag['src'] = 'https://wiki.guildwars.com' + src
                        if tag.has_attr('srcset'):
                            del tag['srcset']

                result_html = str(content)
                if is_offline_fallback:
                    result_html = f"""
                    <div class="wiki-offline-notice">
                        <span class="notice-icon">📡</span>
                        <span>Displaying offline cached version of <strong>{page_title}</strong> (Wiki server currently unreachable).</span>
                    </div>
                    {result_html}
                    """
                return result_html
        except Exception as e:
            logging.error(f"Error cleaning wiki html for {page_title}: {e}")
        return self._get_offline_quest_card(page_title)

    def _get_offline_quest_card(self, quest_name):
        meta = self.data.quest_metadata.get(quest_name, {})
        prof = meta.get("profession", "") or "Available to all professions"
        loc = meta.get("location", "") or "Tyria"
        camp = meta.get("campaign", "") or "Guild Wars"
        return f"""
        <div class="wiki-offline-card">
            <h2>{quest_name}</h2>
            <p><strong>Campaign:</strong> {camp}</p>
            <p><strong>Location:</strong> {loc}</p>
            <p><strong>Profession Requirement:</strong> {prof}</p>
            <hr>
            <h3>Walkthrough &amp; Tactical Briefing</h3>
            <p>This quest entry is stored in the local master database. Full live walkthrough details, NPC dialogue, and maps will cache automatically once connection to the Guild Wars Wiki is re-established.</p>
        </div>
        """

    def _get_offline_article_card(self, title, url):
        return f"""
        <div class="wiki-offline-card">
            <h2>{title}</h2>
            <div class="wiki-offline-notice">
                <span class="notice-icon">⚠️</span>
                <span>This article was not previously cached in your local database, and the Guild Wars Wiki could not be reached.</span>
            </div>
            <p>Target URL: <a href="{url}">{url}</a></p>
            <p>Once your network connection is available or the Wiki server returns online, clicking reload will fetch and store this article in your persistent offline cache.</p>
        </div>
        """

    @Slot(str)
    def open_external_url(self, url):
        QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def export_progression(self):
        data_json = self.data.export_progression_json()
        if data_json:
            self.export_progression_ready.emit(data_json)

    @Slot(str)
    def import_progression(self, json_str):
        if not json_str:
            self.import_progression_finished.emit(False, "Empty progression data provided.")
            return
        success = self.data.import_progression_json(json_str)
        if success:
            self.emit_state_update()
            self.import_progression_finished.emit(True, "Progression data imported successfully!")
        else:
            self.import_progression_finished.emit(False, "Failed to parse or import progression data.")

    @Slot()
    def check_for_updates(self):
        def _worker():
            fallback_releases = [
                {
                    "tag_name": "v1.0.3",
                    "name": "Guild Wars Reforge Quest Tracker v1.0.3",
                    "published_at": "2026-11-02",
                    "body": "### Version 1.0.3 Overhaul\n- Mutually exclusive quest locking with visual grayscale.\n- Configurable yellow/green status palette option.\n- All Campaigns unified view and progress calculation.\n- Class and profession-based quest filtering.\n- In-app Wiki browser with complete backward/forward history.\n- Resilient 30-day offline walkthrough caching.\n- Windows HighDPI PassThrough display scaling.\n- Memory and Low GPU mode optimizations."
                },
                {
                    "tag_name": "v1.0.2",
                    "name": "Guild Wars Reforge Quest Tracker v1.0.2 Update",
                    "published_at": "2025-12-06",
                    "body": "### Version 1.0.2 Update\n- Direct Wiki search from search bar.\n- Settings panel with progression export/import.\n- Update checker against GitHub releases.\n- Pre-Searing Ascalon content and location groupings."
                },
                {
                    "tag_name": "v1.0.1",
                    "name": "Guild Wars Reforge Quest Tracker v1.0.1 Update",
                    "published_at": "2025-12-01",
                    "body": "### Version 1.0.1 Update\n- Legendary Defender of Ascalon (LDoA) tracker.\n- Multi-character user profiles.\n- Location grouping for side quests.\n- Dark mode Wiki styling."
                },
                {
                    "tag_name": "v1.0.0",
                    "name": "Guild Wars Reforge Quest Tracker Release",
                    "published_at": "2025-11-29",
                    "body": "### Version 1.0.0 Initial Release\n- Tri-state quest tracking (Not Started, In Progress, Completed).\n- Real-time Wiki synchronization and background scraping.\n- Integrated Wiki viewer and completion timestamps."
                }
            ]

            try:
                r = requests.get(
                    "https://api.github.com/repos/Mr-Akito/GWReforgeTracker/releases",
                    headers={"User-Agent": AppConfig.USER_AGENT},
                    timeout=10
                )
                if r.status_code == 200:
                    releases_data = r.json()
                    curr_parts = [1, 0, 3]
                    has_update = False
                    latest_tag = "v1.0.3"
                    latest_name = "v1.0.3"
                    latest_url = "https://github.com/Mr-Akito/GWReforgeTracker/releases"

                    if isinstance(releases_data, list) and len(releases_data) > 0:
                        top = releases_data[0]
                        latest_tag = top.get("tag_name", "v1.0.3")
                        latest_name = top.get("name", latest_tag)
                        latest_url = top.get("html_url", "https://github.com/Mr-Akito/GWReforgeTracker/releases")
                        
                        # Parse digits for version check
                        tag_digits = [int(p) for p in re.findall(r'\d+', latest_tag)]
                        if tag_digits and tag_digits > curr_parts:
                            has_update = True

                    compiled_releases = []
                    for rel in releases_data:
                        compiled_releases.append({
                            "tag_name": rel.get("tag_name", ""),
                            "name": rel.get("name", ""),
                            "published_at": (rel.get("published_at", "")[:10] if rel.get("published_at") else ""),
                            "body": rel.get("body", "")
                        })

                    result = {
                        "success": True,
                        "current_version": AppConfig.APP_VERSION,
                        "latest_version": latest_tag,
                        "latest_name": latest_name,
                        "latest_url": latest_url,
                        "has_update": has_update,
                        "releases": compiled_releases
                    }
                    self.update_check_result.emit(json.dumps(result))
                    return
            except Exception as e:
                logging.warning(f"GitHub release check failed: {e}")

            # Fallback when offline or API limit reached
            result = {
                "success": False,
                "current_version": AppConfig.APP_VERSION,
                "latest_version": "v1.0.3",
                "latest_name": "Guild Wars Reforge Quest Tracker v1.0.3",
                "latest_url": "https://github.com/Mr-Akito/GWReforgeTracker/releases",
                "has_update": False,
                "releases": fallback_releases
            }
            self.update_check_result.emit(json.dumps(result))

        threading.Thread(target=_worker, daemon=True).start()

    def _get_lan_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _start_companion_server(self):
        bridge_ref = self

        class CompanionHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress console logging noise

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == "/api/status":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    state = bridge_ref.get_full_state_dict()
                    state["room_code"] = bridge_ref.companion_room
                    self.wfile.write(json.dumps(state).encode("utf-8"))
                elif parsed.path == "/api/pairing_info":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    ip = bridge_ref._get_lan_ip()
                    data = {
                        "ip": ip,
                        "port": bridge_ref.companion_port,
                        "room_code": bridge_ref.companion_room,
                        "pairing_url": f"http://{ip}:{bridge_ref.companion_port}/?room={bridge_ref.companion_room}"
                    }
                    self.wfile.write(json.dumps(data).encode("utf-8"))
                elif parsed.path == "/" or parsed.path == "/index.html":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(bridge_ref._get_mobile_companion_html().encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == "/api/quest_status":
                    content_length = int(self.headers.get("Content-Length", 0))
                    post_data = self.rfile.read(content_length)
                    try:
                        req = json.loads(post_data.decode("utf-8"))
                        q_name = req.get("quest_name")
                        status = int(req.get("status", 0))
                        if q_name:
                            bridge_ref.set_quest_status(q_name, status)
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(b'{"success": true}')
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                        self.wfile.write(str(e).encode("utf-8"))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

        def _serve():
            for port in range(8848, 8860):
                try:
                    server = ThreadingHTTPServer(("0.0.0.0", port), CompanionHandler)
                    bridge_ref.companion_port = port
                    logging.info(f"Companion Sync Server listening on port {port}")
                    server.serve_forever()
                    break
                except OSError:
                    continue

        threading.Thread(target=_serve, daemon=True).start()

    @Slot(result=str)
    def get_companion_pairing_info(self):
        ip = self._get_lan_ip()
        url = f"http://{ip}:{self.companion_port}/?room={self.companion_room}"
        return json.dumps({
            "ip": ip,
            "port": self.companion_port,
            "room_code": self.companion_room,
            "pairing_url": url
        })

    def _get_mobile_companion_html(self):
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Guild Wars Reforge Companion</title>
  <style>
    :root {
      --bg: #0B0D13;
      --card: #151824;
      --border: #232838;
      --text: #F1F5F9;
      --muted: #94A3B8;
      --gold: #D4AF37;
      --green: #10B981;
      --amber: #F59E0B;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding-bottom: 74px; -webkit-tap-highlight-color: transparent; }
    header { background: #11141F; border-bottom: 1px solid var(--border); padding: 12px 16px; position: sticky; top: 0; z-index: 50; }
    .top-bar { display: flex; align-items: center; justify-content: space-between; }
    .app-title { font-size: 14px; font-weight: 800; color: var(--gold); letter-spacing: 1px; }
    .room-badge { font-size: 10px; font-weight: 700; color: #10B981; background: rgba(16, 185, 129, 0.15); padding: 2px 7px; border-radius: 12px; }
    .char-info { display: flex; align-items: center; justify-content: space-between; margin-top: 6px; font-size: 12px; color: var(--muted); }
    .char-name { font-weight: 700; color: var(--text); }
    .progress-bar-wrap { margin-top: 10px; background: rgba(255,255,255,0.08); height: 8px; border-radius: 4px; overflow: hidden; }
    .progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--gold), #10B981); width: 0%; transition: width 0.3s ease; }
    .nav-tabs { display: flex; gap: 6px; overflow-x: auto; padding: 10px 16px; background: var(--bg); border-bottom: 1px solid var(--border); }
    .nav-tabs::-webkit-scrollbar { display: none; }
    .tab-btn { background: var(--card); border: 1px solid var(--border); color: var(--muted); padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; white-space: nowrap; }
    .tab-btn.active { background: var(--gold); color: #000; border-color: var(--gold); }
    .quest-list { padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; }
    .quest-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px; display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .quest-card.in-progress { border-color: var(--amber); background: rgba(245, 158, 11, 0.08); }
    .quest-card.completed { border-color: var(--green); background: rgba(16, 185, 129, 0.08); }
    .quest-card.completed .quest-title { text-decoration: line-through; opacity: 0.65; }
    .quest-title { font-size: 13px; font-weight: 600; color: var(--text); flex: 1; }
    .status-btn { width: 32px; height: 32px; border-radius: 50%; border: 1.5px solid var(--border); background: var(--card); display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; font-size: 14px; }
    .status-btn.in-progress { border-color: var(--amber); background: var(--amber); color: #000; }
    .status-btn.completed { border-color: var(--green); background: var(--green); color: #000; }
    .ad-banner-footer { position: fixed; bottom: 0; left: 0; right: 0; background: #0E111A; border-top: 1px solid var(--border); padding: 6px 12px; text-align: center; z-index: 100; }
    .ad-label { font-size: 9px; font-weight: 700; color: var(--muted); letter-spacing: 0.8px; display: block; margin-bottom: 2px; }
    .ad-box { background: #171B26; border: 1px dashed var(--gold); border-radius: 6px; padding: 6px; font-size: 11px; font-weight: 600; color: var(--gold); }
  </style>
</head>
<body>
  <header>
    <div class="top-bar">
      <span class="app-title">REFORGE COMPANION</span>
      <span class="room-badge" id="room-code">GW-SYNC</span>
    </div>
    <div class="char-info">
      <span id="char-name">Hero (All)</span>
      <span id="progress-percent">0% Completed</span>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-bar-fill" id="progress-fill"></div>
    </div>
  </header>
  <div class="nav-tabs" id="nav-tabs">
    <button class="tab-btn active" data-camp="All">All</button>
    <button class="tab-btn" data-camp="Prophecies">Prophecies</button>
    <button class="tab-btn" data-camp="Factions">Factions</button>
    <button class="tab-btn" data-camp="Nightfall">Nightfall</button>
    <button class="tab-btn" data-camp="Eye of the North">EotN</button>
    <button class="tab-btn" data-camp="Beyond">Beyond</button>
    <button class="tab-btn" data-camp="LDoA">LDoA</button>
  </div>
  <div class="quest-list" id="quest-list">
    <div style="text-align: center; padding: 40px; color: var(--muted);">Connecting to desktop app...</div>
  </div>
  <div class="ad-banner-footer">
    <span class="ad-label">SPONSORED ADVERTISEMENT</span>
    <div class="ad-box">Guild Wars Reforge Companion &bull; Ad Banner (320x50 Responsive)</div>
  </div>
  <script>
    let activeCampaign = 'All';
    let appState = null;

    async function fetchState() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        appState = await res.json();
        render();
      } catch (e) {
        console.error(e);
      }
    }

    function render() {
      if (!appState) return;
      document.getElementById('char-name').textContent = `${appState.current_profile || 'Hero'} (${appState.profession || 'All'})`;
      document.getElementById('room-code').textContent = appState.room_code || 'GW-SYNC';

      const quests = appState.quest_db || {};
      const statusMap = appState.quest_status || {};
      let list = [];
      if (activeCampaign === 'All') {
        const order = ['Prophecies', 'Factions', 'Nightfall', 'Eye of the North', 'Beyond', 'LDoA'];
        order.forEach(c => { if (quests[c]) list = list.concat(quests[c]); });
      } else {
        list = quests[activeCampaign] || [];
      }

      let total = 0, completed = 0;
      const seen = new Set();
      list.forEach(item => {
        if (!item || item.includes('---') || seen.has(item)) return;
        seen.add(item);
        total++;
        const s = (statusMap[item] || {}).status || 0;
        if (s === 2) completed++;
      });

      const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
      document.getElementById('progress-percent').textContent = `${pct}% (${completed}/${total})`;
      document.getElementById('progress-fill').style.width = `${pct}%`;

      const listEl = document.getElementById('quest-list');
      listEl.innerHTML = '';
      seen.clear();
      list.forEach(item => {
        if (!item) return;
        if (item.includes('---')) {
          const sep = document.createElement('div');
          sep.style.fontSize = '10px';
          sep.style.fontWeight = '700';
          sep.style.color = 'var(--muted)';
          sep.style.letterSpacing = '1px';
          sep.style.marginTop = '8px';
          sep.textContent = item.replace(/---/g, '').trim();
          listEl.appendChild(sep);
          return;
        }
        if (seen.has(item)) return;
        seen.add(item);

        const sData = statusMap[item] || { status: 0 };
        const card = document.createElement('div');
        card.className = 'quest-card' + (sData.status === 1 ? ' in-progress' : (sData.status === 2 ? ' completed' : ''));

        const title = document.createElement('span');
        title.className = 'quest-title';
        title.textContent = item;
        card.appendChild(title);

        const btn = document.createElement('button');
        btn.className = 'status-btn' + (sData.status === 1 ? ' in-progress' : (sData.status === 2 ? ' completed' : ''));
        btn.innerHTML = sData.status === 2 ? '&#10003;' : (sData.status === 1 ? '&#9679;' : '');
        btn.addEventListener('click', async () => {
          const next = (sData.status + 1) % 3;
          sData.status = next;
          render();
          await fetch('/api/quest_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quest_name: item, status: next })
          });
        });
        card.appendChild(btn);
        listEl.appendChild(card);
      });
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeCampaign = btn.getAttribute('data-camp');
        render();
      });
    });

    fetchState();
    setInterval(fetchState, 2500);
  </script>
</body>
</html>"""

