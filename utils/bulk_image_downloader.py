"""
MTG Deck Builder v1.1 - Bulk Image Downloader
Lädt alle Kartenbilder von Scryfall (über Nacht)
"""

import requests
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from core.database import get_database
from config import IMAGE_DIR


class BulkImageDownloader:
    def __init__(self, image_dir=None):
        self.image_dir = Path(image_dir) if image_dir else IMAGE_DIR
        self.image_dir.mkdir(exist_ok=True)
        self.db = get_database()
        
        # Scryfall Rate Limit: 10 requests/second = 100ms zwischen Requests
        self.delay_between_requests = 0.11  # 110ms (sicher)
        
        # Progress-Datei (zum Fortsetzen nach Abbruch)
        self.progress_file = self.image_dir / "download_progress.txt"
    
    def download_all(self, resume=True):
        """
        Lädt alle Bilder
        
        Args:
            resume: Bei True, setzt an letzter Stelle fort
        
        Returns:
            dict mit Statistiken
        """
        # Hole alle image_ids aus DB
        cursor = self.db.execute(
            "SELECT DISTINCT image_id FROM cards WHERE image_id IS NOT NULL AND image_id != ''"
        )
        all_image_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"Gefunden: {len(all_image_ids)} eindeutige Bilder")
        
        # Prüfe welche bereits existieren
        existing = set()
        for image_id in all_image_ids:
            if (self.image_dir / f"{image_id}_front.jpg").exists():
                existing.add(image_id)
        
        print(f"Bereits vorhanden: {len(existing)} Bilder")
        
        # Zu downloaden
        to_download = [img_id for img_id in all_image_ids if img_id not in existing]
        
        print(f"Zu downloaden: {len(to_download)} Bilder")
        print(f"Geschätzte Dauer: ~{len(to_download) * 0.11 / 60:.0f} Minuten")
        print()
        
        if not to_download:
            return {
                'success': True,
                'downloaded': 0,
                'skipped': len(existing),
                'errors': 0
            }
        
        # Resume-Punkt laden
        start_index = 0
        if resume and self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    start_index = int(f.read().strip())
                print(f"Fortsetzen ab Bild {start_index}/{len(to_download)}")
            except:
                pass
        
        downloaded = 0
        errors = 0
        
        for i, image_id in enumerate(to_download[start_index:], start=start_index):
            try:
                # Progress
                if i % 10 == 0:
                    percent = (i / len(to_download)) * 100
                    print(f"\r[{percent:5.1f}%] {i}/{len(to_download)} - Downloaded: {downloaded}, Errors: {errors}", 
                          end='', flush=True)
                
                # Download Vorderseite
                success = self.download_image(image_id, 'front')
                
                if success:
                    downloaded += 1
                else:
                    errors += 1
                
                # Speichere Progress
                if i % 100 == 0:
                    with open(self.progress_file, 'w') as f:
                        f.write(str(i))
                
                # Rate Limiting
                time.sleep(self.delay_between_requests)
                
            except KeyboardInterrupt:
                print(f"\n\nUnterbrochen! Fortschritt gespeichert.")
                print(f"Zum Fortsetzen: python bulk_image_downloader.py")
                return {
                    'success': False,
                    'downloaded': downloaded,
                    'skipped': len(existing),
                    'errors': errors,
                    'interrupted': True
                }
            except Exception as e:
                print(f"\nFehler bei {image_id}: {e}")
                errors += 1
        
        # Cleanup
        if self.progress_file.exists():
            self.progress_file.unlink()
        
        print(f"\n\n{'='*60}")
        print(f"Download abgeschlossen!")
        print(f"Downloaded: {downloaded}")
        print(f"Bereits vorhanden: {len(existing)}")
        print(f"Fehler: {errors}")
        
        return {
            'success': True,
            'downloaded': downloaded,
            'skipped': len(existing),
            'errors': errors
        }
    
    def download_image(self, image_id, face='front'):
        """
        Lädt ein einzelnes Bild von Scryfall
        
        Returns:
            bool: True bei Erfolg
        """
        url = f"https://api.scryfall.com/cards/{image_id}?format=image&version=normal&face={face}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                file_path = self.image_dir / f"{image_id}_{face}.jpg"
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def cleanup_progress(self):
        """Lösche Progress-Datei"""
        if self.progress_file.exists():
            self.progress_file.unlink()


def main():
    """Standalone Ausführung"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk Image Download von Scryfall')
    parser.add_argument('--no-resume', action='store_true',
                       help='Von vorne starten (nicht fortsetzen)')
    parser.add_argument('--image-dir', type=str,
                       help='Ziel-Verzeichnis für Bilder')
    
    args = parser.parse_args()
    
    downloader = BulkImageDownloader(args.image_dir)
    
    print("="*60)
    print("MTG Bulk Image Downloader")
    print("="*60)
    print()
    print("HINWEIS:")
    print("- Scryfall Rate Limit: ~10 Anfragen/Sekunde")
    print("- Bei 70.000 Bildern: ~2 Stunden Laufzeit")
    print("- Bei Unterbrechung (Ctrl+C): Fortsetzbar!")
    print()
    print("Drücke Enter zum Starten oder Ctrl+C zum Abbrechen...")
    input()
    
    result = downloader.download_all(resume=not args.no_resume)
    
    if result.get('interrupted'):
        print("\nZum Fortsetzen:")
        print("  python bulk_image_downloader.py")
    elif result['success']:
        print(f"\n✓ Alle Bilder heruntergeladen!")


if __name__ == '__main__':
    main()
