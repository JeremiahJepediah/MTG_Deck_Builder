"""
MTG Deck Builder v1.1 - Database Migration Script
Aktualisiert alte Datenbank-Schemas auf neue Version
"""

import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DB_PATH


def check_column_exists(cursor, table, column):
    """Prüft ob Spalte existiert"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate_database(db_path=None):
    """Migriert Datenbank auf neueste Version"""
    db_path = db_path or DB_PATH
    
    print(f"Migriere Datenbank: {db_path}")
    
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Backup empfehlen
    backup_path = db_path.parent / f"{db_path.stem}_backup.db"
    print(f"\n⚠️  HINWEIS: Erstelle vorher ein Backup!")
    print(f"   Kopiere: {db_path}")
    print(f"   Nach:    {backup_path}")
    
    response = input("\nFortfahren? (j/n): ")
    if response.lower() != 'j':
        print("Abgebrochen.")
        return False
    
    print("\n" + "="*60)
    print("Starte Migration...")
    print("="*60)
    
    # Migration 1: Erweiterte Felder zu cards Tabelle
    new_columns = [
        ('set_code', 'TEXT'),
        ('set_name', 'TEXT'),
        ('rarity', 'TEXT'),
        ('artist', 'TEXT'),
        ('collector_number', 'TEXT'),
        ('power', 'TEXT'),
        ('toughness', 'TEXT'),
        ('loyalty', 'TEXT')
    ]
    
    added_columns = 0
    for column_name, column_type in new_columns:
        if not check_column_exists(cursor, 'cards', column_name):
            print(f"  ➕ Füge Spalte hinzu: cards.{column_name}")
            cursor.execute(f"ALTER TABLE cards ADD COLUMN {column_name} {column_type}")
            added_columns += 1
        else:
            print(f"  ✓ Spalte existiert bereits: cards.{column_name}")
    
    conn.commit()
    
    # Migration 2: Erstelle fehlende Indizes
    print("\n" + "="*60)
    print("Erstelle Indizes...")
    print("="*60)
    
    indices = [
        ('idx_card_name', 'cards', 'name'),
        ('idx_card_type', 'cards', 'type'),
        ('idx_card_colors', 'cards', 'colors'),
        ('idx_card_owned', 'cards', 'owned'),
        ('idx_card_set', 'cards', 'set_code'),
        ('idx_card_rarity', 'cards', 'rarity'),
        ('idx_image_id', 'cards', 'image_id'),
        ('idx_tag', 'card_tags', 'tag'),
        ('idx_deck_cards', 'deck_cards', 'deck_id, card_id')
    ]
    
    created_indices = 0
    for index_name, table, columns in indices:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({columns})")
            print(f"  ✓ Index: {index_name}")
            created_indices += 1
        except sqlite3.OperationalError as e:
            print(f"  ⚠️  Index {index_name}: {e}")
    
    conn.commit()
    
    # Statistiken
    print("\n" + "="*60)
    print("Statistiken")
    print("="*60)
    
    cursor.execute("SELECT COUNT(*) FROM cards")
    card_count = cursor.fetchone()[0]
    print(f"  Karten in DB: {card_count}")
    
    cursor.execute("SELECT COUNT(*) FROM decks")
    deck_count = cursor.fetchone()[0]
    print(f"  Decks in DB:  {deck_count}")
    
    cursor.execute("SELECT COUNT(DISTINCT tag) FROM card_tags")
    tag_count = cursor.fetchone()[0]
    print(f"  Tags in DB:   {tag_count}")
    
    # Abschluss
    conn.close()
    
    print("\n" + "="*60)
    print("✅ Migration abgeschlossen!")
    print("="*60)
    print(f"  Neue Spalten:  {added_columns}")
    print(f"  Indizes:       {created_indices}")
    
    return True


def reset_database(db_path=None):
    """VORSICHT: Löscht komplette Datenbank und erstellt sie neu"""
    db_path = db_path or DB_PATH
    
    print("⚠️  WARNUNG: Dies löscht ALLE Daten!")
    print(f"   Datenbank: {db_path}")
    
    response = input("\nWirklich fortfahren? Tippe 'LÖSCHEN' zum Bestätigen: ")
    if response != 'LÖSCHEN':
        print("Abgebrochen.")
        return False
    
    if db_path.exists():
        db_path.unlink()
        print(f"✓ Gelöscht: {db_path}")
    
    # Importiere und initialisiere neue DB
    from core.database import Database
    db = Database(db_path)
    print("✓ Neue Datenbank erstellt")
    
    return True


def check_database_health(db_path=None):
    """Überprüft Datenbank-Gesundheit"""
    db_path = db_path or DB_PATH
    
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("="*60)
    print("Datenbank-Check")
    print("="*60)
    
    # Tabellen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nTabellen: {', '.join(tables)}")
    
    # Cards-Schema
    print("\nCards-Tabelle Schema:")
    cursor.execute("PRAGMA table_info(cards)")
    for row in cursor.fetchall():
        print(f"  {row[1]:<20} {row[2]}")
    
    # Indizes
    print("\nIndizes:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    for row in cursor.fetchall():
        print(f"  ✓ {row[0]}")
    
    # Integrität
    print("\nIntegritäts-Check:")
    cursor.execute("PRAGMA integrity_check")
    result = cursor.fetchone()[0]
    if result == 'ok':
        print("  ✅ OK")
    else:
        print(f"  ❌ {result}")
    
    conn.close()
    return True


def main():
    """Hauptmenü"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MTG Database Migration')
    parser.add_argument('--check', action='store_true', help='Prüfe Datenbank-Status')
    parser.add_argument('--migrate', action='store_true', help='Migriere Datenbank')
    parser.add_argument('--reset', action='store_true', help='VORSICHT: Lösche und erstelle DB neu')
    parser.add_argument('--db', type=str, help='Pfad zur Datenbank')
    
    args = parser.parse_args()
    
    if args.check:
        check_database_health(args.db)
    elif args.migrate:
        migrate_database(args.db)
    elif args.reset:
        reset_database(args.db)
    else:
        print("MTG Database Migration Tool")
        print("="*60)
        print()
        print("Optionen:")
        print("  --check    : Datenbank-Status prüfen")
        print("  --migrate  : Datenbank migrieren (empfohlen)")
        print("  --reset    : Datenbank neu erstellen (LÖSCHT DATEN!)")
        print()
        print("Beispiel:")
        print("  python migrate_database.py --migrate")
        print("  python migrate_database.py --check")


if __name__ == '__main__':
    main()
