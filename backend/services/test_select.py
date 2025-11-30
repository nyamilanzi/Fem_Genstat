"""
Statistical test selection and execution
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact, ttest_ind, mannwhitneyu, kruskal
import pingouin as pg
from models.schemas import TestResult, EffectSize

def select_continuous_test(
    df: pd.DataFrame, 
    var: str, 
    gender_col: str, 
    categories_order: List[str],
    normality_tests: List[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Select appropriate test for continuous variable vs gender"""
    
    # Ensure lowercase for consistency
    var = var.lower()
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Check if variable exists
    if var not in df.columns:
        return "insufficient_data", {"note": f"Variable '{var}' not found in DataFrame"}
    
    # Get gender groups with data
    groups = []
    group_names = []
    
    for gender in categories_order:
        gender_lower = gender.lower()
        if gender_lower in df[gender_col].values:
            gender_data = df[df[gender_col] == gender_lower]
            var_data = gender_data[var].dropna()
            if len(var_data) > 0:
                groups.append(var_data)
                group_names.append(gender)
    
    if len(groups) < 2:
        return "insufficient_data", {"note": "Less than 2 groups with data"}
    
    # Check normality if provided
    normal_groups = True
    if normality_tests:
        for test in normality_tests:
            if test['var'] == var and test['p'] is not None:
                if test['p'] < 0.05:  # Reject normality
                    normal_groups = False
                    break
    
    # Select test based on number of groups and normality
    if len(groups) == 2:
        if normal_groups:
            return "welch_ttest", _run_welch_ttest(groups[0], groups[1])
        else:
            return "mann_whitney", _run_mann_whitney(groups[0], groups[1])
    else:
        if normal_groups:
            return "welch_anova", _run_welch_anova(groups, group_names)
        else:
            return "kruskal_wallis", _run_kruskal_wallis(groups, group_names)

def select_categorical_test(
    df: pd.DataFrame,
    var: str,
    gender_col: str,
    categories_order: List[str]
) -> Tuple[str, Dict[str, Any]]:
    """Select appropriate test for categorical variable vs gender"""
    
    # Ensure lowercase for consistency
    var = var.lower()
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Check if variable exists
    if var not in df.columns:
        return "insufficient_data", {"note": f"Variable '{var}' not found in DataFrame"}
    
    # Create contingency table
    contingency_table = pd.crosstab(df[var], df[gender_col])
    
    # Filter to only include categories that exist in both variables
    contingency_table = contingency_table.loc[
        contingency_table.index.isin(df[var].dropna().unique()),
        contingency_table.columns.isin(categories_order)
    ]
    
    if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return "insufficient_data", {"note": "Insufficient data for contingency table"}
    
    # Check for small expected frequencies
    expected = stats.chi2_contingency(contingency_table)[3]
    min_expected = expected.min()
    
    if min_expected < 5:
        if contingency_table.shape == (2, 2):
            return "fisher_exact", _run_fisher_exact(contingency_table)
        else:
            # For larger tables with small expected frequencies, use chi-square with warning
            return "chi_square", _run_chi_square(contingency_table, warning=True)
    else:
        return "chi_square", _run_chi_square(contingency_table)

def _run_welch_ttest(group1: pd.Series, group2: pd.Series) -> Dict[str, Any]:
    """Run Welch's t-test for two groups"""
    try:
        statistic, p_value = ttest_ind(group1, group2, equal_var=False)
        return {
            "statistic": round(statistic, 4),
            "p": round(p_value, 4),
            "df": len(group1) + len(group2) - 2,
            "assumptions_met": True,
            "note": "Welch's t-test (unequal variances assumed)"
        }
    except Exception as e:
        return {
            "statistic": np.nan,
            "p": np.nan,
            "df": None,
            "assumptions_met": False,
            "note": f"Error in t-test: {str(e)}"
        }

