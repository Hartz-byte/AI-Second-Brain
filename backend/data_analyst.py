import pandas as pd
import os
from backend.llm_client import client, MODEL_NAME

DATA_FILE_PATH = "temp_data.csv"

def save_csv(file_bytes: bytes):
    with open(DATA_FILE_PATH, "wb") as f:
        f.write(file_bytes)
    return "CSV uploaded and ready for analysis."

def get_csv_context(filepath=DATA_FILE_PATH):
    if not os.path.exists(filepath):
        return "No tabular data is currently uploaded."
        
    try:
        df = pd.read_csv(filepath)
        # Get schema
        schema = "Columns: " + ", ".join([f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes)])
        # Get stats
        stats = df.describe(include='all').to_markdown()
        # Get head
        sample = df.head(10).to_markdown()
        
        return f"Dataset Schema:\n{schema}\n\nSummary Statistics:\n{stats}\n\nSample Data (First 10 rows):\n{sample}"
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

def answer_data_question(question: str) -> str:
    context = get_csv_context()
    
    if "No tabular data" in context or "Error" in context:
         return "I cannot analyze data because no valid CSV file has been uploaded yet. Please upload a dataset first."
         
    prompt = f"""
You are an expert AI Data Analyst. 
Use the provided dataset schema, summary statistics, and sample rows to answer the user's question accurately.
If the question cannot be answered purely with the sample or statistics, explain what insights you can derive and what limitations exist.

{context}

User Question: {question}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Data Analysis Error: {str(e)}"
