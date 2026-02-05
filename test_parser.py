"""
Test Script for Insurance Document Parser
==========================================

This script demonstrates how to use the parser and includes test cases
for different scenarios.
"""

from insurance_parser import (
    InsuranceDocumentParser,
    FinancialPatternMatcher,
    ContextMatcher,
    FieldValidator
)


def test_pattern_matching():
    """Test the pattern matching functionality"""
    print("=" * 70)
    print("TEST 1: Pattern Matching")
    print("=" * 70)
    
    sample_text = """
    Policy Number: LI/2024/123456
    Annual Premium: ₹25,000.00
    Sum Insured: Rs. 10,00,000
    Policy Issue Date: 15/01/2024
    Maturity Date: 15th January 2044
    GST (18%): ₹4,500/-
    """
    
    matcher = FinancialPatternMatcher()
    
    print("\n1. Currency Values Found:")
    currencies = matcher.extract_currency(sample_text)
    for value, context in currencies:
        print(f"   ₹{value:,.2f} - Context: {context[:50]}...")
    
    print("\n2. Dates Found:")
    dates = matcher.extract_dates(sample_text)
    for date, context in dates:
        print(f"   {date} - Context: {context[:50]}...")
    
    print("\n3. Policy Numbers Found:")
    policies = matcher.extract_policy_numbers(sample_text)
    for policy, context in policies:
        print(f"   {policy} - Context: {context[:50]}...")
    
    print("\n4. Percentages Found:")
    percentages = matcher.extract_percentages(sample_text)
    for pct, context in percentages:
        print(f"   {pct}% - Context: {context[:50]}...")


def test_context_matching():
    """Test context-based field matching"""
    print("\n\n" + "=" * 70)
    print("TEST 2: Context Matching")
    print("=" * 70)
    
    context_matcher = ContextMatcher()
    
    test_cases = [
        ("Total Annual Premium: ₹25,000", 25000),
        ("Sum Insured: Rs. 10,00,000", 1000000),
        ("Policy Issue Date: 15/01/2024", "15/01/2024"),
        ("GST Amount (18%): ₹4,500", 4500),
        ("Deductible: ₹5,000 per claim", 5000),
    ]
    
    print("\nMatching fields based on context:")
    for context, value in test_cases:
        field_name, confidence = context_matcher.match_field(context, value)
        print(f"\n   Context: '{context}'")
        print(f"   → Field: {field_name or 'UNKNOWN'}")
        print(f"   → Confidence: {confidence:.2f}")


def test_validation():
    """Test field validation"""
    print("\n\n" + "=" * 70)
    print("TEST 3: Field Validation")
    print("=" * 70)
    
    validator = FieldValidator()
    
    print("\n1. Currency Validation:")
    test_values = [
        (25000, "annual_premium", True),
        (-1000, "monthly_premium", False),
        (150000000, "sum_insured", False),
        (500000, "sum_insured", True),
    ]
    
    for value, field, should_pass in test_values:
        is_valid, msg = validator.validate_currency(value, field)
        status = "✓" if is_valid == should_pass else "✗"
        print(f"   {status} {field}: ₹{value:,} - {msg if msg else 'Valid'}")
    
    print("\n2. Date Validation:")
    test_dates = [
        ("15/01/2024", True),
        ("15 Jan 2024", True),
        ("2024-01-15", True),
        ("invalid-date", False),
    ]
    
    for date_str, should_pass in test_dates:
        is_valid, msg = validator.validate_date(date_str)
        status = "✓" if is_valid == should_pass else "✗"
        print(f"   {status} {date_str} - {msg if msg else 'Valid'}")
    
    print("\n3. Percentage Validation:")
    test_percentages = [
        (18.0, True),
        (5.5, True),
        (-10, False),
        (150, False),
    ]
    
    for pct, should_pass in test_percentages:
        is_valid, msg = validator.validate_percentage(pct)
        status = "✓" if is_valid == should_pass else "✗"
        print(f"   {status} {pct}% - {msg if msg else 'Valid'}")


def test_full_parser_demo():
    """Demonstrate full parser with synthetic data"""
    print("\n\n" + "=" * 70)
    print("TEST 4: Full Parser Demo (Synthetic Data)")
    print("=" * 70)
    
    # Note: This would require an actual PDF file
    print("\nTo test with an actual PDF:")
    print("1. Place an insurance PDF in the current directory")
    print("2. Update the filename in insurance_parser.py's main() function")
    print("3. Run: python insurance_parser.py")
    print("\nThe parser will extract fields and save results to JSON.")


def generate_sample_document():
    """Generate information about creating a sample PDF for testing"""
    print("\n\n" + "=" * 70)
    print("CREATING SAMPLE TEST DOCUMENT")
    print("=" * 70)
    
    sample_content = """
    Sample Insurance Policy Document Content:
    
    ==========================================
    LIFE INSURANCE POLICY
    ==========================================
    
    Policy Details:
    ---------------
    Policy Number: LI/2024/789012
    Policy Holder: John Doe
    Date of Issue: 15 January 2024
    Policy Start Date: 01/02/2024
    Maturity Date: 01/02/2044
    
    Coverage Information:
    ---------------------
    Sum Assured: ₹50,00,000
    Death Benefit: ₹50,00,000
    Maturity Benefit: ₹75,00,000
    
    Premium Details:
    ----------------
    Annual Premium: ₹45,000.00
    Premium Payment Term: 20 years
    Policy Term: 20 years
    
    Premium Breakdown:
    ------------------
    Base Premium:          ₹38,135.00
    Rider Premiums:        ₹5,000.00
    Service Tax (18%):     ₹7,865.00
    --------------------------------
    Total Annual Premium:  ₹45,000.00
    
    Additional Benefits:
    --------------------
    Accidental Death Benefit: ₹10,00,000
    Critical Illness Cover: ₹5,00,000
    Premium Waiver Benefit: Included
    
    Surrender Value:
    ----------------
    After 3 years: 30% of premiums paid
    After 5 years: 50% of premiums paid
    
    Terms and Conditions Apply.
    """
    
    print(sample_content)
    print("\n\nYou can save this to a PDF using any PDF creation tool,")
    print("or create a similar document to test the parser.")


def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("INSURANCE DOCUMENT PARSER - TEST SUITE")
    print("*" * 70)
    
    test_pattern_matching()
    test_context_matching()
    test_validation()
    test_full_parser_demo()
    generate_sample_document()
    
    print("\n\n" + "=" * 70)
    print("TESTS COMPLETED")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Place a sample insurance PDF in the directory")
    print("3. Run the parser: python insurance_parser.py")
    print("4. Review the extracted JSON output")
    print("\n")


if __name__ == "__main__":
    main()
