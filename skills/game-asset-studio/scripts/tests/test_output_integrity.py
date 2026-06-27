#!/usr/bin/env python3
"""Output-integrity tests (task 7): C2 generation reconciliation · m1 unique ids · m2 manifest dir."""

import json
import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pack_sheet  # noqa: E402
import generate  # noqa: E402


def _png(path, color):
    Image.new("RGBA", (32, 32), color).save(path)


def _partial_set(d):
    """sprites/ with item 2 (shield) MISSING + a generation.json listing all 3."""
    sprites = os.path.join(d, "sprites")
    os.makedirs(sprites)
    _png(os.path.join(sprites, "01-sword.png"), (255, 0, 0, 255))
    _png(os.path.join(sprites, "03-potion.png"), (0, 0, 255, 255))
    gen = {"items": [
        {"index": 0, "name": "sword", "file": "01-sword.png", "ok": True},
        {"index": 1, "name": "shield", "file": "02-shield.png", "ok": False},
        {"index": 2, "name": "potion", "file": "03-potion.png", "ok": True},
    ]}
    genp = os.path.join(d, "generation.json")
    with open(genp, "w", encoding="utf-8") as f:
        json.dump(gen, f)
    return sprites, genp


class TestC2Reconciliation(unittest.TestCase):
    def test_partial_refused_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            sprites, genp = _partial_set(d)
            out, man = os.path.join(d, "sheet.png"), os.path.join(d, "m.json")
            rc = pack_sheet.main(["--in", sprites, "--generation", genp,
                                  "--cell", "32x32", "--out", out, "--manifest", man])
            self.assertNotEqual(rc, 0)               # refuse, do not silently re-index
            self.assertFalse(os.path.exists(out))    # no partial artifact

    def test_allow_partial_keeps_index_with_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            sprites, genp = _partial_set(d)
            out, man = os.path.join(d, "sheet.png"), os.path.join(d, "m.json")
            rc = pack_sheet.main(["--in", sprites, "--generation", genp, "--allow-partial",
                                  "--cell", "32x32", "--cols", "3", "--out", out, "--manifest", man])
            self.assertEqual(rc, 0)
            data = json.load(open(man, encoding="utf-8"))
            self.assertEqual(data["count"], 3)
            # index 1 stays 'shield' (intended order preserved, not re-indexed to potion)
            self.assertEqual(data["frames"][1]["name"], "shield")
            self.assertEqual(data["frames"][2]["name"], "potion")
            # the shield cell is a transparent placeholder
            f1 = data["frames"][1]
            sheet = np.array(Image.open(out))
            cell = sheet[f1["y"]:f1["y"] + f1["h"], f1["x"]:f1["x"] + f1["w"], 3]
            self.assertTrue((cell == 0).all())

    def test_complete_set_unaffected(self):
        with tempfile.TemporaryDirectory() as d:
            sprites = os.path.join(d, "sprites")
            os.makedirs(sprites)
            for i, c in [(1, (255, 0, 0, 255)), (2, (0, 255, 0, 255))]:
                _png(os.path.join(sprites, f"0{i}-x.png"), c)
            gen = {"items": [{"index": 0, "name": "a", "file": "01-x.png", "ok": True},
                             {"index": 1, "name": "b", "file": "02-x.png", "ok": True}]}
            genp = os.path.join(d, "generation.json")
            json.dump(gen, open(genp, "w"))
            rc = pack_sheet.main(["--in", sprites, "--generation", genp, "--cell", "32x32",
                                  "--out", os.path.join(d, "s.png"), "--manifest", os.path.join(d, "m.json")])
            self.assertEqual(rc, 0)


class TestGenerationRecord(unittest.TestCase):
    def test_generate_writes_generation_json(self):
        with tempfile.TemporaryDirectory() as d:
            spec = {"out_dir": os.path.join(d, "a"), "style_anchor": "pixel",
                    "transparent": False,
                    "items": [{"name": "sword", "prompt": "a sword"},
                              {"name": "shield", "prompt": "a shield"}]}
            generate.generate_batch(spec, dry_run=True)
            genp = os.path.join(os.path.abspath(spec["out_dir"]), "generation.json")
            self.assertTrue(os.path.exists(genp))
            gen = json.load(open(genp, encoding="utf-8"))
            self.assertEqual([it["name"] for it in gen["items"]], ["sword", "shield"])
            self.assertEqual([it["index"] for it in gen["items"]], [0, 1])


class TestM1UniqueIds(unittest.TestCase):
    def test_duplicate_names_get_distinct_ids(self):
        img = Image.new("RGBA", (16, 16), (255, 0, 0, 255))
        _, manifest = pack_sheet.pack([img, img], ["sword", "sword"],
                                      ids=["01-sword", "02-sword"], cell=(16, 16), cols=2)
        ids = [f["id"] for f in manifest["frames"]]
        self.assertEqual(len(set(ids)), 2)


class TestM2ManifestDir(unittest.TestCase):
    def test_manifest_parent_dir_created(self):
        with tempfile.TemporaryDirectory() as d:
            sprites = os.path.join(d, "sprites")
            os.makedirs(sprites)
            _png(os.path.join(sprites, "01-x.png"), (255, 0, 0, 255))
            rc = pack_sheet.main(["--in", sprites, "--cell", "32x32",
                                  "--out", os.path.join(d, "out", "sheet.png"),
                                  "--manifest", os.path.join(d, "nope", "m.json")])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(d, "nope", "m.json")))


if __name__ == "__main__":
    unittest.main()
