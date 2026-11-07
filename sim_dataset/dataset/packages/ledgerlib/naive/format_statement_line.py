from ledgerlib.format_cents import format_cents


def format_statement_line(day: str, description: str, amount_cents: int, balance_cents: int,
                          width: int = 64) -> str:
    desc_width = width - 38
    if desc_width < 10:
        raise ValueError("statement width too small")
    description = description[:desc_width]
    amount = format_cents(amount_cents)
    balance = format_cents(balance_cents)
    return f"{day:<10}  {description:<{desc_width}} {amount:>12} {balance:>12}"
