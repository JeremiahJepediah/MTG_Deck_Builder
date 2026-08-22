"""
MTG Deck Builder v1.1 - Card Manager
Zentrale Karten-Verwaltung (Suche, Filter, CRUD)
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from core.database import get_database


class CardManager:
    def __init__(self):
        self.db = get_database()
    
    def get_card(self, card_id):
        """Hole eine Karte nach ID"""
        cursor = self.db.execute(
            "SELECT * FROM cards WHERE id = ?",
            (card_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_card_by_name(self, name):
        """Hole eine Karte nach Name"""
        cursor = self.db.execute(
            "SELECT * FROM cards WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def search_cards(self, search_term='', filters=None):
        """
        Suche Karten mit optionalen Filtern
        
        Args:
            search_term: Text-Suche in Name/Text/Typ
            filters: dict mit Filtern (colors, types, owned, etc.)
        
        Returns:
            list of card dicts
        """
        query = "SELECT *, MIN(id) as min_id FROM cards WHERE 1=1"
        params = []
        
        # Text-Suche
        if search_term:
            print(f"\nDEBUG Search: '{search_term}'")
            
            # Split bei mehreren Wörtern
            terms = search_term.strip().split()
            
            # Prüfe ob Format "SET NNN"
            if len(terms) == 2 and terms[1].replace('0', '').isdigit():
                set_code = terms[0]
                number = terms[1].lstrip('0')
                query += " AND set_code LIKE ? AND (collector_number = ? OR collector_number = ?)"
                params.extend([f"%{set_code}%", terms[1], number])
            
            # Multi-Term: jeder Term muss vorkommen (UND-Verknüpfung)
            elif len(terms) > 1:
                conditions = []
                for term in terms:
                    # Jeder Term kann in name, text, type, set_code vorkommen
                    conditions.append("(name LIKE ? OR text LIKE ? OR type LIKE ? OR set_code LIKE ?)")
                    pattern = f"%{term}%"
                    params.extend([pattern, pattern, pattern, pattern])
                
                query += " AND " + " AND ".join(conditions)
            
            # Single Term
            elif search_term.isdigit():
                query += " AND (name LIKE ? OR collector_number = ? OR collector_number = ?)"
                trimmed = search_term.lstrip('0')
                params.extend([f"%{search_term}%", search_term, trimmed])
            
            else:
                query += " AND (name LIKE ? OR text LIKE ? OR type LIKE ? OR set_code LIKE ? OR collector_number LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern, search_pattern])
        
        # Filter anwenden
        if filters:
            # Farben-Filter
            if 'colors' in filters and filters['colors']:
                color_conditions = []
                for color in filters['colors']:
                    color_conditions.append("colors LIKE ?")
                    params.append(f"%{color}%")
                query += f" AND ({' OR '.join(color_conditions)})"
            
            # Typ-Filter
            if 'types' in filters and filters['types']:
                type_conditions = []
                for card_type in filters['types']:
                    type_conditions.append("type LIKE ?")
                    params.append(f"%{card_type}%")
                query += f" AND ({' OR '.join(type_conditions)})"
            
            # Besitz-Filter
            if 'owned' in filters:
                if filters['owned'] == 'only':
                    query += " AND owned = 1"
                elif filters['owned'] == 'not_owned':
                    query += " AND owned = 0"
            
            # CMC-Filter
            if 'cmc_min' in filters:
                # Vereinfachte CMC-Extraktion (TODO: besser machen)
                pass
            
            if 'cmc_max' in filters:
                pass
        
        query += " GROUP BY name, set_code, collector_number"
        query += " ORDER BY name"
        
        # Limit nur wenn KEINE Suche aktiv
        if not search_term and not filters:
            query += " LIMIT 100"
        # Bei aktiver Suche: höheres Limit oder kein Limit
        elif search_term:
            query += " LIMIT 1000"  # Oder ganz weglassen für unbegrenzt
        
        # DEBUG (ZWEITER BLOCK - HIER!)
        if search_term:  # Nur bei Suche debuggen
            print(f"  Final Query: {query}")
            print(f"  Params: {params}")
        
        cursor = self.db.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
        
        # DEBUG
        if search_term:
            print(f"  Results: {len(results)}")

        return results
    
    def get_cards_by_tags(self, tags, match_all=False):
        """
        Hole Karten die bestimmte Tags haben
        
        Args:
            tags: list of tag strings
            match_all: wenn True, müssen alle Tags matchen (AND), sonst OR
        
        Returns:
            list of card dicts
        """
        if not tags:
            return []
        
        if match_all:
            # Alle Tags müssen vorhanden sein
            query = """
                SELECT c.* FROM cards c
                WHERE c.id IN (
                    SELECT card_id FROM card_tags
                    WHERE tag IN ({})
                    GROUP BY card_id
                    HAVING COUNT(DISTINCT tag) = ?
                )
                ORDER BY c.name
            """.format(','.join(['?'] * len(tags)))
            params = tags + [len(tags)]
        else:
            # Mindestens ein Tag muss vorhanden sein
            query = """
                SELECT DISTINCT c.* FROM cards c
                JOIN card_tags ct ON c.id = ct.card_id
                WHERE ct.tag IN ({})
                ORDER BY c.name
            """.format(','.join(['?'] * len(tags)))
            params = tags
        
        cursor = self.db.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def is_double_faced(self, image_id):
        """
        Prüft ob Karte doppelseitig ist — anhand des Kartennamens (// Trennzeichen)
        """
        if not image_id:
            return False, None
        
        cursor = self.db.execute(
            "SELECT * FROM cards WHERE image_id = ? LIMIT 1",
            (image_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False, None
        
        card = dict(row)
        # DFC erkennen über Namen mit //
        if '//' in card.get('name', ''):
            return True, card  # back_card ist hier dasselbe dict (selbe image_id)
        
        return False, None
        

    def update_notes(self, card_id, notes):
        """Aktualisiere Notizen einer Karte"""
        self.db.execute(
            "UPDATE cards SET notes = ? WHERE id = ?",
            (notes, card_id)
        )
        self.db.commit()
    
    def add_card(self, card_data, tags=None):
        """
        Füge neue Karte hinzu
        
        Args:
            card_data: dict mit Kartendaten
            tags: list of tag strings
        
        Returns:
            card_id der eingefügten Karte
        """
        cursor = self.db.execute(
            """INSERT INTO cards 
               (name, mana_cost, type, text, colors, image_id, file_path, notes, owned, quantity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card_data.get('name'),
                card_data.get('mana_cost', ''),
                card_data.get('type', ''),
                card_data.get('text', ''),
                card_data.get('colors', ''),
                card_data.get('image_id', ''),
                card_data.get('file_path', ''),
                card_data.get('notes', ''),
                card_data.get('owned', 0),
                card_data.get('quantity', 0)
            )
        )
        self.db.commit()
        card_id = cursor.lastrowid
        
        # Tags hinzufügen
        if tags:
            self.add_tags(card_id, tags)
        
        return card_id
    
    def add_tags(self, card_id, tags):
        """Füge Tags zu Karte hinzu"""
        tag_data = [(card_id, tag) for tag in tags]
        self.db.execute_many(
            "INSERT INTO card_tags (card_id, tag) VALUES (?, ?)",
            tag_data
        )
        self.db.commit()
    
    def get_tags(self, card_id):
        """Hole alle Tags einer Karte"""
        cursor = self.db.execute(
            "SELECT tag FROM card_tags WHERE card_id = ?",
            (card_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_tags(self):
        """Hole alle existierenden Tags (für Baumstruktur)"""
        cursor = self.db.execute(
            "SELECT DISTINCT tag FROM card_tags ORDER BY tag"
        )
        return [row[0] for row in cursor.fetchall()]
        
    
