"""
MTG Deck Builder v1.1 - Main Window (Option B)
Trennung: Arbeitsbereich (Spalte 3) vs. Vorschau (Spalte 4)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from pathlib import Path
import sys
import threading
import random
from PIL import Image, ImageTk

sys.path.append(str(Path(__file__).parent.parent))
from core.card_manager import CardManager
from core.collection_manager import CollectionManager
from core.deck_manager import DeckManager
from core.image_handler import ImageHandler
from utils.import_script import CardImporter
from config import CARD_IMAGE_SIZE


class MainWindow:
    def __init__(self, root):
        self.root = root
        
        # Manager
        self.card_manager = CardManager()
        self.collection_manager = CollectionManager()
        self.deck_manager = DeckManager()
        self.image_handler = ImageHandler()
        self.importer = CardImporter()
        
        # State
        self.current_card = None
        self.current_deck_id = None  # Bearbeitetes Deck (Spalte 3)
        self.preview_deck_id = None  # Vorschau Deck (Spalte 4)
        self.random_card_count = 30
        
        # Drag & Drop State
        self.drag_data = {"card_id": None, "source": None}
        
        # GUI
        self.setup_gui()
        self.load_random_cards()
    
    def setup_gui(self):
        """Erstelle 5-Spalten Layout"""
        
        # Menüleiste
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Karten importieren", command=self.start_import)
        file_menu.add_command(label="Neues Deck", command=self.create_new_deck_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Einstellungen", menu=settings_menu)
        settings_menu.add_command(label="Anzahl zufälliger Karten", command=self.set_random_count)
        
        # Hauptbereich: PanedWindow
        main_paned = tk.PanedWindow(self.root, orient='horizontal', sashrelief='raised', sashwidth=4)
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Spalte 1: Zufällige Karten
        col1 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col1, minsize=200, width=280)
        self.setup_random_cards_column(col1)
        
        # Spalte 2: Kartendetails
        col2 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col2, minsize=200, width=350)
        self.setup_card_detail_column(col2)
        
        # Spalte 3: Arbeitsbereich (aktuell bearbeitetes Deck)
        col3 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col3, minsize=250, width=300)
        self.setup_workspace_column(col3)
        
        # Spalte 4: Deck-Vorschau
        col4 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col4, minsize=250, width=300)
        self.setup_preview_column(col4)
        
        # Spalte 5: Alle Decks
        col5 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col5, minsize=200, width=280)
        self.setup_all_decks_column(col5)
    
    def setup_random_cards_column(self, parent):
        """Spalte 1: Zufällige Karten"""
        tk.Label(parent, text="Zufällige Karten", font=('Arial', 12, 'bold')).pack(pady=5)
        
        tk.Button(parent, text="🔄 Neue Karten", command=self.load_random_cards).pack(pady=5)
        
        list_frame = tk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.random_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.random_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.random_listbox.yview)
        
        self.random_listbox.bind('<<ListboxSelect>>', self.on_random_card_select)
        self.random_listbox.bind('<ButtonPress-1>', self.on_drag_start)
        self.random_listbox.bind('<B1-Motion>', self.on_drag_motion)
        self.random_listbox.bind('<Button-3>', self.on_random_card_right_click)
    
    def setup_card_detail_column(self, parent):
        """Spalte 2: Kartendetails"""
        tk.Label(parent, text="Kartendetails", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Bilder
        image_container = tk.Frame(parent, bg='black')
        image_container.pack(pady=10)
        
        self.card_image_front = tk.Label(image_container, bg='black')
        self.card_image_front.pack(side='left', padx=5)
        
        self.card_image_back = tk.Label(image_container, bg='black')
        self.card_image_back.pack(side='left', padx=5)
        
        tk.Button(parent, text="🔍 Bild vergrößern", command=self.show_enlarged_image).pack(pady=5)
        
        # Text
        text_frame = tk.Frame(parent)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tk.Label(text_frame, text="Kartentext:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.card_text = scrolledtext.ScrolledText(text_frame, height=8, wrap='word', state='disabled')
        self.card_text.pack(fill='both', expand=True, pady=5)
        
        tk.Label(text_frame, text="Notizen:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.card_notes = scrolledtext.ScrolledText(text_frame, height=5, wrap='word')
        self.card_notes.pack(fill='both', expand=True)
        self.card_notes.bind('<KeyRelease>', lambda e: self.save_notes())
    
    def setup_workspace_column(self, parent):
        """Spalte 3: Arbeitsbereich (bearbeitbares Deck)"""
        header = tk.Frame(parent)
        header.pack(fill='x', pady=5, padx=5)
        
        tk.Label(header, text="Arbeitsbereich", font=('Arial', 12, 'bold')).pack()
        
        self.workspace_deck_label = tk.Label(header, text="Kein Deck geladen", font=('Arial', 10), fg='gray')
        self.workspace_deck_label.pack()
        
        # TreeView für hierarchische Darstellung
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.workspace_tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set, show='tree')
        self.workspace_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.workspace_tree.yview)
        
        self.workspace_tree.bind('<Button-1>', lambda e: self.on_tree_card_click(e, 'workspace'))
        self.workspace_tree.bind('<Button-3>', lambda e: self.on_tree_card_right_click(e, 'workspace'))
        self.workspace_tree.bind('<Enter>', lambda e: self.on_enter_drop_zone(e, 'workspace'))
        self.workspace_tree.bind('<Leave>', lambda e: self.on_leave_drop_zone(e))
        
        # Buttons
        btn_frame = tk.Frame(parent)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(btn_frame, text="Speichern", command=self.save_workspace).pack(side='left', padx=2)
        tk.Button(btn_frame, text="Schließen", command=self.close_workspace).pack(side='left', padx=2)
    
    def setup_preview_column(self, parent):
        """Spalte 4: Deck-Vorschau (nur anschauen)"""
        header = tk.Frame(parent)
        header.pack(fill='x', pady=5, padx=5)
        
        tk.Label(header, text="Deck-Vorschau", font=('Arial', 12, 'bold')).pack()
        
        self.preview_deck_label = tk.Label(header, text="Kein Deck ausgewählt", font=('Arial', 10), fg='gray')
        self.preview_deck_label.pack()
        
        # TreeView
        tree_frame = tk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.preview_tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set, show='tree')
        self.preview_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.preview_tree.yview)
        
        self.preview_tree.bind('<Button-1>', lambda e: self.on_tree_card_click(e, 'preview'))
        
        # Button
        tk.Button(parent, text="▶ Als aktuell laden", 
                 command=self.load_preview_to_workspace).pack(pady=5)
    
    def setup_all_decks_column(self, parent):
        """Spalte 5: Alle Decks"""
        tk.Label(parent, text="Alle Decks", font=('Arial', 12, 'bold')).pack(pady=5)
        
        list_frame = tk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.all_decks_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.all_decks_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.all_decks_listbox.yview)
        
        self.all_decks_listbox.bind('<Button-1>', self.on_deck_click)
        self.all_decks_listbox.bind('<Double-Button-1>', self.on_deck_double_click)
        self.all_decks_listbox.bind('<Button-3>', self.on_deck_right_click)
        
        self.refresh_all_decks()
    
    # === KARTEN LADEN ===
    
    def load_random_cards(self):
        """Lade zufällige Karten"""
        cursor = self.card_manager.db.execute("SELECT id FROM cards")
        all_ids = [row[0] for row in cursor.fetchall()]
        
        if len(all_ids) > self.random_card_count:
            random_ids = random.sample(all_ids, self.random_card_count)
        else:
            random_ids = all_ids
        
        random_cards = [self.card_manager.get_card(cid) for cid in random_ids]
        
        self.random_listbox.delete(0, 'end')
        self.random_card_data = {}
        
        for card in random_cards:
            if card:
                display = f"{card['name']}"
                self.random_listbox.insert('end', display)
                self.random_card_data[display] = card['id']
    
    def on_random_card_select(self, event):
        """Karte in Liste ausgewählt"""
        sel = self.random_listbox.curselection()
        if not sel:
            return
        
        display = self.random_listbox.get(sel[0])
        card_id = self.random_card_data.get(display)
        
        if card_id:
            self.show_card_details(card_id)
    
    def show_card_details(self, card_id):
        """Zeige Kartendetails in Spalte 2"""
        self.current_card = card_id
        card = self.card_manager.get_card(card_id)
        
        if not card:
            return
        
        # Bilder
        image_id = card.get('image_id')
        if image_id:
            is_dfc, back_card = self.card_manager.is_double_faced(image_id)
            
            if is_dfc:
                self.load_and_display_image(card['name'], image_id, 'front', self.card_image_front)
                self.load_and_display_image(card['name'], image_id, 'back', self.card_image_back)
            else:
                self.load_and_display_image(card['name'], image_id, 'front', self.card_image_front)
                self.card_image_back.config(image='')
                self.card_image_back.image = None
        
        # Text
        text = f"Name: {card['name']}\n"
        text += f"Manakosten: {card['mana_cost']}\n"
        text += f"Typ: {card['type']}\n"
        text += f"Farben: {card['colors']}\n\n"
        text += f"Kartentext:\n{card['text']}\n\n"
        text += f"Im Besitz: {'Ja' if card['owned'] else 'Nein'}"
        
        self.card_text.config(state='normal')
        self.card_text.delete('1.0', 'end')
        self.card_text.insert('1.0', text)
        self.card_text.config(state='disabled')
        
        # Notizen
        notes = card.get('notes', '')
        self.card_notes.delete('1.0', 'end')
        self.card_notes.insert('1.0', notes)
    
    def load_and_display_image(self, card_name, image_id, face, label):
        """Lade und zeige Bild"""
        def load_thread():
            image_path = self.image_handler.get_image_path(card_name, image_id, face)
            
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize(CARD_IMAGE_SIZE, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    label.config(image=photo)
                    label.image = photo
                except Exception as e:
                    print(f"Fehler: {e}")
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def save_notes(self):
        """Speichere Notizen"""
        if not self.current_card:
            return
        
        notes = self.card_notes.get('1.0', 'end-1c')
        self.card_manager.update_notes(self.current_card, notes)
    
    def show_enlarged_image(self):
        """Zeige vergrößertes Bild"""
        if not self.current_card:
            messagebox.showinfo("Info", "Keine Karte ausgewählt")
            return
        
        card = self.card_manager.get_card(self.current_card)
        image_id = card.get('image_id')
        
        if not image_id:
            messagebox.showinfo("Info", "Kein Bild verfügbar")
            return
        
        popup = tk.Toplevel(self.root)
        popup.title(f"{card['name']} - Vergrößert")
        popup.geometry("800x600")
        
        container = tk.Frame(popup, bg='black')
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        front_label = tk.Label(container, bg='black')
        front_label.pack(side='left', padx=10)
        
        is_dfc, back_card = self.card_manager.is_double_faced(image_id)
        
        if is_dfc:
            back_label = tk.Label(container, bg='black')
            back_label.pack(side='left', padx=10)
        
        def load_large():
            front_path = self.image_handler.get_image_path(card['name'], image_id, 'front')
            if front_path:
                try:
                    img = Image.open(front_path)
                    img = img.resize((375, 525), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    front_label.config(image=photo)
                    front_label.image = photo
                except:
                    pass
            
            if is_dfc:
                back_path = self.image_handler.get_image_path(card['name'], image_id, 'back')
                if back_path:
                    try:
                        img = Image.open(back_path)
                        img = img.resize((375, 525), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        back_label.config(image=photo)
                        back_label.image = photo
                    except:
                        pass
        
        threading.Thread(target=load_large, daemon=True).start()
    
    # === DECK-VERWALTUNG ===
    
    def build_deck_tree(self, tree_widget, deck_id):
        """Baue hierarchische Deck-Darstellung"""
        tree_widget.delete(*tree_widget.get_children())
        
        cards = self.deck_manager.get_deck_cards(deck_id)
        
        if not cards:
            return
        
        # Gruppiere nach Rolle/Typ
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
            
            # Gruppe
            group_node = tree_widget.insert('', 'end', text=f"📁 {group_name} ({len(group_cards)})")
            
            # Karten
            for card in sorted(group_cards, key=lambda c: c['name']):
                qty = card.get('deck_quantity', 1)
                display = f"   {card['name']}" + (f" ({qty}x)" if qty > 1 else "")
                tree_widget.insert(group_node, 'end', text=display, tags=(card['id'],))
    
    def load_deck_to_workspace(self, deck_id):
        """Lade Deck in Arbeitsbereich"""
        self.current_deck_id = deck_id
        deck = self.deck_manager.get_deck(deck_id)
        
        self.workspace_deck_label.config(text=deck['name'], fg='black')
        self.build_deck_tree(self.workspace_tree, deck_id)
    
    def load_deck_to_preview(self, deck_id):
        """Lade Deck in Vorschau"""
        self.preview_deck_id = deck_id
        deck = self.deck_manager.get_deck(deck_id)
        
        self.preview_deck_label.config(text=deck['name'], fg='black')
        self.build_deck_tree(self.preview_tree, deck_id)
    
    def load_preview_to_workspace(self):
        """Lade Vorschau-Deck in Arbeitsbereich"""
        if not self.preview_deck_id:
            messagebox.showinfo("Info", "Kein Deck in Vorschau")
            return
        
        self.load_deck_to_workspace(self.preview_deck_id)
    
    def save_workspace(self):
        """Speichere Arbeitsbereich (aktuell nichts zu tun)"""
        messagebox.showinfo("Info", "Deck gespeichert!")
    
    def close_workspace(self):
        """Schließe Arbeitsbereich"""
        self.current_deck_id = None
        self.workspace_deck_label.config(text="Kein Deck geladen", fg='gray')
        self.workspace_tree.delete(*self.workspace_tree.get_children())
    
    def on_deck_click(self, event):
        """Einfacher Klick auf Deck → Vorschau"""
        sel = self.all_decks_listbox.curselection()
        if not sel:
            return
        
        display = self.all_decks_listbox.get(sel[0])
        deck_id = self.all_deck_data.get(display)
        
        if deck_id:
            self.load_deck_to_preview(deck_id)
    
    def on_deck_double_click(self, event):
        """Doppelklick auf Deck → In Arbeitsbereich laden"""
        sel = self.all_decks_listbox.curselection()
        if not sel:
            return
        
        display = self.all_decks_listbox.get(sel[0])
        deck_id = self.all_deck_data.get(display)
        
        if deck_id:
            self.load_deck_to_workspace(deck_id)
    
    def on_tree_card_click(self, event, source):
        """Klick auf Karte im Tree"""
        tree = self.workspace_tree if source == 'workspace' else self.preview_tree
        
        item = tree.identify('item', event.x, event.y)
        if not item:
            return
        
        tags = tree.item(item, 'tags')
        if tags:
            card_id = tags[0]
            try:
                card_id = int(card_id)
                self.show_card_details(card_id)
            except:
                pass
    
    def on_tree_card_right_click(self, event, source):
        """Rechtsklick auf Karte im Tree"""
        tree = self.workspace_tree
        
        item = tree.identify('item', event.x, event.y)
        if not item:
            return
        
        tags = tree.item(item, 'tags')
        if not tags:
            return
        
        card_id = int(tags[0])
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Aus Deck entfernen", 
                        command=lambda: self.remove_from_deck(card_id))
        menu.add_command(label="Als Commander markieren", 
                        command=lambda: self.change_card_role(card_id, 'commander'))
        menu.add_command(label="Als Sideboard markieren", 
                        command=lambda: self.change_card_role(card_id, 'sideboard'))
        
        menu.post(event.x_root, event.y_root)
    
    def remove_from_deck(self, card_id):
        """Entferne Karte aus Deck"""
        if not self.current_deck_id:
            return
        
        self.deck_manager.remove_card_from_deck(self.current_deck_id, card_id)
        self.build_deck_tree(self.workspace_tree, self.current_deck_id)
    
    def change_card_role(self, card_id, new_role):
        """Ändere Rolle einer Karte"""
        if not self.current_deck_id:
            return
        
        self.deck_manager.change_card_role(self.current_deck_id, card_id, new_role)
        self.build_deck_tree(self.workspace_tree, self.current_deck_id)
    
    # === RECHTSKLICK-MENÜS ===
    
    def on_random_card_right_click(self, event):
        """Rechtsklick auf zufällige Karte"""
        sel = self.random_listbox.curselection()
        if not sel:
            return
        
        display = self.random_listbox.get(sel[0])
        card_id = self.random_card_data.get(display)
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Neues Deck mit dieser Karte", 
                        command=lambda: self.create_deck_with_card(card_id))
        menu.add_separator()
        menu.add_command(label="Zu Arbeitsbereich hinzufügen", 
                        command=lambda: self.add_to_workspace(card_id))
        menu.add_command(label="Zu Deck hinzufügen...", 
                        command=lambda: self.add_to_deck_dialog(card_id))
        
        menu.post(event.x_root, event.y_root)
    
    def add_to_workspace(self, card_id):
        """Füge Karte zu Arbeitsbereich hinzu"""
        if not self.current_deck_id:
            messagebox.showwarning("Warnung", "Kein Deck im Arbeitsbereich")
            return
        
        # Dialog für Rolle
        role = self.ask_card_role()
        if role:
            self.deck_manager.add_card_to_deck(self.current_deck_id, card_id, role)
            self.build_deck_tree(self.workspace_tree, self.current_deck_id)
    
    def add_to_deck_dialog(self, card_id):
        """Dialog: Zu welchem Deck?"""
        decks = self.deck_manager.get_all_decks()
        
        if not decks:
            messagebox.showinfo("Info", "Erstelle zuerst ein Deck")
            return
        
        # Dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Zu Deck hinzufügen")
        dialog.geometry("300x250")
        
        tk.Label(dialog, text="Deck wählen:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        deck_var = tk.StringVar()
        deck_combo = ttk.Combobox(dialog, textvariable=deck_var, 
                                  values=[d['name'] for d in decks], state='readonly')
        deck_combo.pack(pady=5)
        
        tk.Label(dialog, text="Als:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        role_var = tk.StringVar(value='card')
        tk.Radiobutton(dialog, text="Karte (Standard)", variable=role_var, value='card').pack(anchor='w', padx=20)
        tk.Radiobutton(dialog, text="Commander", variable=role_var, value='commander').pack(anchor='w', padx=20)
        tk.Radiobutton(dialog, text="Sideboard", variable=role_var, value='sideboard').pack(anchor='w', padx=20)
        
        def add():
            deck_name = deck_var.get()
            if not deck_name:
                return
            
            deck = next((d for d in decks if d['name'] == deck_name), None)
            if deck:
                self.deck_manager.add_card_to_deck(deck['id'], card_id, role_var.get())
                messagebox.showinfo("Erfolg", f"Karte zu '{deck_name}' hinzugefügt!")
                dialog.destroy()
                
                # Refresh falls in Vorschau
                if self.preview_deck_id == deck['id']:
                    self.build_deck_tree(self.preview_tree, deck['id'])
                # Refresh falls in Arbeitsbereich
                if self.current_deck_id == deck['id']:
                    self.build_deck_tree(self.workspace_tree, deck['id'])
        
        tk.Button(dialog, text="Hinzufügen", command=add).pack(pady=10)
    
    def ask_card_role(self):
        """Dialog: Welche Rolle?"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Rolle wählen")
        dialog.geometry("250x200")
        
        tk.Label(dialog, text="Als:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        role_var = tk.StringVar(value='card')
        tk.Radiobutton(dialog, text="Karte (Standard)", variable=role_var, value='card').pack(anchor='w', padx=20)
        tk.Radiobutton(dialog, text="Commander", variable=role_var, value='commander').pack(anchor='w', padx=20)
        tk.Radiobutton(dialog, text="Sideboard", variable=role_var, value='sideboard').pack(anchor='w', padx=20)
        
        result = [None]
        
        def ok():
            result[0] = role_var.get()
            dialog.destroy()
        
        tk.Button(dialog, text="OK", command=ok).pack(pady=10)
        
        dialog.wait_window()
        return result[0]
    
    def create_deck_with_card(self, card_id):
        """Erstelle neues Deck mit dieser Karte"""
        card = self.card_manager.get_card(card_id)
        
        suggested_name = f"Deck mit {card['name']}"
        name = simpledialog.askstring("Neues Deck", "Deck-Name:", initialvalue=suggested_name)
        
        if name:
            deck_id = self.deck_manager.create_deck(name)
            if deck_id:
                role = self.ask_card_role()
                if role:
                    self.deck_manager.add_card_to_deck(deck_id, card_id, role)
                    messagebox.showinfo("Erfolg", f"Deck '{name}' erstellt!")
                    self.refresh_all_decks()
                    self.load_deck_to_workspace(deck_id)
    
    def on_deck_right_click(self, event):
        """Rechtsklick auf Deck"""
        sel = self.all_decks_listbox.curselection()
        if not sel:
            return
        
        display = self.all_decks_listbox.get(sel[0])
        deck_id = self.all_deck_data.get(display)
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Vorschau anzeigen", command=lambda: self.load_deck_to_preview(deck_id))
        menu.add_command(label="In Arbeitsbereich laden", command=lambda: self.load_deck_to_workspace(deck_id))
        menu.add_separator()
        menu.add_command(label="Löschen", command=lambda: self.delete_deck(deck_id))
        
        menu.post(event.x_root, event.y_root)
    
    def delete_deck(self, deck_id):
        """Lösche Deck"""
        deck = self.deck_manager.get_deck(deck_id)
        
        if messagebox.askyesno("Bestätigen", f"Deck '{deck['name']}' löschen?"):
            self.deck_manager.delete_deck(deck_id)
            self.refresh_all_decks()
            
            if self.current_deck_id == deck_id:
                self.close_workspace()
            
            if self.preview_deck_id == deck_id:
                self.preview_deck_id = None
                self.preview_deck_label.config(text="Kein Deck ausgewählt", fg='gray')
                self.preview_tree.delete(*self.preview_tree.get_children())
    
    def refresh_all_decks(self):
        """Aktualisiere Deck-Liste"""
        decks = self.deck_manager.get_all_decks()
        
        self.all_decks_listbox.delete(0, 'end')
        self.all_deck_data = {}
        
        for deck in decks:
            display = deck['name']
            self.all_decks_listbox.insert('end', display)
            self.all_deck_data[display] = deck['id']
    
    # === DRAG & DROP ===
    
    def on_drag_start(self, event):
        """Start Drag"""
        widget = event.widget
        sel = widget.curselection()
        if not sel:
            return
        
        display = widget.get(sel[0])
        card_id = self.random_card_data.get(display)
        
        if card_id:
            self.drag_data["card_id"] = card_id
            self.drag_data["source"] = "random"
            self.drag_data["widget"] = widget
            widget.config(cursor="hand2")
    
    def on_drag_motion(self, event):
        """Drag Motion"""
        if self.drag_data["card_id"]:
            widget = self.drag_data.get("widget")
            if widget:
                widget.config(cursor="hand2")
    
    def on_enter_drop_zone(self, event, target):
        """Maus betritt Drop-Zone"""
        if self.drag_data["card_id"]:
            if target == 'workspace':
                event.widget.config(bg='lightgreen')
            self.drag_data["current_target"] = target
    
    def on_leave_drop_zone(self, event):
        """Maus verlässt Drop-Zone"""
        event.widget.config(bg='white')
        if "current_target" in self.drag_data:
            del self.drag_data["current_target"]
    
    def check_drop(self, event):
        """Prüfe Drop"""
        if self.drag_data.get("card_id") and self.drag_data.get("current_target") == 'workspace':
            if not self.current_deck_id:
                messagebox.showwarning("Warnung", "Kein Deck im Arbeitsbereich")
                self.reset_drag_state()
                return
            
            card_id = self.drag_data["card_id"]
            role = self.ask_card_role()
            
            if role:
                self.deck_manager.add_card_to_deck(self.current_deck_id, card_id, role)
                self.build_deck_tree(self.workspace_tree, self.current_deck_id)
            
            self.reset_drag_state()
    
    def reset_drag_state(self):
        """Reset Drag State"""
        if "widget" in self.drag_data and self.drag_data["widget"]:
            self.drag_data["widget"].config(cursor="")
        
        self.workspace_tree.config(bg='white')
        self.drag_data = {"card_id": None, "source": None}
    
    # === EINSTELLUNGEN ===
    
    def set_random_count(self):
        """Setze Anzahl zufälliger Karten"""
        count = simpledialog.askinteger("Einstellung", 
                                       "Anzahl zufälliger Karten:",
                                       initialvalue=self.random_card_count,
                                       minvalue=10,
                                       maxvalue=100)
        if count:
            self.random_card_count = count
            self.load_random_cards()
    
    def create_new_deck_dialog(self):
        """Erstelle neues Deck"""
        name = simpledialog.askstring("Neues Deck", "Deck-Name:")
        
        if name:
            deck_id = self.deck_manager.create_deck(name)
            if deck_id:
                messagebox.showinfo("Erfolg", f"Deck '{name}' erstellt!")
                self.refresh_all_decks()
                self.load_deck_to_workspace(deck_id)
    
    # === IMPORT ===
    
    def start_import(self):
        """Starte Karten-Import"""
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Importiere Karten...")
        progress_window.geometry("400x150")
        
        label = tk.Label(progress_window, text="Importiere Karten...", pady=20)
        label.pack()
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill='x')
        progress_bar.start()
        
        status_label = tk.Label(progress_window, text="")
        status_label.pack()
        
        def import_thread():
            def progress_callback(current, total, name):
                status_label.config(text=f"{current}/{total}: {name}")
                progress_window.update()
            
            result = self.importer.import_all_cards(
                progress_callback=progress_callback,
                clear_existing=True
            )
            
            progress_window.destroy()
            
            if result['success']:
                messagebox.showinfo("Erfolg", 
                    f"{result['imported']} Karten importiert!")
                self.load_random_cards()
            else:
                messagebox.showerror("Fehler", result.get('error'))
        
        threading.Thread(target=import_thread, daemon=True).start()
