# Claim Processing Service (FastAPI + LangGraph)


## Features
- `POST /api/process` accepts `claim_id` and PDF file.
- LangGraph pipeline:
  - `START -> Segregator -> [ID Agent, Discharge Summary Agent, Itemized Bill Agent] -> Aggregator -> END`
- Page classification into 9 required document types.
- Extraction agents process only routed pages.
- No paid APIs required (fully local processing).

## Tech
- FastAPI
- LangGraph
- PyMuPDF (`pymupdf`) for page text extraction
- pdfplumber for table extraction
- spaCy for local NLP extraction

## Structure
```text
claim_processing_service/
  claim_processing_service/
    agents/
    utils/
    graph.py
    main.py
    state.py
  requirements.txt
```

## Run
```bash
cd claim_processing_service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional, better NER
uvicorn claim_processing_service.main:app --host 0.0.0.0 --port 8000 --reload
```

## Test
```bash
curl -X POST "http://localhost:8000/api/process" ^
  -F "claim_id=CLM-1001" ^
  -F "file=@sample_pdfs/sample_claim_form_cms1500.pdf;type=application/pdf"
```

## Public Sample PDFs (Non-Confidential)
Placed in `sample_pdfs/`:
- `sample_claim_form_cms1500.pdf`
- `sample_discharge_summary_template.pdf`
- `sample_itemized_bill.pdf`
- `sample_identity_form_i9.pdf`
- `sample_bank_direct_deposit_form.pdf`

Source URLs:
- `https://www.astellaspharmasupportsolutions.com/content/dam/apss/hcp/north-america/us/en/docs/Sample_CMS_1500_Claim_Form.pdf`
- `https://www.uthsc.edu/pediatrics/clerkship/documents/discharge-summary-template.pdf`
- `https://info.chministries.org/hubfs/Website-Documents/sample-itemized-bill.pdf`
- `https://www.uscis.gov/sites/default/files/document/forms/i-9.pdf`
- `https://www.integrativestaffing.com/wp-content/uploads/2015/02/integrative-staffing-group-direct-deposit.pdf`

## Output
JSON containing:
- `document_classification`
- `identity_extraction`
- `discharge_summary_extraction`
- `itemized_bill_extraction`
