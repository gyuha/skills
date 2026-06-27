#!/usr/bin/env python3
"""Uniform-grid sprite sheet packing + manifest for game-asset-studio.

Packs multiple INDEPENDENT static sprites into a single PNG laid out on a uniform grid
(all cells the same W x H) and writes a simple, engine-agnostic manifest.json mapping
each cell index back to its source asset. This is a texture atlas / tileset — NOT an
animation strip of one character (animation consistency is out of scope; see the skill).

Pillow + numpy only. Deterministic: sprites are ordered by filename, so an NN- prefix on
the generated assets controls cell order.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple


from PIL import Image


def load_sprites(paths: Sequence[str]) -> List[Image.Image]:
    """Open every path as RGBA."""
    return [Image.open(p).convert("RGBA") for p in paths]


def auto_cell(images: Sequence[Image.Image]) -> Tuple[int, int]:
    """Cell size that fits every sprite: (max width, max height). None entries (placeholders) ignored."""
    real = [im for im in images if im is not None]
    w = max(im.size[0] for im in real)
    h = max(im.size[1] for im in real)
    return w, h


def load_generation(path: str) -> Dict:
    """Load the generation record (generation.json) written by generate.py."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def reconcile_items(gen: Dict, sprites_dir: str, allow_partial: bool):
    """Reconcile the intended item list against the PNGs actually on disk (C2).

    Returns an ordered list of (name, id, path_or_None) in the generation's intended
    order — so the sprite-sheet cell index always maps to the original item, never to
    whatever survived. Raises ValueError (refuse) if any item failed/missing and
    allow_partial is False, so a partial generation can't silently re-index the sheet.
    """
    ordered, missing = [], []
    for it in gen.get("items", []):
        fname = it["file"]
        p = os.path.join(sprites_dir, fname)
        stem = os.path.splitext(fname)[0]
        if it.get("ok", True) and os.path.exists(p):
            ordered.append((it["name"], stem, p))
        else:
            missing.append(it["name"])
            ordered.append((it["name"], stem, None))
    if missing and not allow_partial:
        raise ValueError(
            "부분 생성 — 실패/누락 항목: " + ", ".join(missing)
            + " · --allow-partial로 투명 placeholder 패킹 가능 / partial generation; failed/missing: "
            + ", ".join(missing))
    return ordered


def auto_cols(n: int) -> int:
    """Near-square column count for n sprites."""
    return max(1, math.ceil(math.sqrt(n)))


def fit_into_cell(im: Image.Image, cell: Tuple[int, int], mode: str,
                  resample=Image.Resampling.NEAREST) -> Image.Image:
    """Place a sprite centered on a transparent cell-sized canvas.

    Args:
        im: RGBA sprite.
        cell: (w, h) target cell.
        mode: 'contain' resizes (preserving aspect) to fit the cell; 'none' keeps the
              sprite as-is (center-cropped if larger than the cell).
        resample: resize filter for 'contain'. Default NEAREST so already-pixelized dot
            art is not re-blurred into a smooth gradient (C4); pass LANCZOS for smooth art.
    Returns:
        an RGBA image exactly `cell` in size.
    """
    cw, ch = cell
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    src = im
    if mode == "contain":
        sw, sh = im.size
        scale = min(cw / sw, ch / sh)
        nw, nh = max(1, round(sw * scale)), max(1, round(sh * scale))
        src = im.resize((nw, nh), resample)
    sw, sh = src.size
    ox, oy = (cw - sw) // 2, (ch - sh) // 2
    # Center via alpha-composite so partial transparency is preserved.
    canvas.alpha_composite(src, (max(0, ox), max(0, oy)))
    return canvas


