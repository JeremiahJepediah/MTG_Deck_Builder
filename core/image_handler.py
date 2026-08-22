"""
MTG Deck Builder v1.1 - Image Handler
Lädt und cached Kartenbilder (lokal + Scryfall)
"""

import os
from pathlib import Path
import requests
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import IMAGE_DIR, LOCAL_IMAGES, get_scryfall_session


class ImageHandler:
    def __init__(self):
        self.cache_dir = IMAGE_DIR
        self.local_images_dir = Path(LOCAL_IMAGES) if LOCAL_IMAGES else None
        self.cache_dir.mkdir(exist_ok=True)
        self.session = get_scryfall_session()
    
    def get_image_path(self, card_name, image_id, face='front'):
        """
        Hole Pfad zu Kartenbild (sucht lokal, lädt von Scryfall falls nötig)
        
        Args:
            card_name: Name der Karte
            image_id: Scryfall ImageID
            face: 'front' oder 'back'
        
        Returns:
            Path zum Bild oder None
        """
        # 1. Prüfe Cache
        cache_path = self.cache_dir / f"{image_id}_{face}.jpg"
        if cache_path.exists():
            return cache_path
        
        # 2. Prüfe lokale Bilder (nach Kartenname)
        if self.local_images_dir:
            local_path = self.find_local_image(card_name)
            if local_path and face == 'front':  # Lokale Bilder nur für front
                return local_path
        
        # 3. Download von Scryfall
        downloaded_path = self.download_from_scryfall(image_id, face)
        return downloaded_path
    
    def find_local_image(self, card_name):
        """
        Suche lokales Bild nach Kartenname
        Versucht verschiedene Varianten bei Sonderzeichen
        """
        if not self.local_images_dir or not self.local_images_dir.exists():
            return None
        
        # Direkte Suche
        direct_path = self.local_images_dir / f"{card_name}.jpg"
        if direct_path.exists():
            return direct_path
        
        # Versuche ohne Sonderzeichen
        clean_name = card_name.replace(',', '').replace("'", '').replace(':', '')
        clean_path = self.local_images_dir / f"{clean_name}.jpg"
        if clean_path.exists():
            return clean_path
        
        # Versuche mit Unterstrichen
        underscore_name = card_name.replace(' ', '_')
        underscore_path = self.local_images_dir / f"{underscore_name}.jpg"
        if underscore_path.exists():
            return underscore_path
        
        return None

    def download_from_scryfall(self, image_id, face='front'):
        """
        Lädt Bild von Scryfall und cached es
        Nutzt cards.scryfall.io direkt (stabiler als API-Redirect)
        """
        if not image_id:
            return None

        try:
            first = image_id[0]
            second = image_id[1]
            url = f"https://cards.scryfall.io/normal/{face}/{first}/{second}/{image_id}.jpg"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                cache_path = self.cache_dir / f"{image_id}_{face}.jpg"
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                return cache_path
            else:
                print(f"Scryfall returned {response.status_code} for {image_id}")
                return None

        except Exception as e:
            print(f"Fehler beim Download von Scryfall: {e}")
            return None
    
    def cache_exists(self, image_id, face='front'):
        """Prüfe ob Bild bereits gecached ist"""
        cache_path = self.cache_dir / f"{image_id}_{face}.jpg"
        return cache_path.exists()
    
    def clear_cache(self):
        """Lösche alle gecachten Bilder (VORSICHT!)"""
        for file in self.cache_dir.glob("*.jpg"):
            file.unlink()
    
    def get_cache_size(self):
        """Größe des Cache in MB"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.jpg"))
        return total_size / (1024 * 1024)  # MB
    
    def preload_images(self, card_list, face='front', callback=None):
        """
        Lade mehrere Bilder im Voraus (für Deck-Ansicht)
        
        Args:
            card_list: list of card dicts mit 'name' und 'image_id'
            face: 'front' oder 'back'
            callback: Funktion die nach jedem Bild aufgerufen wird (progress)
        """
        for i, card in enumerate(card_list):
            image_id = card.get('image_id')
            card_name = card.get('name')
            
            if image_id:
                self.get_image_path(card_name, image_id, face)
            
            if callback:
                callback(i + 1, len(card_list))
