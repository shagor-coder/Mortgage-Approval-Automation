import streamlit as st

# Allowed file types for validation
ALLOWED_FILE_TYPES = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']

def is_valid_file(file):
    """Check if uploaded file is valid"""
    return file.type in ALLOWED_FILE_TYPES

def display_results(results):
    """Display classification results in an organized manner"""
    st.subheader("Classification Results")

    categories = categorize_results(results)

    col1, col2 = st.columns(2)

    with col1:
        display_successful_classifications(categories)
        display_unclassified_documents(categories)

    with col2:
        display_errors(categories)

    display_summary(results, categories)

def categorize_results(results):
    """Group results by document type"""
    categories = {
        'W2': [],
        'W9': [],
        'Bank Statement': [],
        'Paystub': [],
        'Unknown': [],
        'Error': []
    }

    for result in results:
        if result['status'] == 'error':
            categories['Error'].append(result)
        else:
            categories[result['type']].append(result)

    return categories

def display_successful_classifications(categories):
    """Display successfully classified documents"""
    st.write("### Successfully Classified")
    for category in ['W2', 'W9', 'Bank Statement', 'Paystub']:
        if categories[category]:
            st.write(f"#### {category}s")
            for doc in categories[category]:
                st.write(f"- {doc['filename']}")
                display_income_data(category, doc)

def display_income_data(category, doc):
    """Display income data for W2 and Paystub documents"""
    if 'income_data' in doc and doc['income_data']:
        with st.expander("Income Information"):
            if category == 'W2':
                display_w2_income(doc['income_data'])
            elif category == 'Paystub':
                display_paystub_income(doc['income_data'])

def display_w2_income(income_data):
    """Display W2-specific income details"""
    st.write("W2 Income Details:")
    st.write(f"- Wages and Tips: ${income_data.get('wages_and_tips', 0):,.2f}")
    st.write(f"- Social Security Wages: ${income_data.get('social_security_wages', 0):,.2f}")
    st.write(f"- Medicare Wages: ${income_data.get('medicare_wages', 0):,.2f}")

def display_paystub_income(income_data):
    """Display Paystub-specific income details"""
    st.write("Paystub Income Details:")
    pay_freq_text = {
        52: 'Weekly',
        26: 'Biweekly',
        24: 'Semi-monthly',
        12: 'Monthly',
        4: 'Quarterly',
        1: 'Annually'
    }.get(income_data.get('pay_frequency', 0), 'Unknown')

    st.write(f"- Period Ending: {income_data.get('period_ending', 'Not found')}")
    st.write(f"- Pay Frequency: {pay_freq_text}")
    st.write("\nCurrent Pay Period:")
    st.write(f"- Gross Pay: ${income_data.get('gross_pay', 0):,.2f}")
    if income_data.get('hours', 0) > 0:
        st.write(f"- Hours Worked: {income_data.get('hours', 0)}")
    if income_data.get('rate', 0) > 0:
        st.write(f"- Hourly Rate: ${income_data.get('rate', 0):,.2f}")
    st.write(f"- Net Pay: ${income_data.get('net_pay', 0):,.2f}")
    st.write("\nYear-to-Date and Projections:")
    st.write(f"- YTD Earnings: ${income_data.get('ytd_earnings', 0):,.2f}")
    st.write(f"- Projected Annual Income: ${income_data.get('annualized_income', 0):,.2f}")
    st.write(f"- Estimated Monthly Income: ${income_data.get('monthly_income', 0):,.2f}")

def display_unclassified_documents(categories):
    """Display unclassified documents"""
    if categories['Unknown']:
        st.write("#### Unclassified Documents")
        for doc in categories['Unknown']:
            st.write(f"- {doc['filename']}")
            display_detected_income(doc)

def display_detected_income(doc):
    """Display detected income from unclassified documents"""
    if 'income_data' in doc and doc['income_data']:
        with st.expander("Detected Income Information"):
            amounts = doc['income_data'].get('detected_amounts', [])
            if amounts:
                for idx, item in enumerate(amounts, 1):
                    st.write(f"Amount {idx}: ${item['amount']:,.2f}")
                    st.write(f"Context: {item['context']}")
                    st.write("---")
                st.write(f"Highest amount: ${doc['income_data'].get('highest_amount', 0):,.2f}")
                st.write(f"Total amounts found: {doc['income_data'].get('total_amounts_found', 0)}")
            else:
                st.write("No monetary amounts detected")

def display_errors(categories):
    """Display errors that occurred during document processing"""
    if categories['Error']:
        st.write("### Errors")
        for doc in categories['Error']:
            st.error(f"Error processing {doc['filename']}: {doc.get('message', 'Unknown error')}")

def display_summary(results, categories):
    """Display a summary of the classification process"""
    st.write("### Summary")
    total_files = len(results)
    successful = len([r for r in results if r['status'] == 'success'])
    st.write(f"Total files processed: {total_files}")
    st.write(f"Successfully classified: {successful}")
    st.write(f"Errors: {len(categories['Error'])}")
