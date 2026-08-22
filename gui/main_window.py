"""
MTG Deck Builder v1.1 - Main Window (Refactored)
Verbindet alle Panels
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
import sys
import threading

sys.path.append(str(Path(__file__).parent.parent))
from core.card_manager import CardManager
from core.collection_manager import CollectionManager
from core.deck_manager import DeckManager
from core.image_handler import ImageHandler
from utils.import_script import CardImporter

# GUI Panels
from gui.cards_panel import CardsPanel
from gui.details_panel import DetailsPanel
from gui.workspace_panel import WorkspacePanel
from gui.preview_panel import VisualPreviewPanel
from gui.decks_panel import DecksPanel
from gui.dialogs import (RoleDialog, AddToDeckDialog, NewDeckDialog, 
                         ImportProgressDialog, EnlargedImageDialog)


class MainWindow:
    def __init__(self, root):
        self.root = root
        
        # Manager
        self.card_manager = CardManager()
        self.collection_manager = CollectionManager()
        self.deck_manager = DeckManager()
        self.image_handler = ImageHandler()
        self.importer = CardImporter()
        
        # Drag & Drop State
        self.drag_data = {"card_id": None, "widget": None}
        
        # Panels (werden in setup_gui erstellt)
        self.cards_panel = None
        self.details_panel = None
        self.workspace_panel = None
        self.preview_panel = None
        self.decks_panel = None
        
        self.setup_gui()
    
    def setup_gui(self):
        """Erstelle GUI"""
        # Menüleiste
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Karten importieren", command=self.start_import)
        file_menu.add_command(label="Deck importieren", command=self.import_deck)
        file_menu.add_command(label="Sets aktualisieren", command=self.update_sets)
        file_menu.add_command(label="Neues Deck", command=self.create_new_deck)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        file_menu.add_command(label="DFC-Texte aktualisieren", command=self.update_dfc_texts)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Einstellungen", menu=settings_menu)
        settings_menu.add_command(label="Anzahl zufälliger Karten", command=self.set_random_count)
        
        # Hauptbereich: Frame mit Grid
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Grid-Gewichtung (prozentual)
        main_frame.grid_columnconfigure(0, weight=1, minsize=300)   # 20%
        main_frame.grid_columnconfigure(1, weight=1, minsize=300)   # 25%
        main_frame.grid_columnconfigure(2, weight=2, minsize=300)   # 20%
        main_frame.grid_columnconfigure(3, weight=2, minsize=520)   # 20%
        main_frame.grid_columnconfigure(4, weight=2, minsize=500)   # 15%
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Spalte 1: Karten
        col1 = tk.Frame(main_frame, relief='raised', borderwidth=1)
        col1.grid(row=0, column=0, sticky='nsew')
        self.cards_panel = CardsPanel(col1, self.card_manager,
                                      on_card_select=self.on_card_select,
                                      on_right_click=self.on_cards_right_click,
                                      on_drag_start=self.on_drag_start,
                                      on_drag_motion=self.on_drag_motion,
                                      on_double_click=self.on_card_double_click)
        
        # Spalte 2: Details
        col2 = tk.Frame(main_frame, relief='raised', borderwidth=1)
        col2.grid(row=0, column=1, sticky='nsew')
        self.details_panel = DetailsPanel(col2, self.card_manager, self.image_handler,
                                         on_enlarge_image=self.show_enlarged_image)
        
        # Spalte 3: Arbeitsbereich
        col3 = tk.Frame(main_frame, relief='raised', borderwidth=1)
        col3.grid(row=0, column=2, sticky='nsew')
        self.workspace_panel = WorkspacePanel(col3, self.deck_manager,
                                              on_card_click=self.on_card_select,
                                              on_card_right_click=self.on_workspace_card_right_click,
                                              on_enter_drop=self.on_enter_drop_zone,
                                              on_leave_drop=self.on_leave_drop_zone)
        
        # Spalte 4: Vorschau
        col4 = tk.Frame(main_frame, relief='raised', borderwidth=1)
        col4.grid(row=0, column=3, sticky='nsew')
        self.preview_panel = VisualPreviewPanel(col4, self.deck_manager, self.image_handler,
                                         on_card_click=self.on_card_select,
                                         on_load_to_workspace=self.load_preview_to_workspace)
        
        # Spalte 5: Alle Decks
        col5 = tk.Frame(main_frame, relief='raised', borderwidth=1)
        col5.grid(row=0, column=4, sticky='nsew')
        self.decks_panel = DecksPanel(col5, self.deck_manager,
                                      on_deck_click=self.on_deck_click,
                                      on_deck_double_click=self.on_deck_double_click,
                                      on_deck_right_click=self.on_deck_right_click)
    
    # === CALLBACKS ===
    
    def import_deck(self):
        """Importiere Deck aus TXT-Datei"""
        from tkinter import filedialog
        from utils.deck_importer import DeckImporter
        
        filename = filedialog.askopenfilename(
            title="Deck importieren",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        importer = DeckImporter()
        result = importer.import_from_txt(filename)
        
        if result['success']:
            msg = f"✓ Deck '{result['deck_name']}' importiert!\n\n"
            msg += f"Karten: {result['imported']}\n"
            
            if result['errors']:
                msg += f"\nFehler ({len(result['errors'])}):\n"
                msg += "\n".join(result['errors'][:10])
                if len(result['errors']) > 10:
                    msg += f"\n... und {len(result['errors'])-10} weitere"
            
            messagebox.showinfo("Import erfolgreich", msg)
            
            # Refresh Panels
            self.decks_panel.refresh()
            self.workspace_panel.load_deck(result['deck_id'])
        else:
            messagebox.showerror("Import fehlgeschlagen", result['error'])
    
    def on_card_select(self, card_id):
        """Karte wurde ausgewählt"""
        self.details_panel.show_card(card_id)
    
    def on_cards_right_click(self, event, card_id):
        """Rechtsklick auf Karte in Liste"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Neues Deck mit dieser Karte", 
                        command=lambda: self.create_deck_with_card(card_id))
        menu.add_separator()
        menu.add_command(label="Zu Arbeitsbereich hinzufügen", 
                        command=lambda: self.add_to_workspace(card_id, event))
        menu.add_command(label="Zu Deck hinzufügen...", 
                        command=lambda: self.add_to_deck_dialog(card_id, event))
        menu.add_separator()
        menu.add_command(label="✓ Im Besitz markieren",  # NEU
                        command=lambda: self.mark_card_owned(card_id, event))
        menu.add_command(label="⭐ Zur Wunschliste",  # NEU
                        command=lambda: self.toggle_wishlist(card_id, event))
        
        menu.post(event.x_root, event.y_root)
        
    def on_card_double_click(self, card_id):
        """Doppelklick auf Karte - füge zu Workspace hinzu"""
        if not self.workspace_panel.current_deck_id:
            messagebox.showwarning("Warnung", "Kein Deck im Arbeitsbereich")
            return
        
        self.deck_manager.add_card_to_deck(self.workspace_panel.current_deck_id, card_id, 'card', 1)
        self.workspace_panel.refresh()
        # Optional: Feedback
        print(f"✓ Karte hinzugefügt!")
    
    def on_workspace_card_right_click(self, event, card_ids):
        """Rechtsklick auf Karte(n) im Arbeitsbereich"""
        
        print(f"DEBUG: card_ids = {card_ids}, type = {type(card_ids)}")  # DEBUG
        
        if len(card_ids) > 1:
            # Multi-Select Menu
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=f"✓ {len(card_ids)} Karten als Besitz markieren", 
                            command=lambda: self.mark_cards_owned_bulk(card_ids, event))
            menu.add_command(label=f"⭐ {len(card_ids)} zur Wunschliste",
                            command=lambda: self.mark_cards_wishlist_bulk(card_ids, event))
            menu.add_separator()
            menu.add_command(label=f"🔄 {len(card_ids)} als Karte markieren",  # NEU
                            command=lambda: self.change_cards_role_bulk(card_ids, 'card', event))
            menu.add_command(label=f"🔄 {len(card_ids)} als Sideboard markieren",  # NEU
                            command=lambda: self.change_cards_role_bulk(card_ids, 'sideboard', event))
            menu.add_separator()
            menu.add_command(label=f"✕ {len(card_ids)} Karten aus Deck entfernen", 
                            command=lambda: self.remove_cards_bulk(card_ids, event))
        else:
            # Single-Select Menu
            print("DEBUG: Single-Select Menu")  # DEBUG
            card_id = card_ids[0]
            menu = tk.Menu(self.root, tearoff=0)
            
            print("DEBUG: Adding menu items...")  # DEBUG
            
            menu.add_command(label="Aus Deck entfernen", 
                            command=lambda: self.remove_from_workspace(card_id))
            menu.add_separator()
            menu.add_command(label="Als Commander markieren", 
                            command=lambda: self.change_card_role(card_id, 'commander'))
            menu.add_command(label="Als Sideboard markieren", 
                            command=lambda: self.change_card_role(card_id, 'sideboard'))
            menu.add_command(label="Als Karte markieren", 
                            command=lambda: self.change_card_role(card_id, 'card'))
            menu.add_separator()
            menu.add_command(label="✓ Im Besitz markieren", 
                            command=lambda: self.mark_card_owned(card_id))
            print("DEBUG: Adding wishlist item...")  # DEBUG
            menu.add_command(label="⭐ Zur Wunschliste",  # NEU
                            command=lambda: self.toggle_wishlist(card_id))
            print("DEBUG: Menu created, showing...")  # DEBUG
        
        menu.post(event.x_root, event.y_root)
        print("DEBUG: Menu posted!")  # DEBUG
        
    def change_cards_role_bulk(self, card_ids, new_role, event=None):
        for card_id in card_ids:
            self.deck_manager.change_card_role(self.workspace_panel.current_deck_id, card_id, new_role)
        self.workspace_panel.refresh()
        messagebox.showinfo("Erfolg", f"✓ {len(card_ids)} Karten geändert!")
        
    def toggle_wishlist(self, card_id, event=None):
        """Toggle Wunschliste für eine Karte"""
        from core.collection_manager import CollectionManager
        collection = CollectionManager()
        
        card = self.card_manager.get_card(card_id)
        is_wishlist = card.get('wishlist', 0)
        
        if is_wishlist:
            collection.mark_wishlist(card_id, False)
            messagebox.showinfo("Info", f"✓ {card['name']} von Wunschliste entfernt")
        else:
            collection.mark_wishlist(card_id, True)
            messagebox.showinfo("Erfolg", f"⭐ {card['name']} zur Wunschliste hinzugefügt!")
        
        # Refresh
        if self.details_panel.current_card_id == card_id:
            self.details_panel.show_card(card_id)

    def mark_cards_wishlist_bulk(self, card_ids, event=None):
        """Markiere mehrere Karten als Wunschliste"""
        from core.collection_manager import CollectionManager
        collection = CollectionManager()
        
        for card_id in card_ids:
            collection.mark_wishlist(card_id, True)
        
        messagebox.showinfo("Erfolg", f"⭐ {len(card_ids)} Karten zur Wunschliste hinzugefügt!")
    
    def on_deck_click(self, deck_id):
        """Einfacher Klick auf Deck → Vorschau"""
        self.preview_panel.load_deck(deck_id)
        
    def on_deck_right_click(self, event, deck_id):
        """Rechtsklick auf Deck"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Vorschau anzeigen", 
                        command=lambda: self.preview_panel.load_deck(deck_id))
        menu.add_command(label="In Arbeitsbereich laden", 
                        command=lambda: self.workspace_panel.load_deck(deck_id))
        menu.add_command(label="✏️ Deck umbenennen",  # NEU
                        command=lambda: self.rename_deck(deck_id))
        menu.add_separator()
        menu.add_command(label="Löschen", command=lambda: self.delete_deck(deck_id))
        
        menu.post(event.x_root, event.y_root)
    
    def on_deck_double_click(self, deck_id):
        """Doppelklick auf Deck → Arbeitsbereich"""
        self.workspace_panel.load_deck(deck_id)
    
        
    def mark_cards_owned_bulk(self, card_ids, event=None):
        """Markiere mehrere Karten als im Besitz"""
        from core.collection_manager import CollectionManager
        from tkinter import simpledialog
        
        qty = simpledialog.askinteger(
            "Bulk Besitz",
            f"{len(card_ids)} Karten markieren\n\nAnzahl pro Karte:",
            initialvalue=1,
            minvalue=0,
            maxvalue=999
        )
        
        if qty is not None:
            collection = CollectionManager()
            for card_id in card_ids:
                collection.set_quantity(card_id, qty)
        
        
    def remove_cards_bulk(self, card_ids, event=None):
        """Entferne mehrere Karten aus Deck"""
        if not self.workspace_panel.current_deck_id:
            return
        
        if messagebox.askyesno("Bestätigen", f"{len(card_ids)} Karten aus Deck entfernen?"):
            for card_id in card_ids:
                self.deck_manager.remove_card_from_deck(self.workspace_panel.current_deck_id, card_id)
            
            self.workspace_panel.refresh()
    
    def add_to_workspace(self, card_id, event=None):
        """Füge Karte zu Arbeitsbereich hinzu"""
        if not self.workspace_panel.current_deck_id:
            messagebox.showwarning("Warnung", "Kein Deck im Arbeitsbereich")
            return
        
        role = RoleDialog.ask(self.root)
        if role:
            self.deck_manager.add_card_to_deck(self.workspace_panel.current_deck_id, card_id, role)
            self.workspace_panel.refresh()
            
    def mark_card_owned(self, card_id, event=None):  # event hinzufügen
        """Markiere Karte als im Besitz"""
        from core.collection_manager import CollectionManager
        from tkinter import simpledialog
        
        collection = CollectionManager()
        card = self.card_manager.get_card(card_id)
        current_qty = card.get('quantity', 0)
        
        # Dialog an Mausposition
        dialog_parent = self.root
        qty = simpledialog.askinteger(
            "Im Besitz",
            f"{card['name']}\n\nAktuell: {current_qty}x\n\nNeue Anzahl:",
            initialvalue=max(1, current_qty),
            minvalue=0,
            maxvalue=999,
            parent=dialog_parent
        )
        
        if qty is not None:
            collection.set_quantity(card_id, qty)
            if qty > 0:
                messagebox.showinfo("Erfolg", f"✓ {qty}x {card['name']} markiert!")
            else:
                messagebox.showinfo("Erfolg", f"✓ {card['name']} nicht mehr im Besitz")
            
            # Refresh Details falls angezeigt
            if self.details_panel.current_card_id == card_id:
                self.details_panel.show_card(card_id)
    
    def add_to_deck_dialog(self, card_id, event=None):
        """Dialog: Zu welchem Deck?"""
        decks = self.deck_manager.get_all_decks()
        AddToDeckDialog.show(self.root, card_id, decks, self.card_manager, self.deck_manager)
        
        # Refresh Panels
        if self.workspace_panel.current_deck_id:
            self.workspace_panel.refresh()
        if self.preview_panel.preview_deck_id:
            self.preview_panel.build_tree(self.preview_panel.preview_deck_id)
    
    def remove_from_workspace(self, card_id):
        """Entferne Karte aus Arbeitsbereich"""
        if not self.workspace_panel.current_deck_id:
            return
        
        self.deck_manager.remove_card_from_deck(self.workspace_panel.current_deck_id, card_id)
        self.workspace_panel.refresh()
    
    def change_card_role(self, card_id, new_role):
        """Ändere Rolle einer Karte"""
        if not self.workspace_panel.current_deck_id:
            return
        
        self.deck_manager.change_card_role(self.workspace_panel.current_deck_id, card_id, new_role)
        self.workspace_panel.refresh()
    
    def create_new_deck(self):
        """Erstelle neues Deck"""
        name = NewDeckDialog.ask(self.root)
        
        if name:
            deck_id = self.deck_manager.create_deck(name)
            if deck_id:
                messagebox.showinfo("Erfolg", f"Deck '{name}' erstellt!")
                self.decks_panel.refresh()
                self.workspace_panel.load_deck(deck_id)
    
    def create_deck_with_card(self, card_id):
        """Erstelle Deck mit dieser Karte"""
        card = self.card_manager.get_card(card_id)
        suggested_name = f"Deck mit {card['name']}"
        
        name = NewDeckDialog.ask(self.root, suggested_name)
        
        if name:
            deck_id = self.deck_manager.create_deck(name)
            if deck_id:
                role = RoleDialog.ask(self.root)
                if role:
                    self.deck_manager.add_card_to_deck(deck_id, card_id, role)
                    messagebox.showinfo("Erfolg", f"Deck '{name}' erstellt!")
                    self.decks_panel.refresh()
                    self.workspace_panel.load_deck(deck_id)
    
    def delete_deck(self, deck_id):
        """Lösche Deck"""
        deck = self.deck_manager.get_deck(deck_id)
        
        if messagebox.askyesno("Bestätigen", f"Deck '{deck['name']}' löschen?"):
            self.deck_manager.delete_deck(deck_id)
            self.decks_panel.refresh()
            
            if self.workspace_panel.current_deck_id == deck_id:
                self.workspace_panel.close()
            
            if self.preview_panel.preview_deck_id == deck_id:
                self.preview_panel.clear()
    
    def load_preview_to_workspace(self, deck_id):
        """Lade Vorschau in Arbeitsbereich"""
        self.workspace_panel.load_deck(deck_id)
    
    # === DRAG & DROP ===
    
    def on_drag_start(self, event, card_id, widget):
        """Start Drag"""
        self.drag_data["card_id"] = card_id
        self.drag_data["widget"] = widget
        widget.config(cursor="hand2")
    
    def on_drag_motion(self, event):
        """Drag Motion"""
        if self.drag_data["widget"]:
            self.drag_data["widget"].config(cursor="hand2")
    
    def on_enter_drop_zone(self, event, target):
        """Maus betritt Drop-Zone"""
        if self.drag_data["card_id"] and target == 'workspace':
            try:
                event.widget.config(background='lightgreen')
            except:
                pass  # Widget unterstützt kein background
            self.drag_data["current_target"] = target

    def on_leave_drop_zone(self, event):
        """Maus verlässt Drop-Zone"""
        try:
            event.widget.config(background='white')
        except:
            pass  # Widget unterstützt kein background
        if "current_target" in self.drag_data:
            del self.drag_data["current_target"]
    
    # === SONSTIGES ===
    
    def show_enlarged_image(self, card_id):
        """Zeige vergrößertes Bild"""
        card = self.card_manager.get_card(card_id)
        EnlargedImageDialog(self.root, card, self.image_handler, self.card_manager)
    
    def set_random_count(self):
        """Setze Anzahl zufälliger Karten"""
        count = simpledialog.askinteger("Einstellung", 
                                       "Anzahl zufälliger Karten:",
                                       initialvalue=30,
                                       minvalue=10,
                                       maxvalue=100)
        if count:
            self.cards_panel.set_random_count(count)
    
    def start_import(self):
        """Starte Import"""
        progress = ImportProgressDialog(self.root)
        
        def import_thread():
            result = self.importer.import_all_cards(
                progress_callback=progress.update_status,
                clear_existing=True
            )
            
            progress.close()
            
            if result['success']:
                messagebox.showinfo("Erfolg", f"{result['imported']} Karten importiert!")
                self.cards_panel.load_random_cards()
            else:
                messagebox.showerror("Fehler", result.get('error'))
        
        threading.Thread(target=import_thread, daemon=True).start()
        
    def update_sets(self):
        """Prüfe und importiere neue Sets"""
        from utils.set_updater import SetUpdater
        from tkinter import simpledialog
        
        updater = SetUpdater()
        
        # Prüfe neue Sets
        print("Prüfe verfügbare Sets...")
        new_sets = updater.check_new_sets()
        
        if not new_sets:
            messagebox.showinfo("Sets aktuell", "Keine neuen Sets verfügbar!")
            return
        
        # Zeige Dialog mit verfügbaren Sets
        dialog = tk.Toplevel(self.root)
        dialog.title("Neue Sets verfügbar")
        dialog.geometry("500x400")
        
        tk.Label(dialog, text="Verfügbare Sets:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Listbox mit Sets
        listbox_frame = tk.Frame(dialog)
        listbox_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, selectmode='multiple')
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Fülle Listbox
        for s in new_sets:
            listbox.insert('end', f"{s['name']} ({s['code']}) - {s['card_count']} Karten - Released: {s['released']}")
        
        # Import Button
        def import_selected():
            selected = listbox.curselection()
            if not selected:
                messagebox.showwarning("Keine Auswahl", "Bitte Sets auswählen")
                return
            
            dialog.destroy()
            
            # Importiere ausgewählte Sets
            for idx in selected:
                set_info = new_sets[idx]
                self.import_single_set(set_info, updater)
        
        tk.Button(dialog, text="Ausgewählte Sets importieren", 
                 command=import_selected, font=('Arial', 10, 'bold')).pack(pady=10)

    def import_single_set(self, set_info, updater):
        """Importiere einzelnes Set mit Progress"""
        from gui.dialogs import ImportProgressDialog
        
        progress = ImportProgressDialog(self.root)
        progress.window.title(f"Importiere {set_info['name']}")
        
        def progress_callback(current, total, name):
            progress.update_status(current, total, name)
        
        def import_thread():
            result = updater.import_set(set_info['code'], progress_callback)
            progress.close()
            
            if result['success']:
                msg = f"✓ {set_info['name']} importiert!\n\n"
                msg += f"Karten: {result['imported']}\n"
                
                if result['errors']:
                    msg += f"\nFehler: {len(result['errors'])}"
                
                messagebox.showinfo("Import erfolgreich", msg)
                self.root.after(0, self.cards_panel.load_random_cards)
            else:
                messagebox.showerror("Import fehlgeschlagen", result['error'])
        
        import threading
        threading.Thread(target=import_thread, daemon=True).start()
        
    def rename_deck(self, deck_id):
        """Deck umbenennen"""
        from tkinter import simpledialog
        
        deck = self.deck_manager.get_deck(deck_id)
        new_name = simpledialog.askstring("Deck umbenennen", 
                                          "Neuer Name:", 
                                          initialvalue=deck['name'])
        
        if new_name and new_name != deck['name']:
            try:
                self.deck_manager.db.execute(
                    "UPDATE decks SET name = ? WHERE id = ?",
                    (new_name, deck_id)
                )
                self.deck_manager.db.commit()
                
                messagebox.showinfo("Erfolg", f"✓ Deck umbenannt!")
                self.decks_panel.refresh()
                
                if self.workspace_panel.current_deck_id == deck_id:
                    self.workspace_panel.deck_label.config(text=new_name)
            except Exception as e:
                messagebox.showerror("Fehler", f"Umbenennen fehlgeschlagen: {e}")
                
    def update_dfc_texts(self):
        """Aktualisiere DFC-Texte"""
        from utils.set_updater import SetUpdater
        
        if messagebox.askyesno("DFC Update", 
                               "Aktualisiert alle Doppelkarten-Texte von Scryfall.\n\nForsetzen?"):
            updater = SetUpdater()
            updater.update_dfc_texts()
            messagebox.showinfo("Fertig", "DFC-Texte aktualisiert!")
