# Guild Wars Reforge Quest Tracker

## Version: 1.0.2

Created by: Akito

A modern, minimalist desktop application designed to help Guild Wars players track their progress across all major Guild Wars campaigns, including **Pre-Searing** and the **Legendary Defender of Ascalon (LDoA)** path.

The interface follows a clean Dark UI style and runs entirely as a local executable.

Windows may show an install warning. All files are safe and the full source code is available for verification.

---

### New Features in v1.0.2

* **Direct Wiki Search:** You can now search the Guild Wars Wiki directly from the quest search bar. Type any term and press Enter.
* **New Settings Panel:**  
  * Export and import your progression.  
  * Built-in update check and downloader powered by `updater.py`.  
  * Quest History viewer.  
  * About and Legal moved into Settings.  
* **Old JSON Import:** Older exported progression files can now be imported into the new data structure.
* **Keyboard Navigation Support:** General improvements for faster movement through the UI.
* **UI Improvements:** Cleaner layout, more consistent interactions, and updated styles.
* **Pre-Searing Support:** Complete Pre-Searing quest list added.
* **Link Fixes:** Corrected quests that previously linked to map pages instead of the correct quest page.
* **Removed Unnecessary Annotations:** Cleaner data loading and display.

---

### Additional Notes for Returning Users

Older versions stored quest data locally using previous category names. After updating, you may see outdated categories on first launch.

To refresh them:

1. Open the tracker.
2. Click the **Sync Database** button in the bottom-left corner.
3. The new categories and tabs will appear correctly.

---

### Download and Installation (Windows EXE)

The easiest way to use the tracker is by downloading the standalone executable:

1. **Download:** Get the latest `GWReforgeTracker.exe` from the **Releases page** at:  
   https://github.com/Mr-Akito/GWReforgeTracker/releases
2. **Run:** Place the executable anywhere and launch it. The application automatically creates the local database files it needs.

#### Automatic Updater

Version 1.0.2 introduces an integrated updater using `updater.py`.  
The application can now check for the newest release and download it without opening a browser.

No manual setup is required.

---

### Building from Source

If you want to run the Python source code or build the executable yourself (requires Python 3.10+ and the packages listed in `requirements.txt`):

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/Mr-Akito/GWReforgeTracker/
    cd GWReforgeTracker
    ```

2. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Application:**
    ```bash
    python main.py
    ```
    *Tip: You can launch a specific profile directly:*  
    ```bash
    python main.py --profile "MyWarrior"
    ```

4. **Create the EXE (using PyInstaller):**
    ```bash
    pyinstaller --onefile --windowed --icon "GW_Icon.ico" --name "GWReforgeTracker" main.py
    ```
    *(Make sure `GW_Icon.ico` is in the project root.)*

---

### Legal Disclaimer

This tool is completely **free** and is not for sale. It is an open-source, fan-made project.

* This application is **not affiliated with, endorsed by, sponsored by, or approved by ArenaNet, LLC or NCSoft Corporation**.
* "Guild Wars", "ArenaNet", and "NCSoft" are trademarks or registered trademarks of NCSoft Corporation.
* All game content, quest names, images, and wiki text displayed in this application belong to their respective owners and the Guild Wars Wiki community (licensed under GNU FDL 1.2).
* All application code was written by Akito.

---

<img width="1402" height="932" alt="image" src="https://github.com/user-attachments/assets/b1a2f6eb-e4c9-4df7-a289-ca04d937f2f0" />









