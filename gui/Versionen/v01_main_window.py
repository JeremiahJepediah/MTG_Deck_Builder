"""
MTG Deck Builder v1.1 - Main Window (Neues Layout)
5-Spalten Design mit Drag & Drop
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
        self.current_deck_id = None
        self.deck_history = []  # [deck_id1, deck_id2, ...]
        self.random_card_count = 30
        
        # Drag & Drop State
        self.drag_data = {"card_id": None, "source": None}
        
        # GUI
        self.setup_gui()
        self.load_random_cards()
    
    def setup_gui(self):
        """Erstelle 5-Spalten Layout mit verstellbaren Spalten"""
        
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
        
        # Hauptbereich: PanedWindow für verstellbare Spalten
        main_paned = tk.PanedWindow(self.root, orient='horizontal', sashrelief='raised', sashwidth=4)
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Spalte 1: Zufällige Kartenliste
        col1 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col1, minsize=200, width=280)
        self.setup_random_cards_column(col1)
        
        # Spalte 2: Kartenbild + Text (schmaler)
        col2 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col2, minsize=200, width=350)
        self.setup_card_detail_column(col2)
        
        # Spalte 3: Aktuelles Deck
        col3 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col3, minsize=200, width=280)
        self.setup_current_deck_column(col3)
        
        # Spalte 4: Deck-History
        col4 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col4, minsize=200, width=280)
        self.setup_history_column(col4)
        
        # Spalte 5: Alle Decks
        col5 = tk.Frame(main_paned, relief='raised', borderwidth=1)
        main_paned.add(col5, minsize=200, width=280)
        self.setup_all_decks_column(col5)
    
    def setup_random_cards_column(self, parent):
        """Spalte 1: Zufällige Karten"""
        tk.Label(parent, text="Zufällige Karten", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Reload Button
        tk.Button(parent, text="🔄 Neue Karten", command=self.load_random_cards).pack(pady=5)
        
        # Listbox
        list_frame = tk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.random_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.random_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.random_listbox.yview)
        
        # Bindings
        self.random_listbox.bind('<<ListboxSelect>>', self.on_random_card_select)
        self.random_listbox.bind('<ButtonPress-1>', self.on_drag_start)
        self.random_listbox.bind('<B1-Motion>', self.on_drag_motion)
        self.random_listbox.bind('<Button-3>', self.on_random_card_right_click)
    
    def setup_card_detail_column(self, parent):
        """Spalte 2: Kartenbild + Text"""
        tk.Label(parent, text="Kartendetails", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Kartenbild (oben)
        image_container = tk.Frame(parent, bg='black')
        image_container.pack(pady=10)
        
        self.card_image_front = tk.Label(image_container, bg='black')
        self.card_image_front.pack(side='left', padx=5)
        
        self.card_image_back = tk.Label(image_container, bg='black')
        self.card_image_back.pack(side='left', padx=5)
        
        # Vergrößerungs-Button
        tk.Button(parent, text="🔍 Bild vergrößern", command=self.show_enlarged_image).pack(pady=5)
        
        # Kartentext (unten)
        text_frame = tk.Frame(parent)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tk.Label(text_frame, text="Kartentext:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.card_text = scrolledtext.ScrolledText(text_frame, height=8, wrap='word', state='disabled')
        self.card_text.pack(fill='both', expand=True, pady=5)
        
        tk.Label(text_frame, text="Notizen:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.card_notes = scrolledtext.ScrolledText(text_frame, height=5, wrap='word')
        self.card_notes.pack(fill='both', expand=True)
        self.card_notes.bind('<KeyRelease>', lambda e: self.save_notes())
    
    def setup_current_deck_column(self, parent):
        """Spalte 3: Aktuelles Deck"""
        tk.Label(parent, text="Aktuelles Deck", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Deck Name
        self.current_deck_label = tk.Label(parent, text="Kein Deck geladen", font=('Arial', 10))
        self.current_deck_label.pack(pady=5)
        
        # Listbox
        list_frame = tk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.current_deck_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.current_deck_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.current_deck_listbox.yview)
        
        # Bindings
        self.current_deck_listbox.bind('<Button-3>', self.on_deck_card_right_click)
        self.current_deck_listbox.bind('<Double-Button-1>', self.on_deck_card_double_click)
        
        # Drop-Target
        self.current_deck_listbox.bind('<Enter>', lambda e: self.on_enter_drop_zone(e, 'current'))
        self.current_deck_listbox.bind('<Leave>', lambda e: self.on_leave_drop_zone(e))
        self.current_deck_listbox.bind('<ButtonRelease-1>', lambda e: self.check_drop(e, 'current'))
    
    def setup_history_column(self, parent):
        """Spalte 4: Zuletzt bearbeitete Decks"""
        tk.Label(parent, text="Zuletzt bearbeitet", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Vorletztes Deck
        tk.Label(parent, text="Vorletztes:", font=('Arial', 9)).pack(anchor='w', padx=5)
        
        frame1 = tk.Frame(parent)
        frame1.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar1 = tk.Scrollbar(frame1)
        scrollbar1.pack(side='right', fill='y')
        
        self.prev_deck_listbox = tk.Listbox(frame1, yscrollcommand=scrollbar1.set)
        self.prev_deck_listbox.pack(side='left', fill='both', expand=True)
        scrollbar1.config(command=self.prev_deck_listbox.yview)
        
        self.prev_deck_listbox.bind('<Button-1>', lambda e: self.load_deck_from_history(1))
        self.prev_deck_listbox.bind('<Enter>', lambda e: self.on_enter_drop_zone(e, 'prev'))
        self.prev_deck_listbox.bind('<Leave>', lambda e: self.on_leave_drop_zone(e))
        
        # Zuletzt bearbeitetes Deck
        tk.Label(parent, text="Zuletzt:", font=('Arial', 9)).pack(anchor='w', padx=5)
        
        frame2 = tk.Frame(parent)
        frame2.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar2 = tk.Scrollbar(frame2)
        scrollbar2.pack(side='right', fill='y')
        
        self.last_deck_listbox = tk.Listbox(frame2, yscrollcommand=scrollbar2.set)
        self.last_deck_listbox.pack(side='left', fill='both', expand=True)
        scrollbar2.config(command=self.last_deck_listbox.yview)
        
        self.last_deck_listbox.bind('<Button-1>', lambda e: self.load_deck_from_history(0))
        self.last_deck_listbox.bind('<Enter>', lambda e: self.on_enter_drop_zone(e, 'last'))
        self.last_deck_listbox.bind('<Leave>', lambda e: self.on_leave_drop_zone(e))
    
    def setup_all_decks_column(self, parent):
        """Spalte 5: Alle Decks"""
        tk.Label(parent, text="Alle Decks", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Listbox
        list_frame = tk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.all_decks_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.all_decks_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.all_decks_listbox.yview)
        
        # Bindings
        self.all_decks_listbox.bind('<Double-Button-1>', self.on_deck_select)
        self.all_decks_listbox.bind('<Button-3>', self.on_deck_right_click)
        
        self.refresh_all_decks()
    
    def load_random_cards(self):
        """Lade zufällige Karten in linke Spalte"""
        # Hole alle IDs
        cursor = self.card_manager.db.execute("SELECT id FROM cards")
        all_ids = [row[0] for row in cursor.fetchall()]
        
        # Wähle zufällig
        if len(all_ids) > self.random_card_count:
            random_ids = random.sample(all_ids, self.random_card_count)
        else:
            random_ids = all_ids
        
        # Hole die Karten
        random_cards = [self.card_manager.get_card(cid) for cid in random_ids]
        
        # Zeige in Liste
        self.random_listbox.delete(0, 'end')
        self.random_card_data = {}
    
        for card in random_cards:
            if card:  # Prüfe ob Karte existiert
                display = f"{card['name']}"
                self.random_listbox.insert('end', display)
                self.random_card_data[display] = card['id']
    
    def on_random_card_select(self, event):
        """Wenn Karte in zufälliger Liste ausgewählt wird"""
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
        
        # Bilder laden
        image_id = card.get('image_id')
        if image_id:
            is_dfc, back_card = self.card_manager.is_double_faced(image_id)
            
            if is_dfc:
                # Vorder- und Rückseite
                self.load_and_display_image(image_id, 'front', self.card_image_front)
                self.load_and_display_image(image_id, 'back', self.card_image_back)
            else:
                # Nur Vorderseite
                self.load_and_display_image(image_id, 'front', self.card_image_front)
                self.card_image_back.config(image='')
                self.card_image_back.image = None
        
        # Kartentext
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
    
    def load_and_display_image(self, image_id, face, label):
        """Lade Bild und zeige es an"""
        def load_thread():
            card_name = "Unknown"  # TODO: Get from current card
            image_path = self.image_handler.get_image_path(card_name, image_id, face)
            
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize(CARD_IMAGE_SIZE, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    label.config(image=photo)
                    label.image = photo
                except Exception as e:
                    print(f"Fehler beim Anzeigen: {e}")
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def save_notes(self):
        """Speichere Notizen"""
        if not self.current_card:
            return
        
        notes = self.card_notes.get('1.0', 'end-1c')
        self.card_manager.update_notes(self.current_card, notes)
    
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
                # Zeige visuelles Feedback
                widget.config(cursor="hand2")
    
    def on_enter_drop_zone(self, event, target):
        """Maus betritt Drop-Zone"""
        if self.drag_data["card_id"]:
            event.widget.config(bg='lightblue')
            self.drag_data["current_target"] = target
    
    def on_leave_drop_zone(self, event):
        """Maus verlässt Drop-Zone"""
        event.widget.config(bg='white')
        if "current_target" in self.drag_data:
            del self.drag_data["current_target"]
    
    def check_drop(self, event, target):
        """Prüfe ob Drop stattfinden soll (ButtonRelease über Drop-Zone)"""
        if self.drag_data.get("card_id") and self.drag_data.get("current_target") == target:
            self.on_drop_to_deck(event, target)
    
    def on_drop_to_deck(self, event, target):
        """Drop auf Deck (wird automatisch beim Loslassen aufgerufen)"""
        if not self.drag_data["card_id"]:
            return
        
        card_id = self.drag_data["card_id"]
        
        # Bestimme Ziel-Deck
        if target == 'current':
            deck_id = self.current_deck_id
        elif target == 'last' and len(self.deck_history) > 0:
            deck_id = self.deck_history[0]
        elif target == 'prev' and len(self.deck_history) > 1:
            deck_id = self.deck_history[1]
        else:
            deck_id = None
        
        if deck_id:
            self.deck_manager.add_card_to_deck(deck_id, card_id)
            self.refresh_deck_display(deck_id, target)
            messagebox.showinfo("Erfolg", "Karte zum Deck hinzugefügt!")
        else:
            messagebox.showwarning("Warnung", "Kein Ziel-Deck verfügbar")
        
        # Reset
        self.reset_drag_state()
    
    def reset_drag_state(self):
        """Setze Drag-State zurück"""
        if "widget" in self.drag_data and self.drag_data["widget"]:
            self.drag_data["widget"].config(cursor="")
        
        # Farben zurücksetzen
        self.current_deck_listbox.config(bg='white')
        self.last_deck_listbox.config(bg='white')
        self.prev_deck_listbox.config(bg='white')
        
        self.drag_data = {"card_id": None, "source": None}
    
    # === RECHTSKLICK-MENÜS ===
    
    def on_random_card_right_click(self, event):
        """Rechtsklick auf zufällige Karte"""
        sel = self.random_listbox.curselection()
        if not sel:
            return
        
        display = self.random_listbox.get(sel[0])
        card_id = self.random_card_data.get(display)
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Neues Deck mit dieser Karte erstellen", 
                        command=lambda: self.create_deck_with_card(card_id))
        menu.add_separator()
        menu.add_command(label="Zu aktuellem Deck hinzufügen", 
                        command=lambda: self.add_to_current_deck(card_id))
        menu.add_command(label="Zu Deck hinzufügen...", 
                        command=lambda: self.add_to_deck_dialog(card_id))
        menu.add_separator()
        menu.add_command(label="Details anzeigen", 
                        command=lambda: self.show_card_details(card_id))
        
        menu.post(event.x_root, event.y_root)
    
    def on_deck_card_right_click(self, event):
        """Rechtsklick auf Karte im Deck"""
        # TODO: Implementieren
        pass
    
    def on_deck_right_click(self, event):
        """Rechtsklick auf Deck in Liste"""
        sel = self.all_decks_listbox.curselection()
        if not sel:
            return
        
        display = self.all_decks_listbox.get(sel[0])
        deck_id = self.all_deck_data.get(display)
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Öffnen", command=lambda: self.load_deck(deck_id))
        menu.add_command(label="Löschen", command=lambda: self.delete_deck(deck_id))
        
        menu.post(event.x_root, event.y_root)
    
    def create_deck_with_card(self, card_id):
        """Erstelle neues Deck mit dieser Karte"""
        card = self.card_manager.get_card(card_id)
        
        # Deck-Name vorschlagen
        suggested_name = f"Deck mit {card['name']}"
        name = simpledialog.askstring("Neues Deck", "Deck-Name:", initialvalue=suggested_name)
        
        if name:
            deck_id = self.deck_manager.create_deck(name)
            if deck_id:
                self.deck_manager.add_card_to_deck(deck_id, card_id)
                messagebox.showinfo("Erfolg", f"Deck '{name}' erstellt mit {card['name']}!")
                self.refresh_all_decks()
                self.load_deck(deck_id)
    
    def show_enlarged_image(self):
        """Zeige vergrößertes Kartenbild in Pop-up"""
        if not self.current_card:
            messagebox.showinfo("Info", "Keine Karte ausgewählt")
            return
        
        card = self.card_manager.get_card(self.current_card)
        image_id = card.get('image_id')
        
        if not image_id:
            messagebox.showinfo("Info", "Kein Bild verfügbar")
            return
        
        # Pop-up erstellen
        popup = tk.Toplevel(self.root)
        popup.title(f"{card['name']} - Vergrößert")
        popup.geometry("800x600")
        
        # Container für Bilder
        container = tk.Frame(popup, bg='black')
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Prüfe ob Doppelkarte
        is_dfc, back_card = self.card_manager.is_double_faced(image_id)
        
        # Labels für Bilder
        front_label = tk.Label(container, bg='black')
        front_label.pack(side='left', padx=10)
        
        if is_dfc:
            back_label = tk.Label(container, bg='black')
            back_label.pack(side='left', padx=10)
        
        # Bilder laden (größer)
        def load_large_images():
            card_name = card['name']
            
            # Vorderseite
            front_path = self.image_handler.get_image_path(card_name, image_id, 'front')
            if front_path:
                try:
                    img = Image.open(front_path)
                    img = img.resize((375, 525), Image.Resampling.LANCZOS)  # 1.5x größer
                    photo = ImageTk.PhotoImage(img)
                    front_label.config(image=photo)
                    front_label.image = photo
                except:
                    pass
            
            # Rückseite (falls DFC)
            if is_dfc:
                back_path = self.image_handler.get_image_path(card_name, image_id, 'back')
                if back_path:
                    try:
                        img = Image.open(back_path)
                        img = img.resize((375, 525), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        back_label.config(image=photo)
                        back_label.image = photo
                    except:
                        pass
        
        threading.Thread(target=load_large_images, daemon=True).start()
    
    def add_to_current_deck(self, card_id):
        """Füge Karte zu aktuellem Deck hinzu"""
        if not self.current_deck_id:
            messagebox.showwarning("Warnung", "Kein Deck geladen")
            return
        
        self.deck_manager.add_card_to_deck(self.current_deck_id, card_id)
        self.refresh_deck_display(self.current_deck_id, 'current')
        messagebox.showinfo("Erfolg", "Karte hinzugefügt!")
    
    def add_to_deck_dialog(self, card_id):
        """Dialog: Zu welchem Deck hinzufügen?"""
        decks = self.deck_manager.get_all_decks()
        
        if not decks:
            messagebox.showinfo("Info", "Erstelle zuerst ein Deck")
            return
        
        deck_names = [d['name'] for d in decks]
        
        # Einfacher Dialog
        choice = simpledialog.askstring("Zu Deck hinzufügen", 
                                       f"Deck-Namen eingeben:\n{', '.join(deck_names)}")
        
        if choice:
            deck = next((d for d in decks if d['name'] == choice), None)
            if deck:
                self.deck_manager.add_card_to_deck(deck['id'], card_id)
                messagebox.showinfo("Erfolg", f"Karte zu '{choice}' hinzugefügt!")
    
    # === DECK-VERWALTUNG ===
    
    def create_new_deck_dialog(self):
        """Erstelle neues Deck"""
        name = simpledialog.askstring("Neues Deck", "Deck-Name:")
        
        if name:
            deck_id = self.deck_manager.create_deck(name)
            if deck_id:
                messagebox.showinfo("Erfolg", f"Deck '{name}' erstellt!")
                self.refresh_all_decks()
                self.load_deck(deck_id)
    
    def load_deck(self, deck_id):
        """Lade Deck in aktuelles Deck (Spalte 3)"""
        self.current_deck_id = deck_id
        
        # History aktualisieren
        if deck_id in self.deck_history:
            self.deck_history.remove(deck_id)
        self.deck_history.insert(0, deck_id)
        self.deck_history = self.deck_history[:2]  # Nur 2 behalten
        
        self.refresh_deck_display(deck_id, 'current')
        self.refresh_history_decks()
    
    def refresh_deck_display(self, deck_id, target):
        """Aktualisiere Deck-Anzeige"""
        deck = self.deck_manager.get_deck(deck_id)
        cards = self.deck_manager.get_deck_cards(deck_id)
        
        if target == 'current':
            self.current_deck_label.config(text=deck['name'])
            listbox = self.current_deck_listbox
        elif target == 'last':
            listbox = self.last_deck_listbox
        elif target == 'prev':
            listbox = self.prev_deck_listbox
        else:
            return
        
        listbox.delete(0, 'end')
        
        for card in cards:
            display = f"{card['name']} ({card['deck_quantity']}x) [{card['role']}]"
            listbox.insert('end', display)
    
    def refresh_history_decks(self):
        """Aktualisiere History-Spalte"""
        if len(self.deck_history) > 0:
            self.refresh_deck_display(self.deck_history[0], 'last')
        
        if len(self.deck_history) > 1:
            self.refresh_deck_display(self.deck_history[1], 'prev')
    
    def refresh_all_decks(self):
        """Aktualisiere Deck-Liste (Spalte 5)"""
        decks = self.deck_manager.get_all_decks()
        
        self.all_decks_listbox.delete(0, 'end')
        self.all_deck_data = {}
        
        for deck in decks:
            display = deck['name']
            self.all_decks_listbox.insert('end', display)
            self.all_deck_data[display] = deck['id']
    
    def on_deck_select(self, event):
        """Doppelklick auf Deck in Liste"""
        sel = self.all_decks_listbox.curselection()
        if not sel:
            return
        
        display = self.all_decks_listbox.get(sel[0])
        deck_id = self.all_deck_data.get(display)
        
        if deck_id:
            self.load_deck(deck_id)
    
    def load_deck_from_history(self, index):
        """Klick auf History-Deck"""
        if index < len(self.deck_history):
            self.load_deck(self.deck_history[index])
    
    def on_deck_card_double_click(self, event):
        """Doppelklick auf Karte im Deck"""
        # TODO: Zeige Kartendetails
        pass
    
    def delete_deck(self, deck_id):
        """Lösche Deck"""
        deck = self.deck_manager.get_deck(deck_id)
        
        if messagebox.askyesno("Bestätigen", f"Deck '{deck['name']}' löschen?"):
            self.deck_manager.delete_deck(deck_id)
            self.refresh_all_decks()
            
            if self.current_deck_id == deck_id:
                self.current_deck_id = None
                self.current_deck_label.config(text="Kein Deck geladen")
                self.current_deck_listbox.delete(0, 'end')
    
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