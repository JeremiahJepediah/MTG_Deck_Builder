"""
MTG Deck Builder v1.1 - Deck Manager
Deck-Verwaltung (erstellen, Karten hinzufügen, Analysen)
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from core.database import get_database
from core.collection_manager import CollectionManager


class DeckManager:
    def __init__(self):
        self.db = get_database()
        self.collection = CollectionManager()
    
    def create_deck(self, name):
        """
        Erstelle neues Deck
        
        Returns:
            deck_id oder None bei Fehler
        """
        try:
            cursor = self.db.execute(
                "INSERT INTO decks (name) VALUES (?)",
                (name,)
            )
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Fehler beim Erstellen des Decks: {e}")
            return None
    
    def delete_deck(self, deck_id):
        """Lösche Deck (CASCADE löscht automatisch deck_cards)"""
        self.db.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
        self.db.commit()
    
    def get_all_decks(self):
        """Hole alle Decks"""
        cursor = self.db.execute(
            "SELECT * FROM decks ORDER BY created_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_deck(self, deck_id):
        """Hole einzelnes Deck"""
        cursor = self.db.execute(
            "SELECT * FROM decks WHERE id = ?",
            (deck_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def add_card_to_deck(self, deck_id, card_id, role='card', quantity=1):
        """
        Füge Karte zu Deck hinzu
        
        Args:
            deck_id: ID des Decks
            card_id: ID der Karte
            role: 'card', 'commander', 'sideboard'
            quantity: Anzahl
        """
        # Prüfe ob Karte schon im Deck
        cursor = self.db.execute(
            "SELECT quantity, role FROM deck_cards WHERE deck_id = ? AND card_id = ?",
            (deck_id, card_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update Anzahl/Rolle
            self.db.execute(
                "UPDATE deck_cards SET quantity = ?, role = ? WHERE deck_id = ? AND card_id = ?",
                (quantity, role, deck_id, card_id)
            )
        else:
            # Neue Karte hinzufügen
            self.db.execute(
                "INSERT INTO deck_cards (deck_id, card_id, role, quantity) VALUES (?, ?, ?, ?)",
                (deck_id, card_id, role, quantity)
            )
        
        self.db.commit()
    
    def remove_card_from_deck(self, deck_id, card_id):
        """Entferne Karte aus Deck"""
        self.db.execute(
            "DELETE FROM deck_cards WHERE deck_id = ? AND card_id = ?",
            (deck_id, card_id)
        )
        self.db.commit()
    
    def change_card_role(self, deck_id, card_id, new_role):
        """Ändere Rolle einer Karte im Deck"""
        self.db.execute(
            "UPDATE deck_cards SET role = ? WHERE deck_id = ? AND card_id = ?",
            (new_role, deck_id, card_id)
        )
        self.db.commit()
    
    def get_deck_cards(self, deck_id):
        """
        Hole alle Karten eines Decks
        
        Returns:
            list of dicts mit Kartendaten + role + quantity
        """
        cursor = self.db.execute(
            """SELECT c.*, dc.role, dc.quantity as deck_quantity
               FROM cards c
               JOIN deck_cards dc ON c.id = dc.card_id
               WHERE dc.deck_id = ?
               ORDER BY dc.role, c.name""",
            (deck_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_deck_stats(self, deck_id):
        """
        Berechne Statistiken für ein Deck
        
        Returns:
            dict mit verschiedenen Stats
        """
        cards = self.get_deck_cards(deck_id)
        
        stats = {
            'total_cards': sum(card['deck_quantity'] for card in cards),
            'unique_cards': len(cards),
            'commanders': [],
            'mainboard': 0,
            'sideboard': 0,
            'colors': {},
            'types': {},
            'cmc_distribution': {},
            'owned_percentage': 0
        }
        
        # Zähle nach Rolle
        for card in cards:
            role = card['role']
            qty = card['deck_quantity']
            
            if role == 'commander':
                stats['commanders'].append(card['name'])
            elif role == 'sideboard':
                stats['sideboard'] += qty
            else:
                stats['mainboard'] += qty
        
        # Farben
        for card in cards:
            colors = card.get('colors', '').split(',')
            for color in colors:
                color = color.strip()
                if color:
                    stats['colors'][color] = stats['colors'].get(color, 0) + card['deck_quantity']
        
        # Typen
        for card in cards:
            card_type = card.get('type', '')
            # Einfache Typ-Extraktion
            for t in ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Planeswalker', 'Land']:
                if t in card_type:
                    stats['types'][t] = stats['types'].get(t, 0) + card['deck_quantity']
        
        # Besitz-Prozentsatz
        owned_count = sum(1 for card in cards if card['owned'])
        if cards:
            stats['owned_percentage'] = (owned_count / len(cards)) * 100
        
        return stats
    
    def check_ownership(self, deck_id):
        """
        Prüfe welche Karten im Deck fehlen
        
        Returns:
            dict mit 'owned' und 'missing' Listen
        """
        cards = self.get_deck_cards(deck_id)
        
        owned = []
        missing = []
        
        for card in cards:
            if card['owned']:
                owned.append({
                    'name': card['name'],
                    'quantity_needed': card['deck_quantity'],
                    'quantity_owned': card['quantity']
                })
            else:
                missing.append({
                    'name': card['name'],
                    'quantity_needed': card['deck_quantity']
                })
        
        return {
            'owned': owned,
            'missing': missing,
            'owned_count': len(owned),
            'missing_count': len(missing)
        }
