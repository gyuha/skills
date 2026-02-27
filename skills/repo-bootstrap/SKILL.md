---
name: repo-bootstrap
description: Scaffold a new skill repository with a consistent folder layout and installation-ready SKILL.md files
---

# Repo Bootstrap

Creates and validates a baseline structure for a reusable skills repository.

## When to Use

- Starting a new public/private skills collection
- Standardizing an ad-hoc repository into a `skills/` layout

## Steps

1. Create a `skills/` root directory if missing.
2. Create one folder per skill with `SKILL.md` inside.
3. Ensure each `SKILL.md` has valid `name` and `description` frontmatter.
4. Document installation examples using `npx skills add <owner>/<repo>`.
5. Verify discoverability with `npx skills add <owner>/<repo> --list`.

## Output

- Reproducible repository skeleton
- Installation and contribution docs
- At least one valid example skill
