# MTG Deck Builder v1.1 - Vollständige Code-Analyse

## 📋 Übersicht

Eine umfassende Magic: The Gathering Deck-Building-Anwendung in Python mit Tkinter. Die App ermöglicht Kartenverwaltung, Deck-Erstellung, Sammlungsverwaltung und visuelle Deck-Vorschau.

## 🏗️ Architektur

### Projektstruktur

```
MTG_Deck_Builder/
├── core/                          # Kerngeschäftslogik
│   ├── card_manager.py            # Kartensuche, Filter, CRUD
│   ├── card_parser.py             # Markdown-Parser für Kartendaten
│   ├── collection_manager.py      # Besitzverwaltung
│   ├── database.py                # SQLite Datenbank-Manager
│   ├── deck_manager.py            # Deck-Verwaltung
│   └── image_handler.py           # Bildverwaltung & Cache
├── gui/                           # Benutzeroberfläche
│   ├── cards_panel.py             # Spalte 1: Kartensuche
│   ├── details_panel.py           # Spalte 2: Kartendetails
│   ├── workspace_panel.py         # Spalte 3: Arbeitsbereich
│   ├── preview_panel.py           # Spalte 4: Visuelle Vorschau
│   ├── decks_panel.py             # Spalte 5: Alle Decks
│   ├── dialogs.py                 # Dialog-Fenster
│   └── main_window.py             # Hauptfenster
└── utils/                         # Hilfsfunktionen
    ├── color_identity.py          # Farbidentität-Helper
    └── import_script.py           # Karten-Import
```

---

## 🗄️ Datenbankschema

### Tabelle: `cards`

```sql
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mana_cost TEXT,
    type TEXT,
    text TEXT,
    colors TEXT,
    image_id TEXT,              -- Scryfall Image ID
    file_path TEXT,
    notes TEXT,
    owned INTEGER DEFAULT 0,
    quantity INTEGER DEFAULT 0,
    set_code TEXT,
    set_name TEXT,
    rarity TEXT,
    artist TEXT,
    collector_number TEXT,
    power TEXT,
    toughness TEXT,
    loyalty TEXT
)
```

**Indizes:**
- `idx_card_name` auf `name`
- `idx_card_type` auf `type`
- `idx_card_colors` auf `colors`
- `idx_card_owned` auf `owned`
- `idx_card_set` auf `set_code`
- `idx_card_rarity` auf `rarity`
- `idx_image_id` auf `image_id`

### Tabelle: `card_tags`

```sql
CREATE TABLE card_tags (
    card_id INTEGER,
    tag TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
)
```

**Tags-Beispiele:** `'white'`, `'creature'`, `'flying'`, `'legendary'`, `'alpha_a_d'`

### Tabelle: `decks`

```sql
CREATE TABLE decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Tabelle: `deck_cards`

```sql
CREATE TABLE deck_cards (
    deck_id INTEGER,
    card_id INTEGER,
    role TEXT DEFAULT 'card',      -- 'card', 'commander', 'sideboard'
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
)
```

---

## 🔧 Core-Module im Detail

### 1. CardManager (`core/card_manager.py`)

**Zweck:** Zentrale Kartenverwaltung

**Hauptfunktionen:**

```python
search_cards(search_term, filters)  # Erweiterte Suche
get_card(card_id)                   # Einzelne Karte abrufen
is_double_faced(image_id)           # DFC-Karten erkennen
add_tags(card_id, tags)             # Tag-Verwaltung
update_notes(card_id, notes)        # Notizen speichern
```

**Such-Features:**
- Multi-Term-Suche (AND-Verknüpfung)
- Set-Code + Collector-Number Suche (z.B. "M21 123")
- Suche in Name, Text, Typ, Set-Code
- Filter nach Farben, Typen, Besitz
- Automatisches Debouncing (500ms Verzögerung)

**Beispiel:**
```python
# Suche nach "lightning bolt"
results = card_manager.search_cards("lightning bolt")

# Suche mit Filtern
results = card_manager.search_cards(
    "creature", 
    filters={'colors': ['R'], 'owned': 'only'}
)

