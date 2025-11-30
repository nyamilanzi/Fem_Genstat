"""
False Discovery Rate (FDR) correction for multiple testing
"""

import numpy as np
from typing import List, Dict, Any
from scipy.stats import false_discovery_control

def apply_fdr_correction(p_values: List[float], method: str = "BH") -> List[float]:
    """
    Apply False Discovery Rate correction to p-values
    
    Args:
        p_values: List of p-values to correct
        method: Correction method ("BH" for Benjamini-Hochberg)
    
    Returns:
        List of corrected p-values
    """
    
    if not p_values:
        return []
    
    # Remove NaN values and keep track of original indices
    valid_indices = []
    valid_p_values = []
    
    for i, p in enumerate(p_values):
        if not np.isnan(p) and p is not None:
            valid_indices.append(i)
            valid_p_values.append(p)
    
    if not valid_p_values:
        return [np.nan] * len(p_values)
    
    # Convert to numpy array
    p_array = np.array(valid_p_values)
    
    if method == "BH":
        # Benjamini-Hochberg procedure
        corrected_p = _benjamini_hochberg(p_array)
    else:
        # Default to BH if unknown method
        corrected_p = _benjamini_hochberg(p_array)
    
    # Reconstruct full array with NaN values preserved
    result = [np.nan] * len(p_values)
    for i, corrected_p_val in zip(valid_indices, corrected_p):
        result[i] = corrected_p_val
    
    return result

def _benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """
    Benjamini-Hochberg procedure for FDR control
    
    Args:
        p_values: Array of p-values
    
    Returns:
        Array of corrected p-values
    """
    
    # Sort p-values and get original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    m = len(sorted_p)
    
    # Calculate BH critical values
    bh_critical = np.arange(1, m + 1) / m
    
    # Find largest k such that P(k) <= (k/m) * alpha
    # For FDR, we use the sorted p-values directly
    corrected_p = np.zeros_like(sorted_p)
    
    for i in range(m):
        # BH correction: multiply by m and divide by rank
        corrected_p[i] = sorted_p[i] * m / (i + 1)
    
    # Ensure monotonicity (corrected p-values should be non-decreasing)
    for i in range(m - 2, -1, -1):
        corrected_p[i] = min(corrected_p[i], corrected_p[i + 1])
    
    # Cap at 1.0
    corrected_p = np.minimum(corrected_p, 1.0)
    
    # Restore original order
    result = np.zeros_like(p_values)
    result[sorted_indices] = corrected_p
    
    return result

def apply_fdr_to_analysis_results(
    continuous_results: List[Dict[str, Any]],
    categorical_results: List[Dict[str, Any]],
    method: str = "BH"
) -> Dict[str, Any]:
    """
    Apply FDR correction to analysis results
    
    Args:
        continuous_results: List of continuous variable results
        categorical_results: List of categorical variable results
        method: FDR correction method
    
    Returns:
        Dictionary with corrected results and metadata
    """
    
    # Extract p-values from continuous results
    continuous_p_values = []
    continuous_indices = []
    
    for i, result in enumerate(continuous_results):
        if 'test' in result and 'p' in result['test']:
            p_val = result['test']['p']
            if not np.isnan(p_val) and p_val is not None:
                continuous_p_values.append(p_val)
                continuous_indices.append(i)
    
    # Extract p-values from categorical results
    categorical_p_values = []
    categorical_indices = []
    
    for i, result in enumerate(categorical_results):
        if 'test' in result and 'p' in result['test']:
            p_val = result['test']['p']
            if not np.isnan(p_val) and p_val is not None:
                categorical_p_values.append(p_val)
                categorical_indices.append(i)
    
    # Apply FDR correction separately to each family
    continuous_corrected = apply_fdr_correction(continuous_p_values, method)
    categorical_corrected = apply_fdr_correction(categorical_p_values, method)
    
    # Update results with corrected p-values
    corrected_continuous = continuous_results.copy()
    corrected_categorical = categorical_results.copy()
    
    for i, corrected_p in zip(continuous_indices, continuous_corrected):
        if i < len(corrected_continuous):
            corrected_continuous[i]['test']['p_fdr'] = corrected_p
            corrected_continuous[i]['test']['fdr_method'] = method
    
    for i, corrected_p in zip(categorical_indices, categorical_corrected):
        if i < len(corrected_categorical):
            corrected_categorical[i]['test']['p_fdr'] = corrected_p
            corrected_categorical[i]['test']['fdr_method'] = method
    
    return {
        'continuous_results': corrected_continuous,
        'categorical_results': corrected_categorical,
        'fdr_method': method,
        'continuous_tests_corrected': len(continuous_p_values),
        'categorical_tests_corrected': len(categorical_p_values)
    }

def get_fdr_summary(corrected_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of FDR correction results
    
    Args:
        corrected_results: Results from apply_fdr_to_analysis_results
    
    Returns:
        Summary statistics
    """
    
    continuous_results = corrected_results['continuous_results']
    categorical_results = corrected_results['categorical_results']
    
    # Count significant results before and after correction
    continuous_sig_raw = 0
    continuous_sig_fdr = 0
    categorical_sig_raw = 0
    categorical_sig_fdr = 0
    
    for result in continuous_results:
        if 'test' in result:
            if result['test'].get('p', 1) < 0.05:
                continuous_sig_raw += 1
            if result['test'].get('p_fdr', 1) < 0.05:
                continuous_sig_fdr += 1
    
    for result in categorical_results:
        if 'test' in result:
            if result['test'].get('p', 1) < 0.05:
                categorical_sig_raw += 1
            if result['test'].get('p_fdr', 1) < 0.05:
                categorical_sig_fdr += 1
    
    return {
        'method': corrected_results['fdr_method'],
        'continuous_tests': len(continuous_results),
        'categorical_tests': len(categorical_results),
        'continuous_sig_raw': continuous_sig_raw,
        'continuous_sig_fdr': continuous_sig_fdr,
        'categorical_sig_raw': categorical_sig_raw,
        'categorical_sig_fdr': categorical_sig_fdr,
        'total_tests': len(continuous_results) + len(categorical_results),
        'total_sig_raw': continuous_sig_raw + categorical_sig_raw,
        'total_sig_fdr': continuous_sig_fdr + categorical_sig_fdr
    }

