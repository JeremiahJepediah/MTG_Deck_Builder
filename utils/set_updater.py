"""
Set Update von Scryfall
"""
import requests
import time
from datetime import datetime
from core.database import get_database
from core.card_manager import CardManager
from config import get_scryfall_session

class SetUpdater:
    def __init__(self):
        self.db = get_database()
        self.card_manager = CardManager()
        self.session = get_scryfall_session()

    def check_new_sets(self):
        """
        Prüft ob neue Sets verfügbar sind

        Returns:
            list of dicts mit Set-Info
        """
        try:
            response = self.session.get("https://api.scryfall.com/sets", timeout=10)
            if response.status_code != 200:
                return []

            all_sets = response.json()['data']
            
            # Hole bereits importierte Sets
            cursor = self.db.execute("SELECT DISTINCT set_code FROM cards")
            existing_sets = {row[0].upper() for row in cursor.fetchall()}
            
            # Filtere neue Sets (nur released, nicht digital)
            new_sets = []
            for s in all_sets:
                set_code = s['code'].upper()
                released = s.get('released_at', '')
                
                # Skip wenn bereits importiert
                if set_code in existing_sets:
                    continue
                
                # Skip wenn noch nicht released
                if released > datetime.now().strftime('%Y-%m-%d'):
                    continue
                
                # Skip digitale Sets
                if s.get('digital', False):
                    continue
                
                new_sets.append({
                    'code': set_code,
                    'name': s['name'],
                    'released': released,
                    'card_count': s.get('card_count', 0)
                })
            
            # Sortiere nach Release-Datum (neueste zuerst)
            new_sets.sort(key=lambda x: x['released'], reverse=True)
            
            return new_sets
            
        except Exception as e:
            print(f"Fehler beim Abrufen der Sets: {e}")
            return []
    
    def import_set(self, set_code, progress_callback=None):
        """Importiert ein Set von Scryfall"""
        try:
            # DB-Verbindung im aktuellen Thread erstellen
            from core.database import Database
            db = Database()  # Neue Verbindung für diesen Thread
            
            # Hole alle Karten des Sets
            url = f"https://api.scryfall.com/cards/search?q=set:{set_code}&unique=prints"
            cards = []
            
            while url:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    return {'success': False, 'error': f'Scryfall API Error: {response.status_code}'}
                
                data = response.json()
                cards.extend(data['data'])
                url = data.get('next_page')
            
            if not cards:
                return {'success': False, 'error': 'Keine Karten gefunden'}
            
            imported = 0
            errors = []
            
            for i, card in enumerate(cards):
                try:
                    if progress_callback:
                        progress_callback(i + 1, len(cards), card.get('name', '?'))
                    
                    card_data = self.parse_scryfall_card(card)
                    
                    if card_data:
                        db.execute(  # Nutze lokale db statt self.card_manager.db
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
                                ''
                            )
                        )
                        imported += 1
                        
                        if imported % 50 == 0:
                            db.commit()
                
                except Exception as e:
                    errors.append(f"{card.get('name', '?')}: {str(e)}")
            
            db.commit()
            db.close()  # Schließe Thread-Verbindung
            
            return {
                'success': True,
                'imported': imported,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def parse_scryfall_card(self, card):
        """Parse Scryfall-Karte"""
        try:
            return {
                'name': card.get('name', ''),
                'mana_cost': card.get('mana_cost', ''),
                'type': card.get('type_line', ''),
                'text': card.get('oracle_text', ''),
                'colors': ','.join(card.get('colors', [])),
                'image_id': card.get('id', ''),
                'set_code': card.get('set', '').upper(),
                'set_name': card.get('set_name', ''),
                'rarity': card.get('rarity', ''),
                'artist': card.get('artist', ''),
                'collector_number': card.get('collector_number', ''),
                'power': card.get('power', ''),
                'toughness': card.get('toughness', ''),
                'loyalty': card.get('loyalty', '')
            }
        except Exception as e:
            print(f"Parse error: {e}")
            return None
            
    def update_dfc_texts(self):
        """Aktualisiere nur DFC-Texte in DB"""
        import requests
        
        db = get_database()
        
        # Finde alle DFCs (Name enthält //)
        cursor = db.execute("SELECT id, name, set_code, collector_number FROM cards WHERE name LIKE '%//%'")
        dfcs = cursor.fetchall()
        
        print(f"Gefunden: {len(dfcs)} DFCs")
        
        updated = 0
        for card in dfcs:
            try:
                # Hole Daten von Scryfall
                url = f"https://api.scryfall.com/cards/{card['set_code'].lower()}/{card['collector_number']}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'card_faces' in data:
                        texts = []
                        for face in data['card_faces']:
                            texts.append(f"{face.get('name', '')}\n{face.get('oracle_text', '')}")
                        text = '\n--- Rückseite ---\n'.join(texts)
                        
                        db.execute("UPDATE cards SET text = ? WHERE id = ?", (text, card['id']))
                        updated += 1
                
                time.sleep(0.11)  # Rate Limit
                
            except Exception as e:
                print(f"Fehler bei {card['name']}: {e}")
        
        db.commit()
        print(f"Updated: {updated} DFCs")