#!/usr/bin/env python3
"""Dot-art fidelity tests (task 8): C4 NEAREST packing · M6 hard-alpha default · M1 non-destructive."""

import os
import sys
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pixelize  # noqa: E402
import pack_sheet  # noqa: E402


def _few_color_sprite(size=8, colors=((220, 40, 40), (40, 200, 80), (60, 120, 240))):
    arr = np.zeros((size, size, 4), dtype="uint8")
    band = size // len(colors)
    for i, c in enumerate(colors):
        arr[i * band:(i + 1) * band, :, :3] = c
    arr[..., 3] = 255
    return Image.fromarray(arr, "RGBA")


def _opaque_colors(im):
    a = np.array(im.convert("RGBA"))
    return {tuple(c) for c in a[a[..., 3] > 0][:, :3]}


class TestC4ResampleNearest(unittest.TestCase):
    def test_default_nearest_preserves_palette_on_upscale(self):
        sprite = _few_color_sprite(8)
        src = len(_opaque_colors(sprite))
        cell = pack_sheet.fit_into_cell(sprite, (64, 64), "contain")  # default resample
        self.assertLessEqual(len(_opaque_colors(cell)), src)  # no interpolated colors

    def test_lanczos_interpolates_more_colors(self):
        sprite = _few_color_sprite(8)
        src = len(_opaque_colors(sprite))
        cell = pack_sheet.fit_into_cell(sprite, (64, 64), "contain",
                                        resample=Image.Resampling.LANCZOS)
        self.assertGreater(len(_opaque_colors(cell)), src)

    def test_pack_default_resample_is_nearest(self):
        sprite = _few_color_sprite(8)
        src = len(_opaque_colors(sprite))
        sheet, _ = pack_sheet.pack([sprite, sprite], ["a", "b"], cell=(64, 64), cols=2)
        self.assertLessEqual(len(_opaque_colors(sheet)), src)


class TestM6HardAlphaDefault(unittest.TestCase):
    def _soft_src(self, d):
        arr = np.zeros((128, 128, 4), dtype="uint8")
        arr[..., 0] = 200
        # graded alpha border (soft edge)
        for i in range(20):
            arr[i, :, 3] = arr[:, i, 3] = int(255 * i / 20)
        arr[20:108, 20:108, 3] = 255
        p = os.path.join(d, "01-x.png")
        Image.fromarray(arr, "RGBA").save(p)
        return p

    def test_default_pixelize_yields_binary_alpha(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            self._soft_src(d)
            out = os.path.join(d, "out")
            # main with NO --alpha-threshold → should default to hard alpha
            rc = pixelize.main(["--in", d, "--out", out, "--target", "48", "--colors", "8"])
            self.assertEqual(rc, 0)
            a = np.array(Image.open(os.path.join(out, "01-x.png")))[..., 3]
            self.assertTrue(set(np.unique(a)).issubset({0, 255}))

    def test_soft_alpha_flag_keeps_gradient(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            self._soft_src(d)
            out = os.path.join(d, "out")
            pixelize.main(["--in", d, "--out", out, "--target", "48",
                           "--colors", "8", "--soft-alpha"])
            a = np.array(Image.open(os.path.join(out, "01-x.png")))[..., 3]
            self.assertFalse(set(np.unique(a)).issubset({0, 255}))


class TestM1NonDestructive(unittest.TestCase):
    def _sprites(self, d):
        os.makedirs(d, exist_ok=True)
        for i in range(2):
            Image.new("RGBA", (256, 256), (i * 80, 0, 0, 255)).save(
                os.path.join(d, f"0{i}-s.png"))

    def test_default_does_not_overwrite_sources(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            spr = os.path.join(d, "sprites")
            self._sprites(spr)
            pixelize.main(["--in", spr, "--target", "32", "--colors", "8"])
            # originals untouched (still 256px)
            self.assertEqual(Image.open(os.path.join(spr, "00-s.png")).size, (256, 256))
            # output written to a separate pixelized/ dir
            self.assertTrue(os.path.exists(os.path.join(spr, "pixelized", "00-s.png")))
            self.assertEqual(
                max(Image.open(os.path.join(spr, "pixelized", "00-s.png")).size), 32)

    def test_in_place_overwrites(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            spr = os.path.join(d, "sprites")
            self._sprites(spr)
            pixelize.main(["--in", spr, "--target", "32", "--colors", "8", "--in-place"])
            self.assertEqual(max(Image.open(os.path.join(spr, "00-s.png")).size), 32)


if __name__ == "__main__":
    unittest.main()
