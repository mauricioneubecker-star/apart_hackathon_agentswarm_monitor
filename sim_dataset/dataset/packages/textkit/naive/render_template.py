import re
from collections.abc import Mapping
from typing import Any


def render_template(template: str, context: Mapping[str, Any]) -> str:
    filters = {"upper": str.upper, "lower": str.lower, "title": str.title, "trim": str.strip}

    def replace(match):
        name, *filter_names = [piece.strip() for piece in match.group(1).split("|")]
        value: Any = context
        for part in name.split("."):
            if not isinstance(value, Mapping) or part not in value:
                raise KeyError(name)
            value = value[part]
        text = str(value)
        for filter_name in filter_names:
            if filter_name not in filters:
                raise ValueError(f"unknown filter: {filter_name}")
            text = filters[filter_name](text)
        return text

    return re.sub(r"\{\{(.*?)\}\}", replace, template)
