"""A duck-typed stand-in for the Project ORM model.

The risk engine deliberately depends only on plain attributes, so it can be
exercised without a database. This keeps the core feature unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from app.core.enums import ProjectStatus


@dataclass
class FakeUpdate:
    updated_on: date
    progress_percent: float = 0.0
    planned_progress_percent: Optional[float] = None
    expenditure_amount: float = 0.0
    released_amount: float = 0.0


@dataclass
class FakeProject:
    id: int = 1
    project_code: str = "MPLAD-2025-00001"
    title: str = "Construction of community hall at Shivajinagar"
    description: str = "Construction of a community hall with flooring and electrification."
    district: str = "Pune"
    category: str = "Community Halls"
    executing_agency: str = "Public Works Department (PWD)"
    allocated_amount: float = 20.0
    spent_amount: float = 0.0
    estimated_cost: Optional[float] = None
    progress_percent: float = 0.0
    planned_progress_percent: Optional[float] = None
    status: ProjectStatus = ProjectStatus.IN_PROGRESS
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    beneficiaries: Optional[int] = 1000
    progress_updates: List[FakeUpdate] = field(default_factory=list)
    fund_updates: List[FakeUpdate] = field(default_factory=list)

    @property
    def remaining_amount(self) -> float:
        return round(max(self.allocated_amount - self.spent_amount, 0.0), 2)

    @property
    def utilization_percent(self) -> float:
        if not self.allocated_amount:
            return 0.0
        return round(min(self.spent_amount / self.allocated_amount * 100.0, 999.0), 2)
