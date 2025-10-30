# -*- coding: utf-8 -*-
"""
Convert the tab-separated mapping in 1.txt into CSV rows of the form:
"columnHeader-rowHeader,code"

Usage:
    python3 scripts/convert_mapping.py ../1.txt

Writes a UTF-8 CSV next to the input file named like: 科目映射_YYYYMMDD.csv
"""
import csv
import sys
from pathlib import Path
from datetime import datetime


def read_table(path: Path):
    # read and normalize line endings, handle BOM
    text = path.read_text(encoding='utf-8-sig')
    lines = [ln for ln in text.splitlines() if ln.strip()]
    rows = [ln.split('\t') for ln in lines]
    return rows


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('1.txt')
    if not in_path.exists():
        print(f'Input file not found: {in_path}')
        return
    rows = read_table(in_path)
    if len(rows) < 2:
        print('需要至少两行（表头 + 一行数据）')
        return
    headers = rows[0]
    out_rows = []
    for r in range(1, len(rows)):
        row = rows[r]
        if not row:
            continue
        row_header = row[0].strip()
        for c in range(1, max(len(headers), len(row))):
            col_header = headers[c].strip() if c < len(headers) else ''
            code = row[c].strip() if c < len(row) else ''
            if not col_header or not code:
                continue
            combined = f"{col_header}-{row_header}"
            out_rows.append((combined, code))
    date = datetime.now().strftime('%Y%m%d')
    out_name = in_path.parent / f'科目映射_{date}.csv'
    with out_name.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['科目', '编码'])
        writer.writerows(out_rows)
    print(f'Wrote {len(out_rows)} rows to {out_name}')


if __name__ == '__main__':
    main()
