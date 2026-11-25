"""Generate the two profile images from GitHub's calendar and language APIs."""

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen


DAY = timedelta(days=1)
WINDOW = 365
PAGE_SIZE = 100
CARD_WIDTH = 370
CARD_HEIGHT = 214
ASSETS = Path(__file__).resolve().parents[1] / "assets"
CALENDAR_QUERY = """
query ProfileCalendar($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


class StatsError(RuntimeError):
    pass


class GitHub:
    def __init__(self, token: str):
        self.token = token

    def request(self, path: str, body: dict | None = None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            f"https://api.github.com{path}",
            data=data,
            headers={
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "mavianza-profile-stats",
            },
        )
        # A redirect to a different request must not carry this credential.
        request.add_unredirected_header("Authorization", f"Bearer {self.token}")
        with urlopen(request, timeout=20) as response:
            return json.load(response)


@dataclass(frozen=True)
class Activity:
    total: int
    current: int
    longest: int
    recent: tuple[int, ...]


def contribution_counts(api: GitHub, login: str, now: datetime) -> list[int]:
    today = now.date()
    first = today - (WINDOW - 1) * DAY
    result = api.request("/graphql", {
        "query": CALENDAR_QUERY,
        "variables": {
            "login": login,
            "from": f"{first.isoformat()}T00:00:00Z",
            "to": now.isoformat(timespec="seconds"),
        },
    })
    user = (result.get("data") or {}).get("user")
    if result.get("errors") or not user:
        raise StatsError("GitHub tidak mengembalikan kalender kontribusi.")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    by_date = {}
    for week in calendar["weeks"]:
        for entry in week["contributionDays"]:
            day = date.fromisoformat(entry["date"])
            if not first <= day <= today:
                continue
            count = entry["contributionCount"]
            if day in by_date or type(count) is not int or count < 0:
                raise StatsError("Kalender kontribusi berisi data yang tidak valid.")
            by_date[day] = count

    if len(by_date) != WINDOW:
        raise StatsError("Kalender kontribusi belum memuat seluruh rentang tanggal.")
    return [by_date[first + i * DAY] for i in range(WINDOW)]


def summarize(counts: list[int]) -> Activity:
    run = longest = 0
    for count in counts:
        run = run + 1 if count else 0
        longest = max(longest, run)

    # Hari UTC yang sedang berjalan boleh belum memiliki kontribusi.
    closed = counts if counts[-1] else counts[:-1]
    current = 0
    for count in reversed(closed):
        if not count:
            break
        current += 1
    return Activity(sum(counts), current, longest, tuple(counts[-30:]))


def public_languages(api: GitHub, login: str) -> tuple[Counter, int]:
    totals = Counter()
    seen: set[str] = set()
    language_repos = 0
    owner = login.casefold()
    for page in range(1, 201):
        repos = api.request(
            f"/users/{quote(login, safe='')}/repos?type=owner&sort=full_name"
            f"&per_page={PAGE_SIZE}&page={page}"
        )
        if not isinstance(repos, list):
            raise StatsError("Daftar repositori publik tidak valid.")
        for repo in repos:
            name = repo["name"]
            if (
                repo["owner"]["login"].casefold() != owner
                or repo["private"]
                or repo["fork"]
                or name.casefold() == owner
            ):
                continue
            if name.casefold() in seen:
                raise StatsError("Daftar repositori berubah saat sinkronisasi.")
            seen.add(name.casefold())

            path = f"/repos/{quote(login, safe='')}/{quote(name, safe='')}/languages"
            sizes = api.request(path)
            if not isinstance(sizes, dict) or any(
                type(size) is not int or size < 0 for size in sizes.values()
            ):
                raise StatsError("GitHub mengembalikan data bahasa yang tidak valid.")
            positive_sizes = {name: size for name, size in sizes.items() if size > 0}
            if positive_sizes:
                language_repos += 1
                totals.update(positive_sizes)
        if len(repos) < PAGE_SIZE:
            return totals, language_repos
    raise StatsError("Daftar repositori melebihi batas halaman sinkronisasi.")


def language_rows(totals: Counter) -> list[tuple[str, int]]:
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0].casefold(), item[0]))
    if len(ranked) <= 5:
        return ranked
    return [*ranked[:4], ("Lainnya", sum(size for _, size in ranked[4:]))]


def numeric(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def percentage(size: int, total: int) -> str:
    if size * 1000 < total:
        return "<0,1%"
    return f"{size / total:.1%}".replace(".", ",")


def label(x: int, y: int, style: str, content: str, *, right: bool = False) -> str:
    anchor = ' text-anchor="end"' if right else ""
    return f'<text x="{x}" y="{y}" class="{style}"{anchor}>{escape(content)}</text>'


def card(title: str, description: str, body: list[str], date_label: str = "") -> str:
    children = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="description">{escape(description)}</desc>',
        '<style>',
        '  .heading { font: 26px Georgia, "Liberation Serif", serif; fill: #152733; }',
        '  .value { font: 32px Georgia, "Liberation Serif", serif; fill: #152733; }',
        '  .small { font: 13px system-ui, sans-serif; fill: #475953; }',
        '  .row { font: 14px system-ui, sans-serif; fill: #152733; }',
        '</style>',
        '<rect x=".5" y=".5" width="369" height="213" rx="9" fill="#f5f0e4" stroke="#d9d2c3"/>',
        label(20, 36, "heading", title),
        *body,
    ]
    if date_label:
        children.append(label(349, 196, "small", date_label, right=True))
    return "\n".join(children + ["</svg>", ""])


def render_streak(activity: Activity, as_of: date) -> str:
    columns = [
        (20, "Streak aktif", activity.current),
        (136, "Rekor hari", activity.longest),
        (244, "Kontribusi", activity.total),
    ]
    body = [label(20, 58, "small", "Kalender 365 hari")]
    for x, title, value in columns:
        body.extend([label(x, 103, "value", numeric(value)), label(x, 124, "small", title)])
    body.append('<path d="M20 176H350" fill="none" stroke="#b5bdb0"/>')
    peak = max(1, *activity.recent)
    for index, count in enumerate(activity.recent):
        height = 2 if count == 0 else max(4, round(count * 38 / peak))
        fill = "#216d60" if count else "#b5bdb0"
        x = 20 + index * 11
        body.append(f'<rect x="{x}" y="{176 - height}" width="8" height="{height}" rx="1.5" fill="{fill}"/>')
    body.append(label(20, 196, "small", "30 hari terakhir"))
    desc = (
        f"Streak aktif {activity.current} hari. Rekor {activity.longest} hari. "
        f"{activity.total} kontribusi dalam 365 hari."
    )
    return card("Streak GitHub", desc, body, as_of.isoformat())


def render_languages(totals: Counter, repo_count: int, as_of: date) -> str:
    total = sum(totals.values())
    body = [label(20, 58, "small", "Ukuran kode di repositori publik")]
    desc = "Repositori publik belum memiliki bahasa yang terhitung."
    if not total:
        body.append(label(20, 115, "row", "Belum ada bahasa yang dihitung GitHub."))
        return card("Bahasa repositori", desc, body, as_of.isoformat())

    description = []
    for index, (name, size) in enumerate(language_rows(totals)):
        y = 85 + index * 20
        share = percentage(size, total)
        description.append(f"{name} {share}")
        display = name if len(name) <= 18 else name[:17].rstrip() + "…"
        body.extend([
            label(20, y, "row", display),
            f'<rect x="162" y="{y - 9}" width="121" height="8" rx="2" fill="#d7ddd1"/>',
            f'<rect x="162" y="{y - 9}" width="{121 * size / total:.3f}" height="8" rx="2" fill="#216d60"/>',
            label(349, y, "row", share, right=True),
        ])
    body.append(label(20, 196, "small", f"{numeric(repo_count)} repo dengan data bahasa"))
    return card("Bahasa repositori", ". ".join(description), body, as_of.isoformat())


def initial_card(title: str, subtitle: str) -> str:
    return card(title, "Menunggu pembaruan dari GitHub.", [
        label(20, 61, "small", subtitle),
        '<path d="M20 93H350" fill="none" stroke="#b5bdb0"/>',
        label(20, 130, "row", "Menunggu pembaruan dari GitHub."),
        label(20, 155, "small", "Data akan tampil setelah sinkronisasi pertama."),
    ])


def write_assets(directory: Path, images: dict[str, str]):
    directory.mkdir(parents=True, exist_ok=True)
    for filename, body in images.items():
        destination = directory / filename
        temporary = destination.with_suffix(".svg.tmp")
        temporary.write_text(body, encoding="utf-8")
        temporary.replace(destination)


def sync(api: GitHub, login: str, now: datetime, directory: Path):
    counts = contribution_counts(api, login, now)
    languages, repo_count = public_languages(api, login)
    write_assets(directory, {
        "streak.svg": render_streak(summarize(counts), now.date()),
        "bahasa.svg": render_languages(languages, repo_count, now.date()),
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--login", default="Mavianza")
    parser.add_argument("--output", type=Path, default=ASSETS)
    parser.add_argument("--initial", action="store_true", help="Buat panel sebelum sinkronisasi pertama.")
    args = parser.parse_args()
    try:
        if args.initial:
            write_assets(args.output, {
                "streak.svg": initial_card("Streak GitHub", "Kalender 365 hari"),
                "bahasa.svg": initial_card("Bahasa repositori", "Ukuran kode di repositori publik"),
            })
        else:
            token = os.environ.get("GH_TOKEN")
            if not token:
                raise StatsError("GH_TOKEN diperlukan untuk membaca kalender kontribusi.")
            sync(GitHub(token), args.login, datetime.now(timezone.utc), args.output)
    except (StatsError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Sinkronisasi profil gagal ({type(error).__name__}): {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
