# AUTH.md: authentication, authorisation, sessions

**Decision:** server-side sessions stored in Postgres, opaque random cookie, HTTP-only. Not JWT-in-localStorage (XSS exposure, hard revocation). Passwords hashed with **argon2id**.

---

## 1. Threat summary (STRIDE, condensed)

| Threat | Example | Control |
|---|---|---|
| Spoofing | Stolen or guessed password | argon2id, login throttling, lockout, optional TOTP MFA, session rotation on login |
| Tampering | Edit approved template, audit rows | Immutable versions, trigger, hash-chained audit, app role without UPDATE/DELETE on audit |
| Repudiation | "I never generated that" | Audit with actor, template version, input hash |
| Information disclosure | **IDOR** (change a document id in the URL) | Tenant-scoped queries + `authorize()` on every resource; cross-tenant returns `404`; RLS later; signed short-lived download URLs |
| Denial of service | Login floods, huge uploads | Token-bucket rate limits, upload limits, bounded queue |
| Elevation | Drafter approves a template | Backend RBAC + lifecycle FSM guards; tested 403 matrix |

## 2. Passwords
- argon2id with parameters tuned to about 250 ms on the server (record them in config; re-tune yearly). Library: `argon2-cffi`.
- Minimum 12 characters, no composition rules, check against a common-password list; no forced periodic rotation.
- First login with a temporary password forces a change. Reset tokens: 32 random bytes, stored hashed, expire in 30 minutes, single use, invalidate all sessions on use.
- Password reset responses never reveal whether an email exists (`202` always).

## 3. Sessions
| Item | Value |
|---|---|
| Cookie | `lekhan_session`; `HttpOnly; Secure; SameSite=Lax; Path=/` (+ `__Host-` prefix in production) |
| Value | 32 random bytes, base64url; **only SHA-256 stored** in `sessions.id_hash` |
| Idle timeout | 30 minutes (sliding); absolute 12 hours |
| Rotation | New session id on login, MFA completion, password change, role change |
| Revocation | Delete row; "log out everywhere" removes all rows for the user |
| Fixation | Never accept a client-supplied id |

## 4. CSRF
Cookie sessions require CSRF defence. `GET /auth/me` returns a per-session CSRF token; the frontend sends it as `X-CSRF-Token` on every non-GET request; the backend compares in constant time against `csrf_token_hash`. Also verify `Origin`/`Host` for state-changing requests. CORS: only the app origin, credentials allowed, no wildcards.

## 5. Login throttling and lockout
- Token bucket: 5 attempts per 15 minutes per (account, IP) and 20 per hour per IP.
- After 10 consecutive failures lock the account for 15 minutes (`423`); every failure adds an audit event and a small constant delay to blunt timing differences.
- Never say which of email or password was wrong.

## 6. MFA (TOTP) (Phase 4)
Enrol with a QR code; store the secret **encrypted** (`mfa_secret_enc`); accept codes in a +-1 step window; one-time recovery codes (hashed); admin can reset MFA with an audit event. Required for admin and reviewer roles at launch if time allows.

## 7. Roles and permissions

| Role | Can |
|---|---|
| `admin` | Manage users and settings; view audit; view all documents; delete (non-finalised) documents |
| `template_admin` | Create templates, upload versions, submit for review |
| `reviewer` | Approve/reject template versions; review and finalise documents; view all documents |
| `drafter` | Create and view own or assigned matters and documents |

Rules:
- One person may hold one role in v1. Separation of duties: **the user who submitted a template version cannot approve it.**
- Authorisation is implemented once: `authorize(actor, action, resource) -> Decision(allow, reason)`. Called from the application layer; routes never decide permissions.
- Every repository query includes `tenant_id`. Deny by default.
- Document visibility for drafters: own documents plus those in matters assigned to them.

## 8. Tenancy
`tenant_id` comes from the session. Clients cannot send it. RLS policies are written now and enabled before a second tenant (DATABASE.md section 7). Tests assert that tenant A receives `404` for every tenant B resource.

## 9. Downloads and files
Download endpoints authorise the document, then return a signed URL valid for 60 seconds bound to the user id and document id. Files live in private storage; no public bucket paths. Uploads: size limit 5 MB, extension and magic-byte checks, reject macros, strip external relationships.

## 10. Sensitive data
ID numbers (Aadhaar, PAN) are encrypted with envelope encryption; keys come from environment/secret manager; rotation supported by key id. Show masked values in the UI (last 4 characters); reveal requires an explicit action that writes an audit event. Retention classes per DATABASE.md section 8. Confirm statutory obligations with the company's counsel (including the Digital Personal Data Protection Act, 2023 and its rules).

## 11. Bootstrap and operations
- First admin created by CLI: `python -m app.cli create-admin --email ...` (prompts for a password; never in shell history).
- Secrets only from environment: `SECRET_KEY`, `MASTER_KEY`, `INDEX_KEY`. Rotation runbook in `docs/runbooks/rotate-secrets.md`.
- Security headers via Caddy: HSTS, `X-Content-Type-Options`, strict CSP (no inline scripts), `Referrer-Policy`, `Permissions-Policy`.

## 12. Audit events (auth)
`login_success`, `login_failure`, `lockout`, `logout`, `password_change`, `password_reset`, `mfa_enrolled`, `mfa_disabled`, `role_changed`, `user_created`, `user_deactivated`, `sensitive_value_revealed`, `download_url_issued`. Each with actor, IP (truncated per policy), user agent, correlation id.

## 13. Test matrix (must exist before launch)

| Test | Expectation |
|---|---|
| Every endpoint x every role | Matches the matrix in API.md section 4 |
| Cross-tenant access to each resource type | `404` |
| IDOR: drafter requests another drafter's document | `404` or `403` per policy, never data |
| Missing or wrong CSRF token | `403` |
| Session fixation and rotation | New cookie after login |
| Brute force | `429` / `423` after thresholds |
| Reset token reuse and expiry | Rejected |
| Template submitter approves own version | `409` or `403` |
| Logs and error bodies | No passwords, tokens, hashes or personal data |
| Dependency and header scan | ZAP baseline clean of high findings |

## 14. Out of scope for v1
SSO/OAuth, social login, API keys for third parties, passkeys (consider after launch), per-field attribute-based permissions.
