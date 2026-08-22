"""
MTG Deck Builder v1.1 - Cards Panel
Spalte 1: Suche / Zufällige Karten
"""

import tkinter as tk
from tkinter import ttk
import random


class CardsPanel:
    def __init__(self, parent, card_manager, on_card_select, on_right_click, on_drag_start, on_drag_motion, on_double_click=None):
        self.parent = parent
        self.card_manager = card_manager
        self.on_card_select_callback = on_card_select
        self.on_right_click_callback = on_right_click
        self.on_drag_start_callback = on_drag_start
        self.on_drag_motion_callback = on_drag_motion
        self.on_double_click_callback = on_double_click
        
        self.card_data = {}
        self.random_card_count = 40
        
        # Auto-Search Timer
        self.search_timer = None
        self.search_delay = 500  # Millisekunden (0.5 Sekunden)
        
        self.setup_ui()
        self.load_random_cards()
    
    def setup_ui(self):
        """Erstelle UI"""
        tk.Label(self.parent, text="Karten", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Suchfeld
        search_frame = tk.Frame(self.parent)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(search_frame, text="🔍").pack(side='left')
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.schedule_search())
        
        # Buttons
        btn_frame = tk.Frame(self.parent)
        btn_frame.pack(fill='x', padx=5)
        
        tk.Button(btn_frame, text="Zufällig", command=self.load_random_cards, 
                 width=10).pack(side='left', padx=2)
        tk.Button(btn_frame, text="⭐ Legend", command=self.load_random_legendary,
                 width=10).pack(side='left', padx=2)
        tk.Button(btn_frame, text="✓ Besitz", command=self.mark_owned,  # NEU
                 width=10).pack(side='left', padx=2)   
        tk.Button(btn_frame, text="❌ Leeren", command=self.clear_search, 
                 width=10).pack(side='left', padx=2)
        
        
        
        # Filter
        filter_frame = tk.Frame(self.parent)
        filter_frame.pack(fill='x', padx=5, pady=3)
        
        self.filter_owned = tk.BooleanVar()
        tk.Checkbutton(filter_frame, text="Nur eigene", 
                      variable=self.filter_owned,
                      command=self.do_search).pack(side='left')
        
        # Liste
        list_frame = tk.Frame(self.parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Bindings - EINFACHE VERSION
        # self.listbox.bind('<<ListboxSelect>>', self.on_select)
        # self.listbox.bind('<Button-3>', self.on_right_click)
        # Drag&Drop erstmal deaktiviert
        
        # Drag-State
        # self.drag_start_index = None  

        # Bindings
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind('<ButtonPress-1>', self.on_button_press)
        self.listbox.bind('<B1-Motion>', self.on_motion)
        self.listbox.bind('<ButtonRelease-1>', self.on_button_release)
        self.listbox.bind('<Double-Button-1>', self.on_double_click)
        self.listbox.bind('<Button-3>', self.on_right_click)
        
        # Drag-State
        self.drag_threshold = 5  # Pixel bevor Drag startet
        self.drag_start_x = None
        self.drag_start_y = None
        self.is_dragging = False     

    def on_button_press(self, event):
        """Maus-Button gedrückt"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = False

    def on_motion(self, event):
        """Maus bewegt während Button gedrückt"""
        if self.drag_start_x is None:
            return
        
        # Prüfe ob weit genug bewegt für Drag
        dx = abs(event.x - self.drag_start_x)
        dy = abs(event.y - self.drag_start_y)
        
        if dx > self.drag_threshold or dy > self.drag_threshold:
            if not self.is_dragging:
                # Drag starten
                self.is_dragging = True
                print("Dragging!")
                self.start_drag(event)

    def on_button_release(self, event):
        """Maus-Button losgelassen"""
        if self.is_dragging:
            # War ein Drag - kein Select
            self.is_dragging = False
        
        # Reset
        self.drag_start_x = None
        self.drag_start_y = None

    def start_drag(self, event):
        """Starte Drag-Operation"""
        sel = self.listbox.curselection()
        if not sel:
            return
        
        display = self.listbox.get(sel[0])
        card_id = self.card_data.get(display)
        
        if card_id and self.on_drag_start_callback:
            self.on_drag_start_callback(event, card_id, self.listbox)
    
    def schedule_search(self):
        """Plant verzögerte Suche (Debouncing)"""
        if self.search_timer:
            self.parent.after_cancel(self.search_timer)
        self.search_timer = self.parent.after(self.search_delay, self.do_search)
    
    def do_search(self):
        """Führe Suche aus"""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            return
        
        filters = {}
        if self.filter_owned.get():
            filters['owned'] = 'only'
        
        results = self.card_manager.search_cards(search_term, filters)
        
        self.listbox.delete(0, 'end')
        self.card_data = {}
        
        for card in results:
            set_code = card.get('set_code', '')
            collector_number = card.get('collector_number', '')
            display = f"{card['name']} ({set_code} #{collector_number})"
            
            self.listbox.insert('end', display)
            self.card_data[display] = card['id']
    
    def clear_search(self):
        """Leere Suche"""
        self.search_entry.delete(0, 'end')
        self.filter_owned.set(False)
        self.load_random_cards()
    
    def load_random_cards(self):
        """Lade zufällige Karten"""
        cursor = self.card_manager.db.execute("SELECT id FROM cards")
        all_ids = [row[0] for row in cursor.fetchall()]
        
        if len(all_ids) > self.random_card_count:
            random_ids = random.sample(all_ids, self.random_card_count)
        else:
            random_ids = all_ids
        
        random_cards = [self.card_manager.get_card(cid) for cid in random_ids]
        
        self.listbox.delete(0, 'end')
        self.card_data = {}
        
        for card in random_cards:
            if card:
                # ÄNDERUNG: Zeige auch Set-Code an
                set_code = card.get('set_code', '')
                if set_code:
                    display = f"{card['name']} ({set_code})"
                else:
                    display = f"{card['name']}"
                
                self.listbox.insert('end', display)
                self.card_data[display] = card['id']
                
    def load_random_legendary(self):
        """Lade zufällige Legendary Creatures"""
        cursor = self.card_manager.db.execute(
            "SELECT id FROM cards WHERE type LIKE '%Legendary%' AND type LIKE '%Creature%'"
        )
        all_ids = [row[0] for row in cursor.fetchall()]
        
        if len(all_ids) > self.random_card_count:
            random_ids = random.sample(all_ids, self.random_card_count)
        else:
            random_ids = all_ids
        
        random_cards = [self.card_manager.get_card(cid) for cid in random_ids]
        
        self.listbox.delete(0, 'end')
        self.card_data = {}
        
        for card in random_cards:
            if card:
                set_code = card.get('set_code', '')
                if set_code:
                    display = f"{card['name']} ({set_code})"
                else:
                    display = f"{card['name']}"
                
                self.listbox.insert('end', display)
                self.card_data[display] = card['id']
    
    
    def on_select(self, event):
        """Karte ausgewählt"""
        sel = self.listbox.curselection()
        if not sel:
            return
        
        display = self.listbox.get(sel[0])
        card_id = self.card_data.get(display)
        
        if card_id and self.on_card_select_callback:
            self.on_card_select_callback(card_id)

    def on_right_click(self, event):
        """Rechtsklick"""
        # Wähle Item unter Maus aus
        index = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, 'end')
        self.listbox.selection_set(index)
        
        display = self.listbox.get(index)
        card_id = self.card_data.get(display)
        
        if card_id and self.on_right_click_callback:
            self.on_right_click_callback(event, card_id)
    
    # def on_select(self, event):
        # """Karte ausgewählt"""
        # sel = self.listbox.curselection()
        # if not sel:
            # return
        
        # display = self.listbox.get(sel[0])
        # card_id = self.card_data.get(display)
        
        # if card_id and self.on_card_select_callback:
            # self.on_card_select_callback(card_id)
    
    # def on_right_click(self, event):
        # """Rechtsklick"""
        # sel = self.listbox.curselection()
        # if not sel:
            # return
        
        # display = self.listbox.get(sel[0])
        # card_id = self.card_data.get(display)
        
        # if card_id and self.on_right_click_callback:
            # self.on_right_click_callback(event, card_id)
    
    # def on_drag_start(self, event):
        # """Drag Start"""
        # sel = self.listbox.curselection()
        # if not sel:
            # return
        
        # display = self.listbox.get(sel[0])
        # card_id = self.card_data.get(display)
        
        # if card_id and self.on_drag_start_callback:
            # self.on_drag_start_callback(event, card_id, self.listbox)
    
    # def on_drag_motion(self, event):
        # """Drag Motion"""
        # if self.on_drag_motion_callback:
            # self.on_drag_motion_callback(event)
            
    def mark_owned(self):
        """Markiere ausgewählte Karte als im Besitz"""
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Warnung", "Keine Karte ausgewählt")
            return
        
        display = self.listbox.get(sel[0])
        card_id = self.card_data.get(display)
        
        if not card_id:
            return
        
        # Hole aktuelle Karte
        from core.collection_manager import CollectionManager
        collection = CollectionManager()
        
        card = self.card_manager.get_card(card_id)
        current_qty = card.get('quantity', 0)
        
        # Dialog für Anzahl
        from tkinter import simpledialog
        qty = simpledialog.askinteger(
            "Im Besitz",
            f"{card['name']}\n\nAktuell: {current_qty}x\n\nNeue Anzahl:",
            initialvalue=max(1, current_qty),
            minvalue=0,
            maxvalue=999
        )
        
        if qty is not None:
            collection.set_quantity(card_id, qty)
            if qty > 0:
                messagebox.showinfo("Erfolg", f"✓ {qty}x {card['name']} markiert!")
            else:
                messagebox.showinfo("Erfolg", f"✓ {card['name']} nicht mehr im Besitz")
            
            # Refresh Details
            if self.on_card_select_callback:
                self.on_card_select_callback(card_id)
            
    def on_double_click(self, event):
        """Doppelklick - füge zu Workspace hinzu"""
        sel = self.listbox.curselection()
        if not sel:
            return
        
        display = self.listbox.get(sel[0])
        card_id = self.card_data.get(display)
        
        # Callback zu MainWindow
        if card_id and hasattr(self, 'on_double_click_callback'):
            self.on_double_click_callback(card_id)
    
    def set_random_count(self, count):
        """Setze Anzahl zufälliger Karten"""
        self.random_card_count = count
        self.load_random_cards()
