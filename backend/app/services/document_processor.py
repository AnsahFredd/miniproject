# services/document_processor.py
import fitz  # PyMuPDF
import docx
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            return ""
    
    @staticmethod
    def process_document(file_path: str) -> str:
        """Process document and extract text based on file extension."""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return DocumentProcessor.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return DocumentProcessor.extract_text_from_docx(file_path)
        elif extension == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                return ""
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return ""