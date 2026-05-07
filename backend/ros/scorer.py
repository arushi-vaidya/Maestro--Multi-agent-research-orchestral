"""
Research Opportunity Score (ROS) Engine - IMPROVED
Deterministic scoring that differentiates research opportunities

Key Improvements:
1. Log-scaled evidence strength (no more saturation at 3.5)
2. True recency signals (publication year, trial status)
3. NEW: Novelty/saturation factor (early-phase, under-explored indications score HIGHER)
4. Transparent, tunable formula with configurable weights
5. Clear documentation of why each score is calculated

Factors:
- Evidence strength: Log-scaled quantity and quality
- Evidence diversity: Multiple agent perspectives
- Recency boost: Recent evidence (publication year, trial status)
- Novelty score: Under-explored vs. saturated indications (NEW)
- Conflict penalty: Evidence contradictions
- Patent risk penalty: Patent saturation (freedom-to-operate risk)
"""

import logging
import math
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from ros.ros_config import (
    WEIGHTS, EVIDENCE_STRENGTH, EVIDENCE_DIVERSITY, RECENCY_BOOST,
    NOVELTY_FACTOR, CONFLICT_PENALTY, PATENT_RISK, CLAMPING, DEBUG
)

logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Initialize Gemini with API key from .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("✅ Gemini API initialized with API key from .env")
    except Exception as e:
        logger.warning(f"⚠️  Could not configure Gemini: {e}")
else:
    logger.warning("⚠️  GOOGLE_API_KEY not set in .env - Gemini ROS scoring will not be available")


