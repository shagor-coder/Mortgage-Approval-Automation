import streamlit as st
# import io
from document_processor import process_document
from classifier import classify_document
from income_extractor import IncomeExtractor
from utils import is_valid_file, display_results
import tempfile
import os
from helpers.get_gpt_response import analyze_loan_approval
import asyncio

st.set_page_config(
    page_title="Document Classifier",
    page_icon="📄",
    layout="wide"
)

def main():
    st.title("Document Classification System")
    st.write("Upload PDFs and images to classify them and extract income information.")

    # Initialize income extractor
    income_extractor = IncomeExtractor()

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload your documents",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )

    if uploaded_files:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []

        for idx, file in enumerate(uploaded_files):
            try:
                if is_valid_file(file):
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(file.getvalue())
                        tmp_file_path = tmp_file.name

                    # Process document (Extract text from PDF or Image)
                    processed_content = process_document(tmp_file_path, file.type)
                    
                    # Classify document type
                    doc_type = classify_document(processed_content)
                    income_data = {}  # Initialize income data dictionary

                    # Extract income for single-page documents (e.g., images)
                    income_data = income_extractor.extract_income(processed_content, doc_type)

                    # Store results
                    results.append({
                        'filename': file.name,
                        'type': doc_type,
                        'status': 'success',
                        'income_data': income_data
                    })

                    # Clean up temporary file
                    os.unlink(tmp_file_path)

                else:
                    results.append({
                        'filename': file.name,
                        'type': 'unknown',
                        'status': 'error',
                        'message': 'Invalid file format'
                    })

                # Update progress bar
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f'Processing file {idx + 1} of {len(uploaded_files)}')

            except Exception as e:
                results.append({
                    'filename': file.name,
                    'type': 'unknown',
                    'status': 'error',
                    'message': str(e)
                })

        # Clear progress bar and status message
        progress_bar.empty()
        status_text.empty()

        # Call AI for loan approval analysis
        with st.status("Analyzing loan eligibility with AI...", expanded=True) as status:
            try:
                gpt_response = asyncio.run(analyze_loan_approval(results))
                status.update(label="Loan analysis completed!", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Loan analysis failed!", state="error", expanded=False)
                gpt_response = f"Error: {str(e)}"
                st.error(f"AI analysis failed: {str(e)}")

        # Display AI decision
        st.markdown(f"### Loan Decision: \n {gpt_response}")

        # Display results
        display_results(results)

if __name__ == "__main__":
    main()