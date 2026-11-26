"""Draw the desktop and mobile profile banners using an integer pixel grid."""

from itertools import groupby
from pathlib import Path


ASSETS = Path(__file__).resolve().parents[1] / "assets"
INK = "#111c27"
PANEL = "#192b36"
SEAM = "#35515b"
CREAM = "#fbefd2"
MUTED = "#b4c6bf"
MINT = "#92e1bb"
GOLD = "#efb46e"
COPPER = "#a76b47"
IDLE_START = 3.05
DEVICE_CYCLE = 5.6
PACKET_ARRIVAL = 0.25

LETTER_GRID = {
    "A": ("01110", "11011", "11011", "11111", "11011", "11011", "11011"),
    "F": ("11111", "11000", "11000", "11110", "11000", "11000", "11000"),
    "H": ("11011", "11011", "11011", "11111", "11011", "11011", "11011"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("11000", "11000", "11000", "11000", "11000", "11000", "11111"),
    "M": ("10001", "11011", "11111", "10101", "10001", "10001", "10001"),
    "N": ("11001", "11101", "11101", "11011", "11011", "11001", "11001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "V": ("11011", "11011", "11011", "11011", "01010", "01010", "00100"),
    "Z": ("11111", "00011", "00110", "01100", "11000", "11000", "11111"),
}


def rect(x, y, width, height, color):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{color}"/>'


def path(d, color):
    return f'<path d="{d}" fill="{color}"/>'


def group(x, y, parts, *, pixel=False):
    crisp = ' shape-rendering="crispEdges"' if pixel else ""
    return f'<g transform="translate({x} {y})"{crisp}>\n' + "\n".join(parts) + "\n</g>"


def animated_rect(x, y, width, height, color, animations, *, phase="opening"):
    return "\n".join([
        f'<rect class="motion-only {phase}" x="{x}" y="{y}" width="{width}" height="{height}" fill="{color}" opacity="0">',
        *animations,
        '</rect>',
    ])


def name_wipe(length, size):
    width = (length * 6 - 1) * size
    positions = (*range(0, width, size * 8), width)
    left_edges = ";".join(str(position) for position in positions)
    widths = ";".join(str(width - position) for position in positions)
    return animated_rect(0, 0, width, 7 * size, INK, [
        '<animate attributeName="opacity" values="1;1" begin="0s" dur="0.7s"/>',
        f'<animate attributeName="x" values="{left_edges}" calcMode="discrete" begin="0s" dur="0.7s"/>',
        f'<animate attributeName="width" values="{widths}" calcMode="discrete" begin="0s" dur="0.7s"/>',
    ])


def word(text, x, y, size, color, *, reveal=False):
    pixels = []
    for column, letter in enumerate(text):
        for row, pattern in enumerate(LETTER_GRID[letter]):
            left = 0
            for bit, run in groupby(pattern):
                width = sum(1 for _ in run)
                if bit == "1":
                    px, py = (column * 6 + left) * size, row * size
                    pixels.append(f"M{px} {py}h{width * size}v{size}h{-width * size}Z")
                left += width
    parts = [path(" ".join(pixels), color)]
    if reveal:
        parts.append(name_wipe(len(text), size))
    return group(x, y, parts, pixel=True)


def signal(route, start, travel, color):
    # The base opacity hides the signal when the timed animation ends.
    return (
        '<g class="motion-only opening" opacity="0" shape-rendering="crispEdges">\n'
        + rect(-3, -3, 6, 6, color)
        + f'\n<animateMotion path="{route}" begin="{start}s" dur="{travel}s"/>'
        + f'\n<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.12;0.84;1"'
        + f' begin="{start}s" dur="{travel}s"/>\n</g>'
    )


def arrival(x, y, width, height, start):
    return animated_rect(x, y, width, height, MINT, [
        f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.2;1" begin="{start}s" dur="0.36s"/>',
    ])


def screen_startup():
    return [
        animated_rect(16, 16, 112, 56, INK, [
            '<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.18;1" begin="0s" dur="0.78s"/>',
        ]),
        animated_rect(20, 20, 104, 4, MINT, [
            '<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.2;0.72;1" begin="0.14s" dur="0.58s"/>',
            '<animate attributeName="y" values="20;28;36;44;52;60;64" calcMode="discrete" begin="0.14s" dur="0.58s"/>',
        ]),
    ]


def idle_timing(start, period=DEVICE_CYCLE):
    return f'begin="{start:g}s" dur="{period:g}s" repeatCount="indefinite"'


def idle_cursor():
    timing = idle_timing(IDLE_START, 2.7)
    return animated_rect(58, 53, 7, 10, CREAM, [
        '<animate attributeName="x" values="58;66;74;82;90;96;96" calcMode="discrete"'
        f' keyTimes="0;0.13;0.26;0.39;0.52;0.65;1" {timing}/>',
        '<animate attributeName="opacity" values="0;1;1;0;0"'
        f' keyTimes="0;0.06;0.70;0.80;1" {timing}/>',
    ], phase="idle")


def idle_packet(route, start, color):
    timing = idle_timing(start)
    return "\n".join([
        '<g class="motion-only idle" opacity="0">',
        rect(-4, -4, 8, 8, color),
        rect(-2, -2, 4, 4, CREAM),
        f'<animateMotion path="{route}" calcMode="linear" keyPoints="0;1;1"'
        f' keyTimes="0;{PACKET_ARRIVAL:g};1" {timing}/>',
        '<animate attributeName="opacity" values="0;1;1;0;0"'
        f' keyTimes="0;0.035;0.22;0.29;1" {timing}/>',
        '</g>',
    ])


def monitor():
    return group(104, 12, [
        path("M8 0H140V8H148V84H140V92H0V8H8Z", GOLD),
        path("M136 0H140V8H148V84H140V92H132V84H136Z", COPPER),
        rect(8, 8, 8, 68, CREAM),
        rect(16, 8, 112, 4, CREAM),
        rect(16, 16, 112, 56, INK),
        rect(24, 24, 96, 8, "#467f70"),
        rect(28, 28, 4, 4, MINT),
        rect(36, 28, 4, 4, MINT),
        rect(24, 36, 24, 28, "#2a4d4d"),
        rect(28, 40, 12, 4, "#89b8a3"),
        rect(28, 48, 16, 4, "#89b8a3"),
        rect(52, 36, 68, 28, "#365c58"),
        rect(56, 40, 56, 12, MINT),
        rect(56, 56, 36, 4, "#92b8a4"),
        path("M104 44H108V48H112V52H116V56H112V60H108V56H104Z", CREAM),
        rect(108, 80, 12, 4, "#654a3f"),
        rect(44, 92, 56, 8, COPPER),
        rect(36, 100, 72, 8, GOLD),
        rect(52, 100, 40, 4, CREAM),
        *screen_startup(),
        idle_cursor(),
    ], pixel=True)


def disk_stack(first_pulse):
    parts = []
    for row in range(3):
        y = row * 16
        timing = idle_timing(first_pulse + row * 0.24)
        parts.extend([
            path(f"M8 {y}H96V{y + 4}H104V{y + 12}H96V{y + 16}H0V{y + 4}H8Z", GOLD),
            rect(4, y + 12, 92, 4, COPPER),
            rect(12, y + 4, 40, 4, "#77523d"),
            rect(72, y + 4, 8, 4, INK),
            rect(84, y + 4, 8, 4, CREAM),
            animated_rect(76, y + 4, 20, 5, MINT, [
                '<animate attributeName="opacity" values="0;1;1;0;0"'
                f' keyTimes="0;0.02;0.065;0.105;1" {timing}/>',
            ], phase="idle"),
        ])
    return group(22, 150, parts, pixel=True)


def idle_focus(start):
    timing = idle_timing(start)
    corners = "M0 0H8V2H2V6H0Z M20 0H28V6H26V2H20Z M0 14H2V18H8V20H0Z M26 14H28V20H20V18H26Z"
    return "\n".join([
        '<g class="motion-only idle" opacity="0">',
        path(corners, MINT),
        rect(13, 9, 2, 2, CREAM),
        '<animateMotion path="M22 24H58" calcMode="linear" keyPoints="0;0;1;1"'
        f' keyTimes="0;0.06;0.44;1" {timing}/>',
        '<animate attributeName="opacity" values="0;1;1;0;0"'
        f' keyTimes="0;0.06;0.47;0.58;1" {timing}/>',
        '</g>',
    ])


def media_view(focus_start):
    return group(248, 142, [
        path("M4 0H96V4H104V56H100V60H0V4H4Z", "#6aa99b"),
        rect(4, 4, 96, 4, MINT),
        rect(8, 12, 88, 40, "#233f45"),
        path("M12 44H24V36H32V28H40V32H48V40H60V32H68V24H76V28H84V36H92V48H12Z", "#51806d"),
        rect(56, 20, 8, 8, "#78b299"),
        path("M14 16H26V20H18V28H14Z", CREAM),
        path("M78 16H90V28H86V20H78Z", CREAM),
        path("M14 36H18V44H26V48H14Z", CREAM),
        path("M90 36H86V44H78V48H90Z", CREAM),
        rect(38, 60, 28, 4, "#4c7c75"),
        idle_focus(focus_start),
    ], pixel=True)


def interest_map(x, y):
    to_data = "M176 120V132H74V148"
    to_media = "M176 120V132H298V140"
    media_start = IDLE_START + DEVICE_CYCLE / 2
    travel_time = DEVICE_CYCLE * PACKET_ARRIVAL
    parts = [
        path("M12 0H344V8H356V204H348V220H12V212H0V12H12Z", PANEL),
        path("M12 0H344V4H16V12H0V8H12Z", SEAM),
        path("M8 208H348V204H356V216H12V212H8Z", "#213940"),
        rect(14, 16, 8, 8, SEAM),
        rect(334, 16, 8, 8, SEAM),
        rect(14, 198, 8, 8, SEAM),
        rect(334, 198, 8, 8, SEAM),
        f'<path d="{to_data} {to_media}" fill="none" stroke="#537b74" stroke-width="4"/>',
        rect(170, 126, 12, 12, "#82aa94"),
        rect(68, 142, 12, 12, "#b08456"),
        rect(292, 134, 12, 12, "#72a895"),
        monitor(),
        disk_stack(IDLE_START + travel_time),
        media_view(media_start + travel_time),
        signal(to_data, 0.83, 1.05, GOLD),
        signal(to_media, 1.5, 1.08, MINT),
        arrival(106, 154, 8, 4, 1.82),
        arrival(304, 162, 8, 8, 2.52),
        idle_packet(to_data, IDLE_START, GOLD),
        idle_packet(to_media, media_start, MINT),
    ]
    return group(x, y, parts, pixel=True)


def legend(x, y, label, category):
    if category == "web":
        mark = [
            f'<path d="M0 0H16V12H0Z M3 4V9H13V4Z" fill="{GOLD}" fill-rule="evenodd"/>',
        ]
    elif category == "data":
        mark = [rect(0, y_offset, 16, 3, GOLD) for y_offset in (0, 5, 10)]
    else:
        mark = [
            path("M0 0H6V3H3V6H0Z M10 0H16V6H13V3H10Z M0 7H3V10H6V13H0Z M13 7H16V13H10V10H13Z", MINT),
        ]
    return group(x, y, [*mark, f'<text class="topic" x="24" y="12">{label}</text>'])


def banner(*, mobile):
    if mobile:
        width, height = 400, 464
        body = [
            rect(26, 27, 48, 4, GOLD),
            word("ALFATH", 26, 43, 5, GOLD),
            word("MAVIANZA", 26, 87, 7, CREAM, reveal=True),
            '<text class="affiliation" x="26" y="162">Teknik Informatika · Universitas Mataram</text>',
            interest_map(22, 187),
            legend(24, 429, "Web", "web"),
            legend(151, 429, "Data", "data"),
            legend(252, 429, "Multimedia", "media"),
        ]
    else:
        width, height = 800, 318
        body = [
            rect(36, 44, 64, 4, GOLD),
            word("ALFATH", 36, 68, 6, GOLD),
            word("MAVIANZA", 36, 124, 7, CREAM, reveal=True),
            '<text class="affiliation" x="36" y="207">Teknik Informatika</text>',
            '<text class="affiliation" x="36" y="231">Universitas Mataram</text>',
            interest_map(410, 24),
            rect(34, 267, 732, 1, SEAM),
            legend(36, 284, "Antarmuka web", "web"),
            legend(291, 284, "Sistem informasi", "data"),
            legend(540, 284, "Multimedia interaktif", "media"),
        ]

    frame = f"M10 0H{width - 10}V5H{width - 5}V10H{width}V{height - 10}H{width - 5}V{height - 5}H{width - 10}V{height}H10V{height - 5}H5V{height - 10}H0V10H5V5H10Z"
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">Alfath Mavianza</title>',
        '<desc id="description">Peta minat dalam gaya pixel art. Monitor terhubung ke penyimpanan data dan layar multimedia. Antarmuka web, sistem informasi, dan multimedia interaktif.</desc>',
        '<style>',
        f'  .affiliation {{ font: 500 {15 if mobile else 18}px system-ui, sans-serif; fill: {MUTED}; }}',
        f'  .topic {{ font: 600 {14 if mobile else 16}px system-ui, sans-serif; fill: {CREAM}; }}',
        '  @media (prefers-reduced-motion: reduce) { .motion-only { display: none; } }',
        '</style>',
        f'<path d="{frame}" fill="{INK}" shape-rendering="crispEdges"/>',
        *body,
        '</svg>',
        '',
    ])


if __name__ == "__main__":
    (ASSETS / "peta-minat.svg").write_text(banner(mobile=False), encoding="utf-8")
    (ASSETS / "peta-minat-mobile.svg").write_text(banner(mobile=True), encoding="utf-8")
