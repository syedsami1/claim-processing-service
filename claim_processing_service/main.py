from __future__ import annotations
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from claim_processing_service.graph import build_claim_graph
from claim_processing_service.utils.pdf_utils import extract_page_texts

app = FastAPI(title="Claim Processing Pipeline", version="1.0.0")
_graph = build_claim_graph()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Claim Processing Pipeline</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
body {
    margin: 0;
    font-family: 'Inter', sans-serif;
    background: #f5f7fa;
    color: #333;
}
header {
    background: linear-gradient(90deg, #0ea5e9, #0284c7);
    color: #fff;
    padding: 20px 40px;
    text-align: left;
    font-weight: 700;
    font-size: 2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
main {
    display: flex;
    flex-direction: column;
    max-width: 1200px;
    margin: 40px auto;
    gap: 30px;
}
section {
    background: #fff;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
label {
    font-weight: 600;
    display: block;
    margin-bottom: 8px;
}
input[type=text], input[type=file] {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    font-size: 1rem;
}
button {
    background: #0ea5e9;
    color: #fff;
    padding: 14px 28px;
    border-radius: 10px;
    border: none;
    font-weight: 700;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-top: 10px;
}
button:hover {
    background: #0284c7;
    box-shadow: 0 0 15px rgba(2, 132, 199, 0.5);
}
.status {
    font-size: 1rem;
    min-height: 24px;
    margin-top: 10px;
}
.status.error { color: #dc2626; }
pre {
    background: #f0f4f8;
    padding: 20px;
    border-radius: 12px;
    font-size: 0.9rem;
    overflow-x: auto;
    max-height: 500px;
}
.footer {
    text-align: center;
    color: #64748b;
    font-size: 0.9rem;
    margin-top: 20px;
}
.footer a { color: #0284c7; text-decoration: none; }
.row {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}
.col { flex: 1; min-width: 220px; }
</style>
</head>
<body>
<header>Claim Processing Pipeline</header>
<main>
<section>
  <div class="row">
    <div class="col">
      <label for="claimId">Claim ID</label>
      <input id="claimId" type="text" value="CLM-1001">
    </div>
    <div class="col">
      <label for="pdfFile">Claim PDF</label>
      <input id="pdfFile" type="file" accept="application/pdf,.pdf">
    </div>
  </div>
  <button id="submitBtn">Process Claim</button>
  <div id="status" class="status"></div>
</section>
<section>
  <label>JSON Output:</label>
  <pre id="output">{\n  "message": "Upload a claim PDF and click Process Claim"\n}</pre>
</section>
<div class="footer">
  API endpoint: <code>POST /api/process</code> | <a href="/docs" target="_blank">Docs</a>
</div>
</main>
<script>
const claimIdEl = document.getElementById("claimId");
const pdfFileEl = document.getElementById("pdfFile");
const statusEl = document.getElementById("status");
const outputEl = document.getElementById("output");
const submitBtn = document.getElementById("submitBtn");

async function processClaim() {
  const claimId = claimIdEl.value.trim();
  const file = pdfFileEl.files[0];
  if (!claimId) { statusEl.textContent="Enter claim_id"; statusEl.className="status error"; return; }
  if (!file) { statusEl.textContent="Select a PDF file"; statusEl.className="status error"; return; }
  
  const form = new FormData();
  form.append("claim_id", claimId);
  form.append("file", file);

  submitBtn.disabled=true;
  statusEl.textContent="Processing...";
  statusEl.className="status";
  outputEl.textContent="{\\n  \\"message\\": \\"Waiting...\\n}";

  try {
    const res = await fetch("/api/process", { method:"POST", body: form });
    const data = await res.json();
    if(!res.ok){ statusEl.textContent="Failed"; statusEl.className="status error"; outputEl.textContent=JSON.stringify(data,null,2); return; }
    statusEl.textContent="Success"; statusEl.className="status";
    outputEl.textContent=JSON.stringify(data,null,2);
  } catch(err) {
    statusEl.textContent="Network/server error"; statusEl.className="status error";
    outputEl.textContent=JSON.stringify({error:String(err)},null,2);
  } finally { submitBtn.disabled=false; }
}

submitBtn.addEventListener("click", processClaim);
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=INDEX_HTML)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/process")
async def process_claim(claim_id: str = Form(...), file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf","application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")
    pdf_path = UPLOAD_DIR / f"{claim_id}_{file.filename}"
    content = await file.read()
    pdf_path.write_bytes(content)
    try:
        page_texts = extract_page_texts(str(pdf_path))
        initial_state = {"claim_id": claim_id, "filename": str(pdf_path), "page_texts": page_texts}
        result = _graph.invoke(initial_state)
        return JSONResponse(content=result.get("final_response", {}))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing failed: {exc}") from exc

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("claim_processing_service.main:app", host="0.0.0.0", port=port, reload=True)