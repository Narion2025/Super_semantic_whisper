#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhisperSprecherMatcher V2 - Verbesserte Version
- Erkennt Chatpartner aus Ordnerstruktur
- LLM-freundliches Ausgabeformat
- Priorisiert Zoe-Ordner
- Nur OPUS-Dateien
"""

import os
import sys
import subprocess
import json
import yaml
import re
import logging
from pathlib import Path
from datetime import datetime
import shutil
from typing import List, Dict, Tuple, Optional

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcription_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhisperSpeakerMatcherV2:
    def __init__(self, base_path=None, use_faster_whisper=True):
        if base_path is None:
            self.base_path = Path("/Users/benjaminpoersch/Library/CloudStorage/GoogleDrive-benjamin.poersch@diyrigent.de/Meine Ablage/MyMind/WhisperSprecherMatcher")
        else:
            self.base_path = Path(base_path)
            
        self.eingang_path = self.base_path / "Eingang"
        self.memory_path = self.base_path / "Memory"
        self.output_path = self.base_path / "Transkripte_LLM"
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Fallback für lokale Entwicklung
        if not self.base_path.exists():
            logger.warning(f"Google Drive Pfad nicht verfügbar: {self.base_path}")
            self.base_path = Path("./whisper_speaker_matcher")
            self.eingang_path = self.base_path / "Eingang"
            self.memory_path = self.base_path / "Memory"
            self.output_path = self.base_path / "Transkripte_LLM"
            self._create_local_structure()
        
        self.use_faster_whisper = use_faster_whisper
        self.speakers = self._load_speaker_profiles()
        
    def _create_local_structure(self):
        """Erstelle lokale Verzeichnisstruktur wenn Google Drive nicht verfügbar"""
        for path in [self.eingang_path, self.memory_path, self.output_path]:
            path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Lokale Struktur erstellt: {self.base_path}")
    
    def _load_speaker_profiles(self):
        """Lade bekannte Sprecher-Profile aus Memory-Ordner"""
        speakers = {}
        
        if not self.memory_path.exists():
            logger.warning(f"Memory-Pfad existiert nicht: {self.memory_path}")
            return self._create_default_speakers()
            
        for yaml_file in self.memory_path.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    profile = yaml.safe_load(f)
                    speaker_name = yaml_file.stem
                    speakers[speaker_name] = profile
                    logger.info(f"Sprecher-Profil geladen: {speaker_name}")
            except Exception as e:
                logger.error(f"Fehler beim Laden von {yaml_file}: {e}")
                
        return speakers if speakers else self._create_default_speakers()
    
    def _create_default_speakers(self):
        """Erstelle Standard-Sprecher wenn keine Profile gefunden werden"""
        return {
            'ben': {
                'name': 'Benjamin Poersch',
                'keywords': ['also', 'genau', 'interessant', 'technisch', 'system']
            },
            'zoe': {
                'name': 'Zoe',
                'keywords': ['wow', 'krass', 'mega', 'cool', 'schön']
            },
            'ich': {
                'name': 'Ich',
                'keywords': []
            }
        }
    
    def get_chatpartner_from_path(self, file_path: Path) -> str:
        """Extrahiere Chatpartner aus Ordnerstruktur"""
        # Prüfe ob die Datei in einem Unterordner liegt
        relative_path = file_path.relative_to(self.eingang_path)
        parts = relative_path.parts
        
        if len(parts) > 1:
            # Der erste Teil ist der Chatpartner-Ordner
            chatpartner = parts[0]
            return chatpartner
        
        # Fallback: Versuche aus Dateiname zu extrahieren
        filename = file_path.name.lower()
        for known_person in ['zoe', 'schroeti', 'freddy', 'marike', 'vincent', 'elke']:
            if known_person in filename:
                return known_person.title()
        
        return "Unbekannt"
    
    def transcribe_audio_faster(self, audio_path: Path) -> Optional[str]:
        """Transkribiere Audio mit faster-whisper (schneller als OpenAI Whisper)"""
        try:
            # Prüfe ob faster-whisper installiert ist
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                logger.warning("faster-whisper nicht installiert. Installiere mit: pip install faster-whisper")
                return self.transcribe_audio_standard(audio_path)
            
            logger.info(f"Verwende faster-whisper für {audio_path.name}")
            
            # Lade Modell (small ist ein guter Kompromiss zwischen Geschwindigkeit und Qualität)
            model = WhisperModel("small", device="cpu", compute_type="int8")
            
            # Transkribiere
            segments, info = model.transcribe(str(audio_path), language="de")
            
            # Sammle Text
            transcription = " ".join([segment.text.strip() for segment in segments])
            
            return transcription
            
        except Exception as e:
            logger.error(f"Faster-whisper Fehler für {audio_path}: {e}")
            # Fallback zu Standard Whisper
            return self.transcribe_audio_standard(audio_path)
    
    def transcribe_audio_standard(self, audio_path: Path) -> Optional[str]:
        """Standard Whisper Transkription als Fallback"""
        try:
            # Whisper Command
            whisper_cmd = self._find_whisper_command()
            
            if not whisper_cmd:
                raise Exception("Whisper nicht gefunden. Bitte installieren: pip install openai-whisper")
            
            # Führe Transkription aus
            cmd = [whisper_cmd, str(audio_path), "--language", "de", "--model", "base", "--output_format", "txt"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Whisper Fehler: {result.stderr}")
                return None
                
            # Lese Transkription
            txt_path = audio_path.with_suffix('.txt')
            if txt_path.exists():
                with open(txt_path, 'r', encoding='utf-8') as f:
                    transcription = f.read().strip()
                # Lösche temporäre Datei
                txt_path.unlink()
                return transcription
            
            return None
                
        except Exception as e:
            logger.error(f"Transkriptions-Fehler für {audio_path}: {e}")
            return None
    
    def _find_whisper_command(self):
        """Finde verfügbare Whisper-Installation"""
        possible_commands = ['whisper', 'python -m whisper', 'python3 -m whisper']
        
        for cmd in possible_commands:
            try:
                result = subprocess.run(cmd.split() + ['--help'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd.split()[0] if len(cmd.split()) == 1 else cmd
            except:
                continue
        return None
    
    def identify_speaker_in_conversation(self, transcription: str, chatpartner: str) -> List[Tuple[str, str]]:
        """
        Identifiziere Sprecher in der Konversation
        Gibt Liste von (Sprecher, Text) Tupeln zurück
        """
        # In einer WhatsApp Audio ist normalerweise nur eine Person
        # Der Sprecher ist entweder "Ich" (wenn von mir) oder der Chatpartner
        
        # Einfache Heuristik: Prüfe Keywords
        transcription_lower = transcription.lower()
        
        # Prüfe ob es meine Nachricht ist (ich spreche)
        my_indicators = ['ich schicke', 'ich sende', 'hier ist', 'ich wollte']
        is_my_message = any(indicator in transcription_lower for indicator in my_indicators)
        
        if is_my_message:
            speaker = "Ich"
        else:
            # Annahme: Die andere Person spricht
            speaker = chatpartner
        
        # Für Zukunft: Könnte erweitert werden um Sprecher innerhalb einer Nachricht zu erkennen
        return [(speaker, transcription)]
    
    def format_for_llm(self, chatpartner: str, conversation_parts: List[Tuple[str, str]], 
                      audio_file: Path, timestamp: datetime) -> str:
        """Formatiere Transkription für optimale LLM-Verarbeitung"""
        
        output = f"""# WhatsApp Audio Transkription

