"""
MTG Deck Builder v1.1 - Main Entry Point
"""

import tkinter as tk
from tkinter import messagebox
import sys
from pathlib import Path

# Füge Projekt-Root zu sys.path hinzu
sys.path.append(str(Path(__file__).parent))

from config import WINDOW_TITLE, WINDOW_SIZE, ICON_PATH
from core.database import get_database
from gui.main_window import MainWindow


def main():
    """Hauptfunktion - startet die App"""
    
    # Initialisiere Datenbank
    db = get_database()
    
    # Prüfe ob Karten vorhanden
    card_count = db.get_card_count()
    
    # Erstelle Hauptfenster
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry(WINDOW_SIZE)
    root.minsize(1920, 1080)
    
    # Icon setzen
    if ICON_PATH.exists():
        root.iconbitmap(str(ICON_PATH))
    
    # Erstelle Main Window
    app = MainWindow(root)
    
    # Zeige Import-Dialog wenn keine Karten
    if card_count == 0:
        root.after(500, lambda: show_import_dialog(app))
    
    # Starte Event Loop
    root.mainloop()
    
    # Cleanup
    db.close()


def show_import_dialog(app):
    """Zeigt Import-Dialog an"""
    response = messagebox.askyesno(
        "Karten importieren",
        "Es wurden noch keine Karten importiert.\n\n"
        "Möchtest du jetzt alle Karten aus den Markdown-Dateien importieren?\n\n"
        "Das kann einige Minuten dauern (33.000 Karten)."
    )
    
    if response:
        app.start_import()


if __name__ == '__main__':
    main()
