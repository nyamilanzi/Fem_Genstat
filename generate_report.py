import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import mannwhitneyu, chi2_contingency
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime

def load_data():
    health_df = pd.read_csv('health_data.csv')
    demo_df = pd.read_csv('demographics.csv')
    
    health_df = health_df.drop_duplicates(subset=['id'])
    demo_df = demo_df.drop_duplicates(subset=['id'])
    
    merged_df = pd.merge(health_df, demo_df, on='id', how='inner')
    merged_df['gender'] = merged_df['gender'].map({1: 'Male', 2: 'Female'})
    return merged_df

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

def create_plot(fig):
    imgdata = io.BytesIO()
    fig.savefig(imgdata, format='png', dpi=300, bbox_inches='tight')
    imgdata.seek(0)
    return Image(imgdata, width=6*inch, height=4*inch)

def generate_report():
    # Load data
    df = load_data()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        "health_analysis_report.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    # Content
    story = []
    
    # Title
    story.append(Paragraph("Health Data Analysis Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph("""
    This report presents a comprehensive analysis of health outcomes, barriers to care, and chronic conditions 
    by gender. The analysis includes statistical tests, visualizations, and detailed breakdowns of key metrics.
    """, body_style))
    story.append(Spacer(1, 20))
    
    # Health Check Distribution
    story.append(Paragraph("1. Health Check Distribution Analysis", heading_style))
    
    # Create violin plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=df, x='gender', y='recent_health_check', palette='Set2')
    plt.title('Distribution of Recent Health Checks by Gender')
    plt.xlabel('Gender')
    plt.ylabel('Months Since Last Health Check')
    story.append(create_plot(fig))
    plt.close()
    
    # Summary statistics
    stats_df = df.groupby('gender')['recent_health_check'].agg(['mean', 'std', 'median', 'count']).round(2)
    stats_data = [['Gender', 'Mean', 'Std Dev', 'Median', 'Count']]
    for gender in stats_df.index:
        stats_data.append([gender] + [str(x) for x in stats_df.loc[gender]])
    
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Statistical test results for health checks
    male_data = df[df['gender'] == 'Male']['recent_health_check']
    female_data = df[df['gender'] == 'Female']['recent_health_check']
    test_result = perform_statistical_test(male_data, female_data, 'recent_health_check')
    
    story.append(Paragraph("Statistical Test Results:", body_style))
    story.append(Paragraph(f"Test Type: {test_result['test_type']}", body_style))
    story.append(Paragraph(f"Statistic: {test_result['statistic']:.4f}", body_style))
    story.append(Paragraph(f"p-value: {test_result['p_value']:.4f}", body_style))
    story.append(Spacer(1, 20))
    
    # Barriers to Care
    story.append(Paragraph("2. Barriers to Care Analysis", heading_style))
    
    # Calculate percentages and create contingency table
    barriers_by_gender = pd.crosstab(df['gender'], df['reported_barriers_to_care'])
    barriers_percent = pd.crosstab(df['gender'], df['reported_barriers_to_care'], normalize='index') * 100
    
    # Perform chi-square test
    chi2_result = perform_chi_square_test(barriers_by_gender)
    
    # Create bar plot
    fig, ax = plt.subplots(figsize=(12, 6))
    barriers_percent.plot(kind='bar', ax=ax)
    plt.title('Reported Barriers to Care by Gender (Percentage)')
    plt.xlabel('Barriers to Care')
    plt.ylabel('Percentage')
    plt.legend(title='Gender', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    story.append(create_plot(fig))
    plt.close()
    
    # Add barriers table
    barriers_data = [['Barrier'] + list(barriers_percent.index)]
    for barrier in barriers_percent.columns:
        barriers_data.append([barrier] + [f"{x:.1f}%" for x in barriers_percent[barrier]])
    
    barriers_table = Table(barriers_data)
    barriers_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(barriers_table)
    
    # Add chi-square test results
    story.append(Paragraph("Chi-Square Test Results:", body_style))
    story.append(Paragraph(f"Chi-square statistic: {chi2_result['chi2']:.4f}", body_style))
    story.append(Paragraph(f"p-value: {chi2_result['p_value']:.4f}", body_style))
    story.append(Paragraph(f"Degrees of freedom: {chi2_result['dof']}", body_style))
    story.append(Spacer(1, 20))
    
    # Chronic Conditions
    story.append(Paragraph("3. Chronic Conditions Analysis", heading_style))
    
    # Calculate percentages and create contingency table
    conditions_by_gender = pd.crosstab(df['gender'], df['chronic_condition'])
    conditions_percent = pd.crosstab(df['gender'], df['chronic_condition'], normalize='index') * 100
    
    # Perform chi-square test
    chi2_result_conditions = perform_chi_square_test(conditions_by_gender)
    
    # Create bar plot
    fig, ax = plt.subplots(figsize=(12, 6))
    conditions_percent.plot(kind='bar', ax=ax)
    plt.title('Chronic Conditions by Gender (Percentage)')
    plt.xlabel('Chronic Condition')
    plt.ylabel('Percentage')
    plt.legend(title='Gender', bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    story.append(create_plot(fig))
    plt.close()
    
    # Add conditions table
    conditions_data = [['Condition'] + list(conditions_percent.index)]
    for condition in conditions_percent.columns:
        conditions_data.append([condition] + [f"{x:.1f}%" for x in conditions_percent[condition]])
    
    conditions_table = Table(conditions_data)
    conditions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(conditions_table)
    
    # Add chi-square test results
    story.append(Paragraph("Chi-Square Test Results:", body_style))
    story.append(Paragraph(f"Chi-square statistic: {chi2_result_conditions['chi2']:.4f}", body_style))
    story.append(Paragraph(f"p-value: {chi2_result_conditions['p_value']:.4f}", body_style))
    story.append(Paragraph(f"Degrees of freedom: {chi2_result_conditions['dof']}", body_style))
    story.append(Spacer(1, 20))
    
    # Conclusions with detailed narrative
    story.append(Paragraph("Conclusions", heading_style))
    
    # Generate detailed narrative for each condition
    narrative = []
    
    # Health Check narrative
    male_mean = stats_df.loc['Male', 'mean']
    female_mean = stats_df.loc['Female', 'mean']
    narrative.append(f"""
    1. Health Check Distribution: On average, males had {male_mean:.1f} months since their last health check, 
    while females had {female_mean:.1f} months. The statistical test (p-value: {test_result['p_value']:.4f}) 
    suggests that this difference is {'not ' if test_result['p_value'] > 0.05 else ''}statistically significant.
    """)
    
    # Barriers to Care narrative
    for barrier in barriers_percent.columns:
        male_pct = barriers_percent.loc['Male', barrier]
        female_pct = barriers_percent.loc['Female', barrier]
        narrative.append(f"""
    2. Barriers to Care - {barrier}: {female_pct:.1f}% of females reported {barrier} as a barrier, 
    compared to {male_pct:.1f}% of males. The chi-square test (p-value: {chi2_result['p_value']:.4f}) 
    indicates that this difference is {'not ' if chi2_result['p_value'] > 0.05 else ''}statistically significant.
    """)
    
    # Chronic Conditions narrative
    for condition in conditions_percent.columns:
        male_pct = conditions_percent.loc['Male', condition]
        female_pct = conditions_percent.loc['Female', condition]
        narrative.append(f"""
    3. Chronic Conditions - {condition}: {female_pct:.1f}% of females reported {condition}, 
    compared to {male_pct:.1f}% of males. The chi-square test (p-value: {chi2_result_conditions['p_value']:.4f}) 
    indicates that this difference is {'not ' if chi2_result_conditions['p_value'] > 0.05 else ''}statistically significant.
    """)
    
    story.append(Paragraph("".join(narrative), body_style))
    
    # Build PDF
    doc.build(story)

if __name__ == "__main__":
    generate_report() 