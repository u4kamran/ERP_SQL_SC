"""GL account code formatting (VB6 Dash_GL)."""

from __future__ import annotations

SEG1 = 2
SEG2 = 2
SEG3 = 4
CODE_LEN = SEG1 + SEG2 + SEG3 + 0  # 8 digits typical


def pad_gl_code(value: int | str) -> str:
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits.zfill(SEG1 + SEG2 + SEG3)


def dash_gl(value: int | str) -> str:
    code = pad_gl_code(value)
    return f"{code[:SEG1]}-{code[SEG1:SEG1 + SEG2]}-{code[SEG1 + SEG2:SEG1 + SEG2 + SEG3]}"


def format_voucher_no(voucher_id: int | None, fiscal: int | None) -> str:
    if voucher_id is None:
        return ""
    if not fiscal:
        return str(voucher_id).strip()
    fiscal_text = f"{int(fiscal):02d}"
    return f"{fiscal_text}-{voucher_id}"


def format_voucher_type(voucher_abbr: str | None, v_mode: int | None) -> str:
    abbr = (voucher_abbr or "").strip()
    if not v_mode or v_mode <= 1:
        return abbr
    if v_mode == 2:
        return f"{abbr}P"
    return f"{abbr}R"
