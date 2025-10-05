"""
Test suite for generated bank statement parsers
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_icici_parser_exists():
    """Test that ICICI parser file exists"""
    parser_path = Path("custom_parsers/icici_parser.py")
    assert parser_path.exists(), f"Parser not found at {parser_path}"


def test_icici_parser_has_parse_function():
    """Test that parser has the required parse function"""
    from custom_parsers.icici_parser import parse
    assert callable(parse), "parse function should be callable"


def test_icici_parser_returns_dataframe():
    """Test that parser returns a pandas DataFrame"""
    from custom_parsers.icici_parser import parse
    
    pdf_path = "data/icici/icici sample.pdf"
    result = parse(pdf_path)
    
    assert isinstance(result, pd.DataFrame), "parse() should return a DataFrame"
    assert len(result) > 0, "DataFrame should not be empty"


def test_icici_parser_has_correct_columns():
    """Test that parser output has correct column names"""
    from custom_parsers.icici_parser import parse
    
    pdf_path = "data/icici/icici sample.pdf"
    result = parse(pdf_path)
    
    expected_columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
    assert list(result.columns) == expected_columns, \
        f"Columns mismatch. Expected {expected_columns}, got {list(result.columns)}"


def test_icici_parser_matches_expected_output():
    """Test that parser output matches the expected CSV"""
    from custom_parsers.icici_parser import parse
    
    pdf_path = "data/icici/icici sample.pdf"
    expected_csv = "data/icici/result.csv"
    
    result_df = parse(pdf_path)
    expected_df = pd.read_csv(expected_csv)
    
    # Normalize for comparison
    result_normalized = result_df.fillna('').astype(str)
    expected_normalized = expected_df.fillna('').astype(str)
    
    # Check row count
    assert len(result_df) == len(expected_df), \
        f"Row count mismatch: got {len(result_df)}, expected {len(expected_df)}"
    
    # Check if DataFrames are equal
    assert result_normalized.equals(expected_normalized), \
        "Parser output does not match expected CSV"


def test_icici_parser_row_count():
    """Test that parser extracts correct number of transactions"""
    from custom_parsers.icici_parser import parse
    
    pdf_path = "data/icici/icici sample.pdf"
    expected_csv = "data/icici/result.csv"
    
    result_df = parse(pdf_path)
    expected_df = pd.read_csv(expected_csv)
    
    assert len(result_df) == len(expected_df), \
        f"Expected {len(expected_df)} rows, got {len(result_df)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
