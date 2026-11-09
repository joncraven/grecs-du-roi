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

- **t_5d81959b's card-creation work**: the Phase-2 implementation cards were
  already cut via t_b16a2c44; t_5d81959b itself sits `blocked` and needs a
  human/dispatcher **unblock** to re-spawn now that the git blocker is gone.
  Its acceptance (cards + `==> human` decision gates) may already be satisfied
  by the t_b16a2c44 cut — check before doing it twice.
- The `==> human` decisions in `docs/phase2-plan.md` still need human answers
  before the Phase-2 implementation cards can run.
- Working-tree caveat at time of writing: untracked
  `corpus/iliad_a1_117.json` in the main checkout (someone's in-flight data).

## Repo map

- `src/` — specimen + Estienne recreation pages; `tools/` — build/QA scripts
  (`build_typography.py`, `build_estienne_page.py`, `qa_estienne_page.py`).
- `docs/phase2-plan.md` — the Phase-2 plan (source of the card set).
- `review-punchlist.md`, `qa-evidence/` — QA history; `README.md` — font stack.
