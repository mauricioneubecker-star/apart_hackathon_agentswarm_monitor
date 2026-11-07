from typing import List


def split_csv_line(line: str, delimiter: str = ",") -> List[str]:
    if len(delimiter) != 1 or delimiter == '"':
        raise ValueError("delimiter must be a single character other than a double quote")
    fields: List[str] = []
    pos, end = 0, len(line)
    while True:
        probe = pos
        while probe < end and line[probe] == " " and delimiter != " ":
            probe += 1
        if probe < end and line[probe] == '"':
            probe += 1
            chars = []
            while True:
                if probe >= end:
                    raise ValueError("unterminated quoted field")
                if line[probe] == '"':
                    if probe + 1 < end and line[probe + 1] == '"':
                        chars.append('"')
                        probe += 2
                        continue
                    probe += 1
                    break
                chars.append(line[probe])
                probe += 1
            if probe < end and line[probe] != delimiter:
                raise ValueError("unexpected text after closing quote")
            fields.append("".join(chars))
        else:
            probe = line.find(delimiter, pos)
            if probe == -1:
                probe = end
            fields.append(line[pos:probe])
        if probe >= end:
            return fields
        pos = probe + 1
