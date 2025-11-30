"""
Gender bias assessment module
Uses gender transformative approaches and gender analysis frameworks
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


def assess_gender_bias(
    analysis_results: Dict[str, Any],
    df: pd.DataFrame,
    gender_col: str,
    categories_order: List[str]
) -> Dict[str, Any]:
    """
    Comprehensive gender bias assessment using gender transformative approaches
    
    Assesses:
    1. Statistical disparities (effect sizes and significance)
    2. Representation gaps
    3. Missing data patterns by gender
    4. Intersectional considerations
    5. Practical significance of differences
    """
    
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    bias_assessment = {
        "overall_summary": "",
        "statistical_disparities": [],
        "representation_gaps": [],
        "missing_data_bias": [],
        "practical_significance": [],
        "recommendations": [],
        "gender_transformative_insights": []
    }
    
    # 1. Assess statistical disparities
    statistical_disparities = _assess_statistical_disparities(analysis_results)
    bias_assessment["statistical_disparities"] = statistical_disparities
    
    # 2. Assess representation gaps
    representation_gaps = _assess_representation_gaps(analysis_results, df, gender_col, categories_order)
    bias_assessment["representation_gaps"] = representation_gaps
    
    # 3. Assess missing data bias
    missing_data_bias = _assess_missing_data_bias(analysis_results)
    bias_assessment["missing_data_bias"] = missing_data_bias
    
    # 4. Assess practical significance
    practical_significance = _assess_practical_significance(analysis_results)
    bias_assessment["practical_significance"] = practical_significance
    
    # 5. Generate recommendations
    recommendations = _generate_recommendations(bias_assessment)
    bias_assessment["recommendations"] = recommendations
    
    # 6. Generate gender transformative insights
    insights = _generate_gender_transformative_insights(bias_assessment, analysis_results)
    bias_assessment["gender_transformative_insights"] = insights
    
    # 7. Overall summary
    bias_assessment["overall_summary"] = _generate_overall_summary(bias_assessment)
    
    return bias_assessment


def _assess_statistical_disparities(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Assess statistical disparities between gender groups"""
    
    disparities = []
    
    # Check continuous variables
    for var_result in analysis_results.get("continuous", []):
        var_name = var_result["var"]
        test = var_result.get("test", {})
        effects = var_result.get("effects", [])
        
        p_value = test.get("p")
        if isinstance(p_value, str):
            continue
            
        is_significant = p_value is not None and p_value < 0.05
        
        # Get effect sizes
        effect_size = None
        effect_interpretation = None
        for effect in effects:
            if effect["name"] in ["Cohen's d", "Hedges' g"]:
                effect_size = effect.get("value")
                effect_interpretation = effect.get("interpretation", "")
                break
        
        if is_significant:
            severity = "moderate"
            if effect_size is not None:
                try:
                    eff_val = float(effect_size) if isinstance(effect_size, (int, float, str)) else None
                    if eff_val is not None:
                        if abs(eff_val) >= 0.8:
                            severity = "large"
                        elif abs(eff_val) >= 0.5:
                            severity = "moderate"
                        else:
                            severity = "small"
                except (ValueError, TypeError):
                    pass
            
            disparities.append({
                "variable": var_name,
                "type": "continuous",
                "p_value": p_value,
                "effect_size": effect_size,
                "effect_interpretation": effect_interpretation,
                "severity": severity,
                "interpretation": f"Statistically significant difference found in {var_name} (p={p_value:.4f}). {effect_interpretation or 'Effect size indicates practical significance.'}"
            })
    
    # Check categorical variables
    for var_result in analysis_results.get("categorical", []):
        var_name = var_result["var"]
        test = var_result.get("test", {})
        effects = var_result.get("effects", [])
        
        p_value = test.get("p")
        if isinstance(p_value, str):
            continue
            
        is_significant = p_value is not None and p_value < 0.05
        
        # Get effect sizes
        effect_size = None
        effect_interpretation = None
        for effect in effects:
            if effect["name"] in ["Cramér's V", "Odds Ratio"]:
                effect_size = effect.get("value")
                effect_interpretation = effect.get("interpretation", "")
                break
        
        if is_significant:
            severity = "moderate"
            if effect_size is not None:
                try:
                    eff_val = float(effect_size) if isinstance(effect_size, (int, float, str)) else None
                    if eff_val is not None:
                        if isinstance(effect_size, str) and "Cramér" in str(eff_val):
                            # Cramér's V interpretation
                            if eff_val >= 0.5:
                                severity = "large"
                            elif eff_val >= 0.3:
                                severity = "moderate"
                            else:
                                severity = "small"
                except (ValueError, TypeError):
                    pass
            
            disparities.append({
                "variable": var_name,
                "type": "categorical",
                "p_value": p_value,
                "effect_size": effect_size,
                "effect_interpretation": effect_interpretation,
                "severity": severity,
                "interpretation": f"Statistically significant association found between {var_name} and gender (p={p_value:.4f}). {effect_interpretation or 'This indicates gender-based differences in distribution.'}"
            })
    
    return disparities


