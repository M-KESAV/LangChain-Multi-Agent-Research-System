from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class ResearchCreateRequest(BaseModel):
    topic: str = Field(..., description="The non-empty topic to research", min_length=1, max_length=1000)

    @field_validator("topic")
    @classmethod
    def validate_topic_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Research topic cannot be empty or whitespace.")
        return v.strip()


class ResearchCreateResponse(BaseModel):
    id: str
    topic: str
    status: str
    message: str


class ResearchSummaryResponse(BaseModel):
    id: str
    topic: str
    status: str
    report: Optional[str] = None
    feedback: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: str
    updated_at: str


class ResearchDetailResponse(BaseModel):
    id: str
    topic: str
    status: str
    search_results: Optional[str] = None
    scraped_content: Optional[str] = None
    report: Optional[str] = None
    feedback: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: str
    updated_at: str


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"


class MessageResponse(BaseModel):
    message: str
    id: Optional[str] = None
