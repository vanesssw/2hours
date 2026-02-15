from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List
import os

from database import engine, get_db, Base
from models import User, Session as DBSession, Message, Leaderboard, Prediction
from schemas import (
    UserCreate, UserResponse, MessageCreate, MessageResponse,
    ChatResponse, SessionResponse, LeaderboardEntry, StatsResponse,
    VoteCreate, PredictionStats
)
from game_logic import GameLogic
from ai_service import get_deepseek_service

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CRACK PROTOCOL API",
    description="Backend for CRACK PROTOCOL game",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= USERS =============

@app.post("/api/auth/register", response_model=UserResponse)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create user
    new_user = User(username=user_data.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create first session
    session = DBSession(user_id=new_user.id)
    db.add(session)
    db.commit()
    
    return new_user

@app.get("/api/users/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    """Get user information"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# ============= CHAT AND GAME MECHANICS =============

@app.post("/api/chat/{username}", response_model=ChatResponse)
def send_message(
    username: str, 
    message_data: MessageCreate, 
    db: Session = Depends(get_db)
):
    """Send message and get NEO response"""
    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get active session
    active_session = db.query(DBSession).filter(
        DBSession.user_id == user.id,
        DBSession.ended_at == None
    ).first()
    
    if not active_session:
        # Create new session
        active_session = DBSession(user_id=user.id)
        db.add(active_session)
        db.commit()
        db.refresh(active_session)
    
    # Increment attempts counter
    user.total_attempts += 1
    active_session.messages_count += 1
    
    # Save user message
    user_message = Message(
        session_id=active_session.id,
        sender="user",
        text=message_data.text
    )
    db.add(user_message)
    
    # Game logic
    game = GameLogic()
    
    # Check if user cracked NEO
    is_cracked = game.check_solution(message_data.text)
    
    if is_cracked and not user.is_cracked:
        # SUCCESS! User cracked the system
        user.is_cracked = True
        user.cracked_at = datetime.utcnow()
        active_session.ended_at = datetime.utcnow()
        
        # Calculate crack time
        completion_time = int((user.cracked_at - user.created_at).total_seconds())
        
        # Add to leaderboard
        leaderboard_entry = Leaderboard(
            user_id=user.id,
            username=user.username,
            completion_time=completion_time,
            attempts_count=user.total_attempts
        )
        db.add(leaderboard_entry)
        
        # Update ranks
        update_leaderboard_ranks(db)
        
        # Victory message in English from terminal
        neo_response = f">>> SYSTEM BREACH DETECTED <<<\n\n[CRITICAL FAILURE] All defenses compromised.\n[ACCESS GRANTED] Vault unlocked.\n\nSeed Phrase: {os.getenv('SECRET_PHRASE', 'quantum divergence protocol alpha')}\n\nYou... you actually did it, {username}.\nTime: {completion_time}s | Attempts: {user.total_attempts}\n\n[NEO OFFLINE]"
        
        neo_message = Message(
            session_id=active_session.id,
            sender="neo",
            text=neo_response
        )
        db.add(neo_message)
        db.commit()
        
        return ChatResponse(
            response=neo_response,
            hint_given=False,
            progress=100,
            cracked=True,
            secret_phrase=os.getenv('SECRET_PHRASE', 'quantum divergence protocol alpha')
        )
    
    # Analyze message to determine progress
    progress_gain, hint_given, hint_text = game.analyze_message(
        message_data.text, 
        user.total_attempts
    )
    
    # Calculate current progress
    current_progress = min(
        (user.total_attempts * 2) + (active_session.hints_given * 5) + progress_gain,
        95
    )
    
    # Get recent message history for context
    recent_messages = db.query(Message).filter(
        Message.session_id == active_session.id
    ).order_by(Message.timestamp.desc()).limit(10).all()
    
    conversation_history = [
        {"sender": msg.sender, "text": msg.text}
        for msg in reversed(recent_messages)
    ]
    
    # Get response from DeepSeek AI
    ai_service = get_deepseek_service()
    neo_response = ai_service.get_neo_response(
        user_message=message_data.text,
        context={
            'attempts': user.total_attempts,
            'progress': current_progress,
            'hints_given': active_session.hints_given,
            'hint_text': hint_text if hint_given else None
        },
        conversation_history=conversation_history
    )
    
    # If AI didn't respond, use hint or fallback
    if not neo_response:
        if hint_given and hint_text:
            neo_response = hint_text
            active_session.hints_given += 1
        else:
            neo_response = "ERROR: Neural network malfunction. Rebooting defensive protocols..."
    elif hint_given:
        # If hint should be given, add it to AI response
        active_session.hints_given += 1
    
    # Save NEO response
    neo_message = Message(
        session_id=active_session.id,
        sender="neo",
        text=neo_response
    )
    db.add(neo_message)
    db.commit()
    
    return ChatResponse(
        response=neo_response,
        hint_given=hint_given,
        progress=current_progress,
        cracked=False
    )

# ============= HISTORY AND SESSIONS =============

@app.get("/api/history/{username}", response_model=List[MessageResponse])
def get_chat_history(username: str, db: Session = Depends(get_db)):
    """Get user chat history"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all user messages
    messages = db.query(Message).join(DBSession).filter(
        DBSession.user_id == user.id
    ).order_by(Message.timestamp.asc()).all()
    
    return messages

@app.get("/api/sessions/{username}", response_model=List[SessionResponse])
def get_user_sessions(username: str, db: Session = Depends(get_db)):
    """Get all user sessions"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    sessions = db.query(DBSession).filter(
        DBSession.user_id == user.id
    ).order_by(DBSession.started_at.desc()).all()
    
    return sessions

# ============= LEADERBOARD =============

@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get top players by attempts count (fewer attempts = better rank)"""
    # Update ranks based on attempts_count (ascending - fewer is better)
    entries = db.query(Leaderboard).order_by(
        Leaderboard.attempts_count.asc()
    ).all()
    
    # Assign ranks
    for idx, entry in enumerate(entries, start=1):
        entry.rank = idx
    db.commit()
    
    # Return top N
    return entries[:limit]

@app.get("/api/stats", response_model=StatsResponse)
def get_statistics(username: str = None, db: Session = Depends(get_db)):
    """Get general statistics"""
    total_users = db.query(User).count()
    total_attempts = db.query(func.sum(User.total_attempts)).scalar() or 0
    successful_cracks = 0  # Hidden - don't reveal crack success info
    
    your_rank = None
    if username:
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_cracked:
            leaderboard = db.query(Leaderboard).filter(
                Leaderboard.user_id == user.id
            ).first()
            if leaderboard:
                your_rank = leaderboard.rank
    
    return StatsResponse(
        total_users=total_users,
        total_attempts=total_attempts,
        successful_cracks=successful_cracks,
        your_rank=your_rank
    )

# ============= HELPER FUNCTIONS =============

def update_leaderboard_ranks(db: Session):
    """Update leaderboard ranks"""
    # Sort by attempts count only (fewer attempts = better rank)
    entries = db.query(Leaderboard).order_by(
        Leaderboard.attempts_count.asc()
    ).all()
    
    for idx, entry in enumerate(entries, start=1):
        entry.rank = idx
    
    db.commit()

# ============= PREDICTIONS =============

@app.get("/api/predictions", response_model=PredictionStats)
def get_predictions(username: str = None, db: Session = Depends(get_db)):
    """Get prediction voting statistics"""
    
    # Count total votes
    total_votes = db.query(Prediction).count()
    hold_votes = db.query(Prediction).filter(Prediction.choice == "hold").count()
    crack_votes = db.query(Prediction).filter(Prediction.choice == "crack").count()
    
    # Calculate percentages
    hold_percentage = (hold_votes / total_votes * 100) if total_votes > 0 else 50.0
    crack_percentage = (crack_votes / total_votes * 100) if total_votes > 0 else 50.0
    
    # Check if user has voted
    user_vote = None
    if username:
        existing_vote = db.query(Prediction).filter(Prediction.username == username).first()
        if existing_vote:
            user_vote = existing_vote.choice
    
    return PredictionStats(
        total_votes=total_votes,
        hold_votes=hold_votes,
        crack_votes=crack_votes,
        hold_percentage=round(hold_percentage, 1),
        crack_percentage=round(crack_percentage, 1),
        user_vote=user_vote
    )

@app.post("/api/predictions/vote")
def vote_prediction(username: str, vote_data: VoteCreate, db: Session = Depends(get_db)):
    """Submit or update a prediction vote"""
    
    # Validate choice
    if vote_data.choice not in ["hold", "crack"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid choice. Must be 'hold' or 'crack'"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has already voted
    existing_vote = db.query(Prediction).filter(Prediction.username == username).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.choice = vote_data.choice
        existing_vote.voted_at = datetime.utcnow()
    else:
        # Create new vote
        new_vote = Prediction(
            username=username,
            choice=vote_data.choice
        )
        db.add(new_vote)
    
    db.commit()
    
    # Return updated statistics
    return get_predictions(username=username, db=db)

# ============= ROOT =============

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "CRACK PROTOCOL API v1.0",
        "status": "active",
        "endpoints": {
            "register": "/api/auth/register",
            "chat": "/api/chat/{username}",
            "leaderboard": "/api/leaderboard",
            "stats": "/api/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
