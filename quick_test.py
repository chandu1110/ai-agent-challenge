import sys
from pathlib import Path
import pandas as pd

def main():
    """Run a quick test of the ICICI parser"""
    print("=" * 70)
    print("Quick Parser Test")
    print("=" * 70)
    
    # Check if parser exists
    parser_path = Path("custom_parsers/icici_parser.py")
    if not parser_path.exists():
        print("❌ Parser not found. Run: python agent.py --target icici")
        sys.exit(1)
    
    print("✅ Parser file found")
    
    # Import parser
    try:
        from custom_parsers.icici_parser import parse
        print("✅ Parser imported successfully")
    except Exception as e:
        print(f"❌ Failed to import parser: {e}")
        sys.exit(1)
    
    # Parse PDF
    pdf_path = "data/icici/icici sample.pdf"
    try:
        result_df = parse(pdf_path)
        print(f"✅ PDF parsed successfully - {len(result_df)} rows extracted")
    except Exception as e:
        print(f"❌ Failed to parse PDF: {e}")
        sys.exit(1)
    
    # Load expected output
    expected_df = pd.read_csv("data/icici/result.csv")
    
    # Compare
    print("\n" + "-" * 70)
    print("Comparison:")
    print("-" * 70)
    print(f"Rows extracted: {len(result_df)} (expected: {len(expected_df)})")
    print(f"Columns: {list(result_df.columns)}")
    
    # Normalize for comparison
    result_normalized = result_df.fillna('').astype(str)
    expected_normalized = expected_df.fillna('').astype(str)
    
    if result_normalized.equals(expected_normalized):
        print("✅ Output matches expected CSV perfectly!")
    else:
        print("⚠️  Output differs from expected CSV")
    
    print("\n" + "-" * 70)
    print("Sample Output (first 5 rows):")
    print("-" * 70)
    print(result_df.head().to_string())
    print("-" * 70)
    
    print("\n✅ Quick test complete!")


if __name__ == "__main__":
    main()
