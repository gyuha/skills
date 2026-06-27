#!/usr/bin/env python3
"""Real pixelization post-process for game-asset-studio.

Turns smooth high-resolution generations from gpt-image-2 into true dot art via a
deterministic pipeline: downscale to a target pixel grid + palette quantization
(optionally a shared palette across a set, for visual cohesion) + optional hard-edge
alpha + optional integer nearest-neighbor upscale.

This is the *deterministic* counterpart to writing "pixel art" in a prompt (which only
yields smooth, uneven results). Pillow + numpy only.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import List, Optional, Sequence

import numpy as np
from PIL import Image


def load_rgba(path: str) -> Image.Image:
    """Open an image and coerce it to RGBA.

    Args:
        path: image file path.
    Returns:
        an RGBA PIL image.
    """
    return Image.open(path).convert("RGBA")


def downscale(im: Image.Image, target: int) -> Image.Image:
    """Downscale so the longest side equals `target`, preserving aspect ratio.

    Args:
        im: RGBA image.
        target: longest-side pixel count (e.g. 32, 48, 64).
    Returns:
        the downscaled RGBA image (LANCZOS).
    """
    w, h = im.size
    if max(w, h) <= target:
        return im.copy()
    if w >= h:
        nw = target
        nh = max(1, round(h * target / w))
    else:
        nh = target
        nw = max(1, round(w * target / h))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def binarize_alpha(im: Image.Image, threshold: int) -> Image.Image:
    """Force alpha to be either 0 or 255 at `threshold` — hard edges for dot art.

    Args:
        im: RGBA image.
        threshold: alpha cutoff (0-255). Alpha < threshold -> 0, else 255.
    Returns:
        a new RGBA image with binary alpha.
    """
    arr = np.array(im)
    a = arr[..., 3]
    arr[..., 3] = np.where(a < threshold, 0, 255).astype("uint8")
    return Image.fromarray(arr, "RGBA")


def _opaque_rgb_pixels(arr: np.ndarray, alpha_threshold: int) -> np.ndarray:
    """Flatten the opaque RGB pixels of an RGBA array to an (N, 3) uint8 array."""
    mask = arr[..., 3] > alpha_threshold
    return arr[mask][:, :3].astype("uint8")


def build_palette(
    arrays: Sequence[np.ndarray], colors: int, alpha_threshold: int = 0
) -> Image.Image:
    """Build a quantized palette from the OPAQUE pixels of one or more RGBA arrays.

    Passing every image in a set yields a single shared palette so the whole set reads
    as one cohesive sprite collection.

    Args:
        arrays: list of RGBA numpy arrays (H, W, 4).
        colors: palette size (number of colors).
        alpha_threshold: pixels with alpha <= this are ignored (treated transparent).
    Returns:
        a mode 'P' PIL image whose palette is the quantized color set.
    """
    chunks = [_opaque_rgb_pixels(a, alpha_threshold) for a in arrays]
    chunks = [c for c in chunks if len(c) > 0]
    if not chunks:
        # Fully transparent set — fall back to a 1px black strip.
        strip = Image.new("RGB", (1, 1))
    else:
        allpx = np.concatenate(chunks, axis=0).reshape(-1, 1, 3)
        strip = Image.fromarray(allpx, "RGB")
    return strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)


def quantize_rgb(im_rgba: Image.Image, pal: Image.Image) -> Image.Image:
    """Map an RGBA image's RGB channels onto a fixed palette (no dither), keep alpha.

    Args:
        im_rgba: source RGBA image.
        pal: a mode 'P' palette image (see build_palette).
    Returns:
        an RGBA image whose RGB is snapped to the palette, alpha preserved.
    """
    rgb = im_rgba.convert("RGB")
    q = rgb.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    out = q.convert("RGBA")
    out.putalpha(im_rgba.getchannel("A"))
    return out


def upscale_nn(im: Image.Image, factor: int) -> Image.Image:
    """Integer nearest-neighbor upscale (crisp dot art preview).

    Args:
        im: RGBA image.
        factor: integer scale factor (>=1).
    Returns:
        the upscaled image (NEAREST).
    """
    if factor <= 1:
        return im
    w, h = im.size
    return im.resize((w * factor, h * factor), Image.Resampling.NEAREST)


def pixelize_image(
    im: Image.Image,
    target: int,
    pal: Image.Image,
    alpha_threshold: Optional[int] = None,
    upscale: int = 1,
) -> Image.Image:
    """Run the full pixelization pipeline on a single image with a given palette.

    Args:
        im: source RGBA image.
        target: longest-side pixel count after downscale.
        pal: palette image to quantize onto (per-image or shared).
        alpha_threshold: if set, binarize alpha at this cutoff.
        upscale: integer NN upscale factor applied last.
    Returns:
        the pixelized RGBA image.
    """
    out = downscale(im, target)
    if alpha_threshold is not None:
        out = binarize_alpha(out, alpha_threshold)
    out = quantize_rgb(out, pal)
    out = upscale_nn(out, upscale)
    return out


def pixelize_set(
    paths: Sequence[str],
    target: int,
    colors: int,
    shared_palette: bool = True,
    alpha_threshold: Optional[int] = None,
    upscale: int = 1,
    out_dir: Optional[str] = None,
) -> List[str]:
    """Pixelize a set of images, optionally with one shared palette across the set.

    Args:
        paths: input PNG paths.
        target: longest-side pixel count.
        colors: palette size.
        shared_palette: build one palette from the whole set (cohesion) vs per-image.
        alpha_threshold: optional hard-edge alpha cutoff.
        upscale: integer NN upscale factor.
        out_dir: where to write; defaults to overwriting inputs in place.
    Returns:
        list of written output paths.
    """
    ims = [load_rgba(p) for p in paths]
    # Downscale first so the palette is built from the pixel-grid colors.
    small = [downscale(im, target) for im in ims]
    at = alpha_threshold if alpha_threshold is not None else 0
    arrays = [np.array(im) for im in small]

    written: List[str] = []
    shared = build_palette(arrays, colors, at) if shared_palette else None
    for src, im in zip(paths, ims):
        pal = shared if shared is not None else build_palette(
            [np.array(downscale(im, target))], colors, at
        )
        out = pixelize_image(im, target, pal, alpha_threshold, upscale)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            dst = os.path.join(out_dir, os.path.basename(src))
        else:
            dst = src
        out.save(dst)
        written.append(dst)
    return written


def _expand_inputs(pattern: str) -> List[str]:
    if os.path.isdir(pattern):
        pattern = os.path.join(pattern, "*.png")
    return sorted(glob.glob(pattern))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Pixelize game asset PNGs (deterministic).")
    ap.add_argument("--in", dest="inp", required=True, help="input dir or glob")
    ap.add_argument("--target", type=int, default=64, help="longest-side pixels (32/48/64)")
    ap.add_argument("--colors", type=int, default=16, help="palette size")
    ap.add_argument("--shared-palette", action="store_true", help="one palette for the set")
    ap.add_argument("--alpha-threshold", type=int, default=128,
                    help="binarize alpha at this cutoff (0-255); default 128 = hard-edge dot art")
    ap.add_argument("--soft-alpha", action="store_true",
                    help="keep soft (anti-aliased) alpha — disables the hard-edge binarize")
    ap.add_argument("--upscale", type=int, default=1, help="integer NN upscale factor")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite the source files (default: write to <indir>/pixelized/)")
    ap.add_argument("--out", default=None, help="output dir (default: <indir>/pixelized/)")
    args = ap.parse_args(argv)

    paths = _expand_inputs(args.inp)
    if not paths:
        print(f"ERROR: no PNG inputs matched '{args.inp}'", file=sys.stderr)
        return 1
    if not 2 <= args.colors <= 256:  # m3: clear message instead of a raw Pillow ValueError
        print(f"ERROR: --colors는 2..256 범위여야 합니다(받음 {args.colors}) / "
              f"--colors must be 2..256 (got {args.colors})", file=sys.stderr)
        return 1

    alpha_threshold = None if args.soft_alpha else args.alpha_threshold
    # M1: never overwrite the (expensive) source generations by default.
    if args.in_place:
        out_dir = None  # the only path that overwrites sources in place
    elif args.out:
        out_dir = args.out
    else:
        input_dir = args.inp if os.path.isdir(args.inp) else os.path.dirname(paths[0])
        out_dir = os.path.join(input_dir, "pixelized")

    written = pixelize_set(
        paths, args.target, args.colors, args.shared_palette,
        alpha_threshold, args.upscale, out_dir,
    )
    for p in written:
        print(f"pixelized: {p}")
    print(f"done: {len(written)} image(s), target={args.target}px, colors={args.colors}, "
          f"shared_palette={args.shared_palette}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
