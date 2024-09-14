from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import os
from datetime import datetime
import io

import logging
import json
import zipfile
import re

from typing import Optional
from pydantic import BaseModel
import requests

import PyPDF2
from groq import Groq
from textwrap import wrap


app = FastAPI()

# Define the model for receiving a PDF URL
class PDFLink(BaseModel):
    url: Optional[str] = None

# Define allowed origins
allowed_origins = [
    "https://llama-creator-git-llama-creator-dev-alharkan7s-projects.vercel.app",
    "https://llama-creator.vercel.app",
    "https://8vysdc-3000.csb.app",# Replace with your actual frontend URL
    "https://simple-api-test-nine.vercel.app",
    "https://llama-creator-git-dev-alharkan7s-projects.vercel.app",
]

app.add_middleware(
   CORSMiddleware,
   allow_origins=allowed_origins,  # Allows specific origins
   allow_credentials=True,
   allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
   allow_headers=["*"],  # Allows all headers
)

@app.post("/upload-pdf/")
async def upload_pdf(
    pdf_file: Optional[UploadFile] = File(None), 
    pdf_url: Optional[str] = Form(None)
):
    # Check if either a file or a URL was provided
    if not pdf_file and not pdf_url:
        return JSONResponse({"message": "No PDF link or file was provided."}, status_code=400)

    # Handle file upload
    if pdf_file:
        if pdf_file.content_type != "application/pdf":
            return JSONResponse(status_code=400, content={"message": "Only PDF files are allowed."})

        try:
            # Read the uploaded PDF file into memory
            pdf_file_content = await pdf_file.read()
            extracted_text = extract_text_from_pdf_adobe(pdf_file_content)
            cleaned_text = cleanup_text(extracted_text)
            processed_text = process_text(cleaned_text)
            improved_text = improve_text(processed_text)
            json_text = strip_non_json(improved_text)

            return json.loads(json_text)

        except Exception as e:
            logging.exception(f"Error processing the PDF file: {e}")  # Enhanced logging
            return JSONResponse(status_code=500, content={"message": "Failed to extract text from the PDF.", "error": str(e)})

    # Handle PDF URL processing
    if pdf_url:
        # return JSONResponse({"message": "You provided a PDF link.", "pdf_url": pdf_url})

        try:
            # Read the uploaded PDF file into memory
            extracted_text = extract_text_from_pdf_url(pdf_url)
            cleaned_text = cleanup_text(extracted_text)
            processed_text = process_text(cleaned_text)
            improved_text = improve_text(processed_text)
            json_text = strip_non_json(improved_text)

            return json.loads(json_text)

        except Exception as e:
            logging.exception(f"Error processing the PDF file: {e}")  # Enhanced logging
            return JSONResponse(status_code=500, content={"message": "Failed to extract text from the PDF.", "error": str(e)})

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

def extract_text_from_pdf_adobe(pdf_file_content: bytes) -> str:

    input_stream = io.BytesIO(pdf_file_content)

    from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
    from adobe.pdfservices.operation.pdf_services import PDFServices
    from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
    from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
    from adobe.pdfservices.operation.io.stream_asset import StreamAsset

    from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
    from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
    from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult

    credentials = ServicePrincipalCredentials(
        client_id=os.getenv('PDF_SERVICES_CLIENT_ID'),
        client_secret=os.getenv('PDF_SERVICES_CLIENT_SECRET'))

    # Creates a PDF Services instance
    pdf_services = PDFServices(credentials=credentials)
    # Creates an asset(s) from source file(s) and upload
    input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)
    # Initialize the logger
    logging.basicConfig(level=logging.INFO)
    # Create parameters for the job
    export_pdf_params = ExportPDFParams(target_format=ExportPDFTargetFormat.DOCX)
    # Creates a new job instance
    export_pdf_job = ExportPDFJob(input_asset=input_asset, export_pdf_params=export_pdf_params)
    # Submit the job and gets the job result
    location = pdf_services.submit(export_pdf_job)
    pdf_services_response = pdf_services.get_job_result(location, ExportPDFResult)
    # Get content from the resulting asset(s)
    result_asset: CloudAsset = pdf_services_response.get_result().get_asset()
    stream_asset: StreamAsset = pdf_services.get_content(result_asset)

    input_stream_adobe = stream_asset.get_input_stream()
    # Instead of writing to disk, use in-memory buffer
    output_stream = io.BytesIO(input_stream_adobe)
    # Write the stream content to the in-memory file
    output_stream.write(stream_asset.get_input_stream())
    # Reset stream position to the beginning
    output_stream.seek(0)

    from docx import Document

    # Load the .docx content using `python-docx`
    try:
        doc = Document(output_stream)
        # Extract text from the .docx file
        doc_text = "\n".join([para.text for para in doc.paragraphs])
        #print(doc_text)  # Or use doc_text as needed
        return doc_text
    except Exception as e:
        logging.exception(f'Error while extracting text from PDF: {e}')
        raise Exception("Error extracting text from PDF")

