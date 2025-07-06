#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Chat Weaver - Verwebt alle Chat-Inhalte zu einer Super-Semantic-File
Erstellt eine vollständige semantische Repräsentation einer Konversation
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import hashlib
import re
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class SemanticNode:
    """Repräsentiert einen semantischen Knoten im Gespräch"""
    id: str
    timestamp: datetime
    type: str  # 'text', 'audio', 'image', 'document'
    sender: str
    content: str
    emotion: Dict[str, float]
    markers: List[str]
    references: List[str]  # IDs von verwandten Nodes
    metadata: Dict[str, Any]

@dataclass 
class SemanticThread:
    """Ein semantischer Faden durch das Gespräch"""
    id: str
    theme: str
    nodes: List[str]  # Node IDs
    emotional_arc: List[float]  # Emotionaler Verlauf
    tension_points: List[int]  # Indizes von Spannungspunkten
    resolution_points: List[int]  # Indizes von Auflösungen

class SemanticChatWeaver:
    """Webt alle Chat-Elemente zu einer semantischen Einheit"""
    
    def __init__(self, marker_path: Path):
        self.marker_path = marker_path
        self.markers = self._load_all_markers()
        self.nodes: Dict[str, SemanticNode] = {}
        self.threads: List[SemanticThread] = []
        
    def _load_all_markers(self) -> Dict[str, List[str]]:
        """Lade alle semantischen Marker"""
        markers = {}
        marker_dir = Path(self.marker_path) / "ALL_NEWMARKER01"
        
        if marker_dir.exists():
            for marker_file in marker_dir.glob("*_MARKER.txt"):
                marker_name = marker_file.stem
                try:
                    with open(marker_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extrahiere Patterns
                        patterns = re.findall(r'"([^"]+)"', content)
                        if patterns:
                            markers[marker_name] = patterns
                except Exception as e:
                    logger.warning(f"Fehler beim Laden von {marker_file}: {e}")
                    
        return markers
    
    def create_node(self, 
                   timestamp: datetime,
                   type: str,
                   sender: str,
                   content: str,
                   emotion: Dict[str, float] = None,
                   metadata: Dict[str, Any] = None) -> SemanticNode:
        """Erstelle einen semantischen Knoten"""
        
        # Generiere eindeutige ID
        node_id = hashlib.md5(
            f"{timestamp}{type}{sender}{content[:20]}".encode()
        ).hexdigest()[:12]
        
        # Erkenne Marker im Content
        detected_markers = self._detect_markers(content)
        
        # Finde Referenzen zu anderen Nodes
        references = self._find_references(content, timestamp)
        
        node = SemanticNode(
            id=node_id,
            timestamp=timestamp,
            type=type,
            sender=sender,
            content=content,
            emotion=emotion or {},
            markers=detected_markers,
            references=references,
            metadata=metadata or {}
        )
        
        self.nodes[node_id] = node
        return node
    
    def _detect_markers(self, content: str) -> List[str]:
        """Erkenne semantische Marker im Text"""
        detected = []
        content_lower = content.lower()
        
        for marker_name, patterns in self.markers.items():
            for pattern in patterns:
                if pattern.lower() in content_lower:
                    detected.append(marker_name)
                    break
                    
        return detected
    
    def _find_references(self, content: str, timestamp: datetime) -> List[str]:
        """Finde Referenzen zu anderen Nodes"""
        references = []
        
        # Suche nach zeitlichen Bezügen
        time_refs = re.findall(r'(gestern|vorhin|letzte woche|neulich)', content.lower())
        if time_refs:
            # Finde Nodes aus der referenzierten Zeit
            for node_id, node in self.nodes.items():
                if self._is_time_reference_match(node.timestamp, timestamp, time_refs[0]):
                    references.append(node_id)
        
        # Suche nach inhaltlichen Bezügen
        for node_id, node in self.nodes.items():
            similarity = self._calculate_semantic_similarity(content, node.content)
            if similarity > 0.7:  # Threshold
                references.append(node_id)
                
        return references[:5]  # Max 5 Referenzen
    
    def _is_time_reference_match(self, node_time: datetime, ref_time: datetime, ref_word: str) -> bool:
        """Prüfe ob Zeitreferenz passt"""
        time_diff = ref_time - node_time
        
        if ref_word == "vorhin" and 0 < time_diff.total_seconds() < 3600:  # < 1 Stunde
            return True
        elif ref_word == "gestern" and 86400 < time_diff.total_seconds() < 172800:  # 1-2 Tage
            return True
        elif ref_word == "letzte woche" and 604800 < time_diff.total_seconds() < 1209600:  # 7-14 Tage
            return True
            
        return False
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Berechne semantische Ähnlichkeit (vereinfacht)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def identify_threads(self) -> List[SemanticThread]:
        """Identifiziere semantische Fäden durch das Gespräch"""
        threads = []
        
        # Gruppiere Nodes nach Markern
        marker_groups = {}
        for node_id, node in self.nodes.items():
            for marker in node.markers:
                if marker not in marker_groups:
                    marker_groups[marker] = []
                marker_groups[marker].append(node_id)
        
        # Erstelle Threads aus Marker-Gruppen
        for marker, node_ids in marker_groups.items():
            if len(node_ids) > 2:  # Mindestens 3 Nodes für einen Thread
                # Sortiere nach Zeit
                sorted_nodes = sorted(
                    node_ids, 
                    key=lambda nid: self.nodes[nid].timestamp
                )
                
                # Berechne emotionalen Verlauf
                emotional_arc = [
                    self.nodes[nid].emotion.get('valence', 0.0) 
                    for nid in sorted_nodes
                ]
                
                # Finde Spannungs- und Auflösungspunkte
                tension_points = self._find_tension_points(emotional_arc)
                resolution_points = self._find_resolution_points(emotional_arc)
                
                thread = SemanticThread(
                    id=f"thread_{marker}_{len(threads)}",
                    theme=marker,
                    nodes=sorted_nodes,
                    emotional_arc=emotional_arc,
                    tension_points=tension_points,
                    resolution_points=resolution_points
                )
                threads.append(thread)
        
        self.threads = threads
        return threads
    
    def _find_tension_points(self, emotional_arc: List[float]) -> List[int]:
        """Finde Punkte steigender Spannung"""
        tension_points = []
        
        for i in range(1, len(emotional_arc) - 1):
            # Negativer Trend
            if emotional_arc[i] < emotional_arc[i-1] and emotional_arc[i] < emotional_arc[i+1]:
                tension_points.append(i)
                
        return tension_points
    
    def _find_resolution_points(self, emotional_arc: List[float]) -> List[int]:
        """Finde Auflösungspunkte"""
        resolution_points = []
        
        for i in range(1, len(emotional_arc) - 1):
            # Positiver Trend nach Negativem
            if emotional_arc[i] > emotional_arc[i-1] and emotional_arc[i-1] < 0:
                resolution_points.append(i)
                
        return resolution_points
    
    def weave_super_semantic_file(self, output_path: Path) -> Dict[str, Any]:
        """Erstelle die Super-Semantic-File"""
        
        # Identifiziere Threads wenn noch nicht geschehen
        if not self.threads:
            self.identify_threads()
        
        # Berechne Gesamt-Statistiken
        total_emotion_valence = sum(
            node.emotion.get('valence', 0.0) 
            for node in self.nodes.values()
        ) / len(self.nodes) if self.nodes else 0
        
        # Erstelle Marker-Häufigkeiten
        marker_frequencies = {}
        for node in self.nodes.values():
            for marker in node.markers:
                marker_frequencies[marker] = marker_frequencies.get(marker, 0) + 1
        
        # Finde wichtigste Themen
        top_themes = sorted(
            marker_frequencies.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Erstelle Timeline
        timeline = self._create_timeline()
        
        # Erstelle Super-Semantic-Structure
        super_semantic = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "total_nodes": len(self.nodes),
                "total_threads": len(self.threads),
                "time_span": {
                    "start": min(n.timestamp for n in self.nodes.values()).isoformat() if self.nodes else None,
                    "end": max(n.timestamp for n in self.nodes.values()).isoformat() if self.nodes else None
                }
            },
            "emotional_summary": {
                "overall_valence": total_emotion_valence,
                "emotional_range": self._calculate_emotional_range(),
                "dominant_emotions": self._get_dominant_emotions()
            },
            "semantic_summary": {
                "top_themes": dict(top_themes),
                "marker_frequencies": marker_frequencies,
                "semantic_density": len(marker_frequencies) / len(self.nodes) if self.nodes else 0
            },
            "timeline": timeline,
            "nodes": {
                node_id: asdict(node) 
                for node_id, node in self.nodes.items()
            },
            "threads": [
                asdict(thread) 
                for thread in self.threads
            ],
            "relationships": self._extract_relationships(),
            "narrative_structure": self._analyze_narrative_structure()
        }
        
        # Speichere als JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(super_semantic, f, indent=2, ensure_ascii=False, default=str)
        
        # Erstelle auch eine lesbare Zusammenfassung
        summary_path = output_path.with_suffix('.summary.md')
        self._create_readable_summary(super_semantic, summary_path)
        
        return super_semantic
    
    def _create_timeline(self) -> List[Dict[str, Any]]:
        """Erstelle eine chronologische Timeline"""
        timeline = []
        
        sorted_nodes = sorted(
            self.nodes.values(), 
            key=lambda n: n.timestamp
        )
        
        for i, node in enumerate(sorted_nodes):
            timeline_entry = {
                "index": i,
                "timestamp": node.timestamp.isoformat(),
                "node_id": node.id,
                "type": node.type,
                "sender": node.sender,
                "preview": node.content[:100] + "..." if len(node.content) > 100 else node.content,
                "emotion": node.emotion.get('dominant_emotion', 'neutral'),
                "markers": node.markers[:3]  # Top 3 Marker
            }
            timeline.append(timeline_entry)
            
        return timeline
    
    def _calculate_emotional_range(self) -> Dict[str, float]:
        """Berechne emotionale Bandbreite"""
        if not self.nodes:
            return {"min": 0, "max": 0, "variance": 0}
            
        valences = [
            node.emotion.get('valence', 0.0) 
            for node in self.nodes.values()
        ]
        
        return {
            "min": min(valences),
            "max": max(valences),
            "variance": sum((v - sum(valences)/len(valences))**2 for v in valences) / len(valences)
        }
    
    def _get_dominant_emotions(self) -> Dict[str, int]:
        """Zähle dominante Emotionen"""
        emotion_counts = {}
        
        for node in self.nodes.values():
            dominant = node.emotion.get('dominant_emotion', 'neutral')
            emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
            
        return dict(sorted(
            emotion_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5])
    
    def _extract_relationships(self) -> List[Dict[str, Any]]:
        """Extrahiere Beziehungen zwischen Nodes"""
        relationships = []
        
        for node_id, node in self.nodes.items():
            for ref_id in node.references:
                if ref_id in self.nodes:
                    relationships.append({
                        "from": node_id,
                        "to": ref_id,
                        "type": "reference",
                        "strength": self._calculate_relationship_strength(node, self.nodes[ref_id])
                    })
                    
        return relationships
    
    def _calculate_relationship_strength(self, node1: SemanticNode, node2: SemanticNode) -> float:
        """Berechne Stärke der Beziehung"""
        # Zeitliche Nähe
        time_diff = abs((node1.timestamp - node2.timestamp).total_seconds())
        time_score = 1.0 / (1.0 + time_diff / 3600)  # 1 Stunde als Basis
        
        # Marker-Überlappung
        common_markers = set(node1.markers).intersection(set(node2.markers))
        marker_score = len(common_markers) / max(len(node1.markers), len(node2.markers), 1)
        
        # Emotionale Ähnlichkeit
        emotion_diff = abs(
            node1.emotion.get('valence', 0) - node2.emotion.get('valence', 0)
        )
        emotion_score = 1.0 - emotion_diff
        
        return (time_score + marker_score + emotion_score) / 3
    
    def _analyze_narrative_structure(self) -> Dict[str, Any]:
        """Analysiere narrative Struktur"""
        if not self.nodes:
            return {}
            
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.timestamp)
        
        # Finde Wendepunkte
        turning_points = []
        for i in range(1, len(sorted_nodes) - 1):
            prev_valence = sorted_nodes[i-1].emotion.get('valence', 0)
            curr_valence = sorted_nodes[i].emotion.get('valence', 0)
            next_valence = sorted_nodes[i+1].emotion.get('valence', 0)
            
            # Großer emotionaler Wechsel
            if abs(curr_valence - prev_valence) > 0.5:
                turning_points.append({
                    "index": i,
                    "node_id": sorted_nodes[i].id,
                    "change": curr_valence - prev_valence,
                    "timestamp": sorted_nodes[i].timestamp.isoformat()
                })
        
        # Finde Höhepunkte und Tiefpunkte
        valences = [(i, n.emotion.get('valence', 0)) for i, n in enumerate(sorted_nodes)]
        peaks = sorted(valences, key=lambda x: x[1], reverse=True)[:3]
        valleys = sorted(valences, key=lambda x: x[1])[:3]
        
        return {
            "turning_points": turning_points,
            "emotional_peaks": [
                {"index": i, "node_id": sorted_nodes[i].id, "valence": v}
                for i, v in peaks
            ],
            "emotional_valleys": [
                {"index": i, "node_id": sorted_nodes[i].id, "valence": v}
                for i, v in valleys
            ],
            "narrative_arc": self._classify_narrative_arc(sorted_nodes)
        }
    
    def _classify_narrative_arc(self, sorted_nodes: List[SemanticNode]) -> str:
        """Klassifiziere den narrativen Bogen"""
        if not sorted_nodes:
            return "empty"
            
        start_valence = sorted_nodes[0].emotion.get('valence', 0)
        middle_valence = sorted_nodes[len(sorted_nodes)//2].emotion.get('valence', 0)
        end_valence = sorted_nodes[-1].emotion.get('valence', 0)
        
        if end_valence > start_valence + 0.3:
            return "rising_positive"  # Happy End
        elif end_valence < start_valence - 0.3:
            return "falling_negative"  # Tragisch
        elif middle_valence < start_valence - 0.3 and middle_valence < end_valence - 0.3:
            return "valley_recovery"  # Krise und Erholung
        elif middle_valence > start_valence + 0.3 and middle_valence > end_valence + 0.3:
            return "peak_decline"  # Höhepunkt und Fall
        else:
            return "stable"  # Stabil
    
    def _create_readable_summary(self, super_semantic: Dict[str, Any], output_path: Path):
        """Erstelle eine lesbare Zusammenfassung"""
        summary = f"""# 📊 Super-Semantic Chat-Analyse

**Erstellt am:** {super_semantic['metadata']['created_at']}
**Zeitraum:** {super_semantic['metadata']['time_span']['start']} bis {super_semantic['metadata']['time_span']['end']}

## 🎭 Emotionale Zusammenfassung

**Gesamt-Valenz:** {super_semantic['emotional_summary']['overall_valence']:.2f}
**Emotionale Bandbreite:** {super_semantic['emotional_summary']['emotional_range']['min']:.2f} bis {super_semantic['emotional_summary']['emotional_range']['max']:.2f}

**Dominante Emotionen:**
"""
        for emotion, count in super_semantic['emotional_summary']['dominant_emotions'].items():
            summary += f"- {emotion}: {count} mal\n"
        
        summary += f"""

## 🏷️ Semantische Themen

**Top Themen:**
"""
        for theme, count in super_semantic['semantic_summary']['top_themes'].items():
            summary += f"- {theme}: {count} mal\n"
        
        summary += f"""

## 📈 Narrative Struktur

**Narrativer Bogen:** {super_semantic['narrative_structure']['narrative_arc']}
**Wendepunkte:** {len(super_semantic['narrative_structure']['turning_points'])}

## 🧵 Semantische Fäden

Es wurden {super_semantic['metadata']['total_threads']} thematische Fäden identifiziert:

"""
        for thread in super_semantic['threads'][:5]:  # Top 5 Threads
            summary += f"- **{thread['theme']}**: {len(thread['nodes'])} Nachrichten\n"
        
        summary += f"""

## 💫 Besondere Momente

### Emotionale Höhepunkte:
"""
        for peak in super_semantic['narrative_structure']['emotional_peaks']:
            node = super_semantic['nodes'][peak['node_id']]
            summary += f"- {node['timestamp']}: \"{node['content'][:50]}...\" (Valenz: {peak['valence']:.2f})\n"
        
        summary += f"""

### Emotionale Tiefpunkte:
"""
        for valley in super_semantic['narrative_structure']['emotional_valleys']:
            node = super_semantic['nodes'][valley['node_id']]
            summary += f"- {node['timestamp']}: \"{node['content'][:50]}...\" (Valenz: {valley['valence']:.2f})\n"
        
        summary += f"""

---
*Diese Analyse wurde automatisch erstellt und zeigt die semantische Struktur des Gesprächs.*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)


def integrate_whatsapp_export(export_file: Path, weaver: SemanticChatWeaver) -> None:
    """Integriere einen WhatsApp-Export in die semantische Analyse"""
    
    # Hier würde der WhatsApp-Export-Parser kommen
    # Für das Beispiel simuliere ich es
    
    # Parse WhatsApp Export (vereinfacht)
    with open(export_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        # WhatsApp Format: [DD.MM.YY, HH:MM:SS] Sender: Message
        match = re.match(r'\[(\d{2}\.\d{2}\.\d{2}), (\d{2}:\d{2}:\d{2})\] ([^:]+): (.+)', line)
        if match:
            date_str, time_str, sender, message = match.groups()
            
            # Parse Timestamp
            timestamp = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M:%S")
            
            # Erstelle Node
            weaver.create_node(
                timestamp=timestamp,
                type='text',
                sender=sender.strip(),
                content=message.strip(),
                emotion={'valence': 0.0}  # Würde durch Analyse gefüllt
            )


# Beispiel-Verwendung
if __name__ == "__main__":
    # Initialisiere Weaver
    weaver = SemanticChatWeaver(Path("../ALL_SEMANTIC_MARKER_TXT"))
    
    # Lade verschiedene Quellen
    # 1. WhatsApp Export
    # integrate_whatsapp_export(Path("whatsapp_export.txt"), weaver)
    
    # 2. Transkripte (bereits verarbeitet)
    transcript_dir = Path("Transkripte_LLM")
    for transcript in transcript_dir.glob("*_emotion_transkript.md"):
        # Parse und füge hinzu...
        pass
    
    # 3. Erstelle Super-Semantic-File
    output = weaver.weave_super_semantic_file(Path("super_semantic_chat.json"))
    
    print(f"✨ Super-Semantic-File erstellt mit {len(weaver.nodes)} Nodes und {len(weaver.threads)} Threads!") 