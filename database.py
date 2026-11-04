# database.py
import sqlite3
import json
import os
import logging
import datetime
import time
import shutil
from urllib.parse import quote
from config import (
    AppConfig, SECTION_MARKER, INITIAL_QUEST_DB, INITIAL_QUEST_METADATA,
    QuestStatus, ColorSchemeMode, Professions, MUTUALLY_EXCLUSIVE_QUESTS,
    QUEST_WIKI_URL_OVERRIDES
)

class DiskCache:
    def __init__(self, db_path, expiry_hours, max_size_mb, max_entries):
        self.db_path = db_path
        self.expiry_seconds = expiry_hours * 3600
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self._init_db()

    def _init_db(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=60) 
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        url TEXT PRIMARY KEY,
                        content TEXT,
                        timestamp REAL
                    )
                """)
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_timestamp ON cache(timestamp)")
        except Exception as e:
            logging.error(f"Cache Init Error: {e}", exc_info=True) 

    def get(self, url, allow_stale=True):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT content, timestamp FROM cache WHERE url = ?", (url,))
            row = cursor.fetchone()
            if row:
                content, timestamp = row
                is_fresh = (time.time() - timestamp < self.expiry_seconds)
                if is_fresh or allow_stale:
                    return content
        except sqlite3.Error as e: 
            logging.warning(f"DiskCache GET error for {url}: {e}")
        return None

    def set(self, url, content):
        try:
            with self.conn:
                self.conn.execute("INSERT OR REPLACE INTO cache (url, content, timestamp) VALUES (?, ?, ?)", 
                                  (url, content, time.time()))
            self._prune()
        except sqlite3.Error as e: 
            logging.warning(f"DiskCache SET error for {url}: {e}")

    def delete(self, url):
        try:
            with self.conn:
                self.conn.execute("DELETE FROM cache WHERE url = ?", (url,))
        except sqlite3.Error as e: 
            logging.warning(f"DiskCache DELETE error for {url}: {e}")

    def clear(self):
        try:
            with self.conn:
                self.conn.execute("DELETE FROM cache")
            with self.conn:
                self.conn.execute("VACUUM")
            return True
        except sqlite3.Error as e:
            logging.error(f"DiskCache CLEAR error: {e}")
            return False

    def _prune(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT count(*) FROM cache")
            count = cursor.fetchone()[0]
            
            needs_vacuum = False
            
            if count > self.max_entries:
                logging.info(f"Pruning cache by count: {count} > {self.max_entries}")
                with self.conn:
                    self.conn.execute("""
                        DELETE FROM cache WHERE url IN (
                            SELECT url FROM cache ORDER BY timestamp ASC LIMIT ?
                        )
                    """, (count - self.max_entries,))
                    needs_vacuum = True
            
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > self.max_size_bytes:
                logging.info(f"Pruning cache by size: {os.path.getsize(self.db_path)/1024/1024:.2f}MB > {self.max_size_bytes/1024/1024:.2f}MB")
                with self.conn:
                     self.conn.execute("""
                        DELETE FROM cache WHERE url IN (
                            SELECT url FROM cache ORDER BY timestamp ASC LIMIT ?
                        )
                    """, (self.max_entries // 2,))
                     needs_vacuum = True
                
            if needs_vacuum:
                with self.conn:
                    self.conn.execute("VACUUM")
                    
        except sqlite3.Error as e: 
            logging.error(f"DiskCache PRUNE error: {e}")
    
    def close(self):
        try: 
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except sqlite3.Error as e: 
            logging.error(f"DiskCache CLOSE error: {e}")

class DataManager:
    def __init__(self):
        self.db_path = AppConfig.DB_FILE
        self.json_user_file = AppConfig.USER_FILE
        
        self._backup_db()
        self._init_db()
        
        self.cache = DiskCache(
            AppConfig.CACHE_FILE, 
            AppConfig.CACHE_EXPIRY_HOURS, 
            AppConfig.MAX_CACHE_SIZE_MB,
            AppConfig.MAX_CACHE_ENTRIES
        )
        
        self.current_profile_name = self._get_setting("current_profile", AppConfig.DEFAULT_PROFILE_NAME)
        
        # Initialize quest database and metadata
        self.quest_db = self._load_quest_db()
        if not self.quest_db or len(self.quest_db.get("Prophecies", [])) < 10:
            self.quest_db = INITIAL_QUEST_DB
            self._save_quest_db(self.quest_db)

        self.quest_metadata = self._load_quest_metadata()
        if not self.quest_metadata or len(self.quest_metadata) < 10:
            self.quest_metadata = INITIAL_QUEST_METADATA
            self._save_quest_metadata(self.quest_metadata)
        
        # Migrate from legacy JSON
        self._migrate_from_json()

        # Verify default profile
        if not self._profile_exists(self.current_profile_name):
            self.create_profile(self.current_profile_name) 
        
        # Integrity check
        self._ensure_all_quests_tracked()

    def _backup_db(self):
        if os.path.exists(self.db_path):
            try:
                backup_path = f"{self.db_path}.bak"
                shutil.copy2(self.db_path, backup_path)
                logging.info(f"Database backup created at {backup_path}")
            except Exception as e:
                logging.error(f"Failed to create database backup: {e}")

    def _init_db(self):
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=60)
            with self.conn:
                self.conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
                self.conn.execute("CREATE TABLE IF NOT EXISTS profiles (name TEXT PRIMARY KEY, profession TEXT)")
                
                # Check profile columns for migration
                cursor = self.conn.execute("PRAGMA table_info(profiles)")
                p_columns = [col[1] for col in cursor.fetchall()]
                if 'profession' not in p_columns:
                    self.conn.execute("ALTER TABLE profiles ADD COLUMN profession TEXT DEFAULT 'All Professions'")
                    logging.info("Migrated profiles table: Added profession column.")

                # Check quest_status columns for migration (Legacy v1.0.1 / v1.0.2 upgrade path)
                cursor = self.conn.execute("PRAGMA table_info(quest_status)")
                qs_columns = [col[1] for col in cursor.fetchall()]
                
                if qs_columns:
                    if 'timestamp' not in qs_columns:
                        self.conn.execute("ALTER TABLE quest_status ADD COLUMN timestamp TEXT")
                        logging.info("Migrated quest_status table: Added timestamp column.")
                    if 'is_hidden' not in qs_columns:
                        self.conn.execute("ALTER TABLE quest_status ADD COLUMN is_hidden INTEGER DEFAULT 0")
                        logging.info("Migrated quest_status table: Added is_hidden column.")

                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS quest_status (
                        profile TEXT,
                        quest_name TEXT,
                        status INTEGER,
                        timestamp TEXT,
                        is_hidden INTEGER DEFAULT 0,
                        PRIMARY KEY (profile, quest_name),
                        FOREIGN KEY(profile) REFERENCES profiles(name) ON DELETE CASCADE
                    )
                """)
                self.conn.execute("CREATE TABLE IF NOT EXISTS game_data (key TEXT PRIMARY KEY, json_data TEXT)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_status_profile ON quest_status(profile)")
                
                self.conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                                ("db_version", str(AppConfig.SCHEMA_VERSION)))
        except sqlite3.Error as e:
            logging.critical(f"CRITICAL: Failed to initialize main database: {e}", exc_info=True)

    def _migrate_from_json(self):
        if not os.path.exists(self.json_user_file):
            return

        try:
            logging.info("Checking for legacy JSON data to merge...")
            with open(self.json_user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile_name = self.current_profile_name
            insert_data = []

            for quest_name, quest_info in data.items():
                status = quest_info.get("status")
                timestamp = quest_info.get("timestamp")
                if status == QuestStatus.IN_PROGRESS or status == QuestStatus.COMPLETED:
                    insert_data.append((profile_name, quest_name, status, timestamp, 0))
            
            if insert_data:
                with self.conn:
                    self.conn.executemany("""
                        INSERT OR IGNORE INTO quest_status (profile, quest_name, status, timestamp, is_hidden) 
                        VALUES (?, ?, ?, ?, ?)
                    """, insert_data)
                logging.info(f"Successfully migrated {len(insert_data)} quest entries from legacy JSON.")
        except Exception as e:
            logging.error(f"Migration failed: {e}", exc_info=True)

    def _ensure_all_quests_tracked(self):
        current_status = self.get_current_quests()
        all_quests = set()
        for quest_list in self.quest_db.values():
            for item in quest_list:
                if SECTION_MARKER not in item:
                    all_quests.add(item)
        missing_quests = all_quests - set(current_status.keys())
        if missing_quests:
            logging.debug(f"Detected {len(missing_quests)} untracked quests in current quest database.")

    def _get_setting(self, key, default):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def _set_setting(self, key, value):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))

    def _profile_exists(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM profiles WHERE name = ?", (name,))
        return cursor.fetchone() is not None

    def _load_quest_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT json_data FROM game_data WHERE key = 'quest_db'")
        row = cursor.fetchone()
        return json.loads(row[0]) if row else {}

    def _save_quest_db(self, data):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO game_data (key, json_data) VALUES (?, ?)", 
                              ('quest_db', json.dumps(data)))

    def _load_quest_metadata(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT json_data FROM game_data WHERE key = 'quest_metadata'")
        row = cursor.fetchone()
        return json.loads(row[0]) if row else {}

    def _save_quest_metadata(self, data):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO game_data (key, json_data) VALUES (?, ?)", 
                              ('quest_metadata', json.dumps(data)))

    def get_color_scheme(self):
        return self._get_setting("color_scheme", ColorSchemeMode.CLASSIC)

    def set_color_scheme(self, scheme):
        self._set_setting("color_scheme", scheme)

    def get_theme(self):
        val = self._get_setting("dark_mode", "True")
        return val == "True"

    def set_theme(self, is_dark):
        self._set_setting("dark_mode", str(is_dark))

    def is_first_run(self):
        return self._get_setting("first_run_completed", "False") == "False"

    def complete_first_run(self):
        self._set_setting("first_run_completed", "True")

    def get_preferences(self):
        return {
            "color_scheme": self._get_setting("color_scheme", ColorSchemeMode.CLASSIC),
            "dark_mode": self._get_setting("dark_mode", "True") == "True",
            "show_hidden": self._get_setting("show_hidden", "False") == "True",
            "show_locked": self._get_setting("show_locked", "True") == "True",
            "show_timestamps": self._get_setting("show_timestamps", "True") == "True",
            "low_gpu_mode": self._get_setting("low_gpu_mode", "False") == "True",
            "animation_level": self._get_setting("animation_level", "reduced"),
            "cursor_light": self._get_setting("cursor_light", "subtle"),
            "liquid_wave_anim": self._get_setting("liquid_wave_anim", "True") == "True",
            "card_density": self._get_setting("card_density", "comfortable"),
            "auto_close": self._get_setting("auto_close", "False") == "True"
        }

    def save_preferences(self, prefs):
        if not isinstance(prefs, dict):
            return
        for key in [
            "color_scheme", "dark_mode", "show_hidden", "show_locked",
            "show_timestamps", "low_gpu_mode", "animation_level",
            "cursor_light", "liquid_wave_anim", "card_density", "auto_close"
        ]:
            if key in prefs:
                self._set_setting(key, str(prefs[key]))

    def _normalize_timestamp(self, raw_ts):
        if not raw_ts or not isinstance(raw_ts, str):
            return None
        raw_ts = raw_ts.strip()
        # Check if already in 'Month DD, YYYY, HH:MM am/pm'
        if any(m in raw_ts for m in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]) and ("am" in raw_ts or "pm" in raw_ts):
            return raw_ts
        # Try parsing legacy formats
        for fmt in [
            "%B %d, %Y, %I:%M %p",
            "%m / %d / %Y %I:%M %p",
            "%m/%d/%Y, %I:%M:%S %p",
            "%m/%d/%Y %I:%M %p",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M"
        ]:
            try:
                dt = datetime.datetime.strptime(raw_ts, fmt)
                return AppConfig.format_timestamp(dt)
            except ValueError:
                continue
        return raw_ts

    def get_profiles(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM profiles")
        return [row[0] for row in cursor.fetchall()]

    def get_profile_profession(self, profile_name=None):
        name = profile_name or self.current_profile_name
        cursor = self.conn.cursor()
        cursor.execute("SELECT profession FROM profiles WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else Professions.ALL

    def set_profile_profession(self, profession, profile_name=None):
        name = profile_name or self.current_profile_name
        with self.conn:
            self.conn.execute("UPDATE profiles SET profession = ? WHERE name = ?", (profession, name))

    def create_profile(self, name, profession=Professions.ALL):
        name = (name or "").strip()
        if not name or self._profile_exists(name):
            return False
        try:
            with self.conn:
                self.conn.execute("INSERT INTO profiles (name, profession) VALUES (?, ?)", (name, profession))
            self.switch_profile(name)
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to create profile '{name}': {e}")
            return False

    def rename_profile(self, old_name, new_name, profession=None):
        old_name = (old_name or "").strip()
        new_name = (new_name or "").strip()
        if not old_name or not new_name or not self._profile_exists(old_name):
            return False
        if new_name != old_name and self._profile_exists(new_name):
            return False
        try:
            current_prof = profession if profession else self.get_profile_profession(old_name)
            with self.conn:
                if new_name != old_name:
                    self.conn.execute("INSERT INTO profiles (name, profession) VALUES (?, ?)", (new_name, current_prof))
                    self.conn.execute("UPDATE quest_status SET profile = ? WHERE profile = ?", (new_name, old_name))
                    self.conn.execute("DELETE FROM profiles WHERE name = ?", (old_name,))
                else:
                    self.conn.execute("UPDATE profiles SET profession = ? WHERE name = ?", (current_prof, old_name))
            if self.current_profile_name == old_name:
                self.current_profile_name = new_name
                self._set_setting("current_profile", new_name)
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to rename/update profile '{old_name}' -> '{new_name}': {e}")
            return False

    def delete_profile(self, name):
        profiles = self.get_profiles()
        if len(profiles) <= 1: return False
        try:
            with self.conn:
                self.conn.execute("DELETE FROM profiles WHERE name = ?", (name,))
                self.conn.execute("DELETE FROM quest_status WHERE profile = ?", (name,))
            remaining = self.get_profiles()
            if remaining:
                self.switch_profile(remaining[0])
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to delete profile '{name}': {e}")
            return False
        
    def switch_profile(self, profile_name):
        if self._profile_exists(profile_name):
            self.current_profile_name = profile_name
            self._set_setting("current_profile", profile_name)
            self._ensure_all_quests_tracked()

    def get_current_quests(self, profile_name=None):
        profile = profile_name or self.current_profile_name
        cursor = self.conn.cursor()
        cursor.execute("SELECT quest_name, status, timestamp, is_hidden FROM quest_status WHERE profile = ?", (profile,))
        rows = cursor.fetchall()
        return {
            row[0]: {
                "status": row[1],
                "timestamp": self._normalize_timestamp(row[2]),
                "is_hidden": bool(row[3]) if len(row) > 3 else False
            } for row in rows
        }

    def get_status_data(self, quest, profile_name=None):
        profile = profile_name or self.current_profile_name
        cursor = self.conn.cursor()
        cursor.execute("SELECT status, timestamp, is_hidden FROM quest_status WHERE profile = ? AND quest_name = ?", 
                       (profile, quest))
        row = cursor.fetchone()
        return {
            "status": row[0],
            "timestamp": self._normalize_timestamp(row[1]),
            "is_hidden": bool(row[2])
        } if row else None

    def get_cached_content(self, url):
        return self.cache.get(url)

    def clear_wiki_cache(self):
        return self.cache.clear()
    
    def set_status(self, quest, status, profile_name=None):
        profile = profile_name or self.current_profile_name
        try:
            with self.conn:
                if status == QuestStatus.COMPLETED:
                    current_time = AppConfig.format_timestamp()
                    self.conn.execute("""
                        INSERT INTO quest_status (profile, quest_name, status, timestamp, is_hidden)
                        VALUES (?, ?, ?, ?, 0)
                        ON CONFLICT(profile, quest_name) DO UPDATE SET
                            status=excluded.status,
                            timestamp=excluded.timestamp
                    """, (profile, quest, status, current_time))
                elif status == QuestStatus.IN_PROGRESS:
                    self.conn.execute("""
                        INSERT INTO quest_status (profile, quest_name, status, timestamp, is_hidden)
                        VALUES (?, ?, ?, NULL, 0)
                        ON CONFLICT(profile, quest_name) DO UPDATE SET
                            status=excluded.status,
                            timestamp=NULL
                    """, (profile, quest, status))
                else:
                    # NOT_STARTED
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT is_hidden FROM quest_status WHERE profile = ? AND quest_name = ?", (profile, quest))
                    row = cursor.fetchone()
                    if row and row[0]:
                        self.conn.execute("UPDATE quest_status SET status = ?, timestamp = NULL WHERE profile = ? AND quest_name = ?", 
                                          (QuestStatus.NOT_STARTED, profile, quest))
                    else:
                        self.conn.execute("DELETE FROM quest_status WHERE profile = ? AND quest_name = ?", 
                                          (profile, quest))
        except sqlite3.Error as e:
            logging.error(f"Failed to set status for '{quest}' to {status}: {e}")

    def set_quest_hidden(self, quest, is_hidden, profile_name=None):
        profile = profile_name or self.current_profile_name
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO quest_status (profile, quest_name, status, timestamp, is_hidden)
                    VALUES (?, ?, 0, NULL, ?)
                    ON CONFLICT(profile, quest_name) DO UPDATE SET is_hidden = excluded.is_hidden
                """, (profile, quest, 1 if is_hidden else 0))
        except sqlite3.Error as e:
            logging.error(f"Failed to set hidden status for '{quest}': {e}")

    def unhide_all_quests(self, profile_name=None):
        profile = profile_name or self.current_profile_name
        try:
            with self.conn:
                self.conn.execute("UPDATE quest_status SET is_hidden = 0 WHERE profile = ?", (profile,))
                self.conn.execute("DELETE FROM quest_status WHERE profile = ? AND status = 0 AND is_hidden = 0", (profile,))
            return True
        except sqlite3.Error as e:
            logging.error(f"Failed to unhide all quests for '{profile}': {e}")
            return False

    def get_locked_quests(self, profile_name=None):
        profile = profile_name or self.current_profile_name
        current_quests = self.get_current_quests(profile)
        active_or_done = {
            q for q, data in current_quests.items()
            if data.get("status") in (QuestStatus.IN_PROGRESS, QuestStatus.COMPLETED)
        }
        locked = set()
        for q_name in active_or_done:
            if q_name in MUTUALLY_EXCLUSIVE_QUESTS:
                for exclusive_partner in MUTUALLY_EXCLUSIVE_QUESTS[q_name]:
                    if exclusive_partner not in active_or_done:
                        locked.add(exclusive_partner)
        return locked

    def get_wiki_url(self, quest_name):
        if "Reach Level" in quest_name:
            return "https://wiki.guildwars.com/wiki/Legendary_Defender_of_Ascalon"
        if quest_name in QUEST_WIKI_URL_OVERRIDES:
            return QUEST_WIKI_URL_OVERRIDES[quest_name]
        meta = self.quest_metadata.get(quest_name)
        if meta and meta.get("url"):
            return meta["url"]
        encoded = quote(quest_name.replace(" ", "_"))
        return f"https://wiki.guildwars.com/wiki/{encoded}"

    def reset_campaign(self, campaign, profile_name=None):
        profile = profile_name or self.current_profile_name
        try:
            with self.conn:
                if campaign == "All":
                    self.conn.execute("DELETE FROM quest_status WHERE profile = ?", (profile,))
                elif campaign in self.quest_db:
                    quests_to_reset = [q for q in self.quest_db[campaign] if SECTION_MARKER not in q]
                    for q in quests_to_reset:
                        self.conn.execute("DELETE FROM quest_status WHERE profile = ? AND quest_name = ?", 
                                          (profile, q))
        except sqlite3.Error as e:
            logging.error(f"Failed to reset campaign '{campaign}': {e}")
    
    def update_quest_db(self, new_db, new_metadata=None):
        self.quest_db = new_db
        self._save_quest_db(new_db)
        if new_metadata:
            self.quest_metadata.update(new_metadata)
            self._save_quest_metadata(self.quest_metadata)
        self._ensure_all_quests_tracked()

    def export_progression_json(self):
        """Export all user quest statuses and profiles to a JSON string for backup/migration."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, profession FROM profiles")
            profiles = [{"name": r[0], "profession": r[1]} for r in cursor.fetchall()]
            
            cursor.execute("SELECT profile, quest_name, status, timestamp, is_hidden FROM quest_status")
            statuses = [
                {
                    "profile": r[0],
                    "quest_name": r[1],
                    "status": r[2],
                    "timestamp": self._normalize_timestamp(r[3]),
                    "is_hidden": bool(r[4])
                } for r in cursor.fetchall()
            ]
            
            export_dict = {
                "version": AppConfig.APP_VERSION,
                "exported_at": datetime.datetime.now().isoformat(),
                "current_profile": self.current_profile_name,
                "profiles": profiles,
                "quest_status": statuses,
                "preferences": self.get_preferences()
            }
            return json.dumps(export_dict, indent=2)
        except Exception as e:
            logging.error(f"Failed to export progression: {e}")
            return None

    def import_progression_json(self, json_str):
        """Import user quest statuses and profiles from a JSON string."""
        try:
            data = json.loads(json_str)
            with self.conn:
                if "profiles" in data:
                    for p in data["profiles"]:
                        p_name = p.get("name") if isinstance(p, dict) else p
                        p_prof = p.get("profession", "All Professions") if isinstance(p, dict) else "All Professions"
                        if p_name:
                            self.conn.execute(
                                "INSERT OR REPLACE INTO profiles (name, profession) VALUES (?, ?)",
                                (p_name, p_prof)
                            )
                
                if "quest_status" in data:
                    for qs in data["quest_status"]:
                        p = qs.get("profile", self.current_profile_name)
                        q = qs.get("quest_name")
                        s = qs.get("status", 0)
                        ts = qs.get("timestamp")
                        h = 1 if qs.get("is_hidden") else 0
                        if q:
                            self.conn.execute("""
                                INSERT OR REPLACE INTO quest_status (profile, quest_name, status, timestamp, is_hidden)
                                VALUES (?, ?, ?, ?, ?)
                            """, (p, q, s, ts, h))
                
                if "current_profile" in data:
                    self.current_profile_name = data["current_profile"]
                    self._set_setting("current_profile", self.current_profile_name)
                
                if "preferences" in data and isinstance(data["preferences"], dict):
                    self.save_preferences(data["preferences"])
            return True
        except Exception as e:
            logging.error(f"Failed to import progression: {e}")
            return False
