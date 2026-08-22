# MTG Deck Builder - Fehlende Dateien & Setup

## 📋 Übersicht

Basierend auf dem hochgeladenen Code fehlen noch einige Dateien für die vollständige Funktionalität.

---

## ❌ Fehlende Core-Dateien

### 1. `config.py` (KRITISCH)

**Pfad:** `config.py` (Root-Verzeichnis)

**Inhalt:**
```python
from pathlib import Path

# === Pfade ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "mtg_cards.db"
IMAGE_DIR = DATA_DIR / "card_images"

# Optional: Lokaler Bilder-Ordner
LOCAL_IMAGES = None  # z.B. Path("D:/MTG_Images")

# === Scryfall API ===
SCRYFALL_IMAGE_URL = "https://api.scryfall.com/cards/{image_id}?format=image&face={face}"

# === UI Settings ===
CARD_IMAGE_SIZE = (223, 311)  # Standard MTG-Kartengröße (Pixel)

# === Import Settings ===
IMPORT_BATCH_SIZE = 100  # Karten pro Batch beim Import

# === Cache Settings ===
MAX_CACHE_SIZE_MB = 500  # Maximale Cache-Größe in MB
```

---

### 2. `utils/color_identity.py` (WICHTIG)

**Pfad:** `utils/color_identity.py`

**Zweck:** Commander-Farbidentität berechnen

**Inhalt:**
```python
"""
Farbidentität-Helper für Commander-Decks
"""

def get_color_identity(card):
    """
    Berechne Farbidentität einer Karte (für Commander)
    
    Args:
        card: dict mit Kartendaten
    
    Returns:
        list: Farben als ['W', 'U', 'B', 'R', 'G'] (sortiert)
    """
    colors = set()
    
    # Farben aus colors-Feld
    card_colors = card.get('colors', '').strip()
    if card_colors:
        for c in card_colors.split(','):
            c = c.strip()
            if c in ['W', 'U', 'B', 'R', 'G', 'C']:
                colors.add(c)
    
    # Farben aus Mana-Cost extrahieren
    mana_cost = card.get('mana_cost', '')
    for symbol in ['{W}', '{U}', '{B}', '{R}', '{G}']:
        if symbol in mana_cost:
            colors.add(symbol[1])
    
    # Farben aus Text extrahieren (z.B. "Add {G}")
    text = card.get('text', '')
    for symbol in ['{W}', '{U}', '{B}', '{R}', '{G}']:
        if symbol in text:
            colors.add(symbol[1])
    
    # Sortiere nach WUBRG-Reihenfolge
    order = ['W', 'U', 'B', 'R', 'G', 'C']
    sorted_colors = [c for c in order if c in colors]
    
    return sorted_colors


def format_color_identity(colors):
    """
    Formatiere Farbidentität für Anzeige
    
    Args:
        colors: list wie ['W', 'U']
    
    Returns:
        str: z.B. "Azorius (WU)" oder "Mono White" oder "5-Color"
    """
    if not colors or colors == ['C']:
        return "Colorless"
    
    if len(colors) == 1:
        names = {
            'W': "Mono White",
            'U': "Mono Blue",
            'B': "Mono Black",
            'R': "Mono Red",
            'G': "Mono Green"
        }
        return names.get(colors[0], "Mono")
    
    if len(colors) == 2:
        # Guild-Namen
        guilds = {
            ('W', 'U'): "Azorius",
            ('U', 'B'): "Dimir",
            ('B', 'R'): "Rakdos",
            ('R', 'G'): "Gruul",
            ('G', 'W'): "Selesnya",
            ('W', 'B'): "Orzhov",
            ('U', 'R'): "Izzet",
            ('B', 'G'): "Golgari",
            ('R', 'W'): "Boros",
            ('G', 'U'): "Simic"
        }
        key = tuple(sorted(colors, key=lambda x: ['W', 'U', 'B', 'R', 'G'].index(x)))
        name = guilds.get(key, "")
        return f"{name} ({''.join(colors)})"
    
    if len(colors) == 3:
        # Shard/Wedge-Namen
        shards = {
            ('W', 'U', 'B'): "Esper",
            ('U', 'B', 'R'): "Grixis",
            ('B', 'R', 'G'): "Jund",
            ('R', 'G', 'W'): "Naya",
            ('G', 'W', 'U'): "Bant",
            ('W', 'B', 'R'): "Mardu",
            ('U', 'R', 'W'): "Jeskai",
            ('B', 'G', 'U'): "Sultai",
            ('R', 'W', 'B'): "Abzan",
            ('G', 'U', 'R'): "Temur"
        }
        key = tuple(sorted(colors, key=lambda x: ['W', 'U', 'B', 'R', 'G'].index(x)))
        name = shards.get(key, "")
        return f"{name} ({''.join(colors)})"
    
    if len(colors) == 4:
        return f"4-Color ({''.join(colors)})"
    
    if len(colors) == 5:
        return "5-Color (WUBRG)"
    
    return ''.join(colors)


def check_color_identity(card, identity):
    """
    Prüfe ob Karte in Farbidentität passt
    
    Args:
        card: dict mit Kartendaten
        identity: list wie ['W', 'U']
    
    Returns:
        bool: True wenn Karte erlaubt
    """
    card_identity = get_color_identity(card)
    
    # Alle Farben der Karte müssen in Identity sein
    for color in card_identity:
        if color not in identity and color != 'C':
            return False
    
    return True
```

