# MTG Deck Builder v1.1

Modulare Magic: The Gathering Deck-Building App mit Sammlungsverwaltung.

## Installation

### 1. Projekt-Struktur erstellen

```
mtg_deck_builder_v1_1/
├── main.py
├── config.py
├── README.md
│
├── core/
│   ├── __init__.py (leer)
│   ├── database.py
│   ├── card_manager.py
│   ├── collection_manager.py
│   ├── deck_manager.py
│   ├── card_parser.py
│   └── image_handler.py
│
├── utils/
│   ├── __init__.py (leer)
│   ├── import_script.py
│   └── tree_builder.py
│
├── gui/
│   ├── __init__.py (leer)
│   └── main_window.py
│
├── ai/ (für später)
│   └── __init__.py (leer)
│
└── data/ (wird automatisch erstellt)
    ├── mtg_cards.db
    └── images/
```

### 2. Abhängigkeiten installieren

```bash
python -m pip install pillow requests
```

### 3. config.py anpassen

Öffne `config.py` und passe die Pfade an:

```python
# Deine Markdown-Dateien
MTG_FOLDER = r"M:\Magic_the_gathering\MTG"

# Deine lokalen Bilder (optional)
LOCAL_IMAGES = r"M:\Magic_the_gathering\MTG_App\Images"
```

### 4. Leere __init__.py Dateien erstellen

In jedem Unterordner (`core/`, `utils/`, `gui/`, `ai/`) muss eine leere Datei `__init__.py` existieren.

Windows CMD:
```cmd
type nul > core\__init__.py
type nul > utils\__init__.py
type nul > gui\__init__.py
type nul > ai\__init__.py
```

Linux/Mac:
```bash
touch core/__init__.py utils/__init__.py gui/__init__.py ai/__init__.py
```

### 5. App starten

```bash
python main.py
```

## Erste Schritte

1. **Beim ersten Start**: Karten importieren (dauert 2-5 Minuten für 33k Karten)
2. **Suche**: Karten nach Name/Text/Typ suchen
3. **Filter**: "Nur eigene Karten" aktivieren
4. **Decks**: Neues Deck erstellen
5. **Besitz markieren**: In Sammlung → Statistiken

## Features

### Aktuell implementiert:
- ✅ Karten-Import aus Markdown-Dateien
- ✅ Schnelle Suche (Name, Text, Typ)
- ✅ Besitz-Verwaltung (owned, quantity)
- ✅ Deck-Verwaltung (erstellen, Karten hinzufügen)
- ✅ Doppelkarten-Support
- ✅ Bilder-Caching (lokal + Scryfall)
- ✅ Tags für Baumstruktur

### In Entwicklung:
- 🚧 Baumstruktur-Browser (Farbe/Typ/Alphabet)
- 🚧 Erweiterte Filter (CMC, Farben, etc.)
- 🚧 Kartendetails-Panel mit Bildern
- 🚧 Deck-Statistiken (Mana-Kurve, etc.)

### Geplant:
- 📋 KI-Integration (Ollama/Groq)
- 📋 Deck-Analyse
- 📋 Synergie-Finder
- 📋 Export/Import (Archidekt, Moxfield)
- 📋 Rechtsklick-Kontextmenü

## Modul-Beschreibungen

### core/
Kern-Logik ohne GUI-Abhängigkeit

- `database.py` - SQLite Verbindung, Schema
- `card_manager.py` - Karten suchen, laden, CRUD
- `collection_manager.py` - Besitz-Verwaltung
- `deck_manager.py` - Deck-Verwaltung, Statistiken
- `card_parser.py` - Markdown parsen, Tags extrahieren
- `image_handler.py` - Bilder laden/cachen

### utils/
Hilfsfunktionen und Scripts

- `import_script.py` - Bulk-Import von Karten
- `tree_builder.py` - Baumstruktur generieren

### gui/
Benutzeroberfläche (Tkinter)

- `main_window.py` - Haupt-Fenster, Tabs

### config.py
Zentrale Konfiguration (Pfade, Einstellungen)

## Datenbank-Schema

```sql
cards (
    id, name, mana_cost, type, text, colors, 
    image_id, file_path, notes, owned, quantity
)

card_tags (
    card_id, tag
)

decks (
    id, name, created_at
)

deck_cards (
    deck_id, card_id, role, quantity
)
```

## Troubleshooting

### Import funktioniert nicht
- Prüfe ob `MTG_FOLDER` Pfad korrekt ist
- Prüfe ob Markdown-Dateien existieren

### Bilder werden nicht geladen
- Prüfe Internetverbindung (Scryfall)
- Prüfe ob `LOCAL_IMAGES` Pfad korrekt ist

### Module nicht gefunden
- Prüfe ob `__init__.py` Dateien existieren
- Starte App aus dem richtigen Ordner

### Datenbank-Fehler
- Lösche `data/mtg_cards.db` und importiere neu

## Lizenz

Privates Projekt - Keine Lizenz
