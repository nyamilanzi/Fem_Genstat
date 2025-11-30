"""
Unit tests for backend services
"""

import pytest
import pandas as pd
import numpy as np
from services.load import infer_variable_type, get_sample_values, identify_gender_candidates
from services.summarize import apply_gender_mapping, handle_missing_data
from services.test_select import select_continuous_test, select_categorical_test
from services.effects import calculate_continuous_effect_sizes, calculate_categorical_effect_sizes
from services.fdr import apply_fdr_correction

class TestLoadServices:
    def test_infer_variable_type(self):
        # Test continuous
        continuous_series = pd.Series([1, 2, 3, 4, 5])
        assert infer_variable_type(continuous_series) == 'continuous'
        
        # Test categorical
        categorical_series = pd.Series(['A', 'B', 'A', 'C'])
        assert infer_variable_type(categorical_series) == 'categorical'
        
        # Test boolean
        boolean_series = pd.Series([True, False, True])
        assert infer_variable_type(boolean_series) == 'boolean'
    
    def test_get_sample_values(self):
        series = pd.Series([1, 2, 3, 4, 5, 1, 2])
        sample_values = get_sample_values(series, max_values=3)
        assert len(sample_values) <= 3
        assert all(isinstance(v, (int, float)) for v in sample_values)
    
    def test_identify_gender_candidates(self):
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'gender': ['M', 'F', 'M'],
            'age': [25, 30, 35],
            'sex_variable': ['Male', 'Female', 'Male']
        })
        candidates = identify_gender_candidates(df)
        assert 'gender' in candidates
        assert 'sex_variable' in candidates
        assert 'id' not in candidates
        assert 'age' not in candidates

class TestSummarizeServices:
    def test_apply_gender_mapping(self):
        df = pd.DataFrame({
            'gender': ['M', 'F', 'M', 'Other'],
            'age': [25, 30, 35, 40]
        })
        gender_map = [
            {'from_value': 'M', 'to_value': 'male'},
            {'from_value': 'F', 'to_value': 'female'},
            {'from_value': 'Other', 'to_value': 'other'}
        ]
        
        result = apply_gender_mapping(df, 'gender', gender_map)
        expected_values = ['male', 'female', 'male', 'other']
        assert result['gender'].tolist() == expected_values
    
    def test_handle_missing_data(self):
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4],
            'B': [1, np.nan, 3, 4],
            'C': [1, 2, 3, 4]
        })
        
        # Test listwise deletion
        result_listwise = handle_missing_data(df, 'listwise')
        assert len(result_listwise) == 1  # Only row 3 has no missing values
        
        # Test pairwise (keep all)
        result_pairwise = handle_missing_data(df, 'pairwise')
        assert len(result_pairwise) == 4

class TestTestSelectServices:
    def test_select_continuous_test(self):
        df = pd.DataFrame({
            'var': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'gender': ['M', 'M', 'M', 'M', 'M', 'F', 'F', 'F', 'F', 'F']
        })
        
        test_name, test_result = select_continuous_test(df, 'var', 'gender', ['M', 'F'])
        assert test_name in ['welch_ttest', 'mann_whitney']
        assert 'p' in test_result
        assert 'statistic' in test_result
    
    def test_select_categorical_test(self):
        df = pd.DataFrame({
            'var': ['A', 'A', 'B', 'B', 'A', 'B'],
            'gender': ['M', 'M', 'M', 'F', 'F', 'F']
        })
        
        test_name, test_result = select_categorical_test(df, 'var', 'gender', ['M', 'F'])
        assert test_name in ['chi_square', 'fisher_exact']
        assert 'p' in test_result
        assert 'statistic' in test_result

class TestEffectServices:
    def test_calculate_continuous_effect_sizes(self):
        df = pd.DataFrame({
            'var': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'gender': ['M', 'M', 'M', 'M', 'M', 'F', 'F', 'F', 'F', 'F']
        })
        
        effects = calculate_continuous_effect_sizes(df, 'var', 'gender', ['M', 'F'], 'welch_ttest')
        assert len(effects) > 0
        assert all('name' in effect for effect in effects)
        assert all('value' in effect for effect in effects)
    
    def test_calculate_categorical_effect_sizes(self):
        df = pd.DataFrame({
            'var': ['A', 'A', 'B', 'B', 'A', 'B'],
            'gender': ['M', 'M', 'M', 'F', 'F', 'F']
        })
        
        effects = calculate_categorical_effect_sizes(df, 'var', 'gender', ['M', 'F'], 'chi_square')
        assert len(effects) > 0
        assert all('name' in effect for effect in effects)
        assert all('value' in effect for effect in effects)

class TestFDRServices:
    def test_apply_fdr_correction(self):
        p_values = [0.01, 0.05, 0.1, 0.2, 0.5]
        corrected = apply_fdr_correction(p_values, 'BH')
        
        assert len(corrected) == len(p_values)
        assert all(0 <= p <= 1 for p in corrected if p is not None)
        # FDR correction should generally increase p-values
        assert all(corrected[i] >= p_values[i] for i in range(len(p_values)) if corrected[i] is not None)

