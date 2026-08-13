# Healthcare Claims Analytics Dashboard

A Streamlit-based, consumer-facing healthcare claims analytics demo that helps members understand claims, spending patterns, EOB terminology, and CMS benchmark comparisons.

## Live App

https://healthcare-claims-analytics.streamlit.app/

## Features

- Tab 1: Upload EOB/Claim Data
  - Upload EOB files in PDF/JPEG/PNG
  - Upload claims workbook in Excel format
  - Parse EOB text and validate claims/CMS datasets

- Tab 2: Claims Overview
  - KPIs for provider charges, allowed amount, insurer paid, and patient responsibility
  - Claim-level table with filters

- Tab 3: Healthcare Spending Analysis
  - Category-wise, provider-wise, and month-wise spending charts
  - Choose metric view: provider charge, insurer paid, or patient responsibility

- Tab 4: EOB Explainer
  - Plain-English claim explanation
  - Cost-share breakdown and glossary

- Tab 5: Cost Benchmark
  - Compare selected claim/service against CMS public reference values
  - Benchmark signal: Above, Near, or Below benchmark

## Disclaimers

This project is for learning/demo purposes only.

- Data may be synthetic sample data.
- CMS values are public reference averages and not legal adjudication outputs.
- This app is not affiliated with, endorsed by, or representing any organization.
- Information is not medical, legal, or billing advice.

## Expected Excel Sheets

- Claims (required)
- Member_Info (optional)
- CMS_Reference_Data (optional; app falls back to built-in CMS reference data)

Claims required columns:
- claim_id, service_date, provider_name, hcpcs_code, service_description, service_category,
  provider_charge, allowed_amount, insurance_paid, deductible, copay, coinsurance,
  patient_responsibility, claim_status

CMS required columns:
- hcpcs_code, cms_service_description, place_of_service, avg_submitted_charge,
  avg_medicare_allowed_amount, avg_medicare_payment, benchmark_type, source_url

Note: Members do not need to upload CMS data. The benchmark tab can use internal CMS reference values.

## Run Locally

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run app.py
```

4. Open the local Streamlit URL in your browser.

## Notes on OCR

Image text extraction uses pytesseract. If OCR is needed and not working, install the Tesseract engine on your machine and ensure it is on PATH.
