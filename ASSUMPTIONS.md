# ASSUMPTIONS

This document records the assumptions made when automating resolution of the
CodeQL CI job failures described in the problem statement.

## Repository Structure

- The primary language analysed by CodeQL is **Python**.  C++ (`src/mnn_core.cpp`,
  `src/deterministic_state.cpp`) and JavaScript/TypeScript (React frontend in
  `frontend/`) are also present and are retained in the matrix so that
  security findings in those languages are not silently dropped.
- There are no Flask or Django route handlers that call `response.set_cookie()`,
  so no insecure-cookie fix is required beyond the preventative note in
  DECISION.md.
- There are no calls to `eval()`, `exec()`, or user-input-driven XPath queries
  in the production Python codebase.  The CodeQL queries for those rules are
  therefore expected to return zero findings after the stack-trace fix.
- `md5` / `sha1` are not used for any sensitive data (passwords, tokens).
  Hashing with those algorithms in non-security contexts (e.g. deterministic
  character embedding seeds) is outside the scope of the `py/weak-sensitive-data-hashing`
  rule; those usages are therefore not changed.
- The **default Code Scanning setup** in GitHub repository settings must be
  **disabled** before the advanced (workflow-based) setup will be accepted.
  Enabling both simultaneously causes the SARIF upload to be rejected with:
  `"CodeQL analyses from advanced configurations cannot be processed when the
  default setup is enabled."`.  This repository settings change cannot be
  automated via a code commit; see DECISION.md for the recommended action.

## Dependencies Omitted

- `passlib[bcrypt]` / `argon2-cffi` are commented out in `requirements.txt`
  because no password-hashing code exists in the current codebase.  They
  should be uncommented when a password store is introduced.
- `python-multipart` and `python-jose` remain commented out for the same
  reason (no file-upload or JWT routes in the current codebase).
