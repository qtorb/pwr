# Mojibake Incident Note

Date: 2026-04-23

## What happened

- Production showed broken accent/emojis in runtime text rendered from `app_main.py`.
- The database scan returned `0` mojibake hits, so the issue was not coming from SQLite state.
- Git history shows `app_main.py` was still clean in commit `910e333` (`2026-04-23 01:16:32 +0200`).
- The first bad snapshot appears in commit `7416932` (`2026-04-23 13:23:35 +0200`).

## Most likely cause

The corruption signature matches a UTF-8 file that was read or saved through a cp1252/latin-1 path during the large rewrite that landed in `7416932`.

Git can identify the exact commit window, but it cannot prove which external editor/tool performed the non-UTF-safe save.

## Scope

- Runtime-visible literals in `app_main.py`
- Seed strings created by `init_db()` for fresh databases
- No evidence of persisted corruption in SQLite during the incident review

## Prevention now in repo

- Local detector: `python check_mojibake.py`
- Canonical setup check now fails if mojibake signatures are present: `python validate_setup.py`
- CI guard on push/PR: `.github/workflows/mojibake-guard.yml`

The detector flags the signatures that caused this incident:

- `U+00C3`
- `U+00C2`
- `U+00E2`
- `U+00F0 U+0178`

## If it happens again

1. Stop at source-file level first; do not assume browser/runtime.
2. Run `python check_mojibake.py`.
3. If the detector hits only source literals, repair the affected file as UTF-8 and avoid DB migration.
4. Only normalize persisted data if a DB scan shows the same signatures in stored rows.