**Chat mit:** {chatpartner}
**Datum:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Datei:** {audio_file.name}

## Transkription:

"""
        
        for speaker, text in conversation_parts:
            if speaker == "Ich":
                output += f"**[Ich]:** {text}\n\n"
            else:
                output += f"**[{speaker}]:** {text}\n\n"
        
        output += """---
*Transkribiert mit WhisperSprecherMatcher V2*
"""
        
        return output
    
    def get_sorted_audio_files(self) -> List[Path]:
        """
        Hole alle OPUS-Dateien, priorisiere Zoe-Ordner
        """
        if not self.eingang_path.exists():
            logger.error(f"Eingang-Ordner nicht gefunden: {self.eingang_path}")
            return []
        
        all_opus_files = list(self.eingang_path.rglob("*.opus"))
        
        # Sortiere: Zoe-Dateien zuerst
        zoe_files = []
        other_files = []
        
        for file in all_opus_files:
            if 'zoe' in str(file).lower():
                zoe_files.append(file)
            else:
                other_files.append(file)
        
        # Sortiere nach Datum (neueste zuerst)
        zoe_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        other_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return zoe_files + other_files
    
    def process_audio_files(self):
        """Verarbeite alle OPUS Audio-Dateien mit Priorisierung"""
        
        audio_files = self.get_sorted_audio_files()
        logger.info(f"Gefunden: {len(audio_files)} OPUS-Dateien")
        
        if audio_files:
            zoe_count = sum(1 for f in audio_files if 'zoe' in str(f).lower())
            logger.info(f"Davon {zoe_count} Dateien im Zoe-Ordner (werden zuerst verarbeitet)")
        
        processed_count = 0
        for audio_file in audio_files:
            try:
                # Prüfe ob bereits verarbeitet
                chatpartner = self.get_chatpartner_from_path(audio_file)
                output_filename = f"{chatpartner}_{audio_file.stem}_transkript.md"
                output_path = self.output_path / output_filename
                
                if output_path.exists():
                    logger.info(f"Bereits verarbeitet: {audio_file.name}")
                    continue
                
                logger.info(f"Verarbeite: {audio_file.name} (Chat mit {chatpartner})")
                
                # Transkribiere
                if self.use_faster_whisper:
                    transcription = self.transcribe_audio_faster(audio_file)
                else:
                    transcription = self.transcribe_audio_standard(audio_file)
                
                if not transcription:
                    logger.warning(f"Keine Transkription erhalten für {audio_file.name}")
                    continue
                
                # Identifiziere Sprecher
                conversation_parts = self.identify_speaker_in_conversation(transcription, chatpartner)
                
                # Formatiere für LLM
                timestamp = datetime.fromtimestamp(audio_file.stat().st_mtime)
                llm_formatted = self.format_for_llm(chatpartner, conversation_parts, audio_file, timestamp)
                
                # Speichere Ausgabe
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(llm_formatted)
                
                # Update Memory für Chatpartner
                self.update_speaker_memory(chatpartner, transcription, audio_file)
                
                processed_count += 1
                logger.info(f"✅ Verarbeitet: {audio_file.name} -> {output_filename}")
                
                # Fortschrittsanzeige
                progress = (audio_files.index(audio_file) + 1) / len(audio_files) * 100
                logger.info(f"Fortschritt: {progress:.1f}% ({audio_files.index(audio_file) + 1}/{len(audio_files)})")
                
            except Exception as e:
                logger.error(f"Fehler bei {audio_file.name}: {e}")
                continue
        
        logger.info(f"Verarbeitung abgeschlossen. {processed_count} neue Dateien verarbeitet.")
        self.create_summary_report(processed_count, len(audio_files))
    
    def update_speaker_memory(self, speaker: str, transcription: str, audio_file: Path):
        """Aktualisiere Sprecher-Memory mit neuer Information"""
        if speaker == "Unbekannt":
            return
            
        memory_file = self.memory_path / f"{speaker.lower()}.yaml"
        
        try:
            # Lade existierendes Profil oder erstelle neues
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    profile = yaml.safe_load(f) or {}
            else:
                profile = {'name': speaker, 'interactions': []}
            
            # Füge neue Interaktion hinzu
            interaction = {
                'timestamp': datetime.now().isoformat(),
                'transcription_preview': transcription[:200] + '...' if len(transcription) > 200 else transcription,
                'source_file': str(audio_file.name),
                'length_chars': len(transcription)
            }
            
            if 'interactions' not in profile:
                profile['interactions'] = []
            
            profile['interactions'].append(interaction)
            
            # Behalte nur die letzten 50 Interaktionen
            profile['interactions'] = profile['interactions'][-50:]
            
            # Aktualisiere Statistiken
            profile['last_updated'] = datetime.now().isoformat()
            profile['total_interactions'] = len(profile['interactions'])
            
            # Speichere aktualisiertes Profil
            with open(memory_file, 'w', encoding='utf-8') as f:
                yaml.dump(profile, f, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"Memory für {speaker} aktualisiert")
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Memory für {speaker}: {e}")
    
    def create_summary_report(self, processed: int, total: int):
        """Erstelle Zusammenfassungsbericht"""
        report_path = self.output_path / "verarbeitungs_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"""# WhisperSprecherMatcher V2 - Verarbeitungsbericht

