from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import os
from datetime import datetime

import logging
import json
import zipfile

from adobe.pdfservices.operation.auth.credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdfops.extractpdf.extract_pdf_params import ExtractPDFParams, ExtractElementType
from adobe.pdfservices.operation.pdfops.extractpdf.extract_pdf_result import ExtractPDFResult
from adobe.pdfservices.operation.io.file_ref import FileRef
from adobe.pdfservices.operation.pdfservices_client import PDFServices
from adobe.pdfservices.exception.service_api_exception import ServiceApiException
from adobe.pdfservices.exception.sdk_exception import SdkException


app = FastAPI()

@app.post("/upload-pdf/")
aasync def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(status_code=400, content={"message": "Only PDF files are allowed."})

    try:
        # Save the uploaded PDF to disk
        pdf_file_path = f"/tmp/{file.filename}"
        with open(pdf_file_path, "wb") as f:
            f.write(await file.read())

        # Call Adobe PDF API to extract text
        extracted_text = extract_text_from_pdf(pdf_file_path)

        # Return extracted text in response
        return {"filename": file.filename, "extracted_text": extracted_text}

    except Exception as e:
        logging.exception(f"Error processing the PDF file: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to extract text from the PDF."})


def extract_text_from_pdf(pdf_file_path: str) -> str:
    try:
        # Create Adobe PDF Services credentials
        credentials = ServicePrincipalCredentials(
            client_id=os.getenv('PDF_SERVICES_CLIENT_ID'),
            client_secret=os.getenv('PDF_SERVICES_CLIENT_SECRET')
        )

        # Initialize the Adobe PDF Services client
        pdf_services = PDFServices(credentials=credentials)

        # Create input asset from the PDF file
        input_asset = pdf_services.upload(input_stream=open(pdf_file_path, 'rb').read(), mime_type='application/pdf')

        # Set up extract parameters to extract text
        extract_pdf_params = ExtractPDFParams(
            elements_to_extract=[ExtractElementType.TEXT],
        )

        # Create and submit the extraction job
        extract_pdf_job = pdf_services.submit_job(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
        pdf_services_response = pdf_services.get_job_result(extract_pdf_job)

        # Extract the resulting content
        result_asset = pdf_services_response.get_result().get_resource()
        stream_asset = pdf_services.get_content(result_asset)

        # Extract JSON content from the zip file response
        with zipfile.ZipFile(stream_asset.get_input_stream(), 'r') as archive:
            json_entry = archive.open('structuredData.json')
            json_data = json.loads(json_entry.read())

        # Extract and return text elements from the JSON data
        extracted_text = "\n".join([element['Text'] for element in json_data["elements"] if "Text" in element])

        return extracted_text

    except (ServiceApiException, SdkException) as e:
        logging.exception(f'Error while extracting text from PDF: {e}')
        raise Exception("Adobe PDF Services API error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
# Command to run
# uvicorn main:app --reload
