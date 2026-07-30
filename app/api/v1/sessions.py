"""Session management API endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.database.session import get_db
from app.repositories.session_repository import SessionRepository
from app.schemas import MessageResponse, SessionResponse

router = APIRouter()


@router.get("/", response_model=List[SessionResponse])
def list_sessions(
    current_user: CurrentUser = Depends(require_permission("auth.sessions.view")),
    db: Session = Depends(get_db),
):
    repo = SessionRepository(db)
    sessions = repo.get_active_sessions(current_user.user_id)
    result = []
    for s in sessions:
        resp = SessionResponse.model_validate(s)
        resp.is_current = str(s.SessionId) == current_user.session_id
        result.append(resp)
    return result


@router.get("/user/{user_id}", response_model=List[SessionResponse])
def list_user_sessions(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.sessions.view")),
    db: Session = Depends(get_db),
):
    repo = SessionRepository(db)
    sessions = repo.get_active_sessions(user_id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.delete("/{session_id}", response_model=MessageResponse)
def revoke_session(
    session_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_permission("auth.sessions.revoke")),
    db: Session = Depends(get_db),
):
    repo = SessionRepository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    repo.revoke_session(session_id, "Admin force logout")
    db.commit()
    return MessageResponse(message="Session revoked successfully.")


@router.delete("/user/{user_id}/all", response_model=MessageResponse)
def revoke_all_sessions(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission("auth.sessions.revoke")),
    db: Session = Depends(get_db),
):
    SessionRepository(db).revoke_all_user_sessions(user_id, reason="Admin force logout all")
    db.commit()
    return MessageResponse(message="All sessions revoked.")
