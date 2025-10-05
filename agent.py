import os
import sys
import argparse
import traceback
from pathlib import Path
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv

import pandas as pd
import pdfplumber
import google.generativeai as genai
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')


class AgentState(TypedDict):
    """State for the agent workflow"""
    target_bank: str
    pdf_path: str
    csv_path: str
    parser_path: str
    pdf_analysis: str
    generated_code: str
    test_result: dict
    error_message: str
    iteration: int
    max_iterations: int
    status: Literal["planning", "generating", "testing", "fixing", "success", "failed"]


def analyze_pdf(state: AgentState) -> AgentState:
    """Analyze PDF structure and extract sample data"""
    print(f"\n📊 [Step 1/4] Analyzing PDF structure for {state['target_bank']}...")
    
    try:
        pdf_path = state['pdf_path']
        
        # Extract text and tables from PDF
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            tables_info = []
            
            for page_num, page in enumerate(pdf.pages[:3], 1):  # Analyze first 3 pages
                full_text += f"\n=== Page {page_num} ===\n"
                full_text += page.extract_text() or ""
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    tables_info.append({
                        'page': page_num,
                        'table_count': len(tables),
                        'sample_table': tables[0][:5] if tables else None  # First 5 rows
                    })
        
        # Load expected CSV to understand schema
        csv_df = pd.read_csv(state['csv_path'])
        expected_columns = csv_df.columns.tolist()
        sample_rows = csv_df.head(5).to_dict('records')
        
        analysis = f"""
PDF Analysis for {state['target_bank']} Bank Statement:

Expected Output Schema:
Columns: {expected_columns}
Sample Expected Output:
{pd.DataFrame(sample_rows).to_string()}

PDF Content Sample (first 500 chars):
{full_text[:500]}

Tables Found: {len(tables_info)} tables in first 3 pages
Sample Table Structure:
{tables_info[0]['sample_table'] if tables_info else 'No tables found'}

Total Expected Rows: {len(csv_df)}
"""
        
        state['pdf_analysis'] = analysis
        state['status'] = "generating"
        print("✅ PDF analysis complete")
        return state
        
    except Exception as e:
        state['error_message'] = f"PDF Analysis Error: {str(e)}\n{traceback.format_exc()}"
        state['status'] = "failed"
        print(f"❌ PDF analysis failed: {e}")
        return state


def generate_parser_code(state: AgentState) -> AgentState:
    """Generate parser code using LLM"""
    iteration_info = f" (Attempt {state['iteration']}/{state['max_iterations']})"
    print(f"\n🤖 [Step 2/4] Generating parser code{iteration_info}...")
    
    system_instruction = """You are an expert Python programmer specializing in PDF parsing and data extraction.
Your task is to write a robust parser function that extracts transaction data from bank statement PDFs.

Requirements:
1. Function signature: def parse(pdf_path: str) -> pd.DataFrame
2. Return DataFrame with exact columns as specified
3. Handle missing values (use empty string for missing Debit/Credit)
4. Preserve data types and formats from expected output
5. Use pdfplumber for PDF parsing (it's already imported)
6. Handle multi-page PDFs
7. Be robust to variations in PDF structure

Return ONLY the complete Python code, no explanations."""

    if state['error_message'] and state['iteration'] > 1:
        prompt = f"""Previous attempt failed with error:
{state['error_message']}

Previous code:
```python
{state['generated_code']}
```

Now generate IMPROVED code that fixes these issues.

{state['pdf_analysis']}

Generate the complete parser code:"""
    else:
        prompt = f"""{state['pdf_analysis']}

Generate a complete Python parser that:
1. Opens the PDF using pdfplumber
2. Extracts all transaction data
3. Returns a pandas DataFrame matching the expected schema exactly
4. Handles all edge cases (multi-page, missing values, etc.)

Generate the complete parser code:"""

    try:
        full_prompt = system_instruction + "\n\n" + prompt
        response = model.generate_content(full_prompt)
        code = response.text
        
        # Extract code from markdown if present
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        # Ensure necessary imports
        if "import pandas as pd" not in code:
            code = "import pandas as pd\n" + code
        if "import pdfplumber" not in code:
            code = "import pdfplumber\n" + code
        
        state['generated_code'] = code
        state['status'] = "testing"
        print("✅ Parser code generated")
        return state
        
    except Exception as e:
        state['error_message'] = f"Code Generation Error: {str(e)}\n{traceback.format_exc()}"
        state['status'] = "failed"
        print(f"❌ Code generation failed: {e}")
        return state


