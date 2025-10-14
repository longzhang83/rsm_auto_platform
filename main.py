import pandas as pd

import os
from pathlib import Path
from datetime import datetime


# 读取数据
# 注意：确保 data 目录下存在以下文件：Expense.xlsx, 人员列表.xlsx, 科目映射.csv
data_dir = Path('./data')
df_expanse = pd.read_excel(data_dir / 'Expense.xlsx', usecols='A:AC', header=1, engine='openpyxl')
df_employee = pd.read_excel(data_dir / '人员列表.xlsx', usecols='B:M', header=0, engine='openpyxl', dtype=str)
df_accounting_subject = pd.read_csv(data_dir / '科目映射.csv', header=0)


#df_employee 数据格式：
# 姓名	编码	行政部门名称	部门	雇佣状态	人员类别	性别	出生日期	业务或费用部门名称	到职日期	离职日期	英文名
# 殷子心	0001	部门	01	在职	正式工	男		部门			Ying Zee
# 马章瑜	0002	部门	01	在职	正式工	男		部门			Ma Morris



#获取费用类型列
expense_types = df_expanse.columns[9:26]

#df_expanse的列名包括：报销形式	公司	审批编码	姓名	部门-详	部门	费用科目	费用摘要	日期	差旅费交通	住宿费	文印快递	招待费	市内交通	油费	过路过桥停车费	团建费	固定资产	IT建设	福利费	办公费	维修费	市场费	会务费	通讯费	出差餐补	其他
#每一笔凭证要生成2行，借方和贷方

#生成的会计分录数据示例
# 凭证ID	会计年	会计期间	制单日期	凭证类别	凭证号	制单人	科目编码	摘要	币种名称	原币借方	原币贷方	借方金额	贷方金额	部门编码	职员编码
# 70001	2025	7	2025/7/31	记	0001	cissy	660215	周肖琪-快递费/Zhou Emily-Express charge	人民币	34	0	34	0
# 70001	2025	7	2025/7/31	记	0001	cissy	224104	周肖琪-快递费/Zhou Emily-Express charge	人民币	0	34	0	34	01	0019


#遍历df_expanse的每一行，生成凭证
#凭证中需要的字段有：凭证ID	会计年	会计期间	制单日期	凭证类别	凭证号	制单人	科目编码	摘要	币种名称	原币借方	原币贷方	借方金额	贷方金额	部门编码	职员编码
 # build a dict for quick subject lookup: 科目 -> 编码
subject_map = {str(r['科目']).strip(): str(r['编码']).strip() for _, r in df_accounting_subject.iterrows()}


