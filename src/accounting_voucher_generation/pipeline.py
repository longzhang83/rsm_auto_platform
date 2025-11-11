from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

# 直接使用多账户翻译服务
from .multi_account_translator import (
    batch_translate_texts,
    configure_translation_service,
    translate_text,
)

MULTI_ACCOUNT_AVAILABLE = True

DEFAULT_EXPENSE_FILE = "Expense.xlsx"
DEFAULT_EMPLOYEE_FILE = "人员列表.xlsx"
DEFAULT_SUBJECT_FILE = "科目映射.csv"
DEFAULT_EXPENSE_METADATA = (
    "报销形式",
    "公司",
    "审批编码",
    "姓名",
    "部门-一级部门",
    "费用科目",
    "费用摘要",
    "日期",
)
DEFAULT_EMPLOYEE_NAME_COLUMNS = ("姓名", "英文名")

OUTPUT_SCHEMA = {
    "voucher_id": "\u51ed\u8bc1ID",
    "fiscal_year": "\u4f1a\u8ba1\u5e74",
    "fiscal_period": "\u4f1a\u8ba1\u671f\u95f4",
    "voucher_date": "\u5236\u5355\u65e5\u671f",
    "voucher_category": "\u51ed\u8bc1\u7c7b\u522b",
    "voucher_no": "\u51ed\u8bc1\u53f7",
    "preparer": "\u5236\u5355\u4eba",
    "subject_code": "\u79d1\u76ee\u7f16\u7801",
    "summary": "\u6458\u8981",
    "currency": "\u5e01\u79cd\u540d\u79f0",
    "orig_debit": "\u539f\u5e01\u501f\u65b9",
    "orig_credit": "\u539f\u5e01\u8d37\u65b9",
    "debit_amount": "\u501f\u65b9\u91d1\u989d",
    "credit_amount": "\u8d37\u65b9\u91d1\u989d",
    "dept_code": "\u90e8\u95e8\u7f16\u7801",
    "staff_code": "\u804c\u5458\u7f16\u7801",
}

ADDITIONAL_OUTPUT_COLUMNS = [
    "\u5ba2\u6237\u7f16\u7801",
    "\u4f9b\u5e94\u5546\u7f16\u7801",
    "\u9879\u76ee\u5927\u7c7b\u7f16\u7801",
    "\u9879\u76ee\u7f16\u7801",
    "\u4e1a\u52a1\u5458",
    "\u81ea\u5b9a\u4e49\u98791",
    "\u81ea\u5b9a\u4e49\u98792",
    "\u81ea\u5b9a\u4e49\u98793",
    "\u81ea\u5b9a\u4e49\u98794",
    "\u81ea\u5b9a\u4e49\u98795",
    "\u81ea\u5b9a\u4e49\u98796",
    "\u81ea\u5b9a\u4e49\u98797",
    "\u81ea\u5b9a\u4e49\u98798",
    "\u81ea\u5b9a\u4e49\u98799",
    "\u81ea\u5b9a\u4e49\u987910",
    "\u81ea\u5b9a\u4e49\u987911",
    "\u81ea\u5b9a\u4e49\u987912",
    "\u81ea\u5b9a\u4e49\u987913",
    "\u81ea\u5b9a\u4e49\u987914",
    "\u81ea\u5b9a\u4e49\u987915",
    "\u81ea\u5b9a\u4e49\u987916",
    "\u73b0\u91d1\u6d41\u91cf\u9879\u76ee",
    "\u73b0\u91d1\u6d41\u91cf\u501f\u65b9\u91d1\u989d",
    "\u73b0\u91d1\u6d41\u91cf\u8d37\u65b9\u91d1\u989d",
]

OUTPUT_COLUMNS = list(OUTPUT_SCHEMA.values()) + ADDITIONAL_OUTPUT_COLUMNS


def _coerce_path(value: Path | str) -> Path:
    path = Path(value)
    return path.expanduser().resolve()


@dataclass
class EmployeeInfo:
    code: Optional[str] = None
    dept: Optional[str] = None
    english_name: Optional[str] = None


