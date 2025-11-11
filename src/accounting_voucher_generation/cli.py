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
from .summary_translator import translate_summaries_from_excel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accounting Voucher Generation Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 凭证生成子命令
    voucher_parser = subparsers.add_parser(
        "generate", help="Generate accounting vouchers from expense spreadsheets."
    )
    voucher_parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory that contains the input files.",
    )
    voucher_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data") / "output",
        help="Directory for generated voucher files.",
    )
    voucher_parser.add_argument(
        "--expense-file",
        default=DEFAULT_EXPENSE_FILE,
        help="Expense workbook filename.",
    )
    voucher_parser.add_argument(
        "--expense-sheet",
        help="Expense worksheet name or index (defaults to first sheet).",
    )
    voucher_parser.add_argument(
        "--expense-period",
        help="Accounting period in yyyymm format (overrides sheet name).",
    )
    voucher_parser.add_argument(
        "--employee-file",
        default=DEFAULT_EMPLOYEE_FILE,
        help="Employee workbook filename.",
    )
    voucher_parser.add_argument(
        "--subject-file",
        default=DEFAULT_SUBJECT_FILE,
        help="Subject mapping CSV filename.",
    )
    voucher_parser.add_argument(
        "--translation-map",
        type=Path,
        default=Path("data") / "translation_mapping.csv",
        help="Path to translation mapping CSV.",
    )
    voucher_parser.add_argument(
        "--translation-workers",
        type=int,
        default=3,
        help="Maximum worker threads for translation prefetch.",
    )
    voucher_parser.add_argument(
        "--translation-rps",
        type=float,
        default=0.6,
        help="Translation API requests per second limit.",
    )
    voucher_parser.add_argument(
        "--preparer", default="cissy", help="Preparer name for vouchers."
    )
    voucher_parser.add_argument(
        "--voucher-category", default="\u8bb0", help="Voucher category code."
    )
    voucher_parser.add_argument(
        "--credit-account", default="224104", help="Default credit account code."
    )
    voucher_parser.add_argument(
        "--start-seq",
        type=int,
        default=0,
        help="Starting sequence number for vouchers.",
    )

    # 摘要翻译子命令
    translate_parser = subparsers.add_parser(
        "translate", help="Translate summaries in Excel files."
    )
    translate_parser.add_argument(
        "input_file", type=Path, help="Input Excel file path."
    )
    translate_parser.add_argument(
        "--summary-column",
        default="费用摘要",
        help="Column name containing summaries to translate.",
    )
    translate_parser.add_argument(
        "--sheet", help="Worksheet name or index (defaults to first sheet)."
    )
    translate_parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path (auto-generated if not specified).",
    )
    translate_parser.add_argument(
        "--output-column",
        default="摘要翻译",
        help="Column name for translated summaries.",
    )
    translate_parser.add_argument(
        "--inplace", action="store_true", help="Modify the input file directly."
    )
    translate_parser.add_argument(
        "--translation-map",
        type=Path,
        default=Path("data") / "translation_mapping.csv",
        help="Path to translation mapping CSV.",
    )
    translate_parser.add_argument(
        "--translation-workers",
        type=int,
        default=3,
        help="Maximum worker threads for translation.",
    )
    translate_parser.add_argument(
        "--translation-rps",
        type=float,
        default=0.6,
        help="Translation API requests per second limit.",
    )
    translate_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing translations."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        return handle_generate_command(args)
    elif args.command == "translate":
        return handle_translate_command(args)
    else:
        parser.print_help()
        return 1


def handle_generate_command(args) -> int:
    """处理凭证生成命令"""
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


def handle_translate_command(args) -> int:
    """处理摘要翻译命令"""
    try:
        df_out, output_path = translate_summaries_from_excel(
            input_file=args.input_file,
            summary_column=args.summary_column,
            sheet_name=args.sheet,
            output_file=args.output_file,
            output_column=args.output_column,
            inplace=args.inplace,
            translation_mapping_path=args.translation_map,
            translation_max_workers=args.translation_workers,
            translation_requests_per_second=args.translation_rps,
            skip_existing=not args.force,
            skip_empty=True,
        )

        if df_out.empty:
            print("No data found in the input file.")
            return 1

        print("Translation completed successfully!")
        print(f"Input file: {args.input_file}")
        print(f"Output file: {output_path}")
        print(f"Processed {len(df_out)} rows")

        # 显示翻译统计
        if args.output_column in df_out.columns:
            translated_count = df_out[args.output_column].notna().sum()
            print(f"Translated summaries: {translated_count}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
