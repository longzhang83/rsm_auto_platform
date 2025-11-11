from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

from .multi_account_translator import (
    batch_translate_texts,
    configure_translation_service,
)

logger = logging.getLogger(__name__)

# 银行流水相关常量
DEFAULT_BANK_STATEMENT_FILE = "20Cube银行流水202509.xlsx"
DEFAULT_BANK_STATEMENT_MAPPING_FILE = "银行流水列名mapping.xlsx"
DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE = "会计科目mapping.xlsx"

# 银行流水凭证输出格式
BANK_STATEMENT_OUTPUT_SCHEMA = {
    "date": "日期",
    "voucher_no": "编号",
    "attachment": "附件",
    "summary": "*摘要",
    "subject_code": "*科目代码",
    "subject_name": "科目名称",
    "currency": "币别",
    "contact": "联系人",
    "employee": "员工",
    "product": "商品",
    "expense_item": "费用项目",
    "cost_center": "跟踪项:成本中心",
    "intracompany_code": "跟踪项:Intracompany partner code",
    "orig_amount": "原币金额",
    "debit": "*借方",
    "credit": "*贷方",
    "preparer": "制单",
    "reviewer": "审核",
    "status": "状态",
}

BANK_STATEMENT_ADDITIONAL_COLUMNS = [
    "客户编码",
    "供应商编码",
    "项目大类编码",
    "项目编码",
    "业务员",
    "自定义项1",
    "自定义项2",
    "自定义项3",
    "自定义项4",
    "自定义项5",
    "自定义项6",
    "自定义项7",
    "自定义项8",
    "自定义项9",
    "自定义项10",
    "自定义项11",
    "自定义项12",
    "自定义项13",
    "自定义项14",
    "自定义项15",
    "自定义项16",
    "现金流量项目",
    "现金流量借方金额",
    "现金流量贷方金额",
]

BANK_STATEMENT_OUTPUT_COLUMNS = (
    list(BANK_STATEMENT_OUTPUT_SCHEMA.values()) + BANK_STATEMENT_ADDITIONAL_COLUMNS
)


#
def _coerce_path(value: Path | str) -> Path:
    path = Path(value)
    return path.expanduser().resolve()


@dataclass
class BankStatementConfig:
    """银行流水处理配置"""

    data_dir: Path = field(default_factory=lambda: Path("data"))
    bank_statement_file: str = DEFAULT_BANK_STATEMENT_FILE
    bank_statement_sheet: Optional[Union[str, int]] = None
    customer_name: str = ""
    bank_name: str = ""  # 银行名称
    column_mapping_file: str = DEFAULT_BANK_STATEMENT_MAPPING_FILE
    subject_mapping_file: str = DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE
    output_dir: Path = field(
        default_factory=lambda: Path("data") / "output" / "银行流水转凭证"
    )

    # 默认字段映射
    default_date_column: str = "日期"
    default_counterparty_column: str = "对方户名"
    default_summary_column: str = "摘要"
    default_debit_column: str = "借方"
    default_credit_column: str = "贷方"

    # 凭证配置（使用默认值）
    currency_name: str = "CNY"
    preparer: str = "系统"  # 制单人，使用默认值
    voucher_start_sequence: int = 0  # 凭证起始序号

    # 翻译配置
    translation_mapping_path: Path = field(
        default_factory=lambda: Path("data") / "translation_mapping.csv"
    )
    translation_max_workers: int = 12
    translation_requests_per_second: float = 15
    zhipuai_api_keys: list[str] = field(default_factory=list)
    enable_translation: bool = False  # 是否启用翻译功能

    # 进度回调函数（可选）
    progress_callback: Optional[callable] = None
    cancel_check: Optional[callable] = None

    def resolved(self) -> "BankStatementConfig":
        cfg = replace(self)
        cfg.data_dir = _coerce_path(cfg.data_dir)
        cfg.output_dir = _coerce_path(cfg.output_dir)
        cfg.translation_mapping_path = _coerce_path(cfg.translation_mapping_path)
        return cfg


