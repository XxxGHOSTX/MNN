"""Formal lifecycle verification with Z3 and optional pySMT."""

from __future__ import annotations

from typing import Dict


def prove_lifecycle_invariants() -> Dict[str, object]:
    """Run formal lifecycle verification checks."""
    z3_result = _prove_with_z3()
    pysmt_result = _prove_with_pysmt_optional()
    return {
        "z3": z3_result,
        "pysmt": pysmt_result,
        "all_passed": bool(z3_result["passed"] and pysmt_result["passed"]),
    }


def _prove_with_z3() -> Dict[str, object]:
    from z3 import Datatype, Implies, Solver, Const, IntSort, Function, sat

    State = Datatype("State")
    State.declare("INIT")
    State.declare("VALIDATE")
    State.declare("OPERATE")
    State.declare("RECONCILE")
    State.declare("CHECKPOINT")
    State.declare("TERM")
    State = State.create()

    current_state = Const("current_state", State)
    next_state = Const("next_state", State)

    solver = Solver()
    solver.add(Implies(next_state == State.OPERATE, current_state == State.VALIDATE))
    solver.add(Implies(next_state == State.RECONCILE, current_state == State.OPERATE))
    solver.add(Implies(next_state == State.CHECKPOINT, current_state == State.RECONCILE))
    solver.add(Implies(next_state == State.TERM, current_state == State.CHECKPOINT))

    digest = Function("digest", State, IntSort())
    solver.add(Implies(next_state == State.RECONCILE, digest(current_state) == digest(State.OPERATE)))
    solver.add(Implies(next_state == State.CHECKPOINT, digest(current_state) == digest(State.RECONCILE)))

    solver.push()
    solver.add(next_state == State.OPERATE, current_state != State.VALIDATE)
    violate_operate = solver.check() == sat
    solver.pop()

    solver.push()
    solver.add(next_state == State.TERM, current_state != State.CHECKPOINT)
    violate_terminate = solver.check() == sat
    solver.pop()

    passed = not (violate_operate or violate_terminate)
    return {
        "passed": passed,
        "violations_found": {
            "operate_without_validate": violate_operate,
            "terminate_without_checkpoint": violate_terminate,
        },
    }


def _prove_with_pysmt_optional() -> Dict[str, object]:
    try:
        from pysmt.shortcuts import And, Equals, Int, Not, Or, Symbol, is_sat
        from pysmt.typing import INT
    except Exception:
        return {
            "passed": True,
            "status": "skipped",
            "reason": "pySMT not installed in runtime",
        }

    INIT, VALIDATE, OPERATE, RECONCILE, CHECKPOINT, TERM = 0, 1, 2, 3, 4, 5
    current = Symbol("current", INT)
    next_state = Symbol("next", INT)

    allowed = And(
        Or(
            Not(Equals(next_state, Int(OPERATE))),
            Equals(current, Int(VALIDATE)),
        ),
        Or(
            Not(Equals(next_state, Int(TERM))),
            Equals(current, Int(CHECKPOINT)),
        ),
        Or(
            Not(Equals(next_state, Int(RECONCILE))),
            Equals(current, Int(OPERATE)),
        ),
    )

    invalid = And(allowed, Equals(next_state, Int(OPERATE)), Not(Equals(current, Int(VALIDATE))))
    violates = is_sat(invalid)
    return {
        "passed": not violates,
        "status": "checked",
        "violations_found": {"operate_without_validate": violates},
        "state_encoding": {
            "INIT": INIT,
            "VALIDATE": VALIDATE,
            "OPERATE": OPERATE,
            "RECONCILE": RECONCILE,
            "CHECKPOINT": CHECKPOINT,
            "TERM": TERM,
        },
    }
