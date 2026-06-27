#!/usr/bin/env python3
"""Tests for pixelize.py — deterministic pixelization (S3 completion criterion)."""

import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pixelize  # noqa: E402


def _noisy_rgba(size=256, transparent_border=32):
    """A many-colored gradient image with a fully transparent border."""
    arr = np.zeros((size, size, 4), dtype="uint8")
    xs = np.linspace(0, 255, size, dtype="uint8")
    arr[..., 0] = xs[None, :]
    arr[..., 1] = xs[:, None]
    arr[..., 2] = (xs[None, :] // 2 + xs[:, None] // 2).astype("uint8")
    arr[..., 3] = 255
    b = transparent_border
    arr[:b, :, 3] = 0
    arr[-b:, :, 3] = 0
    arr[:, :b, 3] = 0
    arr[:, -b:, 3] = 0
    return Image.fromarray(arr, "RGBA")


def _opaque_unique_colors(im):
    arr = np.array(im.convert("RGBA"))
    opaque = arr[arr[..., 3] > 0][:, :3]
    return {tuple(c) for c in opaque}


class TestDownscale(unittest.TestCase):
    def test_longest_side_equals_target(self):
        im = _noisy_rgba(256)
        out = pixelize.downscale(im, 32)
        self.assertEqual(max(out.size), 32)

    def test_aspect_preserved(self):
        im = Image.new("RGBA", (200, 100))
        out = pixelize.downscale(im, 50)
        self.assertEqual(out.size, (50, 25))


class TestPixelizeSet(unittest.TestCase):
    def test_output_size_and_palette_cap(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "01-a.png")
            _noisy_rgba(256).save(p)
            out_dir = os.path.join(d, "out")
            written = pixelize.pixelize_set([p], target=32, colors=8,
                                            shared_palette=False, out_dir=out_dir)
            self.assertEqual(len(written), 1)
            out = Image.open(written[0])
            self.assertEqual(max(out.size), 32)
            self.assertLessEqual(len(_opaque_unique_colors(out)), 8)

    def test_alpha_threshold_makes_binary_alpha(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "01-a.png")
            _noisy_rgba(256, transparent_border=40).save(p)
            out_dir = os.path.join(d, "out")
            written = pixelize.pixelize_set([p], target=48, colors=16,
                                            shared_palette=False,
                                            alpha_threshold=128, out_dir=out_dir)
            a = np.array(Image.open(written[0]))[..., 3]
            self.assertTrue(set(np.unique(a)).issubset({0, 255}))

    def test_shared_palette_is_identical_across_set(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i, shade in enumerate((40, 200)):
                arr = np.full((64, 64, 4), shade, dtype="uint8")
                arr[..., 3] = 255
                arr[..., 0] = (i * 90) % 256
                pth = os.path.join(d, f"0{i}-x.png")
                Image.fromarray(arr, "RGBA").save(pth)
                paths.append(pth)
            arrays = [np.array(pixelize.downscale(pixelize.load_rgba(p), 32)) for p in paths]
            pal = pixelize.build_palette(arrays, colors=8)
            # Every output color must be drawn from the one shared palette.
            out_dir = os.path.join(d, "out")
            written = pixelize.pixelize_set(paths, target=32, colors=8,
                                            shared_palette=True, out_dir=out_dir)
            palette_colors = set()
            pal_rgb = pal.convert("RGB").getcolors(maxcolors=100000) or []
            for _, c in pal_rgb:
                palette_colors.add(c)
            for w in written:
                self.assertTrue(_opaque_unique_colors(Image.open(w)).issubset(palette_colors))

    def test_upscale_integer_factor(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "01-a.png")
            _noisy_rgba(128).save(p)
            out_dir = os.path.join(d, "out")
            written = pixelize.pixelize_set([p], target=32, colors=8,
                                            shared_palette=False, upscale=4,
                                            out_dir=out_dir)
            self.assertEqual(max(Image.open(written[0]).size), 128)


if __name__ == "__main__":
    unittest.main()
