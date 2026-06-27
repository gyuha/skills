#!/usr/bin/env python3
"""Input/resource guard tests (task 9): M2 sheet-size · M3 cost cap · M4 slugify CJK · M5 empty · m3 colors."""

import json
import os
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pack_sheet  # noqa: E402
import pixelize  # noqa: E402
import generate  # noqa: E402


class TestM2SheetSizeGuard(unittest.TestCase):
    def test_oversized_sheet_refused(self):
        imgs = [Image.new("RGBA", (1024, 1024), (255, 0, 0, 255)) for _ in range(4)]
        with self.assertRaises(ValueError):
            pack_sheet.pack(imgs, ["a", "b", "c", "d"], cell=(1024, 1024), cols=4,
                            max_size=2048)

    def test_within_budget_ok(self):
        imgs = [Image.new("RGBA", (32, 32)) for _ in range(4)]
        sheet, _ = pack_sheet.pack(imgs, ["a", "b", "c", "d"], cell=(32, 32), cols=2,
                                   max_size=4096)
        self.assertEqual(sheet.size, (64, 64))


class TestM3CostCap(unittest.TestCase):
    def _spec(self, d, n):
        spec = {"out_dir": os.path.join(d, "o"), "style_anchor": "pixel",
                "transparent": False,
                "items": [{"name": f"i{k}", "prompt": "a thing"} for k in range(n)]}
        p = os.path.join(d, "spec.json")
        json.dump(spec, open(p, "w"))
        return p

    def test_over_cap_refused_without_yes(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._spec(d, 21)  # default cap 20
            self.assertNotEqual(generate.main(["--spec", p, "--dry-run"]), 0)

    def test_over_cap_allowed_with_yes(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._spec(d, 21)
            self.assertEqual(generate.main(["--spec", p, "--dry-run", "--yes"]), 0)


class TestM4SlugifyCJK(unittest.TestCase):
    def test_preserves_cjk_and_accented(self):
        self.assertNotEqual(generate.slugify("日本刀"), "asset")
        self.assertNotEqual(generate.slugify("中国剑"), "asset")
        # distinct CJK names do not collapse to the same slug
        self.assertNotEqual(generate.slugify("日本刀"), generate.slugify("中国剑"))
        self.assertNotEqual(generate.slugify("café"), "caf")  # accented char kept

    def test_still_safe_for_ascii(self):
        self.assertEqual(generate.slugify("Gold Coin"), "gold-coin")


class TestM5EmptyItems(unittest.TestCase):
    def test_empty_items_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as d:
            spec = {"out_dir": os.path.join(d, "o"), "items": []}
            p = os.path.join(d, "spec.json")
            json.dump(spec, open(p, "w"))
            self.assertNotEqual(generate.main(["--spec", p, "--dry-run"]), 0)


class Testm3ColorsCap(unittest.TestCase):
    def test_colors_over_256_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            spr = os.path.join(d, "s")
            os.makedirs(spr)
            Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(os.path.join(spr, "01-x.png"))
            rc = pixelize.main(["--in", spr, "--colors", "512", "--out", os.path.join(d, "o")])
            self.assertNotEqual(rc, 0)

    def test_colors_in_range_ok(self):
        with tempfile.TemporaryDirectory() as d:
            spr = os.path.join(d, "s")
            os.makedirs(spr)
            Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(os.path.join(spr, "01-x.png"))
            rc = pixelize.main(["--in", spr, "--colors", "16", "--out", os.path.join(d, "o")])
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
