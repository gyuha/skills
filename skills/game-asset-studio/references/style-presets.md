# Style presets, asset-type defaults, and prompt templates

The wizard uses these to fill smart defaults and to assemble each item's prompt. The
**style anchor** (a shared style descriptor) is prepended to every item by
`scripts/generate.py`; the per-type template below wraps only the *subject*.

## Asset-type defaults

| 종류 (type)        | 투명 기본 (transparent) | 시점 힌트 (perspective) | 시트 비고 |
|--------------------|------------------------|-------------------------|-----------|
| `character`        | on                     | side or 3/4 view        | 단일 포즈. 셀 크기 크게(예 128) |
| `item`             | on                     | 3/4 or front            | 아이템 아틀라스 |
| `tile`             | **off** (불투명)        | top-down, fills frame   | 셀 가장자리까지 채움. *seamless tiling은 best-effort* |
| `icon`             | on                     | front / flat            | 작게 읽혀야 함. 셀 작게(예 64) |

기본 캔버스 크기는 모두 정사각 `1024x1024`. 세로 캐릭터는 `1024x1536`을 제안할 수 있다.

## Style anchor presets

세트 전체 일관성의 *유일한* 레버다(img2img 불가). 프리셋 + 사용자 자유 디테일(팔레트·아웃라인·조명)을 합쳐 `style_anchor`를 만든다.

| 프리셋 | style_anchor 본문 |
|--------|-------------------|
| `pixel` | `16-bit pixel art, crisp dot art, limited cohesive palette, clean dark outlines` |
| `chibi` | `chibi style, large head small body, soft cel shading, bright cohesive palette` |
| `cartoon` | `cartoon game art, bold clean outlines, flat cel shading` |
| `hand-drawn` | `hand-drawn game illustration, painterly soft edges, warm palette` |
| `realistic` | `semi-realistic 2D game art, detailed shading, cohesive palette` |

> 픽셀화 후처리(`pixelize.py`)를 켤 거라면 프리셋은 `pixel`이 아니어도 된다 — 후처리가 진짜 도트로 변환한다. 단 `pixel` 프리셋 + 픽셀화 후처리 조합이 가장 또렷하다.

## Per-type prompt templates (subject wrapper)

`item.prompt`에 들어갈 본문. `generate.py`가 앞에 `style_anchor`를, (투명이면) 뒤에 투명 가이드를 자동으로 붙인다 — 여기엔 스타일·투명 문구를 넣지 않는다.

- `character`: `A game character: {desc}. Full body, single static pose, centered, facing {view}.`
- `item`: `A single game item: {desc}. One object, centered, no background scene.`
- `tile`: `A {view} game terrain/floor tile: {desc}. Fills the frame edge to edge, repeating-friendly.`
- `icon`: `A game UI icon: {desc}. Simple, bold, centered, readable at small size.`

`{view}`는 위 표의 시점 힌트, `{desc}`는 사용자가 입력한 항목 설명.
