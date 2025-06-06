"""
AI Agent schemas for API validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class Language(str, Enum):
    """Supported languages."""
    HEBREW = "he"
    FRENCH = "fr"


class Intent(str, Enum):
    """AI intent types."""
    ADD_CONSTRAINT = "add_constraint"
    EXPLAIN_CONFLICT = "explain_conflict"
    SUGGEST_MODIFICATION = "suggest_modification"
    QUERY_SCHEDULE = "query_schedule"
    GENERAL = "general"


class ActionType(str, Enum):
    """AI action types."""
    ADD_CONSTRAINT = "add_constraint"
    SUGGESTIONS = "suggestions"
    VISUALIZE = "visualize"
    MODIFY_SCHEDULE = "modify_schedule"


class AIQueryRequest(BaseModel):
    """Request schema for AI queries."""
    message: str = Field(..., min_length=1, max_length=2000)
    language: Language = Language.HEBREW
    context: Optional[Dict[str, Any]] = None
    schedule_id: Optional[int] = None
    include_history: bool = False


class AIAction(BaseModel):
    """AI action schema."""
    type: ActionType
    data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)


class AIQueryResponse(BaseModel):
    """Response schema for AI queries."""
    response: str
    intent: Intent
    actions: List[AIAction] = []
    language: Language
    requires_confirmation: bool = False


class ParsedConstraint(BaseModel):
    """Parsed constraint from natural language."""
    entity_type: str  # teacher, class, room, global
    entity_id: Optional[int] = None
    constraint_type: str  # availability, preference, requirement
    parameters: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    original_text: str


class ConstraintParseRequest(BaseModel):
    """Request to parse constraint from natural language."""
    text: str = Field(..., min_length=1, max_length=1000)
    language: Language = Language.HEBREW


class ConstraintParseResponse(BaseModel):
    """Response for parsed constraint."""
    success: bool
    constraint: Optional[ParsedConstraint] = None
    error: Optional[str] = None


class ConflictExplanationRequest(BaseModel):
    """Request for conflict explanation."""
    schedule_id: int
    conflict_ids: Optional[List[int]] = None
    language: Language = Language.HEBREW
    detail_level: str = Field(default="medium", pattern="^(low|medium|high)$")


class ConflictExplanation(BaseModel):
    """Single conflict explanation."""
    conflict_id: int
    type: str
    severity: str
    explanation: str
    suggestions: List[str] = []
    involved_entities: Dict[str, List[str]] = {}


class ConflictExplanationResponse(BaseModel):
    """Response for conflict explanations."""
    explanations: List[ConflictExplanation]
    summary: str
    total_conflicts: int
    resolvable_count: int


class SuggestionRequest(BaseModel):
    """Request for AI suggestions."""
    schedule_id: int
    problem_type: Optional[str] = None  # specific problem to focus on
    language: Language = Language.HEBREW
    max_suggestions: int = Field(default=5, ge=1, le=20)


class AISuggestion(BaseModel):
    """Single AI suggestion."""
    type: str  # constraint_relaxation, resource_addition, schedule_modification
    description: str
    impact: str
    implementation: str
    priority: str = Field(pattern="^(high|medium|low)$")
    estimated_improvement: Optional[float] = None
    actions: List[Dict[str, Any]] = []


class SuggestionResponse(BaseModel):
    """Response for AI suggestions."""
    suggestions: List[AISuggestion]
    analysis_summary: str
    current_score: Optional[float] = None
    potential_score: Optional[float] = None 