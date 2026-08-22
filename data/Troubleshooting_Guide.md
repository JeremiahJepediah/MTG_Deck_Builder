# MTG Deck Builder - Troubleshooting & Debugging Guide

## 🔍 Debugging-Tools

### 1. Debug-Ausgaben aktivieren

Viele Funktionen haben bereits DEBUG-Prints eingebaut:

```python
# In card_manager.py - Zeigt SQL-Queries
if search_term:
    print(f"\nDEBUG Search: '{search_term}'")
    print(f"  Final Query: {query}")
    print(f"  Params: {params}")

# In details_panel.py - Zeigt Lade-Vorgänge
print(f"DEBUG: Lade Karte: {card['name']} (Set: {card.get('set_code')})")

# In workspace_panel.py - Zeigt Rechtsklick-Events
print("DEBUG: on_tree_right_click called")
print(f"DEBUG: card_ids = {card_ids}")
```

### 2. Logging hinzufügen

Erstelle `utils/logger.py`:
```python
import logging
from pathlib import Path

def setup_logger(name='mtg_deck_builder', level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File Handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Verwendung
logger = setup_logger()
logger.info("Application started")
logger.debug(f"Loading card: {card_id}")
logger.error(f"Failed to load image: {e}")
```

---

## 🐛 Häufige Fehler & Lösungen

### Problem 1: "NameError: name 'messagebox' is not defined"

**Symptom:**
```python
NameError: name 'messagebox' is not defined in module 'cards_panel'
```

**Ursache:** Import fehlt

**Lösung:**
```python
# Am Anfang der Datei hinzufügen:
from tkinter import messagebox
```

---

### Problem 2: Wishlist-Feature wirft Fehler

**Symptom:**
```
sqlite3.OperationalError: no such column: wishlist
```

**Ursache:** Datenbank-Schema fehlt Spalte

**Lösung 1 - Migration:**
```python
# migration_add_wishlist.py
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Spalte hinzufügen
cursor.execute('ALTER TABLE cards ADD COLUMN wishlist INTEGER DEFAULT 0')
conn.commit()
conn.close()

print("✓ Wishlist-Spalte hinzugefügt")
```

**Lösung 2 - Neustart:**
```python
# Datenbank löschen und neu erstellen
from core.database import Database

db = Database()
db.clear_all_data()
# Dann Karten neu importieren
```

---

### Problem 3: Bilder werden nicht geladen

**Symptom:** Schwarze Rechtecke statt Kartenbilder

**Debugging:**
```python
# In details_panel.py temporär hinzufügen:
def load_and_display_image(self, card_name, image_id, face, label):
    print(f"DEBUG: Loading image for {card_name}")
    print(f"  ImageID: {image_id}")
    print(f"  Face: {face}")
    
    def load_thread():
        image_path = self.image_handler.get_image_path(card_name, image_id, face)
        print(f"  Path: {image_path}")
        print(f"  Exists: {image_path.exists() if image_path else False}")
        # ...
```

**Mögliche Ursachen:**
1. **ImageID fehlt:** Karte hat kein `image_id` in DB
2. **Scryfall-Fehler:** API-Limit oder Netzwerkproblem
3. **Dateiberechtigungen:** Kann nicht in Cache schreiben
4. **PIL-Fehler:** Bilddatei korrupt

**Lösungen:**
```python
# 1. Prüfe ImageID
card = card_manager.get_card(card_id)
print(f"ImageID: {card.get('image_id')}")  # Sollte nicht None/leer sein

# 2. Teste Scryfall direkt
import requests
url = f"https://api.scryfall.com/cards/{image_id}?format=image&face=front"
response = requests.get(url)
print(f"Status: {response.status_code}")  # Sollte 200 sein

# 3. Prüfe Cache-Verzeichnis
from config import IMAGE_DIR
print(f"Cache: {IMAGE_DIR}")
print(f"Exists: {IMAGE_DIR.exists()}")
print(f"Writable: {os.access(IMAGE_DIR, os.W_OK)}")

# 4. Cache leeren
from core.image_handler import ImageHandler
handler = ImageHandler()
handler.clear_cache()
```

---

### Problem 4: Drag & Drop funktioniert nicht

**Symptom:** Karten lassen sich nicht ziehen

**Debugging:**
```python
# In cards_panel.py
def on_motion(self, event):
    if self.drag_start_x is None:
        print("DEBUG: No drag start")
        return
    
    dx = abs(event.x - self.drag_start_x)
    dy = abs(event.y - self.drag_start_y)
    print(f"DEBUG: dx={dx}, dy={dy}, threshold={self.drag_threshold}")
    
    if dx > self.drag_threshold or dy > self.drag_threshold:
        print("DEBUG: Threshold reached!")
        # ...
```

**Bekanntes Problem:**
- Drag-Detection funktioniert
- Drop-Zonen reagieren inkonsistent
- Workaround: Doppelklick oder Rechtsklick-Menü nutzen

---

### Problem 5: Search Timer-Fehler

