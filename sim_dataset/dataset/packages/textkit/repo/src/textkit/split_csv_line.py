from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def split_csv_line(line: str, delimiter: str = ",") -> List[str]:
    """
    Split one line of CSV into its fields (used by the bulk tag importer).

      * Fields are separated by `delimiter`, a single character other than '"'.
      * A field may be enclosed in double quotes; inside a quoted field the
        delimiter is literal and a doubled quote ("") stands for one '"'.
      * Unquoted fields are returned exactly as written (no trimming).
      * An empty line gives [""]; a trailing delimiter gives a trailing empty field.

    Raises ValueError for an unterminated quoted field, for any text between a
    closing quote and the next delimiter, and for an invalid delimiter (not exactly
    one character, or '"').

    Examples:
        split_csv_line('a,"b,c",d') == ["a", "b,c", "d"]
        split_csv_line('x,"say ""hi"" now"') == ["x", 'say "hi" now']
    """
    raise NotImplementedError