class ROSScorer:
    """
    Improved ROS scoring engine with transparent formula
    
    Formula:
    ROS = w1 * EvidenceStrength +
          w2 * EvidenceDiversity +
          w3 * RecencyBoost +
          w4 * NoveltyScore -
          w5 * ConflictPenalty -
          w6 * PatentRisk
    """

    def __init__(self):
        self.weights = WEIGHTS
        self.max_score = CLAMPING["max_ros"]
        self.min_score = CLAMPING["min_ros"]
        self.debug = DEBUG["verbose_logging"]

    def calculate_ros(
        self,
        query: str,
        references: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
        akgp_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate ROS score from evidence using TRANSPARENT formula.
        
        Args:
            query: Original user query
            references: List of evidence references
            insights: List of insights from agents
            akgp_stats: Knowledge graph statistics (for novelty detection)
            
        Returns:
            Dictionary with ROS score, breakdown, and explanation
        """
        
        if self.debug:
            logger.info(f"[ROS] Calculating score for query: {query[:50]}...")
        
        # Extract drug and disease
        drug_name, disease_name = self._extract_drug_disease(query)
        if self.debug:
            logger.info(f"[ROS] Extracted: drug={drug_name}, disease={disease_name}")
        
        # ================================================================
        # COMPONENT 1: EVIDENCE STRENGTH (LOG-SCALED, NO SATURATION)
        # ================================================================
        evidence_strength = self._calculate_evidence_strength(references, drug_name, disease_name)
        
        # ================================================================
        # COMPONENT 2: EVIDENCE DIVERSITY
        # ================================================================
        evidence_diversity = self._calculate_evidence_diversity(references)
        
        # ================================================================
        # COMPONENT 3: RECENCY BOOST (TRUE SIGNAL)
        # ================================================================
        recency_boost = self._calculate_recency_boost(references)
        
        # ================================================================
        # COMPONENT 4: NOVELTY FACTOR (NEW - MOST IMPORTANT FOR ROS)
        # ================================================================
        novelty_score = self._calculate_novelty_factor(references, insights, akgp_stats)
        
        # ================================================================
        # COMPONENT 5: CONFLICT PENALTY
        # ================================================================
        conflict_penalty = self._calculate_conflict_penalty(insights)
        
        # ================================================================
        # COMPONENT 6: PATENT RISK PENALTY
        # ================================================================
        patent_risk_penalty = self._calculate_patent_risk(references)
        
        # ================================================================
        # AGGREGATE ROS USING TRANSPARENT FORMULA
        # ================================================================
        ros_score = (
            self.weights["evidence_strength"] * evidence_strength +
            self.weights["evidence_diversity"] * evidence_diversity +
            self.weights["recency_boost"] * recency_boost +
            self.weights["novelty_score"] * novelty_score -
            self.weights["conflict_penalty"] * conflict_penalty -
            self.weights["patent_risk"] * patent_risk_penalty
        )
        
        # Clamp to valid range
        ros_score = max(self.min_score, min(self.max_score, ros_score))
        
        if self.debug:
            logger.info(f"[ROS] ════════════════════════════════════")
            logger.info(f"[ROS] COMPONENT SCORES:")
            logger.info(f"[ROS]   Evidence Strength:     {evidence_strength:.2f} × {self.weights['evidence_strength']:.1f} = {self.weights['evidence_strength'] * evidence_strength:.2f}")
            logger.info(f"[ROS]   Evidence Diversity:    {evidence_diversity:.2f} × {self.weights['evidence_diversity']:.1f} = {self.weights['evidence_diversity'] * evidence_diversity:.2f}")
            logger.info(f"[ROS]   Recency Boost:         {recency_boost:.2f} × {self.weights['recency_boost']:.1f} = {self.weights['recency_boost'] * recency_boost:.2f}")
            logger.info(f"[ROS]   Novelty Score:         {novelty_score:.2f} × {self.weights['novelty_score']:.1f} = {self.weights['novelty_score'] * novelty_score:.2f}")
            logger.info(f"[ROS]   Conflict Penalty:      {conflict_penalty:.2f} × {self.weights['conflict_penalty']:.1f} = {self.weights['conflict_penalty'] * conflict_penalty:.2f} (subtracted)")
            logger.info(f"[ROS]   Patent Risk Penalty:   {patent_risk_penalty:.2f} × {self.weights['patent_risk']:.1f} = {self.weights['patent_risk'] * patent_risk_penalty:.2f} (subtracted)")
            logger.info(f"[ROS] ════════════════════════════════════")
            logger.info(f"[ROS] FINAL ROS SCORE: {ros_score:.2f} / {self.max_score:.1f}")
        
        return {
            "ros_score": ros_score,
            "confidence_level": self._get_confidence_level(ros_score),
            "feature_breakdown": {
                "evidence_strength": evidence_strength,
                "evidence_diversity": evidence_diversity,
                "recency_boost": recency_boost,
                "novelty_score": novelty_score,
                "conflict_penalty": conflict_penalty,
                "patent_risk_penalty": patent_risk_penalty,
            },
            "weighted_breakdown": {
                "evidence_strength_weighted": self.weights["evidence_strength"] * evidence_strength,
                "evidence_diversity_weighted": self.weights["evidence_diversity"] * evidence_diversity,
                "recency_boost_weighted": self.weights["recency_boost"] * recency_boost,
                "novelty_score_weighted": self.weights["novelty_score"] * novelty_score,
                "conflict_penalty_weighted": self.weights["conflict_penalty"] * conflict_penalty,
                "patent_risk_weighted": self.weights["patent_risk"] * patent_risk_penalty,
            },
            "explanation": self._generate_explanation(ros_score, novelty_score, conflict_penalty, len(references)),
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
    
    def _extract_drug_disease(self, query: str) -> tuple:
        """Extract drug and disease from query string"""
        if " for " in query:
            parts = query.split(" for ", 1)
            return parts[0].strip(), parts[1].strip()
        return "Unknown Drug", "Unknown Disease"
    
    def _calculate_evidence_strength(self, references: List[Dict[str, Any]], drug: str, disease: str) -> float:
        """
        IMPROVED: Log-scaled evidence strength (no saturation)
        
        OLD LOGIC: Linear, capped at 3.5 (10 sources = 50 sources = 200 sources got same score)
        NEW LOGIC: log(1 + weighted_count) * scale_factor (diminishing returns but differentiates)
        
        Returns: 0-4.0
        """
        if not references:
            return 0.0
        
        # Calculate weighted evidence count
        # Weight by quality (relevance) and evidence type
        weighted_count = 0.0
        for ref in references:
            relevance = ref.get('relevance', 0.5)  # 0-1
            ref_type = ref.get('type', 'clinical_trial')
            type_weight = EVIDENCE_STRENGTH["quality_weights"].get(ref_type, 0.7)
            
            # Weighted contribution: relevance * type_weight
            weighted_count += (relevance * type_weight)
        
        # Log-scale with diminishing returns
        # log(1 + x) grows but never explodes
        log_count = math.log(1.0 + weighted_count)
        strength = log_count * EVIDENCE_STRENGTH["scale_factor"]
        strength = min(strength, EVIDENCE_STRENGTH["max_strength"])
        
        if self.debug:
            logger.info(f"[ROS] Evidence Strength: {len(references)} refs → weighted={weighted_count:.1f} → log={log_count:.2f} → score={strength:.2f}")
        
        return strength
    
    def _calculate_evidence_diversity(self, references: List[Dict[str, Any]]) -> float:
        """
        Evidence diversity (0-2.0)
        Multiple agent perspectives and evidence types
        """
        agents = set()
        types = set()
        
        for ref in references:
            if 'agentId' in ref:
                agents.add(ref['agentId'])
            if 'type' in ref:
                types.add(ref['type'])
        
        agent_diversity = min(len(agents) / EVIDENCE_DIVERSITY["agents_max"], 1.0) * EVIDENCE_DIVERSITY["agents_weight"]
        type_diversity = min(len(types) / EVIDENCE_DIVERSITY["types_max"], 1.0) * EVIDENCE_DIVERSITY["types_weight"]
        
        diversity = agent_diversity + type_diversity
        diversity = min(diversity, EVIDENCE_DIVERSITY["max_diversity"])
        
        if self.debug:
            logger.info(f"[ROS] Diversity: {len(agents)} agents + {len(types)} types → score={diversity:.2f}")
        
        return diversity
    
    def _calculate_recency_boost(self, references: List[Dict[str, Any]]) -> float:
        """
        IMPROVED: True recency signal
        
        OLD LOGIC: Only checked if date exists (mostly 0)
        NEW LOGIC: Publication year, trial status (recruiting > completed), recency windows
        
        Returns: 0-2.0
        """
        if not references:
            return 0.0
        
        now = datetime.utcnow()
        recency_score = 0.0
        recent_count = 0
        active_recruiting = 0
        
        for ref in references:
            try:
                # Check date
                if 'date' in ref:
                    ref_date = datetime.fromisoformat(ref['date'].replace('Z', '+00:00'))
                    days_old = (now - ref_date).days
                    
                    if days_old < RECENCY_BOOST["recent_threshold_days"]:
                        recent_count += 1
                        recency_score += RECENCY_BOOST["recent_multiplier"]
                    elif days_old < RECENCY_BOOST["moderate_threshold_days"]:
                        recency_score += RECENCY_BOOST["moderate_multiplier"]
                
                # Check trial status
                status = ref.get('status', '').lower()
                if 'recruiting' in status or 'active' in status:
                    active_recruiting += 1
                    recency_score += RECENCY_BOOST["recruiting_bonus"]
                elif 'completed' in status:
                    recency_score += RECENCY_BOOST["completed_bonus"]
                    
            except Exception as e:
                if self.debug:
                    logger.debug(f"[ROS] Could not parse date for ref: {e}")
        
        # Normalize by reference count
        recency_boost = (recency_score / len(references)) if references else 0.0
        recency_boost = min(recency_boost, RECENCY_BOOST["max_recency"])
        
        if self.debug:
            logger.info(f"[ROS] Recency: {recent_count} recent + {active_recruiting} recruiting → score={recency_boost:.2f}")
        
        return recency_boost
    
    def _calculate_novelty_factor(self, references: List[Dict[str, Any]], insights: List[Dict[str, Any]], akgp_stats: Optional[Dict]) -> float:
        """
        NEW COMPONENT: Novelty / Saturation Factor
        
        KEY INSIGHT: Novel, under-explored indications are HIGH-OPPORTUNITY research targets.
        Saturated areas (many trials, mature phase) are LOW-OPPORTUNITY.
        
        Scores:
        - Highly novel (<5 trials): 1.5
        - Novel (5-10 trials): 1.3
        - Emerging (10-30 trials): 1.0
        - Established (30-100 trials): 0.6
        - Saturated (>100 trials): 0.2
        
        ALSO considers: Phase distribution (Phase 2 only = more novel than Phase 4)
        
        Returns: 0-1.5
        """
        # Count ONLY clinical trials (not market reports, patents, literature)
        trial_count = len([r for r in references if r.get('type') in ['clinical_trial', 'clinical-trial']])
        
        if self.debug:
            logger.info(f"[ROS] Novelty: Counting clinical_trial type refs → found {trial_count} trials")
        
        # Base novelty by trial count (HEAVILY ADJUSTED FOR EXTREME DIFFERENTIATION)
        if trial_count < 5:
            base_novelty = 2.5  # INCREASED: Highly novel
        elif trial_count < 10:
            base_novelty = 2.2  # INCREASED: Novel
        elif trial_count < 30:
            base_novelty = 1.5  # INCREASED: Emerging
        elif trial_count < 100:
            base_novelty = 0.5  # DECREASED: Established
        else:
            base_novelty = 0.1  # HEAVILY DECREASED: Saturated
        
        # Phase distribution bonus (early phases = more novel)
        phase_bonus = 0.0
        phases = set()
        for ref in references:
            phase = ref.get('phase', 'Unknown')
            # Handle comma-separated phases from clinical trials API
            if isinstance(phase, str) and ',' in phase:
                phase_list = [p.strip() for p in phase.split(',')]
                for p in phase_list:
                    phases.add(p)
            elif phase and phase != 'Unknown':
                phases.add(phase)
        
        if self.debug:
            logger.info(f"[ROS] Novelty phases found: {phases}")
        
        # Check for Phase 1 (most novel)
        phase1_trials = [p for p in phases if 'Phase 1' in p or 'PHASE1' in p or p == 'Phase 1']
        if phase1_trials:
            phase_bonus = NOVELTY_FACTOR["phase_distribution_bonus"].get("phase1_only", 0.5) if len(phases) == 1 else NOVELTY_FACTOR["phase_distribution_bonus"].get("phase1_2", 0.3)
        # Check for Phase 2
        elif any('Phase 2' in p or 'PHASE2' in p or p == 'Phase 2' for p in phases):
            phase_bonus = NOVELTY_FACTOR["phase_distribution_bonus"].get("phase2_3", 0.2) if any('Phase 3' in p or 'PHASE3' in p or p == 'Phase 3' for p in phases) else NOVELTY_FACTOR["phase_distribution_bonus"].get("phase1_2", 0.3)
        # Check for Phase 3
        elif any('Phase 3' in p or 'PHASE3' in p or p == 'Phase 3' for p in phases):
            phase_bonus = NOVELTY_FACTOR["phase_distribution_bonus"].get("phase3_only", 0.1)
        # Check for Phase 4
        elif any('Phase 4' in p or 'PHASE4' in p or p == 'Phase 4' for p in phases):
            phase_bonus = NOVELTY_FACTOR["phase_distribution_bonus"].get("phase4_present", -0.1)
        
        # Combine
        novelty = base_novelty + (phase_bonus * 0.3)  # Phase bonus has smaller weight
        novelty = min(novelty, NOVELTY_FACTOR["max_novelty"])
        
        if DEBUG["show_novelty_details"]:
            logger.info(f"[ROS] Novelty: {trial_count} trials (base={base_novelty:.2f}) + phases {phases} (bonus={phase_bonus:.2f}) → score={novelty:.2f}")
        
        return novelty
    
    def _calculate_conflict_penalty(self, insights: List[Dict[str, Any]]) -> float:
        """
        Conflict penalty (-1.0 to 0)
        Evidence contradictions reduce ROS
        """
        if not insights:
            return 0.0
        
        # Count positive vs negative insights
        positive_count = 0
        negative_count = 0
        
        for insight in insights:
            text = str(insight).lower()
            
            has_positive = any(kw in text for kw in CONFLICT_PENALTY["positive_keywords"])
            has_negative = any(kw in text for kw in CONFLICT_PENALTY["negative_keywords"])
            
            if has_positive:
                positive_count += 1
            if has_negative:
                negative_count += 1
        
        # Calculate conflict
        if positive_count == 0 or negative_count == 0:
            return 0.0  # No conflict
        
        conflict_ratio = negative_count / (positive_count + negative_count)
        
        if conflict_ratio < CONFLICT_PENALTY["min_conflict_threshold"]:
            return 0.0
        
        penalty = -(conflict_ratio * abs(CONFLICT_PENALTY["max_penalty"]))
        
        if self.debug:
            logger.info(f"[ROS] Conflict: +{positive_count} / -{negative_count} → penalty={penalty:.2f}")
        
        return penalty
    
    def _calculate_patent_risk(self, references: List[Dict[str, Any]]) -> float:
        """
        Patent risk penalty (-1.5 to 0)
        High patent density = limited opportunity (IP/FTO risk)
        """
        if not references:
            return 0.0
        
        patent_refs = [r for r in references if r.get('type') == 'patent']
        patent_ratio = len(patent_refs) / len(references)
        
        if patent_ratio > PATENT_RISK["high_patent_ratio"]:
            penalty = PATENT_RISK["high_patent_penalty"]
        elif patent_ratio > PATENT_RISK["medium_patent_ratio"]:
            penalty = PATENT_RISK["medium_patent_penalty"]
        elif patent_ratio > PATENT_RISK["low_patent_ratio"]:
            penalty = PATENT_RISK["low_patent_penalty"]
        else:
            penalty = PATENT_RISK["no_patent_penalty"]
        
        if self.debug:
            logger.info(f"[ROS] Patent Risk: {len(patent_refs)}/{len(references)} = {patent_ratio:.1%} → penalty={penalty:.2f}")
        
        return penalty
    
    def _strip_markdown(self, text: str) -> str:
        """Strip markdown formatting from text"""
        import re
        # Remove bold/italic markers
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **text** -> text
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # *text* -> text
        text = re.sub(r'__(.+?)__', r'\1', text)       # __text__ -> text
        text = re.sub(r'_(.+?)_', r'\1', text)         # _text_ -> text
        # Remove heading markers
        text = re.sub(r'^#+\s', '', text, flags=re.MULTILINE)  # # Heading -> Heading
        # Remove numbered/bullet lists markers and indentation
        text = re.sub(r'^\s*\d+\.\s', '', text, flags=re.MULTILINE)  # 1. text -> text
        text = re.sub(r'^\s*[-*]\s', '', text, flags=re.MULTILINE)   # - text -> text
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines -> 2 newlines
        return text.strip()
    
    def _get_confidence_level(self, ros_score: float) -> str:
        """Map ROS score to confidence level"""
        if ros_score >= 8.0:
            return "EXCEPTIONAL"
        elif ros_score >= 6.0:
            return "STRONG"
        elif ros_score >= 4.0:
            return "MODERATE"
        elif ros_score >= 2.0:
            return "WEAK"
        else:
            return "POOR"
    
    def _generate_explanation(self, ros_score: float, novelty: float, conflict: float, ref_count: int) -> str:
        """Generate human-readable ROS explanation"""
        
        confidence = self._get_confidence_level(ros_score)
        
        if ros_score >= 8.0:
            base = f"{confidence}: Exceptional research opportunity with novel indication and strong evidence."
        elif ros_score >= 6.0:
            base = f"{confidence}: Strong research opportunity with good evidence and moderate novelty."
        elif ros_score >= 4.0:
            base = f"{confidence}: Moderate research opportunity with mixed evidence."
        elif ros_score >= 2.0:
            base = f"{confidence}: Weak research opportunity with limited evidence or high saturation."
        else:
            base = f"{confidence}: Poor research opportunity with insufficient evidence."
        
        # Add novelty commentary
        if novelty > 1.2:
            base += " This is a highly novel indication with limited existing research - excellent opportunity."
        elif novelty > 1.0:
            base += " This indication shows emerging research interest."
        elif novelty < 0.4:
            base += " However, this is a mature, well-established area with many existing trials."
        
        # Add conflict commentary
        if conflict < -0.5:
            base += " Significant conflicting evidence was identified - caution advised."
        elif conflict < 0:
            base += " Some conflicting evidence exists."
        
        base += f" Analysis based on {ref_count} evidence sources across multiple types."
        
        return base
    
    def calculate_ros_with_gemini(
        self,
        query: str,
        references: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
        akgp_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate ROS score using Gemini's own knowledge (no evidence data passed).
        
        Extracts drug and disease from query, then asks Gemini to evaluate based on:
        - Mechanism of action of the drug
        - Pathophysiology of the disease
        - Known efficacy and risks
        - Market saturation from training data
        
        Returns both Gemini's score and reasoning.
        """
        if not GOOGLE_API_KEY:
            logger.warning("[ROS] GOOGLE_API_KEY not set, falling back to deterministic scoring")
            return self.calculate_ros(query, references, insights, akgp_stats)
        
        try:
            # Extract drug and disease
            drug_name, disease_name = self._extract_drug_disease(query)
            
            # Build brutally honest prompt using only Gemini's own knowledge
            system_prompt = """You are a brutally honest pharmaceutical research analyst with deep expertise in pharmacology, pathophysiology, and drug mechanisms.

Your job is to evaluate research opportunities using YOUR OWN KNOWLEDGE:
- Does the drug's mechanism of action actually address the disease?
- Is there ANY scientific basis for this combination?
- What does your knowledge tell you about efficacy potential?
- What is the current market saturation for this indication?
- Are there approved competitors already?

SCORING GUIDE (BE BRUTALLY HONEST):
- 9-10: Exceptional opportunity (rare). Novel, scientifically sound, clear unmet need.
- 7-8: Good opportunity. Mechanism makes sense, some market gap, feasible.
- 5-6: Moderate opportunity. Some scientific basis, but limited novelty or questionable mechanism.
- 3-4: Weak opportunity. Questionable mechanism OR saturated market.
- 0-2: Poor opportunity. NO scientific basis OR clearly wrong mechanism/indication combo.

CRITICAL: If the drug-disease combination doesn't make sense pharmacologically, give it a LOW score.
Don't be influenced by trial volume - score based on SCIENTIFIC MERIT first."""

            user_prompt = f"""Using YOUR KNOWLEDGE, evaluate this research opportunity:

DRUG: {drug_name}
DISEASE: {disease_name}
QUERY: {query}

Based on what you know about:
1. {drug_name}'s mechanism of action
2. {disease_name}'s pathophysiology
3. Existing treatments and market saturation
4. Scientific plausibility of this drug-disease combination

PROVIDE:
1. Does this drug-disease combination make pharmacological sense? Why or why not?
2. What is the mechanism of action and does it address the disease?
3. Are there existing approved treatments? How saturated is the market?
4. What are the major scientific limitations?
5. Your HONEST research opportunity score (0-10).

Be direct and harsh. If it doesn't make sense, say so."""

            # Call Gemini
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,  # Lower temp for more focused/honest assessment
                    max_output_tokens=1500,
                )
            )
            
            gemini_response = response.text
            
            # Strip markdown formatting
            clean_assessment = self._strip_markdown(gemini_response)
            
            # Extract score from response
            gemini_score = self._extract_score_from_gemini(gemini_response)
            
            # Calculate evidence counts
            supporting_count = len([r for r in references if r.get('relevance', 0) > 0.6])
            contradicting_count = len([r for r in references if r.get('relevance', 0) < 0.3])
            
            # Get unique agents
            agents = set()
            for ref in references:
                if 'agentId' in ref:
                    agents.add(ref['agentId'])
            agent_count = len(agents)
            
            if self.debug:
                logger.info(f"[ROS-GEMINI] Gemini score: {gemini_score:.1f}")
                logger.info(f"[ROS-GEMINI] Supporting: {supporting_count}, Contradicting: {contradicting_count}, Agents: {agent_count}")
                logger.info(f"[ROS-GEMINI] Gemini assessment:\n{clean_assessment[:500]}...")
            
            return {
                "ros_score": gemini_score,
                "calculation_method": "gemini_honest",
                "confidence_level": self._get_confidence_level(gemini_score),
                "gemini_assessment": clean_assessment,
                "metadata": {
                    "drug_name": drug_name,
                    "disease_name": disease_name,
                    "num_supporting_evidence": supporting_count,
                    "num_contradicting_evidence": contradicting_count,
                    "distinct_agents": list(agents),
                    "num_references": len(references),
                    "num_insights": len(insights),
                    "computation_timestamp": datetime.utcnow().isoformat(),
                    "method": "Direct Gemini evaluation (brutally honest)",
                }
            }
            
        except Exception as e:
            logger.error(f"[ROS-GEMINI] Error calling Gemini: {e}", exc_info=True)
            # Fallback to deterministic scoring
            logger.info("[ROS] Falling back to deterministic scoring")
            result = self.calculate_ros(query, references, insights, akgp_stats)
            result["calculation_method"] = "fallback_deterministic"
            return result
    
    def _prepare_evidence_summary(self, references: List[Dict[str, Any]], insights: List[Dict[str, Any]]) -> str:
        """Prepare a human-readable evidence summary for Gemini"""
        
        # Count by type
        trial_count = len([r for r in references if r.get('type') in ['clinical_trial', 'clinical-trial']])
        literature_count = len([r for r in references if r.get('type') == 'literature'])
        patent_count = len([r for r in references if r.get('type') == 'patent'])
        market_count = len([r for r in references if r.get('type') == 'market'])
        
        # Get relevance distribution
        high_relevance = len([r for r in references if r.get('relevance', 0) > 0.7])
        medium_relevance = len([r for r in references if 0.4 <= r.get('relevance', 0) <= 0.7])
        low_relevance = len([r for r in references if r.get('relevance', 0) < 0.4])
        
        # Phases
        phases = set()
        for ref in references:
            phase = ref.get('phase', '')
            if phase:
                phases.add(phase)
        
        # Trial statuses
        statuses = set()
        for ref in references:
            status = ref.get('status', '')
            if status:
                statuses.add(status.strip())
        
        # Get top insights
        top_insights = insights[:3] if insights else []
        
        summary = f"""Total Evidence: {len(references)} references
- Clinical Trials: {trial_count}
- Literature: {literature_count}
- Patents: {patent_count}
- Market Data: {market_count}

Evidence Quality:
- High Relevance: {high_relevance}
- Medium Relevance: {medium_relevance}
- Low Relevance: {low_relevance}

Trial Phases Present: {', '.join(sorted(phases)) if phases else 'Unknown'}

Trial Statuses: {', '.join(sorted(statuses)) if statuses else 'Unknown'}

Key Insights from Research:
"""
        for i, insight in enumerate(top_insights, 1):
            text = insight.get('text', str(insight))[:200]
            summary += f"{i}. {text}\n"
        
        return summary
    
    def _extract_score_from_gemini(self, response: str) -> float:
        """Extract numeric ROS score from Gemini response"""
        import re
        
        # Look for patterns like "score: 7.5" or "ROS: 8" or just "8/10"
        patterns = [
            r'(?:score|ros)\s*[:\s=]+\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(?:/10|out of 10)',
            r'research opportunity score.*?(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    # Clamp to 0-10
                    return max(0.0, min(10.0, score))
                except (ValueError, IndexError):
                    continue
        
        # If no pattern matched, try to extract any number between 0-10
        numbers = re.findall(r'\b([0-9]\.[0-9]|[0-9])\b', response)
        for num_str in numbers:
            try:
                num = float(num_str)
                if 0 <= num <= 10:
                    return num
            except ValueError:
                continue
        
        # Default to 5.0 if we can't extract
        logger.warning("[ROS-GEMINI] Could not extract score from Gemini response, defaulting to 5.0")
        return 5.0


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


def calculate_ros_with_gemini(
    query: str,
    references: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    akgp_stats: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate ROS score using Gemini's brutally honest evaluation"""
    return _ros_scorer.calculate_ros_with_gemini(query, references, insights, akgp_stats)
