# Claim Processing Service

FastAPI + LangGraph implementation for automated claim PDF processing.

## Objective
Build a service with `POST /api/process` that accepts:
- `claim_id` (string)
- `file` (PDF)

The service must:
1. Classify pages into document types.
2. Route only relevant pages to extraction agents.
3. Aggregate extracted data into a final JSON response.

## Implemented Workflow

Exact LangGraph flow:

`START -> Segregator Agent -> [ID Agent, Discharge Summary Agent, Itemized Bill Agent] -> Aggregator -> END`

## What Is Implemented

### 1) Segregator Agent
Classifies each page into one of 9 document types:
- `claim_forms`
- `cheque_or_bank_details`
- `identity_document`
- `itemized_bill`
- `discharge_summary`
- `prescription`
- `investigation_report`
- `cash_receipt`
- `other`

This project uses a local classifier (heuristic text rules), so no paid APIs are required.

### 2) ID Agent
Processes only pages routed as `identity_document`.
Extracts:
- patient name
- DOB
- policy number
- member ID
- ID number
- insurance provider

### 3) Discharge Summary Agent
Processes only pages routed as `discharge_summary`.
Extracts:
- diagnosis
- admit date
- discharge date
- physician details

### 4) Itemized Bill Agent
Processes only pages routed as `itemized_bill`.
Extracts:
- line items
- quantity / unit price / amount
- total bill amount

### 5) Aggregator Agent
Combines outputs from all agents and returns final structured JSON.

## Tech Stack
- FastAPI
- LangGraph
- PyMuPDF (`pymupdf`) for PDF text extraction
- pdfplumber for table extraction
- spaCy for local NLP extraction

## API

### `POST /api/process`
Form-data:
- `claim_id`: string
- `file`: PDF

Response:
- `claim_id`
- `document_classification`
- `identity_extraction`
- `discharge_summary_extraction`
- `itemized_bill_extraction`

### `GET /`
Interactive UI to upload PDF, enter claim ID, and view JSON result.

### `GET /health`
Health check endpoint.

## Project Structure
```text
claim_processing_service/
  claim_processing_service/
    agents/
      segregator.py
      id_agent.py
      discharge_agent.py
      itemized_bill_agent.py
      aggregator.py
    utils/
      pdf_utils.py
      nlp_utils.py
    graph.py
    main.py
    state.py
  sample_pdfs/
  requirements.txt
```

## How To Run Locally
```bash
cd claim_processing_service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn claim_processing_service.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:
- `http://localhost:8000/` 
- `http://localhost:8000/docs` 

## Test Via cURL
```bash
curl -X POST "http://localhost:8000/api/process" ^
  -F "claim_id=CLM-1001" ^
  -F "file=@sample_pdfs/sample_claim_form_cms1500.pdf;type=application/pdf"
```

## Sample PDFs
 sample files are included in `sample_pdfs/` for testing:
- `sample_claim_form_cms1500.pdf`
- `sample_discharge_summary_template.pdf`
- `sample_itemized_bill.pdf`
- `sample_identity_form_i9.pdf`
- `sample_bank_direct_deposit_form.pdf`

## Example Response 
```json
{
  "claim_id": "CLM-1001",
  "document_classification": [
    {
      "page_number": 1,
      "document_type": "claim_forms",
      "confidence": 0.7,
      "reason": "local heuristic classifier"
    }
  ],
  "identity_extraction": {
    "source_pages": [],
    "identity": {
      "patient_name": null,
      "dob": null,
      "policy_number": null,
      "member_id": null,
      "id_number": null,
      "insurance_provider": null
    }
  },
  "discharge_summary_extraction": {
    "source_pages": [],
    "medical": {
      "diagnosis": null,
      "admit_date": null,
      "discharge_date": null,
      "physician": null
    }
  },
  "itemized_bill_extraction": {
    "source_pages": [],
    "itemized_lines": [],
    "total_amount": 0,
    "currency": "INR"
  }
}

