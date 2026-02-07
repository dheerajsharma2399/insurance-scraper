# Document 1: Parsing Approach - Financial Field Extraction

## Overview
This document outlines the methodology used to extract critical financial fields from insurance documents. The approach prioritizes **precision over recall** to ensure that financial data, which is sensitive and critical for business logic, is extracted with high confidence.

## Logic: Section-Based Contextual Extraction

Instead of applying global regular expressions across the entire document (which often leads to false positives, e.g., identifying a document date as a dollar amount), I have implemented a **Section-Based Contextual Extraction** strategy.

### 1. Document Segmentation (Block Identification)
Insurance documents are structured into logical blocks (e.g., "Policyholder Information", "Premium Details", "Coverage Schedule"). 
- **Logic**: Identify keywords that signal the start and end of financial sections.
- **Why**: By narrowing the search area to a specific section, we significantly reduce the "noise" (like policy numbers or phone numbers) that often mimic currency formats.

### 2. Multi-Staged Keyword Matching
For each identified block, the parser uses a tiered keyword mapping system:
- **Primary Keywords**: Explicit terms like "Total Premium Payable", "Net Premium", "Taxes".
- **Synonym Mapping**: Handling variations such as "Total Amount Due", "Balance Payable", "Final Premium".
- **Why**: Insurers use inconsistent terminology. A synonym-aware approach ensures the parser handles multiple carriers without manual template configuration.

### 3. Proximity-Based Value Capture
Once a keyword is found, the parser doesn't just look for the "next number." It looks for numbers within a specific geometric or textual window (e.g., same line or 20 characters after).
- **Logic**: Look for currency symbols ($, ₹, £) or specific numeric formats (xx,xxx.xx).
- **Why**: This prevents capturing a line number or a date if the premium field is empty or formatted unusually.

### 4. Semantic Validation & Normalization
Any extracted value undergoes a validation pipeline:
- **Format Normalization**: Removing commas, currency symbols, and spaces to convert values to standard floats.
- **Sanity Checks**: Ensuring premiums aren't negative and totals equal the sum of their parts (if multiple components are found).

## Why This Approach over Others?

| Approach | Why I chose / Why I rejected |
| :--- | :--- |
| **Simple Regex** | **Rejected**: Too many false positives (e.g., "Page 1 of 2" capturing "2" as a deductible). |
| **Template-Based** | **Rejected**: Too fragile. If the insurer moves a field by 5 pixels, it breaks. |
| **LLM-Based** | **Considered**: Excellent for reasoning but often overkill and expensive for high-volume structured data. |
| **Section-Based Contextual (Selected)** | **Chosen**: Offers the best balance. It is as robust as LLMs for structured data but as fast and predictable as Regex. It survives layout shifts as long as the keyword remains near the value. |

## Important Financial Fields Extracted
I identified the following fields as high-priority for any insurance financial analysis:

1.  **Gross/Net Premium**: The core cost of the insurance product.
2.  **Taxes/Levies**: Statutory components (GST, IPT, etc.) that affect the final price.
3.  **Total Amount Due**: The actual outflow for the customer.
4.  **Deductibles/Excess**: Crucial for understanding the customer's risk share.
5.  **Coverage Limits**: The maximum financial liability of the insurer.
6.  **Discounts (e.g., NCB)**: Financial incentives applied to the base price.
7.  **Admin Fees**: Additional service charges that impact the total cost.

## Testing and Relevancy
The implementation includes a mock test suite that simulates real-world insurance document text. I have verified that the parser correctly distinguishes between similar-looking numbers (dates vs. premiums) using the context logic described above.
