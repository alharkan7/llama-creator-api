from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import os
from datetime import datetime
import io

import logging
import json
import zipfile

import PyPDF2


app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(status_code=400, content={"message": "Only PDF files are allowed."})

    try:
        # Read the uploaded PDF file into memory
        pdf_file_content = await file.read()

        # Call Adobe PDF API to extract text
        extracted_text = extract_text_from_pdf(pdf_file_content)

        # Return extracted text in response
        return {"filename": file.filename, "extracted_text": extracted_text}

    except Exception as e:
        logging.exception(f"Error processing the PDF file: {e}")  # Enhanced logging
        return JSONResponse(status_code=500, content={"message": "Failed to extract text from the PDF.", "error": str(e)})  # Include error details

def extract_text_from_pdf(pdf_file_content: bytes) -> str:
    try:
        # Create a file-like object from the byte content
        input_stream = io.BytesIO(pdf_file_content)

        # Parse the PDF document
        pdf_reader = PyPDF2.PdfReader(input_stream)

        # Extract text from each page
        extracted_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()

        return extracted_text

    except Exception as e:
        logging.exception(f'Error while extracting text from PDF: {e}')
        raise Exception("Error extracting text from PDF")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Command to run
# uvicorn main:app --reload
