from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import (
	DEFAULT_EMPLOYEE_FILE,
	DEFAULT_EXPENSE_FILE,
	DEFAULT_SUBJECT_FILE,
	VoucherConfig,
	generate_vouchers,
)


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Generate accounting vouchers from expense spreadsheets."
	)
	parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Directory that contains the input files.")
	parser.add_argument("--output-dir", type=Path, default=Path("data") / "output", help="Directory for generated voucher files.")
	parser.add_argument("--expense-file", default=DEFAULT_EXPENSE_FILE, help="Expense workbook filename.")
	parser.add_argument("--expense-sheet", help="Expense worksheet name or index (defaults to first sheet).")
	parser.add_argument("--expense-period", help="Accounting period in yyyymm format (overrides sheet name).")
	parser.add_argument("--employee-file", default=DEFAULT_EMPLOYEE_FILE, help="Employee workbook filename.")
	parser.add_argument("--subject-file", default=DEFAULT_SUBJECT_FILE, help="Subject mapping CSV filename.")
	parser.add_argument("--translation-map", type=Path, default=Path("data") / "translation_mapping.csv", help="Path to translation mapping CSV.")
	parser.add_argument("--translation-workers", type=int, default=3, help="Maximum worker threads for translation prefetch.")
	parser.add_argument("--translation-rps", type=float, default=0.6, help="Translation API requests per second limit.")
	parser.add_argument("--preparer", default="cissy", help="Preparer name for vouchers.")
	parser.add_argument("--voucher-category", default="\u8bb0", help="Voucher category code.")
	parser.add_argument("--credit-account", default="224104", help="Default credit account code.")
	parser.add_argument("--start-seq", type=int, default=0, help="Starting sequence number for vouchers.")
	return parser


def main(argv: list[str] | None = None) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)

	config = VoucherConfig(
		data_dir=args.data_dir,
		output_dir=args.output_dir,
		expense_file=args.expense_file,
		expense_sheet=args.expense_sheet,
		expense_period=args.expense_period,
		employee_file=args.employee_file,
		subject_file=args.subject_file,
		translation_mapping_path=args.translation_map,
		translation_max_workers=max(1, args.translation_workers),
		translation_requests_per_second=max(args.translation_rps, 0.05),
		preparer=args.preparer,
		voucher_category=args.voucher_category,
		credit_account_default=args.credit_account,
		voucher_start_sequence=args.start_seq,
	)

	df_out = generate_vouchers(config)

	if df_out.empty:
		print("No voucher entries generated; check input data.")
	else:
		print(f"Generated {len(df_out)} voucher lines in {config.output_dir}")

	return 0


if __name__ == "__main__":
	sys.exit(main())
