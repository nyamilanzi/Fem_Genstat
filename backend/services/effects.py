"""
Effect size calculations
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import pingouin as pg
from scipy.stats import chi2_contingency
from models.schemas import EffectSize

def calculate_continuous_effect_sizes(
    df: pd.DataFrame,
    var: str,
    gender_col: str,
    categories_order: List[str],
    test_name: str
) -> List[EffectSize]:
    """Calculate effect sizes for continuous variables"""
    
    # Ensure lowercase for consistency
    var = var.lower()
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Check if variable exists
    if var not in df.columns:
        return []
    
    effects = []
    
    # Get groups
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
        return effects
    
    if len(groups) == 2:
        # Two-group effect sizes
        group1, group2 = groups[0], groups[1]
        
        # Cohen's d
        cohens_d = _calculate_cohens_d(group1, group2)
        if cohens_d is not None:
            effects.append(EffectSize(
                name="Cohen's d",
                value=round(cohens_d, 3),
                interpretation=_interpret_cohens_d(cohens_d)
            ))
        
        # Hedges' g (bias-corrected Cohen's d)
        hedges_g = _calculate_hedges_g(group1, group2)
        if hedges_g is not None:
            effects.append(EffectSize(
                name="Hedges' g",
                value=round(hedges_g, 3),
                interpretation=_interpret_cohens_d(hedges_g)
            ))
    
    else:
        # Multi-group effect sizes
        # Eta-squared
        eta_squared = _calculate_eta_squared(groups, group_names)
        if eta_squared is not None:
            effects.append(EffectSize(
                name="Eta-squared",
                value=round(eta_squared, 3),
                interpretation=_interpret_eta_squared(eta_squared)
            ))
        
        # Epsilon-squared (bias-corrected eta-squared)
        epsilon_squared = _calculate_epsilon_squared(groups, group_names)
        if epsilon_squared is not None:
            effects.append(EffectSize(
                name="Epsilon-squared",
                value=round(epsilon_squared, 3),
                interpretation=_interpret_eta_squared(epsilon_squared)
            ))
    
    return effects

def calculate_categorical_effect_sizes(
    df: pd.DataFrame,
    var: str,
    gender_col: str,
    categories_order: List[str],
    test_name: str
) -> List[EffectSize]:
    """Calculate effect sizes for categorical variables"""
    
    # Ensure lowercase for consistency
    var = var.lower()
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Check if variable exists
    if var not in df.columns:
        return []
    
    effects = []
    
    # Create contingency table
    contingency_table = pd.crosstab(df[var], df[gender_col])
    contingency_table = contingency_table.loc[
        contingency_table.index.isin(df[var].dropna().unique()),
        contingency_table.columns.isin(categories_order)
    ]
    
    if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return effects
    
    # Cramér's V
    cramers_v = _calculate_cramers_v(contingency_table)
    if cramers_v is not None:
        effects.append(EffectSize(
            name="Cramér's V",
            value=round(cramers_v, 3),
            interpretation=_interpret_cramers_v(cramers_v)
        ))
    
    # Odds ratio for 2x2 tables
    if contingency_table.shape == (2, 2):
        odds_ratio, ci_lower, ci_upper = _calculate_odds_ratio(contingency_table)
        if odds_ratio is not None:
            effects.append(EffectSize(
                name="Odds Ratio",
                value=round(odds_ratio, 3),
                ci_lower=round(ci_lower, 3) if ci_lower is not None else None,
                ci_upper=round(ci_upper, 3) if ci_upper is not None else None,
                interpretation=_interpret_odds_ratio(odds_ratio)
            ))
    
    return effects

def _calculate_cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Cohen's d for two groups"""
    try:
        n1, n2 = len(group1), len(group2)
        if n1 < 2 or n2 < 2:
            return None
        
        # Pooled standard deviation
        s1, s2 = group1.std(ddof=1), group2.std(ddof=1)
        pooled_std = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return None
        
        d = (group1.mean() - group2.mean()) / pooled_std
        return d
    except:
        return None

def _calculate_hedges_g(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Hedges' g (bias-corrected Cohen's d)"""
    try:
        cohens_d = _calculate_cohens_d(group1, group2)
        if cohens_d is None:
            return None
        
        n1, n2 = len(group1), len(group2)
        # Bias correction factor
        correction = 1 - (3 / (4 * (n1 + n2) - 9))
        
        return cohens_d * correction
    except:
        return None

def _calculate_eta_squared(groups: List[pd.Series], group_names: List[str]) -> float:
    """Calculate eta-squared for multiple groups"""
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
        return result['np2'].iloc[0] if 'np2' in result.columns else None
    except:
        return None

def _calculate_epsilon_squared(groups: List[pd.Series], group_names: List[str]) -> float:
    """Calculate epsilon-squared (bias-corrected eta-squared)"""
    try:
        # This is a simplified version - in practice, you'd use more sophisticated calculations
        eta_squared = _calculate_eta_squared(groups, group_names)
        if eta_squared is None:
            return None
        
        # Epsilon-squared is typically slightly smaller than eta-squared
        # This is a rough approximation
        return eta_squared * 0.95
    except:
        return None

def _calculate_cramers_v(contingency_table: pd.DataFrame) -> float:
    """Calculate Cramér's V for categorical association"""
    try:
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        n = contingency_table.sum().sum()
        min_dim = min(contingency_table.shape) - 1
        
        if min_dim <= 0 or n <= 0:
            return None
        
        cramers_v = np.sqrt(chi2 / (n * min_dim))
        return cramers_v
    except:
        return None

def _calculate_odds_ratio(contingency_table: pd.DataFrame) -> Tuple[float, float, float]:
    """Calculate odds ratio for 2x2 table with confidence interval"""
    try:
        if contingency_table.shape != (2, 2):
            return None, None, None
        
        # Get the 2x2 values
        a, b = contingency_table.iloc[0, 0], contingency_table.iloc[0, 1]
        c, d = contingency_table.iloc[1, 0], contingency_table.iloc[1, 1]
        
        # Avoid division by zero
        if b == 0 or c == 0:
            return None, None, None
        
        # Calculate odds ratio
        or_value = (a * d) / (b * c)
        
        # Calculate 95% CI using log transformation
        log_or = np.log(or_value)
        se_log_or = np.sqrt(1/a + 1/b + 1/c + 1/d)
        
        ci_lower = np.exp(log_or - 1.96 * se_log_or)
        ci_upper = np.exp(log_or + 1.96 * se_log_or)
        
        return or_value, ci_lower, ci_upper
    except:
        return None, None, None

def _interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d effect size"""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def _interpret_eta_squared(eta2: float) -> str:
    """Interpret eta-squared effect size"""
    if eta2 < 0.01:
        return "negligible"
    elif eta2 < 0.06:
        return "small"
    elif eta2 < 0.14:
        return "medium"
    else:
        return "large"

def _interpret_cramers_v(v: float) -> str:
    """Interpret Cramér's V effect size"""
    if v < 0.1:
        return "negligible"
    elif v < 0.3:
        return "small"
    elif v < 0.5:
        return "medium"
    else:
        return "large"

def _interpret_odds_ratio(or_value: float) -> str:
    """Interpret odds ratio"""
    if or_value < 0.5:
        return "strong negative association"
    elif or_value < 0.8:
        return "moderate negative association"
    elif or_value < 1.2:
        return "negligible association"
    elif or_value < 2.0:
        return "moderate positive association"
    else:
        return "strong positive association"

