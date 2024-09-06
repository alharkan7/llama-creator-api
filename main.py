from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(status_code=400, content={"message": "Only PDF files are allowed."})
    
    # Do something with the file if needed
    content = await file.read()

    # Return confirmation message
    return {"filename": file.filename, "message": "PDF file received successfully!"}

# Command to run
# uvicorn main:app --reload
