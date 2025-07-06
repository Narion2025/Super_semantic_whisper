# WhisperSprecherMatcher 🎤

Ein intelligentes System zur automatischen Transkription von WhatsApp-Audionachrichten mit Sprechererkennung und Memory-System Integration.

## 🚀 Features

- **Automatische Audio-Transkription** mit OpenAI Whisper
- **Intelligente Sprechererkennung** basierend auf Sprachmustern und Kontext
- **Memory-System** das Sprecher-Profile aufbaut und erweitert
- **Multi-Format Support** für Audio-Dateien (.opus, .wav, .mp3, .m4a, .ogg)
- **Automatische Verarbeitung** neuer Audio-Dateien
- **Lokaler Fallback** wenn Google Drive nicht verfügbar ist

## 📋 Voraussetzungen

- **Python 3.8+**
- **FFmpeg** (für Audio-Konvertierung)
- **Mindestens 4GB RAM** (für Whisper-Modelle)

### FFmpeg Installation

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
- Lade FFmpeg von https://ffmpeg.org/ herunter
- Füge FFmpeg zum PATH hinzu

## 🛠️ Installation

### Schritt 1: Repository klonen/downloaden
```bash
cd /Users/benjaminpoersch/claude
```

### Schritt 2: Automatisches Setup
```bash
cd whisper_speaker_matcher
python3 setup_environment.py
```

Das Setup-Skript:
- ✅ Prüft Python-Version
- 📦 Installiert alle Python-Abhängigkeiten
- 📁 Erstellt Verzeichnisstruktur
- 🧪 Testet die Installation
- 🚀 Erstellt Launcher-Skript

### Schritt 3: Manuelle Installation (falls Setup fehlschlägt)
```bash
pip3 install -r requirements.txt
```

## 🎯 Nutzung

### Option 1: Launcher verwenden
```bash
cd whisper_speaker_matcher
./start.sh
```

### Option 2: Direkte Ausführung

**Audio transkribieren:**
```bash
python3 auto_transcriber.py
```

**Memory aus Transkriptionen aufbauen:**
```bash
python3 build_memory_from_transcripts.py
```

## 📁 Verzeichnisstruktur

```
whisper_speaker_matcher/
├── Eingang/                    # Audio-Dateien hier ablegen
│   ├── ben/                   # Sprecher-spezifische Ordner
│   ├── zoe/
│   └── *.opus, *.wav, etc.    # Audio-Dateien
├── Memory/                     # Sprecher-Profile (YAML)
│   ├── ben.yaml
│   ├── zoe.yaml
│   └── schroeti.yaml
├── auto_transcriber.py         # Haupt-Transkriptions-Skript
├── build_memory_from_transcripts.py  # Memory-Builder
└── logs/                       # Log-Dateien
```

## 🧠 Memory-System

Das System erstellt für jeden Sprecher ein YAML-Profil mit:

- **Sprachcharakteristika** (Füllwörter, Satzlänge, etc.)
- **Themen-Präferenzen** (Technology, Business, Personal, etc.)
- **Sentiment-Analyse** (Positive/Negative Ausdrücke)
- **Interaktions-Historie** (Letzte 50 Transkriptionen)
- **Automatische Charakterisierung** (expressiv, präzise, technisch_orientiert)

### Beispiel Memory-Profil:
```yaml
name: Ben
last_updated: '2025-01-12T15:30:00'
total_interactions: 42
statistics:
  avg_sentence_length: 12.5
  most_common_words:
    also: 15
    genau: 12
    interessant: 8
  sentiment:
    positive: 25
    negative: 3
    ratio: 0.89
topics:
  technology: 45
  business: 23
  personal: 12
characteristics:
  - technisch_orientiert
  - bedächtig
  - präzise
```

## 🔧 Sprechererkennung

Das System verwendet mehrere Methoden zur Sprechererkennung:

1. **Dateiname-Analyse** - Erkennt Sprecher aus Dateinamen
2. **Keyword-Matching** - Analysiert charakteristische Wörter/Phrasen
3. **Kontext-Analyse** - Nutzt Selbsterwähnungen und Kontext
4. **Memory-basierte Vorhersagen** - Lernt aus vergangenen Transkriptionen

## 📊 Ausgabeformat

Verarbeitete Transkriptionen werden gespeichert als:
```
YYYY-MM-DD_sprecher_originaldatei.txt
```

Inhalt:
```
Sprecher: ben
Datei: WhatsApp Audio 2025-01-12 at 15.30.45.opus
Datum: 2025-01-12 15:30:45
Transkription:
Also, das ist wirklich interessant. Ich denke, wir sollten...
```

## 🛠️ Fehlerbehebung

### Whisper-Installation Probleme
```bash
# Neuinstallation
pip3 uninstall openai-whisper
pip3 install openai-whisper

# Oder mit Conda
conda install openai-whisper -c conda-forge
```

### FFmpeg nicht gefunden
```bash
# Prüfe Installation
ffmpeg -version

# macOS: Homebrew Pfad hinzufügen
export PATH="/opt/homebrew/bin:$PATH"
```

### Google Drive Sync-Probleme
Das System erstellt automatisch einen lokalen Fallback wenn Google Drive nicht verfügbar ist:
```
./whisper_speaker_matcher/
├── Eingang/
└── Memory/
```

### Logging
Alle Aktivitäten werden geloggt in:
- `transcription.log` (im Ausführungsverzeichnis)
- Console-Ausgabe mit Timestamps

## 🔄 Automatisierung

Für kontinuierliche Verarbeitung kann das System mit Cron oder launchd automatisiert werden:

### macOS launchd Beispiel:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.whisper-transcriber</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/auto_transcriber.py</string>
    </array>
    <key>WatchPaths</key>
    <array>
        <string>/path/to/Eingang</string>
    </array>
</dict>
</plist>
```

## 📝 Logs und Monitoring

Das System erstellt detaillierte Logs:
- ✅ Erfolgreich verarbeitete Dateien
- ⚠️ Warnungen (FFmpeg nicht gefunden, etc.)
- ❌ Fehler mit Dateiname und Grund
- 📊 Statistiken (Anzahl verarbeiteter Dateien, erkannte Sprecher)

## 🤝 Support

Bei Problemen:
1. Prüfe die Log-Dateien
2. Stelle sicher, dass alle Abhängigkeiten installiert sind
3. Teste mit einem kleinen Audio-Sample
4. Prüfe Dateiberechtigungen im Eingang-Ordner

## 📄 Lizenz

Dieses Projekt ist für persönlichen Gebrauch entwickelt.

## 🎉 Viel Erfolg!

Das WhisperSprecherMatcher-System wird deine WhatsApp-Audionachrichten intelligent transkribieren und dabei lernen, wer spricht. Je mehr du es nutzt, desto besser wird die Sprechererkennung! 