import pdfplumber
import pandas as pd
import numpy as np

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses a bank statement PDF to extract transaction data into a pandas DataFrame.

    Args:
        pdf_path (str): The path to the PDF bank statement file.

    Returns:
        pd.DataFrame: A DataFrame containing the extracted transaction data with
                      columns: ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'].
    """
    all_extracted_rows = []
    header = []
    
    # Define the exact columns expected in the final DataFrame
    expected_columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract all tables found on the current page
            tables = page.extract_tables()
            
            if not tables:
                continue # No tables found on this page, move to the next page

            # Assuming the first table found on the page contains the primary transaction data
            current_table = tables[0]

            if not current_table:
                continue # The extracted table is empty, skip it

            # If the header has not been established yet, set it from the first row of the first valid table
            if not header:
                # Clean header names (strip leading/trailing whitespace)
                header = [h.strip() if h else '' for h in current_table[0]]
                # Add data rows, skipping the header row as it's now stored separately
                all_extracted_rows.extend(current_table[1:])
            else:
                # For subsequent pages/tables, assume the first row is a repeated header
                # and skip it to avoid duplicating header rows in the data.
                # Only append if there are actual data rows present after the potential header.
                if len(current_table) > 1:
                    all_extracted_rows.extend(current_table[1:])
    
    # If no data was extracted after processing all pages (e.g., PDF was empty or malformed),
    # return an empty DataFrame with the correct expected columns.
    if not all_extracted_rows or not header:
        return pd.DataFrame(columns=expected_columns)

    # Create an initial DataFrame using the extracted rows and the collected header
    df = pd.DataFrame(all_extracted_rows, columns=header)

    # Ensure the DataFrame has exactly the expected columns, in the specified order.
    # Columns present in `df` but not in `expected_columns` will be dropped.
    # Columns in `expected_columns` but not in `df` will be added with NaN values.
    df = df.reindex(columns=expected_columns)

    # Perform type conversion and data cleaning for numeric columns
    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        if col in df.columns:
            # Replace various representations of empty or missing values (empty string, space, None)
            # with numpy's NaN before converting to numeric type. This makes numeric conversion robust.
            df[col] = df[col].replace(['', ' ', None], np.nan)
            # Convert the column to a numeric type (float). 'errors='coerce'' will turn any values
            # that cannot be parsed as a number (e.g., non-numeric strings) into NaN.
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 'Date' and 'Description' columns are typically strings and should retain their original string format
    # as extracted by pdfplumber. No further specific conversion is needed for these.

    return df
