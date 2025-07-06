#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Semantic Weaver - Nutzt alle deine vorhandenen Komponenten
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import yaml
import re
from typing import List, Dict, Any

# Füge Pfade hinzu für die verschiedenen Module
sys.path.insert(0, str(Path(__file__).parent.parent / "Marker_assist_bot"))
sys.path.insert(0, str(Path(__file__).parent.parent / "MARSAP"))
sys.path.insert(0, str(Path(__file__).parent.parent / "MARSAPv2"))

class IntegratedSemanticWeaver:
    """Integriert alle Komponenten für die Super-Semantic-File"""
    
    def __init__(self):
        self.marker_path = Path("../ALL_SEMANTIC_MARKER_TXT/ALL_NEWMARKER01")
        self.semantic_grabber_path = Path("../Marker_assist_bot/semantic_grabber_library.yaml")
        self.nodes = {}
        self.threads = []
        self.marker_analyzer = None
        self.cosd_analyzer = None
        self._initialize_components()
        
    def _initialize_components(self):
        """Initialisiere alle Komponenten"""
        # 1. Lade Semantic Grabber
        self.semantic_grabbers = self._load_semantic_grabbers()
        
        # 2. Initialisiere Marker-System
        try:
            from frausar_gui import FRAUSARAssistant
            self.marker_analyzer = FRAUSARAssistant(str(self.marker_path.parent))
            print("✅ FRAUSAR Marker-System geladen")
        except Exception as e:
            print(f"⚠️ FRAUSAR nicht verfügbar: {e}")
            
        # 3. Initialisiere CoSD/MARSAP
        try:
            from cosd import CoSDAnalyzer
            self.cosd_analyzer = CoSDAnalyzer()
            print("✅ CoSD/MARSAP Analyzer geladen")
        except Exception as e:
            print(f"⚠️ CoSD nicht verfügbar: {e}")
    
    def _load_semantic_grabbers(self) -> Dict[str, Any]:
        """Lade Semantic Grabbers aus YAML"""
        if self.semantic_grabber_path.exists():
            with open(self.semantic_grabber_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('semantic_grabbers', {})
        return {}
    
    def process_chat_export(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeite einen kompletten Chat-Export"""
        super_semantic = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "2.0",
                "components": {
                    "markers": bool(self.marker_analyzer),
                    "cosd": bool(self.cosd_analyzer),
                    "semantic_grabbers": len(self.semantic_grabbers)
                }
            },
            "nodes": {},
            "analysis": {}
        }
        
        # Verarbeite jeden Chat-Eintrag
        all_texts = []
        for entry in export_data.get('messages', []):
            node = self._create_semantic_node(entry)
            super_semantic['nodes'][node['id']] = node
            all_texts.append(entry.get('content', ''))
        
        # Führe Gesamt-Analysen durch
        if all_texts:
            # 1. Marker-Analyse
            if self.marker_analyzer:
                marker_results = self._analyze_with_markers(all_texts)
                super_semantic['analysis']['markers'] = marker_results
            
            # 2. CoSD/MARSAP Analyse
            if self.cosd_analyzer:
                cosd_results = self._analyze_with_cosd(all_texts)
                super_semantic['analysis']['cosd'] = cosd_results
            
            # 3. Semantic Grabber Matching
            grabber_results = self._match_semantic_grabbers(all_texts)
            super_semantic['analysis']['semantic_grabbers'] = grabber_results
        
        # Erstelle Verbindungen
        super_semantic['connections'] = self._find_semantic_connections(super_semantic['nodes'])
        
        return super_semantic
    
    def _create_semantic_node(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Erstelle einen semantischen Knoten aus einem Chat-Eintrag"""
        import hashlib
        
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', datetime.now())
        
        node_id = hashlib.md5(
            f"{timestamp}{content[:50]}".encode()
        ).hexdigest()[:12]
        
        return {
            'id': node_id,
            'timestamp': str(timestamp),
            'type': entry.get('type', 'text'),
            'sender': entry.get('sender', 'unknown'),
            'content': content,
            'emotion': entry.get('emotion', {}),
            'metadata': entry.get('metadata', {})
        }
    
    def _analyze_with_markers(self, texts: List[str]) -> Dict[str, Any]:
        """Analysiere Texte mit dem Marker-System"""
        results = {
            'detected_markers': {},
            'marker_frequencies': {},
            'top_patterns': []
        }
        
        for text in texts:
            # Nutze das FRAUSAR System zur Marker-Erkennung
            markers = self.marker_analyzer.analyze_text_for_markers(text)
            for marker in markers:
                marker_name = marker.get('name', 'unknown')
                results['marker_frequencies'][marker_name] = \
                    results['marker_frequencies'].get(marker_name, 0) + 1
        
        # Sortiere nach Häufigkeit
        results['top_patterns'] = sorted(
            results['marker_frequencies'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return results
    
    def _analyze_with_cosd(self, texts: List[str]) -> Dict[str, Any]:
        """Analysiere mit CoSD/MARSAP"""
        try:
            result = self.cosd_analyzer.analyze_drift(texts)
            
            return {
                'risk_level': result.risk_assessment.get('risk_level', 'unknown'),
                'drift_velocity': getattr(result, 'drift_velocity', {}),
                'emergent_clusters': len(getattr(result, 'emergent_clusters', [])),
                'resonance_patterns': len(getattr(result, 'resonance_patterns', [])),
                'recommendations': result.risk_assessment.get('recommendations', [])[:3]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _match_semantic_grabbers(self, texts: List[str]) -> Dict[str, Any]:
        """Matche Texte gegen Semantic Grabbers"""
        results = {
            'matched_grabbers': {},
            'top_matches': []
        }
        
        for text in texts:
            for grabber_id, grabber_data in self.semantic_grabbers.items():
                patterns = grabber_data.get('patterns', [])
                for pattern in patterns:
                    if pattern.lower() in text.lower():
                        results['matched_grabbers'][grabber_id] = \
                            results['matched_grabbers'].get(grabber_id, 0) + 1
                        break
        
        results['top_matches'] = sorted(
            results['matched_grabbers'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return results
    
    def _find_semantic_connections(self, nodes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Finde semantische Verbindungen zwischen Nodes"""
        connections = []
        
        # Vereinfachte Verbindungslogik
        node_list = list(nodes.values())
        for i in range(len(node_list) - 1):
            # Verbinde aufeinanderfolgende Nachrichten
            connections.append({
                'from': node_list[i]['id'],
                'to': node_list[i+1]['id'],
                'type': 'temporal',
                'strength': 1.0
            })
        
        return connections

# Beispiel-Verwendung
if __name__ == "__main__":
    weaver = IntegratedSemanticWeaver()
    
    # Beispiel-Export
    export_data = {
        'messages': [
            {
                'timestamp': datetime.now(),
                'sender': 'Zoe',
                'content': 'Hey, ich vermisse dich so sehr!',
                'type': 'text',
                'emotion': {'valence': -0.3, 'dominant_emotion': 'sehnsuchtsvoll_still'}
            }
        ]
    }
    
    result = weaver.process_chat_export(export_data)
    
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str)) 