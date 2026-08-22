"""
MTG Deck Builder v1.1 - Konfiguration
Zentrale Einstellungen für die gesamte App
"""



import os
from pathlib import Path

# Eigene Funktion, um die Skyfall-Requests zu parametrieren
import requests

SCRYFALL_HEADERS = {'User-Agent': 'MTGDeckBuilder/1.1 (personal project)'}

def get_scryfall_session():
    session = requests.Session()
    session.headers.update(SCRYFALL_HEADERS)
    return session

# Basis-Pfade
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "card_images"
MANA_SYMBOLS_DIR = DATA_DIR / "mana_symbols"

# Icon
ICON_PATH = BASE_DIR / "mtg_icon.ico"

# Erstelle Verzeichnisse falls nicht vorhanden
DATA_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)

# Datenbank
DB_PATH = DATA_DIR / "mtg_cards.db"

# Karten-Quellen
MTG_FOLDER = r"M:\Magic_the_gathering\MTG"  # Deine Markdown-Dateien
LOCAL_IMAGES = r"M:\Magic_the_gathering\MTG_App\card_images"

# Scryfall API
SCRYFALL_API_BASE = "https://api.scryfall.com"
SCRYFALL_IMAGE_BASE = "https://cards.scryfall.io/normal"
SCRYFALL_HEADERS = {'User-Agent': 'MTGDeckBuilder/1.1 (personal project)'}

# Baumstruktur-Einstellungen
ALPHABET_GROUPS = [
    ("A-D", ["A", "B", "C", "D"]),
    ("E-H", ["E", "F", "G", "H"]),
    ("I-L", ["I", "J", "K", "L"]),
    ("M-P", ["M", "N", "O", "P"]),
    ("Q-T", ["Q", "R", "S", "T"]),
    ("U-Z", ["U", "V", "W", "X", "Y", "Z"])
]

# Farben
COLORS = {
    "W": "White",
    "U": "Blue", 
    "B": "Black",
    "R": "Red",
    "G": "Green",
    "C": "Colorless"
}

# Mehrfarbige Gilden
MULTICOLOR_GUILDS = {
    "WU": "Azorius",
    "UB": "Dimir",
    "BR": "Rakdos",
    "RG": "Gruul",
    "GW": "Selesnya",
    "WB": "Orzhov",
    "UR": "Izzet",
    "BG": "Golgari",
    "RW": "Boros",
    "GU": "Simic"
}

# Typen für Baumstruktur
CARD_TYPES = [
    "Creature",
    "Instant",
    "Sorcery",
    "Enchantment",
    "Artifact",
    "Planeswalker",
    "Land",
    "Battle"
]

# Creature-Fähigkeiten für Unterteilung
CREATURE_ABILITIES = [
    "Flying",
    "First Strike",
    "Double Strike",
    "Deathtouch",
    "Haste",
    "Hexproof",
    "Indestructible",
    "Lifelink",
    "Menace",
    "Reach",
    "Trample",
    "Vigilance",
    "Ward"
]

# GUI Einstellungen
WINDOW_TITLE = "MTG Deck Builder v1.1"
WINDOW_SIZE = "1400x900"
CARD_IMAGE_SIZE = (300, 420)  # Breite x Höhe in Pixeln

# Import Einstellungen
IMPORT_BATCH_SIZE = 100  # Status-Update nach X Karten
