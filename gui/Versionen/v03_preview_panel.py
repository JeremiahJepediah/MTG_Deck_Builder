"""
MTG Deck Builder v1.1 - Preview Panel
Spalte 4: Deck-Vorschau (nur anschauen)
"""

import tkinter as tk
from tkinter import ttk


class PreviewPanel:
    def __init__(self, parent, deck_manager, on_card_click, on_load_to_workspace):
        self.parent = parent
        self.deck_manager = deck_manager
        self.on_card_click_callback = on_card_click
        self.on_load_to_workspace_callback = on_load_to_workspace
        
        self.preview_deck_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstelle UI"""
        header = tk.Frame(self.parent)
        header.pack(fill='x', pady=5, padx=5)
        
        tk.Label(header, text="Deck-Vorschau", font=('Arial', 12, 'bold')).pack()
        
        self.deck_label = tk.Label(header, text="Kein Deck ausgewählt", 
                                   font=('Arial', 10), fg='gray')
        self.deck_label.pack()
        
        # TreeView
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set, show='tree')
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Button
        tk.Button(self.parent, text="▶ Als aktuell laden", 
                 command=self.load_to_workspace).pack(pady=5)
    
    def load_deck(self, deck_id):
        """Lade Deck in Vorschau"""
        self.preview_deck_id = deck_id
        deck = self.deck_manager.get_deck(deck_id)
        
        self.deck_label.config(text=deck['name'], fg='black')
        self.build_tree(deck_id)
    
    def build_tree(self, deck_id):
        """Baue hierarchische Darstellung"""
        self.tree.delete(*self.tree.get_children())
        
        cards = self.deck_manager.get_deck_cards(deck_id)
        
        if not cards:
            return
        
        # Gruppiere (gleiche Logik wie Workspace)
        groups = {
            'Commander': [],
            'Creatures': [],
            'Instants': [],
            'Sorceries': [],
            'Enchantments': [],
            'Artifacts': [],
            'Planeswalkers': [],
            'Lands': [],
            'Sideboard': [],
            'Other': []
        }
        
        for card in cards:
            role = card.get('role', 'card')
            card_type = card.get('type', '').lower()
            
            if role == 'commander':
                groups['Commander'].append(card)
            elif role == 'sideboard':
                groups['Sideboard'].append(card)
            elif 'creature' in card_type:
                groups['Creatures'].append(card)
            elif 'instant' in card_type:
                groups['Instants'].append(card)
            elif 'sorcery' in card_type:
                groups['Sorceries'].append(card)
            elif 'enchantment' in card_type:
                groups['Enchantments'].append(card)
            elif 'artifact' in card_type:
                groups['Artifacts'].append(card)
            elif 'planeswalker' in card_type:
                groups['Planeswalkers'].append(card)
            elif 'land' in card_type:
                groups['Lands'].append(card)
            else:
                groups['Other'].append(card)
        
        # Baue Tree
        for group_name, group_cards in groups.items():
            if not group_cards:
                continue
            
            group_node = self.tree.insert('', 'end', 
                                         text=f"📁 {group_name} ({len(group_cards)})")
            
            for card in sorted(group_cards, key=lambda c: c['name']):
                qty = card.get('deck_quantity', 1)
                display = f"   {card['name']}" + (f" ({qty}x)" if qty > 1 else "")
                self.tree.insert(group_node, 'end', text=display, tags=(card['id'],))
    
    def on_tree_click(self, event):
        """Klick auf Karte"""
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        tags = self.tree.item(item, 'tags')
        if tags and self.on_card_click_callback:
            try:
                card_id = int(tags[0])
                self.on_card_click_callback(card_id)
            except:
                pass
    
    def load_to_workspace(self):
        """Lade in Arbeitsbereich"""
        if self.preview_deck_id and self.on_load_to_workspace_callback:
            self.on_load_to_workspace_callback(self.preview_deck_id)
    
    def clear(self):
        """Leere Vorschau"""
        self.preview_deck_id = None
        self.deck_label.config(text="Kein Deck ausgewählt", fg='gray')
        self.tree.delete(*self.tree.get_children())