def extract_text_from_pdf_url(pdf_url: str) -> str:
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()

        if 'application/pdf' not in response.headers.get('Content-Type', ''):
            raise ValueError("URL does not point to a valid PDF file.")

        return extract_text_from_pdf(response.content)

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download PDF from URL: {pdf_url} - {e}")
        raise HTTPException(status_code=400, detail="Error downloading the PDF from the URL.")
    except ValueError as e:
        logging.error(f"Invalid PDF URL: {pdf_url} - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Failed to extract text from the PDF URL: {pdf_url} - {e}")
        raise HTTPException(status_code=500, detail="Error extracting text from PDF URL.")

def cleanup_text(text):
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Split into paragraphs (assuming paragraphs are separated by double newlines)
    paragraphs = text.split('\n\n')
    
    # Process each paragraph
    processed_paragraphs = []
    for para in paragraphs:
        # Remove leading/trailing whitespace
        para = para.strip()
        
        # Rejoin hyphenated words
        para = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', para)
        
        # Add proper line breaks (e.g., after periods, question marks, exclamation marks)
        para = re.sub(r'([.!?])\s+', r'\1\n', para)
        
        processed_paragraphs.append(para)
    
    # Join paragraphs with double newlines
    cleanup_text = '\n\n'.join(processed_paragraphs)
    
    return cleanup_text

