from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple, Union

import logging
import pandas as pd

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

from .translation_interface import batch_translate_texts, configure_translation_service

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

BANK_STATEMENT_OUTPUT_COLUMNS = list(BANK_STATEMENT_OUTPUT_SCHEMA.values()) + BANK_STATEMENT_ADDITIONAL_COLUMNS

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
    column_mapping_file: str = DEFAULT_BANK_STATEMENT_MAPPING_FILE
    subject_mapping_file: str = DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE
    output_dir: Path = field(default_factory=lambda: Path("data") / "output" / "银行流水转凭证")

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
    translation_mapping_path: Path = field(default_factory=lambda: Path("data") / "translation_mapping.csv")
    translation_max_workers: int = 12
    translation_requests_per_second: float =15
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


def load_bank_statement_data(config: BankStatementConfig, *, usecols: Optional[Iterable[str]] = None) -> pd.DataFrame:
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


def load_bank_statement_data_from_bytes(file_bytes: bytes, file_name: str, config: BankStatementConfig, *, usecols: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """从字节数据直接加载银行流水数据"""
    import io

    # 根据文件扩展名选择处理方式
    file_extension = Path(file_name).suffix.lower()

    if file_extension in ['.xlsx', '.xls']:
        # 使用BytesIO在内存中处理Excel文件
        excel_file = io.BytesIO(file_bytes)
        excel = pd.ExcelFile(excel_file, engine="openpyxl")

        if config.bank_statement_sheet is not None:
            sheet_name = config.bank_statement_sheet
        else:
            if not excel.sheet_names:
                raise ValueError("Excel文件中没有找到工作表")
            sheet_name = excel.sheet_names[0]

        df = excel.parse(sheet_name=sheet_name, header=0, usecols=usecols)
    elif file_extension == '.csv':
        # 处理CSV文件
        import io
        csv_file = io.StringIO(file_bytes.decode('utf-8'))
        df = pd.read_csv(csv_file, usecols=usecols)
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


def get_column_mapping_for_customer(column_mapping_df: pd.DataFrame, customer_name: str, config: BankStatementConfig) -> Dict[str, str]:
    """获取指定客户的列名映射"""
    # 查找客户对应的映射
    customer_row = column_mapping_df[column_mapping_df.iloc[:, 0] == customer_name]

    if customer_row.empty:
        # 如果没找到，使用默认映射
        return {
            "date": config.default_date_column,
            "counterparty": config.default_counterparty_column,
            "summary": config.default_summary_column,
            "debit": config.default_debit_column,
            "credit": config.default_credit_column,
        }

    # 使用找到的映射
    mapping = customer_row.iloc[0].to_dict()
    # 处理NaN值，避免JSON序列化错误
    for key, value in mapping.items():
        if pd.isna(value):
            mapping[key] = None

    return {
        "date": mapping.get("日期", config.default_date_column),
        "counterparty": mapping.get("对方户名", config.default_counterparty_column),
        "summary": mapping.get("摘要", config.default_summary_column),
        "debit": mapping.get("借方", config.default_debit_column),
        "credit": mapping.get("贷方", config.default_credit_column),
        "bank_account": mapping.get("银行账号", ""),
    }


def build_subject_mapping(subject_mapping_df: pd.DataFrame, customer_name: str) -> Dict[str, Dict[str, str]]:
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
            mapping[key] = {
                "subject_code": subject_code,
                "match_type": match_type
            }

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


def _iter_rows_with_progress(df: pd.DataFrame, description: str, cancel_check: Optional[callable] = None):
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


def map_subject_by_counterparty_or_summary(counterparty: str, summary: str, subject_mapping: Dict[str, Dict[str, str]]) -> Optional[str]:
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
    df: pd.DataFrame,
    column_mapping: Dict[str, str]
) -> pd.DataFrame:
    """
    标准化银行流水数据到统一格式

    Args:
        df: 原始银行流水数据
        column_mapping: 列名映射配置

    Returns:
        标准化后的DataFrame，包含标准列：日期、摘要、对方户名、银行账号、借方、贷方

    Raises:
        ValueError: 当发现面向错误时立即终止
    """
    standardized_df = df.copy().reset_index(drop=True)

    # 获取映射的列名
    date_col = column_mapping.get("date")
    summary_col = column_mapping.get("summary")
    debit_col = column_mapping.get("debit")
    credit_col = column_mapping.get("credit")
    counterparty_col = column_mapping.get("counterparty")
    bank_account_col = column_mapping.get("bank_account")

    logger.info("[数据标准化] 列名映射配置:")
    logger.info(f"[数据标准化]   - 日期列: '{date_col}'")
    logger.info(f"[数据标准化]   - 摘要列: '{summary_col}'")
    logger.info(f"[数据标准化]   - 借方列: '{debit_col}'")
    logger.info(f"[数据标准化]   - 贷方列: '{credit_col}'")
    logger.info(f"[数据标准化]   - 对方户名列: '{counterparty_col}'")
    logger.info(f"[数据标准化]   - 银行账号列: '{bank_account_col}'")

    # 获取原始列名（可能包含付款人/收款人信息）
    original_columns = df.columns.tolist()
    logger.info(f"[数据标准化] 原始数据列名: {original_columns}")

    # === 面向错误检查：立即终止程序 ===

    # 1. 检查必需的列是否存在
    required_mappings = ["date", "summary"]
    missing_mappings = []
    for mapping_key in required_mappings:
        mapped_col = column_mapping.get(mapping_key)
        if not mapped_col or mapped_col not in original_columns:
            missing_mappings.append(f"{mapping_key} -> '{mapped_col}'")

    if missing_mappings:
        error_msg = f"面向错误：缺少必需的列映射配置 - {', '.join(missing_mappings)}"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 可用列名: {original_columns}")
        raise ValueError(error_msg)

    # 2. 检查金额列配置（必须至少有一个金额列）
    if not debit_col and not credit_col:
        error_msg = "面向错误：未配置借方列或贷方列，无法处理金额数据"
        logger.error(f"[数据标准化] {error_msg}")
        raise ValueError(error_msg)

    # 3. 检查金额列是否真实存在
    amount_columns = []
    if debit_col and debit_col in original_columns:
        amount_columns.append(debit_col)
    if credit_col and credit_col in original_columns:
        amount_columns.append(credit_col)

    if not amount_columns:
        error_msg = f"面向错误：配置的金额列在数据中不存在 - 借方列: '{debit_col}', 贷方列: '{credit_col}'"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 可用列名: {original_columns}")
        raise ValueError(error_msg)

    logger.info("[数据标准化] 面向错误检查通过，开始数据处理...")

    # 查找付款人/收款人相关列
    payer_name_col = None
    payee_name_col = None
    payer_account_col = None
    payee_account_col = None

    for col in original_columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ["付款人", "付款方", "payer"]):
            if "账号" in col_lower or "account" in col_lower:
                payer_account_col = col
            else:
                payer_name_col = col
        elif any(keyword in col_lower for keyword in ["收款人", "收款方", "payee"]):
            if "账号" in col_lower or "account" in col_lower:
                payee_account_col = col
            else:
                payee_name_col = col

    # 初始化标准列
    standardized_df["日期"] = pd.to_datetime(standardized_df[date_col], errors="coerce") if date_col and date_col in standardized_df.columns else pd.NaT
    standardized_df["摘要"] = standardized_df[summary_col].astype(str).str.strip() if summary_col and summary_col in standardized_df.columns else ""
    standardized_df["对方户名"] = ""
    standardized_df["银行账号"] = ""
    standardized_df["借方"] = 0.0
    standardized_df["贷方"] = 0.0

    # 处理金额列：判断是单列格式还是双列格式
    has_single_amount_col = False
    has_dual_amount_cols = False

    # 检查是否有单列金额格式
    for col in original_columns:
        if col not in [date_col, summary_col, counterparty_col, debit_col, credit_col]:
            # 尝试判断这是否是金额列
            if any(keyword in str(col).lower() for keyword in ["金额", "amount", "数值", "value"]):
                has_single_amount_col = True
                amount_col = col
                break

    # 检查是否有双列金额格式
    if debit_col and credit_col and debit_col in standardized_df.columns and credit_col in standardized_df.columns:
        has_dual_amount_cols = True

    logger.info(f"检测金额格式: 单列={has_single_amount_col}, 双列={has_dual_amount_cols}")

    # 处理金额标准化
    if has_dual_amount_cols:
        # 双列格式：直接使用借方、贷方列
        standardized_df["借方"] = standardized_df[debit_col].apply(_coerce_amount).fillna(0.0)
        standardized_df["贷方"] = standardized_df[credit_col].apply(_coerce_amount).fillna(0.0)

    elif has_single_amount_col:
        # 单列格式：正数表示借方，负数表示贷方
        if amount_col in standardized_df.columns:
            amounts = standardized_df[amount_col].apply(_coerce_amount).fillna(0.0)
            standardized_df["借方"] = amounts.apply(lambda x: x if x > 0 else 0.0)
            standardized_df["贷方"] = amounts.apply(lambda x: -x if x < 0 else 0.0)

    # 处理对方户名和银行账号标准化
    logger.info("[数据标准化] 开始处理银行账号和对方户名...")
    logger.info(f"[数据标准化] 查找到的列: payer_name={payer_name_col}, payee_name={payee_name_col}, payer_account={payer_account_col}, payee_account={payee_account_col}")

    # 使用位置索引遍历DataFrame，避免索引标签问题
    for i in range(len(standardized_df)):
        try:
            debit_amount = standardized_df.iloc[i, standardized_df.columns.get_loc("借方")]
            credit_amount = standardized_df.iloc[i, standardized_df.columns.get_loc("贷方")]

            # 首先尝试使用直接的银行账号列映射
            if bank_account_col and bank_account_col in standardized_df.columns:
                bank_account_col_idx = standardized_df.columns.get_loc(bank_account_col)
                original_value = str(standardized_df.iloc[i, bank_account_col_idx]).strip()
                standardized_df.iloc[i, standardized_df.columns.get_loc("银行账号")] = original_value
                if i < 3:  # 只记录前3行的调试信息
                    logger.info(f"[数据标准化] 行{i+1}: 从映射列'{bank_account_col}'获取银行账号: '{original_value}'")
            else:
                if i < 3:  # 只记录前3行的调试信息
                    logger.info(f"[数据标准化] 行{i+1}: 没有银行账号映射列或列不存在")

            # 如果没有直接的银行账号列，根据交易方向智能提取
            current_bank_account = standardized_df.iloc[i, standardized_df.columns.get_loc("银行账号")]
            if not current_bank_account or current_bank_account == "nan":
                if debit_amount > 0:
                    # 借方交易：钱从银行出去
                    # 对方户名取付款人名称
                    if payer_name_col and payer_name_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(payer_name_col)]).strip()
                    elif counterparty_col and counterparty_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(counterparty_col)]).strip()

                    # 银行账号取付款人账号
                    if payer_account_col and payer_account_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("银行账号")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(payer_account_col)]).strip()
                    elif counterparty_col and counterparty_col in standardized_df.columns:
                        # 如果没有专门的账号列，尝试从对方户名列中提取账号
                        standardized_df.iloc[i, standardized_df.columns.get_loc("银行账号")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(counterparty_col)]).strip()

                elif credit_amount > 0:
                    # 贷方交易：钱进入银行
                    # 对方户名取收款人名称
                    if payee_name_col and payee_name_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(payee_name_col)]).strip()
                    elif counterparty_col and counterparty_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(counterparty_col)]).strip()

                    # 银行账号取收款人账号
                    if payee_account_col and payee_account_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("银行账号")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(payee_account_col)]).strip()
                    elif counterparty_col and counterparty_col in standardized_df.columns:
                        # 如果没有专门的账号列，尝试从对方户名列中提取账号
                        standardized_df.iloc[i, standardized_df.columns.get_loc("银行账号")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(counterparty_col)]).strip()
            else:
                # 如果已有银行账号，还需要处理对方户名
                if debit_amount > 0:
                    # 借方交易：钱从银行出去
                    if payer_name_col and payer_name_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(payer_name_col)]).strip()
                    elif counterparty_col and counterparty_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(counterparty_col)]).strip()
                elif credit_amount > 0:
                    # 贷方交易：钱进入银行
                    if payee_name_col and payee_name_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(payee_name_col)]).strip()
                    elif counterparty_col and counterparty_col in standardized_df.columns:
                        standardized_df.iloc[i, standardized_df.columns.get_loc("对方户名")] = str(standardized_df.iloc[i, standardized_df.columns.get_loc(counterparty_col)]).strip()

        except Exception as e:
            logger.error(f"[数据标准化] 处理第{i+1}行时发生错误: {str(e)}")
            logger.error(f"[数据标准化] 跳过第{i+1}行，继续处理下一行")
            continue

    # 只保留标准列
    final_columns = ["日期", "摘要", "对方户名", "银行账号", "借方", "贷方"]
    standardized_df = standardized_df[final_columns]

    logger.info(f"数据标准化完成，处理了 {len(standardized_df)} 行数据")
    return standardized_df


