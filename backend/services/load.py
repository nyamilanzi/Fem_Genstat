"""
Data loading and schema inference services
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import pyreadstat
import polars as pl
from models.schemas import VariableType, VariableInfo

def load_file(file_path: str, file_type: str) -> pd.DataFrame:
    """Load file based on type and return DataFrame"""
    
    if file_type == "csv":
        # Try different encodings for CSV
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode CSV file with any supported encoding")
    
    elif file_type in ["xlsx", "xls"]:
        return pd.read_excel(file_path)
    
    elif file_type == "sav":
        df, meta = pyreadstat.read_sav(file_path)
        return df
    
    elif file_type == "dta":
        df, meta = pyreadstat.read_dta(file_path)
        return df
    
    elif file_type == "parquet":
        return pd.read_parquet(file_path)
    
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def infer_variable_type(series: pd.Series) -> VariableType:
    """Infer variable type from pandas Series"""
    
    # Check for datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return VariableType.DATETIME
    
    # Check for boolean
    if pd.api.types.is_bool_dtype(series):
        return VariableType.BOOLEAN
    
    # Check for numeric
    if pd.api.types.is_numeric_dtype(series):
        # Check if it's actually categorical (few unique values relative to length)
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.1 and series.nunique() <= 20:
            return VariableType.CATEGORICAL
        return VariableType.CONTINUOUS
    
    # Check for object/string that might be categorical
    if pd.api.types.is_object_dtype(series):
        unique_ratio = series.nunique() / len(series)
        if unique_ratio < 0.1 and series.nunique() <= 50:
            return VariableType.CATEGORICAL
        return VariableType.CATEGORICAL  # Default object to categorical
    
    return VariableType.CATEGORICAL

def get_sample_values(series: pd.Series, max_values: int = 10) -> List[Any]:
    """Get sample values from series, handling different data types"""
    
    # Remove NaN values
    clean_series = series.dropna()
    
    if len(clean_series) == 0:
        return []
    
    # For numeric types, get unique values
    if pd.api.types.is_numeric_dtype(series):
        unique_vals = clean_series.unique()
        if len(unique_vals) <= max_values:
            return sorted(unique_vals.tolist())
        else:
            # Sample from unique values
            return sorted(np.random.choice(unique_vals, max_values, replace=False).tolist())
    
    # For categorical, get most frequent values
    value_counts = clean_series.value_counts()
    return value_counts.head(max_values).index.tolist()

def identify_gender_candidates(df: pd.DataFrame) -> List[str]:
    """Identify potential gender columns based on common patterns"""
    
    gender_keywords = [
        'gender', 'sex', 'male', 'female', 'man', 'woman', 
        'gend', 'sexe', 'geschlecht', 'género', 'sexo'
    ]
    
    candidates = []
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Direct keyword match
        if any(keyword in col_lower for keyword in gender_keywords):
            candidates.append(col)
            continue
        
        # Check if column has gender-like values
        if df[col].dtype == 'object':
            unique_vals = df[col].dropna().str.lower().unique()
            gender_values = [
                'male', 'female', 'm', 'f', 'man', 'woman', 'men', 'women',
                'masculine', 'feminine', 'other', 'non-binary', 'transgender',
                'prefer not to say', 'unknown', 'missing'
            ]
            
            if any(val in gender_values for val in unique_vals):
                candidates.append(col)
    
    return candidates

def infer_schema(df: pd.DataFrame) -> Tuple[List[VariableInfo], List[str]]:
    """Infer schema from DataFrame and identify gender candidates"""
    
    schema = []
    gender_candidates = identify_gender_candidates(df)
    
    for col in df.columns:
        series = df[col]
        var_type = infer_variable_type(series)
        
        # Calculate missing percentage
        missing_pct = (series.isna().sum() / len(series)) * 100
        
        # Get sample values
        sample_values = get_sample_values(series)
        
        # Convert numpy types to Python types for JSON serialization
        sample_values_clean = []
        for val in sample_values:
            if pd.isna(val):
                sample_values_clean.append(None)
            elif isinstance(val, (np.integer, np.floating)):
                sample_values_clean.append(val.item())
            else:
                sample_values_clean.append(val)
        
        var_info = VariableInfo(
            name=col,
            dtype=str(series.dtype),
            unique_n=series.nunique(),
            sample_values=sample_values_clean,
            missing_pct=round(missing_pct, 2),
            variable_type=var_type
        )
        
        schema.append(var_info)
    
    return schema, gender_candidates

def validate_file_size(file_path: str, max_size_mb: int) -> bool:
    """Validate file size is within limits"""
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get basic file information"""
    stat = os.stat(file_path)
    return {
        "filename": os.path.basename(file_path),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified": stat.st_mtime
    }

