from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from app.models.mixins.timestamp_mixin import TimestampMixin

class CallSession(SQLModel, TimestampMixin, table=True):
    """Model for storing call sessions and user interactions."""
    __tablename__ = "call_sessions"
    
    id: str = Field(primary_key=True, index=True, max_length=36)
    call_sid: str = Field(unique=True, index=True, max_length=50)
    twilio_call_sid: Optional[str] = Field(unique=True, index=True, max_length=50)
    from_number: str = Field(max_length=20)
    to_number: str = Field(max_length=20)
    status: str = Field(default="initiated", max_length=20)
    duration: int = Field(default=0)  # in seconds
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    initial_message: Optional[str] = None
    voice_id: Optional[str] = Field(max_length=50)
    
    # Relationships
    interactions: List["CallInteraction"] = Relationship(back_populates="call_session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    def __repr__(self):
        return f"<CallSession(id={self.id}, call_sid={self.call_sid}, status={self.status})>"

class CallInteraction(SQLModel, TimestampMixin, table=True):
    """Model for storing individual user interactions within a call."""
    __tablename__ = "call_interactions"
    
    id: str = Field(primary_key=True, index=True, max_length=36)
    call_session_id: str = Field(foreign_key="call_sessions.id")
    interaction_type: str = Field(max_length=20)  # "speech", "recording", "transcription"
    sequence_number: int = Field(default=0)
    
    # Speech recognition data
    speech_result: Optional[str] = None
    speech_confidence: Optional[float] = None
    speech_language: Optional[str] = Field(max_length=10)
    
    # Recording data
    recording_sid: Optional[str] = Field(max_length=50)
    recording_url: Optional[str] = Field(max_length=500)
    recording_duration: Optional[int] = None  # in seconds
    s3_audio_url: Optional[str] = Field(max_length=500)
    
    # Transcription data
    transcription_text: Optional[str] = None
    transcription_status: Optional[str] = Field(max_length=20)
    transcription_source: Optional[str] = Field(max_length=20)  # "twilio", "whisper"
    transcription_confidence: Optional[float] = None
    
    # Response data
    system_response: Optional[str] = None
    system_audio_url: Optional[str] = Field(max_length=500)
    
    # Metadata
    processing_time: Optional[float] = None  # in seconds
    error_message: Optional[str] = None
    
    # Relationships
    call_session: Optional[CallSession] = Relationship(back_populates="interactions")
    
    def __repr__(self):
        return f"<CallInteraction(id={self.id}, type={self.interaction_type}, sequence={self.sequence_number})>" 