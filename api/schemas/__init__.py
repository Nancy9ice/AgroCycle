"""Re-exports every public schema model so that `from api.schemas import X` still works."""
from __future__ import annotations

from api.schemas.ask import AskRequest, AskResponse
from api.schemas.compare import (
    CompareRequest,
    CompareResponse,
    ConstraintsRecordedOut,
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
    # compare
    "CompareRequest",
    "CompareResponse",
    "ConstraintsRecordedOut",
    "DecisionOut",
    "EvidenceType",
    "OutcomeAssessmentOut",
    "PriorityId",
    "RuleFindingOut",
    "StrategyAssessmentOut",
    # fields
    "DemoFieldOut",
    "FieldInputRequest",
    "FieldOut",
    "FieldValidationOut",
    "SourceCoverageOut",
    "TimeSeriesOut",
    "TimeSeriesPointOut",
    "ValidationError",
    # meta
    "ConstraintChoiceOut",
    "ConstraintQuestionOut",
    "HealthOut",
    "MetaConstraintOptionsOut",
    # methods / profile
    "CamelModel",
    "ClimateOut",
    "CropHistoryOut",
    "CropYearOut",
    "FieldProfileOut",
    "IndicatorGlossaryOut",
    "IndicatorOut",
    "LineageOut",
    "MarsdenEvidenceOut",
    "MarsdenRowOut",
    "ProvenanceOut",
    "SectionOut",
    "SoilMeasureOut",
    "SoilOut",
    "SourceOut",
    "TechnicalOut",
]
