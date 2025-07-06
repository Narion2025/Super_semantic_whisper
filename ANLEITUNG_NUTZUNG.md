# WhisperSprecherMatcher - Anleitung zur Nutzung

## 🎯 Was wurde repariert?

1. **Google Drive Sync-Probleme behoben** - Das System arbeitet jetzt lokal wenn Google Drive nicht verfügbar ist
2. **Neues V2 Skript erstellt** mit:
   - Chatpartner-Erkennung aus Ordnerstruktur
   - LLM-freundlichem Output-Format
   - Priorisierung des Zoe-Ordners
   - Nur OPUS-Dateien (WhatsApp Audio)
   - Unterstützung für schnellere Transcriber

## 📁 Ordnerstruktur

```
whisper_speaker_matcher/
├── Eingang/                    # Hier Audio-Dateien ablegen
│   ├── Zoe/                   # Wird zuerst verarbeitet
│   │   └── *.opus            
│   ├── Christoph Schröter/
│   │   └── *.opus
│   ├── Freddy/
│   │   └── *.opus
│   └── *.opus                 # Oder direkt hier
├── Transkripte_LLM/           # LLM-optimierte Ausgabe
│   ├── Zoe_WhatsApp_Audio_*.md
│   └── verarbeitungs_report.md
└── Memory/                     # Sprecher-Profile
```

## 🚀 Verwendung

### Option 1: Neues V2 System (Empfohlen!)

```bash
cd /Users/benjaminpoersch/claude/whisper_speaker_matcher

# Mit lokalem Pfad (umgeht Google Drive Probleme)
python3 auto_transcriber_v2.py --local

# Oder direkt mit Google Drive (wenn verfügbar)
python3 auto_transcriber_v2.py
```

### Option 2: Original-System mit lokalem Runner

```bash
python3 run_local.py
# Wähle Option 1 für Transkription
```

### Option 3: Google Drive Sync prüfen

```bash
# Status prüfen
python3 google_drive_sync.py --status

# Synchronisieren wenn verfügbar
python3 google_drive_sync.py --sync
```

## 📝 Output-Format (LLM-optimiert)

Die Transkripte werden im Markdown-Format gespeichert:

```markdown
# WhatsApp Audio Transkription

**Chat mit:** Zoe
**Datum:** 2025-01-12 15:30:45
**Datei:** WhatsApp Audio 2025-01-12 at 15.30.45.opus

## Transkription:

**[Zoe]:** Hey, ich wollte dir nur sagen, dass...

---
*Transkribiert mit WhisperSprecherMatcher V2*
```

## 🎯 Spezielle Features

1. **Automatische Chatpartner-Erkennung**
   - Aus Ordnernamen (z.B. `Eingang/Zoe/`)
   - Aus Dateinamen (falls im Namen enthalten)

2. **Priorisierung**
   - Zoe-Ordner wird immer zuerst verarbeitet
   - Neueste Dateien zuerst

3. **Sprecher-Zuordnung**
   - "Ich" für eigene Nachrichten
   - Chatpartner-Name für deren Nachrichten

## 🛠️ Troubleshooting

### Problem: "Eingang-Ordner nicht gefunden"
```bash
# Erstelle Ordnerstruktur
mkdir -p Eingang/Zoe
mkdir -p Eingang/Christoph\ Schröter
mkdir -p Eingang/Freddy
```

### Problem: "Whisper nicht gefunden"
```bash
# Installiere Whisper
pip3 install openai-whisper
```

### Problem: Speicherplatz voll
```bash
# Prüfe Speicherplatz
df -h /

# Lösche alte Logs
rm -f transcription*.log
```

### Problem: Google Drive Timeout
```bash
# Verwende immer --local Flag
python3 auto_transcriber_v2.py --local
```

## 📊 Verarbeitungsbericht

Nach jeder Verarbeitung findest du einen Bericht unter:
`Transkripte_LLM/verarbeitungs_report.md`

## 🚀 Schnellere Alternativen

Wenn du faster-whisper installieren kannst:
```bash
pip3 install faster-whisper
```

Dann wird es automatisch verwendet (4-5x schneller!).

## 💡 Tipps

1. **Ordne Audio-Dateien in Unterordner** nach Chatpartner für beste Ergebnisse
2. **Lösche verarbeitete OPUS-Dateien** nach erfolgreicher Transkription um Platz zu sparen
3. **Prüfe regelmäßig die Memory-Profile** um zu sehen, was das System über die Sprecher gelernt hat

## 🎉 Viel Erfolg!

Das System ist jetzt bereit, deine WhatsApp-Audios zu transkribieren und dabei zu erkennen, wer mit wem chattet! 