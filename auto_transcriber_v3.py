#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhisperSprecherMatcher V3 - Mit Datum/Zeit-Extraktion
- Extrahiert Datum/Zeit aus WhatsApp-Dateinamen
- Zeigt Original-Aufnahmezeit im Transkript und Dateinamen
- Erkennt Chatpartner aus Ordnerstruktur
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
        logging.FileHandler('transcription_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhisperSpeakerMatcherV3:
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
    
    def extract_whatsapp_datetime(self, filename: str) -> Tuple[Optional[datetime], str]:
        """
        Extrahiere Datum und Zeit aus Audio-Dateinamen
        Beispiele:
        - WhatsApp Audio 2025-06-29 at 13.20.58.opus
        - 00000249-AUDIO-2025-02-28-07-05-24.opus
        """
        # Pattern für WhatsApp Dateien (Standard-Format)
        whatsapp_pattern = r'WhatsApp (?:Audio|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{1,2})\.(\d{2})\.(\d{2})'
        
        match = re.search(whatsapp_pattern, filename)
        if match:
            year, month, day, hour, minute, second = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                # Erstelle benutzerfreundlichen String
                formatted_date = dt.strftime('%Y-%m-%d_%H-%M-%S')
                return dt, formatted_date
            except ValueError as e:
                logger.warning(f"Ungültiges Datum in {filename}: {e}")
        
        # Pattern für nummerierte AUDIO-Dateien (Format: XXXXXXXX-AUDIO-YYYY-MM-DD-HH-MM-SS.opus)
        audio_pattern = r'\d+-AUDIO-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})'
        
        match = re.search(audio_pattern, filename)
        if match:
            year, month, day, hour, minute, second = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                # Erstelle benutzerfreundlichen String
                formatted_date = dt.strftime('%Y-%m-%d_%H-%M-%S')
                logger.info(f"Erkanntes Aufnahmedatum: {dt.strftime('%d.%m.%Y um %H:%M:%S')} aus Datei {filename}")
                return dt, formatted_date
            except ValueError as e:
                logger.warning(f"Ungültiges Datum in {filename}: {e}")
        
        # Fallback: Verwende Datei-Erstellungszeit
        logger.warning(f"Kein Datum im Dateinamen erkannt: {filename}")
        return None, "unbekannt"
    
    def get_chatpartner_from_path(self, file_path: Path) -> str:
        """Extrahiere Chatpartner aus Ordnerstruktur"""
        relative_path = file_path.relative_to(self.eingang_path)
        parts = relative_path.parts
        
        if len(parts) > 1:
            chatpartner = parts[0]
            return chatpartner.replace('_', ' ')
        
        filename = file_path.name.lower()
        for known_person in ['zoe', 'schroeti', 'freddy', 'marike', 'vincent', 'elke']:
            if known_person in filename:
                return known_person.title()
        
        return "Unbekannt"
    
    def transcribe_audio_standard(self, audio_path: Path) -> Optional[str]:
        """Standard Whisper Transkription"""
        try:
            whisper_cmd = self._find_whisper_command()
            
            if not whisper_cmd:
                raise Exception("Whisper nicht gefunden. Bitte installieren: pip install openai-whisper")
            
            cmd = [whisper_cmd, str(audio_path), "--language", "de", "--model", "base", "--output_format", "txt"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Whisper Fehler: {result.stderr}")
                return None
                
            # Whisper erstellt TXT im aktuellen Verzeichnis
            txt_filename = audio_path.name.replace('.opus', '.txt')
            txt_path = Path(txt_filename)
            if txt_path.exists():
                with open(txt_path, 'r', encoding='utf-8') as f:
                    transcription = f.read().strip()
                txt_path.unlink()  # Lösche temporäre Datei
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
        """Identifiziere Sprecher in der Konversation"""
        transcription_lower = transcription.lower()
        
        my_indicators = ['ich schicke', 'ich sende', 'hier ist', 'ich wollte', 'von mir', 'meine']
        is_my_message = any(indicator in transcription_lower for indicator in my_indicators)
        
        if is_my_message:
            speaker = "Ich"
        else:
            speaker = chatpartner
        
        return [(speaker, transcription)]
    
    def format_for_llm(self, chatpartner: str, conversation_parts: List[Tuple[str, str]], 
                      audio_file: Path, recording_datetime: Optional[datetime], 
                      processing_time: datetime) -> str:
        """Formatiere Transkription für optimale LLM-Verarbeitung mit Zeitstempeln"""
        
        if recording_datetime:
            recording_str = recording_datetime.strftime('%d.%m.%Y um %H:%M:%S')
            recording_date = recording_datetime.strftime('%Y-%m-%d')
            recording_time = recording_datetime.strftime('%H:%M:%S')
        else:
            recording_str = "Unbekannt"
            recording_date = "Unbekannt"
            recording_time = "Unbekannt"
        
        output = f"""# WhatsApp Audio Transkription

**Chat mit:** {chatpartner}
**Aufnahme am:** {recording_str}
**Verarbeitet am:** {processing_time.strftime('%d.%m.%Y um %H:%M:%S')}
**Original-Datei:** {audio_file.name}

## Zeitstempel:
- **Aufnahme-Datum:** {recording_date}
- **Aufnahme-Uhrzeit:** {recording_time}
- **Verarbeitungszeit:** {processing_time.strftime('%Y-%m-%d %H:%M:%S')}

## Transkription:

"""
        
        for speaker, text in conversation_parts:
            if speaker == "Ich":
                output += f"**[Ich - {recording_time}]:** {text}\n\n"
            else:
                output += f"**[{speaker} - {recording_time}]:** {text}\n\n"
        
        output += f"""## Kontext für LLM:
Diese Nachricht wurde am {recording_str} in einem WhatsApp-Chat zwischen mir und {chatpartner} aufgenommen.

---
*Transkribiert mit WhisperSprecherMatcher V3 am {processing_time.strftime('%d.%m.%Y um %H:%M:%S')}*
"""
        
        return output
    
    def get_sorted_audio_files(self) -> List[Path]:
        """Hole alle OPUS-Dateien, priorisiere Zoe-Ordner"""
        if not self.eingang_path.exists():
            logger.error(f"Eingang-Ordner nicht gefunden: {self.eingang_path}")
            return []
        
        all_opus_files = list(self.eingang_path.rglob("*.opus"))
        
        zoe_files = []
        other_files = []
        
        for file in all_opus_files:
            if 'zoe' in str(file).lower():
                zoe_files.append(file)
            else:
                other_files.append(file)
        
        def sort_by_whatsapp_date(file_path):
            dt, _ = self.extract_whatsapp_datetime(file_path.name)
            return dt if dt else datetime.fromtimestamp(file_path.stat().st_mtime)
        
        zoe_files.sort(key=sort_by_whatsapp_date, reverse=True)
        other_files.sort(key=sort_by_whatsapp_date, reverse=True)
        
        return zoe_files + other_files
    
    def process_audio_files(self):
        """Verarbeite alle OPUS Audio-Dateien mit Datum/Zeit-Extraktion"""
        
        audio_files = self.get_sorted_audio_files()
        logger.info(f"Gefunden: {len(audio_files)} OPUS-Dateien")
        
        if audio_files:
            zoe_count = sum(1 for f in audio_files if 'zoe' in str(f).lower())
            logger.info(f"Davon {zoe_count} Dateien im Zoe-Ordner (werden zuerst verarbeitet)")
        
        processed_count = 0
        for audio_file in audio_files:
            try:
                recording_datetime, formatted_date = self.extract_whatsapp_datetime(audio_file.name)
                chatpartner = self.get_chatpartner_from_path(audio_file)
                
                if recording_datetime:
                    output_filename = f"{formatted_date}_{chatpartner.replace(' ', '_')}_{audio_file.stem}_transkript.md"
                else:
                    output_filename = f"{chatpartner.replace(' ', '_')}_{audio_file.stem}_transkript.md"
                
                output_path = self.output_path / output_filename
                
                if output_path.exists():
                    logger.info(f"Bereits verarbeitet: {audio_file.name}")
                    continue
                
                if recording_datetime:
                    logger.info(f"Verarbeite: {audio_file.name} (Chat mit {chatpartner}, aufgenommen am {recording_datetime.strftime('%d.%m.%Y um %H:%M')})")
                else:
                    logger.info(f"Verarbeite: {audio_file.name} (Chat mit {chatpartner})")
                
                transcription = self.transcribe_audio_standard(audio_file)
                
                if not transcription:
                    logger.warning(f"Keine Transkription erhalten für {audio_file.name}")
                    continue
                
                conversation_parts = self.identify_speaker_in_conversation(transcription, chatpartner)
                processing_time = datetime.now()
                llm_formatted = self.format_for_llm(chatpartner, conversation_parts, 
                                                   audio_file, recording_datetime, processing_time)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(llm_formatted)
                
                processed_count += 1
                logger.info(f"✅ Verarbeitet: {audio_file.name} -> {output_filename}")
                
                progress = (audio_files.index(audio_file) + 1) / len(audio_files) * 100
                logger.info(f"Fortschritt: {progress:.1f}% ({audio_files.index(audio_file) + 1}/{len(audio_files)})")
                
            except Exception as e:
                logger.error(f"Fehler bei {audio_file.name}: {e}")
                continue
        
        logger.info(f"Verarbeitung abgeschlossen. {processed_count} neue Dateien verarbeitet.")

def main():
    """Hauptfunktion"""
    print("🎤 WhisperSprecherMatcher V3 gestartet...")
    print("Mit Datum/Zeit-Extraktion aus WhatsApp-Dateinamen")
    
    import argparse
    parser = argparse.ArgumentParser(description="WhisperSprecherMatcher V3")
    parser.add_argument("--local", action="store_true", help="Verwende lokalen Pfad")
    
    args = parser.parse_args()
    
    try:
        if args.local:
            matcher = WhisperSpeakerMatcherV3(base_path=".")
        else:
            matcher = WhisperSpeakerMatcherV3()
        
        matcher.process_audio_files()
        print("✅ Verarbeitung erfolgreich abgeschlossen!")
        print(f"📁 Transkripte gespeichert in: {matcher.output_path}")
        
    except Exception as e:
        logger.error(f"Kritischer Fehler: {e}")
        print(f"❌ Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
