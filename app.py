import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import mannwhitneyu, chi2_contingency

# Set page config
st.set_page_config(
    page_title="Health Data Analysis",
    page_icon="🏥",
    layout="wide"
)

# Add title and description
st.title("Health Data Analysis Dashboard")
st.markdown("""
This dashboard analyzes health outcomes, barriers to care, and chronic conditions by gender, region, and education level.
Use the sidebar to customize the visualization and analysis.
""")

# Read and prepare data
@st.cache_data
def load_data():
    health_df = pd.read_csv('health_data.csv')
    demo_df = pd.read_csv('demographics.csv')
    
    # Clean and merge datasets
    health_df = health_df.drop_duplicates(subset=['id'])
    demo_df = demo_df.drop_duplicates(subset=['id'])
    
    # Merge datasets
    merged_df = pd.merge(health_df, demo_df, on='id', how='inner')
    
    # Map categorical variables
    merged_df['gender'] = merged_df['gender'].map({1: 'Female', 2: 'Male'})
    merged_df['region'] = merged_df['region'].map({1: 'North', 2: 'Central', 3: 'South'})
    merged_df['education_level'] = merged_df['education_level'].map({1: 'None', 2: 'Primary', 3: 'Secondary', 4: 'Tertiary'})
    return merged_df

# Load data
df = load_data()

# Sidebar controls
st.sidebar.header("Analysis Controls")

# Select analysis type
analysis_type = st.sidebar.selectbox(
    "Select Analysis Type",
    [
        "Health Check Distribution",
        "Barriers to Care",
        "Chronic Conditions by Gender",
        "Chronic Conditions by Region",
        "Chronic Conditions by Education Level"
    ]
)

def perform_statistical_test(data1, data2, variable_name):
    data1 = data1.dropna()
    data2 = data2.dropna()
    _, p1 = stats.normaltest(data1)
    _, p2 = stats.normaltest(data2)
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

def perform_chi_square_test(contingency_table):
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    return {
        'chi2': chi2,
        'p_value': p_value,
        'dof': dof
    }

# Main content area
if analysis_type == "Health Check Distribution":
    st.header("1. Health Check Distribution")
    st.sidebar.header("Filters")
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        options=df['gender'].dropna().unique(),
        default=df['gender'].dropna().unique()
    )
    filtered_df = df[df['gender'].isin(selected_gender)]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=filtered_df, x='gender', y='recent_health_check', palette='Set2')
    plt.title('Distribution of Recent Health Checks by Gender')
    plt.xlabel('Gender')
    plt.ylabel('Months Since Last Health Check')
    st.pyplot(fig)
    plt.close()
    stats_df = filtered_df.groupby('gender')['recent_health_check'].agg(['mean', 'std', 'median', 'count']).round(2)
    st.write("Summary Statistics:")
    st.dataframe(stats_df)
    male_data = filtered_df[filtered_df['gender'] == 'Male']['recent_health_check']
    female_data = filtered_df[filtered_df['gender'] == 'Female']['recent_health_check']
    test_result = perform_statistical_test(male_data, female_data, 'recent_health_check')
    st.write("Statistical Test Results:")
    st.write(f"Test Type: {test_result['test_type']}")
    st.write(f"Statistic: {test_result['statistic']:.4f}")
    st.write(f"p-value: {test_result['p_value']:.4f}")
    if 'Male' in stats_df.index and 'Female' in stats_df.index:
        male_mean = stats_df.loc['Male', 'mean']
        female_mean = stats_df.loc['Female', 'mean']
        st.write(f"""
        **Analysis:** On average, males had {male_mean:.1f} months since their last health check, 
        while females had {female_mean:.1f} months. The statistical test (p-value: {test_result['p_value']:.4f}) 
        suggests that this difference is {'not ' if test_result['p_value'] > 0.05 else ''}statistically significant.
        """)

