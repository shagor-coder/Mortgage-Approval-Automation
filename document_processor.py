import PyPDF2
from PIL import Image
import pytesseract
# import io
import re

# TESSERACT_PATH = r"C:\Tesseract-TEMP\tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def clean_extracted_text(text):
    """Clean extracted text by removing extra whitespace and normalizing line breaks"""
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable() or char.isspace())
    # Print debug information
    return text.strip()

def process_document(file_path, mime_type):
    """Process document and extract text content"""
    if 'pdf' in mime_type.lower():
        return process_pdf(file_path)
    elif 'image' in mime_type.lower():
        return process_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {mime_type}")

def process_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n"

                # If no text was extracted, try extracting text from images in the PDF
                if not page_text.strip():
                   
                    try:
                        if '/XObject' in page['/Resources']:
                            xObject = page['/Resources']['/XObject'].get_object()
                            for obj in xObject:
                                if xObject[obj]['/Subtype'] == '/Image':
                                    image = Image.frombytes(
                                        'RGB',
                                        [xObject[obj]['/Width'], xObject[obj]['/Height']],
                                        xObject[obj].get_data()
                                    )
                                    image_text = pytesseract.image_to_string(image, config='--psm 3 --oem 3')
                                   
                                    text += image_text + "\n"
                    except Exception as e:
                        cleaned_text = clean_extracted_text(text)
                        return cleaned_text
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")

def process_image(file_path):
    """Extract text from image using OCR"""
    try:
        image = Image.open(file_path)
        # Convert image to RGB if it's not
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # Improve OCR accuracy with image preprocessing
        text = pytesseract.image_to_string(image, config='--psm 3 --oem 3')
        return clean_extracted_text(text)
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")