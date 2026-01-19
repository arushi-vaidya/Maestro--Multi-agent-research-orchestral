"""
Research Opportunity Scoring (ROS) - Phase 6A

Deterministic, explainable, heuristic scoring system for drug-disease pairs.

This module provides:
- Deterministic scoring based on AKGP evidence
- Conflict-aware scoring with penalties
- Temporal recency weighting
- Fully explainable feature breakdown
- Journal-defensible methodology

Design Philosophy:
- Uses ONLY AKGP query outputs (no raw agent data)
- 100% deterministic (no ML, no randomness)
- Explainable (every score component justified)
- Monotonic (more evidence → higher score, more conflicts → lower score)

Phase 6A vs 6B:
- Phase 6A (THIS): Heuristic ROS with explicit rules
- Phase 6B (FUTURE): ML-enhanced ROS (not implemented)
"""

from ros.ros_engine import ROSEngine, compute_ros

__all__ = ['ROSEngine', 'compute_ros']

__version__ = '1.0.0-phase6a'
