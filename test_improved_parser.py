"""
Test the improved insurance parser on the car policy document
"""

from insurance_parser import InsuranceDocumentParser
import json

def test_car_policy():
    """Test parser on car insurance policy"""
    parser = InsuranceDocumentParser()
    
    pdf_path = "sample_documents/car policy.pdf"
    
    print("=" * 80)
    print("TESTING IMPROVED INSURANCE PARSER")
    print("=" * 80)
    print(f"\nParsing: {pdf_path}\n")
    
    try:
        result = parser.parse_pdf(pdf_path)
        
        # Print metadata
        print("\n" + "=" * 80)
        print("DOCUMENT METADATA")
        print("=" * 80)
        for key, value in result.document_metadata.items():
            print(f"{key:25s}: {value}")
        
        # Print extracted fields
        print("\n" + "=" * 80)
        print(f"EXTRACTED FIELDS ({len(result.fields)} fields)")
        print("=" * 80)
        
        for field_name, field_data in sorted(result.fields.items()):
            print(f"\n{field_name.upper().replace('_', ' ')}:")
            print(f"  Value:      {field_data.value}")
            print(f"  Confidence: {field_data.confidence:.2%}")
            print(f"  Page:       {field_data.page}")
            print(f"  Context:    {field_data.context[:80]}...")
        
        # Print tables
        if result.tables_extracted:
            print("\n" + "=" * 80)
            print(f"TABLES EXTRACTED ({len(result.tables_extracted)} tables)")
            print("=" * 80)
            for i, table in enumerate(result.tables_extracted, 1):
                print(f"\nTable {i}:")
                print(f"  Type: {table['table_type']}")
                print(f"  Page: {table['page']}")
                print(f"  Rows: {len(table['rows'])}")
        
        # Print warnings
        if result.warnings:
            print("\n" + "=" * 80)
            print("WARNINGS")
            print("=" * 80)
            for warning in result.warnings:
                print(f"⚠️  {warning}")
        
        # Save results
        output_file = "test_results/car_policy_improved_results.json"
        with open(output_file, 'w') as f:
            f.write(result.to_json())
        
        print("\n" + "=" * 80)
        print(f"✓ Results saved to: {output_file}")
        print("=" * 80)
        
        # Print comparison summary
        print("\n" + "=" * 80)
        print("IMPROVEMENT SUMMARY")
        print("=" * 80)
        print(f"Fields extracted: {len(result.fields)}")
        print(f"Document type: {result.document_metadata['document_type']}")
        
        avg_conf = sum(f.confidence for f in result.fields.values()) / len(result.fields) if result.fields else 0
        print(f"Average confidence: {avg_conf:.2%}")
        
        high_conf = sum(1 for f in result.fields.values() if f.confidence >= 0.8)
        print(f"High confidence fields (≥80%): {high_conf}/{len(result.fields)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_car_policy()
