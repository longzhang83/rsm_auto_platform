import sys
from accounting_voucher_generation.cli import main as cli_main


if __name__ == "__main__":
	# 如果没有提供参数，默认执行凭证生成命令（向后兼容）
	if len(sys.argv) == 1:
		sys.argv.insert(1, "generate")
	raise SystemExit(cli_main())