---

### 3. `utils/import_script.py` (WICHTIG)

**Pfad:** `utils/import_script.py`

**Zweck:** Karten in Datenbank importieren

**Minimal-Version:**
```python
"""
Karten-Import aus JSON-Dateien
"""

import json
from pathlib import Path
from core.card_manager import CardManager
from core.card_parser import CardParser


class CardImporter:
    def __init__(self):
        self.card_manager = CardManager()
        self.parser = CardParser()
    
    def import_from_json(self, json_file):
        """
        Importiere Karten aus JSON-Datei (Scryfall-Format)
        
        Args:
            json_file: Path zu JSON-Datei
        
        Returns:
            dict mit 'success', 'imported', 'error'
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported = 0
            
            # Annahme: data ist Liste von Karten
            for card_data in data:
                self.import_single_card(card_data)
                imported += 1
            
            return {
                'success': True,
                'imported': imported,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'imported': 0,
                'error': str(e)
            }
    
    def import_single_card(self, scryfall_card):
        """
        Importiere einzelne Karte aus Scryfall-Format
        
        Args:
            scryfall_card: dict mit Scryfall-Kartendaten
        """
        # Extrahiere relevante Felder
        card_data = {
            'name': scryfall_card.get('name', ''),
            'mana_cost': scryfall_card.get('mana_cost', ''),
            'type': scryfall_card.get('type_line', ''),
            'text': scryfall_card.get('oracle_text', ''),
            'colors': ','.join(scryfall_card.get('colors', [])),
            'image_id': scryfall_card.get('id', ''),
            'set_code': scryfall_card.get('set', '').upper(),
            'set_name': scryfall_card.get('set_name', ''),
            'rarity': scryfall_card.get('rarity', ''),
            'artist': scryfall_card.get('artist', ''),
            'collector_number': scryfall_card.get('collector_number', ''),
            'power': scryfall_card.get('power', ''),
            'toughness': scryfall_card.get('toughness', ''),
            'loyalty': scryfall_card.get('loyalty', '')
        }
        
        # Tags extrahieren
        tags = self.parser.extract_tags(card_data)
        
        # In Datenbank einfügen
        self.card_manager.add_card(card_data, tags)
    
    def import_all_cards(self, progress_callback=None, clear_existing=False):
        """
        Importiere alle Karten
        
        Args:
            progress_callback: Funktion(current, total, name)
            clear_existing: Lösche existierende Daten
        
        Returns:
            dict mit 'success', 'imported', 'error'
        """
        if clear_existing:
            self.card_manager.db.clear_all_data()
        
        # Hier: Eigene Logik zum Finden/Laden von Karten
        # z.B. aus Scryfall Bulk Data, lokalen JSON-Dateien, etc.
        
        return {
            'success': True,
            'imported': 0,
            'error': 'Not implemented - bitte import_from_json() nutzen'
        }
```

---

### 4. `main.py` (EINSTIEGSPUNKT)

**Pfad:** `main.py` (Root-Verzeichnis)

**Inhalt:**
```python
"""
MTG Deck Builder v1.1
Einstiegspunkt der Anwendung
"""

import tkinter as tk
from gui.main_window import MainWindow


def main():
    # Tkinter Root-Fenster
    root = tk.Tk()
    root.title("MTG Deck Builder v1.1")
    root.geometry("1600x900")
    
    # Hauptfenster erstellen
    app = MainWindow(root)
    
    # Event Loop starten
    root.mainloop()


if __name__ == "__main__":
    main()
```

---

## 🗂️ Erforderliche Verzeichnisstruktur

