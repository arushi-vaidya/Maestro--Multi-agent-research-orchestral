"""
ROS (Research Opportunity Score) Configuration
Centralized tunable parameters for ROS computation

All weights and thresholds can be adjusted here WITHOUT code changes.
"""

# ============================================================================
# ROS COMPONENT WEIGHTS
# ============================================================================
# These control the contribution of each factor to the final ROS score
# Increasing a weight makes that component MORE important

WEIGHTS = {
    "evidence_strength": 0.4,      # Base evidence volume and quality (HEAVILY reduced for differentiation)
    "evidence_diversity": 0.4,      # Multiple agent perspectives (reduced)
    "recency_boost": 1.5,           # Recent evidence weight (INCREASED - key differentiator)
    "novelty_score": 3.0,           # Novel/under-explored indications (HEAVILY INCREASED - PRIMARY differentiator)
    "conflict_penalty": 1.0,        # Evidence contradictions (multiply by negative penalty)
    "patent_risk": 0.8,             # Patent saturation (multiply by negative penalty)
}

# ============================================================================
# EVIDENCE STRENGTH PARAMETERS
# ============================================================================
# Controls how evidence quantity maps to strength score

EVIDENCE_STRENGTH = {
    # Log-scaling for evidence count (diminishing returns)
    # strength = log(1 + weighted_count) * scale_factor
    "log_base": 1.0,  # Natural log
    "scale_factor": 2.5,  # Multiply log result
    
    # Quality weights by evidence type
    "quality_weights": {
        "clinical_trial": 1.0,      # Phase 3/4 trials = highest
        "literature": 0.8,          # Published research
        "mechanistic": 0.7,         # Mechanism studies
        "market": 0.6,              # Market data
        "patent": 0.5,              # Patent landscape
    },
    
    # Maximum evidence strength score
    "max_strength": 4.0,
}

# ============================================================================
# EVIDENCE DIVERSITY PARAMETERS
# ============================================================================

EVIDENCE_DIVERSITY = {
    # Agent diversity scoring
    "agents_max": 4,  # At 4+ agents, max diversity score
    "agents_weight": 1.0,
    
    # Type diversity scoring
    "types_max": 4,  # At 4+ types, max diversity score
    "types_weight": 1.0,
    
    # Maximum diversity score
    "max_diversity": 2.0,
}

# ============================================================================
# RECENCY BOOST PARAMETERS
# ============================================================================
# Based on publication year, trial dates, recruitment status

RECENCY_BOOST = {
    # Thresholds for recency classification (ADJUSTED FOR HIGHER IMPACT)
    "recent_threshold_days": 365,      # Last 1 year = "recent"
    "moderate_threshold_days": 1825,   # Last 5 years = "moderate"
    "old_threshold_days": 2920,        # Older than 8 years = "old"
    
    # Points by recency class (INCREASED)
    "recent_multiplier": 1.5,          # INCREASED: Recruiting trials in last year
    "moderate_multiplier": 0.8,        # INCREASED: Completed in last 5 years
    "old_multiplier": 0.0,             # Older trials
    
    # Trial status bonuses (INCREASED)
    "recruiting_bonus": 1.0,           # INCREASED: Currently recruiting
    "active_bonus": 0.5,               # INCREASED: Active but not recruiting
    "completed_bonus": 0.2,            # INCREASED from 0: Completed
    
    # Maximum recency boost
    "max_recency": 3.5,                # INCREASED from 2.0
}

# ============================================================================
# NOVELTY / SATURATION FACTOR (NEW)
# ============================================================================
# Identifies under-explored indications vs. crowded research areas
# HIGH novelty = research opportunity
# LOW novelty = mature, saturated area

NOVELTY_FACTOR = {
    # Trial count thresholds (ADJUSTED FOR HIGHER SPREAD)
    "saturated_threshold": 100,        # >100 trials = saturated
    "established_threshold": 30,       # 30-100 trials = established
    "emerging_threshold": 10,          # 10-30 trials = emerging
    "novel_threshold": 5,              # 5-10 trials = novel
    # <5 trials = highly novel
    
    # Phase distribution scoring
    # Lower phases = more novel/risky = HIGHER opportunity
    "phase_novelty_scores": {
        "Phase 1": 2.8,    # HEAVILY INCREASED: Very early, very novel
        "Phase 2": 2.3,    # HEAVILY INCREASED: Early, novel
        "Phase 3": 0.6,    # DECREASED: Late, established
        "Phase 4": 0.1,    # DECREASED: Commercial, saturated
        "Unknown": 1.5,    # INCREASED: Uncertain = moderate novelty
    },
    
    # Trial count bonuses by phase distribution
    "phase_distribution_bonus": {
        "phase1_only": 1.0,      # Only Phase 1 = very novel
        "phase1_2": 0.9,         # Phase 1-2 = novel
        "phase2_3": 0.5,         # Phase 2-3 = moderate
        "phase3_only": 0.2,      # Only Phase 3 = established
        "phase4_present": 0.0,   # Phase 4 present = commercialized
    },
    
    # Disease/indication maturity
    # Rare diseases = higher novelty
    # Common diseases = lower novelty
    "rare_disease_bonus": 0.5,         # Rare disease multiplier
    
    # Maximum novelty score
    "max_novelty": 3.0,                # HEAVILY INCREASED from 2.0 for higher ceiling
}

# ============================================================================
# CONFLICT PENALTY PARAMETERS
# ============================================================================

CONFLICT_PENALTY = {
    # Minimum threshold for detecting conflict
    "min_conflict_threshold": 0.3,     # Minimum ratio to trigger penalty
    
    # Penalty scaling
    "max_penalty": -1.0,               # Worst case penalty
    
    # Conflict detection keywords
    "negative_keywords": [
        "negative", "weak", "failed", "ineffective", 
        "adverse", "toxicity", "harmful", "contradicts"
    ],
    "positive_keywords": [
        "positive", "strong", "effective", "supports",
        "beneficial", "safe", "confirms", "supports"
    ],
}

# ============================================================================
# PATENT RISK PARAMETERS
# ============================================================================
# High patent density = limited opportunity (IP/freedom-to-operate risk)

PATENT_RISK = {
    # Patent density thresholds
    "high_patent_ratio": 0.5,          # >50% patents
    "medium_patent_ratio": 0.3,        # 30-50%
    "low_patent_ratio": 0.1,           # 10-30%
    
    # Penalties by density
    "high_patent_penalty": -1.5,
    "medium_patent_penalty": -1.0,
    "low_patent_penalty": -0.5,
    "no_patent_penalty": 0.0,
}

# ============================================================================
# ROS SCORE RANGES (INFORMATIONAL)
# ============================================================================
# These describe the expected ROS ranges after fixes
# NOT hard-coded, just guidelines for tuning

ROS_RANGES = {
    "exceptional": (8.0, 10.0),  # High-impact opportunity
    "strong": (6.0, 8.0),        # Good opportunity
    "moderate": (4.0, 6.0),      # Medium opportunity
    "weak": (2.0, 4.0),          # Low opportunity
    "poor": (0.0, 2.0),          # Very low opportunity
}

# ============================================================================
# CLAMPING AND NORMALIZATION
# ============================================================================

CLAMPING = {
    "min_ros": 0.0,   # Minimum ROS score
    "max_ros": 10.0,  # Maximum ROS score
}

# ============================================================================
# DEBUG FLAGS
# ============================================================================

DEBUG = {
    "verbose_logging": True,           # Log all component calculations
    "export_breakdown": True,          # Export component breakdown
    "show_novelty_details": True,      # Show novelty factor calculation
}
