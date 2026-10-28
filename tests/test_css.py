import re
from pathlib import Path

from django.test import SimpleTestCase

CSS_DIR = (
    Path(__file__).resolve().parent.parent / "debug_toolbar/static/debug_toolbar/css"
)

# Physical properties whose meaning flips in right-to-left layouts. Each one
# has a logical equivalent, e.g. margin-left -> margin-inline-start,
# right -> inset-inline-end.
PHYSICAL_PROPERTY = re.compile(
    r"(?:^|[{;])\s*(?:(?:scroll-)?(?:margin|padding)-(?:left|right)"
    r"|border-(?:left|right)[\w-]*|border-(?:top|bottom)-(?:left|right)-radius"
    r"|left|right)\s*:",
    re.IGNORECASE,
)
# Physical keywords in values that have logical counterparts.
PHYSICAL_VALUE = re.compile(
    r"(?:^|[{;])\s*(?:text-align|float|clear)\s*:\s*(?:left|right)\b",
    re.IGNORECASE,
)
# Four-value shorthands (top right bottom left) whose right and left differ.
FOUR_VALUE_SHORTHAND = re.compile(
    r"(?:^|[{;])\s*(?:margin|padding|inset|scroll-margin|scroll-padding)\s*:"
    r"\s*\S+\s+(\S+)\s+\S+\s+([^\s;]+)",
    re.IGNORECASE,
)
OPT_OUT = re.compile(r"/\*\s*rtl-ok\b")
LINT_OFF = re.compile(r"/\*\s*rtl-lint:\s*off\b")
LINT_ON = re.compile(r"/\*\s*rtl-lint:\s*on\b")


def rtl_unsafe_declarations(css):
    """Yield (line number, line) for CSS that ignores the writing direction.

    A declaration can opt out with a trailing ``/* rtl-ok */`` comment, and
    whole regions can be skipped between ``/* rtl-lint: off */`` and
    ``/* rtl-lint: on */`` comments (used for generated Pygments styles).
    """
    enabled = True
    number = 0
    for number, line in enumerate(css.splitlines(), start=1):
        if LINT_OFF.search(line):
            enabled = False
        elif LINT_ON.search(line):
            enabled = True
        elif enabled and not OPT_OUT.search(line):
            shorthand = FOUR_VALUE_SHORTHAND.search(line)
            if (
                PHYSICAL_PROPERTY.search(line)
                or PHYSICAL_VALUE.search(line)
                or (shorthand and shorthand[1] != shorthand[2])
            ):
                yield number, line.strip()
    if not enabled:
        yield number, "unterminated rtl-lint: off"


class RTLCSSTestCase(SimpleTestCase):
    def test_toolbar_css_uses_logical_properties(self):
        paths = sorted(CSS_DIR.glob("*.css"))
        self.assertIn("toolbar.css", [path.name for path in paths])
        problems = [
            f"{path.name}:{number}: {line}"
            for path in paths
            for number, line in rtl_unsafe_declarations(
                path.read_text(encoding="utf-8")
            )
        ]
        self.assertEqual(
            problems,
            [],
            "Use logical properties (margin-inline-start, inset-inline-end, "
            "text-align: start, ...) so the toolbar's layout follows its "
            "writing direction, or add /* rtl-ok */ when a physical side is "
            "intended.",
        )

    def test_detects_physical_properties(self):
        lines = [
            "a { margin-left: 1px; }",
            "b { padding-right: 0; }",
            "c { border-left-color: red; }",
            "d { right: 0; }",
            "e { text-align: left; }",
            "f { float: right; }",
            "g { margin-inline-start: 1px; }",
            "h { inset-inline-end: 0; }",
            "i { text-align: start; }",
            "j { right: 0; /* rtl-ok */ }",
            "/* rtl-lint: off */",
            "k { padding-left: 5px; }",
            "/* rtl-lint: on */",
            "l { transform-origin: right bottom; }",
            "m { scroll-margin-left: 0; }",
            "#djDebug .left:hover { color: red; }",
            "/* move it left: later */",
            "n { color: red; left: 0; }",
            "o { padding: 0 10px 0 0; }",
            "p { margin: 0 27px 27px 27px; }",
            "q { MARGIN-LEFT: 1px; }",
            "r { border-top-left-radius: 4px; }",
            ".x-rtl-ok { margin-left: 1px; }",
        ]
        self.assertEqual(
            [number for number, _ in rtl_unsafe_declarations("\n".join(lines))],
            [1, 2, 3, 4, 5, 6, 15, 18, 19, 21, 22, 23],
        )

    def test_unterminated_lint_off(self):
        css = "/* rtl-lint: off */\na { margin-left: 1px; }"
        self.assertEqual(
            list(rtl_unsafe_declarations(css)),
            [(2, "unterminated rtl-lint: off")],
        )
