from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts.render_banner import banner


SVG = "{http://www.w3.org/2000/svg}"
ROOT = Path(__file__).resolve().parents[1]


def animations_in(image, phase):
    return [
        animation
        for element in image.iter()
        if phase in element.get("class", "").split()
        for animation in element
        if animation.tag in (f"{SVG}animate", f"{SVG}animateMotion")
    ]


def time_seconds(animation, attribute):
    return float(animation.get(attribute).removesuffix("s"))


class BannerTest(unittest.TestCase):
    def test_committed_assets_match_desktop_and_mobile_layouts(self):
        for mobile, name, dimensions in (
            (False, "peta-minat.svg", ("800", "318")),
            (True, "peta-minat-mobile.svg", ("400", "464")),
        ):
            with self.subTest(mobile=mobile):
                document = banner(mobile=mobile)
                self.assertEqual((ROOT / "assets" / name).read_text(encoding="utf-8"), document)
                image = ET.fromstring(document)
                self.assertEqual((image.get("width"), image.get("height")), dimensions)
                self.assertEqual(image.findtext(f"{SVG}title"), "Alfath Mavianza")
                self.assertEqual(image.get("aria-labelledby"), "title description")

    def test_opening_plays_once_before_the_idle_loops(self):
        for mobile in (False, True):
            with self.subTest(mobile=mobile):
                image = ET.fromstring(banner(mobile=mobile))
                opening = animations_in(image, "opening")
                idle = animations_in(image, "idle")
                opening_end = max(time_seconds(a, "begin") + time_seconds(a, "dur") for a in opening)
                self.assertLess(opening_end, 3)
                self.assertEqual(sum(a.tag == f"{SVG}animateMotion" for a in opening), 2)
                self.assertTrue(all(a.get("repeatCount") is None for a in opening))
                self.assertEqual(len(idle), 2)
                self.assertEqual(len(set(a.get("dur") for a in idle)), 2)
                for animation in idle:
                    self.assertEqual(animation.get("repeatCount"), "indefinite")
                    self.assertGreater(time_seconds(animation, "begin"), opening_end)

    def test_every_animation_is_hidden_with_reduced_motion(self):
        for mobile in (False, True):
            image = ET.fromstring(banner(mobile=mobile))
            animations = image.findall(f".//{SVG}animate") + image.findall(f".//{SVG}animateMotion")
            self.assertCountEqual(animations, animations_in(image, "motion-only"))
            style = image.findtext(f"{SVG}style")
            self.assertIn("prefers-reduced-motion: reduce", style)
            self.assertIn(".motion-only { display: none; }", style)

    def test_readme_disclosure_can_hide_both_banner_sizes(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        disclosure = readme.split("<details open>", 1)[1].split("</details>", 1)[0]
        self.assertRegex(disclosure, r'<summary aria-label="[^"]+" title="[^"]+">&#160;</summary>')
        self.assertIn('src="assets/peta-minat.svg"', disclosure)
        self.assertIn('srcset="assets/peta-minat-mobile.svg"', disclosure)
        self.assertNotIn("assets/streak.svg", disclosure)
