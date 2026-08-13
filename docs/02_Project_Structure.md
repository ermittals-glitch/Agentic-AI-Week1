# Proposed Project Structure (Documentation-Only Stage)

This is the proposed implementation structure. No application code has been generated yet.

```text
Agentic AI Week 1/
├─ app.py
├─ requirements.txt
├─ README.md
├─ docs/
│  ├─ 01_Project_Understanding.md
│  ├─ 02_Project_Structure.md
│  └─ 03_Implementation_Plan.md
├─ assets/
│  ├─ logo/
│  └─ styles/
│     └─ custom.css
├─ data/
│  ├─ sample/
│  │  ├─ Healthcare_Claims_Analytics_Demo_Data.xlsx
│  │  ├─ Sample_EOB_Office_Visit.pdf
│  │  ├─ Sample_EOB_Emergency_Visit.pdf
│  │  └─ Sample_EOB_Vision_CMS_Data.pdf
│  └─ processed/
├─ src/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ ui/
│  │  ├─ __init__.py
│  │  ├─ tab_upload.py
│  │  ├─ tab_overview.py
│  │  ├─ tab_spending_analysis.py
│  │  ├─ tab_eob_explainer.py
│  │  └─ tab_cost_benchmark.py
│  ├─ data/
│  │  ├─ __init__.py
│  │  ├─ loaders.py
│  │  ├─ validators.py
│  │  ├─ transformers.py
│  │  └─ schema.py
│  ├─ parsers/
│  │  ├─ __init__.py
│  │  ├─ eob_pdf_parser.py
│  │  ├─ eob_image_parser.py
│  │  └─ extraction_rules.py
│  ├─ analytics/
│  │  ├─ __init__.py
│  │  ├─ kpis.py
│  │  ├─ spending.py
│  │  ├─ explainer.py
│  │  └─ benchmark.py
│  └─ utils/
│     ├─ __init__.py
│     ├─ formatters.py
│     └─ text_helpers.py
└─ tests/
   ├─ test_validators.py
   ├─ test_analytics.py
   └─ test_benchmark.py
```

## Folder Responsibility

- app.py
  - Streamlit entrypoint
  - Session state and top-level navigation

- src/ui
  - One module per tab for clean separation

- src/data
  - Input loading, schema normalization, and validation

- src/parsers
  - EOB parsing utilities for PDF/JPEG and rule-based extraction

- src/analytics
  - KPI, trend, explainer, and CMS comparison logic

- src/utils
  - Shared formatters and reusable helper functions

- docs
  - Design documentation and implementation notes

- tests
  - Unit tests for core data and analytics logic

## Required Data Contracts

### Claims Dataset Required Columns
- claim_id
- service_date
- provider_name
- hcpcs_code
- service_description
- service_category
- provider_charge
- allowed_amount
- insurance_paid
- deductible
- copay
- coinsurance
- patient_responsibility
- claim_status

### CMS Benchmark Dataset Required Columns
- hcpcs_code
- cms_service_description
- place_of_service
- avg_submitted_charge
- avg_medicare_allowed_amount
- avg_medicare_payment
- benchmark_type
- source_url

## Session State Plan
Expected Streamlit session keys:
- claims_df
- cms_df
- member_info
- parsed_eob_records
- data_quality_report
- selected_claim_id
- selected_hcpcs

## Dependency Plan
Primary packages planned:
- streamlit
- pandas
- plotly
- openpyxl
- pydantic
- python-dateutil
- Pillow
- pdfplumber (for PDF text extraction)
- pytesseract (optional OCR fallback for image/PDF scan cases)
