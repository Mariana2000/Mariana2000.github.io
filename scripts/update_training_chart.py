"""Generate a static chart from wxh's anonymous, public Attackpoint summary.

Only rounded weekly distance totals are retained. No login, notes, GPS tracks,
or activity details are stored. Invalid responses leave the previous SVG intact.
"""

import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.request import Request, urlopen


SOURCE = "https://www.attackpoint.org/log.jsp/user_21269"
OUTPUT = Path(__file__).resolve().parents[1] / "assets/images/training-distance.svg"


class SummaryParser(HTMLParser):
    """Read the existing summary tables, ignoring the rest of the training log."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.depth = 0
        self.in_heading = False
        self.table = None
        self.row = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "table":
            if self.depth:
                self.depth += 1
            elif "stackedbargraph" in classes:
                self.depth = 1
                self.table = {"heading": [], "rows": []}
            return
        if self.depth != 1:
            return
        if tag == "th":
            self.in_heading = True
        elif tag == "tr":
            self.row = {"href": None, "values": []}
        elif tag == "a" and "sbxlink" in classes and self.row is not None:
            self.row["href"] = attrs.get("href", "")
        elif tag == "span" and "graphbar" in classes and self.row is not None:
            self.row["values"].append(attrs.get("title", ""))

    def handle_data(self, data):
        if self.depth == 1 and self.in_heading:
            self.table["heading"].append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "table":
            self.depth -= 1
            if not self.depth:
                self.tables.append(self.table)
                self.table = None
                self.row = None
            return
        if self.depth == 1:
            if tag == "th":
                self.in_heading = False
            elif tag == "tr" and self.row is not None:
                if self.row["href"] is not None:
                    self.table["rows"].append(self.row)
                self.row = None


def parse_weeks(html, today):
    parser = SummaryParser()
    parser.feed(html)
    tables = [table for table in parser.tables if
              "Training kilometers by activity" in " ".join(table["heading"])]
    if len(tables) != 1:
        raise ValueError("The public distance summary is missing or ambiguous.")
    weeks = []
    for row in tables[0]["rows"]:
        match = re.fullmatch(
            r"/viewlog\.jsp/user_21269/period-7/enddate-(\d{4}-\d{2}-\d{2})",
            row["href"],
        )
        if not match:
            raise ValueError("Unexpected user or date in the public summary.")
        total = Decimal(0)
        for value in row["values"]:
            distance = re.fullmatch(r"\d+% .+ \(\d+x\) (\d+(?:\.\d+)?)km", value)
            if not distance:
                raise ValueError("Unexpected distance format; keeping the previous chart.")
            total += Decimal(distance[1])
        weeks.append((date.fromisoformat(match[1]), total))
    weeks.sort()
    if len(weeks) != 5 or any(
        weeks[i + 1][0] - weeks[i][0] != timedelta(days=7) for i in range(4)
    ):
        raise ValueError("Expected five consecutive weekly totals.")
    if any(week[0].weekday() != 5 for week in weeks):
        raise ValueError("The source no longer uses weeks ending on Saturday.")
    if not -1 <= (weeks[-1][0] - today).days <= 7:
        raise ValueError("The public summary is stale or has an unexpected date.")
    return weeks


def render_chart(weeks, today):
    description = "; ".join(
        f"week ending {ending.isoformat()}: approximately {distance:.1f} km"
        for ending, distance in weeks
    )
    description += f". The current week is incomplete. Updated {today.isoformat()} UTC."
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="274" '
        'viewBox="0 0 360 274" role="img" aria-labelledby="title description">',
        '<title id="title">Training distance over the recent five weeks</title>',
        f'<desc id="description">{escape(description)}</desc>',
        '<rect x="0.5" y="0.5" width="359" height="273" rx="10" '
        'fill="#faf9f5" stroke="#dcded6"/>',
        '<g font-family="system-ui, sans-serif" fill="#25392e">',
        '<text x="18" y="29" font-size="18" font-weight="600">Training distance</text>',
        '<text x="340" y="29" text-anchor="end" font-size="12">km</text>',
        '<text x="18" y="49" font-size="12" fill="#58665d">Recent 5 weeks · week ending Saturday</text>',
    ]
    maximum = max(Decimal(1), *(distance for _, distance in weeks))
    for index, (ending, distance) in enumerate(weeks):
        y = 69 + index * 31
        label = f"{ending:%b} {ending.day}"
        current = index == len(weeks) - 1
        if current:
            label += "*"
        width = distance / maximum * 203
        color = "#78a68a" if current else "#36734d"
        svg.extend([
            f'<text x="18" y="{y + 14}" font-size="12">{label}</text>',
            f'<rect x="83" y="{y}" width="203" height="19" rx="3" fill="#e7ece6"/>',
            f'<rect x="83" y="{y}" width="{width:.2f}" height="19" rx="3" fill="{color}"/>',
            f'<text x="340" y="{y + 14}" text-anchor="end" font-size="13">{distance:.1f}</text>',
        ])
    svg.extend([
        f'<text x="18" y="237" font-size="11" fill="#58665d">'
        f'Updated {today:%b} {today.day}, {today.year} (UTC)</text>',
        '<text x="18" y="256" font-size="10.5" fill="#58665d">'
        '* Current week · distances rounded by Attackpoint</text>',
        '</g></svg>',
    ])
    return "\n".join(svg) + "\n"


def update_chart(output=OUTPUT, *, today=None, fetch=None):
    today = today or datetime.now(timezone.utc).date()
    if fetch is None:
        request = Request(SOURCE, headers={
            "User-Agent": "Mariana2000.github.io training chart (public log 21269)",
        })
        with urlopen(request, timeout=30) as response:
            if response.headers.get_content_type() != "text/html":
                raise ValueError("Expected the public HTML training summary.")
            html = response.read().decode("utf-8")
    else:
        html = fetch()
    svg = render_chart(parse_weeks(html, today), today)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".svg.tmp")
    temporary.write_text(svg, encoding="utf-8")
    temporary.replace(output)
    print(f"Updated {output.name} from the public weekly distance summary ({today}).")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, default=OUTPUT)
    args = cli.parse_args()
    update_chart(args.output)
