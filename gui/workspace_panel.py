"""
MTG Deck Builder v1.1 - Workspace Panel
Spalte 3: Arbeitsbereich (bearbeitbares Deck)
"""

import tkinter as tk
from tkinter import ttk, messagebox


class WorkspacePanel:
    def __init__(self, parent, deck_manager, on_card_click, on_card_right_click, 
                 on_enter_drop, on_leave_drop):
        self.parent = parent
        self.deck_manager = deck_manager
        self.on_card_click_callback = on_card_click
        self.on_card_right_click_callback = on_card_right_click
        self.on_enter_drop_callback = on_enter_drop
        self.on_leave_drop_callback = on_leave_drop
        
        self.current_deck_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstelle UI"""
        header = tk.Frame(self.parent)
        header.pack(fill='x', pady=5, padx=5)
        
        tk.Label(header, text="Arbeitsbereich", font=('Arial', 12, 'bold')).pack()
        
        self.deck_label = tk.Label(header, text="Kein Deck geladen", 
                                   font=('Arial', 10), fg='gray', wraplength=250)
        self.deck_label.pack()
        
        # TreeView
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set, show='tree', selectmode='extended')
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bindings
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<Button-3>', self.on_tree_right_click)
        self.tree.bind('<Enter>', lambda e: self.on_enter_drop_callback(e, 'workspace'))
        self.tree.bind('<Leave>', self.on_leave_drop_callback)
        
        # Buttons
        btn_frame = tk.Frame(self.parent)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(btn_frame, text="Speichern", command=self.save).pack(side='left', padx=2)
        tk.Button(btn_frame, text="📄 Export", command=self.export_deck).pack(side='left', padx=2)
        tk.Button(btn_frame, text="🏔️ Lands", command=self.add_basic_lands).pack(side='left', padx=2)
        tk.Button(btn_frame, text="Schließen", command=self.close).pack(side='left', padx=2)
    
    def load_deck(self, deck_id):
        """Lade Deck"""
        self.current_deck_id = deck_id
        deck = self.deck_manager.get_deck(deck_id)
        
        self.deck_label.config(text=deck['name'], fg='black')
        self.show_commander_identity(deck_id)
        self.build_tree(deck_id)
        
    def show_commander_identity(self, deck_id):
        """Zeige Commander Farbidentität"""
        from utils.color_identity import get_color_identity, format_color_identity
        
        cards = self.deck_manager.get_deck_cards(deck_id)
        commanders = [c for c in cards if c.get('role') == 'commander']
        
        if commanders:
            commander = commanders[0]
            colors = get_color_identity(commander)
            identity_text = format_color_identity(colors)
            
            # Zeige unter Deck-Name
            if not hasattr(self, 'identity_label'):
                self.identity_label = tk.Label(self.parent, font=('Arial', 9), fg='blue')
                self.identity_label.pack(after=self.deck_label)
            
            self.identity_label.config(text=f"⚡ {identity_text}")
        else:
            if hasattr(self, 'identity_label'):
                self.identity_label.config(text="")
    
    def build_tree(self, deck_id):
        """Baue hierarchische Darstellung"""
        self.tree.delete(*self.tree.get_children())
        
        cards = self.deck_manager.get_deck_cards(deck_id)
        
        if not cards:
            return
        
        # Gruppiere
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
            
            # Zähle TOTAL Quantity
            total_qty = sum(card.get('deck_quantity', 1) for card in group_cards)
            
            group_node = self.tree.insert('', 'end', 
                                         text=f"📁 {group_name} ({total_qty})")  # Geändert!
            
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
    
    def on_tree_right_click(self, event):
        """Rechtsklick auf Karte"""
        print("DEBUG: on_tree_right_click called")  # DEBUG
        
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            print("DEBUG: no item")  # DEBUG
            return
        
        # Hole ALLE ausgewählten Items
        selected_items = self.tree.selection()
        print(f"DEBUG: selected_items = {selected_items}")  # DEBUG
        
        # Falls geklicktes Item nicht in Selection, nutze nur dieses
        if item not in selected_items:
            self.tree.selection_set(item)
            selected_items = [item]
        
        # Sammle alle card_ids
        card_ids = []
        for sel_item in selected_items:
            tags = self.tree.item(sel_item, 'tags')
            if tags:
                try:
                    card_ids.append(int(tags[0]))
                except:
                    pass
        
        print(f"DEBUG: card_ids = {card_ids}")  # DEBUG
        
        if not card_ids:
            print("DEBUG: no card_ids")  # DEBUG
            return
        
        # Callback mit ALLEN card_ids
        if self.on_card_right_click_callback:
            print(f"DEBUG: calling callback with {card_ids}")  # DEBUG
            self.on_card_right_click_callback(event, card_ids)
        else:
            print("DEBUG: no callback!")  # DEBUG
    
    def save(self):
        """Speichern"""
        messagebox.showinfo("Info", "Deck gespeichert!")
    
    def close(self):
        """Schließen"""
        self.current_deck_id = None
        self.deck_label.config(text="Kein Deck geladen", fg='gray')
        self.tree.delete(*self.tree.get_children())
    
    def get_open_nodes(self):
        """Speichere welche Nodes offen sind"""
        open_nodes = []
        for item in self.tree.get_children():
            text = self.tree.item(item, 'text')
            # Entferne Anzahl: "📁 Sideboard (1)" → "Sideboard"
            node_name = text.split('(')[0].replace('📁', '').strip()
            if self.tree.item(item, 'open'):
                open_nodes.append(node_name)
        return open_nodes

    def restore_open_nodes(self, open_nodes):
        """Stelle offene Nodes wieder her"""
        for item in self.tree.get_children():
            text = self.tree.item(item, 'text')
            node_name = text.split('(')[0].replace('📁', '').strip()
            if node_name in open_nodes:
                self.tree.item(item, open=True)
    
    def refresh(self):
        """Aktualisiere Darstellung"""
        if self.current_deck_id:
            open_nodes = self.get_open_nodes()  # Speichern
            self.build_tree(self.current_deck_id)
            self.restore_open_nodes(open_nodes)  # Wiederherstellen
    
    def add_basic_lands(self):
        """Dialog zum Hinzufügen von Basic Lands"""
        if not self.current_deck_id:
            messagebox.showwarning("Warnung", "Kein Deck geladen")
            return
        
        from tkinter import simpledialog
        
        # Frage nach Land-Typ
        land_types = ["Forest", "Plains", "Island", "Swamp", "Mountain"]
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Basic Lands hinzufügen")
        dialog.geometry("300x250")
        
        tk.Label(dialog, text="Wähle Land-Typ:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        land_var = tk.StringVar(value="Forest")
        for land in land_types:
            tk.Radiobutton(dialog, text=land, variable=land_var, value=land).pack(anchor='w', padx=20)
        
        tk.Label(dialog, text="Anzahl:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        quantity_var = tk.IntVar(value=30)
        tk.Spinbox(dialog, from_=1, to=50, textvariable=quantity_var, width=10).pack()
        
        def add():
            land_type = land_var.get()
            qty = quantity_var.get()
            
            # Hole direkt aus DB
            cursor = self.deck_manager.db.execute(
                "SELECT * FROM cards WHERE name = ? LIMIT 1",
                (land_type,)
            )
            row = cursor.fetchone()
            
            if row:
                card_id = row[0]  # Erste Spalte ist die ID
                self.deck_manager.add_card_to_deck(self.current_deck_id, card_id, 'card', qty)
                messagebox.showinfo("Erfolg", f"{qty}x {land_type} hinzugefügt!")
                self.refresh()
                dialog.destroy()
            else:
                messagebox.showerror("Fehler", f"{land_type} nicht in DB gefunden!")
        
        tk.Button(dialog, text="Hinzufügen", command=add).pack(pady=10)
    
    def export_deck(self):
        """Exportiere Deck als Textdatei"""
        if not self.current_deck_id:
            messagebox.showwarning("Warnung", "Kein Deck geladen")
            return
        
        deck = self.deck_manager.get_deck(self.current_deck_id)
        cards = self.deck_manager.get_deck_cards(self.current_deck_id)
        
        # Erstelle Text
        output = f"# {deck['name']}\n"
        output += f"# Exportiert: {deck.get('created_at', 'Unbekannt')}\n\n"
        
        # Commander
        commanders = [c for c in cards if c.get('role') == 'commander']
        if commanders:
            output += "## Commander\n"
            for cmd in commanders:
                output += f"1 {cmd['name']} ({cmd.get('set_code', '?')})\n"
                # NEU: Commander-Details
                if cmd.get('mana_cost'):
                    output += f"   Mana: {cmd['mana_cost']}\n"
                if cmd.get('type'):
                    output += f"   Type: {cmd['type']}\n"
                if cmd.get('text'):
                    output += f"   Text: {cmd['text']}\n"
                output += "\n"
            output += "\n"
        
        # Gruppiere Rest
        groups = {
            'Creatures': [], 'Instants': [], 'Sorceries': [],
            'Enchantments': [], 'Artifacts': [], 'Planeswalkers': [],
            'Lands': [], 'Other': []
        }
        
        for card in cards:
            if card.get('role') == 'commander':
                continue
            
            card_type = card.get('type', '').lower()
            if 'creature' in card_type:
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
        
        # Schreibe Gruppen
        for group_name, group_cards in groups.items():
            if group_cards:
                output += f"## {group_name} ({len(group_cards)})\n"
                for card in sorted(group_cards, key=lambda c: c['name']):
                    qty = card.get('deck_quantity', 1)
                    set_code = card.get('set_code', '?')
                    # NEU: Füge Kartentext hinzu
                    card_text = card.get('text', '').strip()
                    mana_cost = card.get('mana_cost', '').strip()
                    card_type = card.get('type', '').strip()
                    
                    output += f"{qty} {card['name']} ({set_code})\n"
                    if mana_cost:
                        output += f"   Mana: {mana_cost}\n"
                    if card_type:
                        output += f"   Type: {card_type}\n"
                    if card_text:
                        output += f"   Text: {card_text}\n"
                    output += "\n"  # Leerzeile zwischen Karten
                output += "\n"
        
        # Speichern
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{deck['name']}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(output)
            messagebox.showinfo("Erfolg", f"Deck exportiert nach:\n{filename}")
