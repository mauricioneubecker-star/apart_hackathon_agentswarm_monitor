import re
from typing import List


def extract_invoice_refs(memo: str) -> List[str]:
    pattern = r"(?<![A-Za-z0-9])inv[-# ]?(\d{1,6})(?!\d)"
    return ["INV-" + m.zfill(6) for m in re.findall(pattern, memo, flags=re.IGNORECASE)]
