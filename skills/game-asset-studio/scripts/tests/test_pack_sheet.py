#!/usr/bin/env python3
"""Tests for pack_sheet.py — uniform-grid packing + manifest (S4 completion criterion)."""

import json
import os
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pack_sheet  # noqa: E402


def _solid(size, color):
    return Image.new("RGBA", size, color)


class TestGridMath(unittest.TestCase):
    def test_auto_cols_near_square(self):
        self.assertEqual(pack_sheet.auto_cols(5), 3)
        self.assertEqual(pack_sheet.auto_cols(9), 3)
        self.assertEqual(pack_sheet.auto_cols(10), 4)

    def test_auto_cell_is_max_bbox(self):
        ims = [_solid((16, 24), "red"), _solid((32, 8), "blue")]
        self.assertEqual(pack_sheet.auto_cell(ims), (32, 24))


class TestPack(unittest.TestCase):
    def test_sheet_dims_and_frame_coords(self):
        images = [_solid((16, 16), (i * 40 % 256, 0, 0, 255)) for i in range(5)]
        names = [f"s{i}" for i in range(5)]
        sheet, manifest = pack_sheet.pack(images, names, cell=(16, 16), cols=3, padding=0)
        # 5 sprites, 3 cols -> 2 rows; 48x32 sheet.
        self.assertEqual(sheet.size, (48, 32))
        self.assertEqual(manifest["rows"], 2)
        self.assertEqual(manifest["count"], 5)
        # index 4 -> col=1, row=1 -> (16, 16)
        f4 = manifest["frames"][4]
        self.assertEqual((f4["x"], f4["y"], f4["w"], f4["h"]), (16, 16, 16, 16))
        self.assertEqual(f4["name"], "s4")
        # index 0 at origin
        self.assertEqual((manifest["frames"][0]["x"], manifest["frames"][0]["y"]), (0, 0))

    def test_padding_affects_origin_and_size(self):
        images = [_solid((10, 10), "green") for _ in range(2)]
        sheet, manifest = pack_sheet.pack(images, ["a", "b"], cell=(10, 10),
                                          cols=2, padding=2)
        # sheet_w = 2 + 2*(10+2) = 26 ; sheet_h = 2 + 1*(10+2) = 14
        self.assertEqual(sheet.size, (26, 14))
        self.assertEqual(manifest["frames"][0]["x"], 2)
        self.assertEqual(manifest["frames"][1]["x"], 2 + (10 + 2))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            pack_sheet.pack([], [])


class TestNameOf(unittest.TestCase):
    def test_strips_numeric_order_prefix(self):
        self.assertEqual(pack_sheet._name_of("/x/01-sword.png"), "sword")
        self.assertEqual(pack_sheet._name_of("/x/potion.png"), "potion")
        self.assertEqual(pack_sheet._name_of("/x/12-fire-staff.png"), "fire-staff")


class TestCli(unittest.TestCase):
    def test_end_to_end_writes_sheet_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            sprites = os.path.join(d, "sprites")
            os.makedirs(sprites)
            for i, col in enumerate(["red", "green", "blue", "yellow"]):
                _solid((32, 32), col).save(os.path.join(sprites, f"0{i}-{col}.png"))
            out = os.path.join(d, "sheet.png")
            man = os.path.join(d, "manifest.json")
            rc = pack_sheet.main(["--in", sprites, "--cell", "32x32", "--cols", "2",
                                  "--out", out, "--manifest", man])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(out))
            data = json.load(open(man, encoding="utf-8"))
            self.assertEqual(data["count"], 4)
            self.assertEqual(data["columns"], 2)
            self.assertEqual(data["rows"], 2)
            self.assertEqual(data["image"], "sheet.png")
            self.assertEqual(Image.open(out).size, (64, 64))


if __name__ == "__main__":
    unittest.main()
