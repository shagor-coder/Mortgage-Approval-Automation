import openai
import json
import asyncio
from dotenv import load_dotenv
import os
from helpers.format_income import extract_financial_data 
import json
import asyncio
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create an instance of OpenAI (async client)
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

async def analyze_loan_approval(results):
    """Send financial data to GPT for loan analysis asynchronously."""
    try:
        # Extract only financial data
        financial_data = extract_financial_data(results)

        # Convert to JSON
        formatted_data = json.dumps(financial_data, indent=2)

        message = f"""
        Given the following financial data extracted from multiple documents, determine if the applicant is eligible for a loan. 
        Consider income stability, consistency, and earnings. Provide a detailed explanation.
        Financial Data:
        {formatted_data}
        Based on this, is the loan approvable or not? Provide a clear decision. Don't need to give me the breakdown of the financial data. Just provide decision.
        """

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message}],
            temperature=0.7
        )

        return response.choices[0].message.content

    except openai.OpenAIError as e:
        return f"Error: GPT API failed - {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create an instance of OpenAI (async client)
client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

async def analyze_loan_approval(results):
    """Send financial data to GPT for loan analysis asynchronously."""
    try:
        # Extract only financial data
        financial_data = extract_financial_data(results)

        # Convert to JSON
        formatted_data = json.dumps(financial_data, indent=2)

        message = f"""
        Given the following financial data extracted from multiple documents, determine if the applicant is eligible for a loan. 
        Consider income stability, consistency, and earnings. Provide a detailed explanation.

        Financial Data:
        {formatted_data}

        Based on this, is the loan approvable or not? Provide a clear decision.
        """

        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": message}],
            temperature=0.7
        )

        return response.choices[0].message.content

    except openai.OpenAIError as e:
        return f"Error: GPT API failed - {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
