from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import xlrd
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from accounting_voucher_generation.pipeline import (
	VoucherConfig,
	generate_vouchers,
	load_employee_data,
	load_subject_mapping,
)

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Accounting Voucher Web")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
	return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
async def generate_endpoint(
	request: Request,
	expense_file: UploadFile = File(...),
	employee_file: Optional[UploadFile] = File(None),
	subject_file: Optional[UploadFile] = File(None),
	translation_file: Optional[UploadFile] = File(None),
	preparer: str = Form("cissy"),
	voucher_category: str = Form("记"),
	credit_account: str = Form("224104"),
	start_seq: int = Form(0),
	expense_period: Optional[str] = Form(None),
	expense_sheet: Optional[str] = Form(None),
) -> StreamingResponse:
	default_config = VoucherConfig().resolved()

	try:
		expense_bytes = await expense_file.read()
		if not expense_bytes:
			raise HTTPException(status_code=400, detail="费用报销表文件为空，请重新上传")

		expense_period_value, expense_df = _parse_expense_workbook(
			expense_bytes,
			expense_sheet=expense_sheet,
			expense_period=expense_period,
		)

		if employee_file is not None and (employee_file.filename or "").strip():
			employee_bytes = await employee_file.read()
			if not employee_bytes:
				raise HTTPException(status_code=400, detail="人员列表文件为空，请重新上传")
			employee_df = _read_excel_with_fallback(employee_bytes, header=0, dtype=str)
			employee_df.columns = [str(col).strip() for col in employee_df.columns]
		else:
			employee_df = load_employee_data(default_config)

		if subject_file is not None and (subject_file.filename or "").strip():
			subject_bytes = await subject_file.read()
			if not subject_bytes:
				raise HTTPException(status_code=400, detail="科目映射文件为空，请重新上传")
			subject_df = pd.read_csv(io.BytesIO(subject_bytes), encoding="utf-8-sig")
			subject_df.columns = [str(col).strip() for col in subject_df.columns]
		else:
			subject_df = load_subject_mapping(default_config)
	except Exception as exc:  # pragma: no cover - relies on user provided files
		raise HTTPException(status_code=400, detail=f"上传文件解析失败：{exc}") from exc

	preparer_value = preparer.strip() or VoucherConfig().preparer
	voucher_category_value = voucher_category.strip() or VoucherConfig().voucher_category
	credit_account_value = credit_account.strip() or VoucherConfig().credit_account_default

	try:
		with tempfile.TemporaryDirectory() as tmpdir:
			tmp_path = Path(tmpdir)
			output_dir = tmp_path / "output"
			mapping_path = tmp_path / "translation_mapping.csv"

			if translation_file is not None and (translation_file.filename or "").strip():
				mapping_bytes = await translation_file.read()
				if not mapping_bytes:
					raise HTTPException(status_code=400, detail="翻译映射文件为空，请重新上传")
				mapping_path.write_bytes(mapping_bytes)
			else:
				default_mapping_path = default_config.translation_mapping_path
				if default_mapping_path.exists():
					mapping_path.write_bytes(default_mapping_path.read_bytes())
				else:
					mapping_path.write_text("source,target\n", encoding="utf-8-sig")

			config = VoucherConfig(
				expense_period=expense_period_value,
				preparer=preparer_value,
				voucher_category=voucher_category_value,
				credit_account_default=credit_account_value,
				voucher_start_sequence=start_seq,
				output_dir=output_dir,
				translation_mapping_path=mapping_path,
			)

			df_out = generate_vouchers(
				config,
				expense_df=expense_df,
				employee_df=employee_df,
				subject_df=subject_df,
			)

			if df_out.empty:
				raise HTTPException(status_code=400, detail="生成结果为空，请检查上传数据是否正确。")

			zip_buffer = io.BytesIO()
			with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
				csv_path = output_dir / "vouchers.csv"
				if csv_path.exists():
					archive.write(csv_path, arcname="vouchers.csv")
				xlsx_path = output_dir / "vouchers.xlsx"
				if xlsx_path.exists():
					archive.write(xlsx_path, arcname="vouchers.xlsx")
				if mapping_path.exists() and mapping_path.read_text(encoding="utf-8-sig").strip() != "source,target":
					archive.write(mapping_path, arcname="translation_mapping.csv")

			zip_buffer.seek(0)
	except HTTPException:
		raise
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:  # pragma: no cover
		raise HTTPException(status_code=500, detail=f"生成凭证时发生错误：{exc}") from exc

	headers = {"Content-Disposition": "attachment; filename=vouchers_bundle.zip"}
	return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


