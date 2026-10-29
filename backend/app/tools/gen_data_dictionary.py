"""Generate docs/data_dictionary.md from the SQLAlchemy models (single source of truth).
Run from backend/:  python -m app.tools.gen_data_dictionary
"""
import re
from pathlib import Path

from app.models import Base

OUT = Path(__file__).resolve().parents[3] / "docs" / "data_dictionary.md"

UNITS = {"qty": "units (each)", "quantity": "units (each)", "delta": "units (each)", "cost": "USD",
         "price": "USD", "_pct": "percent", "days": "days", "_at": "UTC timestamp",
         "_on": "date", "_from": "date", "_to": "date"}


def units(name: str) -> str:
    for key, val in UNITS.items():
        if key in name:
            return val
    return "—"


def allowed(table, col) -> str:
    out = []
    for ck in table.constraints:
        txt = str(getattr(ck, "sqltext", ""))
        m = re.match(rf"{col.name} IN \((.*)\)$", txt)
        if m:
            out.append(m.group(1).replace("'", "").replace(", ", " \\| "))
    return out[0] if out else "—"


def rules(table, col) -> str:
    rs = []
    for ck in table.constraints:
        txt = str(getattr(ck, "sqltext", ""))
        if txt and re.search(rf"\b{col.name}\b", txt) and " IN (" not in txt:
            rs.append(f"`{txt}`")
    return "<br>".join(rs) or "—"


def main():
    lines = ["# Data Dictionary", "",
             "_Generated from `backend/app/models/models.py` by `python -m app.tools.gen_data_dictionary`. "
             "Do not edit by hand._", "",
             "All data is **synthetic**. No real customer or confidential inventory information is used.", ""]
    for t in Base.metadata.sorted_tables:
        lines += [f"## `{t.name}`", ""]
        lines += ["| Field | Type | Required | Allowed values | Units | Unique | Foreign key | Validation rules | Description |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for col in t.columns:
            fks = ", ".join(f"`{f.target_fullname}`" for f in col.foreign_keys) or "—"
            uniq = "PK" if col.primary_key else ("yes" if col.unique else "—")
            req = "yes" if (not col.nullable and col.server_default is None and col.default is None) or col.primary_key else (
                "no" if col.nullable else "default")
            lines.append(f"| `{col.name}` | {col.type} | {req} | {allowed(t, col)} | {units(col.name)} | {uniq} | {fks} | {rules(t, col)} | {col.comment} |")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
