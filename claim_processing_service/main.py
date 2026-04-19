from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from claim_processing_service.graph import build_claim_graph
from claim_processing_service.utils.pdf_utils import extract_page_texts

app = FastAPI(title="Claim Processing Pipeline", version="1.0.0")
_graph = build_claim_graph()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process_claim(claim_id: str = Form(...), file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    pdf_path = UPLOAD_DIR / f"{claim_id}_{file.filename}"
    content = await file.read()
    pdf_path.write_bytes(content)

    try:
        page_texts = extract_page_texts(str(pdf_path))
        initial_state = {
            "claim_id": claim_id,
            "filename": str(pdf_path),
            "page_texts": page_texts,
        }
        result = _graph.invoke(initial_state)
        return JSONResponse(content=result.get("final_response", {}))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("claim_processing_service.main:app", host="0.0.0.0", port=8000, reload=True)
