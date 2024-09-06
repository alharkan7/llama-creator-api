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

        # Call Adobe PDF API to extract text
        extracted_text = extract_text_from_pdf(pdf_file_content)

        processed_text = process_text(extracted_text)

        # Return extracted text in response
        return {"filename": file.filename, "processed_text": processed_text}
        # return {"filename": file.filename, "processed_text": extracted_text}

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

def process_text(extracted_text: str) -> str:
    client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    )

    # Replace multiple newlines with one newline to avoid broken paragraphs
    extracted_text = re.sub(r'\n+', '\n', extracted_text)
    
    # Remove spaces around newlines (from markdown-style bullets, etc.)
    extracted_text = re.sub(r' \n', '\n', extracted_text)
    extracted_text = re.sub(r'\n ', '\n', extracted_text)

    # Remove common markdown-like artifacts (like '*' or '•')
    extracted_text = re.sub(r'[*•]', '', extracted_text)

    # Remove double spaces and tabs
    extracted_text = re.sub(r'\t+', ' ', extracted_text)
    extracted_text = re.sub(r' +', ' ', extracted_text)

    # Handle word hyphenation at the end of lines (e.g., "exam-\nple" -> "example")
    extracted_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', extracted_text)

    # Remove any excessive newlines for readability (e.g., collapse multiple empty lines)
    extracted_text = re.sub(r'\n{2,}', '\n\n', extracted_text)

    # Strip leading and trailing whitespaces from the final text
    extracted_text = extracted_text.strip()

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "user",
                "content": f"""
                I have a scientific paper that has been extracted from a PDF using PyPDF2. It is a bit messy, so you must clean it up and make it readable.
                Then I want to turn it into a series of engaging, easy-to-understand text chunks for a layman audience on social media.
                Each chunk should be brief and suitable for being read on a card that people can swipe through, like on TikTok.
                
                Here's how I want you to break down the content:
                - Hook: Identify the most interesting finding or surprising fact from the paper and summarize it in a catchy, attention-grabbing way to draw people in.
                - Research Problem or Question: Summarize the main problem or research question the paper addresses. Keep it simple and relatable.
                - Researcher and Institution: Provide a short introduction to the scientist(s) who conducted the research, or mention the institution they are affiliated with.
                - Research Method: Briefly explain what the researchers did to conduct the study. Keep it straightforward and avoid technical jargon.
                - Findings: Summarize the key findings of the research in a way that highlights their significance.
                - Implications: Explain why these findings matter. What impact could they have on people's lives, society, or future research?
                - Engagement Bait: End with a question or a call to action to encourage audience engagement, such as commenting their thoughts, sharing the content, or asking questions.
                
                Make sure each chunk is concise and suitable for a non-scientific audience. Use simple language and keep each chunk to no more than two sentences.
                You must return all the text in readable format, no markdown, no code, no special characters.
                You MUST only return the output in JSON format with the following template:
                
                    "hook": "...",
                    "question": "...",
                    "researcher": "...",
                    "method": "...",
                    "findings": "...",
                    "implications": "...",
                    "closing": "..."
                                
                Here is the text of the scientific paper: {extracted_text}

                I repeat. Only return in JSON format, no intro like "Here is the output" or "Here is the answer" or anything like that.               
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
