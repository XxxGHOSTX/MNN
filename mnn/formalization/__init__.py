"""
Formalization Module

Converts queries into Constraint Compilation Schemas (CCS).

Author: MNN Engine Contributors
"""

from .ccs import formalize_query, derive_constraints

__all__ = ["formalize_query", "derive_constraints"]
