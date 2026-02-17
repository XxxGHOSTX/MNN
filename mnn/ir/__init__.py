"""
Intermediate Representation (IR) Module

Provides typed models for SMT-based constraint validation and candidate generation.

Author: MNN Engine Contributors
"""

from .models import ConstraintSchema, Candidate, BreachCoordinates

__all__ = ["ConstraintSchema", "Candidate", "BreachCoordinates"]
