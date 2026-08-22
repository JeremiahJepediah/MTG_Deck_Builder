# MTG Deck Builder - Quick Start Guide

## 🚀 Schnelleinstieg

### Installation

1. **Abhängigkeiten installieren:**
```bash
pip install Pillow requests
```

2. **Projektstruktur erstellen:**
```
MTG_Deck_Builder/
├── main.py
├── config.py
├── core/
│   ├── __init__.py
│   ├── card_manager.py
│   ├── card_parser.py
│   ├── collection_manager.py
│   ├── database.py
│   ├── deck_manager.py
│   └── image_handler.py
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── cards_panel.py
│   ├── details_panel.py
│   ├── workspace_panel.py
│   ├── preview_panel.py
│   ├── decks_panel.py
│   └── dialogs.py
├── utils/
│   ├── __init__.py
│   ├── color_identity.py
│   └── import_script.py
└── data/
    ├── card_images/
    └── mana_symbols/
```

3. **`config.py` erstellen:**
```python
from pathlib import Path

# Pfade
DB_PATH = Path("data/mtg_cards.db")
IMAGE_DIR = Path("data/card_images")
LOCAL_IMAGES = None  # Optional: eigener Ordner mit Bildern

# Scryfall API
SCRYFALL_IMAGE_URL = "https://api.scryfall.com/cards/{image_id}?format=image&face={face}"

# UI Settings
CARD_IMAGE_SIZE = (223, 311)
```

4. **`main.py` erstellen:**
```python
import tkinter as tk
from gui.main_window import MainWindow

if __name__ == "__main__":
    root = tk.Tk()
    root.title("MTG Deck Builder v1.1")
    root.geometry("1600x900")
    
    app = MainWindow(root)
    root.mainloop()
```

### Erste Schritte

#### 1. Karten importieren

```
Datei > Karten importieren
```

Dies startet den Import-Prozess, der Karten aus JSON-Dateien oder anderen Quellen in die Datenbank lädt.

#### 2. Neues Deck erstellen

```
Datei > Neues Deck
```

Oder:
```
Rechtsklick auf Karte > Neues Deck mit dieser Karte
```

#### 3. Karten zum Deck hinzufügen

**Methode 1: Doppelklick**
- Karte in Spalte 1 suchen
- Doppelklick → wird zu geladenem Deck hinzugefügt

**Methode 2: Drag & Drop**
- Karte anklicken und ziehen
- Auf Arbeitsbereich (Spalte 3) loslassen

**Methode 3: Rechtsklick-Menü**
- Rechtsklick auf Karte
- "Zu Arbeitsbereich hinzufügen" oder "Zu Deck hinzufügen..."

#### 4. Commander festlegen

```
Rechtsklick auf Karte im Arbeitsbereich > Als Commander markieren
```

#### 5. Deck exportieren

```
Arbeitsbereich > 📄 Export
```

Erstellt eine `.txt` Datei mit vollständiger Deckliste.

---

## 🔍 Such-Tipps

### Einfache Suche
```
lightning bolt
```

### Multi-Term-Suche (AND)
```
red creature haste
```
Findet Karten, die ALLE Begriffe enthalten.

### Set + Collector Number
```
M21 148
ZNR 311
```

### Nach Besitz filtern
```
☑️ Nur eigene Karten aktivieren
```

---

## ⌨️ Tastenkombinationen

| Aktion | Shortcut |
|--------|----------|
| Karte zu Deck | Doppelklick |
| Kontextmenü | Rechtsklick |
| Multi-Select | Strg + Klick (im Arbeitsbereich) |
| Zufällige Karten | Button "Zufällig" |
| Legendary Creatures | Button "⭐ Legend" |

---

## 📊 Deck-Verwaltung

### Deck laden
- **Einfachklick** in Spalte 5: Zeigt Vorschau in Spalte 4
- **Doppelklick** in Spalte 5: Lädt Deck in Arbeitsbereich (Spalte 3)

### Deck-Vorschau nutzen
1. Deck in Spalte 5 anklicken
2. Kategorien in Spalte 4 durchklicken
3. "▶ Als aktuell laden" um in Arbeitsbereich zu laden

### Basic Lands hinzufügen
```
Arbeitsbereich > 🏔️ Lands
```
Dialog öffnet sich → Land-Typ und Anzahl wählen

---

## 🎨 Besitzverwaltung

### Karte als "im Besitz" markieren

**Methode 1:**
```
Rechtsklick auf Karte > ✓ Im Besitz markieren
```

**Methode 2:**
```
Karten-Panel (Spalte 1) > ✓ Besitz Button
```

Dialog fragt nach Anzahl (0-999).

