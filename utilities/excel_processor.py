import pandas as pd

def process_excel(files):
    combined_df = pd.DataFrame()
    dfs = []
    for file in files:
        df = pd.read_excel(file)
        dfs.append(df)
        combined_df = pd.concat([combined_df, df], ignore_index=True)
    return combined_df, dfs
