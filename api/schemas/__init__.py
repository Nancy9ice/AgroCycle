"""Re-exports every public schema model so that `from api.schemas import X` still works."""
from __future__ import annotations

from api.schemas.ask import AskRequest, AskResponse
from api.schemas.compare import (
    CompareRequest,
    CompareResponse,
    ConstraintsRecordedOut,
    ContextAnswers,
    DecisionOut,
    EvidenceType,
    OutcomeAssessmentOut,
    PriorityId,
    RuleFindingOut,
    StrategyAssessmentOut,
)
from api.schemas.fields import (
    DemoFieldOut,
    FieldInputRequest,
    FieldOut,
    FieldValidationOut,
    SourceCoverageOut,
    TimeSeriesOut,
    TimeSeriesPointOut,
    ValidationError,
)
from api.schemas.meta import (
    ConstraintChoiceOut,
    ConstraintQuestionOut,
    HealthOut,
    MetaConstraintOptionsOut,
)
from api.schemas.methods import (
    CamelModel,
    ClimateOut,
    CropHistoryOut,
    CropYearOut,
    FieldProfileOut,
    IndicatorGlossaryOut,
    IndicatorOut,
    LineageOut,
    MarsdenEvidenceOut,
    MarsdenRowOut,
    ProfileVersionsOut,
    ProvenanceOut,
    SectionOut,
    SoilMeasureOut,
    SoilOut,
    SourceOut,
    TechnicalOut,
)

__all__ = [
    # ask
    "AskRequest",
    "AskResponse",
    # methods / profile
    "CamelModel",
    "ClimateOut",
    # compare
    "CompareRequest",
    "CompareResponse",
    # meta
    "ConstraintChoiceOut",
    "ConstraintQuestionOut",
    "ConstraintsRecordedOut",
    "ContextAnswers",
    "CropHistoryOut",
    "CropYearOut",
    "DecisionOut",
    # fields
    "DemoFieldOut",
    "EvidenceType",
    "FieldInputRequest",
    "FieldOut",
    "FieldProfileOut",
    "FieldValidationOut",
    "HealthOut",
    "IndicatorGlossaryOut",
    "IndicatorOut",
    "LineageOut",
    "MarsdenEvidenceOut",
    "MarsdenRowOut",
    "MetaConstraintOptionsOut",
    "OutcomeAssessmentOut",
    "PriorityId",
    "ProfileVersionsOut",
    "ProvenanceOut",
    "RuleFindingOut",
    "SectionOut",
    "SoilMeasureOut",
    "SoilOut",
    "SourceCoverageOut",
    "SourceOut",
    "StrategyAssessmentOut",
    "TechnicalOut",
    "TimeSeriesOut",
    "TimeSeriesPointOut",
    "ValidationError",
]
