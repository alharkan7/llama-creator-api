import io
import zipfile
import json
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_pdf_options import ExtractPDFOptions
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.execution_context import ExecutionContext
from adobe.pdfservices.operation.io.file_ref import FileRef
from adobe.pdfservices.operation.pdfops.extract_pdf_operation import ExtractPDFOperation

def extract_text_from_pdf(pdf_content: bytes) -> str:
    try:
        # Set up credentials (you'll need to set these as environment variables)
        credentials = ServicePrincipalCredentials.builder().build()

        # Create an ExecutionContext using credentials
        execution_context = ExecutionContext.create(credentials)

        # Create a new operation instance
        extract_pdf_operation = ExtractPDFOperation.create_new()

        # Set operation input from stream
        source = FileRef.create_from_stream(io.BytesIO(pdf_content), "application/pdf")
        extract_pdf_operation.set_input(source)

        # Build ExtractPDF options and set them into the operation
        extract_pdf_options = ExtractPDFOptions.builder().add_element_to_extract(ExtractElementType.TEXT).build()
        extract_pdf_operation.set_options(extract_pdf_options)

        # Execute the operation
        result = extract_pdf_operation.execute(execution_context)

        # Parse the result
        text_elements = []
        for content in result.get_contents():
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                for name in zf.namelist():
                    if name.endswith('.json'):
                        data = json.loads(zf.read(name))
                        for element in data['elements']:
                            if 'Text' in element:
                                text_elements.append(element['Text'])

        return '\n'.join(text_elements)

    except (ServiceApiException, ServiceUsageException, SdkException) as e:
        print(f'Exception encountered while executing operation: {e}')
        raise