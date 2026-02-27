---
name: threads-post-blogger
description: Turn a Threads post URL into a structured blog draft by extracting the thread flow and writing a publish-ready article. Use this whenever the user shares a Threads link and asks for summary, blog writing, article drafting, newsletter conversion, or content repurposing from Threads posts. Prefer this skill even when the user just says "이 링크로 글 써줘".
---

# Threads Post Blogger

Threads 단일 포스트 URL을 받아, 원문 맥락을 유지한 블로그 초안을 작성한다.

## When To Use

- 사용자가 Threads 링크로 요약/블로그/아티클 작성을 요청할 때
- 사용자가 "이 쓰레드로 글 써줘", "뉴스레터용으로 바꿔줘"처럼 재가공을 요청할 때
- 입력이 Threads post URL인 콘텐츠 변환 요청일 때

## Input Rules

- 허용 URL: `https://www.threads.com/@<handle>/post/<post_id>`
- 메인 주소(`https://www.threads.com`) 또는 프로필 주소(`https://www.threads.com/@<handle>`)는 무시한다.
- `/post/`가 없는 URL이면 블로그 작성을 시작하지 말고, "포스트 URL" 재입력을 요청한다.

## Core Extraction Rule (가장 중요)

1. 첫 번째 포스트의 작성자를 `root_author`로 확정한다.
2. 첫 포스트부터 아래로 내려가며, 작성자가 `root_author`인 포스트만 연속으로 수집한다.
3. `root_author`가 아닌 작성자가 처음 등장하면 그 지점부터는 댓글 구간으로 간주하고 중단한다.
4. 중단 이후에 `root_author`가 다시 나오더라도 포함하지 않는다.

이 규칙은 댓글 오염을 막기 위한 핵심 필터다.

## Media Handling

연속 수집된 포스트 범위에서만 미디어를 수집한다.

- 이미지: URL, 캡션/설명(있으면), 맥락 문장
- 동영상: URL, 길이/설명(보이는 범위), 핵심 장면 요약
- 여러 미디어가 있으면 본문 문단 흐름에 맞춰 분산 배치한다.
- 미디어 원본 URL이 불분명하면 "원문 미디어(접근 제한 가능)"로 표시하고 대체 설명 문장을 제공한다.

## Workflow

1. URL 검증
- 입력 URL이 post 형식인지 확인한다.
- 메인/프로필 URL이면 포스트 URL 요청 메시지를 반환한다.

2. 원문 읽기
- Threads 내용 추출은 반드시 `agent-browser` skill을 사용해 수행한다.
- 기본 절차:
  - `agent-browser open <post_url>` 후 `agent-browser wait --load networkidle`
  - `agent-browser snapshot -i`로 현재 화면의 작성자/본문/미디어 단서를 수집한다.
  - 필요 시 `agent-browser scroll down <px>` 또는 클릭으로 답글 영역이 로드되도록 진행 후 `agent-browser snapshot -i`를 반복한다.
  - 스냅샷에서 포스트 작성자/본문/미디어 정보를 읽어 수집한다.
  - 완료 후 `agent-browser close`
- 전역 `agent-browser` 실행이 불가능하면 `npx agent-browser`로 동일 절차를 재시도한다.
- 접근 제한(로그인/지역 제한)이 있으면 확인된 내용만 사용하고 누락 범위를 명시한다.

3. 연속 작성자 필터 적용
- `root_author` 기준 연속 구간만 남긴다.
- 타 작성자 등장 시 즉시 수집 중단.

4. 블로그 글 구성
- 원문 문장을 그대로 복붙하지 말고 핵심 논지를 재구성한다.
- 정보 밀도는 유지하고, 읽기 쉬운 블로그 문체로 정리한다.
- 미디어를 문단 맥락과 연결해 삽입 위치를 제안한다.

## Output Format

반드시 아래 구조로 Markdown 출력:

```markdown
# [블로그 제목]

## 한줄 요약
- ...

## 원문 흐름 요약
1. ...
2. ...
3. ...

## 블로그 본문
[도입]
...

[핵심 내용]
...

[정리]
...

## 미디어 활용 제안
- 미디어 1: (타입: 이미지/동영상) [설명]
  - 추천 삽입 위치: 본문의 어떤 단락 뒤
  - 대체 텍스트/캡션: ...
- 미디어 2: ...

## 제외된 내용
- 댓글/타 작성자 내용은 제외함
- 제외 시작 지점(있으면): ...
```

## Quality Checklist

- 입력 URL이 post URL인지 확인했는가?
- 첫 작성자 연속 구간만 사용했는가?
- 타 작성자 시작 이후 내용을 배제했는가?
- 미디어를 최소 1개 이상 반영했는가? (없으면 "미디어 없음" 명시)
- 확인 불가 정보(접근 제한/삭제)는 추정하지 않고 명시했는가?

## Failure Responses

- 잘못된 URL: "Threads 포스트 URL(`/post/`)을 보내주세요. 메인/프로필 주소는 처리하지 않습니다."
- 콘텐츠 접근 실패: "해당 포스트의 본문/미디어 일부를 확인할 수 없어, 확인된 범위만으로 초안을 작성했습니다."

## Example Prompts

- `이 링크를 블로그 글로 바꿔줘: https://www.threads.com/@choi.openai/post/DVQamrZj4vp`
- `이 쓰레드 요약해서 미디어 포함 블로그 초안 만들어줘. 댓글은 빼줘.`
