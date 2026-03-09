## Change summary

<!-- Describe what this PR changes and why. One paragraph minimum. -->

## Rationale

<!-- Explain why this change is necessary. Link to the relevant GitHub Issue if applicable. -->

Closes #<!-- issue number -->

## Commands run locally

<!-- List every command you ran to validate this change. Do not leave blank. -->

```bash
# Example — replace with actual commands run:
pip install -r requirements.txt
make lint
make test
python tools/no_placeholders.py
bash tools/run_ci.sh
```

## Checklist

All items must be checked before requesting review. Unchecked items block merge.

### Code quality
- [ ] `make lint` passes with zero errors
- [ ] `make test` passes — all tests green, no skips added without justification
- [ ] `python tools/no_placeholders.py` passes — **zero** matches for TODO / FIXME / STUB / MOCK / PLACEHOLDER / TBD / HACK / XXX
- [ ] No dead code, commented-out blocks, or incomplete implementations merged
- [ ] All public functions/classes carry Python type annotations

### Determinism
- [ ] Any new randomness uses a named, logged seed registered via `mnn/core/seed_registry.py`
- [ ] New stochastic components have at least one determinism test (same seed → identical output)
- [ ] No unseeded `random` or `numpy.random` calls introduced

### Security
- [ ] No secrets, credentials, or tokens committed
- [ ] New endpoints are authenticated via `auth_utils.py` (or explicitly justified as public)
- [ ] Input validation added for all new API parameters
- [ ] Dependencies added to `requirements.txt` and audited with `pip-audit`

### Documentation
- [ ] `README.md` or relevant docs updated if behaviour or setup changed
- [ ] New modules documented in `.github/copilot-instructions.md` layout section

### Allowlist (fill in only if applicable)
- [ ] Any new `tools/no_placeholders_allowlist.json` entries include a mandatory justification