def pack(
    images: Sequence[Image.Image],
    names: Sequence[str],
    ids: Optional[Sequence[str]] = None,
    cell: Optional[Tuple[int, int]] = None,
    cols: Optional[int] = None,
    padding: int = 0,
    fit: str = "contain",
    resample=Image.Resampling.NEAREST,
    max_size: Optional[int] = None,
) -> Tuple[Image.Image, Dict]:
    """Compose a uniform-grid sprite sheet and its manifest.

    Layout uses a uniform `padding` as both the outer margin and the gutter between
    cells, so frame origin = padding + index*(cellsize+padding).

    Args:
        images: RGBA sprites (cell order = list order).
        names: per-sprite names recorded in the manifest (same length as images).
        cell: (w, h) cell size; auto = (max width, max height) across sprites.
        cols: column count; auto = near-square ceil(sqrt(n)).
        padding: pixels of margin/gutter.
        fit: 'contain' (resize to fit) or 'none' (place as-is, centered).
    Returns:
        (sheet RGBA image, manifest dict).
    """
    n = len(images)
    if n == 0:
        raise ValueError("no sprites to pack")
    ids = list(ids) if ids is not None else list(names)
    cw, ch = cell if cell else auto_cell(images)
    c = cols if cols else auto_cols(n)
    rows = math.ceil(n / c)

    sheet_w = padding + c * (cw + padding)
    sheet_h = padding + rows * (ch + padding)
    if max_size and max(sheet_w, sheet_h) > max_size:  # M2: refuse runaway sheets
        raise ValueError(
            f"시트가 너무 큽니다: {sheet_w}x{sheet_h} > 한 변 {max_size}px. "
            f"픽셀화로 셀을 줄이거나 --cell/--max-size 조정 / sheet {sheet_w}x{sheet_h} "
            f"exceeds {max_size}px per side (pixelize first, or set --cell/--max-size)")
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    frames: List[Dict] = []
    for idx, (im, name, fid) in enumerate(zip(images, names, ids)):
        col, row = idx % c, idx // c
        x = padding + col * (cw + padding)
        y = padding + row * (ch + padding)
        if im is not None:  # None = failed/missing item → transparent placeholder cell
            sheet.alpha_composite(fit_into_cell(im, (cw, ch), fit, resample), (x, y))
        frames.append({"index": idx, "name": name, "id": fid,
                       "x": x, "y": y, "w": cw, "h": ch})

    manifest = {
        "image": "sheet.png",
        "sheet": {"width": sheet_w, "height": sheet_h},
        "cell": {"width": cw, "height": ch},
        "columns": c,
        "rows": rows,
        "padding": padding,
        "count": n,
        "frames": frames,
    }
    return sheet, manifest


def _expand_inputs(pattern: str) -> List[str]:
    if os.path.isdir(pattern):
        pattern = os.path.join(pattern, "*.png")
    return sorted(glob.glob(pattern))


def _name_of(path: str) -> str:
    """Source filename without extension and without a leading 'NN-' order prefix."""
    base = os.path.splitext(os.path.basename(path))[0]
    parts = base.split("-", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[1]
    return base


def _parse_cell(spec: Optional[str]) -> Optional[Tuple[int, int]]:
    if not spec:
        return None
    if "x" not in spec:
        v = int(spec)
        return v, v
    w, h = spec.lower().split("x", 1)
    return int(w), int(h)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Pack PNGs into a uniform-grid sprite sheet.")
    ap.add_argument("--in", dest="inp", required=True, help="input dir or glob")
    ap.add_argument("--cell", default=None, help="cell size WxH (default: auto = max bbox)")
    ap.add_argument("--cols", type=int, default=None, help="columns (default: near-square)")
    ap.add_argument("--padding", type=int, default=0, help="margin/gutter pixels")
    ap.add_argument("--fit", choices=["contain", "none"], default="contain")
    ap.add_argument("--resample", choices=["nearest", "lanczos"], default="nearest",
                    help="resize filter for --fit contain; nearest preserves dot art (default)")
    ap.add_argument("--generation", default=None,
                    help="generation.json to reconcile against (C2 — preserves intended cell order)")
    ap.add_argument("--allow-partial", action="store_true",
                    help="with --generation: pack transparent placeholders for failed/missing items")
    ap.add_argument("--max-size", type=int, default=4096,
                    help="refuse a sheet exceeding this many pixels per side (M2; default 4096)")
    ap.add_argument("--out", default="sheet.png", help="sheet PNG output path")
    ap.add_argument("--manifest", default="manifest.json", help="manifest JSON output path")
    args = ap.parse_args(argv)

    resample = {"nearest": Image.Resampling.NEAREST,
                "lanczos": Image.Resampling.LANCZOS}[args.resample]

    if args.generation:
        sprites_dir = args.inp if os.path.isdir(args.inp) else os.path.dirname(args.inp)
        try:
            ordered = reconcile_items(load_generation(args.generation), sprites_dir,
                                      args.allow_partial)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        names = [name for name, _, _ in ordered]
        ids = [fid for _, fid, _ in ordered]
        images = [Image.open(p).convert("RGBA") if p else None for _, _, p in ordered]
    else:
        paths = _expand_inputs(args.inp)
        if not paths:
            print(f"ERROR: no PNG inputs matched '{args.inp}'", file=sys.stderr)
            return 1
        images = load_sprites(paths)
        names = [_name_of(p) for p in paths]
        ids = [os.path.splitext(os.path.basename(p))[0] for p in paths]

    try:
        sheet, manifest = pack(
            images, names, ids, _parse_cell(args.cell), args.cols, args.padding,
            args.fit, resample, args.max_size
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    manifest["image"] = os.path.basename(args.out)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    sheet.save(args.out)
    os.makedirs(os.path.dirname(os.path.abspath(args.manifest)), exist_ok=True)  # m2
    with open(args.manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"sheet: {args.out} ({manifest['sheet']['width']}x{manifest['sheet']['height']}, "
          f"{manifest['columns']}x{manifest['rows']} cells of {manifest['cell']['width']}"
          f"x{manifest['cell']['height']})")
    print(f"manifest: {args.manifest} ({manifest['count']} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