```
MTG_Deck_Builder/
├── main.py                  # ✓ Erstellen (siehe oben)
├── config.py                # ✓ Erstellen (siehe oben)
│
├── core/
│   ├── __init__.py          # ✓ Erstellen (leer)
│   ├── card_manager.py      # ✓ Vorhanden
│   ├── card_parser.py       # ✓ Vorhanden
│   ├── collection_manager.py# ✓ Vorhanden
│   ├── database.py          # ✓ Vorhanden
│   ├── deck_manager.py      # ✓ Vorhanden
│   └── image_handler.py     # ✓ Vorhanden
│
├── gui/
│   ├── __init__.py          # ✓ Erstellen (leer)
│   ├── main_window.py       # ✓ Vorhanden
│   ├── cards_panel.py       # ✓ Vorhanden
│   ├── details_panel.py     # ✓ Vorhanden
│   ├── workspace_panel.py   # ✓ Vorhanden
│   ├── preview_panel.py     # ✓ Vorhanden
│   ├── decks_panel.py       # ✓ Vorhanden
│   └── dialogs.py           # ✓ Vorhanden
│
├── utils/
│   ├── __init__.py          # ✓ Erstellen (leer)
│   ├── color_identity.py    # ✓ Erstellen (siehe oben)
│   └── import_script.py     # ✓ Erstellen (siehe oben)
│
└── data/                    # ✓ Erstellen (Verzeichnis)
    ├── mtg_cards.db         # Wird automatisch erstellt
    ├── card_images/         # ✓ Erstellen (Verzeichnis)
    └── mana_symbols/        # ✓ Erstellen + Icons hinzufügen
        ├── W.png
        ├── U.png
        ├── B.png
        ├── R.png
        ├── G.png
        └── C.png
```

---

## 🖼️ Mana-Symbol-Icons

### Download-Quellen

1. **Mana Font Icons:**
   - https://mana.andrewgioia.com/
   - Kostenlos, MTG-Community-Projekt

2. **Scryfall SVG Icons:**
   - https://scryfall.com/docs/api/images
   - Direkt-URLs zu SVG-Symbolen

3. **Erstellen mit Python:**

```python
# utils/download_mana_symbols.py
from PIL import Image, ImageDraw, ImageFont
import requests
from pathlib import Path

def download_scryfall_symbols():
    """Download Mana-Symbole von Scryfall"""
    colors = {
        'W': 'https://svgs.scryfall.io/card-symbols/W.svg',
        'U': 'https://svgs.scryfall.io/card-symbols/U.svg',
        'B': 'https://svgs.scryfall.io/card-symbols/B.svg',
        'R': 'https://svgs.scryfall.io/card-symbols/R.svg',
        'G': 'https://svgs.scryfall.io/card-symbols/G.svg',
        'C': 'https://svgs.scryfall.io/card-symbols/C.svg'
    }
    
    output_dir = Path("data/mana_symbols")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for color, url in colors.items():
        response = requests.get(url)
        if response.status_code == 200:
            # SVG zu PNG konvertieren (benötigt cairosvg)
            # Oder SVG direkt speichern
            svg_path = output_dir / f"{color}.svg"
            with open(svg_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ {color}.svg")

def create_simple_symbols():
    """Erstelle einfache Mana-Symbole mit PIL"""
    colors = {
        'W': (249, 250, 244),  # Weiß
        'U': (14, 104, 171),   # Blau
        'B': (21, 11, 0),      # Schwarz
        'R': (211, 32, 42),    # Rot
        'G': (0, 115, 62),     # Grün
        'C': (204, 194, 192)   # Farblos
    }
    
    output_dir = Path("data/mana_symbols")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for color, rgb in colors.items():
        # Erstelle 20x20 Kreis
        img = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Kreis zeichnen
        draw.ellipse([0, 0, 19, 19], fill=rgb)
        
        # Symbol in Mitte (vereinfacht)
        font = ImageFont.load_default()
        draw.text((7, 5), color, fill='white', font=font)
        
        # Speichern
        img.save(output_dir / f"{color}.png")
        print(f"✓ {color}.png")

if __name__ == "__main__":
    create_simple_symbols()
```

---

## 📦 Abhängigkeiten-Datei

### `requirements.txt`

```txt
# UI
Pillow>=10.0.0

# Netzwerk
requests>=2.31.0

# Optional: Erweiterte Features
# cairosvg>=2.7.0        # Für SVG → PNG Konvertierung
# matplotlib>=3.7.0      # Für Mana-Curve-Diagramme
# reportlab>=4.0.0       # Für erweiterte PDF-Generierung
```

**Installation:**
```bash
pip install -r requirements.txt
```

---

## 🚀 Ersteinrichtung - Schritt für Schritt

### 1. Verzeichnisse erstellen

