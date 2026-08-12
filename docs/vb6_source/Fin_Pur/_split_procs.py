from pathlib import Path
import re

base = Path(__file__).resolve().parent / "_analysis"
for stem in ("Fin_PurM", "Fin_PurD"):
    text = (base / f"{stem}_code.bas.txt").read_text(encoding="utf-8", errors="replace")
    parts = re.split(
        r"(?=^(?:Private |Public |Friend )?(?:Sub|Function|Property Get|Property Let|Property Set)\s+\w+)",
        text,
        flags=re.M,
    )
    out = base / f"{stem}_procs"
    out.mkdir(exist_ok=True)
    names = []
    for p in parts:
        m = re.match(
            r"(?:Private |Public |Friend )?(Sub|Function|Property Get|Property Let|Property Set)\s+(\w+)",
            p,
        )
        if not m:
            continue
        kind, name = m.group(1), m.group(2)
        names.append(f"{kind} {name} ({len(p)} chars)")
        (out / f"{name}.txt").write_text(p, encoding="utf-8")
    print(stem, "procs", len(names))
    for n in names:
        print(" ", n)
