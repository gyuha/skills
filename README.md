# Skills Repository

Claude Code용 스킬 저장소입니다. `npx skills` CLI와 호환되는 구조로 되어 있어, 쉽게 설치하고 사용할 수 있습니다.

## Quick Start

```bash
# 저장소의 모든 스킬 설치
npx skills add gyuha/skills

# 특정 스킬만 설치
npx skills add gyuha/skills@agent-browser

# 또는 --skill 옵션 사용
npx skills add gyuha/skills --skill agent-browser
```

## Repository Layout

```
.
├── README.md
├── CONTRIBUTING.md
├── CLAUDE.md
├── docs/
│   └── REPOSITORY_STRUCTURE.md
├── templates/
│   └── SKILL.template.md
├── .agents/
│   └── skills -> ../skills/     # 스킬 디스커버리용 심볼릭 링크
└── skills/
    ├── agent-browser/
    ├── playwright-cli/
    ├── skill-creator/
    ├── threads-blog-post/
    ├── repo-bootstrap/
    └── hello-skill/
```

## Skill Catalog

| 스킬 이름 | 설명 |
|----------|------|
| **agent-browser** | AI Agent를 위한 브라우저 자동화 CLI. 웹사이트 탐색, 폼 작성, 스크린샷, 데이터 추출, 웹 앱 테스트 등 브라우저 작업 자동화에 사용 |
| **playwright-cli** | Playwright를 사용한 브라우저 자동화. 웹 테스트, 폼 작성, 스크린샷, 데이터 추출 등 |
| **skill-creator** | 새 스킬 생성, 기존 스킬 개선, 스킬 성능 측정 및 평가 |
| **threads-blog-post** | Threads.net 포스트를 블로그 글로 변환 (한국어) |
| **repo-bootstrap** | 일관된 폴더 구조와 설치 가능한 SKILL.md 파일로 새 스킬 저장소 스캐폴딩 |
| **hello-skill** | 설치 및 디스커버리 검증을 위한 최소 예시 스킬 |

## Adding a New Skill

1. `skills/<new-skill-name>/SKILL.md` 생성
2. `templates/SKILL.template.md`를 복사해 frontmatter/본문 작성
3. `README.md`의 Skill Catalog에 새 스킬 추가

```bash
mkdir -p skills/my-new-skill
cp templates/SKILL.template.md skills/my-new-skill/SKILL.md
```

## SKILL.md Format

각 스킬은 반드시 `SKILL.md` 하나를 포함해야 하며, YAML frontmatter에 최소 필수 필드가 있어야 합니다.

```markdown
---
name: my-skill
description: What this skill does and when to use it
---

# Skill Content
...
```

- **name**: 고유 식별자 (소문자 + 하이픈 권장, 디렉터리 이름과 일치해야 함)
- **description**: 스킬 사용 목적과 트리거 조건을 명확하게 설명

## Compatibility Notes

- `skills` CLI는 여러 경로를 탐색하지만, 공개 스킬 레포에서는 `skills/` 루트를 유지하는 것이 가장 예측 가능하고 관리가 쉽습니다.
- 설치 대상 에이전트는 CLI 옵션으로 지정할 수 있습니다.

```bash
npx skills add gyuha/skills -a claude-code -a codex
```

## References

- `skills.sh` docs: https://skills.sh/docs
- CLI reference: https://skills.sh/docs/cli
- Reference repository: https://github.com/inference-sh/skills
