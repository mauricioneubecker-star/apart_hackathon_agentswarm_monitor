import re
from typing import List

_REF = re.compile(r"(?<![A-Za-z0-9])inv[-# ]?(\d{1,6})(?!\d)", re.IGNORECASE)


def extract_invoice_refs(memo: str) -> List[str]:
    refs = []
    for match in _REF.finditer(memo):
        ref = "INV-" + match.group(1).zfill(6)
        if ref not in refs:
            refs.append(ref)
    return refs
