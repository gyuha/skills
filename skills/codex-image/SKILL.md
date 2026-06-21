---
name: codex-image
description: |
  Generate images via Codex CLI's built-in image_gen tool (gpt-image-2). OAuth auth — no API key needed.
  Codex CLI의 내장 image_gen 도구로 이미지 생성. OAuth 인증으로 API 키 불필요.
  Usage: /codex-image cherry blossom hanok, /codex-image --size 1024x1536 space cat, /codex-image --quality high seoul night
argument-hint: "[--size <WxH>] [--quality low|medium|high] [--out <path>] [-n <count>] <image prompt>"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
author: wjb127
source: https://github.com/wjb127/codex-image
---

# codex-image — AI Image Generation via Codex OAuth

> Ported from [github.com/wjb127/codex-image](https://github.com/wjb127/codex-image) (author: wjb127).

Generate images using OpenAI's `gpt-image-2` model through Codex CLI.
**No API key required** — uses Codex OAuth (ChatGPT login) authentication.

OpenAI Codex CLI의 내장 `image_gen` 도구를 통해 `gpt-image-2` 모델로 이미지를 생성한다.
**API 키 불필요** — Codex OAuth(ChatGPT 로그인) 인증 사용.

## How it works / 동작 원리

```
User prompt → Claude Code (/codex-image)
  → codex exec (OAuth token auto-managed)
    → built-in image_gen tool (gpt-image-2)
      → ~/.codex/generated_images/<session>/
        → copy to project root
```

> **Important**: OAuth tokens cannot call OpenAI REST API directly (returns 401).
> Must go through `codex exec` which handles auth internally.
>
> OAuth 토큰으로 OpenAI REST API 직접 호출 불가 (401 반환).
> 반드시 `codex exec` 경유 — Codex가 내부적으로 인증 처리.

---

## Step 1 — Verify Codex CLI & Auth / Codex CLI 및 인증 확인

```bash
which codex 2>/dev/null && codex --version 2>/dev/null || echo "NOT_FOUND"
```

If `NOT_FOUND`, stop:
> "Codex CLI not installed. Run `npm install -g @openai/codex` then `codex login`."
> "Codex CLI 없음. `npm install -g @openai/codex` 후 `codex login` 실행해."

```bash
codex login status 2>&1
```

If not "Logged in":
> "Codex login required. Run `codex login` in terminal. OAuth login enables image generation without API key."
> "Codex 로그인 필요. 터미널에서 `codex login` 실행. OAuth 로그인하면 API 키 없이 이미지 생성 가능."

## Step 2 — Parse Arguments / 인자 파싱

Extract from `$ARGUMENTS`:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--size` | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | `1024x1024` | Image dimensions / 이미지 크기 |
| `--quality` | `low`, `medium`, `high`, `auto` | `auto` | Generation quality / 생성 품질 |
| `--out` | directory path | project root | Save location / 저장 위치 |
| `-n` | 1–10 | `1` | Number of images / 생성 장수 |
| `--transparent` | (no value) | off | Force transparent-PNG mode / 투명 PNG 모드 강제 |

Remaining text → image prompt / 나머지 텍스트 → 이미지 프롬프트

### Transparent mode detection / 투명 모드 감지

Set `_TRANSPARENT=1` when **either** is true:

1. The `--transparent` flag is present.
2. The image prompt contains a transparency keyword (**case-insensitive**):
   - KO: `투명`, `투명배경`, `투명 배경`, `누끼`, `배경 제거`, `배경 없`
   - EN: `transparent`, `transparency`, `alpha channel`, `no background`, `cutout`

```bash
_TRANSPARENT=0
case "${_ARGS}" in *"--transparent"*) _TRANSPARENT=1 ;; esac
# prompt keyword scan (case-insensitive); strip --transparent first so it isn't re-matched
_PROMPT_LC=$(printf '%s' "${_PROMPT}" | tr '[:upper:]' '[:lower:]')
for _kw in "투명" "누끼" "배경 제거" "배경 없" "transparent" "transparency" "alpha channel" "no background" "cutout"; do
  case "${_PROMPT_LC}" in *"${_kw}"*) _TRANSPARENT=1 ;; esac
done
```

> Why prompt-only, not an API param: this skill goes through `codex exec` → built-in
> `image_gen`, so the OpenAI `background: "transparent"` parameter is not reachable.
> The only lever is the prompt text — so transparent mode is a **best-effort prompt
> injection**, and true alpha output still depends on the model supporting it.
>
> codex exec 경유라 API의 `background: "transparent"` 파라미터에 접근 불가 — 유일한
> 레버는 프롬프트 텍스트뿐이라 best-effort 프롬프트 주입이며, 진짜 알파 출력 여부는
> 모델 지원에 달렸다.

If prompt is empty, ask via AskUserQuestion:
> "What image should I generate? Enter a prompt."
> "어떤 이미지를 생성할까? 프롬프트를 입력해줘."

## Step 3 — Determine Save Path / 저장 경로 결정

```bash
_PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_OUT_DIR="${_PROJECT_ROOT}"
_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
_FILENAME="codex-image-${_TIMESTAMP}"
```

- If `--out` specified, use that path / `--out` 지정 시 해당 경로 사용
- Single image: `codex-image-<timestamp>.png`
- Multiple (`-n > 1`): `codex-image-<timestamp>-1.png`, `-2.png`, ...
- Never overwrite existing files / 기존 파일 덮어쓰기 금지

## Step 4 — Generate Image / 이미지 생성

Sanitize the prompt before interpolating it into the `codex exec "..."` string —
a raw `"` in the prompt would terminate the double-quoted argument and break the
command (a prompt like `a "vintage" poster` is perfectly normal):

