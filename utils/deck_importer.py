"""
Deck Import aus TXT-Datei
"""
import re
from pathlib import Path
from core.deck_manager import DeckManager
from core.card_manager import CardManager


class DeckImporter:
    def __init__(self):
        self.deck_manager = DeckManager()
        self.card_manager = CardManager()
    
    def import_from_txt(self, file_path):
        """
        Importiert Deck aus TXT-Datei
        
        Returns:
            dict mit 'success', 'deck_id', 'errors'
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse Deck-Name (erste Zeile mit #)
            deck_name_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            deck_name = deck_name_match.group(1) if deck_name_match else Path(file_path).stem
            
            # Erstelle Deck
            deck_id = self.deck_manager.create_deck(deck_name)
            print(f"DEBUG: deck_name = '{deck_name}'")
            print(f"DEBUG: deck_id = {deck_id}")
            if not deck_id:
                return {'success': False, 'error': 'Deck konnte nicht erstellt werden'}
            
            errors = []
            imported = 0
            
            # Parse Karten (Format: "quantity name (set_code)")
            pattern = r'^(\d+)\s+(.+?)\s+\(([^)]+)\)'
            
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip Kommentare und leere Zeilen
                if not line or line.startswith('#'):
                    continue
                
                match = re.match(pattern, line)
                if not match:
                    continue
                
                quantity = int(match.group(1))
                card_name = match.group(2).strip()
                set_code = match.group(3).strip()
                
                # Bestimme Rolle (Commander oder normal)
                role = 'card'
                if '## Commander' in content and line in content.split('## Commander')[1].split('##')[0]:
                    role = 'commander'
                elif '## Sideboard' in content and line in content.split('## Sideboard')[1].split('##')[0]:
                    role = 'sideboard'
                
                # Suche Karte in DB
                card = self.find_card(card_name, set_code)
                
                if card:
                    self.deck_manager.add_card_to_deck(deck_id, card['id'], role, quantity)
                    imported += 1
                else:
                    errors.append(f"Karte nicht gefunden: {card_name} ({set_code})")
            
            return {
                'success': True,
                'deck_id': deck_id,
                'deck_name': deck_name,
                'imported': imported,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def find_card(self, name, set_code):
        """Suche Karte nach Name und Set"""
        # Suche mit exaktem Set-Code
        cursor = self.card_manager.db.execute(
            "SELECT * FROM cards WHERE name = ? AND set_code = ? LIMIT 1",
            (name, set_code.upper())
        )
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        
        # Fallback: Nur Name (erstes Ergebnis)
        cursor = self.card_manager.db.execute(
            "SELECT * FROM cards WHERE name = ? LIMIT 1",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None