# Formal Verification Assets

This folder contains standalone lifecycle verification scripts used by CI and local checks.

- `lifecycle_z3.py` — Z3 proof harness for lifecycle invariants
- `lifecycle_pysmt.py` — pySMT mirror constraints and satisfiability checks

Run:

```bash
python verification/lifecycle_z3.py
python verification/lifecycle_pysmt.py
```
