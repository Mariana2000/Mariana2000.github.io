"""Check data accuracy and preservation of the last good chart on failures."""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree

from update_training_chart import parse_weeks, render_chart, update_chart


TODAY = date(2026, 10, 12)


def summary():
    rows = []
    for i in range(5):
        ending = date(2026, 10, 17) - timedelta(days=7 * i)
        # One zero-distance week; multiple rounded categories in other weeks.
        bars = "" if i == 1 else (
            '<span class="graphbar" title="60% Orienteering (2x) 7.7km"></span>'
            '<span class="graphbar" title="40% Running (Treadmill) (1x) 5.1km"></span>'
        )
        rows.append(f'<tr><td><a class="sbxlink" href="/viewlog.jsp/user_21269/'
                    f'period-7/enddate-{ending}">date</a></td><td>{bars}</td></tr>')
    return ('<table class="stackedbargraph"><tr><th>Week Ending</th>'
            '<th>Training kilometers by activity</th></tr>'
            '<tr><td><table><tr><td>axis labels</td></tr></table></td></tr>'
            + "".join(rows) + '</table>')


class TrainingChartTests(unittest.TestCase):
    def test_totals_dates_and_zero_week(self):
        weeks = parse_weeks(summary(), TODAY)
        self.assertEqual(weeks[0], (date(2026, 9, 19), Decimal("12.8")))
        self.assertEqual(weeks[-2][1], Decimal(0))
        self.assertEqual(weeks[-1][0], date(2026, 10, 17))

    def test_rejects_missing_stale_wrong_user_and_changed_formats(self):
        cases = [
            "<html>Please log in</html>",
            summary().replace("user_21269", "user_1"),
            summary().replace("7.7km", "7.7mi"),
            summary().replace("2026-10-17", "2026-10-10"),
        ]
        for html in cases:
            with self.subTest(html=html[:80]), self.assertRaises(ValueError):
                parse_weeks(html, TODAY)
        with self.assertRaises(ValueError):
            parse_weeks(summary(), date(2026, 11, 1))

    def test_failure_preserves_previous_chart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chart.svg"
            path.write_text("previous valid chart", encoding="utf-8")
            for fetch in [lambda: "Forbidden", self.offline]:
                with self.assertRaises((ValueError, OSError)):
                    update_chart(path, today=TODAY, fetch=fetch)
                self.assertEqual(path.read_text(encoding="utf-8"), "previous valid chart")

    @staticmethod
    def offline():
        raise OSError("Network unavailable")

    def test_zero_chart_is_valid_svg(self):
        weeks = [(end, Decimal(0)) for end, _ in parse_weeks(summary(), TODAY)]
        svg = render_chart(weeks, TODAY)
        ElementTree.fromstring(svg)
        self.assertIn("2026-10-12 UTC", svg)
        self.assertNotIn("NaN", svg)


if __name__ == "__main__":
    unittest.main()
