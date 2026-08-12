"""Parse Fin_PurM / Fin_PurD VB6 forms for modernization analysis."""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "_analysis"


def decode(raw: bytes) -> str:
    for enc in ("cp1252", "latin-1", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def extract_controls(text: str) -> list[dict]:
    controls = []
    stack: list[str] = []
    begin_re = re.compile(r"^\s*Begin ([\w.]+) (\w+)\s*$")
    end_re = re.compile(r"^\s*End\s*$")
    prop_re = re.compile(r'^\s*(\w+)\s*=\s*(.+?)\s*$')
    current: dict | None = None
    props: dict = {}

    for line in text.splitlines():
        bm = begin_re.match(line)
        if bm:
            if current is not None:
                current["props"] = props
                controls.append(current)
            ctype, cname = bm.group(1), bm.group(2)
            current = {"type": ctype, "name": cname, "parent": stack[-1] if stack else None}
            props = {}
            stack.append(cname)
            continue
        if end_re.match(line):
            if current is not None:
                current["props"] = props
                controls.append(current)
                current = None
                props = {}
            if stack:
                stack.pop()
            continue
        if current is not None:
            pm = prop_re.match(line)
            if pm:
                key, val = pm.group(1), pm.group(2).strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                props[key] = val
    return controls


def extract_procedures(text: str) -> list[tuple[str, str]]:
    return re.findall(
        r"^(?:Private |Public |Friend )?(Sub|Function|Property Get|Property Let|Property Set)\s+(\w+)",
        text,
        re.M,
    )


def extract_sql_snippets(text: str) -> list[str]:
    snippets = []
    # string concatenations containing SQL keywords
    patterns = [
        r'"[^"]*\b(SELECT|INSERT|UPDATE|DELETE|EXEC|EXECUTE|FROM|INTO|WHERE)\b[^"]*"',
        r"'\s*(SELECT|INSERT|UPDATE|DELETE|EXEC)\b[^']*'",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            s = m.group(0)
            if len(s) > 20:
                snippets.append(s[:300])
    # also multi-line SQL built via &
    sql_blocks = re.findall(
        r'(?i)((?:["\'][^"\']*(?:SELECT|INSERT|UPDATE|DELETE|EXEC)[^"\']*["\'](?:\s*&\s*(?:["\'][^"\']*["\']|\w+)){0,40}))',
        text,
    )
    for b in sql_blocks:
        if b not in snippets:
            snippets.append(b[:500])
    return snippets


def extract_msgbox(text: str) -> list[str]:
    return re.findall(r'MsgBox\s+(.+?)(?:\s*_\s*\n|\n)', text)


def extract_table_refs(text: str) -> set[str]:
    tables = set()
    for m in re.finditer(
        r'\b(FIN_PUR[A-Z0-9_]*|GL\d+|FIN_[A-Z0-9_]+|v_[A-Za-z0-9_]+|tbl[A-Za-z0-9_]+)\b',
        text,
        re.I,
    ):
        tables.add(m.group(1))
    return tables


def analyze(fname: str) -> None:
    path = BASE / fname
    text = decode(path.read_bytes())
    OUT.mkdir(exist_ok=True)
    stem = path.stem

    controls = extract_controls(text)
    procs = extract_procedures(text)
    sqls = extract_sql_snippets(text)
    msgs = extract_msgbox(text)
    tables = extract_table_refs(text)

    # Form caption / size
    form_cap = ""
    form_w = form_h = ""
    for c in controls:
        if c["type"] == "VB.Form":
            form_cap = c["props"].get("Caption", "")
            form_w = c["props"].get("ClientWidth", c["props"].get("Width", ""))
            form_h = c["props"].get("ClientHeight", c["props"].get("Height", ""))
            break

    report = []
    report.append(f"# Analysis: {fname}")
    report.append(f"Caption: {form_cap}")
    report.append(f"ClientSize: {form_w} x {form_h}")
    report.append(f"Controls: {len(controls)}")
    report.append(f"Procedures: {len(procs)}")
    report.append(f"SQL snippets: {len(sqls)}")
    report.append(f"MsgBox lines: {len(msgs)}")
    report.append("")
    report.append("## Controls")
    report.append("| Name | Type | Caption/Text | Left | Top | Width | Height | TabIndex | Visible | Enabled | Locked |")
    report.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in controls:
        if c["type"] == "VB.Form":
            continue
        p = c["props"]
        report.append(
            "| {name} | {type} | {cap} | {left} | {top} | {w} | {h} | {tab} | {vis} | {en} | {lk} |".format(
                name=c["name"],
                type=c["type"],
                cap=(p.get("Caption") or p.get("Text") or "")[:40].replace("|", "/"),
                left=p.get("Left", ""),
                top=p.get("Top", ""),
                w=p.get("Width", ""),
                h=p.get("Height", ""),
                tab=p.get("TabIndex", ""),
                vis=p.get("Visible", "True"),
                en=p.get("Enabled", "True"),
                lk=p.get("Locked", ""),
            )
        )

    report.append("")
    report.append("## Procedures")
    for kind, name in procs:
        report.append(f"- {kind} {name}")

    report.append("")
    report.append("## Table / View References")
    for t in sorted(tables, key=str.upper):
        report.append(f"- {t}")

    report.append("")
    report.append("## MsgBox / User Messages (raw)")
    for m in msgs[:200]:
        report.append(f"- {m.strip()[:200]}")

    report.append("")
    report.append("## SQL Snippets (sample)")
    for s in sqls[:150]:
        report.append(f"- `{s.replace(chr(10), ' ')[:250]}`")

    out_path = OUT / f"{stem}_analysis.md"
    out_path.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {out_path} controls={len(controls)} procs={len(procs)} sql={len(sqls)} tables={len(tables)}")

    # dump full code section separately
    code_m = re.search(r"^Attribute VB_Name.*", text, re.M)
    # better: after last End of form designer - look for Option Explicit / VERSION is designer
    code_start = text.find("Attribute VB_Name")
    if code_start < 0:
        code_start = text.find("Option Explicit")
    if code_start >= 0:
        (OUT / f"{stem}_code.bas.txt").write_text(text[code_start:], encoding="utf-8")
        print(f"  code length: {len(text) - code_start}")


if __name__ == "__main__":
    for f in ("Fin_PurM.frm", "Fin_PurD.frm"):
        analyze(f)
