import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def preprocess_text(text):
    """Clean and standardize text for better matching"""
    # Convert to lowercase and remove extra whitespace
    text = ' '.join(text.lower().split())
    # Remove special characters but keep hyphens and numbers
    text = re.sub(r'[^a-z0-9\s\-\.]', '', text)
    return text

def has_payroll_numeric_patterns(text):
    """Check for numeric patterns common in payroll documents"""
    # Look for dollar amounts with optional thousands separator
    has_dollar_amounts = bool(re.search(r'\d{1,3}(?:,\d{3})*\.?\d{2}', text))

    # Look for date patterns (MM/DD/YYYY or similar)
    has_dates = bool(re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text))

    # Look for hour-related numbers (like 40.00 or 80.00)
    has_hours = bool(re.search(r'(?:hours?|hrs?).*?(?:worked|total).*?(?:40|80|37\.5|35)', text, re.IGNORECASE))

    # Look for YTD or year-to-date indicators
    has_ytd = bool(re.search(r'ytd|year.*?to.*?date|y-t-d', text, re.IGNORECASE))

    return (has_dollar_amounts and has_dates) or (has_dollar_amounts and (has_hours or has_ytd))

def has_w2_numeric_patterns(text):
    """Check for numeric patterns common in W2s"""
    # Look for dollar amounts with optional thousands separator
    has_dollar_amounts = bool(re.search(r'\d{1,3}(?:,\d{3})*\.\d{2}', text))

    # Look for SSN-like patterns (###-##-#### or last 4 digits)
    has_ssn = bool(re.search(r'\d{3}-?\d{2}-?\d{4}|\d{4}', text))

    # Look for EIN pattern (##-#######)
    has_ein = bool(re.search(r'\d{2}-\d{7}', text))

    # Look for box references
    has_box_numbers = bool(re.search(r'box\s*[1-9]|box\s*1[0-9]', text))

    # Return true if we see dollar amounts AND (SSN or EIN or box numbers)
    return has_dollar_amounts and (has_ssn or has_ein or has_box_numbers)

# Modifying the classification thresholds and patterns for better accuracy
def classify_document(text):
    """Classify document based on content analysis"""
    text = preprocess_text(text)

    # Define keyword patterns for each document type with primary and secondary keywords
    w2_primary = ['w-2', 'w2', 'wage and tax statement', 'wages and tax statement']
    w2_secondary = [
        'social security wages', 'medicare wages', 'federal income tax withheld',
        'employer identification number', 'ein', 'employee social security number',
        'wages tips other compensation', 'state income tax', 'local income tax',
        'medicare tax withheld', 'allocated tips', 'dependent care benefits',
        'box 1', 'box 2', 'box 3', 'box 4', 'box 5'
    ]

    w9_primary = ['w-9', 'w9', 'request for taxpayer identification number']
    w9_secondary = [
        'taxpayer identification number and certification',
        'backup withholding', 'exempt payee code',
        'fatca reporting', 'employer identification number'
    ]

    paystub_primary = [
        'pay stub', 'paystub', 'pay statement', 'earnings statement',
        'pay period', 'payroll', 'period ending', 'pay date'
    ]
    paystub_secondary = [
        'gross pay', 'net pay', 'year to date', 'ytd', 'deductions',
        'federal withholding', 'hours worked', 'regular hours',
        'earnings', 'rate', 'total gross', 'total net',
        'federal tax', 'state tax', 'medicare', 'social security'
    ]

    bank_statement_primary = [
        'account statement', 'banking statement', 'bank of', 
        'checking account', 'savings account'
    ]
    bank_statement_secondary = [
        'balance', 'withdrawal', 'deposit', 'transaction',
        'beginning balance', 'ending balance', 'available balance',
        'account number', 'routing number'
    ]

    def calculate_weighted_score(primary_patterns, secondary_patterns, text):
        """Calculate weighted score with primary keywords worth more"""
        primary_matches = sum(1 for p in primary_patterns if p in text)
        secondary_matches = sum(1 for p in secondary_patterns if p in text)

        # For paystubs, check for numeric patterns
        is_paystub = 'pay stub' in primary_patterns or 'paystub' in primary_patterns
        if is_paystub and has_payroll_numeric_patterns(text):
            if secondary_matches >= 2:  # If we see enough payroll-specific patterns
                primary_matches = max(1, primary_matches)  # Ensure at least one primary match
                secondary_matches += 2  # Boost secondary matches

        # For W2s, we'll be more lenient with primary matches if we see strong numeric indicators
        is_w2 = 'w-2' in primary_patterns or 'w2' in primary_patterns
        if is_w2:
            if has_w2_numeric_patterns(text):  # If we find strong W2 numeric patterns
                primary_matches = max(1, primary_matches)  # Ensure at least one primary match
                secondary_matches += 3  # Boost secondary matches significantly
            elif secondary_matches >= 2:  # If we see enough W2-specific secondary patterns
                primary_matches = max(1, primary_matches)  # Assume at least one primary match

        if primary_matches == 0:  # For other documents, still require primary match
            return 0, 0

        total_patterns = len(primary_patterns) + len(secondary_patterns)
        weighted_score = (primary_matches * 2 + secondary_matches) / (len(primary_patterns) * 2 + len(secondary_patterns)) * 100

        total_matches = primary_matches + secondary_matches

        return total_matches, weighted_score

    # Calculate scores with weighted primary/secondary keywords
    scores = {
        'W2': calculate_weighted_score(w2_primary, w2_secondary, text),
        'W9': calculate_weighted_score(w9_primary, w9_secondary, text),
        'Paystub': calculate_weighted_score(paystub_primary, paystub_secondary, text),
        'Bank Statement': calculate_weighted_score(bank_statement_primary, bank_statement_secondary, text),
    }

    # Find document type with highest confidence
    max_confidence = 0
    doc_type = 'Unknown'

    for doc_name, (matches, confidence) in scores.items():
        if confidence > max_confidence:
            max_confidence = confidence
            doc_type = doc_name

    # Adjusted confidence thresholds based on document type
    min_confidence = {
        'W2': 15,  # Lower threshold for W2s due to OCR challenges
        'W9': 40,  # Higher threshold for W9s
        'Paystub': 20,  # Lower threshold for paystubs due to varying formats
        'Bank Statement': 30  # Higher threshold for bank statements
    }.get(doc_type, 25)

    return doc_type if max_confidence >= min_confidence else 'Unknown'