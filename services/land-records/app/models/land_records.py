# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LandRecordsRequest(BaseModel):
    district: str = Field(..., examples=["Bengaluru Urban"])
    taluk: str = Field(..., examples=["Bengaluru North"])
    hobli: str = Field(..., examples=["Jala"])
    village: str = Field(..., examples=["Yelahanka"])
    survey_number: str = Field(..., examples=["123/4"])
    state: str = "Karnataka"


class BhoomiRecord(BaseModel):
    owner_name: str | None = None
    survey_number: str | None = None
    area_acres: float | None = None
    land_type: str | None = None
    encumbrance_present: bool = False
    mutation_number: str | None = None
    raw_data_available: bool = False


class DeepLink(BaseModel):
    label: str
    url: str
    description: str


class CourtCase(BaseModel):
    case_number: str | None = None
    court: str | None = None
    status: str | None = None
    parties: str | None = None
    filing_date: str | None = None


class LandRecordsResult(BaseModel):
    bhoomi: BhoomiRecord
    court_cases: list[CourtCase] = Field(default_factory=list)
    deep_links: list[DeepLink] = Field(default_factory=list)
    score: float = Field(..., ge=0, le=100)
    severity: Literal["low", "moderate", "high", "none"]
    data_source: str
    notes: str | None = None
