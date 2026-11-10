#!/usr/bin/env python3
"""Convert FFT_Clean_Analysis_Results.csv to FFT_Clean_Analysis_Results.xlsx.

Numeric columns are written as real numbers (not text) so Excel can sort,
chart and compute on them; Test_ID / Status stay text.  The empty
I_Fault_RMS cells of the Healthy rows stay genuinely empty rather than
becoming 0 or "".

Requires openpyxl:
    python3 -m venv .venv && ./.venv/bin/pip install openpyxl
    ./.venv/bin/python csv_to_xlsx.py
"""

import csv
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

CSV_PATH = Path(__file__).with_name("FFT_Clean_Analysis_Results.csv")
XLSX_PATH = Path(__file__).with_name("FFT_Clean_Analysis_Results.xlsx")
SHEET_NAME = "Results"

INT_RE = re.compile(r"^-?\d+$")
FLOAT_RE = re.compile(r"^-?\d*\.\d+$")


def convert(token):
    """CSV text token -> Excel cell value. Empty stays empty."""
    if token.strip() == "":
        return None
    if INT_RE.match(token):
        return int(token)
    if FLOAT_RE.match(token):
        return float(token)
    return token  # anything unexpected is kept verbatim as text


def main():
    with CSV_PATH.open(newline="") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], rows[1:]

    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME

    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in body:
        ws.append([convert(t) for t in row])

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(body) + 1}"

    # column widths from the widest value, so nothing shows as ###
    for idx in range(len(header)):
        widest = max(
            len(str(ws.cell(row=r, column=idx + 1).value or ""))
            for r in range(1, len(body) + 2)
        )
        ws.column_dimensions[get_column_letter(idx + 1)].width = widest + 2

    wb.save(XLSX_PATH)
    print(f"written: {XLSX_PATH.name}  ({len(body)} data rows x {len(header)} cols, sheet '{SHEET_NAME}')")


if __name__ == "__main__":
    main()
