# Insurance Document Parser

Extract financial data from insurance policy PDFs automatically. Supports Life, Health, and Auto insurance documents.

## Features

- **Multi-format Support**: Handles Life, Health, and Auto insurance policies
- **Smart Extraction**: Uses pattern matching and context analysis
- **High Accuracy**: Confidence scoring for each extracted field
- **Easy Integration**: Simple Python API
- **Export Options**: JSON output with detailed metadata

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd insurance-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
python insurance_parser.py sample_documents/Policy1_5645166.pdf
```

## Usage Examples

### Python API

```python
from insurance_parser import InsuranceDocumentParser

parser = InsuranceDocumentParser()
result = parser.parse_pdf('policy.pdf')

# Access extracted fields
print(f"Policy Number: {result.fields['policy_number'].value}")
print(f"Total Premium: ₹{result.fields['total_premium'].value:,.2f}")
print(f"Document Type: {result.document_metadata['document_type']}")

# Export to JSON
with open('results.json', 'w') as f:
    f.write(result.to_json())
```

### Extracted Fields

The parser can extract:

**Policy Information**
- Policy number
- Issue date, effective date, expiry date
- Previous policy details

**Premium Details**
- Total premium, annual premium, monthly premium
- GST amount
- Discounts (NCB, etc.)

**Coverage Information**
- Sum insured / Sum assured
- Deductibles
- Cash value, bonus amounts

**Auto Insurance Specific**
- Vehicle registration number
- IDV (Insured Declared Value)
- Own damage premium
- Third party premium

## Output Format

```json
{
  "document_metadata": {
    "filename": "policy.pdf",
    "pages": 2,
    "document_type": "auto_insurance",
    "extraction_timestamp": "2026-02-07T03:00:00"
  },
  "fields": {
    "policy_number": {
      "value": "3322/02342489/000/00",
      "confidence": 0.95,
      "page": 1,
      "context": "Policy No: 3322/02342489/000/00..."
    },
    "total_premium": {
      "value": 19557.0,
      "confidence": 0.93,
      "page": 1,
      "context": "Gross Premium Paid 19,557"
    }
  }
}
```

## Project Structure

```
insurance-scraper/
├── insurance_parser.py      # Core parser module
├── test_improved_parser.py   # Test suite
├── requirements.txt          # Dependencies
├── sample_documents/         # Example PDFs
├── test_results/             # Test outputs
└── README.md                 # This file
```

## How It Works

1. **PDF Extraction**: Uses `pdfplumber` to extract text and tables
2. **Pattern Matching**: Regex patterns identify currency, dates, policy numbers
3. **Context Analysis**: Surrounding text determines field types
4. **Validation**: Checks values are within reasonable ranges
5. **Confidence Scoring**: Each field gets a confidence score (0-1)

## Configuration

### Confidence Threshold

Adjust minimum confidence in the web UI or filter programmatically:

```python
high_confidence_fields = {
    name: field for name, field in result.fields.items()
    if field.confidence >= 0.8
}
```

### Custom Patterns

Extend the `PatternMatcher` class to add new patterns:

```python
class CustomPatternMatcher(PatternMatcher):
    CUSTOM_PATTERNS = [r'your-pattern-here']
```

## Testing

Run the test suite:

```bash
python test_improved_parser.py
```

Expected output:
- Both sample documents parse successfully
- 9+ fields extracted per document
- Average confidence ≥80%

## Requirements

- Python 3.8+
- pdfplumber
- pandas

See `requirements.txt` for complete list.

## Limitations

- Works best with digital PDFs (not scanned images)
- Requires structured insurance documents
- May need pattern adjustments for different insurers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use in your projects

## Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This tool is for data extraction purposes only. Always verify extracted information against original documents.
