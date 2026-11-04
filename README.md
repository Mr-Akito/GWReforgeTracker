# Guild Wars Reforge Quest Tracker

## Version: 1.0.3

Created by: Akito

A high-performance desktop quest journal and progression tracking companion for Guild Wars. Built on an **HTML5 presentation engine** (`PySide6` + `QWebEngineView` + `QWebChannel`) with visual design and fluid animation concepts inspired by **[reactbits.dev](https://reactbits.dev)** and **[animejs.com](https://animejs.com)**.

---

### Visual Overhaul, Performance, & Stability Architecture (v1.0.3)

* **Configurable Low GPU / Hardware Performance Mode:**
  * Toggleable from both the main header bar (`⚡`) and the Settings menu to reduce GPU consumption on lower-spec graphics hardware by disabling the background canvas, glass blur shaders, and continuous wave loops.
* **Flicker-Free Display & Zero-Stutter Scrolling:**
  * Uses offscreen pre-rendered canvas sprites, CSS content containment (`contain: content`), and surgical in-place DOM updates so toggling quest states or scrolling through 931 quests maintains smooth performance without compositor flickering.
* **Fluid Liquid Wave Progress Bar & Real-Time Campaign Metrics:**
  * Animated liquid fill bar with toggleable wave motion, tracking **Completed / Total** achievable quests, **In Progress** counts, and fractional percentages dynamically across every campaign.
* **High-Contrast Dark & Light Display Modes:**
  * Sanitizes MediaWiki inline styles and enforces 100% opaque, high-contrast typography across both Dark Mode and Light Mode.
* **Configurable Cursor Trailing Light:**
  * Adjustable spotlight effect (`Off`, `Subtle`, `Standard`) on top-level panels to eliminate visual distraction.
* **Standardized Global Scrollbars:**
  * Unified scrollbar styling and smooth scroll behavior across the quest journal, wiki reader, dropdowns, and configuration modals.

---

### Core Progression & Remediation Systems

1. **Character Customization & Profile Renaming:**
   * Modify the default character name (`Default`) or rename any character profile and update their primary profession while preserving all quest history.
2. **Tri-State Quest Synchronization (Journal <-> Dossier <-> Wiki):**
   * Changing quest status (`Not Started`, `In Progress`, `Completed`) in the Quest Journal column, the Quest Dossier header, or the inline Wiki Entry Status Bar updates all views and inline Wiki quest link badges synchronously.
3. **Formatted Completion Timestamps:**
   * Records and displays completed quest timestamps in `'Month DD, YYYY, HH:MM am/pm'` format (e.g., `November 02, 2026, 06:25 pm`) on both journal cards and the quest dossier.
4. **Mutually Exclusive Quests Lockout (Issue #6):**
   * Automatically locks and grays out opposing mutually exclusive quests when one path is active or completed (*Red Tape* vs. *Imperial Assistance*, *Secrets in the Shadow* vs. *For a Price*, *Loyal 'til the End* vs. *Money on the Side*, *A Peaceful Solution* vs. *A Loose Cannon*, *Death with Honor* vs. *The Rite of Valor*, *A Burning Desire* vs. *Douse Your Enthusiasm*, *Refuse to Drink* vs. *Drink from the Chalice of Corruption*, *Defend Droknar's Forge* vs. *The Hero's Challenge*, *Securing the Iron Mines* vs. *Defend the Temple of War*).
5. **Toggleable Status Color Schemes (Issue #5):**
   * **Classic Palette:** In-Progress (Emerald Green), Completed (Guild Wars Gold).
   * **Alternate Palette:** In-Progress (Amber Yellow), Completed (Vibrant Green).
6. **Unified "All" Campaigns View (Issue #4) & Profession Filtering (Issue #3):**
   * View all 931 quests across Prophecies, Factions, Nightfall, Eye of the North, Beyond, and Pre-Searing (LDoA), filtered dynamically by primary profession and hidden quest preferences.

---

### Executable Deliverable

* Standalone Windows executable compiled via PyInstaller:
  `dist\GWReforgeTracker.exe`

### Building from Source

```powershell
# Install requirements
pip install PySide6 requests beautifulsoup4 pyinstaller

# Run in development
python main.py

# Build single-file executable
pyinstaller --noconfirm gw_tracker.spec
```

---

### Legal Disclaimer

This application is fan-made, open-source, and provided **free of charge**.

* This application is **NOT affiliated with, endorsed, sponsored, or approved by ArenaNet, LLC or NCSoft Corporation.**
* "Guild Wars", "ArenaNet", and "NCSoft" are trademarks or registered trademarks of NCSoft Corporation.
* All game content, quest names, and wiki text are property of their respective owners and the Guild Wars Wiki community (GNU FDL 1.2).

<img width="1435" height="945" alt="image" src="https://github.com/user-attachments/assets/c9073e0f-4188-40ce-8423-f73da5f82797" />
