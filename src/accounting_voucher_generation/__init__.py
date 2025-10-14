"""Accounting voucher generation package."""

from .pipeline import generate_vouchers, VoucherConfig

__all__ = ["generate_vouchers", "VoucherConfig"]
