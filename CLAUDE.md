# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **skills repository** compatible with `npx skills add <owner>/<repo>` for Claude Code. It contains reusable skills that can be installed and triggered automatically based on user requests.

### Structure

- `skills/<name>/SKILL.md` - Each skill lives in its own directory with a `SKILL.md` entrypoint
- `templates/SKILL.template.md` - Template for creating new skills
- `docs/REPOSITORY_STRUCTURE.md` - Repository layout documentation
- `skills-lock.json` - Lock file for skills from external sources
- `.agents/skills` - Symlink to `skills/` for agent discovery

### Key Concepts

**SKILL.md Format**: Every skill requires YAML frontmatter with `name` and `description` fields. The description is the primary trigger mechanism - it should clearly state what the skill does AND when to use it.

**Progressive Disclosure**: Skills use a three-level loading system:
1. Metadata (name + description) - always in context
2. SKILL.md body - loaded when skill triggers (<500 lines recommended)
3. Bundled resources (scripts/, references/, assets/) - loaded as needed

**Skill Types in This Repo**:
- `repo-bootstrap` - Scaffold new skill repositories
- `hello-skill` - Minimal validation example
- `threads-blog-post` - Convert Threads.net posts to blog posts (Korean)
- `skill-creator` - Create and improve skills with eval/benchmark workflow
- `agent-browser` - Browser automation via agent-browser CLI
- `playwright-cli` - Browser automation via Playwright CLI

## Common Commands

### Validate Skills Structure
```bash
npx skills add <owner>/<repo> --list
```

### Install Specific Skill
```bash
npx skills add <owner>/<repo> --skill <skill-name>
```

### Create New Skill
```bash
mkdir -p skills/my-new-skill
cp templates/SKILL.template.md skills/my-new-skill/SKILL.md
```

## Adding New Skills

1. Create `skills/<new-skill-name>/SKILL.md`
2. Include YAML frontmatter with `name` and `description`
3. The `name` must match the directory name (lowercase, hyphens)
4. Keep SKILL.md under 500 lines - use `references/` for additional docs
5. Test with `npx skills add <owner>/<repo> --list`

## Skill Writing Guidelines

- **Description quality**: Make descriptions slightly "pushy" to improve triggering - include specific use cases and triggers
- **Progressive disclosure**: Keep main skill file focused, reference additional docs from `references/`
- **Bundled scripts**: Put reusable code in `scripts/` to avoid reinvention across invocations
- **Agent coordination**: For complex skills, define clear roles for Fetcher/Content/Media agents (see `threads-blog-post` for example)

## Language Notes

The repository README and most documentation are in Korean, but skills support both Korean and English content. The `threads-blog-post` skill specifically produces Korean blog output.
