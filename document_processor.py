from PIL import Image
import pytesseract
import io
import re
import fitz

# TESSERACT_PATH = r"D:\Python Apps\Mortgage Approval Automation\tesseract\tesseract.exe"
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
    """Extract text from all pages of a PDF, including scanned images using OCR."""
    full_text = ""  # Store extracted text from all pages

    try:
        # Open the PDF using PyMuPDF (better than PyPDF2)
        pdf_document = fitz.open(file_path)
        
        for page_num in range(len(pdf_document)):  # Loop through all pages
            page = pdf_document[page_num]

            
            # Extract selectable text
            page_text = page.get_text("text")

            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += page_text + "\n"

            # If no text was found, extract images and run OCR
            if not page_text.strip():
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]  # Get image reference
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Run OCR on the image using Tesseract
                    image_text = pytesseract.image_to_string(image, config='--psm 3 --oem 3')
                    
                    full_text += f"\n[Image {img_index + 1} OCR Result on Page {page_num + 1}]\n{image_text}\n"

    except Exception as e:
        return f"Error processing PDF: {str(e)}"
    return full_text.strip()  # Return cleaned extracted text from all pages

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