from pydantic import BaseModel, Field


class AnalysisMetric(BaseModel):
    key: str = Field(description="Stable machine-readable key, e.g. gross_yield.")
    label: str = Field(description="Human-readable metric label.")
    value: str | float | int | None = Field(default=None, description="Metric value.")
    unit: str | None = Field(default=None, description="Optional unit such as %, EUR, or x.")
    confidence: float | None = Field(default=None, description="Optional confidence score.")
    source: str | None = Field(default=None, description="Primary evidence source label.")


class AnalysisSection(BaseModel):
    title: str
    summary: str
    items: list[str] = Field(default_factory=list)


class ExcelFieldMapping(BaseModel):
    field_key: str = Field(description="Stable export key for later Excel template adapters.")
    value: str | float | int | None = None
    source: str | None = None


class RealEstateAnalysisResult(BaseModel):
    asset_name: str | None = None
    executive_summary: str
    metrics: list[AnalysisMetric] = Field(default_factory=list)
    risks: AnalysisSection | None = None
    opportunities: AnalysisSection | None = None
    missing_data: list[str] = Field(default_factory=list)
    recommendation: str | None = None
    excel_fields: list[ExcelFieldMapping] = Field(default_factory=list)