def _run_mann_whitney(group1: pd.Series, group2: pd.Series) -> Dict[str, Any]:
    """Run Mann-Whitney U test for two groups"""
    try:
        statistic, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
        return {
            "statistic": round(statistic, 4),
            "p": round(p_value, 4),
            "df": None,
            "assumptions_met": True,
            "note": "Mann-Whitney U test (non-parametric)"
        }
    except Exception as e:
        return {
            "statistic": np.nan,
            "p": np.nan,
            "df": None,
            "assumptions_met": False,
            "note": f"Error in Mann-Whitney test: {str(e)}"
        }

def _run_welch_anova(groups: List[pd.Series], group_names: List[str]) -> Dict[str, Any]:
    """Run Welch's ANOVA for multiple groups"""
    try:
        # Prepare data for pingouin
        data_list = []
        group_list = []
        
        for i, group in enumerate(groups):
            data_list.extend(group.tolist())
            group_list.extend([group_names[i]] * len(group))
        
        df_anova = pd.DataFrame({
            'value': data_list,
            'group': group_list
        })
        
        result = pg.welch_anova(data=df_anova, dv='value', between='group')
        
        return {
            "statistic": round(result['F'].iloc[0], 4),
            "p": round(result['p-unc'].iloc[0], 4),
            "df": f"{result['ddof1'].iloc[0]}, {result['ddof2'].iloc[0]}",
            "assumptions_met": True,
            "note": "Welch's ANOVA (unequal variances assumed)"
        }
    except Exception as e:
        return {
            "statistic": np.nan,
            "p": np.nan,
            "df": None,
            "assumptions_met": False,
            "note": f"Error in Welch ANOVA: {str(e)}"
        }

def _run_kruskal_wallis(groups: List[pd.Series], group_names: List[str]) -> Dict[str, Any]:
    """Run Kruskal-Wallis test for multiple groups"""
    try:
        statistic, p_value = kruskal(*groups)
        return {
            "statistic": round(statistic, 4),
            "p": round(p_value, 4),
            "df": len(groups) - 1,
            "assumptions_met": True,
            "note": "Kruskal-Wallis test (non-parametric)"
        }
    except Exception as e:
        return {
            "statistic": np.nan,
            "p": np.nan,
            "df": None,
            "assumptions_met": False,
            "note": f"Error in Kruskal-Wallis test: {str(e)}"
        }

def _run_chi_square(contingency_table: pd.DataFrame, warning: bool = False) -> Dict[str, Any]:
    """Run chi-square test of independence"""
    try:
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        result = {
            "statistic": round(chi2, 4),
            "p": round(p_value, 4),
            "df": dof,
            "assumptions_met": not warning,
            "note": "Chi-square test of independence"
        }
        
        if warning:
            result["note"] += " (some expected frequencies < 5, interpret with caution)"
        
        return result
    except Exception as e:
        return {
            "statistic": np.nan,
            "p": np.nan,
            "df": None,
            "assumptions_met": False,
            "note": f"Error in chi-square test: {str(e)}"
        }

def _run_fisher_exact(contingency_table: pd.DataFrame) -> Dict[str, Any]:
    """Run Fisher's exact test for 2x2 table"""
    try:
        if contingency_table.shape != (2, 2):
            return {
                "statistic": np.nan,
                "p": np.nan,
                "df": None,
                "assumptions_met": False,
                "note": "Fisher's exact test only available for 2x2 tables"
            }
        
        # Convert to 2x2 array
        table_array = contingency_table.values
        odds_ratio, p_value = fisher_exact(table_array)
        
        return {
            "statistic": round(odds_ratio, 4),
            "p": round(p_value, 4),
            "df": None,
            "assumptions_met": True,
            "note": "Fisher's exact test (2x2 table)"
        }
    except Exception as e:
        return {
            "statistic": np.nan,
            "p": np.nan,
            "df": None,
            "assumptions_met": False,
            "note": f"Error in Fisher's exact test: {str(e)}"
        }

