# config.py
import os
from seed_data import SEED_QUEST_DB, SEED_QUEST_META

class AppConfig:
    APP_TITLE = "Guild Wars Reforge Quest Tracker" 
    APP_VERSION = "1.0.3"
    FONT_FAMILY = "Segoe UI" 
    
    # Files
    DB_FILE = "gw1_data.db"
    CACHE_FILE = "gw1_cache.db"
    USER_FILE = "gw1_user.json" 
    DEFAULT_PROFILE_NAME = "Default"
    SCHEMA_VERSION = 2 
    
    # Settings
    WINDOW_WIDTH = 1440
    WINDOW_HEIGHT = 920
    GAME_PROCESS_NAMES = ["Gw.exe", "Gw.tmp"]
    AUTO_CLOSE_CHECK_INTERVAL_MS = 10000
    
    # Networking & Resilient Caching
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    REQUEST_TIMEOUT = 25
    REQUEST_DELAY = 1.2
    MAX_RETRIES = 5
    BACKOFF_FACTOR = 2
    CACHE_EXPIRY_HOURS = 720       # 30 days persistent offline cache
    MAX_CACHE_SIZE_MB = 150        # Up to 150MB of cached walkthroughs and sublinks
    MAX_CACHE_ENTRIES = 5000       # Up to 5,000 cached pages and sublinks
    
    # Validation & UI
    MAX_QUEST_NAME_LEN = 128
    MAX_LOCATION_LEN = 64
    LAZY_LOAD_BATCH_SIZE = 25
    LAZY_LOAD_INTERVAL_MS = 15 
    SEARCH_DEBOUNCE_MS = 180
    DATE_FORMAT = "%B %d, %Y, %I:%M %p"

    @staticmethod
    def format_timestamp(dt=None):
        import datetime
        if dt is None:
            dt = datetime.datetime.now()
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        month_str = month_names[dt.month]
        hour_12 = dt.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        ampm = "am" if dt.hour < 12 else "pm"
        return f"{month_str} {dt.day:02d}, {dt.year}, {hour_12:02d}:{dt.minute:02d} {ampm}"

class ColorSchemeMode:
    CLASSIC = "classic"       # In Progress: Green, Completed: Gold
    ALTERNATE = "alternate"   # In Progress: Amber/Yellow, Completed: Green

class ThemeColors:
    GOLD = "#D4AF37"
    GREEN = "#4CAF50"
    RED = "#FF6B6B"
    WHITE = "#ECECEC"
    GREY = "#A0A0A5"
    DARK_GREY = "#606065"
    DARK_BG_GRADIENT_START = "#121214"
    DARK_BG_GRADIENT_END = "#1A1A20"
    PANEL_BG = "rgba(30, 30, 36, 0.92)"
    HOVER_WHITE = "rgba(255, 255, 255, 0.08)"
    
    # Alternate Scheme Colors
    ALT_IN_PROGRESS = "#F59E0B" # Amber/Yellow
    ALT_COMPLETED = "#10B981"   # Vibrant Green
    
    @classmethod
    def get_status_colors(cls, scheme=ColorSchemeMode.CLASSIC):
        if scheme == ColorSchemeMode.ALTERNATE:
            return {
                "in_progress": cls.ALT_IN_PROGRESS,
                "completed": cls.ALT_COMPLETED,
                "in_progress_bg": "rgba(245, 158, 11, 0.15)",
                "completed_bg": "rgba(16, 185, 129, 0.15)"
            }
        return {
            "in_progress": cls.GREEN,
            "completed": cls.GOLD,
            "in_progress_bg": "rgba(76, 175, 80, 0.15)",
            "completed_bg": "rgba(212, 175, 55, 0.15)"
        }

class QuestStatus:
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2

class FilterMode:
    ALL = "All Quests"
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class Professions:
    ALL = "All Professions"
    WARRIOR = "Warrior"
    RANGER = "Ranger"
    MONK = "Monk"
    NECROMANCER = "Necromancer"
    MESMER = "Mesmer"
    ELEMENTALIST = "Elementalist"
    ASSASSIN = "Assassin"
    RITUALIST = "Ritualist"
    PARAGON = "Paragon"
    DERVISH = "Dervish"

    ALL_LIST = [
        ALL, WARRIOR, RANGER, MONK, NECROMANCER, MESMER,
        ELEMENTALIST, ASSASSIN, RITUALIST, PARAGON, DERVISH
    ]