elif analysis_type == "Barriers to Care":
    st.header("2. Barriers to Care Analysis")
    st.sidebar.header("Filters")
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        options=df['gender'].dropna().unique(),
        default=df['gender'].dropna().unique()
    )
    filtered_df = df[df['gender'].isin(selected_gender)]
    barriers_by_gender = pd.crosstab(filtered_df['gender'], filtered_df['reported_barriers_to_care'])
    barriers_percent = pd.crosstab(filtered_df['gender'], filtered_df['reported_barriers_to_care'], normalize='index') * 100
    chi2_result = perform_chi_square_test(barriers_by_gender)
    fig, ax = plt.subplots(figsize=(12, 6))
    barriers_percent.plot(kind='bar', ax=ax)
    plt.title('Reported Barriers to Care by Gender (Percentage)')
    plt.xlabel('Barriers to Care')
    plt.ylabel('Percentage')
    plt.legend(title='Gender', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.write("Barriers to Care Percentages:")
    st.dataframe(barriers_percent.round(1))
    st.write("Chi-Square Test Results:")
    st.write(f"Chi-square statistic: {chi2_result['chi2']:.4f}")
    st.write(f"p-value: {chi2_result['p_value']:.4f}")
    st.write(f"Degrees of freedom: {chi2_result['dof']}")
    st.write("**Analysis by Barrier:**")
    for barrier in barriers_percent.columns:
        if 'Male' in barriers_percent.index and 'Female' in barriers_percent.index:
            male_pct = barriers_percent.loc['Male', barrier]
            female_pct = barriers_percent.loc['Female', barrier]
            st.write(f"""
            - **{barrier}:** {female_pct:.1f}% of females reported {barrier} as a barrier, 
            compared to {male_pct:.1f}% of males. The chi-square test (p-value: {chi2_result['p_value']:.4f}) 
            indicates that this difference is {'not ' if chi2_result['p_value'] > 0.05 else ''}statistically significant.
            """)

elif analysis_type == "Chronic Conditions by Gender":
    st.header("3. Chronic Conditions by Gender")
    st.sidebar.header("Filters")
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        options=df['gender'].dropna().unique(),
        default=df['gender'].dropna().unique()
    )
    filtered_df = df[df['gender'].isin(selected_gender)]
    conditions_by_gender = pd.crosstab(filtered_df['gender'], filtered_df['chronic_condition'])
    conditions_percent = pd.crosstab(filtered_df['gender'], filtered_df['chronic_condition'], normalize='index') * 100
    chi2_result = perform_chi_square_test(conditions_by_gender)
    fig, ax = plt.subplots(figsize=(12, 6))
    conditions_percent.plot(kind='bar', ax=ax)
    plt.title('Chronic Conditions by Gender (Percentage)')
    plt.xlabel('Chronic Condition')
    plt.ylabel('Percentage')
    plt.legend(title='Gender', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.write("Chronic Conditions Percentages:")
    st.dataframe(conditions_percent.round(1))
    st.write("Chi-Square Test Results:")
    st.write(f"Chi-square statistic: {chi2_result['chi2']:.4f}")
    st.write(f"p-value: {chi2_result['p_value']:.4f}")
    st.write(f"Degrees of freedom: {chi2_result['dof']}")
    st.write("**Analysis by Condition:**")
    for condition in conditions_percent.columns:
        if 'Male' in conditions_percent.index and 'Female' in conditions_percent.index:
            male_pct = conditions_percent.loc['Male', condition]
            female_pct = conditions_percent.loc['Female', condition]
            st.write(f"""
            - **{condition}:** {female_pct:.1f}% of females reported {condition}, 
            compared to {male_pct:.1f}% of males. The chi-square test (p-value: {chi2_result['p_value']:.4f}) 
            indicates that this difference is {'not ' if chi2_result['p_value'] > 0.05 else ''}statistically significant.
            """)

elif analysis_type == "Chronic Conditions by Region":
    st.header("4. Chronic Conditions by Region")
    st.sidebar.header("Filters")
    selected_region = st.sidebar.multiselect(
        "Select Region",
        options=df['region'].dropna().unique(),
        default=df['region'].dropna().unique()
    )
    filtered_df = df[df['region'].isin(selected_region)]
    conditions_by_region = pd.crosstab(filtered_df['region'], filtered_df['chronic_condition'])
    conditions_percent = pd.crosstab(filtered_df['region'], filtered_df['chronic_condition'], normalize='index') * 100
    chi2_result = perform_chi_square_test(conditions_by_region)
    fig, ax = plt.subplots(figsize=(12, 6))
    conditions_percent.plot(kind='bar', ax=ax)
    plt.title('Chronic Conditions by Region (Percentage)')
    plt.xlabel('Chronic Condition')
    plt.ylabel('Percentage')
    plt.legend(title='Region', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.write("Chronic Conditions Percentages:")
    st.dataframe(conditions_percent.round(1))
    st.write("Chi-Square Test Results:")
    st.write(f"Chi-square statistic: {chi2_result['chi2']:.4f}")
    st.write(f"p-value: {chi2_result['p_value']:.4f}")
    st.write(f"Degrees of freedom: {chi2_result['dof']}")
    st.write("**Analysis by Condition:**")
    for condition in conditions_percent.columns:
        for region in conditions_percent.index:
            pct = conditions_percent.loc[region, condition]
            st.write(f"- **{condition} in {region}:** {pct:.1f}% of respondents in {region} reported {condition}.")
    st.write(f"The chi-square test (p-value: {chi2_result['p_value']:.4f}) indicates that differences by region are {'not ' if chi2_result['p_value'] > 0.05 else ''}statistically significant.")

elif analysis_type == "Chronic Conditions by Education Level":
    st.header("5. Chronic Conditions by Education Level")
    st.sidebar.header("Filters")
    selected_edu = st.sidebar.multiselect(
        "Select Education Level",
        options=df['education_level'].dropna().unique(),
        default=df['education_level'].dropna().unique()
    )
    filtered_df = df[df['education_level'].isin(selected_edu)]
    conditions_by_edu = pd.crosstab(filtered_df['education_level'], filtered_df['chronic_condition'])
    conditions_percent = pd.crosstab(filtered_df['education_level'], filtered_df['chronic_condition'], normalize='index') * 100
    chi2_result = perform_chi_square_test(conditions_by_edu)
    fig, ax = plt.subplots(figsize=(12, 6))
    conditions_percent.plot(kind='bar', ax=ax)
    plt.title('Chronic Conditions by Education Level (Percentage)')
    plt.xlabel('Chronic Condition')
    plt.ylabel('Percentage')
    plt.legend(title='Education Level', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    st.write("Chronic Conditions Percentages:")
    st.dataframe(conditions_percent.round(1))
    st.write("Chi-Square Test Results:")
    st.write(f"Chi-square statistic: {chi2_result['chi2']:.4f}")
    st.write(f"p-value: {chi2_result['p_value']:.4f}")
    st.write(f"Degrees of freedom: {chi2_result['dof']}")
    st.write("**Analysis by Condition:**")
    for condition in conditions_percent.columns:
        for edu in conditions_percent.index:
            pct = conditions_percent.loc[edu, condition]
            st.write(f"- **{condition} for {edu}:** {pct:.1f}% of respondents with {edu} education reported {condition}.")
    st.write(f"The chi-square test (p-value: {chi2_result['p_value']:.4f}) indicates that differences by education level are {'not ' if chi2_result['p_value'] > 0.05 else ''}statistically significant.")

# Add footer with data information
st.sidebar.markdown("---")
st.sidebar.markdown("""
### Data Information
- Health Check: Months since last health check
- Barriers to Care: Reported obstacles to healthcare access
- Chronic Conditions: Reported chronic health conditions
- Region: 1=North, 2=Central, 3=South
- Education Level: 1=None, 2=Primary, 3=Secondary, 4=Tertiary
- Gender: 1=Female, 2=Male
""")

# Key Findings
st.header("Key Findings")
st.write("""
1. **Health Check Patterns:** The analysis reveals differences in health check frequency between genders, with detailed statistical significance.
2. **Barriers to Care:** The data shows distinct patterns in reported barriers between males and females, with specific percentages and statistical tests for each barrier type.
3. **Chronic Conditions:** The prevalence of different chronic conditions varies by gender, region, and education level, with detailed breakdowns and statistical significance for each.
""") 