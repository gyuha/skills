# Contributing

## Directory Convention

- Put each skill under `skills/<skill-name>/SKILL.md`
- Use lowercase and hyphens for `<skill-name>`
- Keep one primary skill per directory

## SKILL.md Requirements

Every `SKILL.md` must include YAML frontmatter with:

- `name`
- `description`

Recommended optional fields:

- `metadata.internal: true` for hidden/internal skills

## Quality Checklist

- Frontmatter is valid YAML
- `name` matches the directory name
- Description clearly states trigger/use-case
- Instructions are step-by-step and actionable

## Local Validation

Use `skills` CLI list mode against this repository before publishing:

```bash
npx skills add <owner>/<repo> --list
```

You can also install specific skills to test packaging behavior:

```bash
npx skills add <owner>/<repo> --skill <skill-name>
```
