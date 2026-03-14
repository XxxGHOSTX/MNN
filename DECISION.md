# DECISIONS

This document explains the technical decisions made when resolving the CodeQL
CI failures and hardening the codebase.

---

## 1  CodeQL workflow: upgrade to `codeql-action@v4`

**Decision**: Replace `github/codeql-action/{init,autobuild,analyze}@v3` with
`@v4`.

**Reason**: The v3 actions run on Node.js 20, which GitHub Actions is
deprecating (forced migration to Node.js 24 begins 2026-06-02).  Upgrading to
v4 removes the deprecation warning and ensures continued support.

---

## 2  Add a "Clean up stale CodeQL artifacts" step

**Decision**: Add `rm -rf /home/runner/work/_temp/codeql_databases || true` as
the first workflow step.

**Reason**: The CI logs showed:
> "Improved incremental analysis was skipped because it previously failed for
> this repository with CodeQL version 2.24.3 on a runner with similar hardware
> resources.  One possible reason for this is that improved incremental
> analysis can require a significant amount of disk space."

Removing the stale database directory before each run prevents accumulation of
previous artifacts and gives the incremental-analysis step a fresh start.

---

## 3  Use `upload: failure-only` on the `analyze` step

**Decision**: Set `upload: failure-only` on `codeql-action/analyze`.

**Reason**: The primary SARIF upload failure was:
> "CodeQL analyses from advanced configurations cannot be processed when the
> default setup is enabled."

This error occurs when the repository's built-in "default setup" (Settings →
Code security → Code scanning → Default setup) is active **at the same time**
as the workflow-based advanced setup.

`upload: failure-only` prevents a hard failure while the repository owner
evaluates / turns off the default setup.  Once default setup is disabled, the
value can be changed back to the default (`always`) to restore full SARIF
reporting.

**Required manual action**: Disable "Default setup" in repository settings
(Settings → Code security and analysis → Code scanning → Default setup → Off).

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