```bash
# Replace " with ' so the prompt can't break the codex exec double-quoted string.
# Ceiling: backticks and $ in the prompt can still trigger shell substitution —
# if that surfaces in practice, wrap the prompt in a quoted heredoc / single quotes instead.
_PROMPT="${_PROMPT//\"/\'}"
```

When transparent mode is on (`_TRANSPARENT=1`, see Step 2), append the transparent-PNG
keyword formula. The three anchor phrases — `true transparent background`, `alpha channel`,
`no fake transparency` — are mandatory: without them the rest is nullified and a white
background returns.

```bash
if [ "${_TRANSPARENT}" = "1" ]; then
  # Warn (do NOT auto-strip) if the prompt itself carries a background instruction —
  # any background keyword nullifies the transparency formula.
  case "$(printf '%s' "${_PROMPT}" | tr '[:upper:]' '[:lower:]')" in
    *"흰 배경"*|*"흰배경"*|*"white background"*|*"배경 색"*|*"background color"*|*"solid background"*)
      echo "⚠ 프롬프트에 배경 지시가 있어 투명이 무력화될 수 있습니다. 배경 문구 제거를 권장합니다." ;;
  esac
  _PROMPT="${_PROMPT} — isolated subject, true transparent background, alpha channel, PNG with transparency, no background, no shadow, no reflection, no checkerboard pattern, no fake transparency, clean edges, centered composition"
fi
```

```bash
codex exec "Perform the following tasks:
1. Use the built-in image_gen tool to generate an image.
2. Prompt: '${_PROMPT}'
3. Size: ${_SIZE}
4. Quality: ${_QUALITY}
5. Count: ${_N}
6. Copy the generated image to '${_OUT_DIR}/${_FILENAME}.png'. For multiple images use -1.png, -2.png suffix.
7. Print the saved file path and size." \
  -C "${_PROJECT_ROOT}" \
  -s workspace-write \
  -c 'model_reasoning_effort="medium"' \
  --skip-git-repo-check \
  2>&1
```

timeout: 120000ms (2 min)

### Required flags / 필수 플래그

- `-s workspace-write` — file write permission / 파일 쓰기 권한
- `--skip-git-repo-check` — works outside git repos / git 레포 외부에서도 실행 가능

### Internal flow (Codex side) / 내부 동작 흐름

1. Codex calls built-in `image_gen` tool (gpt-image-2)
2. Image saved to `~/.codex/generated_images/<session-id>/ig_*.png`
3. Codex copies file to specified project path
4. Reports file path and size

## Step 5 — Display Result / 결과 출력

```
═══════════════════════════════════════════════
IMAGE GENERATED / 이미지 생성 완료
═══════════════════════════════════════════════
Prompt: <prompt used>
Size: <size>
Quality: <quality>
Count: <n>
Auth: OAuth (ChatGPT)
───────────────────────────────────────────────
<saved file path(s)>
═══════════════════════════════════════════════
```

**Always display the generated image using the Read tool.**
**생성된 이미지를 반드시 Read 도구로 표시한다.**

When transparent mode was on, also print this caveat / 투명 모드였다면 아래 caveat도 출력:
> "Transparent mode — verify the saved PNG actually has an alpha channel. If the model doesn't support transparency, it may return a white or checkerboard background instead."
> "투명 모드 — 저장된 PNG에 실제 알파 채널이 있는지 확인하세요. 모델이 투명도를 지원하지 않으면 흰/체크무늬 배경이 나올 수 있습니다."

## Step 6 — Follow-up / 후속 안내

- "Run `/codex-image` again to generate another image."
- For Next.js projects: suggest moving to `public/images/` if needed.

## Error Handling / 에러 처리

| Error | Message |
|-------|---------|
| Auth expired | "Codex OAuth expired. Run `codex login` again." / "OAuth 인증 만료. `codex login` 다시 실행." |
| Model access denied | "No access to gpt-image-2. Check your OpenAI plan." / "gpt-image-2 접근 권한 없음. OpenAI 플랜 확인." |
| Timeout (>2min) | "Generation timed out. Try `--quality low`." / "생성 시간 초과. `--quality low`로 재시도." |
| Rate limit | "API rate limited. Wait and retry." / "API 호출 제한. 잠시 후 재시도." |
| Trust error | Check `--skip-git-repo-check` flag or add project to `~/.codex/config.toml` |

## Rules / 규칙

- Always use the Read tool to display generated images / 생성된 이미지는 반드시 Read로 표시
- Never overwrite existing files — always use timestamped filenames / 기존 파일 덮어쓰기 금지
- OAuth only — do not attempt direct REST API calls with OAuth token (returns 401) / OAuth 토큰으로 REST API 직접 호출 금지
- Verify prompt intent before generating / 생성 전 프롬프트 의도 확인
- Transparent mode (keyword or `--transparent`): inject the alpha-channel formula and never mix in a background-color instruction; true alpha depends on model support — surface the verify caveat / 투명 모드(키워드 또는 `--transparent`): 알파 채널 공식을 주입하고 배경색 지시를 섞지 않는다. 진짜 알파는 모델 지원에 종속되므로 확인 caveat를 안내
