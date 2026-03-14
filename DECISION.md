# DECISIONS

This document explains the technical decisions made when resolving the CodeQL
CI failures and hardening the codebase.

---

## 1  CodeQL workflow: upgrade to "CodeQL Advanced" with `codeql-action@v4`

**Decision**: Replace the previous `CodeQL` workflow with the "CodeQL Advanced"
configuration provided by the repository owner.  Key changes:

- **Renamed** to `"CodeQL Advanced"` to align with GitHub's recommended template.
- **Actions upgraded** from v3 (Node.js 20) to v4 (Node.js 24).
- **Matrix restructured** to use `include:` with explicit `build-mode` per language,
  covering `actions`, `c-cpp`, `javascript-typescript`, and `python`.
- **Scheduled run** added (`cron: '17 21 * * 0'`) for weekly background scans.
- **Language identifiers updated** to current CodeQL names: `c-cpp` (was `cpp`),
  `javascript-typescript` (was `javascript`).
- **Setup steps added** per-language: `actions/setup-node@v4` (Node 22),
  `actions/setup-python@v5` (Python 3.11), build-essential for C/C++, pip and
  npm dependency installation.
- **`category` parameter added** to `analyze` step to correctly namespace SARIF
  results per language in the GitHub Security tab.
- **`upload: failure-only` removed** – the default (`always`) is restored now
  that the repository owner has disabled the built-in "Default setup" in
  repository settings, which was causing the previous SARIF rejection.

**Reason**: The v3 actions run on deprecated Node.js 20.  The new matrix format
is more readable, and the added setup steps ensure dependencies are available
during extraction.  The `category` parameter is required for multi-language
advanced setups to correctly deduplicate findings per language in the
Security tab.

---

## 4  Fix stack-trace exposure in `mnn/api.py`

**Decision**: Replace `detail=f"... {str(e)}"` with a generic user-facing
message and log the full exception internally via `logger.error(..., exc_info=True)`.

**Reason**: Returning raw exception text to API clients leaks implementation
details and can expose file paths, internal class names, or sensitive
configuration values (CWE-209, CodeQL rule `py/stack-trace-exposure`).  The
full exception is still captured in server logs for operator diagnosis.

---

## 5  Add `bleach` to `requirements.txt`

**Decision**: Pin `bleach==6.1.0` as a production dependency.

**Reason**: The CodeQL rule `py/bad-tag-filter` flags regex-based HTML
sanitisation as unreliable.  `bleach.clean()` provides a standards-compliant,
allowlist-driven HTML sanitiser.  Any future code that needs to strip or
escape user-supplied HTML **must** use `bleach.clean()` instead of custom
regular expressions.

---

## 6  Secure cookie guidance

**Decision**: No code change required today (no `set_cookie` calls exist in
the codebase).  A note is added to ASSUMPTIONS.md and this file.

**Guidance**: When cookies are introduced, always set:
```python
response.set_cookie(
    key="session",
    value=value,
    secure=True,
    httponly=True,
    samesite="Lax",
)
```

---

## 7  Weak cryptography guidance

**Decision**: No code change required today.  `hashlib.sha256` (the only hash
used for security purposes) is not weak.  The `sha1` / `md5` rules in the
codebase are applied to non-sensitive embedding seeds, which is outside the
scope of `py/weak-sensitive-data-hashing`.

**Guidance**: If passwords or secrets ever need to be hashed, use
`passlib[bcrypt]` or `argon2-cffi`, both of which are listed (commented out)
in `requirements.txt`.
