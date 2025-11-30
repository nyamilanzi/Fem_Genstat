"""
Analysis router for statistical analysis
"""

import os
import tempfile
import json
import pandas as pd
import numpy as np
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse

from models.schemas import AnalysisRequest, AnalysisResponse, ErrorResponse, TestResult
from services.cache import DataCache
from services.summarize import (
    apply_gender_mapping, handle_missing_data, apply_small_cell_suppression,
    summarize_by_gender, summarize_continuous_variable, summarize_categorical_variable,
    analyze_missingness, test_normality
)
from services.gender_bias import assess_gender_bias
from services.test_select import select_continuous_test, select_categorical_test
from services.effects import calculate_continuous_effect_sizes, calculate_categorical_effect_sizes
from services.fdr import apply_fdr_to_analysis_results

router = APIRouter()

def get_data_cache(request: Request) -> DataCache:
    """Dependency to get data cache instance"""
    return request.app.state.data_cache

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(
    request: AnalysisRequest,
    cache: DataCache = Depends(get_data_cache)
):
    """Run gender-stratified analysis on uploaded dataset"""
    
    # Get session data
    session = cache.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    df = session["data"].copy()
    
    # Convert all column names to lowercase to avoid case sensitivity issues
    df.columns = df.columns.str.lower()
    
    # Convert variable names to lowercase to match DataFrame columns
    gender_col = request.gender_col.lower()
    vars_continuous = [var.lower() for var in request.vars_continuous]
    vars_categorical = [var.lower() for var in request.vars_categorical]
    
    # Apply gender mapping (convert to string first, then map, then convert to lowercase)
    df[gender_col] = df[gender_col].astype(str)
    gender_map_dict = {item.from_value: item.to_value for item in request.gender_map}
    print(f"DEBUG: Gender mapping dict: {gender_map_dict}")
    print(f"DEBUG: Unique values before mapping: {df[gender_col].unique()}")
    df[gender_col] = df[gender_col].map(gender_map_dict).fillna('missing')
    print(f"DEBUG: Unique values after mapping: {df[gender_col].unique()}")
    # Convert gender values to lowercase after mapping
    df[gender_col] = df[gender_col].str.lower()
    print(f"DEBUG: Unique values after lowercase: {df[gender_col].unique()}")
    
    # Handle missing data
    df = handle_missing_data(df, request.missing_policy, request.impute.dict() if request.impute else None)
    
    # Get gender summary
    gender_summary = summarize_by_gender(df, gender_col, request.categories_order)
    
    # Test normality for continuous variables
    normality_tests = []
    for var in vars_continuous:
        var_normality = test_normality(df, var, gender_col, request.categories_order)
        normality_tests.extend(var_normality)
    
    # Analyze continuous variables
    continuous_results = []
    for var in vars_continuous:
        # Summarize variable
        var_stats = summarize_continuous_variable(
            df, var, gender_col, request.categories_order,
            request.weight_col, request.suppress_threshold
        )
        
        # Select and run appropriate test
        test_name, test_result_dict = select_continuous_test(
            df, var, gender_col, request.categories_order, normality_tests
        )
        
        # Convert test result to TestResult object
        p_val = test_result_dict.get("p", 0.0)
        if p_val is None or (isinstance(p_val, float) and np.isnan(p_val)):
            p_val = "N/A"
        
        stat_val = test_result_dict.get("statistic", 0.0)
        if stat_val is None or (isinstance(stat_val, float) and np.isnan(stat_val)):
            stat_val = "N/A"
        
        df_val = test_result_dict.get("df")
        if df_val is None or (isinstance(df_val, float) and np.isnan(df_val)):
            df_val = None
        
        test_result = TestResult(
            name=test_name,
            p=p_val,
            statistic=stat_val,
            df=df_val,
            assumptions_met=test_result_dict.get("assumptions_met", True),
            note=test_result_dict.get("note")
        )
        
        # Calculate effect sizes
        effect_sizes = calculate_continuous_effect_sizes(
            df, var, gender_col, request.categories_order, test_name
        )
        
        continuous_results.append({
            "var": var,
            "table": [stat.dict() for stat in var_stats],
            "test": test_result.dict(),
            "effects": [effect.dict() for effect in effect_sizes]
        })
    
    # Analyze categorical variables
    categorical_results = []
    for var in vars_categorical:
        # Summarize variable
        var_levels = summarize_categorical_variable(
            df, var, gender_col, request.categories_order,
            request.weight_col, request.suppress_threshold
        )
        
        # Select and run appropriate test
        test_name, test_result_dict = select_categorical_test(
            df, var, gender_col, request.categories_order
        )
        
        # Convert test result to TestResult object
        p_val = test_result_dict.get("p", 0.0)
        if p_val is None or (isinstance(p_val, float) and np.isnan(p_val)):
            p_val = "N/A"
        
        stat_val = test_result_dict.get("statistic", 0.0)
        if stat_val is None or (isinstance(stat_val, float) and np.isnan(stat_val)):
            stat_val = "N/A"
        
        df_val = test_result_dict.get("df")
        if df_val is None or (isinstance(df_val, float) and np.isnan(df_val)):
            df_val = None
        
        test_result = TestResult(
            name=test_name,
            p=p_val,
            statistic=stat_val,
            df=df_val,
            assumptions_met=test_result_dict.get("assumptions_met", True),
            note=test_result_dict.get("note")
        )
        
        # Calculate effect sizes
        effect_sizes = calculate_categorical_effect_sizes(
            df, var, gender_col, request.categories_order, test_name
        )
        
        categorical_results.append({
            "var": var,
            "table": [level.dict() for level in var_levels],
            "test": test_result.dict(),
            "effects": [effect.dict() for effect in effect_sizes]
        })
    
    # Apply FDR correction if requested
    if request.fdr:
        corrected_results = apply_fdr_to_analysis_results(
            continuous_results, categorical_results, "BH"
        )
        continuous_results = corrected_results['continuous_results']
        categorical_results = corrected_results['categorical_results']
    
    # Analyze missingness
    all_vars = vars_continuous + vars_categorical
    missingness_analysis = analyze_missingness(
        df, gender_col, request.categories_order, all_vars
    )
    
    # Prepare analysis results for gender bias assessment
    analysis_results_dict = {
        "settings": request.dict(),
        "by_gender": [summary.dict() for summary in gender_summary],
        "continuous": continuous_results,
        "categorical": categorical_results,
        "missingness": [missing.dict() for missing in missingness_analysis],
        "diagnostics": {
            "normality": normality_tests,
            "multiple_testing": {
                "fdr_method": "BH" if request.fdr else "none",
                "adjusted": request.fdr
            }
        }
    }
    
    # Assess gender bias
    gender_bias_assessment = assess_gender_bias(
        analysis_results_dict, df, gender_col, request.categories_order
    )
    
    # Generate export files
    file_urls = await _generate_export_files(
        df, request, continuous_results, categorical_results, cache
    )
    
    # Prepare response
    response_data = {
        "settings": request.dict(),
        "by_gender": [summary.dict() for summary in gender_summary],
        "continuous": continuous_results,
        "categorical": categorical_results,
        "missingness": [missing.dict() for missing in missingness_analysis],
        "diagnostics": {
            "normality": normality_tests,
            "multiple_testing": {
                "fdr_method": "BH" if request.fdr else "none",
                "adjusted": request.fdr
            }
        },
        "gender_bias": gender_bias_assessment,
        "files": file_urls
    }
    
    # Store analysis results in cache
    cache.update_session(request.session_id, {"analysis_results": response_data})
    
    return AnalysisResponse(**response_data)

