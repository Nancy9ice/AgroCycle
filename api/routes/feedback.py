"""Route: POST /feedback. Appends one row to the feedback log; nothing is read back out through the API."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from api.db.repository import FieldRepository
from api.deps import get_repository
from api.schemas.feedback import FeedbackOut, FeedbackRequest

router = APIRouter()

THANKS = "Thank you. Your feedback was saved."
IOWA_NOTE = (
    "AgroCycle covers Iowa. Feedback from outside Iowa helps us judge how clear and usable the app is, "
    "not whether its Iowa agronomy is right, and the feedback log keeps the two apart."
)
# Anyone can post, so cap how many arrive in an hour. A burst this size is spam, not people.
MAX_FEEDBACK_PER_HOUR = 200


@router.post("/feedback", response_model=FeedbackOut, tags=["feedback"])
def post_feedback(
    body: FeedbackRequest, repository: FieldRepository = Depends(get_repository)
) -> FeedbackOut:
    """Save one piece of feedback. Contact details are kept only when the person ticked consent."""
    feedback_id = f"fb_{uuid.uuid4().hex[:10]}"
    try:
        if repository.count_recent_feedback(1) >= MAX_FEEDBACK_PER_HOUR:
            raise HTTPException(status_code=429, detail="Too much feedback arrived in the last hour. Try again later.")
        repository.save_feedback(
            {
                "feedback_id": feedback_id,
                "role": body.role,
                "farming_context": body.farming_context or "",
                "usefulness": body.usefulness,
                "clarity": body.clarity,
                "what_was_missing": body.what_was_missing or "",
                "would_use": body.would_use or "",
                # Personal data: kept only with consent (the request model already refuses contact without it).
                "contact": body.contact if (body.contact and body.contact_consent) else "",
                "contact_consent": 1 if (body.contact and body.contact_consent) else 0,
                "field_id": body.field_id or "",
                "analysis_id": body.analysis_id or "",
            }
        )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=503, detail=f"Your feedback could not be saved: {err}") from err
    return FeedbackOut(feedback_id=feedback_id, message=THANKS, iowa_note=IOWA_NOTE)
