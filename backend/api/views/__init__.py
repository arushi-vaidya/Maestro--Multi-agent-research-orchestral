"""
API Views - Frontend-Safe Façade Layer

This package provides a thin presentation layer for the frontend.
Views expose already-computed data in a clean, stable format.

CRITICAL CONSTRAINTS:
- Views are READ-ONLY
- Views do NOT trigger agent execution
- Views do NOT modify AKGP graph
- Views do NOT recompute ROS scores
- Views ONLY expose already-produced results

Architecture:
- Each view corresponds to a frontend page/component
- All views use Pydantic models for type safety
- All views access shared QueryResultCache for last query results
"""

from .cache import QueryResultCache

__all__ = ['QueryResultCache']
