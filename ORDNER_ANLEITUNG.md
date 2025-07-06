# 📁 Ordner-Anleitung für WhatsApp Audio-Dateien

## 🎯 Wo soll ich meine OPUS-Dateien ablegen?

Die OPUS-Dateien (WhatsApp Audio) gehören in den **`Eingang/`** Ordner, organisiert nach Chatpartnern:

```
whisper_speaker_matcher/
└── Eingang/
    ├── Zoe/                      ← Audio-Dateien von/zu Zoe
    ├── Christoph_Schröter/       ← Audio-Dateien von/zu Christoph
    ├── Freddy/                   ← Audio-Dateien von/zu Freddy
    ├── Marike/                   ← Audio-Dateien von/zu Marike
    ├── Vincent/                  ← Audio-Dateien von/zu Vincent
    └── Elke_Christina_Poersch/   ← Audio-Dateien von/zu Elke
```

## 📱 WhatsApp Audio-Dateien Beispiele

Typische WhatsApp Audio-Dateinamen:
- `WhatsApp Audio 2025-06-29 at 13.20.58.opus`
- `WhatsApp Audio 2025-01-12 at 15.30.45.opus`

## 🔄 Verarbeitungsreihenfolge

1. **Zuerst:** Alle Dateien im `Zoe/` Ordner (Priorität!)
2. **Dann:** Alle anderen Ordner alphabetisch
3. **Innerhalb jedes Ordners:** Neueste Aufnahmen zuerst

## 📝 Was passiert bei der Verarbeitung?

### Input:
```
Eingang/Zoe/WhatsApp Audio 2025-06-29 at 13.20.58.opus
```

### Output:
```
Transkripte_LLM/2025-06-29_13-20-58_Zoe_WhatsApp Audio 2025-06-29 at 13.20.58_transkript.md
```

### Inhalt des Transkripts:
```markdown
# WhatsApp Audio Transkription

**Chat mit:** Zoe
**Aufnahme am:** 29.06.2025 um 13:20:58
**Verarbeitet am:** 03.07.2025 um 12:30:15
**Original-Datei:** WhatsApp Audio 2025-06-29 at 13.20.58.opus

## Zeitstempel:
- **Aufnahme-Datum:** 2025-06-29
- **Aufnahme-Uhrzeit:** 13:20:58
- **Verarbeitungszeit:** 2025-07-03 12:30:15

## Transkription:

**[Zoe - 13:20:58]:** Hey, ich wollte dir nur sagen, dass...

## Kontext für LLM:
Diese Nachricht wurde am 29.06.2025 um 13:20:58 in einem WhatsApp-Chat zwischen mir und Zoe aufgenommen.
```

## 🚀 So startest du die Verarbeitung:

```bash
cd /Users/benjaminpoersch/claude/whisper_speaker_matcher

# V3 System mit Datum/Zeit-Extraktion (Empfohlen!)
python3 auto_transcriber_v3.py --local
```

## 💡 Tipps:

1. **Ordne deine Dateien vor der Verarbeitung** - Das System erkennt den Chatpartner automatisch aus dem Ordnernamen
2. **Zoe's Nachrichten zuerst** - Werden automatisch priorisiert
3. **Dateinamen bleiben original** - Das System extrahiert Datum/Zeit automatisch
4. **MP4 werden ignoriert** - Nur OPUS-Dateien werden verarbeitet

## 🎯 Ergebnis:

- **LLM-optimierte Markdown-Dateien** mit allen Zeitstempeln
- **Chatpartner im Dateinamen** für einfache Zuordnung
- **Original-Aufnahmezeit** sowohl im Dateinamen als auch im Transkript
- **Perfekt für weitere AI-Verarbeitung** formatiert

## 📊 Nach der Verarbeitung:

Schaue in den `Transkripte_LLM/` Ordner:
- Alle fertigen Transkripte
- `verarbeitungs_report.md` mit Statistiken
- Dateinamen zeigen sofort Datum, Zeit und Chatpartner

**Viel Erfolg mit der Transkription! 🎉** 