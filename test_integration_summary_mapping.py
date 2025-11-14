"""
Integration test for summary field one-to-many mapping in bank statement processing

This test verifies that the summary field mapping works correctly in the
standardize_bank_statement_data() function
"""

import pandas as pd
import sys
from pathlib import Path
import io

# Add src path to sys.path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from accounting_voucher_generation.bank_statement_pipeline import (
    standardize_bank_statement_data,
)

# Set stdout encoding to UTF-8 for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_standardize_with_single_summary_column():
    """Test standardization with single summary column"""
    print("\nIntegration Test 1: Standardize with single summary column")

    # Create sample data
    df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02"],
        "Summary": ["Payment to supplier", "Rent expense"],
        "Counterparty": ["Supplier A", "Landlord B"],
        "BankAccount": ["123456789", "987654321"],
        "Debit": [1000.00, 2000.00],
        "Credit": [0.00, 0.00]
    })

    # Column mapping - single column
    column_mapping = {
        "date": "Date",
        "summary": "Summary",
        "counterparty": "Counterparty",
        "bank_account": "BankAccount",
        "debit": "Debit",
        "credit": "Credit"
    }

    # Standardize
    result = standardize_bank_statement_data(df, column_mapping)

    # Verify
    assert "摘要" in result.columns, "Summary column should exist"
    assert len(result) == 2, "Should have 2 rows"
    assert result["摘要"].iloc[0] == "Payment to supplier"
    assert result["摘要"].iloc[1] == "Rent expense"

    print("[PASS] Single column standardization works correctly")
    print(f"  Row 1 summary: '{result['摘要'].iloc[0]}'")
    print(f"  Row 2 summary: '{result['摘要'].iloc[1]}'")


def test_standardize_with_multi_summary_columns():
    """Test standardization with multi-column summary mapping"""
    print("\nIntegration Test 2: Standardize with multi-column summary mapping")

    # Create sample data with multi-column summary fields
    df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Summary1": ["Payment to supplier", "", None],  # First has value
        "Summary2": ["", "Rent expense", "Other notes"],  # Second fallback
        "Summary3": ["Other", "Other", ""],  # Third fallback
        "Counterparty": ["Supplier A", "Landlord B", "Customer C"],
        "BankAccount": ["123456789", "987654321", "555555555"],
        "Debit": [1000.00, 2000.00, 3000.00],
        "Credit": [0.00, 0.00, 0.00]
    })

    # Column mapping - multi-column with / separator
    column_mapping = {
        "date": "Date",
        "summary": "Summary1/Summary2/Summary3",  # Multi-column mapping
        "counterparty": "Counterparty",
        "bank_account": "BankAccount",
        "debit": "Debit",
        "credit": "Credit"
    }

    # Standardize
    result = standardize_bank_statement_data(df, column_mapping)

    # Verify
    assert "摘要" in result.columns, "Summary column should exist"
    assert len(result) == 3, "Should have 3 rows"

    # Row 1: First column has value
    assert result["摘要"].iloc[0] == "Payment to supplier", \
        f"Row 1 should use Summary1: '{result['摘要'].iloc[0]}'"

    # Row 2: First column empty, use second
    assert result["摘要"].iloc[1] == "Rent expense", \
        f"Row 2 should fallback to Summary2: '{result['摘要'].iloc[1]}'"

    # Row 3: First two empty, use third
    assert result["摘要"].iloc[2] == "Other notes", \
        f"Row 3 should fallback to Summary2: '{result['摘要'].iloc[2]}'"

    print("[PASS] Multi-column standardization works correctly")
    print(f"  Row 1 summary: '{result['摘要'].iloc[0]}' (from Summary1)")
    print(f"  Row 2 summary: '{result['摘要'].iloc[1]}' (fallback to Summary2)")
    print(f"  Row 3 summary: '{result['摘要'].iloc[2]}' (fallback to Summary2)")


def test_standardize_with_mixed_empty_values():
    """Test with mixed empty values (spaces, NaN, None, empty string)"""
    print("\nIntegration Test 3: Standardize with mixed empty values")

    df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "Summary1": ["   ", None, "", float('nan')],  # All variations of empty
        "Summary2": ["Space trimmed", "NaN fallback", "Empty fallback", "All fallback"],
        "Counterparty": ["A", "B", "C", "D"],
        "BankAccount": ["1", "2", "3", "4"],
        "Debit": [1000.00, 2000.00, 3000.00, 4000.00],
        "Credit": [0.00, 0.00, 0.00, 0.00]
    })

    column_mapping = {
        "date": "Date",
        "summary": "Summary1/Summary2",
        "counterparty": "Counterparty",
        "bank_account": "BankAccount",
        "debit": "Debit",
        "credit": "Credit"
    }

    result = standardize_bank_statement_data(df, column_mapping)

    # All rows should fall back to Summary2
    expected = ["Space trimmed", "NaN fallback", "Empty fallback", "All fallback"]
    actual = result["摘要"].tolist()

    assert actual == expected, f"Expected: {expected}, Got: {actual}"

    print("[PASS] Mixed empty values handled correctly")
    for i, summary in enumerate(actual):
        print(f"  Row {i+1} summary: '{summary}'")


def test_all_columns_empty():
    """Test when all summary columns are empty"""
    print("\nIntegration Test 4: Standardize with all summary columns empty")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": [""],
        "Summary2": [None],
        "Summary3": ["   "],
        "Counterparty": ["A"],
        "BankAccount": ["123"],
        "Debit": [1000.00],
        "Credit": [0.00]
    })

    column_mapping = {
        "date": "Date",
        "summary": "Summary1/Summary2/Summary3",
        "counterparty": "Counterparty",
        "bank_account": "BankAccount",
        "debit": "Debit",
        "credit": "Credit"
    }

    result = standardize_bank_statement_data(df, column_mapping)

    # Should have empty summary
    assert result["摘要"].iloc[0] == "", \
        f"Summary should be empty, got: '{result['摘要'].iloc[0]}'"

    print("[PASS] All empty summary columns handled correctly")
    print(f"  Summary is empty: '{result['摘要'].iloc[0]}'")


def run_integration_tests():
    """Run all integration tests"""
    print("=" * 70)
    print("Running integration tests for summary field mapping")
    print("=" * 70)

    tests = [
        test_standardize_with_single_summary_column,
        test_standardize_with_multi_summary_columns,
        test_standardize_with_mixed_empty_values,
        test_all_columns_empty,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"Integration Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