def test_parser(state: AgentState) -> AgentState:
    """Test the generated parser against expected output"""
    print(f"\n🧪 [Step 3/4] Testing generated parser...")
    
    try:
        # Save the generated code temporarily
        temp_parser_path = state['parser_path'].replace('.py', '_temp.py')
        with open(temp_parser_path, 'w') as f:
            f.write(state['generated_code'])
        
        # Import and execute the parser
        import importlib.util
        spec = importlib.util.spec_from_file_location("temp_parser", temp_parser_path)
        parser_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parser_module)
        
        # Run the parser
        result_df = parser_module.parse(state['pdf_path'])
        
        # Load expected output
        expected_df = pd.read_csv(state['csv_path'])
        
        # Compare results
        test_result = {
            'passed': False,
            'row_count_match': len(result_df) == len(expected_df),
            'column_match': list(result_df.columns) == list(expected_df.columns),
            'result_rows': len(result_df),
            'expected_rows': len(expected_df),
            'result_columns': list(result_df.columns),
            'expected_columns': list(expected_df.columns)
        }
        
        # Check if DataFrames are equal
        if test_result['row_count_match'] and test_result['column_match']:
            # Normalize data for comparison
            result_normalized = result_df.fillna('').astype(str)
            expected_normalized = expected_df.fillna('').astype(str)
            
            # Compare values
            differences = []
            for idx in range(min(len(result_normalized), len(expected_normalized))):
                for col in expected_df.columns:
                    if col in result_df.columns:
                        result_val = str(result_normalized.iloc[idx][col]).strip()
                        expected_val = str(expected_normalized.iloc[idx][col]).strip()
                        if result_val != expected_val:
                            differences.append({
                                'row': idx,
                                'column': col,
                                'result': result_val,
                                'expected': expected_val
                            })
            
            if len(differences) == 0:
                test_result['passed'] = True
                test_result['message'] = "✅ Perfect match!"
            else:
                test_result['differences'] = differences[:10]  # First 10 differences
                test_result['total_differences'] = len(differences)
                test_result['message'] = f"❌ Found {len(differences)} differences"
        else:
            test_result['message'] = "❌ Structure mismatch"
        
        state['test_result'] = test_result
        
        if test_result['passed']:
            # Save the successful parser
            with open(state['parser_path'], 'w') as f:
                f.write(state['generated_code'])
            state['status'] = "success"
            print(f"✅ Tests passed! Parser saved to {state['parser_path']}")
        else:
            state['status'] = "fixing"
            error_details = f"""Test Failed:
- Row count: {test_result['result_rows']} (expected {test_result['expected_rows']})
- Columns match: {test_result['column_match']}
- Result columns: {test_result['result_columns']}
- Expected columns: {test_result['expected_columns']}
"""
            if 'differences' in test_result:
                error_details += f"\nSample differences (first 10):\n"
                for diff in test_result['differences'][:5]:
                    error_details += f"  Row {diff['row']}, Column '{diff['column']}': got '{diff['result']}', expected '{diff['expected']}'\n"
            
            state['error_message'] = error_details
            print(f"❌ Tests failed: {test_result['message']}")
        
        # Clean up temp file
        if os.path.exists(temp_parser_path):
            os.remove(temp_parser_path)
        
        return state
        
    except Exception as e:
        state['error_message'] = f"Test Execution Error: {str(e)}\n{traceback.format_exc()}"
        state['status'] = "fixing"
        print(f"❌ Test execution failed: {e}")
        return state


def should_retry(state: AgentState) -> Literal["retry", "end"]:
    """Decide whether to retry or end"""
    if state['status'] == "success":
        return "end"
    elif state['iteration'] >= state['max_iterations']:
        print(f"\n⚠️  Max iterations ({state['max_iterations']}) reached. Stopping.")
        state['status'] = "failed"
        return "end"
    else:
        return "retry"


def fix_and_retry(state: AgentState) -> AgentState:
    """Prepare for retry with error context"""
    print(f"\n🔧 [Step 4/4] Analyzing errors and preparing retry...")
    state['status'] = "generating"
    state['iteration'] += 1
    return state


def create_agent_graph():
    """Create the LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_pdf)
    workflow.add_node("generate", generate_parser_code)
    workflow.add_node("test", test_parser)
    workflow.add_node("fix", fix_and_retry)
    
    # Add edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "generate")
    workflow.add_edge("generate", "test")
    workflow.add_conditional_edges(
        "test",
        should_retry,
        {
            "retry": "fix",
            "end": END
        }
    )
    workflow.add_edge("fix", "generate")
    
    return workflow.compile()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Autonomous agent that generates custom bank statement parsers"
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target bank name (e.g., icici, sbi, hdfc)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum self-correction attempts (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    target_bank = args.target.lower()
    data_dir = Path("data") / target_bank
    pdf_path = list(data_dir.glob("*.pdf"))[0] if data_dir.exists() else None
    csv_path = data_dir / "result.csv"
    parser_path = Path("custom_parsers") / f"{target_bank}_parser.py"
    
    # Validate inputs
    if not pdf_path or not pdf_path.exists():
        print(f"❌ Error: No PDF found in {data_dir}")
        sys.exit(1)
    if not csv_path.exists():
        print(f"❌ Error: Expected CSV not found at {csv_path}")
        sys.exit(1)
    
    print("=" * 70)
    print("🤖 AUTONOMOUS CODING AGENT - Bank Statement Parser Generator")
    print("=" * 70)
    print(f"Target Bank: {target_bank.upper()}")
    print(f"PDF Input: {pdf_path}")
    print(f"Expected Output: {csv_path}")
    print(f"Parser Output: {parser_path}")
    print(f"Max Iterations: {args.max_iterations}")
    print("=" * 70)
    
    # Initialize state
    initial_state = AgentState(
        target_bank=target_bank,
        pdf_path=str(pdf_path),
        csv_path=str(csv_path),
        parser_path=str(parser_path),
        pdf_analysis="",
        generated_code="",
        test_result={},
        error_message="",
        iteration=1,
        max_iterations=args.max_iterations,
        status="planning"
    )
    
    # Create and run agent
    agent = create_agent_graph()
    
    try:
        final_state = agent.invoke(initial_state)
        
        print("\n" + "=" * 70)
        if final_state['status'] == "success":
            print("🎉 SUCCESS! Parser generated and tested successfully!")
            print(f"✅ Parser saved to: {parser_path}")
            print(f"📊 Total iterations: {final_state['iteration']}")
        else:
            print("❌ FAILED to generate working parser")
            print(f"Last error: {final_state['error_message']}")
            sys.exit(1)
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Agent execution failed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
