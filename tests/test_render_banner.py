from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from scripts.render_banner import banner


SVG = "{http://www.w3.org/2000/svg}"
ROOT = Path(__file__).resolve().parents[1]


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

    def test_motion_is_brief_and_reduction_is_supported(self):
        for mobile in (False, True):
            image = ET.fromstring(banner(mobile=mobile))
            pulses = image.findall(f".//{SVG}animateMotion")
            self.assertEqual(len(pulses), 2)
            for pulse in [*pulses, *image.findall(f".//{SVG}animate")]:
                start = float(pulse.get("begin").removesuffix("s"))
                duration = float(pulse.get("dur").removesuffix("s"))
                finish = start + duration
                self.assertLess(finish, 3)
                self.assertIsNone(pulse.get("repeatCount"))
            style = image.findtext(f"{SVG}style")
            self.assertIn("prefers-reduced-motion: reduce", style)
            self.assertIn(".motion-only { display: none; }", style)
