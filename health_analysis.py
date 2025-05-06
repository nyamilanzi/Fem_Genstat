import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import mannwhitneyu
import warnings
warnings.filterwarnings('ignore')

# Set the style for all plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = [10, 6]

# Read the datasets
health_df = pd.read_csv('health_data.csv')
demo_df = pd.read_csv('demographics.csv')

# Clean and merge datasets
# Remove duplicate IDs
health_df = health_df.drop_duplicates(subset=['id'])
demo_df = demo_df.drop_duplicates(subset=['id'])

# Merge datasets
merged_df = pd.merge(health_df, demo_df, on='id', how='inner')

# Convert gender to categorical
merged_df['gender'] = merged_df['gender'].map({1: 'Male', 2: 'Female'})

# Function to test normality and perform appropriate statistical test
def perform_statistical_test(data1, data2, variable_name):
    # Remove NaN values
    data1 = data1.dropna()
    data2 = data2.dropna()
    
    # Test for normality
    _, p1 = stats.normaltest(data1)
    _, p2 = stats.normaltest(data2)
    
    # If either group is not normally distributed, use Mann-Whitney U test
    if p1 < 0.05 or p2 < 0.05:
        stat, pval = mannwhitneyu(data1, data2, alternative='two-sided')
        test_type = 'Mann-Whitney U'
    else:
        stat, pval = stats.ttest_ind(data1, data2)
        test_type = 't-test'
    
    return {
        'variable': variable_name,
        'test_type': test_type,
        'statistic': stat,
        'p_value': pval
    }

# Perform statistical tests
test_results = []
for variable in ['recent_health_check']:
    male_data = merged_df[merged_df['gender'] == 'Male'][variable]
    female_data = merged_df[merged_df['gender'] == 'Female'][variable]
    test_results.append(perform_statistical_test(male_data, female_data, variable))

# 1. Health Check Distribution
plt.figure(figsize=(10, 6))
sns.violinplot(data=merged_df, x='gender', y='recent_health_check', palette='Set2')
plt.title('Distribution of Recent Health Checks by Gender', pad=20, fontsize=12)
plt.xlabel('Gender', fontsize=10)
plt.ylabel('Months Since Last Health Check', fontsize=10)
plt.tight_layout()
plt.savefig('health_checks_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Barriers to Care
plt.figure(figsize=(12, 6))
barriers_by_gender = pd.crosstab(merged_df['gender'], merged_df['reported_barriers_to_care'], normalize='index') * 100

# Plot each barrier type separately
for barrier in barriers_by_gender.columns:
    plt.bar(np.arange(len(barriers_by_gender.index)) + barriers_by_gender.columns.get_loc(barrier) * 0.15,
            barriers_by_gender[barrier],
            width=0.15,
            label=barrier)

plt.title('Reported Barriers to Care by Gender (Percentage)', pad=20, fontsize=12)
plt.xlabel('Gender', fontsize=10)
plt.ylabel('Percentage', fontsize=10)
plt.xticks(np.arange(len(barriers_by_gender.index)), barriers_by_gender.index)
plt.legend(title='Barriers to Care', bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig('barriers_to_care.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Chronic Conditions
plt.figure(figsize=(12, 6))
conditions_by_gender = pd.crosstab(merged_df['gender'], merged_df['chronic_condition'], normalize='index') * 100

# Plot each condition type separately
for condition in conditions_by_gender.columns:
    plt.bar(np.arange(len(conditions_by_gender.index)) + conditions_by_gender.columns.get_loc(condition) * 0.25,
            conditions_by_gender[condition],
            width=0.25,
            label=condition)

plt.title('Chronic Conditions by Gender (Percentage)', pad=20, fontsize=12)
plt.xlabel('Gender', fontsize=10)
plt.ylabel('Percentage', fontsize=10)
plt.xticks(np.arange(len(conditions_by_gender.index)), conditions_by_gender.index)
plt.legend(title='Chronic Condition', bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.savefig('chronic_conditions.png', dpi=300, bbox_inches='tight')
plt.close()

# Generate summary statistics
summary_stats = merged_df.groupby('gender').agg({
    'recent_health_check': ['mean', 'std', 'median', 'count'],
    'reported_barriers_to_care': lambda x: x.value_counts(normalize=True).to_dict(),
    'chronic_condition': lambda x: x.value_counts(normalize=True).to_dict()
}).round(2)

# Save summary statistics to CSV
summary_stats.to_csv('health_analysis_summary.csv')

# Print statistical test results
print("\nStatistical Test Results:")
for result in test_results:
    print(f"\n{result['variable']}:")
    print(f"Test Type: {result['test_type']}")
    print(f"Statistic: {result['statistic']:.4f}")
    print(f"p-value: {result['p_value']:.4f}") 