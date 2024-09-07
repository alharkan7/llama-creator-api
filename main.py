from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import os
from datetime import datetime
import io

import logging
import json
import zipfile
import re

import PyPDF2
from groq import Groq



app = FastAPI()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(status_code=400, content={"message": "Only PDF files are allowed."})

    try:
        # Read the uploaded PDF file into memory
        pdf_file_content = await file.read()

        extracted_text = extract_text_from_pdf(pdf_file_content)

        cleaned_text = cleanup_text(extracted_text)

        processed_text = process_text(cleaned_text)

        json_text = strip_non_json(processed_text)

        # Return extracted text in response
        #return {"filename": file.filename, "processed_text": extracted_text}
        #return {"filename": file.filename, "processed_text": cleaned_text}
        #return {"filename": file.filename, "processed_text": processed_text}
        #return {"filename": file.filename, "processed_text": json_text}    
        

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

def process_text(cleaned_text: str) -> str:
    client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    )

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "user",
                "content": f"""
                Analyze the following scientific paper and create a series of engaging, easy-to-understand text chunks for a layman audience on social media. Return the output ONLY as a JSON object with the following structure:

                {{
                    "hook": "string",
                    "question": "string",
                    "researcher": "string",
                    "method": "string",
                    "findings": "string",
                    "implications": "string",
                    "closing": "string"
                }}

                Guidelines:
                - Each field should contain brief, concise content suitable for social media cards (like TikTok).
                - Use simple language for a non-scientific audience.
                - Limit each chunk to no more than two sentences.
                - Do not use markdown, code blocks, or special characters.
                - "hook": Summarize the most interesting finding or surprising fact to grab attention.
                - "question": Summarize the main research question simply and relatably.
                - "researcher": Briefly introduce the scientist(s) or their institution.
                - "method": Explain the study's method without technical jargon.
                - "findings": Summarize key results, highlighting their significance.
                - "implications": Explain the potential impact on people, society, or future research.
                - "closing": End with a question or call to action to encourage engagement.

                Scientific paper text:
                {cleaned_text}

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Command to run
# uvicorn main:app --reload
