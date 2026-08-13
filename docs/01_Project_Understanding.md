# Healthcare Claims Analytics Dashboard - Project Understanding

## 1) Product Goal
Build a consumer-facing Healthcare Claims Analytics Dashboard using Python + Streamlit that helps a member:
- Upload EOB and claims data
- Understand what happened in their claims
- Analyze healthcare spending patterns
- Get plain-English explanation of medical billing terms and claim outcomes
- Compare costs against CMS public benchmark values

This should feel like a healthcare financial assistant for members, not a generic data table app.

## 2) Primary Users
- Healthcare members/patients (non-technical)
- Secondary user: analytics demo reviewer/interviewer

## 3) Core Functional Scope
The app will have 5 tabs:

### Tab 1: Upload EOB / Claim Data
Two upload modes:
1. Upload EOB as PDF/JPEG
2. Upload claim dataset in Excel format

Expected behavior:
- Accept multiple EOB files
- Parse key fields from EOB documents when possible
- Load Excel claims + CMS reference data
- Show ingestion status and validation messages

### Tab 2: Claims Overview
Purpose:
- Member-facing summary of uploaded claims
- Show top-level claim metrics and detailed claim list

Expected UI outcomes:
- Total provider charges
- Total allowed amount
- Total insurance paid
- Total patient responsibility
- Claim status mix
- Claim detail table with healthcare labels (not only raw column names)

### Tab 3: Healthcare Spending Analysis
Purpose:
- Visualize member spend and insurer spend trends

Required analysis views:
- Category-wise spending
- Provider-wise spending
- Month-wise spending

### Tab 4: EOB Explainer
Purpose:
- Explain a selected claim in plain English for non-insurance users

Expected behavior:
- Translate terms (allowed amount, deductible, copay, coinsurance, patient responsibility)
- Explain how member responsibility was calculated
- Give a simple summary paragraph for selected claim/service

### Tab 5: Cost Benchmark
Purpose:
- Compare member claim costs vs CMS public benchmark data by service/geography proxy

Expected behavior:
- Service selection by HCPCS
- Show member provider charge, allowed amount, insurance paid
- Show CMS averages (submitted charge, allowed, payment)
- Show above/below benchmark indication and percent gap
- Include strong disclaimer that CMS public data is reference-level and not a legal bill adjudication benchmark

## 4) Source Data Understanding from Provided Samples

### 4.1 Sample EOB Documents
Provided samples represent synthetic EOB-like claim summaries, including:
- Office visit example (claim CLM-1001)
- Emergency visit example (claim CLM-1006)
- Vision/ophthalmology multi-line claim example

Important semantics present in samples:
- Provider charge vs allowed amount vs insurance paid vs member owes
- Cost-share components: deductible, copay, coinsurance
- Statement that EOB is not a bill
- Synthetic/demo nature of records

### 4.2 Excel Data Workbook
Workbook contains these sheets:
- Member_Info
- Claims
- CMS_Reference_Data
- EOB_Field_Guide
- README

Claims table fields:
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

CMS reference table fields:
- hcpcs_code
- cms_service_description
- place_of_service
- avg_submitted_charge
- avg_medicare_allowed_amount
- avg_medicare_payment
- benchmark_type
- source_url

## 5) UX / Language Expectations
The interface should:
- Use plain healthcare-friendly terminology
- Include helper text/tooltips for billing terms
- Avoid internal-only insurer jargon where possible
- Show meaningful visuals and interpretation text, not only raw charts

## 6) Disclaimer Requirements (Global)
Every tab should clearly display disclaimers that:
- Data shown may be synthetic/sample data for learning/demo
- CMS data used is public reference data and may be averaged/provider-level
- This project is for educational/learning purposes
- The app is not affiliated with, endorsed by, or representing any organization
- App outputs are informational and not medical, legal, or billing advice

## 7) Non-Functional Expectations
- Clean, responsive Streamlit UI
- Robust data validation and error handling
- Consistent currency formatting
- Explainability-first design for non-technical members
- Modular code to support extension and testing

## 8) What I Will Build After Your Approval
- Full Streamlit app with 5 tabs
- Data ingestion + validation pipeline
- EOB parser (PDF/JPEG text extraction pattern and rule-based field extraction)
- Claims metrics and visual analytics
- Plain-English EOB explainer logic
- CMS benchmark comparison module
- Global and tab-level disclaimers
- Reusable utilities and optional sample config constants