def map_bank_account_subject(
    bank_account: str,
    customer_name: str,
    subject_mapping_df: pd.DataFrame
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

    logger.info(f"[银行账号映射] 开始映射银行账号: '{bank_account}'，客户: {customer_name}")

    # 查找客户的银行账号映射
    customer_mappings = subject_mapping_df[subject_mapping_df.iloc[:, 0] == customer_name]
    logger.info(f"[银行账号映射] 客户 {customer_name} 找到 {len(customer_mappings)} 条映射记录")

    # 查找匹配方式为"银行账号"的记录
    bank_account_mappings = customer_mappings[customer_mappings.iloc[:, 1] == "银行账号"]
    logger.info(f"[银行账号映射] 银行账号映射方式找到 {len(bank_account_mappings)} 条记录")

    if bank_account_mappings.empty:
        logger.warning(f"[银行账号映射] 客户 {customer_name} 没有配置银行账号映射方式")
        return None

    # 输出所有可用的银行账号映射记录
    logger.info("[银行账号映射] 可用的银行账号映射记录:")
    for idx, (_, row) in enumerate(bank_account_mappings.iterrows()):
        mapped_bank_account = str(row.iloc[2]).strip()
        subject_code = str(row.iloc[5]).strip()
        logger.info(f"[银行账号映射]   {idx+1}. 映射账号: '{mapped_bank_account}' -> 科目: '{subject_code}'")

    # 尝试精确匹配
    for _, row in bank_account_mappings.iterrows():
        mapped_bank_account = str(row.iloc[2]).strip()  # 银行账号列
        subject_code = str(row.iloc[5]).strip()  # 会计科目编码列

        if mapped_bank_account and bank_account == mapped_bank_account and subject_code:
            logger.info(f"[银行账号映射] 精确匹配成功: '{bank_account}' -> '{subject_code}'")
            return subject_code

    # 尝试部分匹配（包含关系）
    logger.info("[银行账号映射] 精确匹配失败，尝试部分匹配...")
    for _, row in bank_account_mappings.iterrows():
        mapped_bank_account = str(row.iloc[2]).strip()  # 银行账号列
        subject_code = str(row.iloc[5]).strip()  # 会计科目编码列

        if mapped_bank_account and subject_code:
            # 检查银行流水数据是否包含映射文件中的账号
            if mapped_bank_account in bank_account:
                logger.info(f"[银行账号映射] 部分匹配成功: '{bank_account}' 包含 '{mapped_bank_account}' -> '{subject_code}'")
                return subject_code
            # 检查映射文件中的账号是否包含银行流水数据中的账号
            elif bank_account in mapped_bank_account:
                logger.info(f"[银行账号映射] 部分匹配成功: '{mapped_bank_account}' 包含 '{bank_account}' -> '{subject_code}'")
                return subject_code

    # === 面向错误：银行账号映射失败立即终止 ===
    error_msg = "面向错误：银行账号映射失败，无法确定银行会计科目"
    logger.error(f"[银行账号映射] {error_msg}")
    logger.error("[银行账号映射] 映射失败详情:")
    logger.error(f"[银行账号映射]   - 输入银行账号: '{bank_account}'")
    logger.error(f"[银行账号映射]   - 客户名称: {customer_name}")
    logger.error(f"[银行账号映射]   - 可用映射账号: {[str(row.iloc[2]).strip() for _, row in bank_account_mappings.iterrows() if str(row.iloc[2]).strip()]}")
    logger.error("[银行账号映射]   - 建议检查: 1) 更新会计科目mapping文件中的银行账号配置 2) 检查银行流水数据格式")

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
    bank_statement_df = bank_statement_df if bank_statement_df is not None else load_bank_statement_data(cfg)
    column_mapping_df = column_mapping_df if column_mapping_df is not None else load_bank_statement_column_mapping(cfg)
    subject_mapping_df = subject_mapping_df if subject_mapping_df is not None else load_accounting_subject_mapping(cfg)

    # 获取映射关系
    column_mapping = get_column_mapping_for_customer(column_mapping_df, cfg.customer_name, cfg)
    subject_mapping = build_subject_mapping(subject_mapping_df, cfg.customer_name)

    # 过滤有效的列
    available_columns = [col for col in column_mapping.values() if col in bank_statement_df.columns]
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

    # 转换数据类型（只处理存在的列）
    if "date" in processed_df.columns:
        processed_df["date"] = pd.to_datetime(processed_df["date"], errors="coerce")
    if "debit" in processed_df.columns:
        processed_df["debit"] = processed_df["debit"].apply(_coerce_amount)
    if "credit" in processed_df.columns:
        processed_df["credit"] = processed_df["credit"].apply(_coerce_amount)
    if "summary" in processed_df.columns:
        processed_df["summary"] = processed_df["summary"].astype(str).str.strip()
    if "counterparty" in processed_df.columns:
        processed_df["counterparty"] = processed_df["counterparty"].astype(str).str.strip()

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

    for _, row in _iter_rows_with_progress(valid_df, "生成银行流水凭证", cfg.cancel_check):
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
        bilingual_summary = f"{summary}/{english_summary}" if english_summary else summary

        # 获取银行账号（用于银行科目映射）
        bank_account = row.get("银行账号", "")

        # 映射业务对方科目（通过摘要关键字或对方户名）
        business_subject_code = map_subject_by_counterparty_or_summary(counterparty, summary, subject_mapping)
        if not business_subject_code:
            # 如果没有映射到科目，留空等待人工检查
            logger.warning(f"[科目映射] 未找到匹配科目，留空处理 - 客户: {cfg.customer_name}, 对方户名: {counterparty}, 摘要: {summary}")
            business_subject_code = None

        # === 面向错误：银行科目映射必须成功 ===
        try:
            bank_subject_code = map_bank_account_subject(bank_account, cfg.customer_name, subject_mapping_df)
        except ValueError as e:
            # 银行科目映射失败，立即终止
            error_msg = f"面向错误：银行科目映射失败 - {str(e)}"
            logger.error(f"[凭证生成] {error_msg}")
            logger.error(f"[凭证生成] 失败的银行账号: '{bank_account}'")
            raise ValueError(error_msg)

        # 格式化日期
        formatted_date = date.strftime("%Y-%m-%d")
        voucher_no = f"{voucher_seq:04d}"

        # 使用标准化后的借方/贷方列判断交易方向
        if debit_amount > 0:
            # 借方记录
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update({
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
            })
            voucher_rows.append(voucher_row)

            # 对应的贷方记录（银行存款减少）
            credit_row = _init_bank_statement_output_row()
            credit_row.update({
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
            })
            voucher_rows.append(credit_row)

        elif credit_amount > 0:
            # 贷方交易：钱进入银行
            # 借：银行科目  贷：业务科目
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update({
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
            })
            voucher_rows.append(voucher_row)

            # 对应的贷方记录
            debit_row = _init_bank_statement_output_row()
            debit_row.update({
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
            })
            voucher_rows.append(debit_row)

    # 创建输出DataFrame
    df_out = pd.DataFrame(voucher_rows, columns=BANK_STATEMENT_OUTPUT_COLUMNS)

    # 在内存中创建Excel文件，不保存到磁盘
    import io
    excel_buffer = io.BytesIO()

    # 按照要求，第1、3、4行留空，第2行列名
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        # 第一行：空行
        empty_row1 = pd.DataFrame([[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        empty_row1.to_excel(writer, index=False, header=False, startrow=0)

        # 第二行：列名
        header_row = pd.DataFrame([BANK_STATEMENT_OUTPUT_COLUMNS], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        header_row.to_excel(writer, index=False, header=False, startrow=1)

        # 第三行：空行
        empty_row3 = pd.DataFrame([[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        empty_row3.to_excel(writer, index=False, header=False, startrow=2)

        # 第四行：空行
        empty_row4 = pd.DataFrame([[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
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

    # 直接从字节数据加载数据，不保存临时文件
    bank_statement_df = load_bank_statement_data_from_bytes(file_bytes, file_name, cfg)
    logger.info(f"[调试] 原始银行流水数据列名: {list(bank_statement_df.columns)}")
    logger.info(f"[调试] 原始数据形状: {bank_statement_df.shape}")
    logger.info(f"[调试] 原始数据前3行示例:\n{bank_statement_df.head(3).to_string()}")

    column_mapping_df = column_mapping_df if column_mapping_df is not None else load_bank_statement_column_mapping(cfg)
    logger.info(f"[调试] 列名映射配置客户: {cfg.customer_name}")

    subject_mapping_df = subject_mapping_df if subject_mapping_df is not None else load_accounting_subject_mapping(cfg)

    # 获取映射关系
    column_mapping = get_column_mapping_for_customer(column_mapping_df, cfg.customer_name, cfg)
    subject_mapping = build_subject_mapping(subject_mapping_df, cfg.customer_name)

    # 过滤有效的列
    available_columns = [col for col in column_mapping.values() if col in bank_statement_df.columns]
    if len(available_columns) < 3:  # 至少需要日期、摘要、金额列中的2个
        raise ValueError(f"银行流水文件中缺少必要的列，找到的列: {available_columns}")

    # 数据标准化：处理不同银行格式，统一为标准格式
    logger.info("开始数据标准化...")
    standardized_df = standardize_bank_statement_data(bank_statement_df, column_mapping)
    logger.info(f"数据标准化完成，标准化后数据形状: {standardized_df.shape}")

    # === 面向错误检查：银行账号数据验证 ===
    if "银行账号" not in standardized_df.columns:
        error_msg = "面向错误：标准化后的数据中缺少'银行账号'列"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 可用列: {list(standardized_df.columns)}")
        raise ValueError(error_msg)

    # 检查银行账号数据是否为空
    non_empty_accounts = standardized_df["银行账号"].dropna()
    non_empty_accounts = non_empty_accounts[non_empty_accounts.astype(str).str.strip() != ""]

    if len(non_empty_accounts) == 0:
        error_msg = "面向错误：所有银行账号数据都为空，无法进行银行科目映射"
        logger.error(f"[数据标准化] {error_msg}")
        logger.error(f"[数据标准化] 银行账号列数据示例: {standardized_df['银行账号'].head(5).tolist()}")
        raise ValueError(error_msg)

    # 预览银行账号数据格式（用于调试映射问题）
    unique_bank_accounts = non_empty_accounts.unique()[:10]  # 显示前10个不重复的银行账号
    logger.info("[数据预览] 银行账号数据格式示例 (前10个):")
    for idx, account in enumerate(unique_bank_accounts):
        logger.info(f"[数据预览]   {idx+1}. '{str(account)}' (长度: {len(str(account))})")

    logger.info(f"[数据标准化] 面向错误检查通过，银行账号数据有效，记录数: {len(non_empty_accounts)}")

    # 使用标准化后的数据，跳过原有的列提取和重命名步骤
    processed_df = standardized_df.copy()

    # 转换数据类型（标准化后的数据已经包含标准列名）
    if "date" in processed_df.columns:
        processed_df["date"] = pd.to_datetime(processed_df["date"], errors="coerce")
    if "debit" in processed_df.columns:
        processed_df["debit"] = processed_df["debit"].apply(_coerce_amount)
    if "credit" in processed_df.columns:
        processed_df["credit"] = processed_df["credit"].apply(_coerce_amount)
    if "summary" in processed_df.columns:
        processed_df["summary"] = processed_df["summary"].astype(str).str.strip()
    if "counterparty" in processed_df.columns:
        processed_df["counterparty"] = processed_df["counterparty"].astype(str).str.strip()
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

    for _, row in _iter_rows_with_progress(valid_df, "生成银行流水凭证", cfg.cancel_check):
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
        bilingual_summary = f"{summary}/{english_summary}" if english_summary else summary

        # 获取银行账号（用于银行科目映射）
        bank_account = row.get("银行账号", "")

        # 映射业务对方科目（通过摘要关键字或对方户名）
        business_subject_code = map_subject_by_counterparty_or_summary(counterparty, summary, subject_mapping)
        if not business_subject_code:
            # 如果没有映射到科目，留空等待人工检查
            logger.warning(f"[科目映射] 未找到匹配科目，留空处理 - 客户: {cfg.customer_name}, 对方户名: {counterparty}, 摘要: {summary}")
            business_subject_code = None

        # === 面向错误：银行科目映射必须成功 ===
        try:
            bank_subject_code = map_bank_account_subject(bank_account, cfg.customer_name, subject_mapping_df)
        except ValueError as e:
            # 银行科目映射失败，立即终止
            error_msg = f"面向错误：银行科目映射失败 - {str(e)}"
            logger.error(f"[凭证生成] {error_msg}")
            logger.error(f"[凭证生成] 失败的银行账号: '{bank_account}'")
            raise ValueError(error_msg)

        # 格式化日期
        formatted_date = date.strftime("%Y-%m-%d")
        voucher_no = f"{voucher_seq:04d}"

        # 使用标准化后的借方/贷方列判断交易方向
        if debit_amount > 0:
            # 借方记录
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update({
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
            })
            voucher_rows.append(voucher_row)

            # 对应的贷方记录（银行存款减少）
            credit_row = _init_bank_statement_output_row()
            credit_row.update({
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
            })
            voucher_rows.append(credit_row)

        elif credit_amount > 0:
            # 贷方交易：钱进入银行
            # 借：银行科目  贷：业务科目
            voucher_row = _init_bank_statement_output_row()
            voucher_row.update({
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
            })
            voucher_rows.append(voucher_row)

            # 对应的贷方记录
            debit_row = _init_bank_statement_output_row()
            debit_row.update({
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
            })
            voucher_rows.append(debit_row)

    # 创建输出DataFrame
    df_out = pd.DataFrame(voucher_rows, columns=BANK_STATEMENT_OUTPUT_COLUMNS)

    # 在内存中创建Excel文件，不保存到磁盘
    import io
    excel_buffer = io.BytesIO()

    # 按照要求，第1、3、4行留空，第2行列名
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        # 第一行：空行
        empty_row1 = pd.DataFrame([[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        empty_row1.to_excel(writer, index=False, header=False, startrow=0)

        # 第二行：列名
        header_row = pd.DataFrame([BANK_STATEMENT_OUTPUT_COLUMNS], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        header_row.to_excel(writer, index=False, header=False, startrow=1)

        # 第三行：空行
        empty_row3 = pd.DataFrame([[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        empty_row3.to_excel(writer, index=False, header=False, startrow=2)

        # 第四行：空行
        empty_row4 = pd.DataFrame([[""] * len(BANK_STATEMENT_OUTPUT_COLUMNS)], columns=BANK_STATEMENT_OUTPUT_COLUMNS)
        empty_row4.to_excel(writer, index=False, header=False, startrow=3)

        # 第五行开始：数据
        if not df_out.empty:
            df_out.to_excel(writer, index=False, header=False, startrow=4)

    # 获取Excel文件的字节数据
    excel_bytes = excel_buffer.getvalue()
    excel_buffer.close()

    generated_vouchers = voucher_seq
    return df_out, processed_records, generated_vouchers, excel_bytes
