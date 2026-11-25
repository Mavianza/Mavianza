from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.profile_stats import (
    DAY,
    WINDOW,
    StatsError,
    language_rows,
    render_languages,
    summarize,
    sync,
)


NOW = datetime(2026, 11, 26, 1, 42, tzinfo=timezone.utc)
NS = {"svg": "http://www.w3.org/2000/svg"}


def repository(name, *, fork=False, private=False, owner="Mavianza"):
    return {"name": name, "fork": fork, "private": private, "owner": {"login": owner}}


class FakeGitHub:
    def __init__(self, counts, pages, languages):
        self.counts = counts
        self.pages = pages
        self.languages = languages
        self.language_requests = []

    def request(self, path, body=None):
        if path == "/graphql":
            first = NOW.date() - (WINDOW - 1) * DAY
            days = [
                {"date": (first + i * DAY).isoformat(), "contributionCount": count}
                for i, count in enumerate(self.counts)
            ]
            return {"data": {"user": {"contributionsCollection": {
                "contributionCalendar": {"weeks": [
                    {"contributionDays": days[i:i + 7]} for i in range(0, len(days), 7)
                ]},
            }}}}
        if path.startswith("/users/"):
            return self.pages.get(int(path.rsplit("=", 1)[1]), [])
        name = path.split("/")[-2]
        self.language_requests.append(name)
        result = self.languages[name]
        if isinstance(result, Exception):
            raise result
        return result


class ProfileStatsTest(unittest.TestCase):
    def test_update_renders_both_cards_and_filters_repositories(self):
        counts = [0] * (WINDOW - 5) + [3, 1, 0, 4, 0]
        archived_forks = [repository(f"fork-{i}", fork=True) for i in range(99)]
        pages = {
            1: [repository("web"), *archived_forks],
            2: [
                repository("media"), repository("MaViAnZa"),
                repository("private", private=True), repository("another", owner="other"),
                repository("without-code"),
            ],
        }
        api = FakeGitHub(counts, pages, {
            "web": {"JavaScript": 50, "CSS": 10}, "media": {"Java": 40},
            "without-code": {},
        })
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            sync(api, "Mavianza", NOW, directory)
            streak = ET.parse(directory / "streak.svg").getroot()
            languages = ET.parse(directory / "bahasa.svg").getroot()
            self.assertEqual(
                streak.findtext("svg:desc", namespaces=NS),
                "Streak aktif 1 hari. Rekor 2 hari. 8 kontribusi dalam 365 hari.",
            )
            self.assertEqual(
                languages.findtext("svg:desc", namespaces=NS),
                "JavaScript 50,0%. Java 40,0%. CSS 10,0%",
            )
            self.assertIn("2 repo dengan data bahasa", "".join(languages.itertext()))
            self.assertEqual(api.language_requests, ["web", "media", "without-code"])

    def test_failed_request_preserves_previous_cards(self):
        api = FakeGitHub([1] * WINDOW, {1: [repository("web")]}, {
            "web": OSError("GitHub sedang tidak tersedia"),
        })
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in ("streak.svg", "bahasa.svg"):
                (directory / name).write_text(f"previous {name}", encoding="utf-8")
            with self.assertRaises(OSError):
                sync(api, "Mavianza", NOW, directory)
            for name in ("streak.svg", "bahasa.svg"):
                self.assertEqual((directory / name).read_text(), f"previous {name}")

    def test_missing_calendar_day_does_not_produce_false_zero(self):
        api = FakeGitHub([1] * (WINDOW - 1), {}, {})
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            with self.assertRaises(StatsError):
                sync(api, "Mavianza", NOW, directory)
            self.assertEqual(list(directory.iterdir()), [])

    def test_streak_today_yesterday_and_broken(self):
        self.assertEqual((summarize([1, 2, 1]).current, summarize([1, 2, 1]).longest), (3, 3))
        self.assertEqual(summarize([1, 2, 0]).current, 2)
        self.assertEqual(summarize([1, 2, 0, 0]).current, 0)

    def test_languages_are_deterministic_and_escape_svg(self):
        sizes = Counter({"C++": 21, "A&B": 20, "C": 13, "D": 8, "E": 4, "F": 1})
        self.assertEqual(language_rows(sizes)[-1], ("Lainnya", 5))
        self.assertEqual(language_rows(Counter({"Zig": 1, "Go": 1})), [("Go", 1), ("Zig", 1)])
        rendered = ET.fromstring(render_languages(sizes, 1, NOW.date()))
        self.assertIn("A&B", rendered.findtext("svg:desc", namespaces=NS))

    def test_empty_repository_data_is_labeled(self):
        rendered = ET.fromstring(render_languages(Counter(), 0, NOW.date()))
        self.assertIn("Belum ada bahasa yang dihitung GitHub.", "".join(rendered.itertext()))
