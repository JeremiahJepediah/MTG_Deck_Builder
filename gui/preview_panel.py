"""
MTG Deck Builder v1.1 - Visual Preview Panel
Spalte 4: Deck-Vorschau mit Kartenbildern
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))


class VisualPreviewPanel:
    def __init__(self, parent, deck_manager, image_handler, on_card_click, on_load_to_workspace):
        self.parent = parent
        self.deck_manager = deck_manager
        self.image_handler = image_handler
        self.on_card_click_callback = on_card_click
        self.on_load_to_workspace_callback = on_load_to_workspace
        
        self.preview_deck_id = None
        self.current_category = None
        self.card_images = {}  # Cache für PhotoImage Objekte
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstelle UI"""
        # Header
        header = tk.Frame(self.parent)
        header.pack(fill='x', pady=5, padx=5)
        
        tk.Label(header, text="Deck-Vorschau", font=('Arial', 12, 'bold')).pack()
        
        self.deck_label = tk.Label(header, text="Kein Deck ausgewählt", 
                                   font=('Arial', 10), fg='gray', wraplength=250)
        self.deck_label.pack()
        
        # Commander-Bereich (immer sichtbar)
        commander_frame = tk.LabelFrame(self.parent, text="Commander", 
                                        font=('Arial', 10, 'bold'))
        commander_frame.pack(fill='x', padx=5, pady=5)
        
        self.commander_container = tk.Frame(commander_frame, background='black')
        self.commander_container.pack(fill='x', padx=5, pady=5)
        
        # Kategorien (klickbare Buttons)
        categories_frame = tk.LabelFrame(self.parent, text="Kategorien",
                                         font=('Arial', 10, 'bold'))
        categories_frame.pack(fill='x', padx=5, pady=5)
        
        self.category_buttons = {}
        categories = [
            ('Creatures', '🦁'),
            ('Instants', '⚡'),
            ('Sorceries', '🔥'),
            ('Enchantments', '✨'),
            ('Artifacts', '⚙️'),
            ('Planeswalkers', '👤'),
            ('Lands', '🏔️'),
            ('Sideboard', '📦')
        ]
        
        row = 0
        col = 0
        for cat_name, emoji in categories:
            btn = tk.Button(categories_frame, 
                          text=f"{emoji} {cat_name}",
                          command=lambda c=cat_name: self.show_category(c),
                          width=15)
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.category_buttons[cat_name] = btn
            
            col += 1
            if col >= 4:  # 4 Buttons pro Zeile
                col = 0
                row += 1
        
        # Karten-Anzahl Label
        self.stats_label = tk.Label(self.parent, text="", font=('Arial', 9))
        self.stats_label.pack(pady=5)
        
        # Scrollbare Karten-Ansicht
        canvas_frame = tk.Frame(self.parent)
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, background='#2b2b2b')
        scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        
        # Frame für Karten im Canvas
        self.cards_frame = tk.Frame(self.canvas, background='#2b2b2b')
        self.canvas_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor='nw')
        
        # Bind für Scrolling
        self.cards_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Mausrad-Scroll
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)  # Windows
        self.canvas.bind('<Button-4>', self.on_mousewheel)    # Linux scroll up
        self.canvas.bind('<Button-5>', self.on_mousewheel)    # Linux scroll down
        
        # Button
        tk.Button(self.parent, text="▶ Als aktuell laden", 
                 command=self.load_to_workspace).pack(pady=5)
    
    def on_frame_configure(self, event=None):
        """Update scroll region"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def on_canvas_configure(self, event):
        """Update canvas window width"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def load_deck(self, deck_id):
        """Lade Deck in Vorschau"""
        self.preview_deck_id = deck_id
        deck = self.deck_manager.get_deck(deck_id)
        
        self.deck_label.config(text=deck['name'], fg='black')
        
        # Lade Commander
        self.load_commanders(deck_id)
        
        # Zeige Stats
        self.update_stats(deck_id)
        
        # Leere Karten-Bereich
        self.clear_cards_display()
    
    def load_commanders(self, deck_id):
        """Zeige Commander-Karten"""
        # Lösche alte Commander
        for widget in self.commander_container.winfo_children():
            widget.destroy()
        
        cards = self.deck_manager.get_deck_cards(deck_id)
        commanders = [c for c in cards if c.get('role') == 'commander']
        
        if not commanders:
            tk.Label(self.commander_container, text="Kein Commander",
                    background='black', foreground='gray').pack(pady=10)
            return
        
        # Zeige Commander-Bilder
        for commander in commanders:
            self.create_card_image(commander, self.commander_container, size=(150, 210))
    
    def show_category(self, category):
        """Zeige Karten einer Kategorie"""
        self.current_category = category
        
        # Highlight aktiven Button
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.config(relief='sunken', background='lightblue')
            else:
                btn.config(relief='raised', background='SystemButtonFace')
        
        # Lade Karten
        self.load_category_cards(category)
    
    def load_category_cards(self, category):
        """Lade und zeige Karten einer Kategorie"""
        self.clear_cards_display()
        
        if not self.preview_deck_id:
            return
        
        cards = self.deck_manager.get_deck_cards(self.preview_deck_id)
        
        # Filtere nach Kategorie
        filtered_cards = []
        for card in cards:
            role = card.get('role', 'card')
            card_type = card.get('type', '').lower()
            
            if category == 'Sideboard' and role == 'sideboard':
                filtered_cards.append(card)
            elif role == 'commander':
                continue  # Commander schon oben angezeigt
            elif category == 'Creatures' and 'creature' in card_type:
                filtered_cards.append(card)
            elif category == 'Instants' and 'instant' in card_type:
                filtered_cards.append(card)
            elif category == 'Sorceries' and 'sorcery' in card_type:
                filtered_cards.append(card)
            elif category == 'Enchantments' and 'enchantment' in card_type:
                filtered_cards.append(card)
            elif category == 'Artifacts' and 'artifact' in card_type:
                filtered_cards.append(card)
            elif category == 'Planeswalkers' and 'planeswalker' in card_type:
                filtered_cards.append(card)
            elif category == 'Lands' and 'land' in card_type:
                filtered_cards.append(card)
        
        # Zeige Karten in Grid
        self.display_cards_grid(filtered_cards)
    
    def display_cards_grid(self, cards):
        """Zeige Karten als Grid"""
        if not cards:
            label = tk.Label(self.cards_frame, text="Keine Karten in dieser Kategorie",
                            background='#2b2b2b', foreground='gray',
                            font=('Arial', 12))
            label.pack(pady=20)
            # Bind scroll
            label.bind('<MouseWheel>', self.on_mousewheel)
            label.bind('<Button-4>', self.on_mousewheel)
            label.bind('<Button-5>', self.on_mousewheel)
            return
        
        # Sortiere nach Name
        cards = sorted(cards, key=lambda c: c['name'])
        
        # Erstelle Grid (3 Karten pro Reihe)
        row = 0
        col = 0
        max_cols = 3
        
        for card in cards:
            frame = tk.Frame(self.cards_frame, background='#2b2b2b')
            frame.grid(row=row, column=col, padx=5, pady=5)
            
            frame.bind('<MouseWheel>', self.on_mousewheel)
            frame.bind('<Button-4>', self.on_mousewheel)
            frame.bind('<Button-5>', self.on_mousewheel)
            
            self.create_card_image(card, frame, size=(120, 168))
                        
            # Name + Quantity unter Bild
            qty = card.get('deck_quantity', 1)
            label_text = f"{card['name']}"
            if qty > 1:
                label_text += f" ({qty}x)"
            
            name_label = tk.Label(frame, text=label_text, background='#2b2b2b',
                                 foreground='white', wraplength=120, font=('Arial', 8))
            name_label.pack()
            
            # Bind scroll
            name_label.bind('<MouseWheel>', self.on_mousewheel)
            name_label.bind('<Button-4>', self.on_mousewheel)
            name_label.bind('<Button-5>', self.on_mousewheel)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.on_frame_configure()
    
    def create_card_image(self, card, parent, size=(150, 210)):
        """Erstelle Karten-Bild Widget"""
        image_id = card.get('image_id')
        
        if not image_id:
            # Platzhalter
            placeholder = tk.Label(parent, text=card['name'][:20],
                                  background='gray', foreground='white',
                                  width=size[0]//10, height=size[1]//20)
            placeholder.pack(side='left', padx=2)
            placeholder.bind('<MouseWheel>', self.on_mousewheel)
            placeholder.bind('<Button-4>', self.on_mousewheel)
            placeholder.bind('<Button-5>', self.on_mousewheel)
            return
        
        # Erstelle Label für Bild
        img_label = tk.Label(parent, background='black')
        img_label.pack(side='left', padx=2)
        
        # Bind Click
        img_label.bind('<Button-1>', lambda e, cid=card['id']: self.on_image_click(cid))    
        img_label.bind('<MouseWheel>', self.on_mousewheel)
        img_label.bind('<Button-4>', self.on_mousewheel)
        img_label.bind('<Button-5>', self.on_mousewheel)
        
        # Lade Bild in Thread
        def load_image():
            image_path = self.image_handler.get_image_path(card['name'], image_id, 'front')
            
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label.config(image=photo)
                    img_label.image = photo  # Keep reference
                except Exception as e:
                    print(f"Fehler beim Laden: {e}")
        
        threading.Thread(target=load_image, daemon=True).start()
    
    def on_image_click(self, card_id):
        """Karten-Bild geklickt"""
        if self.on_card_click_callback:
            self.on_card_click_callback(card_id)
            
    def on_mousewheel(self, event):
        """Mausrad-Scroll"""
        if event.num == 5 or event.delta < 0:
            # Scroll down
            self.canvas.yview_scroll(1, 'units')
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            self.canvas.yview_scroll(-1, 'units')
    
    def clear_cards_display(self):
        """Leere Karten-Anzeige"""
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        
        # Reset Buttons
        for btn in self.category_buttons.values():
            btn.config(relief='raised', background='SystemButtonFace')
        
        self.current_category = None
    
    def update_stats(self, deck_id):
        """Zeige Deck-Statistiken"""
        stats = self.deck_manager.get_deck_stats(deck_id)
        
        text = f"Gesamt: {stats['total_cards']} Karten"
        if stats['commanders']:
            text += f" | Commander: {', '.join(stats['commanders'])}"
        
        self.stats_label.config(text=text)
    
    def load_to_workspace(self):
        """Lade in Arbeitsbereich"""
        if self.preview_deck_id and self.on_load_to_workspace_callback:
            self.on_load_to_workspace_callback(self.preview_deck_id)
    
    def clear(self):
        """Leere Vorschau"""
        self.preview_deck_id = None
        self.deck_label.config(text="Kein Deck ausgewählt", fg='gray')
        
        for widget in self.commander_container.winfo_children():
            widget.destroy()
        
        self.clear_cards_display()
        self.stats_label.config(text="")
