import re
from collections.abc import Mapping
from typing import Any

_PLACEHOLDER = re.compile(r"\{\{\s*([^{}]*?)\s*\}\}")
_FILTERS = (("upper", str.upper), ("lower", str.lower), ("title", str.title), ("trim", str.strip))


def _lookup(context: Mapping, path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise KeyError(path)
        value = value[part]
    return value


def render_template(template: str, context: Mapping[str, Any]) -> str:
    filters = dict(_FILTERS)

    def replace(match):
        name, *filter_names = [piece.strip() for piece in match.group(1).split("|")]
        value = _lookup(context, name)
        text = "" if value is None else str(value)
        for filter_name in filter_names:
            if filter_name not in filters:
                raise ValueError(f"unknown filter: {filter_name}")
            text = filters[filter_name](text)
        return text

    return _PLACEHOLDER.sub(replace, template)