**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistiken:
- **Gefundene OPUS-Dateien:** {total}
- **Neu verarbeitet:** {processed}
- **Bereits verarbeitet:** {total - processed}

## Verarbeitete Chatpartner:
""")
            
            # Zähle Dateien pro Chatpartner
            chatpartner_counts = {}
            for md_file in self.output_path.glob("*.md"):
                if md_file.name != "verarbeitungs_report.md":
                    chatpartner = md_file.name.split('_')[0]
                    chatpartner_counts[chatpartner] = chatpartner_counts.get(chatpartner, 0) + 1
            
            for chatpartner, count in sorted(chatpartner_counts.items()):
                f.write(f"- **{chatpartner}:** {count} Transkriptionen\n")
            
            f.write(f"\n*Bericht generiert von WhisperSprecherMatcher V2*")
        
        logger.info(f"📊 Zusammenfassungsbericht erstellt: {report_path}")

def main():
    """Hauptfunktion"""
    print("🎤 WhisperSprecherMatcher V2 gestartet...")
    print("Priorisiere Zoe-Ordner und verwende LLM-optimiertes Format")
    
    # Argumente parsen
    import argparse
    parser = argparse.ArgumentParser(description="WhisperSprecherMatcher V2")
    parser.add_argument("--standard-whisper", action="store_true", 
                       help="Verwende Standard Whisper statt faster-whisper")
    parser.add_argument("--local", action="store_true",
                       help="Verwende lokalen Pfad statt Google Drive")
    
    args = parser.parse_args()
    
    try:
        if args.local:
            matcher = WhisperSpeakerMatcherV2(base_path=".", 
                                            use_faster_whisper=not args.standard_whisper)
        else:
            matcher = WhisperSpeakerMatcherV2(use_faster_whisper=not args.standard_whisper)
        
        matcher.process_audio_files()
        print("✅ Verarbeitung erfolgreich abgeschlossen!")
        print(f"📁 Transkripte gespeichert in: {matcher.output_path}")
        
    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}")
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
