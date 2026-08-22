"""
MTG Deck Builder v1.1 - Tree Builder
Generiert Baumstruktur für Browse-Tab
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import COLORS, MULTICOLOR_GUILDS, CARD_TYPES, CREATURE_ABILITIES
from core.card_manager import CardManager


class TreeNode:
    """Repräsentiert einen Knoten im Baum"""
    def __init__(self, name, tag=None, is_leaf=False):
        self.name = name
        self.tag = tag  # Tag-String für Datenbankabfrage
        self.children = []
        self.is_leaf = is_leaf  # True = Enthält Karten, False = Enthält Unterordner
        self.card_count = 0
    
    def add_child(self, child):
        self.children.append(child)
        return child
    
    def __repr__(self):
        return f"TreeNode({self.name}, tag={self.tag}, cards={self.card_count})"


class TreeBuilder:
    def __init__(self):
        self.card_manager = CardManager()
    
    def build_full_tree(self):
        """
        Baut die komplette Baumstruktur
        
        Struktur:
        - Farbe
          - Typ
            - Fähigkeit (nur Creatures) / Legendary
              - Alphabet-Gruppe
                - [Karten]
        
        Returns:
            TreeNode (root)
        """
        root = TreeNode("MTG Karten", tag=None)
        
        # Farben
        color_nodes = self._build_color_nodes()
        for node in color_nodes:
            root.add_child(node)
        
        return root
    
    def _build_color_nodes(self):
        """Erstelle Farb-Knoten"""
        nodes = []
        
        # Einfarbige
        for color_code, color_name in COLORS.items():
            tag = color_name.lower()
            node = TreeNode(color_name, tag=tag)
            
            # Typen darunter
            type_nodes = self._build_type_nodes(tag)
            for type_node in type_nodes:
                node.add_child(type_node)
            
            nodes.append(node)
        
        # Mehrfarbige (Gilden)
        multicolor_node = TreeNode("Multicolor", tag='multicolor')
        for colors, guild_name in MULTICOLOR_GUILDS.items():
            tag = f'multicolor_{colors.lower()}'
            guild_node = TreeNode(guild_name, tag=tag)
            
            # Typen darunter
            type_nodes = self._build_type_nodes(tag)
            for type_node in type_nodes:
                guild_node.add_child(type_node)
            
            multicolor_node.add_child(guild_node)
        
        nodes.append(multicolor_node)
        
        return nodes
    
    def _build_type_nodes(self, parent_tag):
        """Erstelle Typ-Knoten für eine Farbe"""
        nodes = []
        
        for card_type in CARD_TYPES:
            tag = card_type.lower()
            combined_tag = f"{parent_tag}+{tag}"
            node = TreeNode(card_type, tag=combined_tag)
            
            # Für Creatures: Fähigkeiten + Legendary
            if card_type == "Creature":
                # Legendary-Unterordner
                legendary_node = TreeNode("Legendary", tag=f"{combined_tag}+legendary")
                alpha_nodes = self._build_alphabet_nodes(f"{combined_tag}+legendary")
                for alpha_node in alpha_nodes:
                    legendary_node.add_child(alpha_node)
                node.add_child(legendary_node)
                
                # Fähigkeiten
                for ability in CREATURE_ABILITIES:
                    ability_tag = ability.lower().replace(' ', '_')
                    ability_node = TreeNode(ability, tag=f"{combined_tag}+{ability_tag}")
                    
                    alpha_nodes = self._build_alphabet_nodes(f"{combined_tag}+{ability_tag}")
                    for alpha_node in alpha_nodes:
                        ability_node.add_child(alpha_node)
                    
                    node.add_child(ability_node)
                
                # Sonstige Creatures (keine besonderen Fähigkeiten)
                other_node = TreeNode("Sonstige", tag=f"{combined_tag}+other")
                alpha_nodes = self._build_alphabet_nodes(f"{combined_tag}+other")
                for alpha_node in alpha_nodes:
                    other_node.add_child(alpha_node)
                node.add_child(other_node)
            
            else:
                # Für andere Typen: Legendary + Normal
                legendary_node = TreeNode("Legendary", tag=f"{combined_tag}+legendary")
                alpha_nodes = self._build_alphabet_nodes(f"{combined_tag}+legendary")
                for alpha_node in alpha_nodes:
                    legendary_node.add_child(alpha_node)
                node.add_child(legendary_node)
                
                normal_node = TreeNode("Normal", tag=f"{combined_tag}+normal")
                alpha_nodes = self._build_alphabet_nodes(f"{combined_tag}+normal")
                for alpha_node in alpha_nodes:
                    normal_node.add_child(alpha_node)
                node.add_child(normal_node)
            
            nodes.append(node)
        
        return nodes
    
    def _build_alphabet_nodes(self, parent_tag):
        """Erstelle Alphabet-Gruppen (A-D, E-H, etc.)"""
        groups = [
            ("A-D", "alpha_a_d"),
            ("E-H", "alpha_e_h"),
            ("I-L", "alpha_i_l"),
            ("M-P", "alpha_m_p"),
            ("Q-T", "alpha_q_t"),
            ("U-Z", "alpha_u_z")
        ]
        
        nodes = []
        for group_name, group_tag in groups:
            combined_tag = f"{parent_tag}+{group_tag}"
            node = TreeNode(group_name, tag=combined_tag, is_leaf=True)
            nodes.append(node)
        
        return nodes
    
    def get_cards_for_node(self, node):
        """
        Hole Karten für einen Baum-Knoten
        
        Args:
            node: TreeNode mit tag
        
        Returns:
            list of card dicts
        """
        if not node.tag:
            return []
        
        # Parse Tag (z.B. "white+creature+flying+alpha_a_d")
        tags = node.tag.split('+')
        
        # Hole Karten die ALLE Tags haben
        cards = self.card_manager.get_cards_by_tags(tags, match_all=True)
        
        return cards
    
    def count_cards_recursive(self, node):
        """
        Zähle Karten rekursiv für alle Unterknoten
        Aktualisiert node.card_count
        """
        if node.is_leaf:
            # Blatt-Knoten: Zähle direkt
            cards = self.get_cards_for_node(node)
            node.card_count = len(cards)
            return node.card_count
        else:
            # Nicht-Blatt: Summiere Kinder
            total = 0
            for child in node.children:
                total += self.count_cards_recursive(child)
            node.card_count = total
            return total
