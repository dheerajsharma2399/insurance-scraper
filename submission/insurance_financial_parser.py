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
        text_lower = document_text.lower()
        
        for field, config in self.field_definitions.items():
            best_match = None
            highest_confidence = 0
            
            for keyword in config["keywords"]:
                # Use regex to find keywords and their immediate context
                # This handles cases where values are on the same line or next line
                keyword_search = re.compile(re.escape(keyword), re.IGNORECASE)
                for match in keyword_search.finditer(document_text):
                    start_pos = match.start()
                    # Look ahead 50 characters for a numeric value
                    context_window = document_text[start_pos : start_pos + 60]
                    
                    # Find potential currency matches in this window
                    value_matches = []
                    for val in re.findall(config["pattern"], context_window):
                        # Filter out values that are followed by % or within parentheses like (18%)
                        if f"{val}%" in context_window or f"({val}%)" in context_window:
                            continue
                        value_matches.append(val)
                    
                    if value_matches:
                        # Usually the first number after the keyword is the value
                        value = value_matches[0]
                        # Basic confidence logic: proximity of keyword to value
                        dist = context_window.find(value)
                        confidence = 1.0 - (dist / 60.0)
                        
                        if confidence > highest_confidence:
                            best_match = self._normalize_currency(value)
                            highest_confidence = confidence
            
            results[field] = best_match if best_match is not None else 0.0
            
        return results

    def finalize_results(self, results):
        """Adds business logic validation (e.g., Total = Net + Tax + Fee - Discount)."""
        # This is a simplified validation to show approach
        total = results.get("total_premium", 0.0)
        net = results.get("net_premium", 0.0)
        tax = results.get("tax_amount", 0.0)
        
        if total == 0 and net > 0:
            # If total is missing but net/tax exist, we can infer it
            results["total_premium"] = net + tax
            
        return results

def run_test():
    """Simple test block to verify parser relevancy."""
    test_document = """
    POLICY SCHEDULE - MOTOR INSURANCE
    Policy Number: ABC-12345-DEF
    Period of Insurance: 01/01/2024 to 31/12/2024
    
    PREMIUM DETAILS:
    ----------------
    Net Premium: 15,000.00
    GST (18%): 2,700.00
    NCB Discount: 1,500.00
    Policy Fee: 500.00
    
    Total Amount Due: 16,700.00
    
    COVERAGE DETAILS:
    -----------------
    Third Party Limit: 500,000.00
    Compulsory Deductible: 2,500.00
    """
    
    parser = InsuranceFinancialParser()
    extracted_data = parser.parse_text(test_document)
    validated_data = parser.finalize_results(extracted_data)
    
    print("--- Extracted Financial Fields ---")
    print(json.dumps(validated_data, indent=4))
    
    # Simple validation for the test output
    if validated_data["total_premium"] == 16700.0:
        print("\n[SUCCESS] Parser correctly extracted the Total Premium.")
    else:
        print("\n[FAILURE] Parser missed the Total Premium.")

if __name__ == "__main__":
    run_test()
