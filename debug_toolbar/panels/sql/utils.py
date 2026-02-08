from functools import cache, lru_cache
from html import escape

import sqlparse
from django.dispatch import receiver
from django.test.signals import setting_changed
from sqlparse import tokens as T
from sqlparse.exceptions import SQLParseError

from debug_toolbar import settings as dt_settings


class ElideSelectListsFilter:
    """sqlparse filter to elide the select list from top-level SELECT ... FROM clauses,
    if present"""

    def process(self, stream):
        allow_elision = True
        for token_type, value in stream:
            yield token_type, value
            if token_type in T.Keyword:
                keyword = value.upper()
                if allow_elision and keyword == "SELECT":
                    yield from self.elide_until_from(stream)
                allow_elision = keyword in ["EXCEPT", "INTERSECT", "UNION"]

    @staticmethod
    def elide_until_from(stream):
        has_dot = False
        saved_tokens = []
        for token_type, value in stream:
            if token_type in T.Keyword and value.upper() == "FROM":
                # Do not elide a select lists that do not contain dots (used to separate
                # table names from column names) in order to preserve
                #    SELECT COUNT(*) AS `__count` FROM ...
                # and
                #    SELECT (1) AS `a` FROM ...
                # queries.
                if not has_dot:
                    yield from saved_tokens
                else:
                    # U+2022: Unicode character 'BULLET'
                    yield T.Other, " \u2022\u2022\u2022 "
                yield token_type, value
                break
            if not has_dot:
                if token_type in T.Punctuation and value == ".":
                    has_dot = True
                else:
                    saved_tokens.append((token_type, value))


class BoldKeywordFilter:
    """sqlparse filter to bold SQL keywords"""

    def process(self, stmt):
        idx = 0
        while idx < len(stmt.tokens):
            token = stmt[idx]
            if token.is_keyword:
                stmt.insert_before(idx, sqlparse.sql.Token(T.Other, "<strong>"))
                stmt.insert_after(
                    idx + 1,
                    sqlparse.sql.Token(T.Other, "</strong>"),
                    skip_ws=False,
                )
                idx += 2
            elif token.is_group:
                self.process(token)
            idx += 1


def escaped_value(token):
    # Don't escape T.Whitespace tokens because AlignedIndentFilter inserts its tokens as
    # T.Whitesapce, and in our case those tokens are actually HTML.
    if token.ttype in (T.Other, T.Whitespace):
        return token.value
    return escape(token.value, quote=False)


class EscapedStringSerializer:
    """sqlparse post-processor to convert a Statement into a string escaped for
    inclusion in HTML ."""

    @staticmethod
    def process(stmt):
        return "".join(escaped_value(token) for token in stmt.flatten())


def is_select_query(sql):
    # UNION queries can start with "(".
    return sql.lower().lstrip(" (").startswith("select")


def reformat_sql(sql, *, with_toggle=False):
    formatted = parse_sql(sql)
    if not with_toggle:
        return formatted
    simplified = parse_sql(sql, simplify=True)

    uncollapsed = f'<span class="djDebugUncollapsed">{simplified}</span>'
    collapsed = f'<span class="djDebugCollapsed djdt-hidden">{formatted}</span>'
    return collapsed + uncollapsed


@lru_cache(maxsize=128)
def parse_sql(sql, *, simplify=False):
    stack = get_filter_stack(simplify=simplify)
    try:
        return "".join(stack.run(sql))
    except SQLParseError:
        # The query either exceeds the number of tokens or depth of tokens.
        # Recreate the FilterStack and explicitly disable the grouping to avoid
        # those errors.
        stack = get_filter_stack(simplify=simplify)
        stack._grouping = False
        return "".join(stack.run(sql))


@cache
def get_filter_stack(*, simplify):
    stack = sqlparse.engine.FilterStack()
    if simplify:
        stack.preprocess.append(ElideSelectListsFilter())
    else:
        if dt_settings.get_config()["PRETTIFY_SQL"]:
            stack.enable_grouping()
        stack.stmtprocess.append(
            sqlparse.filters.AlignedIndentFilter(char="&nbsp;", n="<br/>")
        )
    stack.stmtprocess.append(BoldKeywordFilter())
    stack.postprocess.append(EscapedStringSerializer())  # Statement -> str
    return stack


@receiver(setting_changed)
def clear_caches(*, setting, **kwargs):
    if setting == "DEBUG_TOOLBAR_CONFIG":
        parse_sql.cache_clear()
        get_filter_stack.cache_clear()


def contrasting_color_generator():
    """
    Generate contrasting colors by varying most significant bit of RGB first,
    and then vary subsequent bits systematically.
    """

    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(*tuple(rgb))

    triples = [
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 1, 0),
        (0, 1, 1),
        (1, 0, 1),
        (1, 1, 1),
    ]
    n = 1 << 7
    so_far = [[0, 0, 0]]
    while True:
        if n == 0:  # This happens after 2**24 colours; presumably, never
            yield "#000000"  # black
        copy_so_far = list(so_far)
        for triple in triples:
            for previous in copy_so_far:
                rgb = [n * triple[i] + previous[i] for i in range(3)]
                so_far.append(rgb)
                yield rgb_to_hex(rgb)
        n >>= 1
