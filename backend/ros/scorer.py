"""
Research Opportunity Score (ROS) Engine
Deterministic scoring based on evidence and conflict assessment
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ROSScorer:
    """
    Deterministic ROS scoring engine
    
    Factors:
    - Evidence strength: Number and quality of sources
    - Evidence diversity: Multiple agent perspectives  
    - Conflict penalty: Evidence contradictions
    - Recency boost: Recent evidence weight
    - Patent risk penalty: Patent landscape assessment
    """

    def __init__(self):
        self.max_score = 10.0

    def calculate_ros(
        self,
        query: str,
        references: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
        akgp_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate ROS score from evidence
        
        Args:
            query: Original user query
            references: List of evidence references
            insights: List of insights from agents
            akgp_stats: Knowledge graph statistics
            
        Returns:
            Dictionary with ROS score and breakdown
        """
        
        logger.info(f"Calculating ROS for query: {query[:50]}...")
        
        # Parse drug and disease from query
        drug_name, disease_name = self._extract_drug_disease(query)
        logger.info(f"Extracted: drug={drug_name}, disease={disease_name}")
        
        # Calculate component scores
        evidence_strength = self._calculate_evidence_strength(references)
        evidence_diversity = self._calculate_evidence_diversity(references)
        recency_boost = self._calculate_recency_boost(references)
        conflict_penalty = self._calculate_conflict_penalty(insights)
        patent_risk_penalty = self._calculate_patent_risk(references)
        
        # Aggregate ROS score (max 10.0)
        ros_score = (
            evidence_strength +      # 0-3.5
            evidence_diversity +     # 0-2.0
            recency_boost +          # 0-2.0
            conflict_penalty +       # -1.0 to 0
            patent_risk_penalty      # -1.5 to 0
        )
        
        # Clamp score to 0-10
        ros_score = max(0.0, min(10.0, ros_score))
        
        logger.info(f"ROS Score Breakdown:")
        logger.info(f"  Evidence Strength: {evidence_strength:.2f}")
        logger.info(f"  Evidence Diversity: {evidence_diversity:.2f}")
        logger.info(f"  Recency Boost: {recency_boost:.2f}")
        logger.info(f"  Conflict Penalty: {conflict_penalty:.2f}")
        logger.info(f"  Patent Risk: {patent_risk_penalty:.2f}")
        logger.info(f"  TOTAL ROS SCORE: {ros_score:.2f}")
        
        return {
            "ros_score": ros_score,
            "feature_breakdown": {
                "evidence_strength": evidence_strength,
                "evidence_diversity": evidence_diversity,
                "conflict_penalty": conflict_penalty,
                "recency_boost": recency_boost,
                "patent_risk_penalty": patent_risk_penalty,
            },
            "explanation": self._generate_explanation(ros_score, conflict_penalty, len(references)),
            "metadata": {
                "drug_name": drug_name,
                "disease_name": disease_name,
                "num_supporting_evidence": len([r for r in references if r.get('relevance', 0) > 0.5]),
                "num_contradicting_evidence": len([r for r in references if r.get('relevance', 0) < 0.3]),
                "num_suggesting_evidence": len([r for r in references if 0.3 <= r.get('relevance', 0) <= 0.5]),
                "distinct_agents": list(set([r.get('agentId', 'unknown') for r in references if 'agentId' in r])),
                "computation_timestamp": datetime.utcnow().isoformat(),
            }
        }
    
    def _extract_drug_disease(self, query: str) -> tuple[str, str]:
        """Extract drug and disease from query"""
        # Simple heuristic: assume format "Drug for Disease"
        if " for " in query:
            parts = query.split(" for ", 1)
            return parts[0].strip(), parts[1].strip()
        return "Unknown Drug", "Unknown Disease"
    
    def _calculate_evidence_strength(self, references: List[Dict[str, Any]]) -> float:
        """
        Calculate evidence strength (0-3.5)
        Based on: quantity and relevance of sources
        """
        if not references:
            return 0.0
        
        # Base score from count
        count_score = min(len(references) / 10.0, 1.5)  # Max 1.5 from count
        
        # Quality score from relevance
        avg_relevance = sum(r.get('relevance', 0.5) for r in references) / len(references)
        quality_score = avg_relevance * 2.0  # Max 2.0 from quality
        
        total = count_score + quality_score
        return min(total, 3.5)
    
    def _calculate_evidence_diversity(self, references: List[Dict[str, Any]]) -> float:
        """
        Calculate evidence diversity (0-2.0)
        Based on: number of distinct agent sources
        """
        agents = set()
        types = set()
        
        for ref in references:
            if 'agentId' in ref:
                agents.add(ref['agentId'])
            if 'type' in ref:
                types.add(ref['type'])
        
        # Score from agent diversity
        agent_diversity = min(len(agents) / 4.0, 1.0)  # Max 1.0 from 4+ agents
        
        # Score from type diversity
        type_diversity = min(len(types) / 4.0, 1.0)  # Max 1.0 from 4+ types
        
        return (agent_diversity + type_diversity) * 1.0
    
    def _calculate_recency_boost(self, references: List[Dict[str, Any]]) -> float:
        """
        Calculate recency boost (0-2.0)
        Recent evidence weighted more highly
        """
        if not references:
            return 0.0
        
        now = datetime.utcnow()
        recent_count = 0
        
        for ref in references:
            try:
                if 'date' in ref:
                    ref_date = datetime.fromisoformat(ref['date'].replace('Z', '+00:00'))
                    days_old = (now - ref_date).days
                    if days_old < 365:  # Within last year
                        recent_count += 1
            except:
                pass
        
        # Score based on proportion of recent evidence
        recency_ratio = recent_count / len(references)
        return recency_ratio * 2.0  # Max 2.0
    
    def _calculate_conflict_penalty(self, insights: List[Dict[str, Any]]) -> float:
        """
        Calculate conflict penalty (-1.0 to 0)
        More conflicting evidence = larger penalty
        """
        if not insights:
            return 0.0
        
        # Check for conflicting findings
        positive_insights = sum(1 for i in insights if 'positive' in str(i).lower() or 'strong' in str(i).lower())
        negative_insights = sum(1 for i in insights if 'negative' in str(i).lower() or 'weak' in str(i).lower())
        
        if positive_insights == 0 or negative_insights == 0:
            return 0.0  # No conflict
        
        # Calculate conflict ratio
        total_insights = len(insights)
        conflict_ratio = min(negative_insights / total_insights, 1.0)
        
        return -conflict_ratio  # Negative penalty
    
    def _calculate_patent_risk(self, references: List[Dict[str, Any]]) -> float:
        """
        Calculate patent risk penalty (-1.5 to 0)
        More patents = higher risk
        """
        patent_refs = [r for r in references if r.get('type') == 'patent']
        
        if not patent_refs:
            return 0.0
        
        patent_ratio = len(patent_refs) / len(references)
        
        # Higher patent density = higher risk
        if patent_ratio > 0.5:
            return -1.5
        elif patent_ratio > 0.3:
            return -1.0
        elif patent_ratio > 0.1:
            return -0.5
        else:
            return 0.0
    
    def _generate_explanation(self, ros_score: float, conflict: float, ref_count: int) -> str:
        """Generate human-readable ROS explanation"""
        
        if ros_score >= 7.0:
            base = "Strong research opportunity with good evidence support."
        elif ros_score >= 5.0:
            base = "Moderate research opportunity with mixed evidence."
        elif ros_score >= 3.0:
            base = "Weak research opportunity with limited evidence."
        else:
            base = "Poor research opportunity with insufficient supporting evidence."
        
        if conflict < -0.5:
            base += " However, significant conflicting evidence exists."
        elif conflict < 0:
            base += " Some conflicting evidence was noted."
        
        base += f" Analysis based on {ref_count} sources across multiple evidence types."
        
        return base


# Singleton instance
_ros_scorer = ROSScorer()


def calculate_ros(
    query: str,
    references: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    akgp_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate ROS score for query results"""
    return _ros_scorer.calculate_ros(query, references, insights, akgp_stats)
