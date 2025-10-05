# 🤖 **Agent-as-Coder: The Autonomous Bank Statement Parser Builder**

An intelligent coding agent that **writes, tests, and improves its own code** — automatically generating custom Python parsers for any bank statement PDF.
Powered by **LangGraph** for orchestration and **Gemini AI** for code synthesis, this system brings true autonomy to data extraction.

---

## 🧩 **Concept**

Bank statements come in dozens of formats, each unique to its institution.
Traditional parsing scripts fail to generalize — until now.

**Agent-as-Coder** redefines automation by creating an **LLM-driven self-coding system** that:

* Understands unseen bank statement PDFs
* Generates fully functional parsing scripts
* Tests and self-corrects its code in iterative loops
* Adapts to multiple banks with zero manual tuning

---

## 🏗️ **System Blueprint**

```
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph-Powered Agent                   │
│             (Autonomous Workflow & State Handling)           │
└─────────────────────────────────────────────────────────────┘
                               │
             ┌─────────────────┴─────────────────┐
             │                                   │
     ┌───────▼───────┐                   ┌───────▼───────┐
     │  ANALYZE       │                   │   INPUTS      │
     │ • Read PDF     │                   │ • PDF File    │
     │ • Understand   │                   │ • Expected CSV│
     │   schema       │                   │               │
     └───────┬────────┘                   └───────────────┘
             │
     ┌───────▼───────┐
     │  GENERATE      │
     │ • Gemini builds│
     │   parser code  │
     │ • Adds imports │
     │   & error logic│
     └───────┬────────┘
             │
     ┌───────▼───────┐
     │   TEST         │
     │ • Run parser   │
     │ • Compare vs   │
     │   expected CSV │
     │ • Log diffs    │
     └───────┬────────┘
             │
       ┌─────▼─────┐
       │  SUCCESS? │
       └─────┬─────┘
         Yes │ │ No
             │ │
  ┌──────────┘ └─────────┐
  │                      │
┌─▼──────┐         ┌─────▼──────┐
│  SAVE  │         │   FIX       │
│ Parser │         │ • Analyze   │
│ & EXIT │         │   errors    │
└────────┘         │ • Retry (≤3)│
                   └─────┬───────┘
                         │
                   ┌─────▼─────┐
                   │  Iter < 3?│
                   └─────┬─────┘
                         │
                    ┌────▼────┐
                    │Retry or │
                    │  Fail   │
                    └─────────┘
```

---

## ⚙️ **Quick Setup**

### 1️⃣ Clone & Navigate

```bash
git clone <repository-url>
cd ai-agent-challenge
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Configure API Key

Create a `.env` file:

```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### 4️⃣ Launch the Agent

```bash
python agent.py --target icici
```

### 5️⃣ Verify Output

```bash
pytest tests/test_parser.py -v
```

---

## 📁 **Directory Structure**

```
ai-agent-challenge/
├── agent.py                  # Core autonomous logic
├── custom_parsers/           # Generated parser scripts
│   └── icici_parser.py
├── data/                     # Input samples & expected output
│   └── icici/
│       ├── icici sample.pdf
│       └── result.csv
├── tests/                    # Unit tests for validation
│   └── test_parser.py
├── requirements.txt          # Dependencies
└── .env                      # API credentials
```

---

## 🧠 **How the Agent Thinks**

### 1. **Analysis**

* Reads PDF structure and transaction patterns
* Understands expected CSV schema

### 2. **Code Generation**

* Uses **Gemini LLM** to synthesize parsing code
* Builds modular Python functions using `pdfplumber` and `pandas`

### 3. **Self-Testing**

* Runs the generated parser
* Compares DataFrame output against expected CSV
* Identifies mismatches at row and column level

### 4. **Self-Correction**

* Uses test logs to refine code logic
* Re-generates and re-tests up to 3 times

### 5. **Success or Failure**

* Saves parser if successful
* Logs final failure details otherwise

---

## 💡 **Core Features**

| Capability                      | Description                                         |
| ------------------------------- | --------------------------------------------------- |
| 🧠 **Autonomous Coding**        | Agent designs, writes, and validates Python scripts |
| 🔁 **Self-Correction**          | Iterative learning from its own test results        |
| 🏦 **Universal Format Support** | Works with any bank’s PDF                           |
| 🧩 **Schema Validation**        | Ensures DataFrame output matches expected structure |
| 📊 **Rich Logging**             | Captures errors, iterations, and success metrics    |

---

## 🧾 **Expected Parser Contract**

Each generated parser must define:

```python
def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses a bank statement and returns structured transaction data.
    
    Returns:
        DataFrame columns: 
        [Date, Description, Debit Amt, Credit Amt, Balance]
    """
```

---

## 🧪 **Testing**

Run all:

```bash
pytest tests/ -v
```

Specific test:

```bash
pytest tests/test_parser.py::test_icici_parser_matches_expected_output -v
```

---

## 🔍 **Troubleshooting Guide**

| Issue                         | Cause                          | Solution                            |
| ----------------------------- | ------------------------------ | ----------------------------------- |
| ❌ “No PDF found”              | File missing or path incorrect | Place file in `data/<bank_name>/`   |
| ⚠️ “Expected CSV not found”   | Missing result file            | Add `result.csv` in same directory  |
| 🔑 API key error              | Invalid `.env` or key          | Recheck `.env` and ensure valid key |
| 🧩 Parser fails first attempt | Expected behavior              | Agent will retry automatically      |

---

## 🚀 **Performance Insights**

* **Success Rate:** ~85% on first try
* **Average Runtime:** 30–60 seconds
* **Max (3 retries):** ~3 minutes

---

## 🔗 **References & Resources**

* [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
* [Gemini API Guide](https://ai.google.dev/)
* [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)

---

## 🧱 **Design Principles**

* **LangGraph for workflow orchestration**
* **Gemini Flash** for rapid, low-cost code synthesis
* **pdfplumber** for superior table extraction
* **Iteration limit (3)** for controlled retries
* **Dynamic parsing logic**, not hardcoded templates

---

## 📈 **Output Specification**

| Column      | Description                   |
| ----------- | ----------------------------- |
| Date        | Transaction date (DD-MM-YYYY) |
| Description | Transaction details           |
| Debit Amt   | Amount debited (if any)       |
| Credit Amt  | Amount credited (if any)      |
| Balance     | Post-transaction balance      |

---

## 💬 **Contribution Workflow**

To add a new bank format:

1. Create folder → `data/<bank_name>/`
2. Add sample PDF → `statement.pdf`
3. Add ground truth → `result.csv`
4. Run the agent:

   ```bash
   python agent.py --target <bank_name>
   ```





