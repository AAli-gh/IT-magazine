"""PostgreSQL full-text query building."""

import re

_LEXEME = re.compile(r"\w+", re.UNICODE)


def build_tsquery(groups):
    """Turn textutils.expand_query() groups into a raw PostgreSQL tsquery string.

    Groups are AND-ed, synonyms inside a group OR-ed, multi-word terms become phrases,
    and every word is a prefix match ("pyth" finds "python"). Only \\w characters reach
    the query, so user input can't inject tsquery operators.
    """
    clauses = []
    for group in groups:
        options = []
        for term in group:
            words = _LEXEME.findall(term)
            if words:
                options.append(" <-> ".join(f"'{w}':*" for w in words))
        if options:
            clauses.append("(" + " | ".join(options) + ")")
    return " & ".join(clauses)