def process_text(cleaned_text: str) -> str:
    client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    )

    def process_chunk(chunk: str) -> dict:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Analyze the following scientific paper and create a series of engaging, easy-to-understand text chunks for a layman audience on social media. Return the output ONLY as a JSON object with the following structure:

                    {{
                        "intro": "string",
                        "question": "string",
                        "researcher": "string",
                        "method": "string",
                        "findings": "string",
                        "implications": "string",
                        "closing": "string"
                    }}

                    Guidelines:
                    - Each field should contain engaging short content suitable for social media cards (like TikTok).
                    - Use simple language for a non-scientific audience.
                    - Do not use markdown, code blocks, or special characters.
                    - Make the summary coherent from "intro to "closing", resembling a well-structured narrative or storytelling format.
                    - "intro": Summarize the most interesting finding or surprising fact to grab attention. For example, "Did you know that the study found that the average person spends 10 hours a week on social media?"
                    - "question": Summarize the main research question simply and relatably. For example, "The researcher(s) question on what are the effects of social media on mental health?"  
                    - "researcher": Briefly introduce the scientist(s) or their institution. For example, "This study was conducted by researchers at the University of California, Los Angeles."
                    - "method": Explain the study's method without technical jargon. For example, "This study used a sample of 1,000 participants and was conducted over a period of 12 months."
                    - "findings": Summarize key results, highlighting their significance. For example, "Researcher(s) found that the average person spends 10 hours a week on social media."
                    - "implications": Explain the potential impact on people, society, or future research. For example, "The study can help scientists for understanding the impact of social media on mental health."
                    - "closing": End with a question or call to action to encourage engagement. For example, "What are your thoughts on the study? Do you think it's important to understand the impact of social media on mental health?"

                    Scientific paper text:
                    {chunk}

                    Remember: Respond ONLY with the JSON object. No introductory text, no explanations outside the JSON structure.               
                    """
                }
            ],
            temperature=1,
            max_tokens=8000,
            top_p=1,
            stream=True,
            stop=None,
        )

        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content or ""

        return response_text

    # Split the text into smaller chunks
    chunks = wrap(cleaned_text, width=40000)  # Adjust chunk size based on token limits
    results = []

    for chunk in chunks:
        result = process_chunk(chunk)
        results.append(result)

    # Combine results into a single JSON object (this will depend on your exact needs)
    combined_result = combine_results(results)
    
    return json.dumps(combined_result)

def combine_results(results: list) -> str:
    combined_result = {
        "intro": "",
        "question": "",
        "researcher": "",
        "method": "",
        "findings": "",
        "implications": "",
        "closing": ""
    }

    # Iterate over each result and combine them
    for result in results:
        result_json = json.loads(result)  # Convert JSON string to Python dictionary
        
        # Combine fields; here we're just concatenating text from each chunk
        combined_result["intro"] += result_json.get("intro", "") + " "
        combined_result["question"] += result_json.get("question", "") + " "
        combined_result["researcher"] += result_json.get("researcher", "") + " "
        combined_result["method"] += result_json.get("method", "") + " "
        combined_result["findings"] += result_json.get("findings", "") + " "
        combined_result["implications"] += result_json.get("implications", "") + " "
        combined_result["closing"] += result_json.get("closing", "") + " "
    
    # Optionally, trim or clean up the combined fields
    combined_result = {key: value.strip() for key, value in combined_result.items()}
    
    return combined_result

def improve_text(dict_text):
    client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    )

    completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    You are given a dictionary that contains a summary of a science paper for social media publication in the following format:
                    {{
                        "intro": "string",
                        "question": "string",
                        "researcher": "string",
                        "method": "string",
                        "findings": "string",
                        "implications": "string",
                        "closing": "string"
                    }}

                    Your task is to rewrite and improve each section of this summary to ensure that when read sequentially from "intro" to "closing," the information flows smoothly and coherently. The goal is to make the summary engaging and easy to understand, resembling a well-structured narrative or storytelling format. Avoid redundancies, and ensure that each section naturally leads to the next.
                    
                    Here is the dictionary:
                    {dict_text}
                    
                    Please return only the improved dictionary with the sections rephrased to provide a seamless reading experience, with no additional explanation or text outside of it.

                    
                    """
                    }
            ],
            temperature=1,
            max_tokens=8000,
            top_p=1,
            stream=True,
            stop=None,
        )

    improved_text = ""
    for chunk in completion:
        improved_text += chunk.choices[0].delta.content or ""

    return improved_text


def strip_non_json(text):
    # Find the first occurrence of '{'
    start = text.find('{')
    # Find the last occurrence of '}'
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        # Extract the potential JSON content
        json_text = text[start:end+1]
        
        # Remove any leading/trailing whitespace
        json_text = json_text.strip()
        
        # Attempt to parse the JSON
        try:
            json_obj = json.loads(json_text)
            return json.dumps(json_obj, indent=2)  # Return formatted JSON string
        except json.JSONDecodeError:
            # If parsing fails, try to clean up the text further
            # Remove any non-JSON characters (keeping only {}, [], :, ",, and whitespace)
            cleaned_text = re.sub(r'[^\{\}\[\]:,".\s\w]', '', json_text)
            try:
                json_obj = json.loads(cleaned_text)
                return json.dumps(json_obj, indent=2)  # Return formatted JSON string
            except json.JSONDecodeError:
                return "Error: Unable to extract valid JSON from the response."
    else:
        return "Error: No JSON-like structure found in the response."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Command to run
# uvicorn main:app --reload
