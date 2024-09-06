from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import os
from datetime import datetime

import logging
import json
import zipfile

from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType

from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult


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
        # Create Adobe PDF Services credentials
        credentials = ServicePrincipalCredentials(
            client_id=os.getenv('PDF_SERVICES_CLIENT_ID'),
            client_secret=os.getenv('PDF_SERVICES_CLIENT_SECRET')
        )

        # Initialize the Adobe PDF Services client
        pdf_services = PDFServices(credentials=credentials)

        # Create input asset from the PDF file content
        input_asset = pdf_services.upload(input_stream=pdf_file_content, mime_type='application/pdf')

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