### Zur Wunschliste hinzufügen
```
Rechtsklick auf Karte > ⭐ Zur Wunschliste
```

### Statistiken anzeigen
```python
from core.collection_manager import CollectionManager

collection = CollectionManager()
stats = collection.get_collection_stats()

print(f"Im Besitz: {stats['owned_cards']} / {stats['total_cards']}")
print(f"Total: {stats['total_quantity']} Karten")
```

---

## 🐛 Häufige Probleme

### "Kein Bild verfügbar"
- **Ursache:** Scryfall ImageID fehlt oder Download fehlgeschlagen
- **Lösung:** Prüfe Internetverbindung, warte kurz und klicke Karte erneut

### "Drag & Drop funktioniert nicht"
- **Ursache:** Bekanntes Problem, teilweise implementiert
- **Lösung:** Nutze Doppelklick oder Rechtsklick-Menü

### "Deck lässt sich nicht speichern"
- **Ursache:** Datenbank-Berechtigungen oder Pfad-Problem
- **Lösung:** Prüfe `config.py` DB_PATH und Schreibrechte

### Suche findet keine Ergebnisse
- **Ursache:** 
  - Karten noch nicht importiert
  - Falsche Schreibweise
- **Lösung:**
  - Erst Karten importieren
  - Nur Teilbegriffe verwenden

---

## 💡 Pro-Tipps

### 1. Schnelles Deck-Building
```
1. "⭐ Legend" Button → Zufällige Legendary Creatures
2. Doppelklick auf Commander
3. Dialog: "Neues Deck mit dieser Karte"
4. Karten suchen und per Doppelklick hinzufügen
5. "🏔️ Lands" für Basic Lands
```

### 2. Multi-Select im Arbeitsbereich
```
Strg + Klick auf mehrere Karten
→ Rechtsklick
→ "✓ N Karten als Besitz markieren"
```

### 3. Deck schnell klonen
```
1. Deck in Arbeitsbereich laden
2. Datei > Neues Deck (neuer Name)
3. Alle Karten erneut hinzufügen
```

### 4. Effiziente Suche
```
# Statt: "Avenger of Zendikar"
# Nutze: "avenger zen"

# Statt: "Lightning Bolt M21"
# Nutze: "M21 148" (wenn Collector Number bekannt)
```

---

## 📝 Notizen & Tipps

### Notizen zu Karten
- Notizen werden in Spalte 2 (Details) bearbeitet
- Automatisches Speichern beim Tippen
- Bleiben kartenspezifisch erhalten

### Kartenbilder
- Erste Ansicht kann langsam sein (Download)
- Danach aus Cache geladen (schnell)
- Cache: `data/card_images/`

### Deck-Export
- Format: Markdown-ähnlich
- Enthält vollständige Karteninfos
- Import in andere Tools möglich

---

## 🔧 Erweiterte Nutzung

### Programmatischer Zugriff

```python
from core.card_manager import CardManager
from core.deck_manager import DeckManager

# Alle roten Kreaturen finden
card_mgr = CardManager()
results = card_mgr.search_cards(
    "creature",
    filters={'colors': ['R']}
)

# Deck-Statistiken
deck_mgr = DeckManager()
stats = deck_mgr.get_deck_stats(deck_id)
print(f"Commander: {stats['commanders']}")
print(f"Karten: {stats['total_cards']}")
```

### Eigene Filter erstellen

Bearbeite `card_manager.py`:
```python
# Beispiel: CMC-Filter
if 'cmc_min' in filters:
    cmc_min = filters['cmc_min']
    query += " AND cmc >= ?"
    params.append(cmc_min)
```

---

## 📚 Weitere Ressourcen

- **Scryfall API Docs:** https://scryfall.com/docs/api
- **MTG Rules:** https://magic.wizards.com/en/rules
- **EDH/Commander Rules:** https://mtgcommander.net/index.php/rules/

---

## ❓ Häufig gestellte Fragen (FAQ)

**F: Kann ich Karten aus anderen Programmen importieren?**
A: Ja, über `utils/import_script.py` können JSON-Daten importiert werden.

**F: Werden meine Decks automatisch gespeichert?**
A: Ja, alle Änderungen werden sofort in der Datenbank gespeichert.

**F: Kann ich mehrere Commander haben?**
A: Technisch ja, aber Format-Validierung ist noch nicht implementiert.

**F: Wo finde ich Mana-Symbole für Icons?**
A: In `data/mana_symbols/` (W.png, U.png, B.png, R.png, G.png, C.png)

**F: Funktioniert die App offline?**
A: Ja, sobald Bilder gecacht sind. Nur Scryfall-Downloads benötigen Internet.

---

*Letzte Aktualisierung: Januar 2025*