SECTION_MARKER = "---"

CAMPAIGN_URLS = {
    "Prophecies": "https://wiki.guildwars.com/wiki/List_of_Prophecies_quests",
    "Factions": "https://wiki.guildwars.com/wiki/List_of_Factions_quests",
    "Nightfall": "https://wiki.guildwars.com/wiki/List_of_Nightfall_quests",
    "Eye of the North": "https://wiki.guildwars.com/wiki/List_of_Eye_of_the_North_quests",
    "Beyond": "https://wiki.guildwars.com/wiki/List_of_Beyond_quests"
}

CAMPAIGN_ORDER = ["All", "Prophecies", "Factions", "Nightfall", "Eye of the North", "Beyond", "LDoA"]

MUTUALLY_EXCLUSIVE_QUESTS = {
    "Imperial Assistance": ["Red Tape"],
    "Red Tape": ["Imperial Assistance"],
    "Secrets in the Shadow": ["For a Price"],
    "For a Price": ["Secrets in the Shadow"],
    "Loyal 'til the End": ["Money on the Side"],
    "Money on the Side": ["Loyal 'til the End"],
    "A Peaceful Solution": ["A Loose Cannon"],
    "A Loose Cannon": ["A Peaceful Solution"],
    "Death with Honor": ["The Rite of Valor"],
    "The Rite of Valor": ["Death with Honor"],
    "A Burning Desire": ["Douse Your Enthusiasm"],
    "Douse Your Enthusiasm": ["A Burning Desire"],
    "Refuse to Drink": ["Drink from the Chalice of Corruption"],
    "Drink from the Chalice of Corruption": ["Refuse to Drink"],
    "Defend Droknar's Forge": ["The Hero's Challenge"],
    "The Hero's Challenge": ["Defend Droknar's Forge"],
    "Securing the Iron Mines": ["Defend the Temple of War"],
    "Defend the Temple of War": ["Securing the Iron Mines"]
}

