from typing import List


def split_csv_line(line: str, delimiter: str = ",") -> List[str]:
    if len(delimiter) != 1 or delimiter == '"':
        raise ValueError("delimiter must be a single character other than a double quote")
    fields: List[str] = []
    field = ""
    in_quotes = False
    was_quoted = False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quotes:
            if ch == '"' and line[i + 1:i + 2] == '"':
                field += '"'
                i += 1
            elif ch == '"':
                in_quotes = False
            else:
                field += ch
        elif ch == delimiter:
            fields.append(field)
            field, was_quoted = "", False
        elif ch == '"' and field == "" and not was_quoted:
            in_quotes = was_quoted = True
        elif was_quoted:
            raise ValueError("unexpected text after closing quote")
        else:
            field += ch
        i += 1
    if in_quotes:
        raise ValueError("unterminated quoted field")
    fields.append(field)
    return fields
