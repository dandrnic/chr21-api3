from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path

app = FastAPI(title="Chromosome 21 Gene API")

# Path to your local gene data file
DATA_FILE = Path(__file__).with_name("mart_export(3).txt")

# Load gene data
def load_genes() -> pd.DataFrame:
    return pd.read_csv(DATA_FILE)

@app.get("/")
def root():
    return {"message": "Welcome to Chromosome 21 Gene API"}

@app.get("/genes", response_model=List[Dict[str, Any]])
def list_genes() -> List[Dict[str, Any]]:
    df = load_genes().copy()
    df = df.where(pd.notnull(df), None)  # Replace NaN/NaT with None
    return df.to_dict(orient="records")

@app.get("/genes/{gene_name}", response_model=Dict[str, Any])
def get_gene_by_name(gene_name: str) -> Dict[str, Any]:
    df = load_genes().copy()
    df = df.where(pd.notnull(df), None)

    # Detect correct column name for gene name
    if "Gene name" in df.columns:
        name_col = "Gene name"
    elif "gene_name" in df.columns:
        name_col = "gene_name"
    else:
        raise HTTPException(status_code=500, detail="Dataset missing gene name column")

    match = df[df[name_col].fillna("").str.lower() == gene_name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail="Gene not found")
    return match.to_dict(orient="records")[0]
