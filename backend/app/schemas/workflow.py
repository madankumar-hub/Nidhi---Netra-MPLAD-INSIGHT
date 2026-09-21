from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    ActivityType,
    CitizenReportCategory,
    CitizenReportStatus,
    NoteType,
    ReviewStatus,
)


# --- Reviews --------------------------------------------------------------
class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    reviewer_id: Optional[int] = None
    reviewer_name: str
    reviewer_role: str
    review_date: datetime
    previous_status: Optional[ReviewStatus] = None
    status: ReviewStatus
    findings: str
    notes: Optional[str] = None
    action_required: Optional[str] = None
    escalated_to: Optional[str] = None
    follow_up_required: bool
    created_at: datetime


class ReviewCreate(BaseModel):
    status: ReviewStatus
    findings: str = Field(min_length=3, max_length=4000)
    notes: Optional[str] = Field(default=None, max_length=4000)
    action_required: Optional[str] = Field(default=None, max_length=2000)
    escalated_to: Optional[str] = Field(default=None, max_length=160)
    follow_up_required: bool = False


# --- Notes ----------------------------------------------------------------
class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    author_id: Optional[int] = None
    author_name: str
    author_role: str
    note_type: NoteType
    content: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime


class NoteCreate(BaseModel):
    content: str = Field(min_length=2, max_length=4000)
    note_type: NoteType = NoteType.GENERAL
    is_pinned: bool = False


class NoteUpdate(BaseModel):
    content: Optional[str] = Field(default=None, min_length=2, max_length=4000)
    note_type: Optional[NoteType] = None
    is_pinned: Optional[bool] = None


# --- Activity -------------------------------------------------------------
class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: Optional[int] = None
    actor_name: str
    actor_role: str
    activity_type: ActivityType
    summary: str
    detail: Optional[str] = None
    from_value: Optional[str] = None
    to_value: Optional[str] = None
    created_at: datetime


# --- Citizen reports (FR7) ------------------------------------------------
class CitizenReportCreate(BaseModel):
    category: CitizenReportCategory
    description: str = Field(min_length=10, max_length=2000)


class CitizenReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    reporter_name: str
    category: CitizenReportCategory
    description: str
    status: CitizenReportStatus
    official_response: Optional[str] = None
    created_at: datetime


class CitizenReportTriage(BaseModel):
    status: CitizenReportStatus
    official_response: Optional[str] = Field(default=None, max_length=2000)
