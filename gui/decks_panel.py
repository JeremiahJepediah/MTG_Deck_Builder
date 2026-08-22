"""
MTG Deck Builder v1.1 - Decks Panel
Spalte 5: Alle Decks (mit Mana-Symbol-Icons)
"""

import tkinter as tk
import re
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
from utils.color_identity import get_color_identity



class DecksPanel:
    def __init__(self, parent, deck_manager, on_deck_click, on_deck_double_click, on_deck_right_click):
        self.parent = parent
        self.deck_manager = deck_manager
        self.on_deck_click_callback = on_deck_click
        self.on_deck_double_click_callback = on_deck_double_click
        self.on_deck_right_click_callback = on_deck_right_click
        
        self.deck_data = {}
        self.icon_cache = {}  # Cache für Mana-Symbole
        
        self.setup_ui()
        self.load_icons()
        self.refresh()
    
    def setup_ui(self):
        """Erstelle UI"""
        tk.Label(self.parent, text="Alle Decks", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Canvas mit Scrollbar
        canvas_frame = tk.Frame(self.parent)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(canvas_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.canvas = tk.Canvas(canvas_frame, yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        # Frame für Deck-Liste
        self.list_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor='nw')
        
        # Bindings
        self.list_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
    
    def load_icons(self):
        from config import MANA_SYMBOLS_DIR
        icons_dir = MANA_SYMBOLS_DIR
        
        print(f"DEBUG: Icons dir: {icons_dir}")
        print(f"DEBUG: Exists: {icons_dir.exists()}")
        
        for color in ['W', 'U', 'B', 'R', 'G', 'C']:
            icon_path = icons_dir / f"{color}.png"
            print(f"DEBUG: Looking for {icon_path}, exists: {icon_path.exists()}")
            if icon_path.exists():
                try:
                    img = Image.open(icon_path)
                    print(f"DEBUG: {color} - Size: {img.size}, Mode: {img.mode}")
                    img = img.resize((15, 15), Image.Resampling.LANCZOS)  # Größe anpassen
                    photo = ImageTk.PhotoImage(img)
                    self.icon_cache[color] = photo
                    print(f"  ✓ {color} loaded ({img.size})")
                except Exception as e:
                    print(f"  ✗ {color} error: {e}")
                    pass
    
            # Zahlen 0-20
        for num in range(21):
            icon_path = icons_dir / f"{num}.png"
            if icon_path.exists():
                img = Image.open(icon_path)
                img = img.resize((15, 15), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.icon_cache[str(num)] = photo
    
    def refresh(self):
        """Aktualisiere Deck-Liste mit Icons"""
        # Lösche alte Widgets
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        self.deck_data = {}
        decks = self.deck_manager.get_all_decks()
        
        for idx, deck in enumerate(decks):
            # Erstelle Deck-Zeile
            deck_frame = tk.Frame(self.list_frame, relief='flat', borderwidth=1)
            deck_frame.pack(fill='x', pady=1)
            deck_frame.grid_columnconfigure(0, minsize=140)  # Icon-Spalte mindestens 140px
            deck_frame.grid_columnconfigure(1, weight=1)     # Name-Spalte dehnt sich
            
            # Hole Commander-Farben
            cards = self.deck_manager.get_deck_cards(deck['id'])
            commanders = [c for c in cards if c.get('role') == 'commander']
            
            # Icon-Container
            icon_container = tk.Frame(deck_frame)
            icon_container.grid(row=0, column=0, sticky='w', padx=(5, 15))
            
            if commanders:
                colors = get_color_identity(commanders[0])
                for color in colors:
                    if color in self.icon_cache:
                        icon_label = tk.Label(icon_container, image=self.icon_cache[color])
                        icon_label.pack(side='left', padx=1)
            else:
                tk.Label(icon_container, text="—", font=('Arial', 10)).pack(side='left')
            
            # Deck-Name (Spalte 1)
            name_label = tk.Label(deck_frame, text=deck['name'], anchor='w', font=('Arial', 10), wraplength=200)
            name_label.grid(row=0, column=1, sticky='w')

            # Mana-Cost rechts (Spalte 2) - NEU
            mana_container = tk.Frame(deck_frame)
            mana_container.grid(row=0, column=2, sticky='e', padx=5)

            if commanders:
                mana_cost = commanders[0].get('mana_cost', '')
                print(f"DEBUG: Mana cost: {mana_cost}")
                symbols = re.findall(r'\{([^}]+)\}', mana_cost)
                print(f"DEBUG: Symbols: {symbols}")
                print(f"DEBUG: Cache has: {list(self.icon_cache.keys())}")
                
                for symbol in symbols:
                    print(f"DEBUG: Symbol '{symbol}' in cache: {symbol in self.icon_cache}")
                    if symbol in self.icon_cache:
                        icon_label = tk.Label(mana_container, image=self.icon_cache[symbol])
                        icon_label.pack(side='left', padx=1)
            
            # Bindings (für BEIDE Widgets)
            deck_id = deck['id']
            for widget in [deck_frame, icon_container, name_label, mana_container]:
                widget.bind('<Button-1>', lambda e, did=deck_id: self.on_click(did))
                widget.bind('<Double-Button-1>', lambda e, did=deck_id: self.on_double_click(did))
                widget.bind('<Button-3>', lambda e, did=deck_id: self.on_right_click(e, did))
                widget.bind('<Enter>', lambda e, frame=deck_frame: frame.config(bg='lightblue'))
                widget.bind('<Leave>', lambda e, frame=deck_frame: frame.config(bg='SystemButtonFace'))
            
            self.deck_data[deck_id] = deck
    
    def on_click(self, deck_id):
        """Einfacher Klick"""
        if self.on_deck_click_callback:
            self.on_deck_click_callback(deck_id)
    
    def on_double_click(self, deck_id):
        """Doppelklick"""
        if self.on_deck_double_click_callback:
            self.on_deck_double_click_callback(deck_id)
    
    def on_right_click(self, event, deck_id):
        """Rechtsklick"""
        if self.on_deck_right_click_callback:
            self.on_deck_right_click_callback(event, deck_id)