def _assess_representation_gaps(
    analysis_results: Dict[str, Any],
    df: pd.DataFrame,
    gender_col: str,
    categories_order: List[str]
) -> List[Dict[str, Any]]:
    """Assess representation gaps using gender analysis frameworks"""
    
    gaps = []
    gender_col = gender_col.lower()
    categories_order = [cat.lower() for cat in categories_order]
    
    # Get gender distribution
    gender_summary = analysis_results.get("by_gender", [])
    total_n = sum(g.get("n", 0) for g in gender_summary if isinstance(g.get("n"), (int, float)))
    
    if total_n == 0:
        return gaps
    
    # Check for significant representation imbalances (>60% in one group)
    for gender_info in gender_summary:
        gender = gender_info.get("gender", "")
        n = gender_info.get("n", 0)
        pct = gender_info.get("pct", 0)
        
        if isinstance(n, str) or isinstance(pct, str):
            continue
            
        if pct > 60:
            gaps.append({
                "type": "representation_imbalance",
                "gender": gender,
                "percentage": pct,
                "interpretation": f"{gender.capitalize()} participants represent {pct:.1f}% of the sample, indicating potential sampling bias or population characteristics that may limit generalizability."
            })
    
    # Check categorical variables for representation gaps
    for var_result in analysis_results.get("categorical", []):
        var_name = var_result["var"]
        table = var_result.get("table", [])
        
        # Group by level and check distribution
        level_gender_counts = {}
        for row in table:
            level = row.get("level", "")
            gender = row.get("gender", "")
            n = row.get("n", 0)
            
            if isinstance(n, str):
                continue
                
            if level not in level_gender_counts:
                level_gender_counts[level] = {}
            level_gender_counts[level][gender] = n
        
        # Check for levels with significant gender gaps (>20 percentage points)
        for level, gender_counts in level_gender_counts.items():
            total_level = sum(gender_counts.values())
            if total_level == 0:
                continue
                
            for gender, count in gender_counts.items():
                pct = (count / total_level) * 100
                # Check if this gender is over/under-represented
                if pct > 70:
                    gaps.append({
                        "type": "level_representation",
                        "variable": var_name,
                        "level": level,
                        "gender": gender,
                        "percentage": pct,
                        "interpretation": f"In {var_name}, the level '{level}' shows {gender.capitalize()} representation of {pct:.1f}%, indicating potential gender-based differences in this category."
                    })
    
    return gaps


