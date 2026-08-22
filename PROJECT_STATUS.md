# MTG Deck Builder - Projekt Status

## Aktuelle Version: V1.2_dev
## Vorherige: V1.1_stable (gesichert)

---

## V1.2 Komplett:
- Grid-Layout prozentual (weight + minsize)
- Mana-Symbole in Deck-Liste (links: Color Identity, rechts: Mana-Cost)
- Deck-Import aus TXT
- Deck-Export (war schon da)
- Set-Update von Scryfall (manuell, Menü: Datei > Sets aktualisieren)
- Deck umbenennen (Rechtsklick > Umbenennen)
- Multi-Select Fixes (Karte/Sideboard markieren)
- TreeView Node-State beibehalten nach Aktion
- Erfolgs-Dialoge entfernt
- Kategorie-Buttons 2 Zeilen in Preview

## V1.2 Noch Offen:
- Horizontale Scrollbar (Canvas-Lösung, komplex - für später)
- Wishlist komplett fertigstellen (DB-Spalte da, UI partial)
- CMC-Filter implementieren
- Drag & Drop instabil (bekannt, workaround: double-click/rechtsklick)

---

## AI-Assistent (Entscheidungen):
- **Ansatz: RAG (Retrieval Augmented Generation)**
  - Kartendaten aus eigener DB → an LLM senden → Antwort
  - Verhindert Hallucinations (ChatGPT erfinde Karten)
  - LLM antwortet NUR basierend auf DB-Daten
- **Prompt-Strategie:** Wird noch getestet (separater Chat)
- **Modell-Auswahl:**
  - Online: Claude API (beste Qualität)
  - Offline: Ollama (lokal, braucht GPU)
  - Ohne AI: Nur lokale Statistiken
- **User gibt eigenen API-Key ein** (keine Kosten für App)
- **Spezialisiertes MTG-Modell:** Zu aufwendig (ständig neue Sets/Regeln)

## AI Features Geplant:
- Synergie-Analyse zwischen Karten
- "Deck fehlt was?" Analyse
- Regels-Fragen beantworten
- Mana-Curve/Statistiken (lokal, kein AI nötig)

---

## V2.0+ Roadmap:
- PWA (Progressive Web App) für Mobile/Desktop
  - Service Worker für Offline
  - IndexedDB für lokale Speicherung
  - Installierbar ohne App Store
- AI Deck-Analyse (RAG + Claude/Ollama)
- Hardware-Scanner
  - Raspberry Pi + Kamera
  - Auto-Feed Mechanik (Förderband)
  - Set Symbol + Collector Number OCR
  - Einziger Desktop-Deck-Builder mit Hardware-Scanner
- AI Regels-Assistent

---

## Architektur (aktuell):
```
V1.2_dev/
├── main.py              # Entry point
├── config.py            # Zentrale Konfiguration
├── PROJECT_STATUS.md    # Dieser File
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
│   ├── import_script.py
│   ├── deck_importer.py      # NEU V1.2
│   ├── set_updater.py        # NEU V1.2
│   ├── tree_builder.py
│   ├── bulk_image_downloader.py
│   ├── download_mana_symbols.py
│   ├── import_json.py
│   └── add_wishlist_column.py
└── data/
    ├── mtg_cards.db
    ├── card_images/
    └── mana_symbols/
```

## Technische Hinweise:
- SQLite: **Neue DB-Verbindung pro Thread!** (sonst NameError)
- TreeView: Node-Names ohne Anzahl speichern für Restore
- pack_propagate(False) verhindert Icon-Anzeige
- config.py: MANA_SYMBOLS_DIR für Icons
- Mana-Symbole: RGBA Mode, transparenter Hintergrund
- Grid-Layout: weight = Verhältnis Extra-Platz, minsize = Minimum in Pixel
- Fenster: 1920x1080, minsize gesetzt

## Lizenz/Legal:
- Scryfall Bilder: Kostenlos für nicht-kommerziell
- WotC Fan Content Policy: Kostenlos ok, Werbung = Grauzone
- App-Name: Nicht "MTG" nutzen (Trademark)
- Bei Erfolg: WotC Official Partner Program kontaktieren

## Dependencies:
- Pillow (PIL)
- requests
- tkinter (stdlib)
- sqlite3 (stdlib)
- Futur: anthropic / ollama (für AI)
