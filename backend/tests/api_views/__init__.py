"""
API Façade Views Tests

Tests for STEP 7.6 API Façade Layer

Test Coverage:
- Schema validation (responses match Pydantic models)
- Idempotency (multiple calls return same data)
- Read-only behavior (no agents triggered, no graph modifications)
- Regression (existing functionality unchanged)
"""