QUEST_WIKI_URL_OVERRIDES = {
    "Isle of the Dead": "https://wiki.guildwars.com/wiki/Isle_of_the_Dead_(quest)",
    "The Great Northern Wall": "https://wiki.guildwars.com/wiki/The_Great_Northern_Wall_(quest)",
    "Fort Ranik": "https://wiki.guildwars.com/wiki/Fort_Ranik_(quest)",
    "Ruins of Surmia": "https://wiki.guildwars.com/wiki/Ruins_of_Surmia_(quest)",
    "Nolani Academy": "https://wiki.guildwars.com/wiki/Nolani_Academy_(quest)",
    "Borlis Pass": "https://wiki.guildwars.com/wiki/Borlis_Pass_(quest)",
    "The Frost Gate": "https://wiki.guildwars.com/wiki/The_Frost_Gate_(quest)",
    "Gates of Kryta": "https://wiki.guildwars.com/wiki/Gates_of_Kryta_(quest)",
    "D'Alessio Seaboard": "https://wiki.guildwars.com/wiki/D%27Alessio_Seaboard_(quest)",
    "Divinity Coast": "https://wiki.guildwars.com/wiki/Divinity_Coast_(quest)",
    "Riverside Province": "https://wiki.guildwars.com/wiki/Riverside_Province_(quest)",
    "Sanctum Cay": "https://wiki.guildwars.com/wiki/Sanctum_Cay_(quest)",
    "Dunes of Despair": "https://wiki.guildwars.com/wiki/Dunes_of_Despair_(quest)",
    "Thirsty River": "https://wiki.guildwars.com/wiki/Thirsty_River_(quest)",
    "Elona Reach": "https://wiki.guildwars.com/wiki/Elona_Reach_(quest)",
    "Augury Rock": "https://wiki.guildwars.com/wiki/Augury_Rock_(quest)",
    "The Dragon's Lair": "https://wiki.guildwars.com/wiki/The_Dragon%27s_Lair_(quest)",
    "Ice Caves of Sorrow": "https://wiki.guildwars.com/wiki/Ice_Caves_of_Sorrow_(quest)",
    "Iron Mines of Moladune": "https://wiki.guildwars.com/wiki/Iron_Mines_of_Moladune_(quest)",
    "Thunderhead Keep": "https://wiki.guildwars.com/wiki/Thunderhead_Keep_(quest)",
    "Ring of Fire": "https://wiki.guildwars.com/wiki/Ring_of_Fire_(quest)",
    "Abaddon's Mouth": "https://wiki.guildwars.com/wiki/Abaddon%27s_Mouth_(quest)",
    "Hell's Precipice": "https://wiki.guildwars.com/wiki/Hell%27s_Precipice_(quest)",
    "Minister Cho's Estate": "https://wiki.guildwars.com/wiki/Minister_Cho%27s_Estate_(quest)",
    "Zen Daijun": "https://wiki.guildwars.com/wiki/Zen_Daijun_(quest)",
    "Vizunah Square": "https://wiki.guildwars.com/wiki/Vizunah_Square_(quest)",
    "Nahpui Quarter": "https://wiki.guildwars.com/wiki/Nahpui_Quarter_(quest)",
    "Tahnnakai Temple": "https://wiki.guildwars.com/wiki/Tahnnakai_Temple_(quest)",
    "Arborstone": "https://wiki.guildwars.com/wiki/Arborstone_(quest)",
    "Boreas Seabed": "https://wiki.guildwars.com/wiki/Boreas_Seabed_(quest)",
    "Sunjiang District": "https://wiki.guildwars.com/wiki/Sunjiang_District_(quest)",
    "The Eternal Grove": "https://wiki.guildwars.com/wiki/The_Eternal_Grove_(quest)",
    "Gyala Hatchery": "https://wiki.guildwars.com/wiki/Gyala_Hatchery_(quest)",
    "Unwaking Waters": "https://wiki.guildwars.com/wiki/Unwaking_Waters_(quest)",
    "Raisu Palace": "https://wiki.guildwars.com/wiki/Raisu_Palace_(quest)",
    "Imperial Sanctum": "https://wiki.guildwars.com/wiki/Imperial_Sanctum_(quest)",
    "Chahbek Village": "https://wiki.guildwars.com/wiki/Chahbek_Village_(quest)",
    "Jokanur Diggings": "https://wiki.guildwars.com/wiki/Jokanur_Diggings_(quest)",
    "Blacktide Den": "https://wiki.guildwars.com/wiki/Blacktide_Den_(quest)",
    "Consulate Docks": "https://wiki.guildwars.com/wiki/Consulate_Docks_(quest)",
    "Venta Cemetery": "https://wiki.guildwars.com/wiki/Venta_Cemetery_(quest)",
    "Kodonur Crossroads": "https://wiki.guildwars.com/wiki/Kodonur_Crossroads_(quest)",
    "Rilohn Refuge": "https://wiki.guildwars.com/wiki/Rilohn_Refuge_(quest)",
    "Pogahn Passage": "https://wiki.guildwars.com/wiki/Pogahn_Passage_(quest)",
    "Moddok Crevice": "https://wiki.guildwars.com/wiki/Moddok_Crevice_(quest)",
    "Tihark Orchard": "https://wiki.guildwars.com/wiki/Tihark_Orchard_(quest)",
    "Grand Court of Sebelkeh": "https://wiki.guildwars.com/wiki/Grand_Court_of_Sebelkeh_(quest)",
    "Jennur's Horde": "https://wiki.guildwars.com/wiki/Jennur%27s_Horde_(quest)",
    "Nundu Bay": "https://wiki.guildwars.com/wiki/Nundu_Bay_(quest)",
    "Gate of Desolation": "https://wiki.guildwars.com/wiki/Gate_of_Desolation_(quest)",
    "Ruins of Morah": "https://wiki.guildwars.com/wiki/Ruins_of_Morah_(quest)",
    "Gate of Pain": "https://wiki.guildwars.com/wiki/Gate_of_Pain_(quest)",
    "Gate of Madness": "https://wiki.guildwars.com/wiki/Gate_of_Madness_(quest)",
    "Abaddon's Gate": "https://wiki.guildwars.com/wiki/Abaddon%27s_Gate_(quest)",
    "Boreal Station": "https://wiki.guildwars.com/wiki/Boreal_Station_(quest)"
}

INITIAL_QUEST_DB = SEED_QUEST_DB
INITIAL_QUEST_METADATA = SEED_QUEST_META