```bash
# Haupt-Verzeichnis
mkdir MTG_Deck_Builder
cd MTG_Deck_Builder

# Module
mkdir core gui utils data
mkdir data/card_images data/mana_symbols

# __init__.py Dateien
touch core/__init__.py gui/__init__.py utils/__init__.py
```

### 2. Dateien kopieren

```bash
# Hochgeladene Dateien → richtige Ordner
mv card_manager.py core/
mv card_parser.py core/
mv collection_manager.py core/
mv database.py core/
mv deck_manager.py core/
mv image_handler.py core/

mv main_window.py gui/
mv cards_panel.py gui/
mv details_panel.py gui/
mv workspace_panel.py gui/
mv preview_panel.py gui/
mv decks_panel.py gui/
mv dialogs.py gui/
```

### 3. Fehlende Dateien erstellen

```bash
# Siehe Inhalte oben in diesem Dokument
nano config.py
nano utils/color_identity.py
nano utils/import_script.py
nano main.py
```

### 4. Mana-Symbole hinzufügen

```bash
# Entweder Download-Script ausführen
python utils/download_mana_symbols.py

# Oder manuell PNG-Dateien in data/mana_symbols/ kopieren
```

### 5. Erste Karten importieren

```python
# import_example.py
from utils.import_script import CardImporter
import json

# Beispiel-Karten (Scryfall-Format)
example_cards = [
    {
        "name": "Lightning Bolt",
        "mana_cost": "{R}",
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "colors": ["R"],
        "id": "abc123",  # Scryfall ID
        "set": "m21",
        "set_name": "Core Set 2021",
        "rarity": "common",
        "collector_number": "148"
    }
]

# In Datei speichern
with open("example_cards.json", "w") as f:
    json.dump(example_cards, f)

# Importieren
importer = CardImporter()
result = importer.import_from_json("example_cards.json")
print(f"Importiert: {result['imported']} Karten")
```

### 6. App starten

```bash
python main.py
```

---

## 🔧 Optional: Scryfall Bulk Data nutzen

Für eine vollständige Datenbank:

```python
# download_scryfall_bulk.py
import requests
import json

# Hole Bulk Data Info
response = requests.get("https://api.scryfall.com/bulk-data")
bulk_info = response.json()

# Finde "All Cards" Download
for item in bulk_info['data']:
    if item['type'] == 'all_cards':
        download_url = item['download_uri']
        
        print(f"Downloading {item['size']} MB...")
        
        # Download
        cards_response = requests.get(download_url)
        cards = cards_response.json()
        
        # Speichern
        with open("all_cards.json", "w", encoding='utf-8') as f:
            json.dump(cards, f)
        
        print(f"✓ {len(cards)} Karten heruntergeladen")
        break

# Dann importieren:
# importer = CardImporter()
# result = importer.import_from_json("all_cards.json")
```

**Warnung:** Scryfall Bulk Data ist ~200 MB und enthält >50.000 Karten!

---

## ✅ Checkliste vor erstem Start

- [ ] Python 3.8+ installiert
- [ ] `pip install Pillow requests` ausgeführt
- [ ] Alle Verzeichnisse erstellt
- [ ] `config.py` erstellt
- [ ] `main.py` erstellt
- [ ] `utils/color_identity.py` erstellt
- [ ] `utils/import_script.py` erstellt
- [ ] Alle `__init__.py` Dateien vorhanden
- [ ] Mana-Symbol-Icons in `data/mana_symbols/`
- [ ] Test-Karten importiert

---

## 🎯 Schnellstart mit Minimal-Setup

Falls du **sofort starten** möchtest ohne alle Dateien:

1. Erstelle nur die absolut notwendigen Dateien:
   - `config.py`
   - `main.py`
   - `utils/color_identity.py` (Dummy-Version unten)

2. **Dummy color_identity.py:**
```python
def get_color_identity(card):
    return []

def format_color_identity(colors):
    return "Unknown"

def check_color_identity(card, identity):
    return True
```

3. **Kommentiere Import-Funktion aus:**
In `gui/main_window.py` Zeile 61:
```python
# file_menu.add_command(label="Karten importieren", command=self.start_import)
```

4. **Starte App:**
```bash
python main.py
```

Die App startet dann ohne Karten, aber du kannst manuell Karten hinzufügen:

```python
from core.card_manager import CardManager

manager = CardManager()
manager.add_card({
    'name': 'Test Karte',
    'mana_cost': '{1}{R}',
    'type': 'Creature',
    'text': 'Haste',
    'colors': 'R'
})
```

---

*Letzte Aktualisierung: Januar 2025*
