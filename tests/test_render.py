import unittest

from animation import choreography, theme
from animation.camera import Camera
from animation.fog import fogged
from animation.frame import FRAME_HEIGHT, FRAME_WIDTH, render_frame
from animation.hero3d import Placement, draw_hero3d
from animation.hero_poses import CROUCH
from animation.raster import Canvas, hex_to_rgb
from animation.screens import BULB_FRAME, BULB_ON, CODE_PATTERN_ROWS, CODE_ROW, WallScreen, screen_pixel
from animation.sheet import flip_keyframes
from animation.suit import NAVY, RED, back_spider
from animation.world import PERIOD, avenue, visible_boxes


class CameraTest(unittest.TestCase):
    def test_point_on_axis_lands_on_horizon_centre(self):
        camera = Camera(0, 10, 0)
        self.assertEqual(camera.project(0, 10, 50), (FRAME_WIDTH / 2, camera.horizon))

    def test_point_behind_near_plane_is_hidden(self):
        self.assertIsNone(Camera(0, 0, 10).project(0, 0, 10.5))


class RasterTest(unittest.TestCase):
    def test_dither_level_half_covers_half_the_pixels(self):
        canvas = Canvas(4, 4, (0, 0, 0))
        canvas.fill_rect(0, 0, 4, 4, (0, 0, 0), (255, 255, 255), 0.5)
        lit = sum(p == (255, 255, 255) for row in canvas.pixels for p in row)
        self.assertEqual(lit, 8)

    def test_hex_to_rgb_rejects_bad_input(self):
        with self.assertRaisesRegex(ValueError, "'red'"):
            hex_to_rgb("red")


class FogTest(unittest.TestCase):
    def test_near_is_untouched_and_far_is_fog(self):
        base, _, level = fogged("#000000", 0.0)
        self.assertEqual((base, level), ((0, 0, 0), 0.0))
        far_base, far_other, _ = fogged("#000000", theme.FOG_FAR * 2)
        self.assertEqual(far_other, hex_to_rgb(theme.HORIZON_FOG))


class WorldTest(unittest.TestCase):
    def test_each_logo_appears_exactly_once_per_period(self):
        names = [s.logo.name for b in avenue() for s in b.screens if s.kind == "logo"]
        self.assertEqual(sorted(names), sorted(["ruby", "python", "javascript", "cpp", "huggingface", "appsec"]))

    def test_city_repeats_every_period(self):
        city = avenue()
        here = visible_boxes(city, 10.0, 200.0)
        later = visible_boxes(city, 10.0 + PERIOD, 200.0)
        self.assertEqual([(b.z0 + PERIOD, b.height) for b in here], [(b.z0, b.height) for b in later])


class ScreensTest(unittest.TestCase):
    def setUp(self):
        self.screen = WallScreen(0, 10, 10, 20, "code", "#3f8f9c", seed=5, bulbs=True)

    def test_bulb_border_surrounds_the_face(self):
        self.assertIn(screen_pixel((self.screen,), -0.3, 15, 0, 0), (BULB_ON, BULB_FRAME))
        self.assertIsNone(screen_pixel((self.screen,), -2, 15, 0, 0))

    def test_code_scroll_repeats_after_one_pattern(self):
        period = CODE_PATTERN_ROWS * CODE_ROW
        for y in (11.2, 14.7, 18.9):
            for z in (0.5, 3.3, 7.1):
                self.assertEqual(screen_pixel((self.screen,), z, y, 3.0, 0),
                                 screen_pixel((self.screen,), z, y, 3.0 + period, 0))


class SuitTest(unittest.TestCase):
    def test_back_spider_has_body_and_legs_but_not_everywhere(self):
        self.assertTrue(back_spider(0.0, 0.0, 0.01))
        self.assertTrue(back_spider(0.12, 0.17, 0.01))
        self.assertFalse(back_spider(0.25, 0.0, 0.01))

    def test_hero_draws_red_navy_and_outline(self):
        canvas = Canvas(FRAME_WIDTH, FRAME_HEIGHT, (0, 0, 0))
        draw_hero3d(canvas, Camera(-0.8, 1.05, -2.0), CROUCH, Placement((0, 0, 0), yaw=-20))
        colours = {p for row in canvas.pixels for p in row}
        self.assertGreater(len(colours), 10)
        reds = [c for c in colours if c[0] > 2 * c[2] and c[0] > 60]
        navies = [c for c in colours if c[2] > c[0] and c[2] > 40]
        self.assertTrue(reds and navies, "expected both the red and the navy parts of the suit")
        self.assertTrue(RED != NAVY)


class ChoreographyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.times = choreography.sample_times() + [choreography.LOOP_SECONDS]
        cls.states = [choreography.hero_at(t) for t in cls.times]
        cls.cameras = choreography.camera_track(cls.times, cls.states)

    def test_loop_ends_exactly_where_it_started(self):
        self.assertEqual(self.cameras[0], self.cameras[-1])
        self.assertEqual(self.states[0], self.states[-1])

    def test_hero_travels_one_full_period(self):
        landed = choreography.hero_at(choreography.TRAVEL[1]).placement.position
        self.assertAlmostEqual(landed[2], choreography.HOME[2] + PERIOD)

    def test_hero_stays_in_shot(self):
        for t, state, camera in zip(self.times, self.states, self.cameras):
            screen = camera.project(*state.placement.position)
            self.assertIsNotNone(screen, f"hero behind camera at t={t:.2f}")
            x, y = screen
            self.assertTrue(0 <= x <= FRAME_WIDTH and 0 <= y <= FRAME_HEIGHT + 10, f"({x:.0f},{y:.0f}) at t={t:.2f}")

    def test_hero_slows_down_before_settling_on_the_perch(self):
        # Regression: the landing used to end at ~2 units/frame and freeze on the
        # next frame, a hard stop right before the loop restarts.
        landing = [s.placement.position for t, s in zip(self.times, self.states)
                   if choreography.TRAVEL[1] - 0.5 <= t < choreography.TRAVEL[1]]
        landing.append(choreography.landing_home())
        steps = [sum((a - b) ** 2 for a, b in zip(p, q)) ** 0.5 for p, q in zip(landing, landing[1:])]
        self.assertEqual(steps, sorted(steps, reverse=True), f"not decelerating: {steps}")
        self.assertLess(steps[-1], 0.3, f"arrives too fast: {steps}")

    def test_scroll_completes_whole_patterns(self):
        total = choreography.scroll_at(choreography.LOOP_SECONDS)
        self.assertEqual(total % (CODE_PATTERN_ROWS * CODE_ROW), 0)

    def test_first_and_wrapped_frames_render_identically(self):
        city = avenue()
        first = render_frame(self.cameras[0], city, self.states[0].view(), choreography.scroll_at(0))
        last = render_frame(self.cameras[-1], city, self.states[-1].view(),
                            choreography.scroll_at(choreography.LOOP_SECONDS))
        self.assertEqual(first.pixels, last.pixels)

    def test_time_outside_loop_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the loop"):
            choreography.hero_at(choreography.LOOP_SECONDS + 1)


class SheetTest(unittest.TestCase):
    def test_keyframes_only_where_the_frame_changes(self):
        css = flip_keyframes([0, 0, 1, 1], 1.0)
        self.assertEqual(css.count("translateY"), 3)
        self.assertIn("50%{transform:translateY(-100px)}", css)


if __name__ == "__main__":
    unittest.main()
