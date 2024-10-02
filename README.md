
# Llama Creator API

The Llama Creator API is a FastAPI backend service designed to process scientific papers in PDF format or via URLs. This API transforms the content of the papers into JSON format, generating flashcard content that includes essential information such as Overview, Research Question, Researcher and Institution, Research Method, Research Findings, Implications, and Engagement.

## Features

- Accepts PDF files or URLs of scientific papers for processing.
- Generates structured JSON output containing key components of research papers.
- Built with FastAPI for high performance and easy scalability.

## Technologies Used

- **FastAPI**: For building the backend API.
- **Python**: Programming language used for the API logic.
- **Pydantic**: For data validation and settings management.
- **PDF processing libraries**: To extract content from PDF files.

## Getting Started

To run this API locally, follow these steps:

**1. Clone the repository:**

```bash
git clone https://github.com/alharkan7/llama-creator-api.git
```

 -  Navigate to the project directory:
    
```bash
cd llama-creator-api 
```

 -  Create a virtual environment (optional but recommended):
    
```bash
python -m venv venv
```

**2.  Navigate to the project directory:**
    
```bash
cd llama-creator-api
```
    
**3.  Create a virtual environment (optional but recommended):**
    
```bash
python -m venv venv 
```

**4.  Activate the virtual environment:**
    
- On Windows:
        
```bash
venv\Scripts\activate` 
```
- On macOS and Linux:
        
```bash
source venv/bin/activate
```

**5.  Install the dependencies:**
    
```bash
pip install -r requirements.txt` 
```
**6.  Start the FastAPI server:**
    
```bash
 uvicorn main:app --reload` 
```

**7.  Open your browser** 

Visit `http://127.0.0.1:8000/docs` to access the API documentation and test the endpoints.

## Try the API in Action

To try this API in action, you can visit [llama-creator.vercel.app](https://llama-creator.vercel.app/) where this API is deployed on [Render](https://render.com/).
    

## API Endpoints

-   **POST /process**: Upload a PDF file or provide a URL to receive flashcard content in JSON format.

## Contributing

Contributions are welcome! If you have suggestions for improvements or features, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

-   FastAPI for building a fast and efficient API.
-   Pydantic for data validation and management.

## Happy processing!    
