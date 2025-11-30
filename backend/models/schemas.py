"""
Pydantic models for API request/response schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class MissingPolicy(str, Enum):
    LISTWISE = "listwise"
    PAIRWISE = "pairwise"
    FLAG = "flag"

class VariableType(str, Enum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    BOOLEAN = "boolean"

class GenderMapping(BaseModel):
    from_value: str = Field(..., description="Original value in dataset")
    to_value: str = Field(..., description="Standardized gender category")

class ImputeConfig(BaseModel):
    mean: Optional[List[str]] = Field(None, description="Variables to impute with mean")
    median: Optional[List[str]] = Field(None, description="Variables to impute with median")
    mode: Optional[List[str]] = Field(None, description="Variables to impute with mode")

class AnalysisRequest(BaseModel):
    session_id: str
    gender_col: str
    gender_map: List[GenderMapping]
    categories_order: List[str] = Field(default=["female", "male", "other", "missing"])
    vars_continuous: List[str]
    vars_categorical: List[str]
    weight_col: Optional[str] = None
    cluster_id: Optional[str] = None
    robust_se: bool = False
    missing_policy: MissingPolicy = MissingPolicy.LISTWISE
    impute: Optional[ImputeConfig] = None
    suppress_threshold: int = Field(default=5, ge=1)
    fdr: bool = False

class VariableInfo(BaseModel):
    name: str
    dtype: str
    unique_n: int
    sample_values: List[Any]
    missing_pct: float
    variable_type: VariableType

class SchemaResponse(BaseModel):
    session_id: str
    schema_data: List[VariableInfo] = Field(alias="schema")
    gender_candidates: List[str]
    file_info: Dict[str, Any]

class GenderSummary(BaseModel):
    gender: str
    n: int
    pct: float
    missing_pct: float

class ContinuousStats(BaseModel):
    gender: str
    n: Union[int, str]
    mean: Union[float, str]
    sd: Union[float, str]
    median: Union[float, str]
    iqr: Union[float, str]
    min: Union[float, str]
    max: Union[float, str]

class TestResult(BaseModel):
    name: str
    p: Union[float, str]
    statistic: Union[float, str]
    df: Optional[Union[int, str]] = None
    assumptions_met: bool = True
    note: Optional[str] = None

class EffectSize(BaseModel):
    name: str
    value: Union[float, str]
    ci_lower: Optional[Union[float, str]] = None
    ci_upper: Optional[Union[float, str]] = None
    interpretation: Optional[str] = None

class ContinuousResult(BaseModel):
    var: str
    table: List[ContinuousStats]
    test: TestResult
    effects: List[EffectSize]

class CategoricalLevel(BaseModel):
    level: str
    gender: str
    n: Union[int, str]
    pct: Union[float, str]

class CategoricalResult(BaseModel):
    var: str
    table: List[CategoricalLevel]
    test: TestResult
    effects: List[EffectSize]

class MissingnessInfo(BaseModel):
    var: str
    gender: str
    missing_n: int
    missing_pct: float

class NormalityTest(BaseModel):
    var: str
    gender: str
    test: str
    p: Union[float, str]
    statistic: Union[float, str]

class MultipleTesting(BaseModel):
    fdr_method: Optional[str] = "BH"
    adjusted: bool

class Diagnostics(BaseModel):
    normality: List[Dict[str, Any]]
    multiple_testing: MultipleTesting

class FileUrls(BaseModel):
    csv_wide_url: str
    csv_long_url: str
    json_url: str

class GenderBiasAssessment(BaseModel):
    overall_summary: str
    statistical_disparities: List[Dict[str, Any]]
    representation_gaps: List[Dict[str, Any]]
    missing_data_bias: List[Dict[str, Any]]
    practical_significance: List[Dict[str, Any]]
    recommendations: List[str]
    gender_transformative_insights: List[str]

class AnalysisResponse(BaseModel):
    settings: Dict[str, Any]
    by_gender: List[GenderSummary]
    continuous: List[ContinuousResult]
    categorical: List[CategoricalResult]
    missingness: List[MissingnessInfo]
    diagnostics: Diagnostics
    gender_bias: Optional[GenderBiasAssessment] = None
    files: FileUrls

class ReportRequest(BaseModel):
    session_id: str
    title: str = "Gender Analysis Report"
    organization: Optional[str] = None
    authors: Optional[List[str]] = None
    notes: Optional[str] = None

class ReportResponse(BaseModel):
    html_url: str
    pdf_url: str
    docx_url: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
