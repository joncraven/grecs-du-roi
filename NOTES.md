# NOTES — state of this project (handoff for the next worker)

Written during verification of t_4d46ee5a (card: "Unblock t_5d81959b: ensure git
repo and resume work"). No re-investigation needed — read this first.

## What the original task (t_5d81959b) was

Create the Kanban card set from `docs/phase2-plan.md` (grecs-du-roi Phase 2:
Estienne-1550 page fidelity, cursive cut, human-decision gates marked
`==> human` in the plan). See that file for the phase breakdown.

## Why it was blocked

Both t_5d81959b and its takeover card t_4d46ee5a declared
`workspace_kind=worktree` while this directory had **no `.git`** anywhere up
to `/Volumes`. The dispatcher's pre-spawn validation
(`_resolve_worktree_workspace` in `hermes_cli/kanban_db.py`) rejected the
spawn 8 times with:

    workspace: task ... worktree path '...' is not inside a git repo and
    does not point at a git repo root

so the worker never started and could never run the `git init` the card
itself asked for (chicken-and-egg). Diagnosis: comment 1042 on t_c29b4aac.

## What was done

- `git init -b main` here + `.gitignore` (OS/editor cruft only) + initial
  commit `c76369f` "Import existing work from t_5d81959b" (67 files, 11 MB;
  fonts, glyph PNGs and QA evidence all tracked).
- Note `/Volumes/RAID10/jon/Projects -> /Volumes/RAID10/Projects` is a
  symlink, so both cards' workspace_paths resolve to this one repo.
- Verified end-to-end by calling the dispatcher's real
  `_resolve_worktree_workspace` for both cards: both PASS and now
  materialize `.worktrees/<task-id>` on branches `wt/t_4d46ee5a` /
  `wt/t_5d81959b` off `main`.

## What remains

- ~~t_5d81959b's card-creation work~~ **RESOLVED 2026-11-09 (t_4899f8ed):**
  verified its acceptance is satisfied by the t_b16a2c44 cut — five Phase-2
  cards exist on the board (t_c33604f9 2.0, t_480a0018 2.1, t_a130c5fc 2.2,
  t_8e2d4b30 2.3/2.4, t_1bdfa688 2.5) with parent/child deps; all three
  `==> human` annotations in `docs/phase2-plan.md` are answered (D1=C and
  D2=John 1 recorded APPROVED §3; the GitHub-repo addition is t_1bdfa688).
- ~~The `==> human` decisions~~ **ANSWERED:** plan header is
  `Status: APPROVED`; Phase-2 dispatch is live (2.0 running, 2.3/2.4 ready).
- Working-tree caveat: untracked `corpus/*.json` (iliad_a1_117,
  hymn_delos_callimachus) belong to in-flight Phase-2.0 (t_c33604f9) —
  that worker commits them.
- `.worktrees/` is gitignored; the dispatcher materializes/removes them per task.

## Repo map

- `src/` — specimen + Estienne recreation pages; `tools/` — build/QA scripts
  (`build_typography.py`, `build_estienne_page.py`, `qa_estienne_page.py`).
- `docs/phase2-plan.md` — the Phase-2 plan (source of the card set).
- `review-punchlist.md`, `qa-evidence/` — QA history; `README.md` — font stack.
