"""
MTG Deck Builder v1.1 - Dialogs
Alle Dialog-Fenster (Rolle wählen, Deck hinzufügen, etc.)
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox


class RoleDialog:
    """Dialog: Welche Rolle hat die Karte?"""
    
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Rolle wählen")
        self.dialog.geometry("250x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text="Als:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        self.role_var = tk.StringVar(value='card')
        tk.Radiobutton(self.dialog, text="Karte (Standard)", 
                      variable=self.role_var, value='card').pack(anchor='w', padx=20)
        tk.Radiobutton(self.dialog, text="Commander", 
                      variable=self.role_var, value='commander').pack(anchor='w', padx=20)
        tk.Radiobutton(self.dialog, text="Sideboard", 
                      variable=self.role_var, value='sideboard').pack(anchor='w', padx=20)
        
        tk.Button(self.dialog, text="OK", command=self.ok).pack(pady=10)
        
        self.dialog.wait_window()
    
    def ok(self):
        self.result = self.role_var.get()
        self.dialog.destroy()
    
    @staticmethod
    def ask(parent):
        """Zeige Dialog und gib Rolle zurück"""
        dialog = RoleDialog(parent)
        return dialog.result


class AddToDeckDialog:
    """Dialog: Zu welchem Deck hinzufügen?"""
    
    def __init__(self, parent, decks, card_manager, deck_manager):
        self.card_manager = card_manager
        self.deck_manager = deck_manager
        self.decks = decks
        self.card_id = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Zu Deck hinzufügen")
        self.dialog.geometry("300x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text="Deck wählen:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        self.deck_var = tk.StringVar()
        self.deck_combo = ttk.Combobox(self.dialog, textvariable=self.deck_var,
                                       values=[d['name'] for d in decks], state='readonly')
        self.deck_combo.pack(pady=5, padx=10, fill='x')
        
        tk.Label(self.dialog, text="Als:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        self.role_var = tk.StringVar(value='card')
        tk.Radiobutton(self.dialog, text="Karte (Standard)", 
                      variable=self.role_var, value='card').pack(anchor='w', padx=20)
        tk.Radiobutton(self.dialog, text="Commander", 
                      variable=self.role_var, value='commander').pack(anchor='w', padx=20)
        tk.Radiobutton(self.dialog, text="Sideboard", 
                      variable=self.role_var, value='sideboard').pack(anchor='w', padx=20)
        
        tk.Button(self.dialog, text="Hinzufügen", command=self.add).pack(pady=10)
    
    def add(self):
        deck_name = self.deck_var.get()
        if not deck_name:
            return
        
        deck = next((d for d in self.decks if d['name'] == deck_name), None)
        if deck and self.card_id:
            self.deck_manager.add_card_to_deck(deck['id'], self.card_id, self.role_var.get())
            messagebox.showinfo("Erfolg", f"Karte zu '{deck_name}' hinzugefügt!")
            self.dialog.destroy()
    
    @staticmethod
    def show(parent, card_id, decks, card_manager, deck_manager):
        """Zeige Dialog"""
        if not decks:
            messagebox.showinfo("Info", "Erstelle zuerst ein Deck")
            return None
        
        dialog = AddToDeckDialog(parent, decks, card_manager, deck_manager)
        dialog.card_id = card_id
        return dialog


class NewDeckDialog:
    """Dialog: Neues Deck erstellen"""
    
    @staticmethod
    def ask(parent, suggested_name=None):
        """Frage nach Deck-Namen"""
        if suggested_name:
            return simpledialog.askstring("Neues Deck", "Deck-Name:", initialvalue=suggested_name)
        else:
            return simpledialog.askstring("Neues Deck", "Deck-Name:")


class ImportProgressDialog:
    """Progress-Dialog für Karten-Import"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Importiere Karten...")
        self.window.geometry("400x150")
        self.window.transient(parent)
        self.window.grab_set()
        
        tk.Label(self.window, text="Importiere Karten...", pady=20).pack()
        
        self.progress_bar = ttk.Progressbar(self.window, mode='indeterminate')
        self.progress_bar.pack(pady=10, padx=20, fill='x')
        self.progress_bar.start()
        
        self.status_label = tk.Label(self.window, text="")
        self.status_label.pack()
    
    def update_status(self, current, total, name):
        """Update Status-Text"""
        self.status_label.config(text=f"{current}/{total}: {name}")
        self.window.update()
    
    def close(self):
        """Schließe Dialog"""
        self.window.destroy()


class EnlargedImageDialog:
    """Dialog: Vergrößertes Kartenbild"""
    
    def __init__(self, parent, card, image_handler, card_manager):
        self.popup = tk.Toplevel(parent)
        self.popup.title(f"{card['name']} - Vergrößert")
        self.popup.geometry("800x600")
        
        container = tk.Frame(self.popup, bg='black')
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.front_label = tk.Label(container, bg='black')
        self.front_label.pack(side='left', padx=10)
        
        self.back_label = None
        
        # Prüfe Doppelkarte
        image_id = card.get('image_id')
        if image_id:
            is_dfc, back_card = card_manager.is_double_faced(image_id)
            
            if is_dfc:
                self.back_label = tk.Label(container, bg='black')
                self.back_label.pack(side='left', padx=10)
            
            # Lade Bilder in Thread
            import threading
            threading.Thread(target=lambda: self.load_images(card, image_id, is_dfc, image_handler), 
                           daemon=True).start()
    
    def load_images(self, card, image_id, is_dfc, image_handler):
        """Lade Bilder (größer)"""
        from PIL import Image, ImageTk
        
        # Vorderseite
        front_path = image_handler.get_image_path(card['name'], image_id, 'front')
        if front_path:
            try:
                img = Image.open(front_path)
                img = img.resize((375, 525), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.front_label.config(image=photo)
                self.front_label.image = photo
            except:
                pass
        
        # Rückseite
        if is_dfc and self.back_label:
            back_path = image_handler.get_image_path(card['name'], image_id, 'back')
            if back_path:
                try:
                    img = Image.open(back_path)
                    img = img.resize((375, 525), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.back_label.config(image=photo)
                    self.back_label.image = photo
                except:
                    pass
