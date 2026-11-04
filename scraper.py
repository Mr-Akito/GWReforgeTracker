# scraper.py
import requests
import logging
import copy
import time
import unicodedata
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PySide6.QtCore import QThread, Signal
from config import AppConfig, INITIAL_QUEST_DB, INITIAL_QUEST_METADATA, CAMPAIGN_URLS, SECTION_MARKER
from database import DiskCache 

class WikiScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': AppConfig.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        retry_strategy = Retry(
            total=AppConfig.MAX_RETRIES,
            backoff_factor=AppConfig.BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.cache = DiskCache(AppConfig.CACHE_FILE, AppConfig.CACHE_EXPIRY_HOURS, AppConfig.MAX_CACHE_SIZE_MB, AppConfig.MAX_CACHE_ENTRIES)
        self.ignore_exact = {"Quest", "Name", "Location", "Type", "Given by", "Level", "Reward", "Experience", "Gold", "Preceded by", "Followed by"}

    def _sanitize_text(self, text, max_len):
        if not text: return ""
        text = unicodedata.normalize('NFKC', text)
        text = "".join(ch for ch in text if ch.isprintable())
        text = text.strip()
        if len(text) > max_len: return text[:max_len] + "..."
        return text

    def run_sync(self, existing_db, existing_meta=None, progress_callback=None, interrupt_check=None):
        new_db = copy.deepcopy(existing_db if existing_db else INITIAL_QUEST_DB)
        new_meta = copy.deepcopy(existing_meta if existing_meta else INITIAL_QUEST_METADATA)
        
        total_campaigns = len(CAMPAIGN_URLS)
        current_count = 0
        error_log = []
        
        for campaign, url in CAMPAIGN_URLS.items():
            if interrupt_check and interrupt_check(): 
                self.cache.close()
                return None, None, None
            
            if current_count > 0:
                time.sleep(AppConfig.REQUEST_DELAY)
            
            if progress_callback:
                progress_callback(int((current_count / total_campaigns) * 100), f"Scanning {campaign}...")

            side_quests_map = {} 
            seen_quests = set()
            
            try:
                content = self.cache.get(url)
                if not content:
                    response = self.session.get(url, timeout=AppConfig.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        content = response.text
                        self.cache.set(url, content) 
                    else:
                        raise Exception(f"HTTP {response.status_code}")
                
                soup = BeautifulSoup(content, 'html.parser')
                content_root = soup.find('div', {'id': 'mw-content-text'}) or soup
                tables = content_root.find_all('table')
                
                for table in tables:
                    if interrupt_check and interrupt_check(): 
                        self.cache.close()
                        return None, None, None
                    
                    headers = [th.get_text().strip().lower() for th in table.find_all('th')]
                    q_idx = -1
                    loc_idx = -1
                    prof_idx = -1
                    
                    for i, h in enumerate(headers):
                        if 'quest' in h or 'name' in h: q_idx = i
                        elif 'location' in h or 'given at' in h: loc_idx = i
                        elif 'profession' in h: prof_idx = i
                    
                    if q_idx == -1 and headers:
                        q_idx = 0
                    
                    rows = table.find_all('tr')
                    for row in rows:
                        if interrupt_check and interrupt_check(): 
                            self.cache.close()
                            return None, None, None
                        
                        if row.find('th'): continue
                        cols = row.find_all('td')
                        if not cols: continue
                        
                        target_col = cols[q_idx] if q_idx != -1 and len(cols) > q_idx else cols[0]
                        anchor = target_col.find('a')
                        if not anchor: continue
                        
                        quest_name = self._sanitize_text(anchor.get_text(), AppConfig.MAX_QUEST_NAME_LEN)
                        if not quest_name or len(quest_name) < 2 or quest_name in self.ignore_exact:
                            continue 
                        
                        href = anchor.get('href', '')
                        if href and href.startswith('/'):
                            href = f"https://wiki.guildwars.com{href}"
                        
                        location = "Uncategorized"
                        if loc_idx != -1 and len(cols) > loc_idx:
                            raw = self._sanitize_text(cols[loc_idx].get_text(), AppConfig.MAX_LOCATION_LEN)
                            if raw: location = raw
                        
                        prof = ""
                        if prof_idx != -1 and len(cols) > prof_idx:
                            prof = self._sanitize_text(cols[prof_idx].get_text(), 64).lower()
                        
                        if location not in side_quests_map: side_quests_map[location] = []
                        if quest_name not in side_quests_map[location] and quest_name not in seen_quests:
                            side_quests_map[location].append(quest_name)
                            seen_quests.add(quest_name)
                            
                        new_meta[quest_name] = {
                            'campaign': campaign,
                            'location': location,
                            'profession': prof,
                            'url': href
                        }
                
                final_campaign_list = []
                sorted_locations = sorted(side_quests_map.keys())
                if "Uncategorized" in sorted_locations:
                    sorted_locations.remove("Uncategorized")
                    sorted_locations.append("Uncategorized")
                    
                for loc in sorted_locations:
                    unique_quests = sorted(side_quests_map[loc])
                    if unique_quests:
                        final_campaign_list.append(f"{SECTION_MARKER} {loc.upper()} {SECTION_MARKER}")
                        final_campaign_list.extend(unique_quests)

                if final_campaign_list:
                    new_db[campaign] = final_campaign_list

            except Exception as e:
                logging.error(f"Failed to scrape {campaign}: {e}")
                error_log.append(f"{campaign}: {str(e)}")
                if campaign in existing_db:
                    new_db[campaign] = existing_db[campaign]
            
            current_count += 1
        
        self.cache.close()
        return new_db, new_meta, error_log

class DatabaseSyncer(QThread):
    progress_updated = Signal(int, str)
    sync_finished = Signal(dict, dict, list)

    def __init__(self):
        super().__init__()
        self.current_db = {}
        self.current_meta = {}

    def set_current_data(self, db, meta):
        self.current_db = db
        self.current_meta = meta

    def run(self):
        scraper = WikiScraper()
        try:
            db_res, meta_res, errors = scraper.run_sync(
                self.current_db,
                self.current_meta,
                lambda p, m: self.progress_updated.emit(p, m), 
                lambda: self.isInterruptionRequested()
            )
            if db_res:
                self.sync_finished.emit(db_res, meta_res or {}, errors or [])
        except Exception as e:
            logging.error(f"Syncer thread exception: {e}")
