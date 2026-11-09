# Guild Wars Reforge Quest Tracker

## Version: 1.0.3

Created by: Akito

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-yellow?style=flat&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/mr.akito)

A desktop quest journal and progression tracker for Guild Wars. Built using **PySide6** and **Qt WebEngine** featuring a modern, hardware-accelerated dark presentation theme, responsive typography, and smooth CSS transitions.

---

### Visual Engine, Performance, and Stability (v1.0.3)

* **Configurable Low GPU / Hardware Performance Mode:**
  * Toggleable from the Settings menu to reduce GPU consumption on lower-spec graphics hardware by disabling the background canvas, glass blur shaders, and continuous wave loops.
* **Flicker-Free Display & Zero-Stutter Scrolling:**
  * Uses offscreen canvas caching and CSS content containment (`contain: content`) to ensure smooth, flicker-free list scrolling and state toggling across all 931 quests.
* **Fluid Liquid Wave Progress Bar & Real-Time Campaign Metrics:**
  * Animated liquid fill bar with toggleable wave motion, tracking **Completed / Total** achievable quests, **In Progress** counts, and fractional percentages dynamically across every campaign.
* **High-Contrast Dark & Light Display Modes:**
  * Sanitizes MediaWiki inline styles and enforces 100% opaque, high-contrast typography across both Dark Mode and Light Mode.
* **Configurable Cursor Trailing Light:**
  * Adjustable spotlight effect (`Off`, `Subtle`, `Standard`) on top-level panels to eliminate visual distraction.
* **Standardized Global Scrollbars:**
  * Unified scrollbar styling and smooth scroll behavior across the quest journal, wiki reader, dropdowns, and configuration modals.

---

### Core Progression Systems

1. **Character Customization & Profile Renaming:**
   * Modify the default character name (`Default`) or rename any character profile and update their primary profession while preserving all quest history.
2. **Tri-State Quest Synchronization (Journal <-> Dossier <-> Wiki):**
   * Changing quest status (`Not Started`, `In Progress`, `Completed`) in the Quest Journal column, the Quest Dossier header, or the inline Wiki Entry Status Bar updates all views and inline Wiki quest link badges synchronously.
3. **Formatted Completion Timestamps:**
   * Records and displays completed quest timestamps in `'Month DD, YYYY, HH:MM am/pm'` format (e.g., `November 02, 2026, 06:25 pm`) on both journal cards and the quest dossier.
4. **Mutually Exclusive Quests Lockout:**
   * Automatically locks and grays out opposing mutually exclusive quests when one path is active or completed (*Red Tape* vs. *Imperial Assistance*, *Secrets in the Shadow* vs. *For a Price*, *Loyal 'til the End* vs. *Money on the Side*, *A Peaceful Solution* vs. *A Loose Cannon*, *Death with Honor* vs. *The Rite of Valor*, *A Burning Desire* vs. *Douse Your Enthusiasm*, *Refuse to Drink* vs. *Drink from the Chalice of Corruption*, *Defend Droknar's Forge* vs. *The Hero's Challenge*, *Securing the Iron Mines* vs. *Defend the Temple of War*).
5. **Toggleable Status Color Schemes:**
   * **Classic Palette:** In-Progress (Emerald Green), Completed (Guild Wars Gold).
   * **Alternate Palette:** In-Progress (Amber Yellow), Completed (Vibrant Green).
6. **Unified "All" Campaigns View & Profession Filtering:**
   * View all 931 quests across Prophecies, Factions, Nightfall, Eye of the North, Beyond, and Pre-Searing (LDoA), filtered dynamically by primary profession and hidden quest preferences.

---

### Mobile Companion App (In Progress)

* A dedicated Android companion app is actively in the works to allow players to inspect quests and synchronize progress from their phone or tablet.
* The companion application is fully functional and supports real-time local network QR pairing. It is currently undergoing extended testing across multiple hardware models to ensure seamless compatibility with system notification bars, hardware cutouts, camera scanning, and landscape/tablet orientations.
* An official standalone APK deliverable will be released once broad device verification is completed.

---

### Upcoming Expansion Support (Guild Wars: Afterlife)

* ArenaNet has officially announced **Guild Wars: Afterlife**, the first major expansion for the original *Guild Wars* in nearly 20 years, slated for release on **January 13, 2027**.
* *Guild Wars Reforge Tracker* will receive a dedicated expansion update upon the launch of the new DLC, incorporating:
  * Full quest tracking and tactical compendium support for the journey through the Mists to Xotecha.
  * Campaign walkthrough data covering the conflict against the Cult of Odran.
  * Dynamic dungeon progression metrics for *The Unformed* and its skill-drafting system.
  * Extended cross-profession build loadout intelligence.

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
