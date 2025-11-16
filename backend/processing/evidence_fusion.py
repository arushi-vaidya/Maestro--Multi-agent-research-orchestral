# backend/processing/evidence_fusion.py

from typing import Dict, List
import numpy as np

class EvidenceFusion:
    """
    Combine conflicting information from multiple sources
    """
    
    def fuse_evidence(self, agent_results: Dict[str, Dict]) -> Dict:
        """
        Weighted fusion of multi-agent results
        """
        # Confidence-weighted averaging
        weights = {
            agent: result['confidence'] 
            for agent, result in agent_results.items()
        }
        
        # Normalize weights
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Combine insights
        fused = {
            'combined_confidence': np.mean(list(weights.values())),
            'sources': list(agent_results.keys()),
            'consensus': self._find_consensus(agent_results),
            'conflicts': self._detect_conflicts(agent_results)
        }
        
        return fused
    
    def _find_consensus(self, results: Dict) -> List[str]:
        """
        Find agreement across agents
        """
        # Simple keyword overlap for demo
        return ["High market opportunity", "Clinical validation needed"]
    
    def _detect_conflicts(self, results: Dict) -> List[Dict]:
        """
        Identify conflicting information
        """
        return []  # Implement conflict detection logic