"""
MTG Deck Builder v1.1 - Details Panel
Spalte 2: Kartendetails (Bild, Text, Notizen)
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
from PIL import Image, ImageTk
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import CARD_IMAGE_SIZE


class DetailsPanel:
    def __init__(self, parent, card_manager, image_handler, on_enlarge_image):
        self.parent = parent
        self.card_manager = card_manager
        self.image_handler = image_handler
        self.on_enlarge_image_callback = on_enlarge_image
        
        self.current_card_id = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Erstelle UI"""
        tk.Label(self.parent, text="Kartendetails", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Bilder
        image_container = tk.Frame(self.parent, background='black')
        image_container.pack(pady=10)
        
        self.image_label_front = tk.Label(image_container, background='black')
        self.image_label_front.pack(side='left', padx=5)
        
        self.image_label_back = tk.Label(image_container, background='black')
        self.image_label_back.pack(side='left', padx=5)
        
        tk.Button(self.parent, text="🔍 Bild vergrößern", 
                 command=self.enlarge_image).pack(pady=5)
        
        # Text
        text_frame = tk.Frame(self.parent)
        text_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tk.Label(text_frame, text="Kartentext:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.card_text = scrolledtext.ScrolledText(text_frame, height=8, wrap='word', state='disabled')
        self.card_text.pack(fill='both', expand=True, pady=5)
        
        tk.Label(text_frame, text="Notizen:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.card_notes = scrolledtext.ScrolledText(text_frame, height=5, wrap='word')
        self.card_notes.pack(fill='both', expand=True)
        self.card_notes.bind('<KeyRelease>', lambda e: self.save_notes())
    
    def show_card(self, card_id):
        """Zeige Kartendetails"""
        self.current_card_id = card_id
        card = self.card_manager.get_card(card_id)
        
        if not card:
            return
        
        # DEBUG
        print(f"DEBUG: Lade Karte: {card['name']} (Set: {card.get('set_code')}, ImageID: {card.get('image_id')})")
        
        # WICHTIG: Lösche alte Bilder zuerst (verhindert Cache-Probleme)
        self.image_label_front.config(image='')
        self.image_label_front.image = None
        self.image_label_back.config(image='')
        self.image_label_back.image = None
        
        # Bilder
        image_id = card.get('image_id')
        if image_id:
            is_dfc, back_card = self.card_manager.is_double_faced(image_id)
            
            if is_dfc:
                self.load_and_display_image(card['name'], image_id, 'front', self.image_label_front)
                self.load_and_display_image(card['name'], image_id, 'back', self.image_label_back)
            else:
                self.load_and_display_image(card['name'], image_id, 'front', self.image_label_front)
                self.image_label_back.config(image='')
                self.image_label_back.image = None
        
        # Text
        text = f"Name: {card['name']}\n"
        text += f"Manakosten: {card['mana_cost']}\n"
        text += f"Typ: {card['type']}\n"
        text += f"Farben: {card['colors']}\n\n"
        text += f"Kartentext:\n{card['text']}\n\n"
                
        if card['owned'] and card.get('quantity', 0) > 0:
            text += f"Im Besitz: ✓ JA ({card['quantity']}x)\n"
        else:
            text += f"Im Besitz: ✗ Nein\n"

        # Wunschliste
        if card.get('wishlist', 0):
            text += f"Wunschliste: ⭐ JA\n"
        else:
            text += f"Wunschliste: ✗ Nein\n"
        
        self.card_text.config(state='normal')
        self.card_text.delete('1.0', 'end')
        self.card_text.insert('1.0', text)
        self.card_text.config(state='disabled')
        
        # Notizen
        notes = card.get('notes') or ''  # Falls None, nimm ''
        self.card_notes.delete('1.0', 'end')
        if notes:  # Nur einfügen wenn nicht leer
            self.card_notes.insert('1.0', str(notes))
    
    def load_and_display_image(self, card_name, image_id, face, label):
        """Lade und zeige Bild"""
        def load_thread():
            image_path = self.image_handler.get_image_path(card_name, image_id, face)
            
            if image_path:
                try:
                    img = Image.open(image_path)
                    img = img.resize(CARD_IMAGE_SIZE, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # WICHTIG: Update im Main Thread
                    label.config(image=photo)
                    label.image = photo  # Referenz halten
                except Exception as e:
                    print(f"Fehler beim Laden von {image_path}: {e}")
                    # Zeige leeres Bild bei Fehler
                    label.config(image='')
                    label.image = None
            else:
                # Kein Bild gefunden - leeres Label
                label.config(image='')
                label.image = None
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def save_notes(self):
        """Speichere Notizen"""
        if not self.current_card_id:
            return
        
        notes = self.card_notes.get('1.0', 'end-1c')
        self.card_manager.update_notes(self.current_card_id, notes)
    
    def enlarge_image(self):
        """Zeige vergrößertes Bild"""
        if self.on_enlarge_image_callback and self.current_card_id:
            self.on_enlarge_image_callback(self.current_card_id)
