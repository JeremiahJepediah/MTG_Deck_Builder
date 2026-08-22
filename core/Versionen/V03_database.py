"""
MTG Deck Builder v1.1 - Datenbank Manager
Zentrale Datenbank-Verbindung und Schema
"""

import sqlite3
from pathlib import Path
import sys

# Import config
sys.path.append(str(Path(__file__).parent.parent))
from config import DB_PATH


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.connection = None
        self.init_database()
        
    
    def connect(self):
        """Stelle Verbindung zur Datenbank her"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Zugriff per Spaltenname
        return self.connection
    
    def close(self):
        """Schließe Verbindung"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute(self, query, params=None):
        """Führe Query aus und gib Ergebnis zurück"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        return cursor
    
    def execute_many(self, query, params_list):
        """Führe Query mehrfach aus (bulk insert)"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor
    
    def commit(self):
        """Speichere Änderungen"""
        if self.connection:
            self.connection.commit()
    
    def init_database(self):
        """Erstelle Tabellen falls nicht vorhanden"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Karten-Tabelle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mana_cost TEXT,
                type TEXT,
                text TEXT,
                colors TEXT,
                image_id TEXT,
                file_path TEXT,
                notes TEXT,
                owned INTEGER DEFAULT 0,
                quantity INTEGER DEFAULT 0
            )
        ''')
        
        # Index für schnelle Suche
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_card_name ON cards(name)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_card_type ON cards(type)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_card_colors ON cards(colors)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_card_owned ON cards(owned)
        ''')
        
        # Tags für Baumstruktur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_tags (
                card_id INTEGER,
                tag TEXT,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tag ON card_tags(tag)
        ''')
        
        # Decks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Deck-Karten Zuordnung
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deck_cards (
                deck_id INTEGER,
                card_id INTEGER,
                role TEXT DEFAULT 'card',
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_deck_cards ON deck_cards(deck_id, card_id)
        ''')
        
        conn.commit()
    
    def get_card_count(self):
        """Gibt Anzahl der Karten zurück"""
        cursor = self.execute("SELECT COUNT(*) FROM cards")
        return cursor.fetchone()[0]
    
    def clear_all_data(self):
        """VORSICHT: Löscht alle Daten (für Neuimport)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM deck_cards")
        cursor.execute("DELETE FROM decks")
        cursor.execute("DELETE FROM card_tags")
        cursor.execute("DELETE FROM cards")
        
        conn.commit()


# Singleton-Instanz
_db_instance = None

def get_database():
    """Hole die zentrale Datenbank-Instanz"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
