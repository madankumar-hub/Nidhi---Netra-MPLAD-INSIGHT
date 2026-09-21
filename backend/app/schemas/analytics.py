from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class KeyValueCount(BaseModel):
    label: str
    value: int


class KeyValueAmount(BaseModel):
    label: str
    allocated: float
    spent: float
    utilization_percent: float
    count: int = 0


class TrendPoint(BaseModel):
    period: str
    allocated: float
    spent: float
    projects: int
    avg_progress: float


class DashboardSummary(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    delayed_projects: int
    not_started_projects: int
    pending_review_projects: int
    escalated_projects: int
    projects_with_open_risks: int
    high_risk_projects: int
    critical_risk_projects: int
    open_mitigations: int
    overdue_projects: int
    citizen_reports_open: int
    total_allocated: float
    total_spent: float
    total_remaining: float
    utilization_percent: float
    average_progress: float
    average_risk_score: float


class PublicSummary(BaseModel):
    """Aggregates safe to show on the citizen portal."""

    total_projects: int
    completed_projects: int
    ongoing_projects: int
    districts_covered: int
    categories_covered: int
    total_allocated: float
    total_spent: float
    utilization_percent: float
    average_progress: float


class AdminAnalytics(BaseModel):
    summary: DashboardSummary
    by_status: List[KeyValueCount] = Field(default_factory=list)
    by_review_status: List[KeyValueCount] = Field(default_factory=list)
    by_risk_level: List[KeyValueCount] = Field(default_factory=list)
    by_category: List[KeyValueAmount] = Field(default_factory=list)
    by_district: List[KeyValueAmount] = Field(default_factory=list)
    by_agency: List[KeyValueAmount] = Field(default_factory=list)
    by_mp: List[KeyValueAmount] = Field(default_factory=list)
    progress_distribution: List[KeyValueCount] = Field(default_factory=list)
    utilization_distribution: List[KeyValueCount] = Field(default_factory=list)
    yearly_trend: List[TrendPoint] = Field(default_factory=list)
    spending_trend: List[TrendPoint] = Field(default_factory=list)
    risk_category_distribution: List[KeyValueCount] = Field(default_factory=list)
    top_risk_factors: List[KeyValueCount] = Field(default_factory=list)
    generated_at: str


class PublicAnalytics(BaseModel):
    summary: PublicSummary
    by_status: List[KeyValueCount] = Field(default_factory=list)
    by_category: List[KeyValueAmount] = Field(default_factory=list)
    by_district: List[KeyValueAmount] = Field(default_factory=list)
    yearly_trend: List[TrendPoint] = Field(default_factory=list)
    generated_at: str