@dataclass(slots=True)
class VoucherConfig:
    data_dir: Path = field(default_factory=lambda: Path("data"))
    expense_file: str = DEFAULT_EXPENSE_FILE
    expense_sheet: Optional[Union[str, int]] = None
    expense_period: Optional[str] = None
    employee_file: str = DEFAULT_EMPLOYEE_FILE
    subject_file: str = DEFAULT_SUBJECT_FILE
    output_dir: Path = field(default_factory=lambda: Path("data") / "output")
    expense_summary_col: str = "\u8d39\u7528\u6458\u8981"
    expense_subject_col: str = "\u8d39\u7528\u79d1\u76ee"
    expense_name_col: str = "\u59d3\u540d"
    expense_date_col: str = "\u65e5\u671f"
    expense_metadata_columns: Sequence[str] = DEFAULT_EXPENSE_METADATA
    expense_amount_columns: Sequence[str] = (
        "\u5dee\u65c5\u8d39\u4ea4\u901a",
        "\u4f4f\u5bbf\u8d39",
        "\u6587\u5370\u5feb\u9012",
        "\u62db\u5f85\u8d39",
        "\u5e02\u5185\u4ea4\u901a",
        "\u6cb9\u8d39",
        "\u8fc7\u8def\u8fc7\u6865\u505c\u8f66\u8d39",
        "\u56e2\u5efa\u8d39",
        "\u56fa\u5b9a\u8d44\u4ea7",
        "IT\u5efa\u8bbe",
        "\u798f\u5229\u8d39",
        "\u529e\u516c\u8d39",
        "\u7ef4\u4fee\u8d39",
        "\u5e02\u573a\u8d39",
        "\u4f1a\u52a1\u8d39",
        "\u901a\u8baf\u8d39",
        "\u51fa\u5dee\u9910\u8865",
        "\u5176\u4ed6",
    )
    employee_name_columns: Sequence[str] = DEFAULT_EMPLOYEE_NAME_COLUMNS
    employee_english_name_col: str = "\u82f1\u6587\u540d"
    employee_code_col: str = "\u7f16\u7801"
    employee_dept_col: str = "\u90e8\u95e8"
    subject_name_col: str = "\u79d1\u76ee"
    subject_code_col: str = "\u7f16\u7801"
    voucher_category: str = "\u8bb0"
    preparer: str = "cissy"
    credit_account_default: str = "224104"
    voucher_start_sequence: int = 0
    currency_name: str = "\u4eba\u6c11\u5e01"
    translation_mapping_path: Path = field(
        default_factory=lambda: Path("data") / "translation_mapping.csv"
    )
    translation_max_workers: int = 3
    translation_requests_per_second: float = 0.6
    zhipuai_api_keys: list[str] = field(
        default_factory=list
    )  # GLM API密钥列表，支持多账户

    def resolved(self) -> "VoucherConfig":
        cfg = replace(self)
        cfg.data_dir = _coerce_path(cfg.data_dir)
        cfg.output_dir = _coerce_path(cfg.output_dir)
        cfg.translation_mapping_path = _coerce_path(cfg.translation_mapping_path)
        return cfg


def load_expense_data(
    config: VoucherConfig,
    *,
    usecols: Optional[Iterable[str]] = None,
) -> Tuple[pd.DataFrame, str]:
    file_path = config.data_dir / config.expense_file
    excel = pd.ExcelFile(file_path, engine="openpyxl")

    if config.expense_sheet is not None:
        sheet_name = config.expense_sheet
    else:
        if not excel.sheet_names:
            raise ValueError(f"No sheets found in {file_path}")
        sheet_name = excel.sheet_names[0]

    df = excel.parse(sheet_name=sheet_name, header=1, usecols=usecols)
    df.columns = [str(col).strip() for col in df.columns]
    return df, str(sheet_name)


def load_employee_data(
    config: VoucherConfig, *, usecols: Optional[Iterable[str]] = None
) -> pd.DataFrame:
    file_path = config.data_dir / config.employee_file
    df = pd.read_excel(
        file_path, header=0, engine="openpyxl", dtype=str, usecols=usecols
    )
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_subject_mapping(
    config: VoucherConfig, *, usecols: Optional[Iterable[str]] = None
) -> pd.DataFrame:
    file_path = config.data_dir / config.subject_file
    df = pd.read_csv(file_path, header=0, usecols=usecols, encoding="utf-8-sig")
    df.columns = [str(col).strip() for col in df.columns]
    return df


