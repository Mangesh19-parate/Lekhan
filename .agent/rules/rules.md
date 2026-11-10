# Agent Rules

All development within this repository is governed strictly by the rules and protocols in [AGENTS.md](../../AGENTS.md).

Key Rules:
1. No real personal data anywhere in repository, fixtures, or logs.
2. Never `eval`, `exec`, `compile`, or `pickle.loads` on template or user input.
3. Approved templates are immutable.
4. Authorisation and tenant scoping are enforced in the backend.
5. Exact numbers: Decimal only for money and area. No floats.
6. Unicode text normalised to NFC with grapheme clusters for Marathi.