def find_employee(name: str):
	"""Try to find employee code and dept code by name.
	Returns (职员编码, 部门编码) or (None, None) if not found.
	"""
	if not isinstance(name, str) or not name.strip():

		for index, row in df_expanse.iterrows():
			# build voucher header values (only once per row)
			voucher_seq += 1
			# date handling
			try:
				dt = pd.to_datetime(row.get('日期'))
				v_year = dt.year
				v_period = dt.month
			except Exception:
				v_year = datetime.now().year
				v_period = datetime.now().month
				print(f"Warning: invalid date in row {index+2}, using today as voucher period")
			# set 制单日期 to last day of v_year/v_period
			if v_period == 12:
				next_month = datetime(v_year+1, 1, 1)
			else:
				next_month = datetime(v_year, v_period+1, 1)
			v_date = (next_month - pd.Timedelta(days=1)).strftime('%Y/%m/%d')

			v_id = f"{str(v_period).zfill(2)}{str(voucher_seq).zfill(4)}"
			voucher_no = str(voucher_seq).zfill(4)
			preparer = "cissy"

			name = row.get('姓名') if '姓名' in row.index else None
			emp_code, dept_code = find_employee(name if pd.notna(name) else '')

			# iterate expense-type columns and create voucher lines when amount > 0
			for exp_col in expense_types:
				try:
					amt = row.get(exp_col)
				except Exception:
					amt = None
				if pd.isna(amt) or amt == 0:
					continue
				try:
					amt = float(amt)
				except Exception:
					continue
				if amt == 0:
					continue

				# description
				desc_parts = []
				if pd.notna(name):
					desc_parts.append(str(name))
				if pd.notna(row.get('费用摘要')):
					desc_parts.append(str(row.get('费用摘要')))
				desc_parts.append(str(exp_col))
				summary = '-'.join([p for p in desc_parts if p])

				# map debit subject
				debit_code = map_subject(exp_col, row)
				# default credit account
				credit_code = '224104'

				# construct debit line
				debit_line = {
					'凭证ID': v_id,
					'会计年': v_year,
					'会计期间': v_period,
					'制单日期': v_date,
					'凭证类别': '记',
					'凭证号': voucher_no,
					'制单人': preparer,
					'科目编码': debit_code or '',
					'摘要': summary,
					'币种名称': '人民币',
					'原币借方': amt,
					'原币贷方': 0,
					'借方金额': amt,
					'贷方金额': 0,
					'部门编码': dept_code or '',
					'职员编码': emp_code or ''
				}

				# construct credit line
				credit_line = {
					'凭证ID': v_id,
					'会计年': v_year,
					'会计期间': v_period,
					'制单日期': v_date,
					'凭证类别': '记',
					'凭证号': voucher_no,
					'制单人': preparer,
					'科目编码': credit_code,
					'摘要': summary,
					'币种名称': '人民币',
					'原币借方': 0,
					'原币贷方': amt,
					'借方金额': 0,
					'贷方金额': amt,
					'部门编码': dept_code or '',
					'职员编码': emp_code or ''
				}

				voucher_rows.append(debit_line)
				voucher_rows.append(credit_line)
			desc_parts.append(str(row.get('费用摘要')))
		desc_parts.append(str(exp_col))
		summary = '-'.join([p for p in desc_parts if p])

		# map debit subject
		debit_code = map_subject(exp_col, row)
		# default credit account
		credit_code = '224104'

		# find employee and dept codes
		emp_code, dept_code = find_employee(name if pd.notna(name) else '')

		# construct debit line
		debit_line = {
			'凭证ID': v_id,
			'会计年': v_year,
			'会计期间': v_period,
			'制单日期': v_date,
			'凭证类别': '记',
			'凭证号': voucher_no,
			'制单人': preparer,
			'科目编码': debit_code or '',
			'摘要': summary,
			'币种名称': '人民币',
			'原币借方': amt,
			'原币贷方': 0,
			'借方金额': amt,
			'贷方金额': 0,
			'部门编码': '',
			'职员编码': ''
		}

		# construct credit line
		credit_line = {
			'凭证ID': v_id,
			'会计年': v_year,
			'会计期间': v_period,
			'制单日期': v_date,
			'凭证类别': '记',
			'凭证号': voucher_no,
			'制单人': preparer,
			'科目编码': credit_code,
			'摘要': summary,
			'币种名称': '人民币',
			'原币借方': 0,
			'原币贷方': amt,
			'借方金额': 0,
			'贷方金额': amt,
			'部门编码': dept_code or '',
			'职员编码': emp_code or ''
		}

		voucher_rows.append(debit_line)
		voucher_rows.append(credit_line)


# write output
out_dir = Path('./data/output')
out_dir.mkdir(parents=True, exist_ok=True)
out_csv = out_dir / 'vouchers.csv'
out_xlsx = out_dir / 'vouchers.xlsx'
df_out = pd.DataFrame(voucher_rows)
if not df_out.empty:
	df_out.to_csv(out_csv, index=False, encoding='utf-8-sig')
	try:
		df_out.to_excel(out_xlsx, index=False, engine='openpyxl')
	except Exception:
		# if openpyxl missing, skip xlsx export
		pass

print(f'Generated {len(df_out)} voucher lines -> {out_csv} {out_xlsx}')