def _build_subject_map(df: pd.DataFrame, config: VoucherConfig) -> Dict[str, str]:
    subject_map: Dict[str, str] = {}
    for _, row in df.iterrows():
        name = str(row.get(config.subject_name_col, "")).strip()
        code = str(row.get(config.subject_code_col, "")).strip()
        if not name or not code:
            continue
        subject_map[name] = code
    return subject_map


def _build_employee_map(
    df: pd.DataFrame, config: VoucherConfig
) -> Dict[str, EmployeeInfo]:
    employee_map: Dict[str, EmployeeInfo] = {}

    for _, row in df.iterrows():
        info = EmployeeInfo(
            code=str(row.get(config.employee_code_col, "")).strip() or None,
            dept=str(row.get(config.employee_dept_col, "")).strip() or None,
            english_name=str(row.get(config.employee_english_name_col, "")).strip()
            or None,
        )

        for col_name in config.employee_name_columns:
            if col_name not in df.columns:
                continue
            candidate = str(row.get(col_name, "")).strip()
            if candidate:
                employee_map[candidate] = info

        if info.english_name:
            employee_map[info.english_name] = info

    return employee_map


def _last_day_of_period(year: int, month: int) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)


def _coerce_amount(value: object) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if abs(amount) < 1e-9:
        return None
    return round(amount, 2)


def _resolve_amount_columns(
    expense_df: pd.DataFrame, config: VoucherConfig
) -> List[str]:
    return [col for col in config.expense_amount_columns if col in expense_df.columns]


def _iter_rows_with_progress(df: pd.DataFrame, description: str):
    iterator = df.iterrows()
    if tqdm is None:
        for item in iterator:
            yield item
        return

    with tqdm(total=len(df), desc=description, unit="\u884c") as progress:  # 行
        for item in iterator:
            progress.update(1)
            yield item


def _map_subject(
    expense_col: str, row: pd.Series, subject_map: Dict[str, str], config: VoucherConfig
) -> Optional[str]:
    expense_name = str(expense_col).strip()
    subject_field = str(row.get(config.expense_subject_col, "")).strip()
    summary_field = str(row.get(config.expense_summary_col, "")).strip()

    if not expense_name:
        return None

    if subject_field:
        key = f"{expense_name}-{subject_field}"
        if key in subject_map:
            return subject_map[key]

    if expense_name in subject_map:
        return subject_map[expense_name]

    if subject_field in subject_map:
        return subject_map[subject_field]

    if summary_field in subject_map:
        return subject_map[summary_field]

    return None


def _compose_summary(
    chinese_name: str,
    chinese_desc: str,
    english_name: Optional[str],
    english_desc: str,
) -> str:
    cn_parts = [part for part in (chinese_name.strip(), chinese_desc.strip()) if part]
    en_parts = [
        part for part in ((english_name or "").strip(), english_desc.strip()) if part
    ]

    cn_segment = "-".join(cn_parts)
    en_segment = "-".join(en_parts)

    if cn_segment and en_segment:
        return f"{cn_segment}/{en_segment}"
    return cn_segment or en_segment


def _init_output_row() -> Dict[str, object]:
    row = {column: "" for column in OUTPUT_COLUMNS}
    for amount_field in (
        OUTPUT_SCHEMA["orig_debit"],
        OUTPUT_SCHEMA["orig_credit"],
        OUTPUT_SCHEMA["debit_amount"],
        OUTPUT_SCHEMA["credit_amount"],
        "\u73b0\u91d1\u6d41\u91cf\u501f\u65b9\u91d1\u989d",
        "\u73b0\u91d1\u6d41\u91cf\u8d37\u65b9\u91d1\u989d",
    ):
        row[amount_field] = 0.0
    return row


def _apply_payload(row: Dict[str, object], payload: Dict[str, object]) -> None:
    for key, column_name in OUTPUT_SCHEMA.items():
        if key in payload:
            row[column_name] = payload[key]


