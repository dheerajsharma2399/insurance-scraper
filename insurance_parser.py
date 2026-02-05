"""
Insurance Document Financial Field Parser
==========================================

A hybrid pattern-based parser for extracting financial fields from insurance documents.
Supports mixed document types: Life, Health, Property/Auto insurance.

Author: [Your Name]
Date: February 2026
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import pdfplumber
from pathlib import Path


@dataclass
class ExtractedField:
    """Represents a single extracted financial field"""
    value: Any
    confidence: float
    page: int
    context: str = ""
    coordinates: Optional[Tuple[float, float]] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ExtractionResult:
    """Container for complete extraction results"""
    document_metadata: Dict[str, Any]
    fields: Dict[str, ExtractedField]
    tables_extracted: List[Dict[str, Any]]
    warnings: List[str]
    
    def to_dict(self):
        result = {
            'document_metadata': self.document_metadata,
            'fields': {k: v.to_dict() for k, v in self.fields.items()},
            'tables_extracted': self.tables_extracted,
            'warnings': self.warnings
        }
        return result
    
    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent, default=str)


class FinancialPatternMatcher:
    """Pattern matching engine for financial data"""
    
    # Currency patterns
    CURRENCY_PATTERNS = [
        r'₹\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # ₹1,00,000.00
        r'Rs\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Rs. 100000
        r'INR\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # INR 100000
        r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:/-|only)',  # 100000/- or only
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        r'(\d{2}[-/]\d{2}[-/]\d{4})',  # DD-MM-YYYY or DD/MM/YYYY
        r'(\d{2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',  # DD Mon YYYY
        r'(\d{4}[-/]\d{2}[-/]\d{2})',  # YYYY-MM-DD
    ]
    
    # Policy number patterns
    POLICY_NUMBER_PATTERNS = [
        r'Policy\s*(?:No\.?|Number|#)\s*:?\s*([A-Z0-9/-]{6,20})',
        r'\b([A-Z]{2,4}[-/]\d{6,12})\b',
    ]
    
    # Percentage patterns
    PERCENTAGE_PATTERNS = [
        r'(\d{1,3}(?:\.\d{1,2})?)\s*%',
    ]
    
    @staticmethod
    def extract_currency(text: str) -> List[Tuple[float, str]]:
        """Extract all currency values from text"""
        results = []
        for pattern in FinancialPatternMatcher.CURRENCY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str)
                    context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                    results.append((value, context))
                except ValueError:
                    continue
        return results
    
    @staticmethod
    def extract_dates(text: str) -> List[Tuple[str, str]]:
        """Extract all dates from text"""
        results = []
        for pattern in FinancialPatternMatcher.DATE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                results.append((date_str, context))
        return results
    
    @staticmethod
    def extract_policy_numbers(text: str) -> List[Tuple[str, str]]:
        """Extract policy numbers from text"""
        results = []
        for pattern in FinancialPatternMatcher.POLICY_NUMBER_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                policy_num = match.group(1)
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                results.append((policy_num, context))
        return results
    
    @staticmethod
    def extract_percentages(text: str) -> List[Tuple[float, str]]:
        """Extract percentage values from text"""
        results = []
        for pattern in FinancialPatternMatcher.PERCENTAGE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    value = float(match.group(1))
                    context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                    results.append((value, context))
                except ValueError:
                    continue
        return results


class ContextMatcher:
    """Match extracted values to specific fields using context keywords"""
    
    FIELD_KEYWORDS = {
        'policy_number': [
            'policy number', 'policy no', 'policy #', 'certificate number',
            'certificate no', 'policy id'
        ],
        'issue_date': [
            'issue date', 'date of issue', 'policy issue', 'issued on',
            'commencement date'
        ],
        'effective_date': [
            'effective date', 'start date', 'commence date', 'from date',
            'policy start', 'effective from'
        ],
        'expiry_date': [
            'expiry date', 'maturity date', 'end date', 'valid till',
            'policy expiry', 'expire', 'maturity'
        ],
        'annual_premium': [
            'annual premium', 'yearly premium', 'premium per annum',
            'total annual premium', 'annualized premium'
        ],
        'monthly_premium': [
            'monthly premium', 'premium per month', 'monthly installment',
            'per month'
        ],
        'total_premium': [
            'total premium', 'gross premium', 'premium payable',
            'total amount', 'amount payable'
        ],
        'sum_insured': [
            'sum insured', 'sum assured', 'coverage', 'cover amount',
            'insured amount', 'face value', 'death benefit', 'coverage limit'
        ],
        'deductible': [
            'deductible', 'own damage', 'copay', 'co-payment', 'co payment',
            'basic excess'
        ],
        'gst_amount': [
            'gst', 'service tax', 'tax amount', 'goods and services tax',
            'igst', 'cgst', 'sgst'
        ],
        'discount': [
            'discount', 'rebate', 'deduction', 'ncb', 'no claim bonus'
        ],
        'cash_value': [
            'cash value', 'surrender value', 'maturity benefit',
            'accumulated value'
        ],
        'bonus': [
            'bonus', 'reversionary bonus', 'terminal bonus', 'additional benefit'
        ],
    }
    
    @staticmethod
    def match_field(context: str, value: Any) -> Tuple[Optional[str], float]:
        """
        Match a value to a field based on surrounding context
        Returns: (field_name, confidence_score)
        """
        context_lower = context.lower()
        
        best_match = None
        best_score = 0.0
        
        for field_name, keywords in ContextMatcher.FIELD_KEYWORDS.items():
            for keyword in keywords:
                if keyword in context_lower:
                    # Calculate confidence based on keyword match quality
                    keyword_position = context_lower.find(keyword)
                    value_position = len(context) // 2  # Approximate value position
                    
                    # Closer keyword = higher confidence
                    distance = abs(keyword_position - value_position)
                    proximity_score = max(0, 1 - (distance / len(context)))
                    
                    # Longer keyword = more specific = higher confidence
                    specificity_score = len(keyword) / 30  # Normalized
                    
                    score = (proximity_score * 0.6 + specificity_score * 0.4)
                    
                    if score > best_score:
                        best_score = score
                        best_match = field_name
        
        return best_match, best_score


class FieldValidator:
    """Validate extracted field values"""
    
    @staticmethod
    def validate_currency(value: float, field_name: str) -> Tuple[bool, str]:
        """Validate currency values are within reasonable ranges"""
        if value < 0:
            return False, "Negative value not allowed"
        
        # Range validation based on field type
        if 'premium' in field_name:
            if value < 500 or value > 100000000:
                return False, f"Premium {value} outside reasonable range (₹500 - ₹1Cr)"
        elif 'sum_insured' in field_name or 'coverage' in field_name:
            if value < 10000 or value > 1000000000:
                return False, f"Coverage {value} outside reasonable range (₹10k - ₹100Cr)"
        
        return True, ""
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, str]:
        """Validate date format and reasonable range"""
        # Basic format check - actual date parsing would be more robust
        date_patterns = [
            r'\d{2}[-/]\d{2}[-/]\d{4}',
            r'\d{2}\s+\w+\s+\d{4}',
            r'\d{4}[-/]\d{2}[-/]\d{2}'
        ]
        
        if not any(re.match(pattern, date_str) for pattern in date_patterns):
            return False, "Invalid date format"
        
        return True, ""
    
    @staticmethod
    def validate_percentage(value: float) -> Tuple[bool, str]:
        """Validate percentage values"""
        if value < 0 or value > 100:
            return False, f"Percentage {value} outside valid range (0-100)"
        return True, ""


class InsuranceDocumentParser:
    """Main parser class for insurance documents"""
    
    def __init__(self):
        self.pattern_matcher = FinancialPatternMatcher()
        self.context_matcher = ContextMatcher()
        self.validator = FieldValidator()
        
    def parse_pdf(self, pdf_path: str) -> ExtractionResult:
        """
        Parse a PDF insurance document and extract financial fields
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractionResult object containing extracted fields and metadata
        """
        pdf_path_obj = Path(pdf_path)
        
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Initialize result containers
        extracted_fields = {}
        tables_extracted = []
        warnings = []
        
        # Document metadata
        metadata = {
            'filename': pdf_path_obj.name,
            'extraction_timestamp': datetime.now().isoformat(),
            'pages': 0,
            'document_type': 'unknown'
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata['pages'] = len(pdf.pages)
                
                # Process each page
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text() or ""
                    
                    # Process tables
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_info = self._process_table(table, page_num)
                            if table_info:
                                tables_extracted.append(table_info)
                    
                    # Extract fields from text
                    page_fields = self._extract_from_text(text, page_num)
                    
                    # Merge fields (keep highest confidence)
                    for field_name, field_data in page_fields.items():
                        if field_name not in extracted_fields:
                            extracted_fields[field_name] = field_data
                        elif field_data.confidence > extracted_fields[field_name].confidence:
                            warnings.append(
                                f"Duplicate field '{field_name}' found - "
                                f"keeping page {field_data.page} value (higher confidence)"
                            )
                            extracted_fields[field_name] = field_data
                
                # Classify document type based on extracted fields
                metadata['document_type'] = self._classify_document_type(extracted_fields)
                
        except Exception as e:
            warnings.append(f"Error processing PDF: {str(e)}")
        
        return ExtractionResult(
            document_metadata=metadata,
            fields=extracted_fields,
            tables_extracted=tables_extracted,
            warnings=warnings
        )
    
    def _extract_from_text(self, text: str, page_num: int) -> Dict[str, ExtractedField]:
        """Extract fields from page text"""
        fields = {}
        
        # Extract policy numbers
        policy_numbers = self.pattern_matcher.extract_policy_numbers(text)
        for policy_num, context in policy_numbers:
            field_name, context_score = self.context_matcher.match_field(context, policy_num)
            if field_name == 'policy_number' or not field_name:
                confidence = 0.8 + (context_score * 0.2)  # Base 0.8 for policy number match
                fields['policy_number'] = ExtractedField(
                    value=policy_num,
                    confidence=confidence,
                    page=page_num,
                    context=context.strip()
                )
                break  # Take first match
        
        # Extract dates
        dates = self.pattern_matcher.extract_dates(text)
        for date_str, context in dates:
            field_name, context_score = self.context_matcher.match_field(context, date_str)
            if field_name and field_name.endswith('_date'):
                is_valid, error_msg = self.validator.validate_date(date_str)
                confidence = context_score * (0.9 if is_valid else 0.5)
                
                if field_name not in fields or confidence > fields[field_name].confidence:
                    fields[field_name] = ExtractedField(
                        value=date_str,
                        confidence=confidence,
                        page=page_num,
                        context=context.strip()
                    )
        
        # Extract currency values
        currency_values = self.pattern_matcher.extract_currency(text)
        for value, context in currency_values:
            field_name, context_score = self.context_matcher.match_field(context, value)
            
            if field_name and context_score > 0.3:  # Minimum threshold
                is_valid, error_msg = self.validator.validate_currency(value, field_name)
                
                # Calculate final confidence
                pattern_score = 0.4
                validation_score = 0.1 if is_valid else 0.0
                confidence = min(1.0, pattern_score + context_score * 0.5 + validation_score)
                
                if field_name not in fields or confidence > fields[field_name].confidence:
                    fields[field_name] = ExtractedField(
                        value=value,
                        confidence=confidence,
                        page=page_num,
                        context=context.strip()
                    )
        
        # Extract percentages
        percentages = self.pattern_matcher.extract_percentages(text)
        for value, context in percentages:
            field_name, context_score = self.context_matcher.match_field(context, value)
            
            if field_name and context_score > 0.4:
                is_valid, error_msg = self.validator.validate_percentage(value)
                confidence = context_score * (0.9 if is_valid else 0.5)
                
                if field_name not in fields or confidence > fields[field_name].confidence:
                    fields[field_name] = ExtractedField(
                        value=value,
                        confidence=confidence,
                        page=page_num,
                        context=context.strip()
                    )
        
        return fields
    
    def _process_table(self, table: List[List[str]], page_num: int) -> Optional[Dict[str, Any]]:
        """Process a table and extract structured financial data"""
        if not table or len(table) < 2:
            return None
        
        # Assume first row is header
        headers = [str(cell).lower().strip() if cell else "" for cell in table[0]]
        
        # Check if this looks like a financial table
        financial_keywords = ['premium', 'amount', 'coverage', 'sum', 'total', 'benefit']
        if not any(keyword in ' '.join(headers) for keyword in financial_keywords):
            return None
        
        table_data = {
            'page': page_num,
            'headers': table[0],
            'rows': table[1:],
            'table_type': 'financial_data'
        }
        
        # Try to identify table type
        if 'premium' in ' '.join(headers):
            table_data['table_type'] = 'premium_breakdown'
        elif 'coverage' in ' '.join(headers) or 'benefit' in ' '.join(headers):
            table_data['table_type'] = 'coverage_details'
        
        return table_data
    
    def _classify_document_type(self, fields: Dict[str, ExtractedField]) -> str:
        """Classify insurance document type based on extracted fields"""
        field_names = set(fields.keys())
        
        life_indicators = {'cash_value', 'bonus', 'maturity_date', 'sum_assured'}
        health_indicators = {'deductible', 'copay', 'room_rent'}
        auto_indicators = {'idv', 'ncb', 'depreciation'}
        
        life_score = len(field_names & life_indicators)
        health_score = len(field_names & health_indicators)
        auto_score = len(field_names & auto_indicators)
        
        if life_score >= health_score and life_score >= auto_score and life_score > 0:
            return 'life_insurance'
        elif health_score >= auto_score and health_score > 0:
            return 'health_insurance'
        elif auto_score > 0:
            return 'auto_insurance'
        else:
            return 'general_insurance'


def main():
    """Example usage"""
    parser = InsuranceDocumentParser()
    
    # Example: Parse a PDF file
    pdf_path = "sample_insurance_document.pdf"
    
    try:
        result = parser.parse_pdf(pdf_path)
        
        # Print results
        print("=" * 70)
        print("EXTRACTION RESULTS")
        print("=" * 70)
        print(f"\nDocument: {result.document_metadata['filename']}")
        print(f"Pages: {result.document_metadata['pages']}")
        print(f"Document Type: {result.document_metadata['document_type']}")
        print(f"\nExtracted Fields ({len(result.fields)}):")
        print("-" * 70)
        
        for field_name, field_data in sorted(result.fields.items()):
            print(f"\n{field_name.upper().replace('_', ' ')}:")
            print(f"  Value: {field_data.value}")
            print(f"  Confidence: {field_data.confidence:.2f}")
            print(f"  Page: {field_data.page}")
            print(f"  Context: {field_data.context[:100]}...")
        
        if result.tables_extracted:
            print(f"\n\nTables Found: {len(result.tables_extracted)}")
            for i, table in enumerate(result.tables_extracted, 1):
                print(f"\n  Table {i} (Page {table['page']}): {table['table_type']}")
        
        if result.warnings:
            print("\n\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
        
        # Save to JSON
        output_path = pdf_path.replace('.pdf', '_extracted.json')
        with open(output_path, 'w') as f:
            f.write(result.to_json())
        print(f"\n\n✓ Results saved to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease provide a valid PDF file path.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
