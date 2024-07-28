import pandas as pd
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

def process_excel(files, sheet_name=None, remove_duplicates=False):
    """
    Process a list of Excel files and combine their data into a single DataFrame.

    Args:
        files (list of str): List of file paths to the Excel files.
        sheet_name (str or int or None): Name or index of the sheet to read.
                                         Default is None, which reads the first sheet.
        remove_duplicates (bool): Whether to remove duplicate rows in the combined DataFrame.
                                  Default is False.

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
            df = pd.read_excel(file, sheet_name=sheet_name)
            dfs.append(df)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
            report[file] = {"rows": df.shape[0], "columns": df.shape[1]}
            logging.info(f"Processed file: {file} with {df.shape[0]} rows and {df.shape[1]} columns.")
        except Exception as e:
            logging.error(f"Error processing file {file}: {e}")

    if remove_duplicates:
        combined_df.drop_duplicates(inplace=True)
        logging.info("Removed duplicate rows in the combined DataFrame.")

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
    plt.title('Summary of Processed Excel Files')
    plt.show()


