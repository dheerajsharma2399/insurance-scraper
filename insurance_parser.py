import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import pdfplumber
from pathlib import Path


@dataclass
class ExtractedField:
    value: Any
    confidence: float
    page: int
    context: str = ""
    coordinates: Optional[Tuple[float, float]] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ExtractionResult:
    document_metadata: Dict[str, Any]
    fields: Dict[str, ExtractedField]
    tables_extracted: List[Dict[str, Any]]
    warnings: List[str]
    
    def to_dict(self):
        return {
            'document_metadata': self.document_metadata,
            'fields': {k: v.to_dict() for k, v in self.fields.items()},
            'tables_extracted': self.tables_extracted,
            'warnings': self.warnings
        }
    
    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent, default=str)


class PatternMatcher:
    """Extract financial data using regex patterns"""
    
    CURRENCY_PATTERNS = [
        r'₹\s*(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)',
        r'Rs\.?\s*(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)',
        r'INR\s*(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)',
        r'₹\s*(\d+(?:\.\d{1,2})?)',
        r'Rs\.?\s*(\d+(?:\.\d{1,2})?)',
        r'\b(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)\s*(?:/-|only)',
    ]
    
    DATE_PATTERNS = [
        r'(\d{2}[-/]\d{2}[-/]\d{4})',
        r'(\d{2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{4})',
        r'(\d{4}[-/]\d{2}[-/]\d{2})',
        r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
    ]
    
    POLICY_PERIOD = r'(\d{2}[-\s][A-Z]{3}[-\s]\d{4})\s+[Tt]o\s+(\d{2}[-\s][A-Z]{3}[-\s]\d{4})'
    
    POLICY_NUMBERS = [
        r'(?:Policy|Certificate)\s*(?:No\.?|Number|#)\s*:?\s*([A-Z0-9/-]{6,25})',
        r'(?:Previous\s+)?Policy\s+No\.?\s*:?\s*(\d{10,20})',
        r'\b([A-Z]{2,4}[-/]\d{6,15})\b',
    ]
    
    VEHICLE_REG = [r'\b([A-Z]{2}[-\s]?\d{1,2}[-\s]?[A-Z]{1,2}[-\s]?\d{4})\b']
    
    IDV = [
        r'(?:IDV|Insured Declared Value|Vehicle Value)\s*:?\s*₹?\s*(\d{1,3}(?:,\d{3})+)',
        r'EX[-\s]?SHOWROOM\s+PRICE\s*:?\s*₹?\s*(\d{1,3}(?:,\d{3})+)',
    ]
    
    @staticmethod
    def _extract_with_context(text, patterns, value_parser=None):
        results, seen = [], set()
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    value = match.group(1).strip()
                    if value_parser:
                        value = value_parser(value)
                    
                    start = max(0, match.start() - 60)
                    end = min(len(text), match.end() + 60)
                    context = text[start:end].strip()
                    
                    key = (value, match.start())
                    if key not in seen:
                        results.append((value, context))
                        seen.add(key)
                except (ValueError, IndexError):
                    continue
        return results
    
    @classmethod
    def extract_currency(cls, text):
        def parse(v):
            val = float(v.replace(',', ''))
            return val if val >= 1 else None
        return [(v, c) for v, c in cls._extract_with_context(text, cls.CURRENCY_PATTERNS, parse) if v]
    
    @classmethod
    def extract_dates(cls, text):
        return cls._extract_with_context(text, cls.DATE_PATTERNS)
    
    @classmethod
    def extract_policy_numbers(cls, text):
        return cls._extract_with_context(text, cls.POLICY_NUMBERS)
    
    @classmethod
    def extract_percentages(cls, text):
        return cls._extract_with_context(text, [r'(\d{1,3}(?:\.\d{1,2})?)\s*%'], float)
    
    @classmethod
    def extract_vehicle_registration(cls, text):
        return cls._extract_with_context(text, cls.VEHICLE_REG)
    
    @classmethod
    def extract_idv(cls, text):
        def parse(v):
            return float(v.replace(',', ''))
        return cls._extract_with_context(text, cls.IDV, parse)
    
    @classmethod
    def extract_policy_period(cls, text):
        match = re.search(cls.POLICY_PERIOD, text, re.IGNORECASE)
        if match:
            start, end = match.group(1).strip(), match.group(2).strip()
            ctx_start = max(0, match.start() - 40)
            ctx_end = min(len(text), match.end() + 40)
            return (start, end, text[ctx_start:ctx_end].strip())
        return None


