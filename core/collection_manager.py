"""
MTG Deck Builder v1.1 - Collection Manager
Verwaltet Kartenbesitz (owned, quantity)
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from core.database import get_database


class CollectionManager:
    def __init__(self):
        self.db = get_database()
    
    def mark_owned(self, card_id, owned=True, quantity=1):
        """
        Markiere Karte als im Besitz / nicht im Besitz
        
        Args:
            card_id: ID der Karte
            owned: True = im Besitz, False = nicht im Besitz
            quantity: Anzahl (nur relevant wenn owned=True)
        """
        if owned:
            self.db.execute(
                "UPDATE cards SET owned = 1, quantity = ? WHERE id = ?",
                (quantity, card_id)
            )
        else:
            self.db.execute(
                "UPDATE cards SET owned = 0, quantity = 0 WHERE id = ?",
                (card_id,)
            )
        self.db.commit()
        
    def mark_wishlist(self, card_id, wishlist=True):
        """Markiere Karte als Wunschliste"""
        if wishlist:
            self.db.execute(
                "UPDATE cards SET wishlist = 1 WHERE id = ?",
                (card_id,)
            )
        else:
            self.db.execute(
                "UPDATE cards SET wishlist = 0 WHERE id = ?",
                (card_id,)
            )
        self.db.commit()

    def get_wishlist_cards(self):
        """Hole alle Wunschlisten-Karten"""
        cursor = self.db.execute(
            "SELECT * FROM cards WHERE wishlist = 1 ORDER BY name"
        )
        return [dict(row) for row in cursor.fetchall()]

    def is_wishlist(self, card_id):
        """Prüfe ob auf Wunschliste"""
        cursor = self.db.execute(
            "SELECT wishlist FROM cards WHERE id = ?",
            (card_id,)
        )
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    
    def set_quantity(self, card_id, quantity):
        """
        Setze Anzahl einer Karte
        (setzt automatisch owned=1 wenn quantity > 0)
        """
        if quantity > 0:
            self.db.execute(
                "UPDATE cards SET owned = 1, quantity = ? WHERE id = ?",
                (quantity, card_id)
            )
        else:
            self.db.execute(
                "UPDATE cards SET owned = 0, quantity = 0 WHERE id = ?",
                (card_id,)
            )
        self.db.commit()
    
    def get_owned_cards(self):
        """Hole alle Karten im Besitz"""
        cursor = self.db.execute(
            "SELECT * FROM cards WHERE owned = 1 ORDER BY name"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_owned_count(self):
        """Anzahl der Karten im Besitz"""
        cursor = self.db.execute(
            "SELECT COUNT(*) FROM cards WHERE owned = 1"
        )
        return cursor.fetchone()[0]
    
    def get_total_quantity(self):
        """Gesamtanzahl aller Karten (Summe der quantities)"""
        cursor = self.db.execute(
            "SELECT SUM(quantity) FROM cards WHERE owned = 1"
        )
        result = cursor.fetchone()[0]
        return result if result else 0
    
    def is_owned(self, card_id):
        """Prüfe ob Karte im Besitz"""
        cursor = self.db.execute(
            "SELECT owned, quantity FROM cards WHERE id = ?",
            (card_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'owned': bool(row[0]),
                'quantity': row[1]
            }
        return {'owned': False, 'quantity': 0}
    
    def filter_owned(self, card_list):
        """
        Filtere Liste von Karten, behalte nur die im Besitz
        
        Args:
            card_list: list of card dicts mit 'id' key
        
        Returns:
            list of card dicts (nur owned)
        """
        card_ids = [card['id'] for card in card_list]
        
        if not card_ids:
            return []
        
        placeholders = ','.join(['?'] * len(card_ids))
        query = f"SELECT id FROM cards WHERE id IN ({placeholders}) AND owned = 1"
        
        cursor = self.db.execute(query, card_ids)
        owned_ids = {row[0] for row in cursor.fetchall()}
        
        return [card for card in card_list if card['id'] in owned_ids]
    
    def get_collection_stats(self):
        """
        Statistiken über die Sammlung
        
        Returns:
            dict mit verschiedenen Stats
        """
        stats = {}
        
        # Gesamtanzahl
        cursor = self.db.execute("SELECT COUNT(*) FROM cards")
        stats['total_cards'] = cursor.fetchone()[0]
        
        # Im Besitz
        cursor = self.db.execute("SELECT COUNT(*) FROM cards WHERE owned = 1")
        stats['owned_cards'] = cursor.fetchone()[0]
        
        # Gesamtmenge
        cursor = self.db.execute("SELECT SUM(quantity) FROM cards WHERE owned = 1")
        result = cursor.fetchone()[0]
        stats['total_quantity'] = result if result else 0
        
        # Nach Farben
        colors = ['W', 'U', 'B', 'R', 'G', 'C']
        stats['by_color'] = {}
        for color in colors:
            cursor = self.db.execute(
                "SELECT COUNT(*) FROM cards WHERE owned = 1 AND colors LIKE ?",
                (f'%{color}%',)
            )
            stats['by_color'][color] = cursor.fetchone()[0]
        
        # Nach Typen
        types = ['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Planeswalker', 'Land']
        stats['by_type'] = {}
        for card_type in types:
            cursor = self.db.execute(
                "SELECT COUNT(*) FROM cards WHERE owned = 1 AND type LIKE ?",
                (f'%{card_type}%',)
            )
            stats['by_type'][card_type] = cursor.fetchone()[0]
        
        return stats
