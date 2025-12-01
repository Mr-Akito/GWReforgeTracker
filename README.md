# Guild Wars Reforge Quest Tracker

## Version: 1.0.1 (The "Legendary Defender" Update)

Created by: Akito

A modern, minimalist desktop application designed to help Guild Wars players track their progress across all major campaigns, including the new **Legendary Defender of Ascalon (LDoA)** achievement path.

The interface follows a clean, modern Dark UI/UX theme and runs entirely as a local executable.

---

### New Features in v1.0.1

* **Multi-Profile Support:** Track progress for **multiple characters or accounts** separately. All quest progress is saved and loaded per character profile.
* **Legendary Defender of Ascalon (LDoA) Tracker:** Dedicated section to track LDoA milestones, including leveling goals and daily Vanguard quests.
* **Tri-State Quest Tracking:** Mark quests as **Not Started** (Empty), **In Progress** (Green, Italic), or **Completed** (Gold, Strikethrough).
* **Intelligent Quest Grouping:** Side quests scraped from the wiki are now automatically **grouped by their starting location** for better organization.
* **Integrated Wiki Viewer with Dark Mode:** Loads quest details directly into the rounded right panel. Features custom CSS to provide a clean, focused **dark reading experience** without sidebars or clutter.
* **Global Search & Filters:** Search across all campaigns simultaneously and filter quests by **Status** (Not Started, In Progress, Completed).
* **Time Tracking:** Records and displays the exact date/time of completion when a finished quest is selected.
* **Real-Time Data Sync:** Synchronizes and updates quest lists against the official Guild Wars Wiki in a non-blocking background thread.

---

### ⬇️ Download and Installation (Windows EXE)

The easiest way to use the tracker is by downloading the standalone executable:

1.  **Download:** Download the latest `GWReforgeTracker.exe` file from the **Releases** page.
2.  **Run:** Place the executable in any folder and run it. The application automatically creates `gw1_data.db` and `gw1_cache.db` files to store your quest lists and progress locally.

### Building from Source

If you want to run the Python source code or build the executable yourself (requires Python 3.10+ and the packages listed in `requirements.txt`):

1.  **Clone the Repository:**
    ```bash
    git clone [github.com/Mr-Akito/GWReforgeTracker/](https://github.com/Mr-Akito/GWReforgeTracker/releases)
    cd GWReforgeTracker
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Application:**
    ```bash
    python main.py
    ```
    * **Tip:** You can launch a specific profile directly: `python main.py --profile "MyWarrior"`
4.  **Create the EXE (using PyInstaller):**
    ```bash
    pyinstaller --onefile --windowed --icon "GW_Icon.ico" --name "GWReforgeTracker" main.py
    ```
    *(Note: This command assumes your icon file `GW_Icon.ico` is in the root directory alongside `main.py`.)*

---

### Legal Disclaimer

This tool is provided completely **FREE of charge** and is not for sale. It is an open-source, fan-made project.

* This application is **NOT affiliated with, endorsed, sponsored, or approved by ArenaNet, LLC or NCSoft Corporation.**
* "Guild Wars", "ArenaNet", and "NCSoft" are trademarks or registered trademarks of NCSoft Corporation.
* All game content, quest names, images, and wiki text displayed within this application are the property of their respective owners and the Guild Wars Wiki community (licensed under GNU FDL 1.2).

* The application's code author is Akito.

<img width="1685" height="1076" alt="image" src="https://github.com/user-attachments/assets/2cc7e365-bab5-4d3d-9943-6407a3a61e50" />

<img width="435" height="1011" alt="image" src="https://github.com/user-attachments/assets/45c41724-4619-4454-a5d9-70cc5a3c5c82" />

<img width="383" height="238" alt="image" src="https://github.com/user-attachments/assets/2250afc5-7b71-46d7-b5dd-5b274ae421c3" />


