import pandas as pd
import os
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate

def process_csv(files):
    combined_df = pd.DataFrame()
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df, dfs

def generate_insights(query, df):
    # Combine CSV data into a single DataFrame for analysis
    if df is None or df.empty:
        return "No CSV data available for generating insights."

    # Initialize LLM
    llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.3, api_key=os.getenv("GOOGLE_API_KEY"))

    # Define prompt template
    prompt_template = """
    Using the following data, answer the query as accurately as possible. If the query cannot be answered with the provided data, 
    please state "The query cannot be answered with the provided data."

    Data:\n {data}

    Query: {query}

    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["data", "query"])

    # Format the DataFrame as a string for the prompt
    data_string = df.to_string()

    # Prepare the input for the LLM
    input_variables = {"data": data_string, "query": query}
    prompt_text = prompt.format(**input_variables)

    # Generate the response
    response = llm(prompt_text)

    return response