**Symptom:**
```
TclError: invalid command name "..."
```

**Ursache:** `after_cancel` auf bereits gelöschtem Widget

**Lösung:**
```python
def schedule_search(self):
    # Prüfe ob Widget noch existiert
    try:
        if self.search_timer:
            self.parent.after_cancel(self.search_timer)
    except tk.TclError:
        pass
    
    self.search_timer = self.parent.after(self.search_delay, self.do_search)
```

---

### Problem 6: Multi-Select-Menü erscheint nicht

**Symptom:** Rechtsklick auf mehrere Karten zeigt Single-Select-Menü

**Debugging:**
```python
# In workspace_panel.py
def on_tree_right_click(self, event):
    selected_items = self.tree.selection()
    print(f"DEBUG: Selected items: {selected_items}")
    print(f"DEBUG: Length: {len(selected_items)}")
    
    card_ids = []
    for sel_item in selected_items:
        tags = self.tree.item(sel_item, 'tags')
        print(f"DEBUG: Tags for {sel_item}: {tags}")
        # ...
```

**Häufige Ursache:** TreeView-Tags nicht korrekt gesetzt

**Lösung:**
```python
# In workspace_panel.py - build_tree()
# WICHTIG: Tags als tuple übergeben!
self.tree.insert(group_node, 'end', 
                text=display, 
                tags=(card['id'],))  # NICHT tags=card['id']
```

---

## 🔬 Performance-Debugging

### 1. Langsames Laden von Decks

**Problem:** Workspace/Preview braucht lange zum Laden

**Profiling:**
```python
import time

def load_deck(self, deck_id):
    start = time.time()
    
    # ... existing code ...
    
    print(f"⏱️ load_deck took {time.time() - start:.2f}s")
```

**Optimierung:**
```python
# VORHER: Sequentielle Bildabfragen
for card in cards:
    self.create_card_image(card, ...)  # Blockiert!

# NACHHER: Batch-Preloading
card_list = [{'name': c['name'], 'image_id': c['image_id']} for c in cards]
self.image_handler.preload_images(card_list)
```

### 2. Langsame Suche

**Problem:** Suche dauert mehrere Sekunden

**SQL-Query analysieren:**
```python
# In card_manager.py
import time

def search_cards(self, search_term='', filters=None):
    start = time.time()
    
    # ... build query ...
    
    cursor = self.db.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    elapsed = time.time() - start
    print(f"⏱️ Search took {elapsed:.3f}s ({len(results)} results)")
    
    return results
```

**Optimierung - Index prüfen:**
```python
# In database.py - init_database()
# Stelle sicher, dass Indizes existieren:
cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_name ON cards(name)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_card_text ON cards(text)')
```

### 3. Memory-Leak bei Bildern

**Problem:** Speicherverbrauch steigt kontinuierlich

**Debugging:**
```python
import tracemalloc

tracemalloc.start()

# ... nach einiger Nutzung ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

**Häufige Ursache:** PhotoImage-Referenzen nicht gehalten

**Lösung:**
```python
# FALSCH:
photo = ImageTk.PhotoImage(img)
label.config(image=photo)  # Wird sofort garbage-collected!

# RICHTIG:
photo = ImageTk.PhotoImage(img)
label.config(image=photo)
label.image = photo  # Referenz halten!
```

---

## 🛠️ Erweiterte Debugging-Techniken

### 1. Datenbankabfragen loggen

```python
# In database.py
class Database:
    def execute(self, query, params=None):
        # Log query
        if os.getenv('DEBUG_SQL'):
            print(f"\n📊 SQL: {query}")
            if params:
                print(f"   Params: {params}")
        
        conn = self.connect()
        cursor = conn.cursor()
        # ...
```

**Aktivieren:**
```bash
export DEBUG_SQL=1
python main.py
```

### 2. Event-Tracking

```python
# In main_window.py
class MainWindow:
    def __init__(self, root):
        # ...
        if os.getenv('DEBUG_EVENTS'):
            self.track_events()
    
    def track_events(self):
        original_bind = tk.Widget.bind
        
        def logged_bind(widget, event, func):
            def wrapper(*args, **kwargs):
                print(f"🔔 Event: {event} on {widget.__class__.__name__}")
                return func(*args, **kwargs)
            return original_bind(widget, event, wrapper)
        
        tk.Widget.bind = logged_bind
```

### 3. Callback-Tracing

```python
# In main_window.py
def on_card_select(self, card_id):
    import traceback
    if os.getenv('DEBUG_CALLBACKS'):
        print(f"\n📞 on_card_select({card_id})")
        traceback.print_stack()
    
    self.details_panel.show_card(card_id)
```

---

## 🧪 Unit-Tests erstellen

### Test-Setup

```python
# tests/test_card_manager.py
import unittest
import tempfile
from pathlib import Path
from core.database import Database
from core.card_manager import CardManager

