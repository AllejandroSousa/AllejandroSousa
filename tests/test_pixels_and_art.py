import struct
import unittest
import zlib

from animation import hero_poses, theme
from animation.logos import SIZE, all_logos
from animation.pixels import grid_from_cells, validate_grid
from animation.png import MAX_COLORS, build_palette, encode_png


class ValidateGridTest(unittest.TestCase):
    def test_rejects_ragged_rows_with_widths_in_message(self):
        with self.assertRaisesRegex(ValueError, r"\[1, 2\]"):
            validate_grid(["R", "RR"], {"R": "#f00"}, "ragged")

    def test_rejects_unknown_keys(self):
        with self.assertRaisesRegex(ValueError, "'Z'"):
            validate_grid(["Z"], {"R": "#f00"}, "unknown")


class GridFromCellsTest(unittest.TestCase):
    def test_places_cells_and_leaves_rest_transparent(self):
        self.assertEqual(grid_from_cells(3, 2, {(2, 1): "R"}), ["...", "..R"])


class LogosTest(unittest.TestCase):
    def test_six_logos_in_swing_order_all_16px(self):
        logos = all_logos()
        self.assertEqual([l.name for l in logos], ["ruby", "python", "javascript", "cpp", "huggingface", "appsec"])
        for logo in logos:
            validate_grid(logo.grid, logo.palette, logo.name)
            self.assertEqual((len(logo.grid), len(logo.grid[0])), (SIZE, SIZE), logo.name)


class ThemeTest(unittest.TestCase):
    def test_mix_endpoints_and_midpoint(self):
        self.assertEqual(theme.mix("#102030", "#ffffff", 0), "#102030")
        self.assertEqual(theme.mix("#102030", "#ffffff", 1), "#ffffff")
        self.assertEqual(theme.mix("#000000", "#ffffff", 0.5), "#808080")

    def test_mix_rejects_short_hex(self):
        with self.assertRaisesRegex(ValueError, "'#fff'"):
            theme.mix("#fff", "#000000", 0.5)


class PngTest(unittest.TestCase):
    def _chunks(self, data: bytes):
        pos, chunks = 8, {}
        while pos < len(data):
            (length,) = struct.unpack(">I", data[pos : pos + 4])
            kind = data[pos + 4 : pos + 8]
            chunks[kind] = data[pos + 8 : pos + 8 + length]
            pos += 12 + length
        return chunks

    def test_round_trips_pixels_through_palette(self):
        rows = [bytes([255, 0, 0, 0, 0, 255]), bytes([0, 0, 255, 255, 0, 0])]
        chunks = self._chunks(encode_png(2, rows))
        palette = chunks[b"PLTE"]
        raw = zlib.decompress(chunks[b"IDAT"])
        decoded = [palette[i * 3 : i * 3 + 3] for i in (raw[1], raw[2], raw[4], raw[5])]
        self.assertEqual(decoded, [rows[0][:3], rows[0][3:], rows[1][:3], rows[1][3:]])

    def test_more_than_256_colours_map_to_nearest_kept(self):
        row = b"".join(bytes([i % 256, i // 256, 0]) for i in range(300))
        palette, index = build_palette([row])
        self.assertEqual(len(palette), MAX_COLORS)
        self.assertEqual(len(index), 300)

    def test_rejects_rows_of_wrong_length(self):
        with self.assertRaisesRegex(ValueError, "expected 6"):
            encode_png(2, [b"\x00\x00\x00"])


class PosesTest(unittest.TestCase):
    def test_every_pose_has_every_joint(self):
        for pose in (hero_poses.CROUCH, hero_poses.SWING_RIGHT, hero_poses.SWING_LEFT, hero_poses.SPREAD):
            self.assertEqual(set(pose), set(hero_poses.JOINTS))

    def test_mirror_swaps_sides_and_flips_x(self):
        mirrored = hero_poses.mirror(hero_poses.SWING_RIGHT)
        x, y, z = hero_poses.SWING_RIGHT["r_hand"]
        self.assertEqual(mirrored["l_hand"], (-x, y, z))

    def test_blend_endpoints(self):
        a, b = hero_poses.CROUCH, hero_poses.SPREAD
        for u, expected in ((0.0, a), (1.0, b)):
            blended = hero_poses.blend(a, b, u)
            for joint, point in expected.items():
                for got, want in zip(blended[joint], point):
                    self.assertAlmostEqual(got, want)


if __name__ == "__main__":
    unittest.main()
