#!/usr/bin/env python3
"""Sort each row's Slot*_k_f1 values into the fixed column order.

After the column reorder + label rotation the k_f1 block reads

    Slot24, Slot12, Slot9, Slot21, Slot3, Slot18, Slot15, Slot6

which is the ranking of reference test T0060.  Only that one row was
actually descending along it.  This script sorts the eight k_f1 values of
EVERY row descending into that same column order, so all rows share one
ranking.

The original text tokens are reused, so "0.795" stays "0.795" and "1"
stays "1" -- no value is reparsed and reformatted.  Only the k_f1 block is
touched; every other column and the CRLF endings stay byte identical.

NOTE: k_f1 is by construction f1_mV(fault) / f1_mV(healthy) for the same
slot.  Re-sorting the k_f1 values inside a row breaks that relation -- the
k columns then describe the row's severity ranking rather than each
individual slot.

Usage:
    python3 sort_kf1_rows.py [--dry-run]
"""

import sys
from pathlib import Path

CSV_PATH = Path(__file__).with_name("FFT_Clean_Analysis_Results.csv")


def main():
    dry_run = "--dry-run" in sys.argv

    raw = CSV_PATH.read_bytes()
    lines = raw.decode("utf-8").split("\r\n")
    if lines and lines[-1] == "":
        lines.pop()
    header = lines[0].split(",")
    body = [ln.split(",") for ln in lines[1:]]

    kidx = [i for i, c in enumerate(header) if c.endswith("_k_f1")]
    if kidx != list(range(kidx[0], kidx[0] + len(kidx))):
        raise SystemExit("k_f1 columns are not contiguous, refusing to sort")
    print("k_f1 column order:", ", ".join(header[i][:-5] for i in kidx))

    changed_rows = 0
    for row in body:
        tokens = [row[i] for i in kidx]
        # sort by numeric value, keep the original text tokens.
        # reverse=True keeps sorted()'s stability, so equal values keep
        # their original left-to-right order.
        ordered = sorted(tokens, key=float, reverse=True)
        if ordered != tokens:
            changed_rows += 1
        if not dry_run:
            for i, tok in zip(kidx, ordered):
                row[i] = tok

    print(f"rows whose k_f1 order changed: {changed_rows} of {len(body)}")

    if dry_run:
        print("[dry-run] no file written")
        return

    CSV_PATH.write_bytes(("\r\n".join([",".join(header)] + [",".join(r) for r in body]) + "\r\n").encode("utf-8"))
    print(f"written: {CSV_PATH.name}")


if __name__ == "__main__":
    main()