# Set + Number Suche
results = card_manager.search_cards("M21 148")
```

---

### 2. CollectionManager (`core/collection_manager.py`)

**Zweck:** Verwaltung des Kartenbesitzes

**Hauptfunktionen:**

```python
mark_owned(card_id, owned=True, quantity=1)
set_quantity(card_id, quantity)
get_owned_cards()
get_collection_stats()              # Statistiken
mark_wishlist(card_id, wishlist=True)  # Wunschliste
```

**Statistiken-Beispiel:**
```python
stats = collection_manager.get_collection_stats()
# Returns:
{
    'total_cards': 5000,
    'owned_cards': 1200,
    'total_quantity': 2500,
    'by_color': {'W': 200, 'U': 180, ...},
    'by_type': {'Creature': 500, 'Instant': 200, ...}
}
```

---

### 3. DeckManager (`core/deck_manager.py`)

**Zweck:** Deck-Erstellung und -Verwaltung

**Hauptfunktionen:**

```python
create_deck(name)
add_card_to_deck(deck_id, card_id, role, quantity)
remove_card_from_deck(deck_id, card_id)
change_card_role(deck_id, card_id, new_role)
get_deck_stats(deck_id)
check_ownership(deck_id)            # Welche Karten fehlen?
```

**Deck-Statistiken:**
```python
stats = deck_manager.get_deck_stats(deck_id)
# Returns:
{
    'total_cards': 100,
    'unique_cards': 75,
    'commanders': ['Omnath, Locus of Creation'],
    'mainboard': 99,
    'sideboard': 0,
    'colors': {'W': 10, 'U': 15, ...},
    'types': {'Creature': 30, 'Instant': 12, ...},
    'owned_percentage': 85.5
}
```

---

### 4. ImageHandler (`core/image_handler.py`)

**Zweck:** Bildverwaltung mit lokalem Cache und Scryfall-Download

**Funktionsweise:**
1. Prüfe lokalen Cache (`data/card_images/`)
2. Prüfe lokale Bilder (falls konfiguriert)
3. Download von Scryfall API
4. Cache für zukünftige Nutzung

**Hauptfunktionen:**

```python
get_image_path(card_name, image_id, face='front')
download_from_scryfall(image_id, face)
preload_images(card_list, callback)  # Batch-Download
clear_cache()
get_cache_size()                     # Cache-Größe in MB
```

**Scryfall-URL-Format:**
```
https://api.scryfall.com/cards/{image_id}?format=image&face={face}
```

---

### 5. CardParser (`core/card_parser.py`)

**Zweck:** Parsen von Markdown-Kartendateien

**Markdown-Format:**
```markdown
# Lightning Bolt

**ManaCost:** {R}
**Type:** Instant
**Text:**
Lightning Bolt deals 3 damage to any target.

**Colors:** R
**ImageID:** abc123-def456-ghi789
```

**Tag-Extraktion:**
- Farben: `'white'`, `'blue'`, `'multicolor_rw'`
- Typen: `'creature'`, `'instant'`, `'legendary'`
- Fähigkeiten: `'flying'`, `'haste'`, `'lifelink'`
- Alphabet: `'alpha_a_d'`, `'alpha_e_h'`, etc.

---

## 🖥️ GUI-Module im Detail

### Layout-Struktur

```
┌─────────────────────────────────────────────────────────────┐
│                      Menüleiste                             │
├──────┬──────────┬────────────┬────────────┬─────────────────┤
│      │          │            │            │                 │
│  1   │    2     │     3      │     4      │        5        │
│      │          │            │            │                 │
│Karten│ Details  │Arbeits-    │  Visuelle  │  Alle Decks    │
│Suche │          │ bereich    │  Vorschau  │                 │
│      │          │            │            │                 │
│      │          │            │            │                 │
└──────┴──────────┴────────────┴────────────┴─────────────────┘
```

### 1. CardsPanel (Spalte 1)

**Features:**
- Live-Suche mit 500ms Debouncing
- Zufällige Karten laden
- Nur Legendary Creatures laden
- Filter "Nur eigene Karten"
- Drag & Drop-Unterstützung
- Doppelklick zum Hinzufügen
- Rechtsklick-Kontextmenü

**Besonderheiten:**
```python
# Drag-Detection mit Threshold
self.drag_threshold = 5  # Pixel

