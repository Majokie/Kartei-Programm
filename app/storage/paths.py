"""Central paths. On Windows the user data is stored in %APPDATA%/Kartei-Programm,
on other systems (for now) in the data folder inside the project."""
from pathlib import Path
import os
import sys
from pathlib import Path

APP_Name = "Kartei-Programm"


def user_data_dir() -> Path:
    """Folder for the user data, depending on the operating system"""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
        return base / APP_Name
    # other systems: inside the project folder for now
    return Path(__file__).resolve().parents[2] / "data"

PROJECT_ROOT = Path(__file__).resolve().parents[2]   # .../Kartei-Programm
DATA_DIR = user_data_dir()                 # all user data lives here
DECKS_DIR = DATA_DIR / "decks"                       # one subfolder per deck
LEARNBLOCKS_DIR = DATA_DIR / "learnblocks"           # one JSON file per learn block
