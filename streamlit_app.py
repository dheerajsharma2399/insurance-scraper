"""
Insurance Document Parser - Streamlit Web Application
=====================================================

A simple web interface for uploading and parsing insurance documents.

Usage:
    streamlit run streamlit_app.py
"""

import streamlit as st
import json
from pathlib import Path
import tempfile
from datetime import datetime
import pandas as pd

from insurance_parser import InsuranceDocumentParser

# Page configuration
st.set_page_config(
    page_title="Insurance Document Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .field-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'parser' not in st.session_state:
    st.session_state.parser = InsuranceDocumentParser()
if 'results' not in st.session_state:
    st.session_state.results = None

# Header
st.markdown('<div class="main-header">📄 Insurance Document Parser</div>', unsafe_allow_html=True)
st.markdown("Extract financial fields from insurance policy documents (Life, Health, Auto)")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.info("""
    This tool extracts financial information from insurance documents including:
    
    - Policy numbers and dates
    - Premium amounts
    - Coverage details
    - Deductibles and bonuses
    - And more...
    """)
    
    st.header("⚙️ Settings")
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
        help="Only show fields with confidence above this threshold"
    )
    
    show_context = st.checkbox("Show Context", value=True, help="Display surrounding text for each field")
    show_low_confidence = st.checkbox("Show Low Confidence Fields", value=True, help="Include fields below threshold")

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Parse", "📊 Results", "📥 Export"])

with tab1:
    st.header("Upload Insurance Document")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload an insurance policy document in PDF format"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        parse_button = st.button("🔍 Parse Document", type="primary", disabled=uploaded_file is None)
    
    if parse_button and uploaded_file:
        with st.spinner("Parsing document... This may take a few seconds."):
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            try:
                # Parse the document
                result = st.session_state.parser.parse_pdf(tmp_path)
                st.session_state.results = result
                
                st.success(f"✅ Successfully parsed document! Extracted {len(result.fields)} fields.")
                
                # Show quick summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Fields Extracted", len(result.fields))
                with col2:
                    st.metric("Pages", result.document_metadata['pages'])
                with col3:
                    st.metric("Document Type", result.document_metadata['document_type'].replace('_', ' ').title())
                with col4:
                    avg_conf = sum(f.confidence for f in result.fields.values()) / len(result.fields) if result.fields else 0
                    st.metric("Avg Confidence", f"{avg_conf:.0%}")
                
                # Show warnings if any
                if result.warnings:
                    with st.expander("⚠️ Warnings", expanded=False):
                        for warning in result.warnings:
                            st.warning(warning)
                
            except Exception as e:
                st.error(f"❌ Error parsing document: {str(e)}")
            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)

