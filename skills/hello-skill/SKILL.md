---
name: hello-skill
description: Minimal example skill for validating installation and discovery
---

# Hello Skill

Minimal example used to confirm skill discovery and install flow.

## When to Use

- Smoke-testing a new skills repository
- Verifying `npx skills add ... --skill hello-skill`

## Steps

1. Confirm this skill appears in `--list` output.
2. Install only this skill using `--skill hello-skill`.
3. Ensure the target agent can read and load the skill file.

## Output

- A validated installation baseline for future skills
