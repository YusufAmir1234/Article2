#!/usr/bin/env python3
"""Reorder the Slot* column blocks of FFT_Clean_Analysis_Results.csv.

The reference row is the 100 RPM / 10 Turn test at the highest load
(T0060, Target_A = 4.0).  Its Slot*_k_f1 values define the target slot
ordering; every Slot* column block in the file is then laid out in that
same order.

No numeric value is touched: the file is handled as raw comma separated
text tokens, so formatting, precision and the CRLF line endings survive
unchanged.  Only the column order moves.

Usage:
    python3 reorder_slot_columns.py [--dry-run]
"""

import csv
import re
import shutil
import sys
from pathlib import Path

CSV_PATH = Path(__file__).with_name("FFT_Clean_Analysis_Results.csv")
BACKUP_PATH = Path(__file__).with_name("FFT_Clean_Analysis_Results_ORIGINAL.csv")

REF_STATUS = "10 Turn"
REF_RPM = "100"
REF_TARGET_A = "4"

SLOT_RE = re.compile(r"^Slot(\d+)_")


def slot_of(column):
    m = SLOT_RE.match(column)
    return int(m.group(1)) if m else None


def reference_order(rows, header):
    """Slot numbers sorted by descending Slot*_k_f1 of the reference row."""
    hits = [
        r
        for r in rows
        if r["Status"] == REF_STATUS
        and r["RPM"] == REF_RPM
        and r["Target_A"] == REF_TARGET_A
    ]
    if len(hits) != 1:
        raise SystemExit(
            f"expected exactly 1 reference row ({REF_STATUS} / {REF_RPM} RPM / "
            f"{REF_TARGET_A} A), found {len(hits)}"
        )
    ref = hits[0]
    kcols = [c for c in header if c.endswith("_k_f1")]
    ranked = sorted(kcols, key=lambda c: -float(ref[c]))
    return ref["Test_ID"], [slot_of(c) for c in ranked], {
        slot_of(c): float(ref[c]) for c in ranked
    }


def blocks_of(header):
    """Split header indices into (is_slot_block, [indices]) runs."""
    runs = []
    for i, col in enumerate(header):
        is_slot = slot_of(col) is not None
        if runs and runs[-1][0] == is_slot:
            runs[-1][1].append(i)
        else:
            runs.append((is_slot, [i]))
    return runs


def reorder(header, order):
    rank = {slot: pos for pos, slot in enumerate(order)}
    runs = blocks_of(header)
    new_indices = []
    for is_slot, idxs in runs:
        if not is_slot:
            new_indices.extend(idxs)
            continue
        # stable sort: slots follow the reference ranking, and the columns
        # belonging to one slot keep their original relative order
        new_indices.extend(sorted(idxs, key=lambda i: rank[slot_of(header[i])]))
    return new_indices


def main():
    dry_run = "--dry-run" in sys.argv

    raw = CSV_PATH.read_bytes()
    text = raw.decode("utf-8")
    lines = text.split("\r\n")
    if lines and lines[-1] == "":
        lines.pop()  # trailing newline
    header = lines[0].split(",")
    body = [ln.split(",") for ln in lines[1:]]

    width = len(header)
    for n, row in enumerate(body, start=2):
        if len(row) != width:
            raise SystemExit(f"line {n}: {len(row)} fields, expected {width}")

    rows = list(csv.DictReader(CSV_PATH.open(newline="")))
    ref_id, order, ref_vals = reference_order(rows, header)

    print(f"reference row : {ref_id}  ({REF_STATUS} / {REF_RPM} RPM / {REF_TARGET_A} A)")
    print("slot order    : " + " > ".join(f"Slot{s} ({ref_vals[s]})" for s in order))
    print()
    print("old header order:")
    print("  " + ", ".join(header))

    new_indices = reorder(header, order)
    assert sorted(new_indices) == list(range(width)), "index mapping is broken"

    new_header = [header[i] for i in new_indices]
    print()
    print("new header order:")
    print("  " + ", ".join(new_header))

    if dry_run:
        print("\n[dry-run] no file written")
        return

    if not BACKUP_PATH.exists():
        shutil.copy2(CSV_PATH, BACKUP_PATH)
        print(f"\nbackup written: {BACKUP_PATH.name}")
    else:
        print(f"\nbackup already exists, left untouched: {BACKUP_PATH.name}")

    out_lines = [",".join(new_header)]
    out_lines += [",".join(row[i] for i in new_indices) for row in body]
    CSV_PATH.write_bytes(("\r\n".join(out_lines) + "\r\n").encode("utf-8"))
    print(f"reordered file written: {CSV_PATH.name} ({len(body)} data rows)")


if __name__ == "__main__":
    main()
