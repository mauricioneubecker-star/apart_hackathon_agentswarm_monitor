from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def render_template(template: str, context: Mapping[str, Any]) -> str:
    """
    Render "{{ ... }}" placeholders in a notification/email template.

    Placeholder syntax: "{{" name ("|" filter)* "}}", with optional whitespace
    around the name, the filters and the bars. `name` is a dotted path looked up in
    `context` through nested mappings: "user.first_name" means
    context["user"]["first_name"]. The value is converted with str() and the
    filters are applied left to right. Supported filters: upper, lower, title
    (str.title) and trim (str.strip). Text outside placeholders is copied
    unchanged.

    Errors:
      * KeyError if any part of the path is missing, or if a non-mapping value
        would have to be indexed.
      * ValueError for an unknown filter name.

    Examples:
        render_template("Hi {{ user.name | title }}!", {"user": {"name": "ada"}}) == "Hi Ada!"
        render_template("{{count}} new", {"count": 3}) == "3 new"
    """
    raise NotImplementedError
