# Skills Repository Starter

`skills.sh` 설치 플로우와 호환되는 스킬 저장소 기본 구조입니다.

## Quick Start

이 저장소를 GitHub에 올린 뒤 아래처럼 설치할 수 있습니다.

```bash
# 저장소의 모든 스킬 설치
npx skills add <owner>/<repo>

# 특정 스킬만 설치
npx skills add <owner>/<repo>@repo-bootstrap

# 또는 --skill 옵션 사용
npx skills add <owner>/<repo> --skill repo-bootstrap
```

`inference-sh/skills` 스타일을 따라 루트에 `skills/` 디렉터리를 두고, 각 스킬은 독립 폴더 + `SKILL.md` 파일로 관리합니다.

## Repository Layout

```text
.
├── README.md
├── CONTRIBUTING.md
├── docs/
│   └── REPOSITORY_STRUCTURE.md
├── templates/
│   └── SKILL.template.md
└── skills/
    ├── repo-bootstrap/
    │   └── SKILL.md
    └── hello-skill/
        └── SKILL.md
```

## Skill Rules

각 스킬은 반드시 `SKILL.md` 하나를 포함해야 하며, YAML frontmatter에 최소 필수 필드가 있어야 합니다.

```markdown
---
name: my-skill
description: What this skill does and when to use it
---
```

- `name`: 고유 식별자 (소문자 + 하이픈 권장)
- `description`: 스킬 사용 목적과 트리거를 짧게 설명

## Add a New Skill

1. `skills/<new-skill-name>/SKILL.md` 생성
2. `templates/SKILL.template.md`를 복사해 frontmatter/본문 작성
3. `README.md`의 Skill Catalog 섹션에 새 스킬 추가

예시:

```bash
mkdir -p skills/my-new-skill
cp templates/SKILL.template.md skills/my-new-skill/SKILL.md
```

## Skill Catalog

- `repo-bootstrap`: 스킬 저장소를 빠르게 시작할 때 쓰는 가이드형 스킬
- `hello-skill`: 최소 구조 예시

## Compatibility Notes

- `skills` CLI는 여러 경로를 탐색하지만, 공개 스킬 레포에서는 `skills/` 루트를 유지하는 것이 가장 예측 가능하고 관리가 쉽습니다.
- 설치 대상 에이전트는 CLI 옵션으로 지정할 수 있습니다.

```bash
npx skills add <owner>/<repo> -a claude-code -a codex
```

## References

- `skills.sh` docs: https://skills.sh/docs
- CLI reference: https://skills.sh/docs/cli
- Reference repository: https://github.com/inference-sh/skills