class TestCardManager(unittest.TestCase):
    def setUp(self):
        # Temporäre Datenbank
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db = Database(self.temp_db.name)
        self.manager = CardManager()
        
        # Test-Karte einfügen
        self.manager.add_card({
            'name': 'Lightning Bolt',
            'mana_cost': '{R}',
            'type': 'Instant',
            'text': 'Deal 3 damage to any target.',
            'colors': 'R'
        })
    
    def tearDown(self):
        Path(self.temp_db.name).unlink()
    
    def test_search_by_name(self):
        results = self.manager.search_cards('lightning')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Lightning Bolt')
    
    def test_search_by_color(self):
        results = self.manager.search_cards('', filters={'colors': ['R']})
        self.assertGreater(len(results), 0)

if __name__ == '__main__':
    unittest.main()
```

**Ausführen:**
```bash
python -m unittest tests/test_card_manager.py
```

---

## 📊 Performance-Benchmarks

### Benchmark-Script

```python
# benchmark.py
import time
from core.card_manager import CardManager
from core.deck_manager import DeckManager

def benchmark_search():
    manager = CardManager()
    
    tests = [
        ("Single term", "creature"),
        ("Multi term", "red creature haste"),
        ("Set code", "M21 148"),
    ]
    
    for name, query in tests:
        start = time.time()
        results = manager.search_cards(query)
        elapsed = time.time() - start
        print(f"{name:20s}: {elapsed*1000:6.2f}ms ({len(results)} results)")

def benchmark_deck_loading():
    manager = DeckManager()
    decks = manager.get_all_decks()
    
    if not decks:
        print("No decks to benchmark")
        return
    
    deck_id = decks[0]['id']
    
    start = time.time()
    cards = manager.get_deck_cards(deck_id)
    elapsed = time.time() - start
    print(f"Load deck cards: {elapsed*1000:6.2f}ms ({len(cards)} cards)")
    
    start = time.time()
    stats = manager.get_deck_stats(deck_id)
    elapsed = time.time() - start
    print(f"Calculate stats: {elapsed*1000:6.2f}ms")

if __name__ == '__main__':
    print("=== Search Benchmarks ===")
    benchmark_search()
    print("\n=== Deck Benchmarks ===")
    benchmark_deck_loading()
```

**Beispiel-Output:**
```
=== Search Benchmarks ===
Single term         :  12.34ms (450 results)
Multi term          :  23.45ms (120 results)
Set code            :   8.12ms (1 results)

=== Deck Benchmarks ===
Load deck cards:  15.67ms (100 cards)
Calculate stats:   3.21ms
```

---

## 🔍 Fehlersuche-Checkliste

Bei Problemen diese Schritte durchgehen:

### ☑️ Basis-Checks

- [ ] Alle Abhängigkeiten installiert? (`pip list`)
- [ ] `config.py` existiert und ist korrekt?
- [ ] Datenbank-Datei existiert in `data/`?
- [ ] Logs-Verzeichnis beschreibbar?

### ☑️ Import-Probleme

- [ ] Alle `__init__.py` Dateien vorhanden?
- [ ] Relative Imports korrekt?
- [ ] `sys.path.append` wo nötig?

### ☑️ GUI-Probleme

- [ ] Tkinter korrekt installiert? (`python -m tkinter`)
- [ ] PIL/Pillow funktioniert? (`from PIL import Image`)
- [ ] Event-Bindings korrekt gesetzt?

### ☑️ Datenbank-Probleme

- [ ] Schema vollständig? (alle Tabellen/Spalten)
- [ ] Indizes erstellt?
- [ ] Fremdschlüssel-Constraints aktiv?
- [ ] Schreibrechte vorhanden?

### ☑️ Netzwerk-Probleme

- [ ] Internetverbindung aktiv?
- [ ] Scryfall API erreichbar?
- [ ] Firewall blockiert nicht?
- [ ] Rate-Limits beachtet?

---

## 📝 Debug-Log-Beispiel

Gutes Debug-Logging sollte so aussehen:

```
2025-01-28 14:32:01 - mtg_deck_builder - INFO - Application started
2025-01-28 14:32:01 - database - INFO - Connected to data/mtg_cards.db
2025-01-28 14:32:01 - database - INFO - 5234 cards in database
2025-01-28 14:32:05 - card_manager - DEBUG - Search: 'lightning'
2025-01-28 14:32:05 - card_manager - DEBUG - Query: SELECT * FROM cards WHERE name LIKE ?
2025-01-28 14:32:05 - card_manager - DEBUG - Found 15 results in 0.012s
2025-01-28 14:32:10 - details_panel - DEBUG - Loading card 1234: Lightning Bolt
2025-01-28 14:32:10 - image_handler - DEBUG - Cache hit: abc123_front.jpg
2025-01-28 14:32:15 - deck_manager - INFO - Created deck 'Mono Red Aggro' (id=42)
2025-01-28 14:32:20 - deck_manager - INFO - Added card 1234 to deck 42 (role=card, qty=4)
2025-01-28 14:32:25 - workspace_panel - DEBUG - Refreshing deck 42 (100 cards)
```

---

*Letzte Aktualisierung: Januar 2025*