# Unterscheidung zwischen Click und Drag
if dx > threshold or dy > threshold:
    self.is_dragging = True
```

---

### 2. DetailsPanel (Spalte 2)

**Anzeige:**
- Kartenbild (Vorder- und Rückseite bei DFC)
- Kartentext (Read-Only)
- Notizen (Editierbar, Auto-Save)
- Besitzstatus
- Wunschlistenstatus

**Bild-Laden:**
```python
# Threading für nicht-blockierendes Laden
threading.Thread(target=load_image, daemon=True).start()

# Wichtig: Image-Referenz halten!
label.image = photo  # Verhindert Garbage Collection
```

---

### 3. WorkspacePanel (Spalte 3)

**Struktur:**
- TreeView mit hierarchischer Darstellung
- Gruppierung nach Kartentypen
- Anzeige der Gesamtanzahl pro Gruppe
- Multi-Select-Unterstützung

**Gruppen:**
```
📁 Commander (1)
📁 Creatures (35)
📁 Instants (10)
📁 Sorceries (8)
📁 Enchantments (7)
📁 Artifacts (12)
📁 Planeswalkers (3)
📁 Lands (37)
📁 Sideboard (0)
```

**Export-Format:**
```
# Deck Name
# Exportiert: 2025-01-28

## Commander
1 Omnath, Locus of Creation (ZNR)
   Mana: {R}{G}{W}{U}
   Type: Legendary Creature — Elemental
   Text: When Omnath enters...

## Creatures (35)
1 Avenger of Zendikar (C18)
   Mana: {5}{G}{G}
   ...
```

---

### 4. VisualPreviewPanel (Spalte 4)

**Features:**
- Commander-Bereich (immer sichtbar)
- Kategorien-Buttons mit Emojis
- 3-Spalten-Grid-Layout
- Asynchrones Bild-Laden
- Mousewheel-Scrolling

**Kategorien:**
- 🦎 Creatures
- ⚡ Instants
- 🔥 Sorceries
- ✨ Enchantments
- ⚙️ Artifacts
- 👤 Planeswalkers
- 🏔️ Lands
- 📦 Sideboard

**Scrolling-Implementierung:**
```python
# Plattformübergreifend
if event.num == 5 or event.delta < 0:  # Scroll down
    self.canvas.yview_scroll(1, 'units')
elif event.num == 4 or event.delta > 0:  # Scroll up
    self.canvas.yview_scroll(-1, 'units')
```

---

### 5. DecksPanel (Spalte 5)

**Features:**
- Anzeige aller Decks
- Mana-Symbol-Icons für Commander
- Hover-Effekte
- Doppelklick zum Laden
- Rechtsklick-Menü

**Icon-System:**
```python
# Icons aus data/mana_symbols/
# W.png, U.png, B.png, R.png, G.png, C.png
```

---

## 🔄 Hauptworkflow

### Deck erstellen und bearbeiten

```
1. Datei > Neues Deck
   ↓
2. Karten suchen (Spalte 1)
   ↓
3. Karte per Doppelklick oder Drag&Drop hinzufügen
   ↓
4. Im Arbeitsbereich (Spalte 3) organisieren
   ↓
5. Rolle ändern (Commander/Sideboard)
   ↓
6. Export als .txt Datei
```

### Rechtsklick-Menüs

**Karten-Liste:**
- Neues Deck mit dieser Karte
- Zu Arbeitsbereich hinzufügen
- Zu Deck hinzufügen...
- ✓ Im Besitz markieren
- ⭐ Zur Wunschliste

**Arbeitsbereich (Einzelauswahl):**
- Aus Deck entfernen
- Als Commander markieren
- Als Sideboard markieren
- Als Karte markieren
- ✓ Im Besitz markieren
- ⭐ Zur Wunschliste

**Arbeitsbereich (Multi-Select):**
- ✓ N Karten als Besitz markieren
- ⭐ N zur Wunschliste
- ✕ N Karten aus Deck entfernen

**Deck-Liste:**
- 👁️ Vorschau anzeigen
- ✏️ Deck umbenennen
- 🗑️ Deck löschen

---

## 🐛 Bekannte Probleme & TODO

### Aktuelle Einschränkungen

1. **Wishlist-Feature teilweise implementiert**
   - Datenbank-Spalte fehlt noch
   - UI vorhanden, Backend-Logik unvollständig

2. **CMC-Filter nicht implementiert**
   - In `search_cards()` als TODO markiert
   - Mana-Cost-Parsing existiert, aber nicht genutzt

3. **Drag & Drop unvollständig**
   - Drag-Detection funktioniert
   - Drop-Zonen reagieren nicht zuverlässig

4. **Fehlende Validierung**
   - Keine Prüfung auf doppelte Commander
   - Keine Deck-Size-Validierung

### Verbesserungspotenzial

**Performance:**
```python
# PROBLEM: Sequentielle Bildabfragen
for card in cards:
    image_path = get_image_path(...)  # Blocking

