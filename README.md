# Gender Analysis Tool

A production-ready web application for gender-stratified descriptive analysis with statistical tests and effect sizes. This tool enables researchers to perform comprehensive gender-based statistical analysis with privacy protection and professional reporting capabilities.

## Features

### Data Processing
- **Multi-format Support**: Upload CSV, Excel (.xlsx, .xls), SPSS (.sav), Stata (.dta), and Parquet files
- **Smart Schema Inference**: Automatic variable type detection and gender candidate identification
- **Data Validation**: File size limits (50MB), format validation, and data quality checks
- **Gender Mapping**: Flexible mapping of dataset gender values to standardized categories

### Statistical Analysis
- **Comprehensive Tests**: 
  - Continuous variables: Welch's t-test, Mann-Whitney U, Welch's ANOVA, Kruskal-Wallis
  - Categorical variables: Chi-square test, Fisher's exact test
- **Effect Sizes**: Cohen's d, Hedges' g, Cramér's V, odds ratios with confidence intervals
- **Multiple Testing**: Benjamini-Hochberg FDR correction
- **Assumption Testing**: Normality tests (Shapiro-Wilk, D'Agostino) with automatic test selection

### Privacy & Security
- **Small-cell Suppression**: Automatic suppression of cells with counts < 5
- **In-memory Storage**: No persistent data storage, automatic 60-minute expiry
- **Manual Data Purge**: One-click data deletion
- **Privacy Disclaimers**: Clear warnings about re-identification risks

### Visualization & Reporting
- **Interactive Charts**: Box plots, histograms, bar charts using Plotly
- **Export Formats**: HTML, PDF, and DOCX reports with professional formatting
- **Comprehensive Reports**: Methods, results, statistical tests, effect sizes, and caveats
- **Data Exports**: Wide and long format CSV, JSON metadata

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Zustand, Plotly
- **Backend**: FastAPI, Python 3.11, pandas, scipy, statsmodels, pingouin
- **Report Generation**: Jinja2, WeasyPrint, python-docx
- **Testing**: Jest, Playwright, pytest

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FemStat
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your preferred settings
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Start the development servers**
   ```bash
   make dev
   ```

5. **Open the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

## Usage Guide

### 1. Upload Data
- Drag and drop or select a file (CSV, Excel, SPSS, Stata, Parquet)
- Review the inferred schema and gender candidates
- File size limit: 50MB

### 2. Configure Analysis
- Select the gender variable from candidates
- Map dataset values to standard categories (female, male, other, missing)
- Choose continuous and categorical variables for analysis
- Set missing data policy and other options

### 3. View Results
- **Overview**: Gender distribution and analysis summary
- **Continuous**: Statistical tests, effect sizes, and visualizations
- **Categorical**: Contingency tables, tests, and charts
- **Missingness**: Missing data patterns by gender
- **Settings**: Analysis configuration used

### 4. Export Reports
- Download data as CSV (wide/long) or JSON
- Generate professional HTML, PDF, or DOCX reports
- Reports include methods, results, and statistical details

## API Documentation

The backend provides a RESTful API with the following endpoints:

- `POST /api/upload` - Upload dataset file
- `POST /api/variables` - Get variable information
- `POST /api/analyze` - Run statistical analysis
- `POST /api/report` - Generate reports
- `POST /api/purge/{session_id}` - Delete session data

See http://localhost:8000/docs for interactive API documentation.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Backend server port |
| `MAX_UPLOAD_MB` | 50 | Maximum file upload size |
| `SESSION_TTL_MIN` | 60 | Session expiry time in minutes |
| `SUPPRESS_THRESHOLD` | 5 | Small cell suppression threshold |
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend API URL |

### Analysis Options

- **Missing Data Policy**: listwise, pairwise, or flag
- **Gender Categories**: Customizable order and mapping
- **Statistical Tests**: Automatic selection based on data characteristics
- **Effect Sizes**: Multiple measures with confidence intervals
- **Multiple Testing**: Optional FDR correction

## Testing

```bash
# Run all tests
make test

# Backend tests only
cd backend && python -m pytest tests/ -v

# Frontend tests only
cd frontend && npm test

# End-to-end tests
cd frontend && npm run test:e2e
```

## Development

### Project Structure

```
FemStat/
├── backend/                 # FastAPI backend
│   ├── main.py             # FastAPI application
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic
│   ├── models/             # Pydantic schemas
│   ├── templates/          # Jinja2 report templates
│   └── tests/              # Backend tests
├── frontend/               # Next.js frontend
│   ├── app/                # App router pages
│   ├── components/         # React components
│   ├── lib/                # Utilities and API client
│   └── tests/              # Frontend tests
├── docker/                 # Docker configuration
├── Makefile               # Development commands
└── docker-compose.yml     # Multi-container setup
```

### Available Commands

```bash
make help          # Show all available commands
make dev           # Start both frontend and backend
make backend       # Start backend only
make frontend      # Start frontend only
make test          # Run all tests
make lint          # Run linting
make build         # Build for production
make clean         # Clean build artifacts
```

## Sample Data

The repository includes sample data for testing:
- `backend/tests/data/synthetic_mnh.csv` - Synthetic maternal and newborn health data
- Includes varied gender labels to test mapping functionality
- Contains both continuous and categorical variables

## Privacy & Ethics

This tool is designed with privacy and ethical considerations:

- **No Data Persistence**: All data is stored in memory and automatically expires
- **Small-cell Suppression**: Protects against re-identification in small subgroups
- **Transparent Methods**: All statistical methods and assumptions are clearly documented
- **Manual Control**: Users can manually purge their data at any time

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions, issues, or feature requests, please open an issue on the repository.

## Acknowledgments

Built with modern web technologies and statistical best practices. Special thanks to the open-source community for the excellent libraries that make this tool possible.
