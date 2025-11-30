"""
Statistical summarization services
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, ttest_ind, mannwhitneyu, kruskal
import pingouin as pg
from models.schemas import (
    GenderSummary, ContinuousStats, CategoricalLevel, 
    MissingnessInfo, TestResult, EffectSize
)

def apply_gender_mapping(df: pd.DataFrame, gender_col: str, gender_map: List[Dict[str, str]]) -> pd.DataFrame:
    """Apply gender mapping to standardize gender categories"""
    
    df = df.copy()
    mapping_dict = {item['from_value']: item['to_value'] for item in gender_map}
    df[gender_col] = df[gender_col].map(mapping_dict).fillna('missing')
    
    return df

def handle_missing_data(df: pd.DataFrame, missing_policy: str, impute_config: Dict[str, Any] = None) -> pd.DataFrame:
    """Handle missing data based on policy"""
    
    df = df.copy()
    
    if missing_policy == "listwise":
        # Remove rows with any missing values
        return df.dropna()
    
    elif missing_policy == "pairwise":
        # Keep all data, handle missing in individual analyses
        return df
    
    elif missing_policy == "flag":
        # Keep missing as separate category
        return df
    
    # Apply imputation if configured
    if impute_config:
        for var, method in impute_config.items():
            if var in df.columns:
                if method == "mean" and pd.api.types.is_numeric_dtype(df[var]):
                    df[var] = df[var].fillna(df[var].mean())
                elif method == "median" and pd.api.types.is_numeric_dtype(df[var]):
                    df[var] = df[var].fillna(df[var].median())
                elif method == "mode":
                    mode_val = df[var].mode()
                    if not mode_val.empty:
                        df[var] = df[var].fillna(mode_val[0])
    
    return df

def apply_small_cell_suppression(data: Any, threshold: int) -> Any:
    """Apply small cell suppression to data"""
    
    if isinstance(data, (int, float)):
        if data < threshold:
            return f"<{threshold}"
        return data
    
    elif isinstance(data, dict):
        suppressed = {}
        for key, value in data.items():
            suppressed[key] = apply_small_cell_suppression(value, threshold)
        return suppressed
    
    elif isinstance(data, list):
        return [apply_small_cell_suppression(item, threshold) for item in data]
    
    return data

def summarize_by_gender(df: pd.DataFrame, gender_col: str, categories_order: List[str]) -> List[GenderSummary]:
    """Create gender summary statistics"""
    
    summaries = []
    total_n = len(df)
    
    # Debug: Check what's in the gender column
    print(f"DEBUG summarize_by_gender: gender_col = {gender_col}")
    print(f"DEBUG summarize_by_gender: unique values = {df[gender_col].unique()}")
    print(f"DEBUG summarize_by_gender: categories_order = {categories_order}")
    print(f"DEBUG summarize_by_gender: df[gender_col].dtype = {df[gender_col].dtype}")
    
    for gender in categories_order:
        print(f"DEBUG: Checking for gender '{gender}' in values: {gender in df[gender_col].values}")
        if gender in df[gender_col].values:
            gender_data = df[df[gender_col] == gender]
            n = len(gender_data)
            pct = (n / total_n) * 100
            missing_pct = (gender_data[gender_col].isna().sum() / n) * 100 if n > 0 else 0
            
            summaries.append(GenderSummary(
                gender=gender,
                n=n,
                pct=round(pct, 2),
                missing_pct=round(missing_pct, 2)
            ))
            print(f"DEBUG: Added summary for {gender}: n={n}")
    
    print(f"DEBUG: Final summaries count = {len(summaries)}")
    return summaries

def summarize_continuous_variable(
    df: pd.DataFrame, 
    var: str, 
    gender_col: str, 
    categories_order: List[str],
    weight_col: str = None,
    suppress_threshold: int = 5
) -> List[ContinuousStats]:
    """Summarize continuous variable by gender"""
    
    # Ensure lowercase for consistency
    var = var.lower()
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Check if variable exists
    if var not in df.columns:
        print(f"WARNING: Variable '{var}' not found in DataFrame. Available columns: {list(df.columns)}")
        return []
    
    stats_list = []
    
    for gender in categories_order:
        gender_lower = gender.lower()
        if gender_lower in df[gender_col].values:
            gender_data = df[df[gender_col] == gender_lower]
            var_data = gender_data[var].dropna()
            
            if len(var_data) == 0:
                continue
            
            n = len(var_data)
            
            if n < suppress_threshold:
                # Suppress small cells
                stats_list.append(ContinuousStats(
                    gender=gender,
                    n=f"<{suppress_threshold}",
                    mean="<threshold",
                    sd="<threshold",
                    median="<threshold",
                    iqr="<threshold",
                    min="<threshold",
                    max="<threshold"
                ))
                continue
            
            if weight_col and weight_col in df.columns:
                weights = gender_data[weight_col].dropna()
                if len(weights) == len(var_data):
                    # Weighted statistics
                    mean_val = np.average(var_data, weights=weights)
                    # Weighted variance
                    variance = np.average((var_data - mean_val)**2, weights=weights)
                    sd_val = np.sqrt(variance)
                else:
                    mean_val = var_data.mean()
                    sd_val = var_data.std()
            else:
                mean_val = var_data.mean()
                sd_val = var_data.std()
            
            median_val = var_data.median()
            q1 = var_data.quantile(0.25)
            q3 = var_data.quantile(0.75)
            iqr_val = q3 - q1
            min_val = var_data.min()
            max_val = var_data.max()
            
            stats_list.append(ContinuousStats(
                gender=gender,
                n=n,
                mean=round(mean_val, 3),
                sd=round(sd_val, 3),
                median=round(median_val, 3),
                iqr=round(iqr_val, 3),
                min=round(min_val, 3),
                max=round(max_val, 3)
            ))
    
    return stats_list

def summarize_categorical_variable(
    df: pd.DataFrame,
    var: str,
    gender_col: str,
    categories_order: List[str],
    weight_col: str = None,
    suppress_threshold: int = 5
) -> List[CategoricalLevel]:
    """Summarize categorical variable by gender"""
    
    # Ensure lowercase for consistency
    var = var.lower()
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Check if variable exists
    if var not in df.columns:
        print(f"WARNING: Variable '{var}' not found in DataFrame. Available columns: {list(df.columns)}")
        return []
    
    levels = []
    
    # Get all unique values in the variable
    all_values = df[var].dropna().unique()
    
    for gender in categories_order:
        gender_lower = gender.lower()
        if gender_lower in df[gender_col].values:
            gender_data = df[df[gender_col] == gender_lower]
            gender_total = len(gender_data)
            
            for level in all_values:
                level_data = gender_data[gender_data[var] == level]
                n = len(level_data)
                
                if n < suppress_threshold:
                    levels.append(CategoricalLevel(
                        level=str(level),
                        gender=gender,
                        n=f"<{suppress_threshold}",
                        pct="<threshold"
                    ))
                else:
                    pct = (n / gender_total) * 100 if gender_total > 0 else 0
                    levels.append(CategoricalLevel(
                        level=str(level),
                        gender=gender,
                        n=int(n),  # Ensure integer for categorical counts
                        pct=round(pct, 1)  # One decimal place for percentages
                    ))
    
    return levels

def analyze_missingness(
    df: pd.DataFrame,
    gender_col: str,
    categories_order: List[str],
    variables: List[str]
) -> List[MissingnessInfo]:
    """Analyze missing data patterns by gender"""
    
    # Ensure lowercase for consistency
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    variables = [var.lower() for var in variables]
    
    missingness = []
    
    for var in variables:
        # Check if variable exists
        if var not in df.columns:
            print(f"WARNING: Variable '{var}' not found in DataFrame. Available columns: {list(df.columns)}")
            continue
            
        for gender in categories_order:
            gender_lower = gender.lower()
            if gender_lower in df[gender_col].values:
                gender_data = df[df[gender_col] == gender_lower]
                missing_n = gender_data[var].isna().sum()
                missing_pct = (missing_n / len(gender_data)) * 100 if len(gender_data) > 0 else 0
                
                missingness.append(MissingnessInfo(
                    var=var,
                    gender=gender,
                    missing_n=missing_n,
                    missing_pct=round(missing_pct, 2)
                ))
    
    return missingness

def test_normality(df: pd.DataFrame, var: str, gender_col: str, categories_order: List[str]) -> List[Dict[str, Any]]:
    """Test normality for continuous variables by gender group"""
    
    normality_tests = []
    
    # Ensure var is lowercase to match DataFrame columns
    var = var.lower()
    gender_col = gender_col.lower()
    
    # Check if variable exists in DataFrame
    if var not in df.columns:
        print(f"WARNING: Variable '{var}' not found in DataFrame. Available columns: {list(df.columns)}")
        return normality_tests
    
    for gender in categories_order:
        gender_lower = gender.lower()
        if gender_lower in df[gender_col].values:
            gender_data = df[df[gender_col] == gender_lower]
            var_data = gender_data[var].dropna()
            
            if len(var_data) < 3:  # Need at least 3 observations
                continue
            
            # Choose test based on sample size
            if len(var_data) <= 5000:
                test_name = "Shapiro-Wilk"
                try:
                    statistic, p_value = stats.shapiro(var_data)
                except:
                    statistic, p_value = np.nan, np.nan
            else:
                test_name = "D'Agostino"
                try:
                    statistic, p_value = stats.normaltest(var_data)
                except:
                    statistic, p_value = np.nan, np.nan
            
            normality_tests.append({
                "var": var,
                "gender": gender,
                "test": test_name,
                "p": round(p_value, 4) if not np.isnan(p_value) else None,
                "statistic": round(statistic, 4) if not np.isnan(statistic) else None
            })
    
    return normality_tests