# LÖSUNG: Batch-Preloading
image_handler.preload_images(cards, callback=update_progress)
```

**Fehlerbehandlung:**
```python
# Aktuell:
try:
    img = Image.open(path)
except:
    pass  # Stummes Ignorieren

# Besser:
try:
    img = Image.open(path)
except FileNotFoundError:
    logger.warning(f"Image not found: {path}")
    show_placeholder()
except Exception as e:
    logger.error(f"Failed to load image: {e}")
```

---

## 📦 Abhängigkeiten

```python
# Standard Library
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext, filedialog
import sqlite3
import threading
import random
import re
from pathlib import Path

# Third-Party
from PIL import Image, ImageTk  # Pillow
import requests               # Für Scryfall-Downloads
```

**Installation:**
```bash
pip install Pillow requests
```

---

## ⚙️ Konfiguration

**Erforderliche `config.py`:**
```python
from pathlib import Path

# Pfade
DB_PATH = Path("data/mtg_cards.db")
IMAGE_DIR = Path("data/card_images")
LOCAL_IMAGES = None  # Optional: Path("D:/MTG/Images")

# Scryfall API
SCRYFALL_IMAGE_URL = "https://api.scryfall.com/cards/{image_id}?format=image&face={face}"

# UI
CARD_IMAGE_SIZE = (223, 311)  # Normalgröße
```

**Verzeichnisstruktur:**
```
project/
├── config.py
├── main.py
├── core/
├── gui/
├── utils/
└── data/
    ├── mtg_cards.db
    ├── card_images/          # Cache
    └── mana_symbols/         # W.png, U.png, etc.
```

---

## 🎯 Verwendungsbeispiele

### 1. App starten

```python
import tkinter as tk
from gui.main_window import MainWindow

root = tk.Tk()
root.title("MTG Deck Builder v1.1")
root.geometry("1600x900")

app = MainWindow(root)
root.mainloop()
```

### 2. Karten importieren

```python
from utils.import_script import CardImporter

importer = CardImporter()
result = importer.import_all_cards(
    clear_existing=True,
    progress_callback=lambda curr, total, name: print(f"{curr}/{total}: {name}")
)

print(f"Imported {result['imported']} cards")
```

### 3. Programmatisch Deck erstellen

```python
from core.deck_manager import DeckManager
from core.card_manager import CardManager

deck_mgr = DeckManager()
card_mgr = CardManager()

# Deck erstellen
deck_id = deck_mgr.create_deck("Mono Red Aggro")

# Commander hinzufügen
commander = card_mgr.get_card_by_name("Purphoros, God of the Forge")
deck_mgr.add_card_to_deck(deck_id, commander['id'], role='commander', quantity=1)

# Karten hinzufügen
for _ in range(30):
    mountain = card_mgr.get_card_by_name("Mountain")
    deck_mgr.add_card_to_deck(deck_id, mountain['id'], role='card', quantity=1)
```

---

## 🔒 Best Practices im Code

### 1. Singleton-Pattern für Datenbank

```python
_db_instance = None

def get_database():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
```

### 2. Callback-Pattern für Panel-Kommunikation

```python
# MainWindow definiert Callbacks
self.cards_panel = CardsPanel(
    parent=col1,
    card_manager=self.card_manager,
    on_card_select=self.on_card_select,     # Callback
    on_right_click=self.on_cards_right_click  # Callback
)

