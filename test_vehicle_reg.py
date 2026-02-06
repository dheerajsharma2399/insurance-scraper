"""
Test Vehicle Registration Pattern
==================================
Quick test to verify the vehicle registration pattern handles both formats.
"""

from insurance_parser import FinancialPatternMatcher

def test_vehicle_registration_patterns():
    """Test vehicle registration extraction with different formats"""
    
    print("=" * 70)
    print("VEHICLE REGISTRATION PATTERN TEST")
    print("=" * 70)
    
    # Test cases with different formats
    test_cases = [
        "Vehicle Registration No: UP 14 DX 9941",
        "Registration Number: UP14DX9941",
        "Reg No: MH-12-AB-1234",
        "Vehicle No: MH12AB1234",
        "Registration: DL 01 CA 1234",
        "Reg: KA-05-MN-5678",
        "Vehicle: TN09BX7890",
        "Multiple vehicles: UP 14 DX 9941 and MH12AB1234 in same text",
    ]
    
    matcher = FinancialPatternMatcher()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. Test: {test_text}")
        results = matcher.extract_vehicle_registration(test_text)
        
        if results:
            for reg_num, context in results:
                print(f"   ✓ Found: {reg_num}")
                print(f"   Context: {context[:60]}...")
        else:
            print("   ✗ No registration found")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    test_vehicle_registration_patterns()
