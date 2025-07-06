#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Runner für WhisperSprecherMatcher
Führt das System mit lokalen Pfaden aus (Fallback für Google Drive Probleme)
"""

import os
import sys
from pathlib import Path

# Setze Working Directory
os.chdir(Path(__file__).parent)

# Importiere das Hauptsystem
from auto_transcriber import WhisperSpeakerMatcher
from build_memory_from_transcripts import MemoryBuilder

def run_transcription():
    """Führe Transkription mit lokalem Pfad aus"""
    print("🎤 WhisperSprecherMatcher (Lokaler Modus) gestartet...")
    
    try:
        # Verwende explizit lokalen Pfad
        matcher = WhisperSpeakerMatcher(base_path=".")
        matcher.process_audio_files()
        print("✅ Transkription erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler bei Transkription: {e}")
        return False
    
    return True

def run_memory_builder():
    """Führe Memory Builder mit lokalem Pfad aus"""
    print("🧠 Memory Builder (Lokaler Modus) gestartet...")
    
    try:
        # Verwende explizit lokalen Pfad
        builder = MemoryBuilder(base_path=".")
        builder.process_transcription_files()
        print("✅ Memory-Aufbau erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler beim Memory-Aufbau: {e}")
        return False
    
    return True

def main():
    """Hauptmenü"""
    print("🎤 WhisperSprecherMatcher - Lokaler Modus")
    print("=" * 50)
    print("Dieser Modus arbeitet mit lokalen Dateien und umgeht Google Drive-Probleme.")
    print("")
    print("Optionen:")
    print("1) Audio-Dateien transkribieren")
    print("2) Memory aus Transkriptionen aufbauen")
    print("3) Beide Schritte nacheinander")
    print("4) Status anzeigen")
    print("5) Beenden")
    print("")
    
    while True:
        try:
            choice = input("Wähle eine Option (1-5): ").strip()
            
            if choice == "1":
                print("\n" + "="*30)
                run_transcription()
                print("="*30 + "\n")
                
            elif choice == "2":
                print("\n" + "="*30)
                run_memory_builder()
                print("="*30 + "\n")
                
            elif choice == "3":
                print("\n" + "="*30)
                print("🔄 Führe vollständigen Workflow aus...")
                if run_transcription():
                    print("\n📊 Baue Memory auf...")
                    run_memory_builder()
                print("="*30 + "\n")
                
            elif choice == "4":
                show_status()
                
            elif choice == "5":
                print("👋 Auf Wiedersehen!")
                break
                
            else:
                print("❌ Ungültige Option. Bitte wähle 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Programm beendet.")
            break
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")

def show_status():
    """Zeige aktuellen Status"""
    print("\n📊 Status Report")
    print("="*30)
    
    base_path = Path(".")
    eingang_path = base_path / "Eingang"
    memory_path = base_path / "Memory"
    
    # Zähle Dateien
    if eingang_path.exists():
        audio_files = list(eingang_path.rglob("*.opus")) + list(eingang_path.rglob("*.wav")) + list(eingang_path.rglob("*.mp3"))
        txt_files = list(eingang_path.rglob("*.txt"))
        print(f"🎵 Audio-Dateien: {len(audio_files)}")
        print(f"📝 Transkriptionen: {len(txt_files)}")
    else:
        print("📁 Eingang-Ordner nicht gefunden")
        
    if memory_path.exists():
        memory_files = list(memory_path.glob("*.yaml"))
        print(f"🧠 Memory-Profile: {len(memory_files)}")
        if memory_files:
            print("👥 Bekannte Sprecher:")
            for yaml_file in memory_files:
                print(f"   - {yaml_file.stem}")
    else:
        print("📁 Memory-Ordner nicht gefunden")
    
    print("="*30 + "\n")

if __name__ == "__main__":
    main() 