async def _generate_export_files(
    df, request: AnalysisRequest, continuous_results, categorical_results, cache: DataCache
) -> Dict[str, str]:
    """Generate CSV and JSON export files"""
    
    session_id = request.session_id
    
    # Create temporary directory for exports
    temp_dir = tempfile.mkdtemp()
    
    # Wide format CSV (summary statistics)
    wide_data = []
    for result in continuous_results:
        for stat in result['table']:
            wide_data.append({
                'variable': result['var'],
                'gender': stat['gender'],
                'n': stat['n'],
                'mean': stat['mean'],
                'sd': stat['sd'],
                'median': stat['median'],
                'iqr': stat['iqr'],
                'min': stat['min'],
                'max': stat['max']
            })
    
    wide_df = pd.DataFrame(wide_data)
    wide_csv_path = os.path.join(temp_dir, f"{session_id}_wide.csv")
    wide_df.to_csv(wide_csv_path, index=False)
    
    # Long format CSV (detailed results)
    long_data = []
    for result in continuous_results + categorical_results:
        for stat in result['table']:
            long_data.append({
                'variable': result['var'],
                'variable_type': 'continuous' if result in continuous_results else 'categorical',
                'gender': stat['gender'],
                **stat
            })
    
    long_df = pd.DataFrame(long_data)
    long_csv_path = os.path.join(temp_dir, f"{session_id}_long.csv")
    long_df.to_csv(long_csv_path, index=False)
    
    # JSON metadata
    json_data = {
        "session_id": session_id,
        "analysis_settings": request.dict(),
        "continuous_results": continuous_results,
        "categorical_results": categorical_results,
        "export_timestamp": pd.Timestamp.now().isoformat()
    }
    
    json_path = os.path.join(temp_dir, f"{session_id}_metadata.json")
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    # Move files to static directory
    static_dir = "static/exports"
    os.makedirs(static_dir, exist_ok=True)
    
    wide_final = os.path.join(static_dir, f"{session_id}_wide.csv")
    long_final = os.path.join(static_dir, f"{session_id}_long.csv")
    json_final = os.path.join(static_dir, f"{session_id}_metadata.json")
    
    os.rename(wide_csv_path, wide_final)
    os.rename(long_csv_path, long_final)
    os.rename(json_path, json_final)
    
    # Clean up temp directory
    os.rmdir(temp_dir)
    
    return {
        "csv_wide_url": f"/static/exports/{session_id}_wide.csv",
        "csv_long_url": f"/static/exports/{session_id}_long.csv",
        "json_url": f"/static/exports/{session_id}_metadata.json"
    }
