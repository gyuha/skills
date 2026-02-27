# Repository Structure

This repository follows the common public skills-repo pattern:

- Root `skills/` directory for discoverable skills
- One skill directory per capability
- `SKILL.md` as the skill entrypoint

## Why this structure

- Compatible with `npx skills add <owner>/<repo>`
- Predictable for contributors
- Similar to widely used public skill collections

## Discovery Notes

The `skills` CLI can discover skills from multiple paths, but this repository standardizes on:

- `skills/<name>/SKILL.md`

Optional future expansion (if needed):

- `skills/.curated/`
- `skills/.experimental/`
- `skills/.system/`

## Naming

- Directory name: lowercase, hyphen-separated
- Frontmatter `name`: same as directory name
