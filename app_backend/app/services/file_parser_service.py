import PyPDF2
import docx
import io
import hashlib

def parse_pdf(file_content: bytes) -> str:
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() or ""
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        # Depending on strictness, could raise an error here
    return text

def parse_docx(file_content: bytes) -> str:
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error parsing DOCX: {e}")
    return text

def calculate_sha256_hash(file_content: bytes) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()