def generate_vouchers(
    config: VoucherConfig,
    *,
    expense_df: Optional[pd.DataFrame] = None,
    employee_df: Optional[pd.DataFrame] = None,
    subject_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    cfg = config.resolved()

    # 初始化多账户翻译服务（如果可用）
    if MULTI_ACCOUNT_AVAILABLE and cfg.zhipuai_api_keys:
        try:
            configure_translation_service(
                api_keys=cfg.zhipuai_api_keys,
                cache_path=cfg.translation_mapping_path,
                max_workers=cfg.translation_max_workers,
            )
            print(f"已初始化多账户翻译服务，共 {len(cfg.zhipuai_api_keys)} 个API密钥")
        except Exception as e:
            print(f"初始化多账户翻译服务失败: {e}")
            print("将使用原有的翻译服务")

    if expense_df is None:
        expense_df, sheet_name = load_expense_data(cfg)
        raw_period = cfg.expense_period or str(sheet_name).strip()
    else:
        raw_period = (cfg.expense_period or "").strip()

    employee_df = employee_df if employee_df is not None else load_employee_data(cfg)
    subject_df = subject_df if subject_df is not None else load_subject_mapping(cfg)

    subject_map = _build_subject_map(subject_df, cfg)
    employee_map = _build_employee_map(employee_df, cfg)
    amount_columns = _resolve_amount_columns(expense_df, cfg)

    voucher_rows: List[Dict[str, object]] = []
    voucher_seq = cfg.voucher_start_sequence
    translation_cache: Dict[str, str] = {}

    unique_descriptions: set[str] = set()
    for _, row in expense_df.iterrows():
        for column in amount_columns:
            amount = _coerce_amount(row.get(column))
            if amount is None:
                continue
            chinese_desc = (
                str(row.get(cfg.expense_summary_col, "")).strip() or str(column).strip()
            )
            if chinese_desc:
                unique_descriptions.add(chinese_desc)

    prefetched_translations = batch_translate_texts(
        unique_descriptions,
        max_workers=cfg.translation_max_workers,
        requests_per_second=cfg.translation_requests_per_second,
        progress_description="\u7ffb\u8bd1\u6458\u8981",
        mapping_path=cfg.translation_mapping_path,
    )
    translation_cache.update(prefetched_translations)

    def _derive_period() -> Tuple[int, int]:
        if raw_period and len(raw_period) == 6 and raw_period.isdigit():
            year = int(raw_period[:4])
            month = int(raw_period[4:])
            if 1 <= month <= 12:
                return year, month
        raise ValueError(
            "\u65e0\u6cd5\u4ece\u8d39\u7528\u8868\u5de5\u4f5c\u8868\u540d\u6216\u914d\u7f6e\u4e2d\u89e3\u6790\u4f1a\u8ba1\u671f\u95f4\uff08\u9700\u8981 yyyymm \u683c\u5f0f\uff09"
        )

    sheet_year, sheet_month = _derive_period()

    for _, row in _iter_rows_with_progress(expense_df, "\u751f\u6210\u51ed\u8bc1"):
        name_value = str(row.get(cfg.expense_name_col, "")).strip()
        if not name_value:
            continue

        employee_info = employee_map.get(name_value)
        english_name_value = employee_info.english_name if employee_info else None

        line_items: List[Tuple[str, float, str]] = []
        for column in amount_columns:
            amount = _coerce_amount(row.get(column))
            if amount is None:
                continue

            chinese_desc = (
                str(row.get(cfg.expense_summary_col, "")).strip() or str(column).strip()
            )
            if not chinese_desc:
                continue

            if chinese_desc not in translation_cache:
                translation_cache[chinese_desc] = translate_text(
                    chinese_desc,
                    mapping_path=cfg.translation_mapping_path,
                )
            english_desc = translation_cache[chinese_desc]

            summary = _compose_summary(
                name_value, chinese_desc, english_name_value, english_desc
            )
            debit_code = _map_subject(column, row, subject_map, cfg) or ""

            line_items.append((summary, amount, debit_code))

        if not line_items:
            continue

        voucher_seq += 1

        v_year, v_period = sheet_year, sheet_month
        v_date = _last_day_of_period(v_year, v_period).strftime("%Y/%m/%d")

        voucher_id = f"{v_period:02d}{voucher_seq:04d}"
        voucher_no = f"{voucher_seq:04d}"
        credit_code = cfg.credit_account_default

        dept_code = employee_info.dept if employee_info else ""
        emp_code = employee_info.code if employee_info else ""

        base_payload = {
            "voucher_id": voucher_id,
            "fiscal_year": v_year,
            "fiscal_period": v_period,
            "voucher_date": v_date,
            "voucher_category": cfg.voucher_category,
            "voucher_no": voucher_no,
            "preparer": cfg.preparer,
            "currency": cfg.currency_name,
        }

        # 计算总金额，用于合并贷方
        total_amount = sum(amount for _, amount, _ in line_items)

        # 为每个借方费用项生成分录
        for summary, amount, debit_code in line_items:
            line_payload = {**base_payload, "summary": summary}

            debit_line = _init_output_row()
            _apply_payload(debit_line, line_payload)
            debit_line[OUTPUT_SCHEMA["subject_code"]] = debit_code
            debit_line[OUTPUT_SCHEMA["orig_debit"]] = amount
            debit_line[OUTPUT_SCHEMA["orig_credit"]] = 0.0
            debit_line[OUTPUT_SCHEMA["debit_amount"]] = amount
            debit_line[OUTPUT_SCHEMA["credit_amount"]] = 0.0
            debit_line[OUTPUT_SCHEMA["dept_code"]] = ""
            debit_line[OUTPUT_SCHEMA["staff_code"]] = ""

            voucher_rows.append(debit_line)

        # 生成一条合并的贷方分录
        if total_amount > 0:
            # 收集所有唯一的中文和英文费用描述
            chinese_expenses = set()
            english_expenses = set()

            for summary, amount, debit_code in line_items:
                # 从summary中提取中文和英文部分
                parts = summary.split("/")
                chinese_part = (
                    parts[0].split("-", 1)[-1]
                    if len(parts) > 0 and "-" in parts[0]
                    else parts[0]
                    if parts
                    else ""
                )
                english_part = (
                    parts[1].split("-", 1)[-1]
                    if len(parts) > 1 and "-" in parts[1]
                    else parts[1]
                    if len(parts) > 1
                    else ""
                )

                if chinese_part:
                    chinese_expenses.add(chinese_part.strip())
                if english_part:
                    english_expenses.add(english_part.strip())

            # 合并费用描述
            chinese_expense_desc = (
                "&".join(sorted(chinese_expenses)) if chinese_expenses else "费用合并"
            )
            english_expense_desc = (
                ", ".join(sorted(english_expenses))
                if english_expenses
                else "expenses combined"
            )

            credit_summary = _compose_summary(
                name_value,
                chinese_expense_desc,
                english_name_value,
                english_expense_desc,
            )
            credit_payload = {**base_payload, "summary": credit_summary}

            credit_line = _init_output_row()
            _apply_payload(credit_line, credit_payload)
            credit_line[OUTPUT_SCHEMA["subject_code"]] = credit_code
            credit_line[OUTPUT_SCHEMA["orig_debit"]] = 0.0
            credit_line[OUTPUT_SCHEMA["orig_credit"]] = total_amount
            credit_line[OUTPUT_SCHEMA["debit_amount"]] = 0.0
            credit_line[OUTPUT_SCHEMA["credit_amount"]] = total_amount
            credit_line[OUTPUT_SCHEMA["dept_code"]] = dept_code or ""
            credit_line[OUTPUT_SCHEMA["staff_code"]] = emp_code or ""

            voucher_rows.append(credit_line)

    output_dir = cfg.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df_out = pd.DataFrame(voucher_rows, columns=OUTPUT_COLUMNS)
    if df_out.empty:
        return df_out

    df_out.to_csv(output_dir / "vouchers.csv", index=False, encoding="utf-8-sig")
    try:
        df_out.to_excel(output_dir / "vouchers.xlsx", index=False, engine="openpyxl")
    except ModuleNotFoundError:
        pass

    return df_out