# Panel ruft Callback auf
def on_select(self, event):
    if self.on_card_select_callback:
        self.on_card_select_callback(card_id)
```

### 3. Threading für I/O-Operationen

```python
def load_and_display_image(self, card_name, image_id, face, label):
    def load_thread():
        # Blocking I/O hier
        image_path = self.image_handler.get_image_path(...)
        # ...
        label.config(image=photo)
        label.image = photo
    
    threading.Thread(target=load_thread, daemon=True).start()
```

### 4. Debouncing für Suche

```python
def schedule_search(self):
    if self.search_timer:
        self.parent.after_cancel(self.search_timer)
    self.search_timer = self.parent.after(500, self.do_search)
```

---

## 🚀 Erweiterungsmöglichkeiten

### 1. Erweiterte Statistiken

```python
# deck_manager.py
def get_mana_curve(self, deck_id):
    """Mana-Curve-Analyse"""
    cards = self.get_deck_cards(deck_id)
    curve = {i: 0 for i in range(8)}
    
    for card in cards:
        cmc = parse_cmc(card['mana_cost'])
        if cmc >= 7:
            curve[7] += card['deck_quantity']
        else:
            curve[cmc] += card['deck_quantity']
    
    return curve
```

### 2. Deck-Validierung

```python
def validate_commander_deck(self, deck_id):
    """Prüfe Commander-Format-Regeln"""
    cards = self.get_deck_cards(deck_id)
    errors = []
    
    # Genau 1 Commander
    commanders = [c for c in cards if c['role'] == 'commander']
    if len(commanders) != 1:
        errors.append("Genau 1 Commander erforderlich")
    
    # 100 Karten total
    total = sum(c['deck_quantity'] for c in cards if c['role'] != 'sideboard')
    if total != 100:
        errors.append(f"100 Karten erforderlich (aktuell: {total})")
    
    # Farbidentität
    if commanders:
        identity = get_color_identity(commanders[0])
        for card in cards:
            if not check_color_identity(card, identity):
                errors.append(f"{card['name']} nicht in Farbidentität")
    
    return errors
```

### 3. Import von Decklist-Formaten

```python
def import_from_moxfield(url):
    """Import von Moxfield.com"""
    response = requests.get(f"{url}/api/v1/decks")
    data = response.json()
    
    deck_id = create_deck(data['name'])
    
    for card in data['commanders']:
        add_card_to_deck(deck_id, find_card(card['name']), 'commander')
    
    for card in data['mainboard']:
        add_card_to_deck(deck_id, find_card(card['name']), 'card', card['quantity'])
```

### 4. Proxy-Druck-Feature

```python
def generate_proxy_sheet(deck_id, cards_per_page=9):
    """Erstelle druckbare Proxy-Seite"""
    from PIL import Image
    
    cards = get_deck_cards(deck_id)
    sheet = Image.new('RGB', (2480, 3508))  # A4 300dpi
    
    # Grid: 3x3
    for i, card in enumerate(cards[:9]):
        img = load_card_image(card)
        x = (i % 3) * 826
        y = (i // 3) * 1169
        sheet.paste(img, (x, y))
    
    sheet.save(f"proxy_sheet_{deck_id}.pdf")
```

---

## 📚 Zusammenfassung

**Stärken:**
- ✅ Saubere Trennung von Core-Logik und GUI
- ✅ Robuste Datenbankstruktur mit Indizes
- ✅ Asynchrones Bild-Laden
- ✅ Umfangreiche Such-Funktionalität
- ✅ Intuitive 5-Spalten-UI

**Verbesserungsbedarf:**
- ⚠️ Wishlist-Feature finalisieren
- ⚠️ Drag & Drop vervollständigen
- ⚠️ Fehlerbehandlung verbessern
- ⚠️ Unit-Tests hinzufügen
- ⚠️ Logging implementieren

**Geschätzte Codezeilen:** ~2500 LOC

---

## 📄 Lizenz & Danksagungen

**Scryfall API:** Kartenbilder und Daten von [Scryfall.com](https://scryfall.com)
**Wizards of the Coast:** Magic: The Gathering ist ein eingetragenes Warenzeichen
