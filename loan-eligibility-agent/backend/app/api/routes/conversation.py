"""
Conversation API Routes
REST endpoints for managing conversational interactions.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services import ConversationService
from ...models import ConversationState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversation", tags=["conversation"])

# Initialize conversation service
conversation_service = ConversationService()


class StartConversationResponse(BaseModel):
    """Response when starting a new conversation."""
    session_id: str
    message: str
    current_step: str


class MessageRequest(BaseModel):
    """Request model for sending a message."""
    session_id: str
    message: str = Field(..., min_length=1, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "message": "I'm interested in a personal loan"
            }
        }


class MessageResponse(BaseModel):
    """Response model for message processing."""
    session_id: str
    response: str
    current_step: str
    collected_data: Dict[str, Any]
    missing_fields: list
    conversation_complete: bool = False


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    session_id: str
    messages: list
    current_step: str
    started_at: str
    last_activity: str


@router.post("/start", response_model=StartConversationResponse)
async def start_conversation():
    """
    Start a new loan pre-qualification conversation.

    Returns a session ID and initial greeting message.
    """
    try:
        state = conversation_service.create_session()

        # Generate initial greeting
        response, state = await conversation_service.process_message(
            state.session_id,
            "__START__"  # Internal trigger for greeting
        )

        return StartConversationResponse(
            session_id=state.session_id,
            message=response,
            current_step=state.current_step
        )
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")


@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """
    Send a message in an existing conversation.

    Processes the user's message, updates conversation state,
    and returns the agent's response.
    """
    try:
        # Check if session exists
        state = conversation_service.get_session(request.session_id)
        if not state:
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please start a new conversation."
            )

        # Process the message
        response, updated_state = await conversation_service.process_message(
            request.session_id,
            request.message
        )

        # Check if conversation is complete
        conversation_complete = updated_state.current_step in ["present_result", "next_steps"]

        # Serialize collected data for response
        collected_data = {}
        for key, value in updated_state.collected_data.items():
            if hasattr(value, 'value'):  # Enum
                collected_data[key] = value.value
            elif hasattr(value, '__str__'):
                collected_data[key] = str(value)
            else:
                collected_data[key] = value

        return MessageResponse(
            session_id=updated_state.session_id,
            response=response,
            current_step=updated_state.current_step,
            collected_data=collected_data,
            missing_fields=updated_state.missing_fields,
            conversation_complete=conversation_complete
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str):
    """
    Retrieve conversation history for a session.
    """
    state = conversation_service.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    return ConversationHistoryResponse(
        session_id=state.session_id,
        messages=state.conversation_history,
        current_step=state.current_step,
        started_at=state.started_at.isoformat(),
        last_activity=state.last_activity.isoformat()
    )


@router.get("/state/{session_id}")
async def get_conversation_state(session_id: str):
    """
    Get the current state of a conversation.

    Useful for resuming conversations or debugging.
    """
    state = conversation_service.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Serialize state for response
    collected_data = {}
    for key, value in state.collected_data.items():
        if key == "eligibility_result":
            continue  # Skip complex nested object
        if hasattr(value, 'value'):  # Enum
            collected_data[key] = value.value
        elif hasattr(value, '__str__'):
            collected_data[key] = str(value)
        else:
            collected_data[key] = value

    return {
        "session_id": state.session_id,
        "current_step": state.current_step,
        "collected_data": collected_data,
        "missing_fields": state.missing_fields,
        "message_count": len(state.conversation_history),
        "started_at": state.started_at.isoformat(),
        "last_activity": state.last_activity.isoformat(),
        "has_eligibility_result": "eligibility_result" in state.collected_data
    }


@router.delete("/session/{session_id}")
async def end_conversation(session_id: str):
    """
    End and clean up a conversation session.
    """
    state = conversation_service.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove session
    if session_id in conversation_service.sessions:
        del conversation_service.sessions[session_id]

    return {
        "message": "Session ended successfully",
        "session_id": session_id
    }


@router.post("/handoff/{session_id}")
async def request_human_handoff(
    session_id: str,
    reason: Optional[str] = None
):
    """
    Request handoff to a human agent.

    This endpoint logs the handoff request and returns
    options for connecting with a human representative.
    """
    state = conversation_service.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Log handoff request
    from ...core.logging_config import conversation_logger
    conversation_logger.log_handoff(session_id, reason or "user_requested")

    return {
        "message": "Handoff request received",
        "session_id": session_id,
        "handoff_options": [
            {
                "type": "callback",
                "description": "Schedule a callback from a loan specialist",
                "availability": "Within 24 hours"
            },
            {
                "type": "live_chat",
                "description": "Connect with an agent now",
                "availability": "Mon-Fri 8am-8pm EST"
            },
            {
                "type": "branch",
                "description": "Visit a local branch",
                "availability": "Find nearest location"
            }
        ],
        "conversation_summary": {
            "current_step": state.current_step,
            "data_collected": list(state.collected_data.keys()),
            "message_count": len(state.conversation_history)
        }
    }