class ContextMatcher:
    """Match values to fields using context keywords"""
    
    KEYWORDS = {
        'policy_number': ['policy number', 'policy no', 'certificate number', 'policy id'],
        'issue_date': ['issue date', 'date of issue', 'policy issue', 'issued on'],
        'effective_date': ['effective date', 'start date', 'from date', 'valid from'],
        'expiry_date': ['expiry date', 'maturity date', 'end date', 'valid till', 'expire'],
        'annual_premium': ['annual premium', 'yearly premium', 'premium per annum'],
        'monthly_premium': ['monthly premium', 'premium per month', 'per month'],
        'total_premium': ['total premium', 'gross premium', 'premium payable', 'amount payable'],
        'sum_insured': ['sum insured', 'sum assured', 'coverage', 'cover amount', 'face value'],
        'deductible': ['deductible', 'own damage', 'compulsory deductible', 'voluntary deductible'],
        'gst_amount': ['gst amount', 'igst', 'cgst', 'sgst', 'service tax', 'tax amount'],
        'discount': ['discount', 'rebate', 'deduction'],
        'ncb_discount': ['ncb', 'no claim bonus', 'no claim discount'],
        'cash_value': ['cash value', 'surrender value', 'maturity benefit'],
        'bonus': ['bonus', 'reversionary bonus', 'terminal bonus'],
        'idv': ['idv', 'insured declared value', 'vehicle value', 'market value'],
        'vehicle_registration': ['registration no', 'reg no', 'vehicle no', 'registration number'],
        'own_damage_premium': ['own damage premium', 'od premium', 'net own damage'],
        'third_party_premium': ['third party', 'liability premium', 'tp premium', 'net liability'],
    }
    
    @classmethod
    def match_field(cls, context, value):
        context_lower = context.lower()
        best_match, best_score = None, 0.0
        
        for field, keywords in cls.KEYWORDS.items():
            for keyword in keywords:
                if keyword in context_lower:
                    pos = context_lower.find(keyword)
                    proximity = max(0, 1 - (abs(pos - len(context)//2) / len(context)))
                    specificity = min(1.0, len(keyword) / 25)
                    score = proximity * 0.6 + specificity * 0.4
                    
                    if score > best_score:
                        best_score = score
                        best_match = field
        
        return best_match, best_score


class Validator:
    """Validate extracted values"""
    
    @staticmethod
    def validate_currency(value, field_name):
        if value < 0:
            return False, "Negative value"
        
        ranges = {
            'premium': (100, 100000000),
            'sum_insured': (1000, 10000000000),
            'coverage': (1000, 10000000000),
            'idv': (1000, 10000000000),
            'deductible': (0, 100000),
        }
        
        for key, (min_val, max_val) in ranges.items():
            if key in field_name and not (min_val <= value <= max_val):
                return False, f"Value {value} outside range"
        
        return True, ""
    
    @staticmethod
    def validate_date(date_str):
        patterns = [
            r'\d{2}[-/]\d{2}[-/]\d{4}',
            r'\d{2}[-\s]\w+[-\s]\d{4}',
            r'\d{4}[-/]\d{2}[-/]\d{2}',
            r'\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4}'
        ]
        return (True, "") if any(re.match(p, date_str, re.I) for p in patterns) else (False, "Invalid format")
    
    @staticmethod
    def validate_percentage(value):
        return (True, "") if 0 <= value <= 100 else (False, f"Value {value} outside 0-100")


class InsuranceDocumentParser:
    """Parse insurance PDFs and extract financial fields"""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.context_matcher = ContextMatcher()
        self.validator = Validator()
    
    def parse_pdf(self, pdf_path):
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        fields, tables, warnings = {}, [], []
        metadata = {
            'filename': path.name,
            'extraction_timestamp': datetime.now().isoformat(),
            'pages': 0,
            'document_type': 'unknown'
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata['pages'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    
                    # Extract tables
                    for table in page.extract_tables():
                        if table:
                            table_info = self._process_table(table, page_num)
                            if table_info:
                                tables.append(table_info)
                                table_fields = self._extract_from_table(table_info, page_num)
                                for fname, fdata in table_fields.items():
                                    if fname not in fields or fdata.confidence > fields[fname].confidence:
                                        fields[fname] = fdata
                    
                    # Extract from text
                    page_fields = self._extract_from_text(text, page_num)
                    for fname, fdata in page_fields.items():
                        if fname not in fields:
                            fields[fname] = fdata
                        elif fdata.confidence > fields[fname].confidence:
                            warnings.append(f"Duplicate '{fname}' - keeping page {fdata.page} (higher confidence)")
                            fields[fname] = fdata
                
                metadata['document_type'] = self._classify_document(fields)
        
        except Exception as e:
            warnings.append(f"Error: {str(e)}")
        
        return ExtractionResult(metadata, fields, tables, warnings)
    
    def _extract_from_text(self, text, page_num):
        fields = {}
        
        # Policy period
        period = self.pattern_matcher.extract_policy_period(text)
        if period:
            start, end, ctx = period
            fields['effective_date'] = ExtractedField(start, 0.92, page_num, ctx[:150])
            fields['expiry_date'] = ExtractedField(end, 0.92, page_num, ctx[:150])
        
        # Policy numbers
        for num, ctx in self.pattern_matcher.extract_policy_numbers(text):
            fname, score = self.context_matcher.match_field(ctx, num)
            if fname == 'policy_number' or not fname:
                fields['policy_number'] = ExtractedField(num, 0.85 + score * 0.15, page_num, ctx[:150])
                break
        
        # Dates
        for date, ctx in self.pattern_matcher.extract_dates(text):
            fname, score = self.context_matcher.match_field(ctx, date)
            if fname and fname.endswith('_date') and fname not in fields:
                valid, _ = self.validator.validate_date(date)
                conf = score * (0.95 if valid else 0.5)
                if conf > 0.4:
                    fields[fname] = ExtractedField(date, conf, page_num, ctx[:150])
        
        # Currency
        for value, ctx in self.pattern_matcher.extract_currency(text):
            fname, score = self.context_matcher.match_field(ctx, value)
            if fname and score > 0.35:
                valid, _ = self.validator.validate_currency(value, fname)
                if 'gst' in fname and value < 50:
                    continue
                conf = min(1.0, 0.4 + score * 0.5 + (0.1 if valid else 0))
                if conf > 0.5 and (fname not in fields or conf > fields[fname].confidence):
                    fields[fname] = ExtractedField(value, conf, page_num, ctx[:150])
        
        # Percentages
        for value, ctx in self.pattern_matcher.extract_percentages(text):
            fname, score = self.context_matcher.match_field(ctx, value)
            if fname and score > 0.45:
                valid, _ = self.validator.validate_percentage(value)
                conf = score * (0.9 if valid else 0.5)
                if conf > 0.5 and (fname not in fields or conf > fields[fname].confidence):
                    fields[fname] = ExtractedField(value, conf, page_num, ctx[:150])
        
        # Vehicle registration
        for reg, ctx in self.pattern_matcher.extract_vehicle_registration(text):
            fname, score = self.context_matcher.match_field(ctx, reg)
            if fname == 'vehicle_registration' or score > 0.3:
                fields['vehicle_registration'] = ExtractedField(reg, 0.8 + score * 0.2, page_num, ctx[:150])
                break
        
        # IDV
        for value, ctx in self.pattern_matcher.extract_idv(text):
            if value > 10000:
                fields['idv'] = ExtractedField(value, 0.88, page_num, ctx[:150])
                break
        
        return fields
    
    def _extract_from_table(self, table_info, page_num):
        fields = {}
        if table_info['table_type'] != 'premium_breakdown':
            return fields
        
        for row in table_info['rows']:
            if not row:
                continue
            
            row_text = ' '.join([str(c) if c else '' for c in row])
            row_lower = row_text.lower()
            
            # Total premium
            if any(k in row_lower for k in ['gross premium paid', 'total premium paid', 'premium paid']):
                nums = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', row_text)
                if nums:
                    try:
                        val = float(nums[-1].replace(',', ''))
                        if val > 500:
                            fields['total_premium'] = ExtractedField(val, 0.93, page_num, f"From table: {row_text[:100]}")
                    except ValueError:
                        pass
            
            # Net premium
            elif 'net premium' in row_lower or 'total premium' in row_lower:
                if 'total_premium' not in fields:
                    nums = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', row_text)
                    if nums:
                        try:
                            val = float(nums[-1].replace(',', ''))
                            if val > 500:
                                fields['total_premium'] = ExtractedField(val, 0.88, page_num, f"From table: {row_text[:100]}")
                        except ValueError:
                            pass
            
            # GST
            if 'igst' in row_lower or ('gst' in row_lower and '(' in row_text):
                nums = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', row_text)
                if nums:
                    try:
                        vals = [float(n.replace(',', '')) for n in nums]
                        val = max(vals)
                        if val > 50:
                            fields['gst_amount'] = ExtractedField(val, 0.90, page_num, f"From table: {row_text[:100]}")
                    except ValueError:
                        pass
            
            # NCB
            if 'no claim bonus' in row_lower or ('ncb' in row_lower and '(' in row_text):
                nums = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', row_text)
                if nums:
                    try:
                        val = float(nums[-1].replace(',', ''))
                        if val >= 0:
                            fields['ncb_discount'] = ExtractedField(val, 0.87, page_num, f"From table: {row_text[:100]}")
                    except ValueError:
                        pass
            
            # OD Premium
            if 'net own damage' in row_lower or 'own damage premium' in row_lower:
                nums = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', row_text)
                if nums:
                    try:
                        val = float(nums[-1].replace(',', ''))
                        if val > 100:
                            fields['own_damage_premium'] = ExtractedField(val, 0.89, page_num, f"From table: {row_text[:100]}")
                    except ValueError:
                        pass
            
            # TP Premium
            if 'net liability' in row_lower or 'liability premium' in row_lower:
                nums = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', row_text)
                if nums:
                    try:
                        val = float(nums[-1].replace(',', ''))
                        if val > 100:
                            fields['third_party_premium'] = ExtractedField(val, 0.89, page_num, f"From table: {row_text[:100]}")
                    except ValueError:
                        pass
        
        return fields
    
    def _process_table(self, table, page_num):
        if not table or len(table) < 2:
            return None
        
        headers = [str(c).lower().strip() if c else "" for c in table[0]]
        keywords = ['premium', 'amount', 'coverage', 'sum', 'total', 'benefit', 'gst', 'tax']
        
        if not any(k in ' '.join(headers) for k in keywords):
            table_text = ' '.join([' '.join([str(c) if c else '' for c in r]) for r in table])
            if not any(k in table_text.lower() for k in keywords):
                return None
        
        table_data = {
            'page': page_num,
            'headers': table[0],
            'rows': table[1:],
            'table_type': 'financial_data'
        }
        
        header_text = ' '.join(headers).lower()
        if 'premium' in header_text:
            table_data['table_type'] = 'premium_breakdown'
        elif 'coverage' in header_text or 'benefit' in header_text:
            table_data['table_type'] = 'coverage_details'
        
        return table_data
    
    def _classify_document(self, fields):
        field_names = set(fields.keys())
        
        if any(f in field_names for f in ['vehicle_registration', 'idv', 'own_damage_premium']):
            return 'auto_insurance'
        elif any(f in field_names for f in ['sum_insured', 'cash_value', 'bonus']):
            return 'life_insurance'
        elif 'deductible' in field_names:
            return 'health_insurance'
        
        return 'unknown'


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python insurance_parser.py <pdf_file>")
        sys.exit(1)
    
    parser = InsuranceDocumentParser()
    result = parser.parse_pdf(sys.argv[1])
    
    print(f"\nExtracted {len(result.fields)} fields from {result.document_metadata['filename']}")
    print(f"Document type: {result.document_metadata['document_type']}")
    print(f"\nFields:")
    for name, field in sorted(result.fields.items()):
        print(f"  {name}: {field.value} (confidence: {field.confidence:.0%})")
    
    # Save to JSON
    output_file = Path(sys.argv[1]).stem + "_results.json"
    with open(output_file, 'w') as f:
        f.write(result.to_json())
    print(f"\nSaved results to {output_file}")
