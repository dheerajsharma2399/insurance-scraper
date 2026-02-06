# Document 2: Code Submission

## Insurance Document Parser - Implementation

### Quick Start

```bash
# Install dependencies
pip install pdfplumber pandas python-dateutil

# Run parser
python insurance_parser.py <pdf_file>

# Example
python insurance_parser.py sample_documents/Policy1_5645166.pdf
```

### Output

The parser extracts financial fields and outputs:

1. **Console Output**: Summary of extracted fields
2. **JSON File**: Complete results with confidence scores

**Example Output:**
```
Extracted 10 fields from Policy1_5645166.pdf
Document type: auto_insurance

Fields:
  policy_number: 3322/02342489/000/00 (confidence: 95%)
  total_premium: 19557.0 (confidence: 93%)
  own_damage_premium: 19557.0 (confidence: 89%)
  third_party_premium: 3916.0 (confidence: 89%)
  gst_amount: 658.0 (confidence: 90%)
  ncb_discount: 50.0 (confidence: 87%)
  vehicle_registration: UP 14 DX 2531 (confidence: 88%)
  deductible: 1000.0 (confidence: 92%)
  issue_date: 29-NOV-2025 (confidence: 71%)
  expiry_date: 30/05/2028 (confidence: 63%)

Saved results to Policy1_5645166_results.json
```

---

## Python API Usage

```python
from insurance_parser import InsuranceDocumentParser

# Initialize parser
parser = InsuranceDocumentParser()

# Parse document
result = parser.parse_pdf('policy.pdf')

# Access fields
for field_name, field_data in result.fields.items():
    print(f"{field_name}: {field_data.value}")
    print(f"  Confidence: {field_data.confidence:.0%}")
    print(f"  Page: {field_data.page}")

# Get document metadata
print(f"Document type: {result.document_metadata['document_type']}")
print(f"Pages: {result.document_metadata['pages']}")

# Export to JSON
with open('output.json', 'w') as f:
    f.write(result.to_json())
```

---

## JSON Output Format

```json
{
  "document_metadata": {
    "filename": "Policy1_5645166.pdf",
    "extraction_timestamp": "2026-02-07T03:21:00.418611",
    "pages": 2,
    "document_type": "auto_insurance"
  },
  "fields": {
    "policy_number": {
      "value": "3322/02342489/000/00",
      "confidence": 0.95,
      "page": 1,
      "context": "Policy No: 3322/02342489/000/00 Proposal No..."
    },
    "total_premium": {
      "value": 19557.0,
      "confidence": 0.93,
      "page": 1,
      "context": "Gross Premium Paid 19,557"
    }
  },
  "tables_extracted": [
    {
      "page": 1,
      "table_type": "premium_breakdown",
      "headers": [...],
      "rows": [...]
    }
  ],
  "warnings": []
}
```

---

## Extracted Fields

The parser identifies and extracts the following financial fields:

### Core Policy Information
- `policy_number` - Unique policy identifier
- `issue_date` - Policy issuance date
- `effective_date` - Coverage start date
- `expiry_date` - Coverage end date

### Premium & Financial Details
- `total_premium` - Total amount payable
- `annual_premium` - Yearly premium amount
- `monthly_premium` - Monthly installment
- `gst_amount` - GST/tax amount
- `discount` - Applied discounts
- `ncb_discount` - No Claim Bonus

### Coverage Information
- `sum_insured` - Coverage amount
- `deductible` - Out-of-pocket amount
- `cash_value` - Surrender value
- `bonus` - Bonus amounts

### Auto Insurance Specific
- `vehicle_registration` - License plate number
- `idv` - Insured Declared Value
- `own_damage_premium` - OD premium component
- `third_party_premium` - TP premium component

---

## Implementation Details

### Core Components

1. **PatternMatcher** - Regex-based value extraction
2. **ContextMatcher** - Field type identification using keywords
3. **Validator** - Value range validation
4. **InsuranceDocumentParser** - Main orchestrator

### Key Features

- **Format Flexibility**: Handles variations in date/currency formats
- **Context-Aware**: Uses surrounding text to identify field types
- **Table Support**: Extracts structured data from tables
- **Confidence Scoring**: Each field has accuracy indicator
- **Document Classification**: Auto-detects insurance type

---

## Testing

Two sample insurance documents are included:

1. `sample_documents/Policy1_5645166.pdf` - Auto insurance (2 pages)
2. `sample_documents/car policy.pdf` - Auto insurance (6 pages)

**Run tests:**
```bash
python test_improved_parser.py
```

**Expected Results:**
- 7-10 fields extracted per document
- 80%+ average confidence
- Auto insurance type detected

---

## Requirements

- Python 3.8+
- pdfplumber>=0.10.3
- pandas>=2.0.0
- python-dateutil>=2.8.2

**Install:**
```bash
pip install -r requirements.txt
```

---

## File Structure

```
insurance-scraper/
├── insurance_parser.py          # Main parser (Document 2)
├── Document_1_Parsing_Approach.md  # Approach explanation
├── test_improved_parser.py      # Test suite
├── requirements.txt             # Dependencies
├── sample_documents/            # Test PDFs
│   ├── Policy1_5645166.pdf
│   └── car policy.pdf
└── test_results/                # Sample outputs
    ├── Policy1_5645166_results.json
    └── car_policy_improved_results.json
```

---

## Code Implementation

The complete implementation is in `insurance_parser.py` (550 lines):

**Main Classes:**
- `ExtractedField` - Data structure for field + metadata
- `ExtractionResult` - Container for all results
- `PatternMatcher` - Pattern extraction engine
- `ContextMatcher` - Context-based field identification
- `Validator` - Value validation
- `InsuranceDocumentParser` - Main parser orchestrator

**See `insurance_parser.py` for complete implementation.**

---

## Performance

- **Speed**: <3 seconds per document
- **Accuracy**: 80-95% confidence on most fields
- **Coverage**: Supports Life, Health, Auto insurance
- **Format Support**: Digital PDFs (structured text)

---

## Contact

For questions or clarifications about the implementation, please contact via careers@finuture.in

---

**Submission Date**: February 7, 2026
