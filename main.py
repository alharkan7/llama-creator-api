from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pdf_processor import extract_text_from_pdf
from llm_generator import generate_content

app = FastAPI()

@app.post("/process_pdf")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    try:
        pdf_content = await file.read()
        paper_text = extract_text_from_pdf(pdf_content)
        content = generate_content(paper_text)
        return JSONResponse(content={"content": content})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)