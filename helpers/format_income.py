def extract_financial_data(results):
    """Extract only the financial data from classified documents."""
    financial_data = [doc['income_data'] for doc in results if 'income_data' in doc]
    return financial_data  # Returns a clean list of income-related data
