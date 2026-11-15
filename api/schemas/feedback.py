"""Schemas for POST /feedback (spec section 5.3)."""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

# A rating is a real number from 1 to 5: strict, so the string "4" is refused rather than quietly converted.
Rating = Annotated[int, Field(strict=True, ge=1, le=5)]


class FeedbackRequest(BaseModel):
    """What a person tells us about the app. Skipped optional answers are null and mean "not provided"."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["farmer", "adviser", "researcher", "other"]
    farming_context: str | None = Field(
        default=None,
        max_length=120,
        description='Who is speaking, e.g. "Nigerian farmer, usability review" or "Iowa adviser".',
    )
    usefulness: Rating
    clarity: Rating
    what_was_missing: str | None = Field(default=None, max_length=1000)
    would_use: Literal["yes", "maybe", "no"] | None = None
    contact: str | None = Field(default=None, max_length=200)
    contact_consent: StrictBool = Field(
        default=False, description="Must be true for `contact` to be kept; it is personal data."
    )
    field_id: str | None = Field(default=None, max_length=64)
    analysis_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def contact_needs_consent(self) -> FeedbackRequest:
        if self.contact and not self.contact_consent:
            raise ValueError("Tick the consent box if you want us to keep your contact details.")
        return self


class FeedbackOut(BaseModel):
    feedback_id: str
    message: str
    iowa_note: str
