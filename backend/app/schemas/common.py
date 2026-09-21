from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Optional[str] = None


class OptionCount(BaseModel):
    label: str
    value: str
    count: int = 0


class FilterOptions(BaseModel):
    mps: List[OptionCount] = Field(default_factory=list)
    districts: List[OptionCount] = Field(default_factory=list)
    states: List[OptionCount] = Field(default_factory=list)
    categories: List[OptionCount] = Field(default_factory=list)
    agencies: List[OptionCount] = Field(default_factory=list)
    years: List[OptionCount] = Field(default_factory=list)
    statuses: List[OptionCount] = Field(default_factory=list)
