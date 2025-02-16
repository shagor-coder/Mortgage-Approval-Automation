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
    st.write("Upload PDFs and images to classify them and extract income information")

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
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(file.getvalue())
                        tmp_file_path = tmp_file.name

                    # Process document
                    processed_content = process_document(tmp_file_path, file.type)

                    # Classify document
                    doc_type = classify_document(processed_content)

                    # Extract income from all documents
                    income_data = income_extractor.extract_income(processed_content, doc_type);

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

                # Update progress
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

        progress_bar.empty()
        status_text.empty()

        with st.status("Analyzing loan eligibility with AI...", expanded=True) as status:
                # Run GPT-4o analysis
                gptresponse =  asyncio.run(analyze_loan_approval(results))
                # Update status
                status.update(label="Loan analysis completed!", state="complete", expanded=False)

            # Display GPT-4o response
        st.markdown(f"### Loan Decision: \n {gptresponse}")


        # Display results
        display_results(results)

if __name__ == "__main__":
    main()