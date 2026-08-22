"""
MTG Color Identity Parser
Extrahiert alle Farbsymbole aus Mana Cost und Card Text
"""

import re

def get_color_identity(card):
    """
    Berechnet die Farbidentität einer Karte
    
    Args:
        card: dict mit 'mana_cost' und 'text'
    
    Returns:
        list: ['W', 'U', 'B', 'R', 'G'] sortiert
    """
    colors = set()
    
    # Parse Mana Cost
    mana_cost = card.get('mana_cost', '')
    colors.update(extract_colors_from_text(mana_cost))
    
    # Parse Card Text
    card_text = card.get('text', '')
    colors.update(extract_colors_from_text(card_text))
    
    # Sortiere nach WUBRG-Reihenfolge
    color_order = {'W': 0, 'U': 1, 'B': 2, 'R': 3, 'G': 4}
    sorted_colors = sorted(colors, key=lambda c: color_order.get(c, 99))
    
    return sorted_colors


def extract_colors_from_text(text):
    """
    Extrahiert Farbsymbole aus Text
    Findet: {W}, {U}, {B}, {R}, {G}, {W/U}, {2}{G}, etc.
    """
    if not text:
        return set()
    
    colors = set()
    
    # Regex für Mana-Symbole: {W}, {U}, {B}, {R}, {G}
    # Auch Hybrid: {W/U}, {2/W}, etc.
    pattern = r'\{[^}]*([WUBRG])[^}]*\}'
    
    matches = re.findall(pattern, text)
    colors.update(matches)
    
    return colors


def get_color_name(color_code):
    """Wandelt W/U/B/R/G in Namen um"""
    names = {
        'W': 'White',
        'U': 'Blue',
        'B': 'Black',
        'R': 'Red',
        'G': 'Green'
    }
    return names.get(color_code, '?')


def format_color_identity(colors):
    """
    Formatiert Farbidentität für Anzeige
    """
    if not colors:
        return "Colorless"
    
    if len(colors) == 1:
        return f"Mono-{get_color_name(colors[0])}"
    
    # Farbnamen
    color_names = '/'.join([get_color_name(c) for c in colors])
    
    # 2-Farben: Gilden
    if len(colors) == 2:
        guilds = {
            'WU': 'Azorius', 'UB': 'Dimir', 'BR': 'Rakdos',
            'RG': 'Gruul', 'GW': 'Selesnya', 'WB': 'Orzhov',
            'UR': 'Izzet', 'BG': 'Golgari', 'RW': 'Boros', 'GU': 'Simic'
        }
        guild_key = ''.join(colors)
        guild_name = guilds.get(guild_key, '')
        
        if guild_name:
            return f"{color_names} ({guild_name})"
    
    # 3-Farben: Shards & Wedges
    elif len(colors) == 3:
        tri_colors = {
            'WUB': 'Esper', 'UBR': 'Grixis', 'BRG': 'Jund',
            'RGW': 'Naya', 'GWU': 'Bant',
            'WBG': 'Abzan', 'URW': 'Jeskai', 'BGU': 'Sultai',
            'RWB': 'Mardu', 'GUR': 'Temur'
        }
        tri_key = ''.join(colors)
        tri_name = tri_colors.get(tri_key, '')
        
        if tri_name:
            return f"{color_names} ({tri_name})"
    
    # 4-Farben
    elif len(colors) == 4:
        four_colors = {
            'UBRG': 'Glint (no-White)',
            'WBRG': 'Dune (no-Blue)', 
            'WURG': 'Ink (no-Black)',
            'WUBG': 'Witch (no-Red)',
            'WUBR': 'Yore (no-Green)'
        }
        four_key = ''.join(colors)
        four_name = four_colors.get(four_key, '4-Color')
        
        return f"{color_names} ({four_name})"
    
    # 5-Farben
    elif len(colors) == 5:
        return "Five-Color (WUBRG)"
    
    return color_names
    
def get_color_symbol(color_code):
    """Unicode-Symbole für Farben"""
    symbols = {
        'W': '☀',  # Weiß (Sonne)
        'U': '💧', # Blau (Tropfen)
        'B': '💀', # Schwarz (Totenkopf)
        'R': '🔥', # Rot (Feuer)
        'G': '🌳'  # Grün (Baum)
    }
    return symbols.get(color_code, '⚪')