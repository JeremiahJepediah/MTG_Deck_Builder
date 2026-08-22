"""
MTG Deck Builder v1.1 - Card Parser
Liest Markdown-Dateien und extrahiert Kartendaten + Tags
"""

import re
from pathlib import Path


class CardParser:
    def __init__(self):
        pass
    
    def parse_markdown(self, file_path):
        """
        Liest Markdown-Datei und extrahiert alle Felder
        
        Returns:
            dict mit Kartendaten oder None bei Fehler
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extrahiere Felder mit Regex
            name_m = re.search(r'^# (.+)$', content, re.MULTILINE)
            mana_m = re.search(r'\*\*ManaCost:\*\* (.+)$', content, re.MULTILINE)
            type_m = re.search(r'\*\*Type:\*\* (.+)$', content, re.MULTILINE)
            text_m = re.search(r'\*\*Text:\*\*\n(.+?)(?=\*\*|$)', content, re.DOTALL)
            colors_m = re.search(r'\*\*Colors:\*\* (.+)$', content, re.MULTILINE)
            image_m = re.search(r'\*\*ImageID:\*\* (.+)$', content, re.MULTILINE)
            
            card_data = {
                'name': name_m.group(1) if name_m else file_path.stem,
                'mana_cost': mana_m.group(1) if mana_m else '',
                'type': type_m.group(1) if type_m else '',
                'text': text_m.group(1).strip() if text_m else '',
                'colors': colors_m.group(1) if colors_m else '',
                'image_id': image_m.group(1) if image_m else '',
                'file_path': str(file_path)
            }
            
            return card_data
            
        except Exception as e:
            print(f"Fehler beim Parsen von {file_path}: {e}")
            return None
    
    def extract_tags(self, card_data):
        """
        Extrahiert Tags für Baumstruktur aus Kartendaten
        
        Returns:
            list of tags (z.B. ['white', 'creature', 'flying', 'legendary'])
        """
        tags = []
        
        # Farben
        colors = card_data.get('colors', '').strip()
        if colors:
            # Mehrfarbig?
            color_list = [c.strip() for c in colors.split(',') if c.strip()]
            if len(color_list) > 1:
                # Sortiere für konsistente Guild-Namen
                sorted_colors = ''.join(sorted(color_list))
                tags.append(f'multicolor_{sorted_colors.lower()}')
            else:
                # Einfarbig
                color_map = {
                    'W': 'white',
                    'U': 'blue',
                    'B': 'black',
                    'R': 'red',
                    'G': 'green',
                    'C': 'colorless'
                }
                for c in color_list:
                    if c in color_map:
                        tags.append(color_map[c])
        else:
            tags.append('colorless')
        
        # Typ
        card_type = card_data.get('type', '').lower()
        
        # Haupt-Typen
        if 'creature' in card_type:
            tags.append('creature')
        if 'instant' in card_type:
            tags.append('instant')
        if 'sorcery' in card_type:
            tags.append('sorcery')
        if 'enchantment' in card_type:
            tags.append('enchantment')
        if 'artifact' in card_type:
            tags.append('artifact')
        if 'planeswalker' in card_type:
            tags.append('planeswalker')
        if 'land' in card_type:
            tags.append('land')
        if 'battle' in card_type:
            tags.append('battle')
        
        # Legendary
        if 'legendary' in card_type:
            tags.append('legendary')
        
        # Creature-Fähigkeiten (aus Text extrahieren)
        if 'creature' in card_type:
            card_text = card_data.get('text', '').lower()
            
            abilities = [
                'flying', 'first strike', 'double strike', 'deathtouch',
                'haste', 'hexproof', 'indestructible', 'lifelink',
                'menace', 'reach', 'trample', 'vigilance', 'ward'
            ]
            
            for ability in abilities:
                if ability in card_text:
                    tags.append(ability.replace(' ', '_'))
        
        # Alphabet (erster Buchstabe des Namens)
        name = card_data.get('name', '')
        if name:
            first_letter = name[0].upper()
            
            # Zuordnung zu Gruppen
            if first_letter in ['A', 'B', 'C', 'D']:
                tags.append('alpha_a_d')
            elif first_letter in ['E', 'F', 'G', 'H']:
                tags.append('alpha_e_h')
            elif first_letter in ['I', 'J', 'K', 'L']:
                tags.append('alpha_i_l')
            elif first_letter in ['M', 'N', 'O', 'P']:
                tags.append('alpha_m_p')
            elif first_letter in ['Q', 'R', 'S', 'T']:
                tags.append('alpha_q_t')
            else:
                tags.append('alpha_u_z')
        
        return tags
    
    def parse_mana_cost(self, mana_string):
        """
        Parst Mana-Kosten String und gibt strukturierte Daten zurück
        
        Returns:
            dict mit 'cmc' (converted mana cost) und 'colors'
        """
        if not mana_string:
            return {'cmc': 0, 'colors': []}
        
        # Einfache CMC-Berechnung
        cmc = 0
        colors = set()
        
        # Entferne Klammern
        mana_string = mana_string.replace('{', '').replace('}', '')
        
        # Splitte nach Symbolen
        symbols = mana_string.split()
        
        for symbol in symbols:
            # Zahlen
            if symbol.isdigit():
                cmc += int(symbol)
            # Farb-Symbole
            elif symbol in ['W', 'U', 'B', 'R', 'G']:
                cmc += 1
                colors.add(symbol)
            # X kostet 0
            elif symbol == 'X':
                cmc += 0
        
        return {
            'cmc': cmc,
            'colors': list(colors)
        }
