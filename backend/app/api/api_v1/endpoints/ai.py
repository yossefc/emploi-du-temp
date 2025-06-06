"""
AI Agent endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.db.base import get_db
from app.models.user import User
from app.ai.agent import AIAgent
from app.schemas.ai import (
    AIQueryRequest,
    AIQueryResponse,
    ConstraintParseRequest,
    ConstraintParseResponse,
    ConflictExplanationRequest,
    ConflictExplanationResponse,
    SuggestionRequest,
    SuggestionResponse
)

router = APIRouter()


@router.post("/query", response_model=AIQueryResponse)
async def query_ai(
    request: AIQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Query the AI agent with natural language."""
    agent = AIAgent(db)
    
    try:
        result = await agent.process_message(
            user_message=request.message,
            language=request.language,
            context=request.context
        )
        
        return AIQueryResponse(
            response=result["response"],
            intent=result["intent"],
            actions=[{
                "type": action["type"],
                "data": action["data"],
                "confidence": action.get("confidence", 0.8)
            } for action in result.get("actions", [])],
            language=request.language,
            requires_confirmation=any(
                action["type"] in ["add_constraint", "modify_schedule"]
                for action in result.get("actions", [])
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-constraint", response_model=ConstraintParseResponse)
async def parse_constraint(
    request: ConstraintParseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Parse a natural language constraint."""
    agent = AIAgent(db)
    
    try:
        constraint = await agent._parse_constraint(
            message=request.text,
            language=request.language
        )
        
        if constraint:
            return ConstraintParseResponse(
                success=True,
                constraint={
                    "entity_type": constraint["entity_type"],
                    "entity_id": constraint.get("entity_id"),
                    "constraint_type": constraint["constraint_type"],
                    "parameters": constraint["parameters"],
                    "confidence": constraint.get("confidence", 0.8),
                    "original_text": request.text
                }
            )
        else:
            return ConstraintParseResponse(
                success=False,
                error="Failed to parse constraint from text"
            )
    except Exception as e:
        return ConstraintParseResponse(
            success=False,
            error=str(e)
        )


@router.post("/explain-conflicts", response_model=ConflictExplanationResponse)
async def explain_conflicts(
    request: ConflictExplanationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI explanations for schedule conflicts."""
    # This would be implemented with actual conflict analysis
    # For now, returning a sample response
    return ConflictExplanationResponse(
        explanations=[],
        summary="No conflicts found in the schedule.",
        total_conflicts=0,
        resolvable_count=0
    )


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI suggestions for schedule improvement."""
    agent = AIAgent(db)
    
    try:
        # Get schedule data
        # This would fetch actual schedule data
        schedule_data = {"schedule_id": request.schedule_id}
        
        suggestions = await agent._generate_suggestions(
            schedule_data=schedule_data,
            language=request.language
        )
        
        return SuggestionResponse(
            suggestions=[{
                "type": s.get("type", "general"),
                "description": s.get("description", ""),
                "impact": s.get("impact", ""),
                "implementation": s.get("implementation", ""),
                "priority": s.get("priority", "medium"),
                "estimated_improvement": s.get("estimated_improvement"),
                "actions": s.get("actions", [])
            } for s in suggestions[:request.max_suggestions]],
            analysis_summary="Schedule analysis completed.",
            current_score=None,
            potential_score=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 