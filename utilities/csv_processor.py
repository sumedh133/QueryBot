import pandas as pd
import os
import matplotlib.pyplot as plt
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate

def process_csv(files):
    """
    Process a list of CSV files and combine their data into a single DataFrame.

    Args:
        files (list of str): List of file paths to the CSV files.

    Returns:
        combined_df (pd.DataFrame): Combined DataFrame containing data from all files.
        dfs (list of pd.DataFrame): List of individual DataFrames for each file.
        report (dict): Summary report of the number of rows and columns from each file.
    """
    combined_df = pd.DataFrame()
    dfs = []
    report = {}

    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
            report[file] = {"rows": df.shape[0], "columns": df.shape[1]}
            print(f"Processed file: {file} with {df.shape[0]} rows and {df.shape[1]} columns.")
        except Exception as e:
            print(f"Error processing file {file}: {e}")

    return combined_df, dfs, report

def plot_summary(report):
    """
    Plot a summary of the processed files.

    Args:
        report (dict): Summary report of the number of rows and columns from each file.
    """
    files = list(report.keys())
    rows = [report[file]['rows'] for file in files]
    columns = [report[file]['columns'] for file in files]

    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_xlabel('Files')
    ax1.set_ylabel('Rows', color=color)
    ax1.bar(files, rows, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Columns', color=color)
    ax2.plot(files, columns, color=color, marker='o')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    plt.title('Summary of Processed CSV Files')
    plt.show()

def generate_insights(query, df):
    """
    Generate insights based on the provided query and DataFrame.

    Args:
        query (str): The query for generating insights.
        df (pd.DataFrame): The DataFrame containing the data.

    Returns:
        str: Generated insights.
    """
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