def _assess_missing_data_bias(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Assess missing data patterns for gender bias"""
    
    bias_findings = []
    missingness = analysis_results.get("missingness", [])
    
    # Group missing data by variable
    var_missing = {}
    for missing in missingness:
        var = missing.get("var", "")
        gender = missing.get("gender", "")
        missing_pct = missing.get("missing_pct", 0)
        
        if isinstance(missing_pct, str):
            continue
            
        if var not in var_missing:
            var_missing[var] = {}
        var_missing[var][gender] = missing_pct
    
    # Check for differential missingness (>10 percentage point difference)
    for var, gender_missing in var_missing.items():
        if len(gender_missing) < 2:
            continue
            
        missing_values = [v for v in gender_missing.values() if isinstance(v, (int, float))]
        if len(missing_values) < 2:
            continue
            
        max_missing = max(missing_values)
        min_missing = min(missing_values)
        diff = max_missing - min_missing
        
        if diff > 10:
            # Find which gender has more missing data
            max_gender = max(gender_missing.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)
            bias_findings.append({
                "variable": var,
                "max_missing_gender": max_gender[0],
                "max_missing_pct": max_gender[1],
                "min_missing_pct": min_missing,
                "difference": diff,
                "interpretation": f"Differential missing data pattern in {var}: {max_gender[0].capitalize()} group has {max_gender[1]:.1f}% missing data compared to {min_missing:.1f}% in other groups. This {diff:.1f} percentage point difference may indicate systematic data collection or response patterns that could introduce bias."
            })
    
    return bias_findings


def _assess_practical_significance(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Assess practical significance of differences"""
    
    practical_findings = []
    
    # Check continuous variables for meaningful differences
    for var_result in analysis_results.get("continuous", []):
        var_name = var_result["var"]
        table = var_result.get("table", [])
        effects = var_result.get("effects", [])
        
        # Get means by gender
        means = {}
        for stat in table:
            gender = stat.get("gender", "")
            mean_val = stat.get("mean", None)
            if isinstance(mean_val, (int, float)):
                means[gender] = mean_val
        
        if len(means) < 2:
            continue
            
        # Calculate relative difference
        mean_values = list(means.values())
        max_mean = max(mean_values)
        min_mean = min(mean_values)
        
        if min_mean != 0:
            relative_diff = ((max_mean - min_mean) / abs(min_mean)) * 100
            if relative_diff > 20:  # >20% relative difference
                practical_findings.append({
                    "variable": var_name,
                    "type": "continuous",
                    "relative_difference": relative_diff,
                    "interpretation": f"Substantial practical difference in {var_name}: {relative_diff:.1f}% relative difference between gender groups. This may have meaningful implications for policy or programmatic interventions."
                })
    
    return practical_findings


def _generate_recommendations(bias_assessment: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on bias assessment"""
    
    recommendations = []
    
    # Recommendations based on statistical disparities
    if bias_assessment["statistical_disparities"]:
        large_disparities = [d for d in bias_assessment["statistical_disparities"] if d.get("severity") == "large"]
        if large_disparities:
            recommendations.append(
                "Consider conducting intersectional analysis to understand how gender interacts with other social determinants (e.g., age, education, socioeconomic status) to produce observed differences."
            )
            recommendations.append(
                "Engage with affected communities to understand the root causes of observed gender differences and co-design interventions that address structural barriers."
            )
    
    # Recommendations based on representation gaps
    if bias_assessment["representation_gaps"]:
        recommendations.append(
            "Review sampling and recruitment strategies to ensure equitable representation across gender groups, particularly for underrepresented populations."
        )
    
    # Recommendations based on missing data
    if bias_assessment["missing_data_bias"]:
        recommendations.append(
            "Investigate reasons for differential missing data patterns and implement strategies to improve data collection completeness across all gender groups."
        )
    
    # General recommendations
    recommendations.append(
        "Use gender-transformative approaches that address root causes of gender inequality rather than focusing solely on individual-level differences."
    )
    recommendations.append(
        "Consider power dynamics, social norms, and structural barriers that may contribute to observed patterns, beyond statistical associations."
    )
    recommendations.append(
        "Ensure data collection and analysis processes are inclusive and respect diverse gender identities and expressions."
    )
    
    return recommendations


def _generate_gender_transformative_insights(
    bias_assessment: Dict[str, Any],
    analysis_results: Dict[str, Any]
) -> List[str]:
    """Generate insights using gender transformative frameworks"""
    
    insights = []
    
    # Count significant findings
    num_disparities = len(bias_assessment["statistical_disparities"])
    num_gaps = len(bias_assessment["representation_gaps"])
    
    if num_disparities > 0:
        insights.append(
            f"The analysis identified {num_disparities} variable(s) with statistically significant gender differences. "
            "These differences may reflect structural inequalities, social norms, or differential access to resources and opportunities. "
            "A gender-transformative approach would examine the underlying power relations and systemic barriers that produce these patterns."
        )
    
    if num_gaps > 0:
        insights.append(
            f"Representation gaps were identified in {num_gaps} area(s), suggesting potential sampling biases or population characteristics. "
            "These gaps may limit the generalizability of findings and should be addressed through inclusive data collection strategies."
        )
    
    # Check for patterns
    continuous_vars = len(analysis_results.get("continuous", []))
    categorical_vars = len(analysis_results.get("categorical", []))
    
    if continuous_vars > 0 or categorical_vars > 0:
        insights.append(
            "Gender analysis requires moving beyond descriptive statistics to understand the social, economic, and political contexts "
            "that shape gender relations. Consider complementing quantitative findings with qualitative research to understand lived experiences "
            "and the mechanisms through which gender differences emerge."
        )
    
    insights.append(
        "Gender-transformative analysis recognizes that gender is not a binary construct and that individuals may experience multiple "
        "forms of discrimination and privilege simultaneously. Intersectional approaches are essential for comprehensive understanding."
    )
    
    return insights


def _generate_overall_summary(bias_assessment: Dict[str, Any]) -> str:
    """Generate overall summary of gender bias assessment"""
    
    num_disparities = len(bias_assessment["statistical_disparities"])
    num_gaps = len(bias_assessment["representation_gaps"])
    num_missing_bias = len(bias_assessment["missing_data_bias"])
    num_practical = len(bias_assessment["practical_significance"])
    
    summary_parts = []
    
    if num_disparities == 0 and num_gaps == 0 and num_missing_bias == 0:
        summary_parts.append(
            "The analysis did not identify significant gender-based statistical disparities, representation gaps, or missing data bias. "
        )
    else:
        if num_disparities > 0:
            summary_parts.append(
                f"{num_disparities} variable(s) showed statistically significant gender differences. "
            )
        if num_gaps > 0:
            summary_parts.append(
                f"{num_gaps} representation gap(s) were identified. "
            )
        if num_missing_bias > 0:
            summary_parts.append(
                f"{num_missing_bias} variable(s) showed differential missing data patterns by gender. "
            )
    
    if num_practical > 0:
        summary_parts.append(
            f"{num_practical} variable(s) showed substantial practical differences (>20% relative difference) that may warrant programmatic attention. "
        )
    
    summary_parts.append(
        "These findings should be interpreted within the broader social, economic, and political context, "
        "using gender-transformative approaches that address root causes of inequality."
    )
    
    return "".join(summary_parts)

