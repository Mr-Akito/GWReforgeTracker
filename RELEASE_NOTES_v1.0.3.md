# Guild Wars Reforge Tracker v1.0.3

## Release Overview
**Version 1.0.3** introduces a comprehensive modern HTML5 presentation engine overhaul, hardware-accelerated dark theme styling, full internal wiki browser navigation, resolution-independent High-DPI rendering, and resilient offline caching.

---

### What's New in v1.0.3

#### Visual Engine & Modern HTML5 Overhaul
* **Hardware-Accelerated HTML5 Presentation:** Completely migrated UI from legacy forms to a high-performance HTML5 presentation engine (`PySide6` + `QWebEngineView` + `QWebChannel`).
* **Fluid Liquid Wave Progress Tracker:** Real-time animated liquid wave bar tracking campaign completion percentages, in-progress quests, and total achievable metrics with fluid fill transitions.
* **Flicker-Free Display & Stutter-Free Scrolling:** Optimized with offscreen sprite caching and CSS content containment (`contain: content`) to ensure zero compositor flickering.
* **Dynamic High-DPI & Multi-Monitor Support:** Automatic native resolution detection (1080p, 1440p, 4K QD-OLED) using vector font rasterization to eliminate blurriness across multi-display setups.
* **Low GPU Performance Toggle:** Configurable in the Settings menu to disable background canvas loops and blur shaders for lower-spec graphics hardware.
* **Adjustable Cursor Trailing Spotlight:** Configurable between `Off`, `Subtle`, and `Standard`.
* **Standardized Obsidian & Gold Aesthetics:** Custom unified dropdown menus, smoothed theme transitions, and standardized scrollbar behavior across all interface columns.

#### Internal Wiki Browser & Resilient Caching
* **Seamless Internal Navigation:** All wiki links, quest objectives, and sublinks open directly within the application with browser-style Backward/Forward navigation buttons.
* **Clean Page Transition:** Previous quest content is suppressed while new wiki entries load.
* **Persistent Offline Caching:** Caches up to 5,000 wiki walkthrough pages and sublinks for up to 30 days, preserving full offline access during wiki downtime.

#### Quest Progression & Game Logic Updates
* **Mutually Exclusive Quests Lockout:** Opposing exclusive quest paths (such as *Red Tape* vs. *Imperial Assistance*) automatically lock and gray out once one quest is active or completed.
* **Toggleable Status Color Schemes:** Added toggle in Settings between the Classic palette (In-Progress: Green, Completed: Gold) and the Alternate palette (In-Progress: Amber, Completed: Green).
* **Select Campaign -> "All" View:** Unified view displaying all 931 quests across Prophecies, Factions, Nightfall, Eye of the North, Beyond, and Pre-Searing (LDoA).
* **Primary Profession Filtering:** Filter quest journal entries specifically restricted to your character's primary class.
* **Synchronized Quest States:** Status selection changes (`Not Started`, `In Progress`, `Completed`) update simultaneously across the journal column, quest dossier, and inline wiki badges.
* **Standardized Completion Timestamps:** Completed quest entries display formatted timestamps as `'Month DD, YYYY, HH:MM am/pm'` within the wiki column.
* **Character Customization:** Easily rename character profiles or switch primary professions while retaining full quest history.

---

### Future Roadmap & Upcoming Content

* **Android Mobile Companion App:** A standalone mobile companion application is actively in development. The application is operational with live QR synchronization and is undergoing testing across varied screen dimensions, system cutouts, and hardware configurations. An official APK will be released in an upcoming update.
* **Guild Wars: Afterlife Expansion Update:** ArenaNet announced *Guild Wars: Afterlife*, the first new DLC expansion for the original *Guild Wars* in nearly 20 years, launching **January 13, 2027**. Guild Wars Reforge Tracker will receive a dedicated expansion release incorporating the Xotecha realm, Cult of Odran storylines, *The Unformed* dungeon progression, and cross-profession skill builds.

---

### Release Assets & Checksums

| Asset File | Size | Description |
| :--- | :--- | :--- |
| **`GWReforgeTracker.exe`** | 216.5 MB | Standalone Windows 11 Desktop Application (v1.0.3) |
| **`Source code (zip)`** | Auto | Complete v1.0.3 source code archive |
| **`Source code (tar.gz)`** | Auto | Complete v1.0.3 source code archive |

---

### Legal Disclaimer
This application is fan-made, open-source, and provided **free of charge**.
* Not affiliated with, endorsed, sponsored, or approved by ArenaNet, LLC or NCSoft Corporation.
* "Guild Wars", "ArenaNet", and "NCSoft" are trademarks or registered trademarks of NCSoft Corporation.
* All game content and wiki text are property of their respective owners and the Guild Wars Wiki community (GNU FDL 1.2).
