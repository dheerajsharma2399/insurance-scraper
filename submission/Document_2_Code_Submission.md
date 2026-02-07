# Document 2: Code Submission - Insurance Financial Parser

## Implementation
The following Python script implements the section-based parsing logic described in Document 1. It is designed to be lightweight, fast, and easily integrated into existing pipelines.

```python
import re
import json

class InsuranceFinancialParser:
    """
    A robust parser for extracting financial fields from insurance documents.
    Uses section-based context and proximity regex matching.
    """

    def __init__(self):
        # Define field patterns and their associated context keywords
        self.field_definitions = {
            "total_premium": {
                "keywords": ["total premium", "total amount due", "total payable", "final premium", "total due"],
                "pattern": r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            },
            "net_premium": {
                "keywords": ["net premium", "basic premium", "premium amount", "amount before tax"],
                "pattern": r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            },
            "tax_amount": {
                "keywords": ["gst", "tax", "ipt", "levy", "vat", "service tax"],
                "pattern": r"(?<!\()(\d{1,3}(?:,\d{3})*(?:\.\d{2}))"  # Requires decimal, avoids (18%)
            },
            "deductible": {
                "keywords": ["deductible", "excess", "self-insured", "compulsory excess"],
                "pattern": r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            },
            "coverage_limit": {
                "keywords": ["sum insured", "limit of liability", "total coverage", "max payout", "limit"],
                "pattern": r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            },
            "admin_fee": {
                "keywords": ["policy fee", "admin fee", "documentation fee", "installment fee"],
                "pattern": r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            },
            "discount": {
                "keywords": ["discount", "ncb", "no claim bonus", "loyalty bonus"],
                "pattern": r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
            }
        }
        
    def _normalize_currency(self, text):
        """Converts string currency to float."""
        if not text:
            return 0.0
        # Remove commas and currency symbols
        clean_text = re.sub(r'[^\d.]', '', text)
        try:
            return float(clean_text)
        except ValueError:
            return 0.0

    def parse_text(self, document_text):
        """
        Parses text to find financial fields.
        Logic: Scans for keywords, then looks for the nearest numeric value within a context window.
        """
        results = {}
        for field, config in self.field_definitions.items():
            best_match = None
            highest_confidence = 0
            
            for keyword in config["keywords"]:
                keyword_search = re.compile(re.escape(keyword), re.IGNORECASE)
                for match in keyword_search.finditer(document_text):
                    start_pos = match.start()
                    context_window = document_text[start_pos : start_pos + 80]
                    
                    # Find potential currency matches in this window
                    value_matches = []
                    for val in re.findall(config["pattern"], context_window):
                        # Filter out values that are followed by % or within parentheses
                        if f"{val}%" in context_window or f"({val}%)" in context_window:
                            continue
                        value_matches.append(val)
                    
                    if value_matches:
                        value = value_matches[0]
                        dist = context_window.find(value)
                        confidence = 1.0 - (dist / 80.0)
                        
                        if confidence > highest_confidence:
                            best_match = self._normalize_currency(value)
                            highest_confidence = confidence
            
            results[field] = best_match if best_match is not None else 0.0
            
        return results

    def finalize_results(self, results):
        """Business logic validation."""
        if results.get("total_premium") == 0 and results.get("net_premium", 0) > 0:
            results["total_premium"] = results["net_premium"] + results.get("tax_amount", 0)
        return results

# Usage Example
if __name__ == "__main__":
    parser = InsuranceFinancialParser()
    sample_text = "Total Premium: 1,500.00, GST: 270.00"
    data = parser.parse_text(sample_text)
    print(json.dumps(data, indent=4))
```

## How to Run
1. Ensure you have Python 3.x installed.
2. Place the code in a file named `insurance_financial_parser.py`.
3. Run using `python insurance_financial_parser.py`.
