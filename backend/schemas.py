from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# User schemas
class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    total_attempts: int
    is_cracked: bool
    
    class Config:
        from_attributes = True

# Message schemas
class MessageCreate(BaseModel):
    text: str

class MessageResponse(BaseModel):
    id: int
    sender: str
    text: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Chat response
class ChatResponse(BaseModel):
    response: str
    hint_given: bool = False
    progress: int  # 0-100
    cracked: bool = False
    secret_phrase: Optional[str] = None

# Session schemas
class SessionResponse(BaseModel):
    id: int
    started_at: datetime
    messages_count: int
    hints_given: int
    
    class Config:
        from_attributes = True

# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    rank: Optional[int] = 1
    username: str
    completion_time: int
    attempts_count: int
    completed_at: datetime
    
    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_users: int
    total_attempts: int
    successful_cracks: int
    your_rank: Optional[int] = None

# Prediction schemas
class VoteCreate(BaseModel):
    choice: str  # 'hold' or 'crack'

class PredictionStats(BaseModel):
    total_votes: int
    hold_votes: int
    crack_votes: int
    hold_percentage: float
    crack_percentage: float
    user_vote: Optional[str] = None  # 'hold', 'crack', or None
