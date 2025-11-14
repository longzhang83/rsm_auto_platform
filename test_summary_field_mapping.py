"""
Test summary field one-to-many mapping feature

Test scenarios:
1. Single column summary mapping
2. Multi-column summary mapping (separated by /)
3. First field is empty, get from second field
4. All fields are empty
5. Column doesn't exist
"""

import pandas as pd
import sys
from pathlib import Path
import io

# Add src path to sys.path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from accounting_voucher_generation.bank_statement_pipeline import _extract_summary_from_columns

# Set stdout encoding to UTF-8 for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_single_column_summary():
    """Test single column summary mapping"""
    print("\nTest 1: Single column summary mapping")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary": ["Payment to supplier"],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "Summary", df)
    expected = "Payment to supplier"

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Single column mapping correct: '{result}'")


def test_multi_column_fallback():
    """Test multi-column mapping - first field empty"""
    print("\nTest 2: Multi-column mapping - first field empty")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": [""],
        "Summary2": ["Rent payment"],
        "Summary3": ["Other info"],
        "Amount": [1000.00]
    })

    # Configure to check Summary1, then Summary2, then Summary3
    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2/Summary3", df)
    expected = "Rent payment"

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Multi-column mapping correct (fallback to 2nd): '{result}'")


def test_multi_column_first_valid():
    """Test multi-column mapping - first field valid"""
    print("\nTest 3: Multi-column mapping - first field valid")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": ["Salary"],
        "Summary2": ["Rent payment"],
        "Summary3": ["Other info"],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2/Summary3", df)
    expected = "Salary"

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Multi-column mapping correct (use first): '{result}'")


def test_multi_column_all_empty():
    """Test multi-column mapping - all fields empty"""
    print("\nTest 4: Multi-column mapping - all fields empty")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": [""],
        "Summary2": [None],
        "Summary3": [""],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2/Summary3", df)
    expected = ""

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Multi-column mapping correct (all empty, return empty)")


def test_column_not_exist():
    """Test when columns don't exist"""
    print("\nTest 5: Column not exist")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Amount": [1000.00]
    })

    # Configure non-existent columns
    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2", df)
    expected = ""

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Non-existent columns handled correctly (return empty)")


def test_nan_values():
    """Test NaN value handling"""
    print("\nTest 6: NaN value handling")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": [float('nan')],
        "Summary2": ["Payment expense"],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2", df)
    expected = "Payment expense"

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] NaN values handled correctly (fallback to next): '{result}'")


def test_whitespace_handling():
    """Test whitespace handling"""
    print("\nTest 7: Whitespace handling")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": ["   "],
        "Summary2": ["  Salary payment  "],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2", df)
    expected = "Salary payment"

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Whitespace handled correctly: '{result}'")


def test_empty_spec():
    """Test empty spec case"""
    print("\nTest 8: Empty spec")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary": ["Payment"],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "", df)
    expected = ""

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Empty spec handled correctly")


def test_numeric_to_string():
    """Test numeric value handling"""
    print("\nTest 9: Numeric value handling")

    df = pd.DataFrame({
        "Date": ["2024-01-01"],
        "Summary1": [None],
        "Summary2": [12345],
        "Amount": [1000.00]
    })

    result = _extract_summary_from_columns(df.iloc[0], "Summary1/Summary2", df)
    expected = "12345"

    assert result == expected, f"Expected: '{expected}', Got: '{result}'"
    print(f"[PASS] Numeric values handled correctly: '{result}'")


def test_complex_scenario():
    """Test complex scenario - multiple rows with mixed empty fields"""
    print("\nTest 10: Complex scenario - multiple rows")

    df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "Summary1": ["Salary", "", None],
        "Summary2": ["", "Rent", "Notes"],
        "Summary3": ["Other", "Other", ""],
        "Amount": [5000, 3000, 2000]
    })

    results = [
        _extract_summary_from_columns(df.iloc[i], "Summary1/Summary2/Summary3", df)
        for i in range(len(df))
    ]

    expected = ["Salary", "Rent", "Notes"]

    assert results == expected, f"Expected: {expected}, Got: {results}"
    print(f"[PASS] Complex scenario handled correctly: {results}")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("Running summary field one-to-many mapping tests")
    print("=" * 70)

    tests = [
        test_single_column_summary,
        test_multi_column_fallback,
        test_multi_column_first_valid,
        test_multi_column_all_empty,
        test_column_not_exist,
        test_nan_values,
        test_whitespace_handling,
        test_empty_spec,
        test_numeric_to_string,
        test_complex_scenario,
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
            failed += 1

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