with tab2:
    st.header("Extraction Results")
    
    if st.session_state.results is None:
        st.info("👆 Upload and parse a document to see results here")
    else:
        result = st.session_state.results
        
        # Filter fields by confidence
        filtered_fields = {
            name: field for name, field in result.fields.items()
            if show_low_confidence or field.confidence >= confidence_threshold
        }
        
        if not filtered_fields:
            st.warning(f"No fields found with confidence >= {confidence_threshold:.0%}. Try lowering the threshold.")
        else:
            # Display fields grouped by type
            st.subheader(f"Extracted Fields ({len(filtered_fields)})")
            
            # Group fields by category
            field_categories = {
                'Policy Information': ['policy_number', 'issue_date', 'effective_date', 'expiry_date'],
                'Premium Details': ['annual_premium', 'monthly_premium', 'total_premium', 'gst_amount', 'discount'],
                'Coverage': ['sum_insured', 'cash_value', 'bonus', 'deductible'],
                'Other': []
            }
            
            # Categorize fields
            categorized = {cat: {} for cat in field_categories}
            for field_name, field_data in sorted(filtered_fields.items()):
                placed = False
                for category, field_list in field_categories.items():
                    if category != 'Other' and field_name in field_list:
                        categorized[category][field_name] = field_data
                        placed = True
                        break
                if not placed:
                    categorized['Other'][field_name] = field_data
            
            # Display by category
            for category, fields in categorized.items():
                if fields:
                    with st.expander(f"📋 {category} ({len(fields)})", expanded=True):
                        for field_name, field_data in fields.items():
                            # Determine confidence color
                            if field_data.confidence >= 0.8:
                                conf_class = "confidence-high"
                                conf_emoji = "🟢"
                            elif field_data.confidence >= 0.6:
                                conf_class = "confidence-medium"
                                conf_emoji = "🟡"
                            else:
                                conf_class = "confidence-low"
                                conf_emoji = "🔴"
                            
                            # Display field
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{field_name.replace('_', ' ').title()}**")
                                st.markdown(f"Value: `{field_data.value}`")
                                if show_context and field_data.context:
                                    st.caption(f"Context: {field_data.context[:150]}...")
                            with col2:
                                st.markdown(f"{conf_emoji} <span class='{conf_class}'>{field_data.confidence:.0%}</span>", unsafe_allow_html=True)
                                st.caption(f"Page {field_data.page}")
                            
                            st.divider()
            
            # Display tables if any
            if result.tables_extracted:
                st.subheader(f"📊 Extracted Tables ({len(result.tables_extracted)})")
                for i, table in enumerate(result.tables_extracted, 1):
                    with st.expander(f"Table {i}: {table['table_type'].replace('_', ' ').title()} (Page {table['page']})", expanded=False):
                        # Convert to DataFrame
                        df = pd.DataFrame(table['rows'], columns=table['headers'])
                        st.dataframe(df, use_container_width=True)

with tab3:
    st.header("Export Results")
    
    if st.session_state.results is None:
        st.info("👆 Parse a document first to export results")
    else:
        result = st.session_state.results
        
        st.subheader("Download Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # JSON export
            json_data = result.to_json(indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"extraction_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # CSV export
            csv_data = []
            for field_name, field_data in result.fields.items():
                csv_data.append({
                    'Field': field_name,
                    'Value': field_data.value,
                    'Confidence': f"{field_data.confidence:.2%}",
                    'Page': field_data.page,
                    'Context': field_data.context[:100]
                })
            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)
            
            st.download_button(
                label="📊 Download CSV",
                data=csv_string,
                file_name=f"extraction_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col3:
            # Pretty text report
            report = f"""INSURANCE DOCUMENT EXTRACTION REPORT
{'=' * 70}

Document: {result.document_metadata['filename']}
Pages: {result.document_metadata['pages']}
Document Type: {result.document_metadata['document_type']}
Extraction Date: {result.document_metadata['extraction_timestamp']}

EXTRACTED FIELDS ({len(result.fields)})
{'=' * 70}

"""
            for field_name, field_data in sorted(result.fields.items()):
                report += f"""
{field_name.upper().replace('_', ' ')}:
  Value:      {field_data.value}
  Confidence: {field_data.confidence:.2%}
  Page:       {field_data.page}
  Context:    {field_data.context[:80]}...

"""
            
            if result.warnings:
                report += f"\nWARNINGS:\n{'=' * 70}\n"
                for warning in result.warnings:
                    report += f"⚠️  {warning}\n"
            
            st.download_button(
                label="📝 Download Report",
                data=report,
                file_name=f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        # Preview
        st.subheader("Preview")
        preview_format = st.radio("Select format to preview:", ["JSON", "Table", "Text Report"])
        
        if preview_format == "JSON":
            st.json(result.to_dict())
        elif preview_format == "Table":
            st.dataframe(df, use_container_width=True)
        else:
            st.text(report)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Insurance Document Parser v1.0 | Built with Streamlit | 
    <a href='#' style='color: #1f77b4;'>Documentation</a> | 
    <a href='#' style='color: #1f77b4;'>GitHub</a>
    </small>
</div>
""", unsafe_allow_html=True)
