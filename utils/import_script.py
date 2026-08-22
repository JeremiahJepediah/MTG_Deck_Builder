"""
MTG Deck Builder v1.1 - Import Script
Importiert alle Markdown-Dateien in die Datenbank
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import MTG_FOLDER, IMPORT_BATCH_SIZE
from core.database import get_database
from core.card_parser import CardParser
from core.card_manager import CardManager


class CardImporter:
    def __init__(self):
        self.db = get_database()
        self.parser = CardParser()
        self.card_manager = CardManager()
    
    def import_all_cards(self, folder_path=None, progress_callback=None, clear_existing=False):
        """
        Importiere alle Markdown-Dateien aus Ordner
        
        Args:
            folder_path: Pfad zum Ordner (default: config.MTG_FOLDER)
            progress_callback: Funktion(current, total, card_name) für Fortschritt
            clear_existing: Wenn True, lösche existierende Daten vorher
        
        Returns:
            dict mit Statistiken
        """
        folder = Path(folder_path) if folder_path else Path(MTG_FOLDER)
        
        if not folder.exists():
            return {
                'success': False,
                'error': f'Ordner nicht gefunden: {folder}'
            }
        
        # Lösche alte Daten wenn gewünscht
        if clear_existing:
            print("Lösche existierende Daten...")
            self.db.clear_all_data()
        
        # Finde alle Markdown-Dateien
        md_files = list(folder.rglob("*.md"))
        total = len(md_files)
        
        if total == 0:
            return {
                'success': False,
                'error': 'Keine Markdown-Dateien gefunden'
            }
        
        print(f"Starte Import von {total} Karten...")
        
        imported = 0
        skipped = 0
        errors = []
        
        for i, md_file in enumerate(md_files):
            try:
                # Parse Markdown
                card_data = self.parser.parse_markdown(md_file)
                
                if not card_data:
                    skipped += 1
                    continue
                
                # Extrahiere Tags
                tags = self.parser.extract_tags(card_data)
                
                # Füge Karte hinzu
                self.card_manager.add_card(card_data, tags)
                imported += 1
                
                # Fortschritt melden
                if progress_callback and (i % IMPORT_BATCH_SIZE == 0 or i == total - 1):
                    progress_callback(i + 1, total, card_data['name'])
                
            except Exception as e:
                errors.append(f"{md_file.name}: {str(e)}")
                skipped += 1
        
        print(f"\nImport abgeschlossen!")
        print(f"Importiert: {imported}")
        print(f"Übersprungen: {skipped}")
        if errors:
            print(f"Fehler: {len(errors)}")
        
        return {
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'total': total,
            'errors': errors
        }
    
    def import_single_file(self, file_path):
        """
        Importiere einzelne Markdown-Datei
        
        Returns:
            dict mit Erfolg/Fehler
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'success': False, 'error': 'Datei nicht gefunden'}
            
            card_data = self.parser.parse_markdown(file_path)
            
            if not card_data:
                return {'success': False, 'error': 'Parsen fehlgeschlagen'}
            
            tags = self.parser.extract_tags(card_data)
            card_id = self.card_manager.add_card(card_data, tags)
            
            return {
                'success': True,
                'card_id': card_id,
                'card_name': card_data['name']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reimport_card(self, card_id):
        """
        Importiere Karte neu (liest Markdown neu, aktualisiert DB)
        Nützlich wenn Markdown-Datei geändert wurde
        """
        # Hole file_path aus DB
        card = self.card_manager.get_card(card_id)
        
        if not card or not card.get('file_path'):
            return {'success': False, 'error': 'Karte oder file_path nicht gefunden'}
        
        file_path = Path(card['file_path'])
        
        if not file_path.exists():
            return {'success': False, 'error': f'Datei nicht mehr vorhanden: {file_path}'}
        
        # Parse neu
        card_data = self.parser.parse_markdown(file_path)
        
        if not card_data:
            return {'success': False, 'error': 'Parsen fehlgeschlagen'}
        
        # Update in DB
        self.db.execute(
            """UPDATE cards 
               SET name = ?, mana_cost = ?, type = ?, text = ?, colors = ?, image_id = ?
               WHERE id = ?""",
            (
                card_data['name'],
                card_data['mana_cost'],
                card_data['type'],
                card_data['text'],
                card_data['colors'],
                card_data['image_id'],
                card_id
            )
        )
        
        # Update Tags
        self.db.execute("DELETE FROM card_tags WHERE card_id = ?", (card_id,))
        tags = self.parser.extract_tags(card_data)
        self.card_manager.add_tags(card_id, tags)
        
        self.db.commit()
        
        return {'success': True, 'card_name': card_data['name']}


# Standalone-Ausführung für Tests
if __name__ == '__main__':
    def progress(current, total, name):
        print(f"[{current}/{total}] {name}")
    
    importer = CardImporter()
    result = importer.import_all_cards(progress_callback=progress)
    
    print(f"\n{'='*50}")
    print(f"Ergebnis: {result}")
