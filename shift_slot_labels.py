#!/usr/bin/env python3
"""Rotate the Slot labels of FFT_Clean_Analysis_Results.csv by one step.

The sensors sit on every third slot of a 24 slot stator, so the labels run
3, 6, 9, 12, 15, 18, 21, 24.  Shifting by one position means every label
takes the next value in that cycle:

    Slot3 -> Slot6    Slot6 -> Slot9    Slot9  -> Slot12   Slot12 -> Slot15
    Slot15 -> Slot18  Slot18 -> Slot21  Slot21 -> Slot24   Slot24 -> Slot3

Only the column headers are renamed; the measured values stay exactly where
they are.  Because the mapping is a bijection this is the same file you
would get by moving each slot's data into the next slot's columns: the
column now called Slot24_f1_mV holds the numbers that used to be labelled
Slot21_f1_mV.

No numeric value is parsed or rewritten, so precision, empty cells and the
CRLF line endings survive untouched.

Usage:
    python3 shift_slot_labels.py [--dry-run] [--inverse]
"""

import re
import sys
from pathlib import Path

CSV_PATH = Path(__file__).with_name("FFT_Clean_Analysis_Results.csv")
STEP = 3
CYCLE_MAX = 24

SLOT_RE = re.compile(r"^Slot(\d+)_")


def shifted(slot):
    """Next label in the 3..24 cycle, `STEP` at a time."""
    new = slot + STEP if slot + STEP <= CYCLE_MAX else slot + STEP - CYCLE_MAX
    return new


def main():
    dry_run = "--dry-run" in sys.argv
    inverse = "--inverse" in sys.argv

    raw = CSV_PATH.read_bytes()
    lines = raw.decode("utf-8").split("\r\n")
    if lines and lines[-1] == "":
        lines.pop()
    header = lines[0].split(",")
    body = [ln.split(",") for ln in lines[1:]]

    slots = sorted({int(SLOT_RE.match(c).group(1)) for c in header if SLOT_RE.match(c)})
    mapping = {s: shifted(s) for s in slots}
    if inverse:
        mapping = {v: k for k, v in mapping.items()}

    if len(set(mapping.values())) != len(mapping):
        raise SystemExit("mapping is not a bijection, refusing to relabel")

    new_header = []
    for col in header:
        m = SLOT_RE.match(col)
        new_header.append(f"Slot{mapping[int(m.group(1))]}_{col[m.end():]}" if m else col)

    # The header is only a permutation of itself when every slot carries the
    # same sub-columns.  Here Slot24 is the only slot with f1_Hz / Dom_Hz, so
    # relabelling it legitimately creates names that did not exist before.
    # The invariants that must hold instead: no duplicate names, and the
    # multiset of sub-column suffixes unchanged.
    def suffixes(cols):
        return sorted(c[m.end():] for c in cols if (m := SLOT_RE.match(c)))

    if len(set(new_header)) != len(new_header):
        raise SystemExit("relabelled header contains duplicates")
    if suffixes(new_header) != suffixes(header):
        raise SystemExit("relabelled header changed the set of sub-columns")
    if len(new_header) != len(header):
        raise SystemExit("column count changed")

    print("label shift: " + "  ".join(f"Slot{k}->Slot{v}" for k, v in sorted(mapping.items())))
    print()
    for old, new in zip(header, new_header):
        flag = "   (moved)" if old != new else ""
        print(f"  {old:20s} -> {new:20s}{flag}")

    if dry_run:
        print("\n[dry-run] no file written")
        return

    # body rows are written back verbatim: only the header line changes
    CSV_PATH.write_bytes(("\r\n".join([",".join(new_header)] + [",".join(r) for r in body]) + "\r\n").encode("utf-8"))
    print(f"\nrelabeled file written: {CSV_PATH.name} ({len(body)} data rows, body untouched)")


if __name__ == "__main__":
    main()
