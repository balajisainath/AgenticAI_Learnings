"""Pydantic schemas for structured resume extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Experience(BaseModel):
    """A single work experience entry."""

    company: str = Field(description="Company or organisation name")
    role: str = Field(description="Job title or role held")
    duration: str = Field(description="Duration or date range (e.g. 'Jan 2020 – Mar 2022')")
    highlights: list[str] = Field(
        default_factory=list,
        description="Key achievements or responsibilities (brief bullet points)",
    )


class Education(BaseModel):
    """A single education entry."""

    institution: str = Field(description="University or school name")
    degree: str = Field(description="Degree or certification obtained")
    year: str = Field(description="Graduation year or date range")


class ResumeData(BaseModel):
    """Structured resume data extracted from raw text."""

    name: str = Field(description="Full name of the candidate")
    email: str = Field(default="", description="Email address if available")
    phone: str = Field(default="", description="Phone number if available")
    summary: str = Field(default="", description="Professional summary or objective (1-2 sentences)")
    skills: list[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience: list[Experience] = Field(default_factory=list, description="Work experience entries")
    education: list[Education] = Field(default_factory=list, description="Education entries")
