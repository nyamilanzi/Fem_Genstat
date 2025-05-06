# Fem_Genstat
---

# Gender Health Data Analysis Dashboard

This project provides a comprehensive analysis of health outcomes, barriers to care, and chronic conditions using survey data. The analysis is performed using Python, with interactive visualizations and statistical tests available via a Streamlit web app.

## Features

- **Data Merging & Cleaning:** Combines health and demographic data, applies correct label mappings.
- **Statistical Analysis:**  
  - Health check frequency by gender  
  - Barriers to care by gender  
  - Chronic conditions by gender, region, and education level  
  - Statistical significance testing (t-test, Mann-Whitney U, Chi-square)
- **Interactive Dashboard:**  
  - Built with Streamlit  
  - Filter by gender, region, and education level  
  - Visualize distributions and group differences
- **Automated PDF Reporting:**  
  - Generates a professional PDF report with summary statistics, plots, and narratives

## Data

- `health_data.csv`: Contains health check, barriers to care, and chronic condition data.
- `demographics.csv`: Contains gender, age, region, and education level data.

### Label Mappings

- **Gender:** 1 = Female, 2 = Male
- **Region:** 1 = North, 2 = Central, 3 = South
- **Education Level:** 1 = None, 2 = Primary, 3 = Secondary, 4 = Tertiary
