"""
MTG Deck Builder v1.1 - JSON Importer (FIXED)
Importiert AllPrintings.json von MTG JSON mit korrekten Scryfall IDs
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from core.database import get_database
from core.card_manager import CardManager


class JSONImporter:
    def __init__(self, json_path=r"M:\Magic_the_gathering\AllPrintings.json"):
        self.json_path = Path(json_path)
        self.db = get_database()
        self.card_manager = CardManager()
    
    def import_all(self, progress_callback=None, update_only=False):
        """
        Importiere alle Karten aus JSON
        
        Args:
            progress_callback: Funktion(current, total, card_name)
            update_only: Wenn True, nur neue Karten importieren
        
        Returns:
            dict mit Statistiken
        """
        if not self.json_path.exists():
            return {
                'success': False,
                'error': f'JSON nicht gefunden: {self.json_path}'
            }
        
        print(f"Lade JSON... (kann 1-2 Minuten dauern)")
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {
                'success': False,
                'error': f'Fehler beim Laden: {str(e)}'
            }
        
        print(f"JSON geladen! Starte Import...")
        
        # Hole existierende Karten (für update_only)
        existing_cards = set()
        if update_only:
            cursor = self.db.execute("SELECT name, set_code, collector_number FROM cards")
            existing_cards = {(row[0], row[1], row[2]) for row in cursor.fetchall()}
            print(f"Gefunden: {len(existing_cards)} existierende Karten")
        
        imported = 0
        skipped = 0
        errors = 0
        total = 0
        
        # Zähle Gesamtanzahl
        for set_code, set_data in data['data'].items():
            total += len(set_data.get('cards', []))
        
        print(f"Importiere {total} Karten...")
        
        current = 0
        
        for set_code, set_data in data['data'].items():
            set_name = set_data.get('name', set_code)
            
            for card in set_data.get('cards', []):
                current += 1
                
                # Progress alle 500 Karten
                if progress_callback and current % 500 == 0:
                    progress_callback(current, total, card.get('name', '?'))
                
                # Skip wenn update_only und Karte existiert
                card_key = (
                    card.get('name'),
                    set_code,
                    card.get('number')
                )
                
                if update_only and card_key in existing_cards:
                    skipped += 1
                    continue
                
                # Parse Karte
                card_data = self.parse_card(card, set_code, set_name)
                
                if card_data:
                    try:
                        # Füge hinzu
                        self.card_manager.db.execute(
                            '''INSERT INTO cards 
                               (name, mana_cost, type, text, colors, image_id, 
                                set_code, set_name, rarity, artist, collector_number,
                                power, toughness, loyalty, file_path)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (
                                card_data['name'],
                                card_data['mana_cost'],
                                card_data['type'],
                                card_data['text'],
                                card_data['colors'],
                                card_data['image_id'],
                                card_data['set_code'],
                                card_data['set_name'],
                                card_data['rarity'],
                                card_data['artist'],
                                card_data['collector_number'],
                                card_data['power'],
                                card_data['toughness'],
                                card_data['loyalty'],
                                ''  # file_path leer
                            )
                        )
                        imported += 1
                        
                        # Commit alle 1000 Karten
                        if imported % 1000 == 0:
                            self.db.commit()
                            
                    except Exception as e:
                        print(f"\nFehler bei {card_data['name']}: {e}")
                        errors += 1
                else:
                    skipped += 1
        
        # Final commit
        self.db.commit()
        
        print(f"\n{'='*60}")
        print(f"Import abgeschlossen!")
        print(f"  Importiert:    {imported}")
        print(f"  Übersprungen:  {skipped}")
        print(f"  Fehler:        {errors}")
        print(f"  Gesamt:        {total}")
        
        return {
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors,
            'total': total
        }
    
    def parse_card(self, card, set_code, set_name):
        """Parse einzelne Karte aus JSON - MIT KORREKTER SCRYFALL ID"""
        try:
            # Farben
            colors = ','.join(card.get('colors', []))
            
            # Mana Cost
            mana_cost = card.get('manaCost', '')
            
            # Text (Oracle Text bevorzugt)
            text = card.get('text', '')
            
            # Type Line
            type_line = card.get('type', '')
            
            # WICHTIG: Scryfall ID aus identifiers holen
            # MTG JSON Format: identifiers.scryfallId
            identifiers = card.get('identifiers', {})
            scryfall_id = identifiers.get('scryfallId', '')
            
            # Falls nicht vorhanden, versuche uuid
            if not scryfall_id:
                scryfall_id = card.get('uuid', '')
            
            # Debug für erste paar Karten
            if not scryfall_id:
                print(f"\n⚠️  Keine Scryfall ID für: {card.get('name')} ({set_code})")
                print(f"   Verfügbare Keys: {list(card.keys())}")
                print(f"   Identifiers: {identifiers}")
            
            # Power/Toughness/Loyalty
            power = card.get('power', '')
            toughness = card.get('toughness', '')
            loyalty = card.get('loyalty', '')
            
            return {
                'name': card.get('name', 'Unknown'),
                'mana_cost': mana_cost,
                'type': type_line,
                'text': text,
                'colors': colors,
                'image_id': scryfall_id,  # Korrekte Scryfall ID!
                'set_code': set_code,
                'set_name': set_name,
                'rarity': card.get('rarity', ''),
                'artist': card.get('artist', ''),
                'collector_number': card.get('number', ''),
                'power': power,
                'toughness': toughness,
                'loyalty': loyalty
            }
            
        except Exception as e:
            print(f"\nParse-Fehler: {e}")
            print(f"Card data: {card.get('name', 'Unknown')}")
            return None


def main():
    """Standalone Ausführung"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Importiere MTG JSON')
    parser.add_argument('--update', action='store_true', 
                       help='Nur neue Karten importieren')
    parser.add_argument('--json', type=str, 
                       default=r"M:\Magic_the_gathering\AllPrintings.json",
                       help='Pfad zur JSON-Datei')
    parser.add_argument('--test', action='store_true',
                       help='Test-Modus: Zeige erste 10 Karten')
    
    args = parser.parse_args()
    
    # Test-Modus
    if args.test:
        print("TEST-MODUS: Prüfe JSON-Struktur...")
        print("="*60)
        
        with open(args.json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Zeige erste Set-Daten
        first_set = list(data['data'].keys())[0]
        print(f"\nErste Set: {first_set}")
        print(f"Set-Name: {data['data'][first_set].get('name')}")
        
        # Zeige erste Karte
        first_card = data['data'][first_set]['cards'][0]
        print(f"\nErste Karte Struktur:")
        print(f"  Name: {first_card.get('name')}")
        print(f"  Set: {first_set}")
        print(f"  Identifiers: {first_card.get('identifiers')}")
        print(f"  UUID: {first_card.get('uuid')}")
        
        print("\n✅ JSON-Struktur sieht gut aus!")
        return
    
    def progress(current, total, name):
        percent = (current / total) * 100
        print(f"\r[{percent:5.1f}%] {current}/{total}: {name[:40]:<40}", end='', flush=True)
    
    importer = JSONImporter(args.json)
    result = importer.import_all(
        progress_callback=progress,
        update_only=args.update
    )
    
    if result['success']:
        print(f"\n{'='*60}")
        print(f"✅ Erfolgreich!")
        print(f"  Importiert:    {result['imported']}")
        print(f"  Übersprungen:  {result['skipped']}")
        print(f"  Fehler:        {result.get('errors', 0)}")
    else:
        print(f"\n{'='*60}")
        print(f"❌ Fehler: {result['error']}")


if __name__ == '__main__':
    main()
