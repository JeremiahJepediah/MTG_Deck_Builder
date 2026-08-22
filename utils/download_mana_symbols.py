"""
Download Mana Symbols from Scryfall
"""

import requests
from pathlib import Path

SYMBOLS_DIR = Path("data/mana_symbols")
SYMBOLS_DIR.mkdir(parents=True, exist_ok=True)

# Alle benötigten Symbole
SYMBOLS = [
    'W', 'U', 'B', 'R', 'G', 'C',  # Basis-Farben
    'WU', 'UB', 'BR', 'RG', 'GW',  # Hybrid
    'WB', 'UR', 'BG', 'RW', 'GU',  # Hybrid
    'WP', 'UP', 'BP', 'RP', 'GP',  # Phyrexian
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',  # Zahlen
    '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    'X', 'Y', 'Z',  # Variables
    'T', 'Q', 'E', 'S'  # Tap, Untap, Energy, Snow
]

def download_symbols():
    """Download alle Mana-Symbole von Scryfall"""
    print("Downloading mana symbols from Scryfall...")
    headers = {'User-Agent': 'MTGDeckBuilder/1.1 (personal project)'}
    response = requests.get(url, timeout=10, headers=headers)

    success = 0
    failed = 0
    
    for symbol in SYMBOLS:
        url = f"https://svgs.scryfall.io/card-symbols/{symbol}.svg"
        output_path = SYMBOLS_DIR / f"{symbol}.svg"
        
        if output_path.exists():
            print(f"  ✓ {symbol}.svg (already exists)")
            success += 1
            continue
        
        try:
            response = requests.get(url, timeout=10, headers=headers)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ {symbol}.svg")
                success += 1
            else:
                print(f"  ✗ {symbol}.svg (HTTP {response.status_code})")
                failed += 1
        except Exception as e:
            print(f"  ✗ {symbol}.svg ({e})")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Success: {success}")
    print(f"❌ Failed:  {failed}")
    print(f"📁 Saved to: {SYMBOLS_DIR.absolute()}")

if __name__ == '__main__':
    download_symbols()