def _parse_expense_workbook(
	data: bytes,
	expense_sheet: Optional[str],
	expense_period: Optional[str],
) -> tuple[str, pd.DataFrame]:
	errors: list[str] = []
	try:
		buffer = io.BytesIO(data)
		excel = pd.ExcelFile(buffer, engine="openpyxl")
		target_sheet = expense_sheet or (excel.sheet_names[0] if excel.sheet_names else None)
		if target_sheet is None:
			raise ValueError("费用工作簿中未找到任何工作表")
		df = excel.parse(sheet_name=target_sheet, header=1)
		excel.close()
		return (expense_period or str(target_sheet)).strip(), df
	except Exception as exc_openpyxl:
		try:
			target_sheet_name, df_xls = _read_xls_with_xlrd(data, expense_sheet, header=1)
			return (expense_period or target_sheet_name).strip(), df_xls
		except Exception as exc_xlrd:
			raise HTTPException(
				status_code=400,
				detail=f"费用工作簿解析失败：openpyxl: {exc_openpyxl}; xlrd: {exc_xlrd}",
			) from exc_xlrd


def _read_excel_with_fallback(
	data: bytes,
	*,
	header: int = 0,
	dtype: Optional[object] = None,
) -> pd.DataFrame:
	try:
		buffer = io.BytesIO(data)
		return pd.read_excel(buffer, header=header, dtype=dtype, engine="openpyxl")
	except Exception as exc_openpyxl:
		try:
			_, df_xls = _read_xls_with_xlrd(data, None, header=header, dtype=dtype)
			return df_xls
		except Exception as exc_xlrd:
			raise HTTPException(
				status_code=400,
				detail=f"Excel 解析失败：openpyxl: {exc_openpyxl}; xlrd: {exc_xlrd}",
			) from exc_xlrd


def _read_xls_with_xlrd(
	data: bytes,
	sheet: Optional[str],
	*,
	header: int = 0,
	dtype: Optional[object] = None,
) -> Tuple[str, pd.DataFrame]:
	tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
	try:
		tmp.write(data)
		tmp.flush()
		tmp_path = Path(tmp.name)
	finally:
		tmp.close()

	try:
		book = xlrd.open_workbook(filename=str(tmp_path))

		target_sheet: xlrd.sheet.Sheet
		if sheet is None:
			target_sheet = book.sheet_by_index(0)
		elif isinstance(sheet, int):
			target_sheet = book.sheet_by_index(sheet)
		else:
			try:
				target_sheet = book.sheet_by_name(sheet)
			except xlrd.biffh.XLRDError:
				try:
					target_sheet = book.sheet_by_index(int(sheet))
				except Exception as exc:
					raise xlrd.biffh.XLRDError(f"未找到工作表：{sheet}") from exc

		header_row = header
		if header_row >= target_sheet.nrows:
			raise ValueError("指定的 header 行超出范围")

		columns = [str(value).strip() for value in target_sheet.row_values(header_row)]
		data_rows = [
			target_sheet.row_values(row_idx)
			for row_idx in range(header_row + 1, target_sheet.nrows)
		]

		df = pd.DataFrame(data_rows, columns=columns)
		if dtype == str:
			df = df.astype(str)
		return target_sheet.name, df
	finally:
		try:
			tmp_path.unlink(missing_ok=True)
		except Exception:
			pass