def load_bank_statement_data(
    config: BankStatementConfig, *, usecols: Optional[Iterable[str]] = None
) -> pd.DataFrame:
    """加载银行流水数据"""
    file_path = config.data_dir / config.bank_statement_file
    excel = pd.ExcelFile(file_path, engine="openpyxl")

    if config.bank_statement_sheet is not None:
        sheet_name = config.bank_statement_sheet
    else:
        if not excel.sheet_names:
            raise ValueError(f"No sheets found in {file_path}")
        sheet_name = excel.sheet_names[0]

    df = excel.parse(sheet_name=sheet_name, header=0, usecols=usecols)
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_bank_statement_data_from_bytes(
    file_bytes: bytes,
    file_name: str,
    config: BankStatementConfig,
    column_mapping: Dict[str, str],
    *,
    usecols: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """从字节数据直接加载银行流水数据"""
    import io

    # 根据文件扩展名选择处理方式
    file_extension = Path(file_name).suffix.lower()
    date_col = column_mapping.get("date")
    if file_extension in [".xlsx", ".xls"]:
        # 使用BytesIO在内存中处理Excel文件
        excel_file = io.BytesIO(file_bytes)

        if config.bank_statement_sheet is not None:
            sheet_name = config.bank_statement_sheet
        else:
            # 默认使用第一个工作表
            sheet_name = 0

        # 直接使用pd.read_excel，不在加载阶段进行日期解析
        read_excel_kwargs = {
            "io": excel_file,
            "sheet_name": sheet_name,
            "header": 0,
            "engine": "openpyxl",
            "parse_dates": [date_col],  # 不进行日期解析
        }

        if usecols:
            read_excel_kwargs["usecols"] = usecols

        df = pd.read_excel(**read_excel_kwargs)
    elif file_extension == ".csv":
        # 处理CSV文件
        import io

        csv_file = io.StringIO(file_bytes.decode("utf-8"))

        # 直接使用pd.read_csv，不在加载阶段进行日期解析
        read_csv_kwargs = {"filepath_or_buffer": csv_file, "encoding": "utf-8"}

        if usecols:
            read_csv_kwargs["usecols"] = usecols

        logger.info("[数据加载] 调用pd.read_csv加载CSV文件，不进行日期解析")
        df = pd.read_csv(**read_csv_kwargs)
    else:
        raise ValueError(f"不支持的文件格式: {file_extension}")

    # 清理列名
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_bank_statement_column_mapping(config: BankStatementConfig) -> pd.DataFrame:
    """加载银行流水列名映射"""
    file_path = config.data_dir / config.column_mapping_file
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_accounting_subject_mapping(config: BankStatementConfig) -> pd.DataFrame:
    """加载会计科目映射"""
    file_path = config.data_dir / config.subject_mapping_file
    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = [str(col).strip() for col in df.columns]
    return df


def get_column_mapping_for_customer(
    column_mapping_df: pd.DataFrame,
    customer_name: str,
    config: BankStatementConfig,
    bank_name: Optional[str] = None,
) -> Dict[str, str]:
    """获取指定客户的列名映射（支持银行名称）"""

    # 1. 优先尝试客户+银行精确匹配
    if bank_name and bank_name.strip():
        bank_name = bank_name.strip()
        logger.info(
            f"[列名映射] 尝试客户+银行精确匹配: {customer_name} + '{bank_name}' (长度: {len(bank_name)})"
        )

        # 显示可用的银行选项
        customer_banks = (
            column_mapping_df[column_mapping_df.iloc[:, 0] == customer_name]
            .iloc[:, 1]
            .unique()
        )
        logger.info(
            f"[列名映射] 客户 {customer_name} 可用的银行选项: {list(customer_banks)}"
        )

        exact_match = column_mapping_df[
            (column_mapping_df.iloc[:, 0] == customer_name)
            & (column_mapping_df.iloc[:, 1] == bank_name)
        ]
        if not exact_match.empty:
            logger.info(
                f"[列名映射] 找到客户+银行精确匹配: {customer_name} + {bank_name}"
            )
            mapping = exact_match.iloc[0].to_dict()
            return _build_mapping_from_row(mapping, config)
        else:
            logger.info(
                f"[列名映射] 客户+银行精确匹配失败: {customer_name} + {bank_name}，尝试仅客户匹配"
            )

    # 2. Fallback到仅客户名称匹配（向后兼容）
    customer_rows = column_mapping_df[column_mapping_df.iloc[:, 0] == customer_name]
    if not customer_rows.empty:
        if bank_name and bank_name.strip():
            logger.info(
                f"[列名映射] 使用客户 {customer_name} 的第一条记录（银行 {bank_name} 未找到）"
            )
        else:
            logger.info(
                f"[列名映射] 使用客户 {customer_name} 的第一条记录（未指定银行）"
            )

        mapping = customer_rows.iloc[0].to_dict()
        return _build_mapping_from_row(mapping, config)

    # 3. 最后使用默认配置
    logger.warning(f"[列名映射] 客户 {customer_name} 未找到任何映射配置，使用默认配置")
    return _get_default_mapping(config)


def _build_mapping_from_row(
    mapping: Dict[str, Any], config: BankStatementConfig
) -> Dict[str, str]:
    """从数据行构建映射字典"""
    # 处理NaN值，避免JSON序列化错误
    cleaned_mapping = {}
    for key, value in mapping.items():
        if pd.isna(value):
            cleaned_mapping[key] = None
        else:
            cleaned_mapping[key] = (
                str(value).strip() if isinstance(value, str) else value
            )

    return {
        "date": cleaned_mapping.get("日期", config.default_date_column),
        "counterparty": cleaned_mapping.get(
            "对方户名", config.default_counterparty_column
        ),
        "summary": cleaned_mapping.get("摘要", config.default_summary_column),
        "debit": cleaned_mapping.get("借方", config.default_debit_column),
        "credit": cleaned_mapping.get("贷方", config.default_credit_column),
        "amount": cleaned_mapping.get("金额", ""),  # 仅用于单列金额格式
        "bank_account": cleaned_mapping.get("银行账号", ""),
        "payer_account": cleaned_mapping.get("付款人账号", ""),
        "payer_name": cleaned_mapping.get("付款人名称", ""),
        "payee_account": cleaned_mapping.get("收款人账号", ""),
        "payee_name": cleaned_mapping.get("收款人名称", ""),
    }


def _get_default_mapping(config: BankStatementConfig) -> Dict[str, str]:
    """获取默认映射配置"""
    return {
        "date": config.default_date_column,
        "counterparty": config.default_counterparty_column,
        "summary": config.default_summary_column,
        "debit": config.default_debit_column,
        "credit": config.default_credit_column,
        "amount": "",  # 仅用于单列金额格式
        "bank_account": "",
        "payer_account": "",
        "payer_name": "",
        "payee_account": "",
        "payee_name": "",
    }


def get_customer_banks(
    column_mapping_df: pd.DataFrame, customer_name: str
) -> List[str]:
    """获取客户对应的银行列表"""
    try:
        customer_rows = column_mapping_df[column_mapping_df.iloc[:, 0] == customer_name]
        banks = customer_rows.iloc[:, 1].dropna().unique().tolist()

        # 过滤掉空值和"默认"值
        valid_banks = []
        for bank in banks:
            bank_str = str(bank).strip()
            if (
                bank_str
                and bank_str.lower() != "nan"
                and bank_str.lower() != "default"
                and bank_str.lower() != "默认"
            ):
                valid_banks.append(bank_str)

        logger.info(f"[银行列表] 客户 {customer_name} 的可用银行: {valid_banks}")
        return valid_banks

    except Exception as e:
        logger.error(f"[银行列表] 获取客户 {customer_name} 银行列表失败: {e}")
        return []


def get_available_customers(column_mapping_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """获取可用的客户列表（包含银行信息）"""
    try:
        customers = []
        for customer_name in column_mapping_df.iloc[:, 0].dropna().unique():
            customer_str = str(customer_name).strip()
            if customer_str and customer_str.lower() != "nan":
                banks = get_customer_banks(column_mapping_df, customer_str)
                customers.append({"name": customer_str, "banks": banks})

        logger.info(f"[客户列表] 获取到 {len(customers)} 个客户")
        return customers

    except Exception as e:
        logger.error(f"[客户列表] 获取客户列表失败: {e}")
        return []


def build_subject_mapping(
    subject_mapping_df: pd.DataFrame, customer_name: str
) -> Dict[str, Dict[str, str]]:
    """构建会计科目映射"""
    mapping = {}

    # 按匹配方式分组
    for _, row in subject_mapping_df.iterrows():
        if row.get("客户名称") != customer_name:
            continue

        match_type = str(row.get("匹配方式", "")).strip()
        counterparty_name = str(row.get("对方账户名称", "")).strip()
        keywords = str(row.get("关键字", "")).strip()
        subject_code = str(row.get("会计科目编码", "")).strip()

        if not subject_code:
            continue

        key = counterparty_name if match_type == "对方账户名称" else keywords

        if key and key not in mapping:
            mapping[key] = {"subject_code": subject_code, "match_type": match_type}

    return mapping


def _coerce_amount(value: object) -> Optional[float]:
    """转换金额格式"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if abs(amount) < 1e-9:
        return None
    return round(amount, 2)


def _extract_summary_from_columns(
    row: pd.Series, summary_col_spec: str, df: pd.DataFrame
) -> str:
    """
    从列规范中提取摘要，支持一对多字段映射

    支持格式:
    - "摘要" - 单列映射
    - "摘要/备注/说明" - 多列映射，以/分隔，按顺序检查，第一个非空值即为结果

    Args:
        row: DataFrame行数据
        summary_col_spec: 摘要列规范字符串（可能包含/分隔的多个列名）
        df: 完整的DataFrame，用于检查列是否存在

    Returns:
        提取到的摘要字符串，如果所有列都为空则返回空字符串
    """
    if not summary_col_spec:
        return ""

    # 解析多列规范
    column_names = [col.strip() for col in summary_col_spec.split("/")]

    # 按顺序检查每个列，返回第一个非空值
    for col_name in column_names:
        if col_name not in df.columns:
            logger.debug(f"[摘要提取] 列'{col_name}'不存在于数据中，跳过")
            continue

        try:
            value = row[col_name]
            # 检查是否为空（None, NaN, 空字符串）
            if value is None or (isinstance(value, float) and pd.isna(value)):
                logger.debug(f"[摘要提取] 列'{col_name}'为空，尝试下一个列")
                continue

            # 转为字符串并去除空格
            summary = str(value).strip()
            if summary and summary != "nan":
                logger.debug(f"[摘要提取] 从列'{col_name}'获取摘要: '{summary}'")
                return summary
            else:
                logger.debug(f"[摘要提取] 列'{col_name}'为空字符串，尝试下一个列")
                continue

        except Exception as e:
            logger.debug(f"[摘要提取] 从列'{col_name}'读取时出错: {e}")
            continue

    logger.debug("[摘要提取] 所有列都为空，返回空摘要")
    return ""


def _iter_rows_with_progress(
    df: pd.DataFrame, description: str, cancel_check: Optional[callable] = None
):
    """带进度条的行迭代器，支持取消检查"""
    iterator = df.iterrows()
    if tqdm is None:
        for item in iterator:
            # 检查是否取消
            if cancel_check and cancel_check():
                logger.info(f"迭代已取消: {description}")
                break
            yield item
        return

    with tqdm(total=len(df), desc=description, unit="行") as progress:
        for item in iterator:
            # 检查是否取消
            if cancel_check and cancel_check():
                logger.info(f"迭代已取消: {description}")
                break
            progress.update(1)
            yield item


def map_subject_by_counterparty_or_summary(
    counterparty: str, summary: str, subject_mapping: Dict[str, Dict[str, str]]
) -> Optional[str]:
    """根据对方户名或摘要映射会计科目"""
    counterparty = str(counterparty).strip()
    summary = str(summary).strip()

    # 方式一：通过对方户名映射
    if counterparty in subject_mapping:
        mapping_info = subject_mapping[counterparty]
        if mapping_info["match_type"] == "对方账户名称":
            return mapping_info["subject_code"]

    # 方式二：通过摘要关键字映射
    for key, mapping_info in subject_mapping.items():
        if mapping_info["match_type"] == "摘要关键字":
            if key and key in summary:
                return mapping_info["subject_code"]

    return None


def standardize_bank_statement_data(
    df: pd.DataFrame, column_mapping: Dict[str, str]
) -> pd.DataFrame:
    """
    标准化银行流水数据到统一格式

    Args:
        df: 原始银行流水数据
        column_mapping: 列名映射配置

    Returns:
        标准化后的DataFrame，包含标准列：日期、摘要、对方户名、银行账号、借方、贷方

    Raises:
        ValueError: 当发现错误时立即终止
    """
    standardized_df = df.copy().reset_index(drop=True)

    # 获取映射的列名（包含新增字段）
    date_col = column_mapping.get("date")
    summary_col = column_mapping.get("summary")
    debit_col = column_mapping.get("debit")
    credit_col = column_mapping.get("credit")
    amount_col = column_mapping.get("amount")  # 新增：单列金额格式
    counterparty_col = column_mapping.get("counterparty")
    bank_account_col = column_mapping.get("bank_account")
    payer_account_col = column_mapping.get("payer_account")  # 新增：付款人账号
    payer_name_col = column_mapping.get("payer_name")  # 新增：付款人名称
    payee_account_col = column_mapping.get("payee_account")  # 新增：收款人账号
    payee_name_col = column_mapping.get("payee_name")  # 新增：收款人名称

    logger.info("[数据标准化] 列名映射配置:")
    logger.info(f"[数据标准化]   - 日期列: '{date_col}'")
    logger.info(f"[数据标准化]   - 摘要列: '{summary_col}'")
    logger.info(f"[数据标准化]   - 借方列: '{debit_col}'")
    logger.info(f"[数据标准化]   - 贷方列: '{credit_col}'")
    logger.info(f"[数据标准化]   - 金额列: '{amount_col}' (单列格式)")
    logger.info(f"[数据标准化]   - 对方户名列: '{counterparty_col}'")
    logger.info(f"[数据标准化]   - 银行账号列: '{bank_account_col}'")
    logger.info(f"[数据标准化]   - 付款人账号列: '{payer_account_col}'")
    logger.info(f"[数据标准化]   - 付款人名称列: '{payer_name_col}'")
    logger.info(f"[数据标准化]   - 收款人账号列: '{payee_account_col}'")
    logger.info(f"[数据标准化]   - 收款人名称列: '{payee_name_col}'")

    # 获取原始列名（可能包含付款人/收款人信息）
    original_columns = df.columns.tolist()
    logger.info(f"[数据标准化] 原始数据列名: {original_columns}")

    # 1. 检查核心必需的列是否存在（支持多列映射）
    core_required_mappings = ["date", "summary"]
    core_missing_mappings = []
    for mapping_key in core_required_mappings:
        mapped_col = column_mapping.get(mapping_key)
        if not mapped_col:
            core_missing_mappings.append(f"{mapping_key} -> '{mapped_col}'")
            continue

        # 对于摘要列，支持多列映射（以/分隔）
        if mapping_key == "summary" and "/" in mapped_col:
            # 解析多列映射，检查是否至少有一个列存在
            summary_cols = [col.strip() for col in mapped_col.split("/")]
            has_any_column = any(col in original_columns for col in summary_cols)
            if not has_any_column:
                core_missing_mappings.append(
                    f"{mapping_key} -> '{mapped_col}' (none of the columns exist)"
                )
        else:
            # 对于其他列，直接检查
            if mapped_col not in original_columns:
                core_missing_mappings.append(f"{mapping_key} -> '{mapped_col}'")

    if core_missing_mappings:
        error_msg = f"缺少核心必需的列映射配置 - {', '.join(core_missing_mappings)}"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 可用列名: {original_columns}")
        raise ValueError(error_msg)

    # 2. 检查金额列配置（确保至少有一个金额列可用）
    amount_mapping_keys = ["debit", "credit", "amount"]
    available_amount_mappings = []
    for mapping_key in amount_mapping_keys:
        mapped_col = column_mapping.get(mapping_key)
        if mapped_col and mapped_col in original_columns:
            available_amount_mappings.append(f"{mapping_key} -> '{mapped_col}'")

    if not available_amount_mappings:
        error_msg = "缺少金额列映射配置，需要配置借方列、贷方列或金额列中的至少一个"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 可用列名: {original_columns}")
        raise ValueError(error_msg)

    logger.info(
        f"[数据标准化] 核心配置验证通过，可用金额列: {', '.join(available_amount_mappings)}"
    )

    # 3. 检查可选的增强字段（记录但不报错）
    optional_mappings = [
        "counterparty",
        "bank_account",
        "payer_account",
        "payer_name",
        "payee_account",
        "payee_name",
    ]
    available_optional_mappings = []
    for mapping_key in optional_mappings:
        mapped_col = column_mapping.get(mapping_key)
        if mapped_col and mapped_col in original_columns:
            available_optional_mappings.append(f"{mapping_key} -> '{mapped_col}'")

    if available_optional_mappings:
        logger.info(
            f"[数据标准化] 检测到可选增强字段: {', '.join(available_optional_mappings)}"
        )
    else:
        logger.info("[数据标准化] 未配置可选增强字段，将使用基础处理模式")

    logger.info("[数据标准化] 检查通过，开始数据处理...")

    # 日期列=源数据
    standardized_df["日期"] = standardized_df[date_col]
    # 摘要列=源数据（支持一对多字段映射）
    logger.info(f"[数据标准化] 摘要字段配置: '{summary_col}'")
    # 使用新的摘要提取函数，支持一对多字段映射（以/分隔多个列名）
    standardized_df["摘要"] = standardized_df.apply(
        lambda row: _extract_summary_from_columns(row, summary_col, standardized_df),
        axis=1,
    )

    # 初始化标准化列

    standardized_df["对方户名"] = ""
    standardized_df["银行账号"] = ""
    standardized_df["借方"] = 0.0
    standardized_df["贷方"] = 0.0

    # 处理金额列：基于映射配置判断格式
    has_dual_amount_cols = False
    has_single_amount_col = False

    # 检查双列金额格式（借方/贷方列）
    if (
        debit_col
        and credit_col
        and debit_col in standardized_df.columns
        and credit_col in standardized_df.columns
    ):
        has_dual_amount_cols = True
        logger.info(
            f"[数据标准化] 使用双列金额格式 - 借方列: '{debit_col}', 贷方列: '{credit_col}'"
        )

    # 检查单列金额格式（金额列）
    elif amount_col and amount_col in standardized_df.columns:
        has_single_amount_col = True
        logger.info(
            f"[数据标准化] 使用单列金额格式 - 金额列: '{amount_col}' (正数=借方, 负数=贷方)"
        )

    # 处理金额标准化
    if has_dual_amount_cols:
        # 双列格式：直接使用借方、贷方列
        standardized_df["借方"] = (
            standardized_df[debit_col].apply(_coerce_amount).fillna(0.0)
        )
        standardized_df["贷方"] = (
            standardized_df[credit_col].apply(_coerce_amount).fillna(0.0)
        )
        logger.debug("[数据标准化] 已处理双列金额格式")

    elif has_single_amount_col:
        # 单列格式：正数表示借方，负数表示贷方
        amounts = standardized_df[amount_col].apply(_coerce_amount).fillna(0.0)
        standardized_df["借方"] = amounts.apply(lambda x: x if x > 0 else 0.0)
        standardized_df["贷方"] = amounts.apply(lambda x: -x if x < 0 else 0.0)
        logger.debug("[数据标准化] 已处理单列金额格式，转换为借方/贷方")

    else:
        # 如果都没有，尝试自动检测（向后兼容）
        logger.warning("[数据标准化] 映射配置中的金额列都存在，尝试自动检测...")
        # 这里可以添加向后兼容的自动检测逻辑

    # 处理对方户名和银行账号标准化（基于映射配置）
    logger.info("[数据标准化] 开始处理银行账号和对方户名...")
    logger.info(
        f"[数据标准化] 配置的列 - 对方户名: '{counterparty_col}', 银行账号: '{bank_account_col}'"
    )
    logger.info(
        f"[数据标准化] 配置的列 - 付款人名称: '{payer_name_col}', 付款人账号: '{payer_account_col}'"
    )
    logger.info(
        f"[数据标准化] 配置的列 - 收款人名称: '{payee_name_col}', 收款人账号: '{payee_account_col}'"
    )

    # 使用位置索引遍历DataFrame，避免索引标签问题
    for i in range(len(standardized_df)):
        try:
            debit_amount = standardized_df.iloc[
                i, standardized_df.columns.get_loc("借方")
            ]
            credit_amount = standardized_df.iloc[
                i, standardized_df.columns.get_loc("贷方")
            ]

            # === 银行账号处理（优先级1：直接银行账号列）===
            if bank_account_col and bank_account_col in standardized_df.columns:
                bank_account_value = str(
                    standardized_df.iloc[
                        i, standardized_df.columns.get_loc(bank_account_col)
                    ]
                ).strip()
                if bank_account_value and bank_account_value != "nan":
                    standardized_df.iloc[
                        i, standardized_df.columns.get_loc("银行账号")
                    ] = bank_account_value
                    if i < 3:  # 只记录前3行的调试信息
                        logger.info(
                            f"[数据标准化] 行{i + 1}: 从映射列'{bank_account_col}'获取银行账号: '{bank_account_value}'"
                        )

            # === 对方户名处理（优先级1：直接对方户名列）===
            current_counterparty = ""
            if counterparty_col and counterparty_col in standardized_df.columns:
                counterparty_value = str(
                    standardized_df.iloc[
                        i, standardized_df.columns.get_loc(counterparty_col)
                    ]
                ).strip()
                if counterparty_value and counterparty_value != "nan":
                    current_counterparty = counterparty_value
                    standardized_df.iloc[
                        i, standardized_df.columns.get_loc("对方户名")
                    ] = current_counterparty
                    if i < 3:
                        logger.info(
                            f"[数据标准化] 行{i + 1}: 从对方户名列'{counterparty_col}'获取: '{current_counterparty}'"
                        )

            # === 智能补充处理（当主要列为空时）===
            # 如果银行账号为空，尝试从付款人/收款人账号补充
            current_bank_account = standardized_df.iloc[
                i, standardized_df.columns.get_loc("银行账号")
            ]
            if (
                not current_bank_account
                or current_bank_account == "nan"
                or current_bank_account.strip() == ""
            ):
                if debit_amount > 0:
                    # 借方交易：钱从银行出去，从收款人账号获取银行账号
                    if (
                        payee_account_col
                        and payee_account_col in standardized_df.columns
                    ):
                        payee_account_value = str(
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc(payee_account_col)
                            ]
                        ).strip()
                        if payee_account_value and payee_account_value != "nan":
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc("银行账号")
                            ] = payee_account_value
                            if i < 3:
                                logger.info(
                                    f"[数据标准化] 行{i + 1} (借方): 从收款人账号列'{payee_account_col}'补充银行账号: '{payee_account_value}'"
                                )

                elif credit_amount > 0:
                    # 贷方交易：钱进入银行，从付款人账号获取银行账号
                    if (
                        payer_account_col
                        and payer_account_col in standardized_df.columns
                    ):
                        payer_account_value = str(
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc(payer_account_col)
                            ]
                        ).strip()
                        if payer_account_value and payer_account_value != "nan":
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc("银行账号")
                            ] = payer_account_value
                            if i < 3:
                                logger.info(
                                    f"[数据标准化] 行{i + 1} (贷方): 从付款人账号列'{payer_account_col}'补充银行账号: '{payer_account_value}'"
                                )

            # 如果对方户名为空，尝试从付款人/收款人名称补充
            if (
                not current_counterparty
                or current_counterparty == "nan"
                or current_counterparty.strip() == ""
            ):
                if debit_amount > 0:
                    # 借方交易：对方是付款人
                    if payer_name_col and payer_name_col in standardized_df.columns:
                        payer_name_value = str(
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc(payer_name_col)
                            ]
                        ).strip()
                        if payer_name_value and payer_name_value != "nan":
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc("对方户名")
                            ] = payer_name_value
                            current_counterparty = payer_name_value
                elif credit_amount > 0:
                    # 贷方交易：对方是收款人
                    if payee_name_col and payee_name_col in standardized_df.columns:
                        payee_name_value = str(
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc(payee_name_col)
                            ]
                        ).strip()
                        if payee_name_value and payee_name_value != "nan":
                            standardized_df.iloc[
                                i, standardized_df.columns.get_loc("对方户名")
                            ] = payee_name_value
                            current_counterparty = payee_name_value
                            if i < 3:
                                logger.info(
                                    f"[数据标准化] 行{i + 1} (贷方): 从收款人名称列'{payee_name_col}'补充对方户名: '{payee_name_value}'"
                                )

            # 最终日志记录（只记录前3行）
            if i < 3:
                final_bank_account = standardized_df.iloc[
                    i, standardized_df.columns.get_loc("银行账号")
                ]
                final_counterparty = standardized_df.iloc[
                    i, standardized_df.columns.get_loc("对方户名")
                ]
                logger.info(
                    f"[数据标准化] 行{i + 1} 最终结果 - 银行账号: '{final_bank_account}', 对方户名: '{final_counterparty}', 交易方向: {'借方' if debit_amount > 0 else '贷方'}"
                )

        except Exception as e:
            logger.error(f"[数据标准化] 处理第{i + 1}行时发生错误: {str(e)}")
            continue

    # 只保留标准列
    final_columns = ["日期", "摘要", "对方户名", "银行账号", "借方", "贷方"]
    standardized_df = standardized_df[final_columns]

    logger.info(f"数据标准化完成，处理了 {len(standardized_df)} 行数据")
    return standardized_df


def map_bank_account_subject(
    bank_account: str, customer_name: str, subject_mapping_df: pd.DataFrame
) -> Optional[str]:
    """
    根据银行账号映射到银行存款会计科目

    Args:
        bank_account: 银行账号
        customer_name: 客户名称
        subject_mapping_df: 会计科目映射DataFrame

    Returns:
        银行科目编码，如 1002.01
    """
    if not bank_account or pd.isna(bank_account):
        logger.debug(f"[银行账号映射] 银行账号为空或NaN，客户: {customer_name}")
        return None

    bank_account = str(bank_account).strip()
    if not bank_account:
        logger.debug(f"[银行账号映射] 银行账号为空字符串，客户: {customer_name}")
        return None

    logger.info(
        f"[银行账号映射] 开始映射银行账号: '{bank_account}'，客户: {customer_name}"
    )

    # 查找客户的银行账号映射
    customer_mappings = subject_mapping_df[
        subject_mapping_df.iloc[:, 0] == customer_name
    ]
    logger.info(
        f"[银行账号映射] 客户 {customer_name} 找到 {len(customer_mappings)} 条映射记录"
    )

    # 查找匹配方式为"银行账号"的记录
    bank_account_mappings = customer_mappings[
        customer_mappings.iloc[:, 1] == "银行账号"
    ]
    logger.info(
        f"[银行账号映射] 银行账号映射方式找到 {len(bank_account_mappings)} 条记录"
    )

    if bank_account_mappings.empty:
        logger.warning(f"[银行账号映射] 客户 {customer_name} 没有配置银行账号映射方式")
        return None

    # 输出所有可用的银行账号映射记录
    logger.info("[银行账号映射] 可用的银行账号映射记录:")
    for idx, (_, row) in enumerate(bank_account_mappings.iterrows()):
        mapped_bank_account = str(row.iloc[2]).strip()
        subject_code = str(row.iloc[5]).strip()
        logger.info(
            f"[银行账号映射]   {idx + 1}. 映射账号: '{mapped_bank_account}' -> 科目: '{subject_code}'"
        )

    # 尝试精确匹配
    for _, row in bank_account_mappings.iterrows():
        mapped_bank_account = str(row.iloc[2]).strip()  # 银行账号列
        subject_code = str(row.iloc[5]).strip()  # 会计科目编码列

        if mapped_bank_account and bank_account == mapped_bank_account and subject_code:
            logger.info(
                f"[银行账号映射] 精确匹配成功: '{bank_account}' -> '{subject_code}'"
            )
            return subject_code

    # 尝试部分匹配（包含关系）
    logger.info("[银行账号映射] 精确匹配失败，尝试部分匹配...")
    for _, row in bank_account_mappings.iterrows():
        mapped_bank_account = str(row.iloc[2]).strip()  # 银行账号列
        subject_code = str(row.iloc[5]).strip()  # 会计科目编码列

        if mapped_bank_account and subject_code:
            # 检查银行流水数据是否包含映射文件中的账号
            if mapped_bank_account in bank_account:
                logger.info(
                    f"[银行账号映射] 部分匹配成功: '{bank_account}' 包含 '{mapped_bank_account}' -> '{subject_code}'"
                )
                return subject_code
            # 检查映射文件中的账号是否包含银行流水数据中的账号
            elif bank_account in mapped_bank_account:
                logger.info(
                    f"[银行账号映射] 部分匹配成功: '{mapped_bank_account}' 包含 '{bank_account}' -> '{subject_code}'"
                )
                return subject_code

    # === 银行账号映射失败立即终止 ===
    error_msg = "银行账号映射失败，无法确定银行会计科目"
    logger.error(f"[银行账号映射] {error_msg}")
    logger.error("[银行账号映射] 映射失败详情:")
    logger.error(f"[银行账号映射]   - 输入银行账号: '{bank_account}'")
    logger.error(f"[银行账号映射]   - 客户名称: {customer_name}")
    logger.error(
        f"[银行账号映射]   - 可用映射账号: {[str(row.iloc[2]).strip() for _, row in bank_account_mappings.iterrows() if str(row.iloc[2]).strip()]}"
    )
    logger.error(
        "[银行账号映射]   - 建议检查: 1) 更新会计科目mapping文件中的银行账号配置 2) 检查银行流水数据格式"
    )

    raise ValueError(error_msg)


def _init_bank_statement_output_row() -> Dict[str, object]:
    """初始化银行流水凭证输出行"""
    row = {column: "" for column in BANK_STATEMENT_OUTPUT_COLUMNS}
    for amount_field in [
        BANK_STATEMENT_OUTPUT_SCHEMA["orig_amount"],
        BANK_STATEMENT_OUTPUT_SCHEMA["debit"],
        BANK_STATEMENT_OUTPUT_SCHEMA["credit"],
        "现金流量借方金额",
        "现金流量贷方金额",
    ]:
        row[amount_field] = 0.0
    return row


def generate_bank_statement_vouchers(
    config: BankStatementConfig,
    *,
    bank_statement_df: Optional[pd.DataFrame] = None,
    column_mapping_df: Optional[pd.DataFrame] = None,
    subject_mapping_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, int, int]:
    """生成银行流水凭证"""
    cfg = config.resolved()

    # 初始化翻译服务
    if cfg.zhipuai_api_keys:
        try:
            configure_translation_service(
                api_keys=cfg.zhipuai_api_keys,
                cache_path=cfg.translation_mapping_path,
                max_workers=cfg.translation_max_workers,
            )
            print(f"已初始化多账户翻译服务，共 {len(cfg.zhipuai_api_keys)} 个API密钥")
        except Exception as e:
            print(f"初始化多账户翻译服务失败: {e}")

    # 加载数据
    bank_statement_df = (
        bank_statement_df
        if bank_statement_df is not None
        else load_bank_statement_data(cfg)
    )
    column_mapping_df = (
        column_mapping_df
        if column_mapping_df is not None
        else load_bank_statement_column_mapping(cfg)
    )
    subject_mapping_df = (
        subject_mapping_df
        if subject_mapping_df is not None
        else load_accounting_subject_mapping(cfg)
    )

    # 获取映射关系
    column_mapping = get_column_mapping_for_customer(
        column_mapping_df, cfg.customer_name, cfg
    )
    subject_mapping = build_subject_mapping(subject_mapping_df, cfg.customer_name)

    # 过滤有效的列
    available_columns = [
        col for col in column_mapping.values() if col in bank_statement_df.columns
    ]
    if len(available_columns) < 4:  # 至少需要日期、摘要、借方、贷方中的3个
        raise ValueError(f"银行流水文件中缺少必要的列，找到的列: {available_columns}")

    # 准备数据
    processed_df = bank_statement_df.copy()

    # 提取需要的列并重命名（过滤掉None值）
    columns_to_extract = []
    for col_key in ["date", "counterparty", "summary", "debit", "credit"]:
        col_name = column_mapping[col_key]
        if col_name is not None:  # 只添加非None的列名
            columns_to_extract.append(col_name)

    processed_df = processed_df[columns_to_extract].copy()

    # 为提取的列设置正确的列名
    new_columns = []
    for col_key in ["date", "counterparty", "summary", "debit", "credit"]:
        col_name = column_mapping[col_key]
        if col_name is not None:  # 只为实际存在的列设置新列名
            new_columns.append(col_key)

    processed_df.columns = new_columns

    # 转换数据类型（使用新的日期解析）
    if "debit" in processed_df.columns:
        processed_df["debit"] = processed_df["debit"].apply(_coerce_amount)
    if "credit" in processed_df.columns:
        processed_df["credit"] = processed_df["credit"].apply(_coerce_amount)
    if "summary" in processed_df.columns:
        processed_df["summary"] = processed_df["summary"].astype(str).str.strip()
    if "counterparty" in processed_df.columns:
        processed_df["counterparty"] = (
            processed_df["counterparty"].astype(str).str.strip()
        )

    # 过滤日期为空的行
    if "date" in processed_df.columns:
        valid_df = processed_df.dropna(subset=["date"])
    else:
        valid_df = processed_df  # 如果没有日期列，不过滤

    # 根据借方/贷方金额过滤有效记录
    amount_conditions = []
    if "debit" in valid_df.columns:
        amount_conditions.append(valid_df["debit"].notna() & (valid_df["debit"] > 0))
    if "credit" in valid_df.columns:
        amount_conditions.append(valid_df["credit"].notna() & (valid_df["credit"] > 0))

    if amount_conditions:  # 如果有金额列
        combined_condition = amount_conditions[0]
        for condition in amount_conditions[1:]:
            combined_condition = combined_condition | condition
        valid_df = valid_df[combined_condition]

    if valid_df.empty:
        raise ValueError("没有找到有效的银行流水记录")

    # 收集需要翻译的摘要（如果summary列存在）
    unique_summaries = set()
    if "summary" in valid_df.columns:
        unique_summaries = set(valid_df["summary"].tolist())

    # 批量翻译摘要
    translation_cache = {}
    if unique_summaries:
        # 检查是否取消
        if cfg.cancel_check and cfg.cancel_check():
            logger.info("银行流水处理已取消，跳过后续翻译")
            return pd.DataFrame(), 0, 0

        # 根据配置决定是否执行翻译
        translated_texts = {}
        if cfg.enable_translation:
            translated_texts = batch_translate_texts(
                list(unique_summaries),
                max_workers=cfg.translation_max_workers,
                requests_per_second=cfg.translation_requests_per_second,
                progress_description="翻译银行流水摘要",
                mapping_path=cfg.translation_mapping_path,
                progress_callback=cfg.progress_callback,
                cancel_check=cfg.cancel_check,
            )
            translation_cache.update(translated_texts)
        else:
            logger.info("翻译功能已禁用，跳过翻译步骤")
            # 保持原文不变
            translated_texts = {summary: summary for summary in unique_summaries}

    # 生成凭证
    voucher_rows = []
    voucher_seq = cfg.voucher_start_sequence
    processed_records = 0

    for i, row in _iter_rows_with_progress(
        valid_df, "生成银行流水凭证", cfg.cancel_check
    ):
        date = row["日期"]
        # 安全获取各列数据，处理缺失列的情况
        counterparty = row.get("对方户名", "")
        summary = row.get("摘要", "")
        debit_amount = row.get("借方")
        credit_amount = row.get("贷方")

        # 跳过空记录
        if pd.isna(debit_amount) and pd.isna(credit_amount):
            continue

        processed_records += 1
        voucher_seq += 1

        # 翻译摘要
        english_summary = translation_cache.get(summary, "")
        bilingual_summary = (
            f"{summary}/{english_summary}" if english_summary else summary
        )

        # 获取银行账号（用于银行科目映射）
        bank_account = row.get("银行账号", "")

        # 映射业务对方科目（通过摘要关键字或对方户名）
        business_subject_code = map_subject_by_counterparty_or_summary(
            counterparty, summary, subject_mapping
        )
        if not business_subject_code:
            # 如果没有映射到科目，留空等待人工检查
            logger.warning(
                f"[科目映射] 未找到匹配科目，留空处理 - 客户: {cfg.customer_name}, 对方户名: {counterparty}, 摘要: {summary}"
            )
            business_subject_code = None

        # 银行科目映射必须成功 ===
        try:
            bank_subject_code = map_bank_account_subject(
                bank_account, cfg.customer_name, subject_mapping_df
            )
        except ValueError as e:
            # 银行科目映射失败，立即终止
            error_msg = f"银行科目映射失败 - {str(e)}"
            logger.error(f"[凭证生成] {error_msg}")
            logger.error(f"[凭证生成] 失败的银行账号: '{bank_account}'")
            raise ValueError(error_msg)

        # 检查日期有效性
        if pd.isna(date):
            logger.warning(f"[凭证生成] 跳过无效日期的记录，行索引: {i}")
            continue  # 跳过无效日期的记录

        # 格式化日期
        formatted_date = date.strftime("%Y-%m-%d")
        voucher_no = f"{voucher_seq:04d}"

        # 使用标准化后的借方/贷方列判断交易方向
        if debit_amount > 0:
            # 借方记录
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "1",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: business_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: debit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(voucher_row)

            # 对应的贷方记录（银行存款减少）
            credit_row = _init_bank_statement_output_row()
            credit_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: bank_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: debit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(credit_row)

        elif credit_amount > 0:
            # 贷方交易：钱进入银行
            # 借：银行科目  贷：业务科目
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "1",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: bank_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: credit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(voucher_row)

            # 对应的贷方记录
            debit_row = _init_bank_statement_output_row()
            debit_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: business_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: credit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(debit_row)

    # 创建输出DataFrame
    df_out = pd.DataFrame(voucher_rows, columns=BANK_STATEMENT_OUTPUT_COLUMNS)

    # 在内存中创建Excel文件，不保存到磁盘
    import io

    excel_buffer = io.BytesIO()

    # 按照要求，第1、3、4行留空，第2行列名
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        # 第一行：空行
        empty_row1 = pd.DataFrame(
            [[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)],
            columns=BANK_STATEMENT_OUTPUT_COLUMNS,
        )
        empty_row1.to_excel(writer, index=False, header=False, startrow=0)

        # 第二行：列名
        header_row = pd.DataFrame(
            [BANK_STATEMENT_OUTPUT_COLUMNS], columns=BANK_STATEMENT_OUTPUT_COLUMNS
        )
        header_row.to_excel(writer, index=False, header=False, startrow=1)

        # 第三行：空行
        empty_row3 = pd.DataFrame(
            [[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)],
            columns=BANK_STATEMENT_OUTPUT_COLUMNS,
        )
        empty_row3.to_excel(writer, index=False, header=False, startrow=2)

        # 第四行：空行
        empty_row4 = pd.DataFrame(
            [[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)],
            columns=BANK_STATEMENT_OUTPUT_COLUMNS,
        )
        empty_row4.to_excel(writer, index=False, header=False, startrow=3)

        # 第五行开始：数据
        if not df_out.empty:
            df_out.to_excel(writer, index=False, header=False, startrow=4)

    # 获取Excel文件的字节数据
    excel_bytes = excel_buffer.getvalue()
    excel_buffer.close()

    generated_vouchers = voucher_seq
    return df_out, processed_records, generated_vouchers, excel_bytes


def generate_bank_statement_vouchers_from_bytes(
    config: BankStatementConfig,
    file_bytes: bytes,
    file_name: str,
    *,
    column_mapping_df: Optional[pd.DataFrame] = None,
    subject_mapping_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, int, int, bytes]:
    """
    直接从文件字节数据生成银行流水凭证（不保存临时文件）

    Args:
        config: 银行流水处理配置
        file_bytes: 文件字节数据
        file_name: 文件名（用于判断文件类型）
        column_mapping_df: 列名映射DataFrame（可选）
        subject_mapping_df: 科目映射DataFrame（可选）

    Returns:
        Tuple[DataFrame, processed_records, generated_vouchers, excel_bytes]
    """
    cfg = config.resolved()

    # 初始化翻译服务
    if cfg.zhipuai_api_keys:
        try:
            configure_translation_service(
                api_keys=cfg.zhipuai_api_keys,
                cache_path=cfg.translation_mapping_path,
                max_workers=cfg.translation_max_workers,
            )
            print(f"已初始化多账户翻译服务，共 {len(cfg.zhipuai_api_keys)} 个API密钥")
        except Exception as e:
            print(f"初始化多账户翻译服务失败: {e}")

    # 加载必要的配置文件（统一加载，传递完整参数包括bank_name）
    column_mapping_df = load_bank_statement_column_mapping(cfg)
    column_mapping = get_column_mapping_for_customer(
        column_mapping_df, cfg.customer_name, cfg
    )

    logger.info(f"[数据加载] 开始加载银行流水数据，文件名: {file_name}")
    bank_statement_df = load_bank_statement_data_from_bytes(
        file_bytes, file_name, cfg, column_mapping
    )
    logger.info(
        f"[数据加载] 加载完成 - 列数: {len(bank_statement_df.columns)}, 行数: {len(bank_statement_df)}"
    )

    subject_mapping_df = (
        subject_mapping_df
        if subject_mapping_df is not None
        else load_accounting_subject_mapping(cfg)
    )

    subject_mapping = build_subject_mapping(subject_mapping_df, cfg.customer_name)

    # 过滤有效的列
    available_columns = [
        col for col in column_mapping.values() if col in bank_statement_df.columns
    ]
    if len(available_columns) < 3:  # 至少需要日期、摘要、金额列中的2个
        raise ValueError(f"银行流水文件中缺少必要的列，找到的列: {available_columns}")

    # 数据标准化：处理不同银行格式，统一为标准格式
    logger.info("开始数据标准化...")
    standardized_df = standardize_bank_statement_data(bank_statement_df, column_mapping)
    logger.info(f"数据标准化完成，标准化后数据形状: {standardized_df.shape}")

    # ===银行账号数据验证 ===
    if "银行账号" not in standardized_df.columns:
        error_msg = "标准化后的数据中缺少'银行账号'列"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 可用列: {list(standardized_df.columns)}")
        raise ValueError(error_msg)

    # 检查银行账号数据是否为空
    non_empty_accounts = standardized_df["银行账号"].dropna()
    non_empty_accounts = non_empty_accounts[
        non_empty_accounts.astype(str).str.strip() != ""
    ]

    if len(non_empty_accounts) == 0:
        error_msg = "所有银行账号数据都为空，无法进行银行科目映射"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(
            f"[数据标准化] 银行账号列数据示例: {standardized_df['银行账号'].head(5).tolist()}"
        )
        raise ValueError(error_msg)

    # 预览银行账号数据格式（用于调试映射问题）
    unique_bank_accounts = non_empty_accounts.unique()[:3]  # 显示前3个不重复的银行账号
    logger.info(f"[数据预览] 银行账号示例: {list(unique_bank_accounts)}")

    logger.info(
        f"[数据标准化]检查通过，银行账号数据有效，记录数: {len(non_empty_accounts)}"
    )

    # 使用标准化后的数据，跳过原有的列提取和重命名步骤
    processed_df = standardized_df.copy()

    # 日期已经在数据加载时通过parse_dates标准化，无需重复处理
    if "debit" in processed_df.columns:
        processed_df["debit"] = processed_df["debit"].apply(_coerce_amount)
    if "credit" in processed_df.columns:
        processed_df["credit"] = processed_df["credit"].apply(_coerce_amount)
    if "summary" in processed_df.columns:
        processed_df["summary"] = processed_df["summary"].astype(str).str.strip()
    if "counterparty" in processed_df.columns:
        processed_df["counterparty"] = (
            processed_df["counterparty"].astype(str).str.strip()
        )
    if "银行账号" in processed_df.columns:
        processed_df["银行账号"] = processed_df["银行账号"].astype(str).str.strip()

    # 过滤无效数据
    if "date" in processed_df.columns:
        valid_df = processed_df.dropna(subset=["date"])
    else:
        valid_df = processed_df  # 如果没有日期列，不过滤

    # 根据借方/贷方金额过滤有效记录
    amount_conditions = []
    if "debit" in valid_df.columns:
        amount_conditions.append(valid_df["debit"].notna() & (valid_df["debit"] > 0))
    if "credit" in valid_df.columns:
        amount_conditions.append(valid_df["credit"].notna() & (valid_df["credit"] > 0))

    if amount_conditions:  # 如果有金额列
        combined_condition = amount_conditions[0]
        for condition in amount_conditions[1:]:
            combined_condition = combined_condition | condition
        valid_df = valid_df[combined_condition]

    if valid_df.empty:
        raise ValueError("没有找到有效的银行流水记录")

    # 收集需要翻译的摘要（如果summary列存在）
    unique_summaries = set()
    if "summary" in valid_df.columns:
        unique_summaries = set(valid_df["summary"].tolist())

    # 批量翻译摘要
    translation_cache = {}
    if unique_summaries:
        # 检查是否取消
        if cfg.cancel_check and cfg.cancel_check():
            logger.info("银行流水处理已取消，跳过后续翻译")
            return pd.DataFrame(), 0, 0

        # 根据配置决定是否执行翻译
        translated_texts = {}
        if cfg.enable_translation:
            translated_texts = batch_translate_texts(
                list(unique_summaries),
                max_workers=cfg.translation_max_workers,
                requests_per_second=cfg.translation_requests_per_second,
                progress_description="翻译银行流水摘要",
                mapping_path=cfg.translation_mapping_path,
                progress_callback=cfg.progress_callback,
                cancel_check=cfg.cancel_check,
            )
            translation_cache.update(translated_texts)
        else:
            logger.info("翻译功能已禁用，跳过翻译步骤")
            # 保持原文不变
            translated_texts = {summary: summary for summary in unique_summaries}

    # 生成凭证
    voucher_rows = []
    voucher_seq = cfg.voucher_start_sequence
    processed_records = 0

    for i, row in _iter_rows_with_progress(
        valid_df, "生成银行流水凭证", cfg.cancel_check
    ):
        date = row["日期"]
        # 安全获取各列数据，处理缺失列的情况
        counterparty = row.get("对方户名", "")
        summary = row.get("摘要", "")
        debit_amount = row.get("借方")
        credit_amount = row.get("贷方")

        # 跳过空记录
        if pd.isna(debit_amount) and pd.isna(credit_amount):
            continue

        processed_records += 1
        voucher_seq += 1

        # 翻译摘要
        english_summary = translation_cache.get(summary, "")
        bilingual_summary = (
            f"{summary}/{english_summary}" if english_summary else summary
        )

        # 获取银行账号（用于银行科目映射）
        bank_account = row.get("银行账号", "")

        # 映射业务对方科目（通过摘要关键字或对方户名）
        business_subject_code = map_subject_by_counterparty_or_summary(
            counterparty, summary, subject_mapping
        )
        if not business_subject_code:
            # 如果没有映射到科目，留空等待人工检查
            logger.warning(
                f"[科目映射] 未找到匹配科目，留空处理 - 客户: {cfg.customer_name}, 对方户名: {counterparty}, 摘要: {summary}"
            )
            business_subject_code = None

        # ===银行科目映射必须成功 ===
        try:
            bank_subject_code = map_bank_account_subject(
                bank_account, cfg.customer_name, subject_mapping_df
            )
        except ValueError as e:
            # 银行科目映射失败，立即终止
            error_msg = f"银行科目映射失败 - {str(e)}"
            logger.error(f"[凭证生成] {error_msg}")
            logger.error(f"[凭证生成] 失败的银行账号: '{bank_account}'")
            raise ValueError(error_msg)

        # 检查日期有效性
        if pd.isna(date):
            logger.warning(f"[凭证生成] 跳过无效日期的记录，行索引: {i}")
            continue  # 跳过无效日期的记录

        # 格式化日期
        formatted_date = date.strftime("%Y-%m-%d")
        voucher_no = f"{voucher_seq:04d}"

        # 使用标准化后的借方/贷方列判断交易方向
        if debit_amount > 0:
            # 借方记录
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "1",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: business_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: debit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(voucher_row)

            # 对应的贷方记录（银行存款减少）
            credit_row = _init_bank_statement_output_row()
            credit_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: bank_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: debit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(credit_row)

        elif credit_amount > 0:
            # 贷方交易：钱进入银行
            # 借：银行科目  贷：业务科目
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "1",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: bank_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: credit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(voucher_row)

            # 对应的贷方记录
            debit_row = _init_bank_statement_output_row()
            debit_row.update(
                {
                    BANK_STATEMENT_OUTPUT_SCHEMA["date"]: formatted_date,
                    BANK_STATEMENT_OUTPUT_SCHEMA["voucher_no"]: voucher_no,
                    BANK_STATEMENT_OUTPUT_SCHEMA["attachment"]: "",
                    BANK_STATEMENT_OUTPUT_SCHEMA["summary"]: bilingual_summary,
                    BANK_STATEMENT_OUTPUT_SCHEMA["subject_code"]: business_subject_code,
                    BANK_STATEMENT_OUTPUT_SCHEMA["currency"]: "CNY",
                    BANK_STATEMENT_OUTPUT_SCHEMA["debit"]: 0.0,
                    BANK_STATEMENT_OUTPUT_SCHEMA["credit"]: credit_amount,
                    BANK_STATEMENT_OUTPUT_SCHEMA["preparer"]: cfg.preparer,
                    BANK_STATEMENT_OUTPUT_SCHEMA["status"]: "未审核",
                }
            )
            voucher_rows.append(debit_row)

    # 创建输出DataFrame
    df_out = pd.DataFrame(voucher_rows, columns=BANK_STATEMENT_OUTPUT_COLUMNS)

    # 在内存中创建Excel文件，不保存到磁盘
    import io

    excel_buffer = io.BytesIO()

    # 按照要求，第1、3、4行留空，第2行列名
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        # 第一行：空行
        empty_row1 = pd.DataFrame(
            [[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)],
            columns=BANK_STATEMENT_OUTPUT_COLUMNS,
        )
        empty_row1.to_excel(writer, index=False, header=False, startrow=0)

        # 第二行：列名
        header_row = pd.DataFrame(
            [BANK_STATEMENT_OUTPUT_COLUMNS], columns=BANK_STATEMENT_OUTPUT_COLUMNS
        )
        header_row.to_excel(writer, index=False, header=False, startrow=1)

        # 第三行：空行
        empty_row3 = pd.DataFrame(
            [[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)],
            columns=BANK_STATEMENT_OUTPUT_COLUMNS,
        )
        empty_row3.to_excel(writer, index=False, header=False, startrow=2)

        # 第四行：空行
        empty_row4 = pd.DataFrame(
            [[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)],
            columns=BANK_STATEMENT_OUTPUT_COLUMNS,
        )
        empty_row4.to_excel(writer, index=False, header=False, startrow=3)

        # 第五行开始：数据
        if not df_out.empty:
            df_out.to_excel(writer, index=False, header=False, startrow=4)

    # 获取Excel文件的字节数据
    excel_bytes = excel_buffer.getvalue()
    excel_buffer.close()

    generated_vouchers = voucher_seq
    return df_out, processed_records, generated_vouchers, excel_bytes
