from sqlmodel import SQLModel, Field, Relationship, create_engine, Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import json
import pytz


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    GUEST = "guest"


class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MeetingType(str, Enum):
    ONE_ON_ONE = "one_on_one"
    TEAM_MEETING = "team_meeting"
    ALL_HANDS = "all_hands"
    CLIENT_MEETING = "client_meeting"
    INTERVIEW = "interview"
    TRAINING = "training"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
    role: UserRole = Field(default=UserRole.EMPLOYEE)
    timezone: str = Field(default="UTC")  # e.g., "America/New_York"
    
    # Working hours preferences (in user's timezone)
    work_start_hour: int = Field(default=9)  # 9 AM
    work_end_hour: int = Field(default=17)   # 5 PM
    work_days: str = Field(default="1,2,3,4,5")  # Monday-Friday (1-7)
    
    # Meeting preferences
    max_meetings_per_day: int = Field(default=8)
    preferred_meeting_duration: int = Field(default=30)  # minutes
    buffer_time: int = Field(default=15)  # minutes between meetings
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    organized_meetings: List["Meeting"] = Relationship(back_populates="organizer")
    participations: List["Participant"] = Relationship(back_populates="user")
    availability_windows: List["AvailabilityWindow"] = Relationship(back_populates="user")

    def get_work_days_list(self) -> List[int]:
        """Convert work_days string to list of integers"""
        return [int(day) for day in self.work_days.split(",") if day.strip()]

    def is_work_day(self, day_of_week: int) -> bool:
        """Check if a day is a work day (1=Monday, 7=Sunday)"""
        return day_of_week in self.get_work_days_list()

    def get_timezone(self) -> timezone:
        """Get user's timezone object"""
        return pytz.timezone(self.timezone)


class Meeting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    meeting_type: MeetingType = Field(default=MeetingType.TEAM_MEETING)
    
    # Timing
    start_time: datetime
    end_time: datetime
    timezone: str = Field(default="UTC")
    
    # Meeting details
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    agenda: Optional[str] = None
    
    # Organization
    organizer_id: int = Field(foreign_key="user.id")
    status: MeetingStatus = Field(default=MeetingStatus.SCHEDULED)
    
    # AI insights
    effectiveness_score: Optional[float] = None  # 0-10 scale
    productivity_rating: Optional[float] = None  # 0-10 scale
    engagement_level: Optional[float] = None     # 0-10 scale
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    organizer: Optional[User] = Relationship(back_populates="organized_meetings")
    participants: List["Participant"] = Relationship(back_populates="meeting")
    analyses: List["MeetingAnalysis"] = Relationship(back_populates="meeting")
    
    @property
    def duration_minutes(self) -> int:
        """Get meeting duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def get_timezone(self) -> timezone:
        """Get meeting's timezone object"""
        return pytz.timezone(self.timezone)


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    meeting_id: int = Field(foreign_key="meeting.id")
    
    # Participation details
    is_required: bool = Field(default=True)
    response_status: str = Field(default="pending")  # pending, accepted, declined, tentative
    attended: Optional[bool] = None
    
    # Engagement metrics
    participation_level: Optional[float] = None  # 0-10 scale
    contribution_score: Optional[float] = None   # 0-10 scale
    
    # Metadata
    invited_at: datetime = Field(default_factory=datetime.now)
    responded_at: Optional[datetime] = None
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="participations")
    meeting: Optional[Meeting] = Relationship(back_populates="participants")


class AvailabilityWindow(SQLModel, table=True):
    """User's availability windows for scheduling"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    # Time window
    start_time: datetime
    end_time: datetime
    timezone: str = Field(default="UTC")
    
    # Availability details
    is_available: bool = Field(default=True)
    priority: int = Field(default=1)  # 1=highest, 5=lowest
    reason: Optional[str] = None  # e.g., "Out of office", "Focus time"
    
    # Recurrence (for recurring availability)
    is_recurring: bool = Field(default=False)
    recurrence_pattern: Optional[str] = None  # JSON string
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="availability_windows")


class MeetingAnalysis(SQLModel, table=True):
    """AI analysis results for meetings"""
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.id")
    
    # Pattern analysis
    meeting_frequency_score: Optional[float] = None  # How often this type of meeting occurs
    duration_appropriateness: Optional[float] = None  # Was duration appropriate?
    timing_effectiveness: Optional[float] = None     # Was timing good for participants?
    
    # Workload analysis
    organizer_workload_impact: Optional[float] = None
    participant_workload_impact: Optional[float] = None
    
    # Effectiveness metrics
    agenda_quality_score: Optional[float] = None
    participant_balance_score: Optional[float] = None
    follow_up_clarity: Optional[float] = None
    
    # Optimization suggestions
    suggested_duration: Optional[int] = None  # minutes
    suggested_time_slots: Optional[str] = None  # JSON array of time slots
    improvement_suggestions: Optional[str] = None  # JSON array of suggestions
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)
    analysis_version: str = Field(default="1.0")
    
    # Relationships
    meeting: Optional[Meeting] = Relationship(back_populates="analyses")
    
    def get_suggested_time_slots(self) -> List[Dict[str, Any]]:
        """Convert suggested time slots JSON to list"""
        return json.loads(self.suggested_time_slots) if self.suggested_time_slots else []
    
    def get_improvement_suggestions(self) -> List[str]:
        """Convert improvement suggestions JSON to list"""
        return json.loads(self.improvement_suggestions) if self.improvement_suggestions else []


class MeetingPattern(SQLModel, table=True):
    """Analyzed patterns for recurring meetings and user behavior"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id", default=None)
    
    # Pattern identification
    pattern_type: str  # "daily_peak", "weekly_pattern", "meeting_type_frequency"
    pattern_name: str
    pattern_data: str  # JSON data about the pattern
    
    # Pattern metrics
    confidence_score: float = Field(default=0.0)  # 0-1 confidence in pattern
    frequency: int = Field(default=1)  # How often pattern occurs
    impact_score: float = Field(default=0.0)  # Impact on productivity
    
    # Time period
    start_date: datetime
    end_date: datetime
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def get_pattern_data(self) -> Dict[str, Any]:
        """Convert pattern data JSON to dict"""
        return json.loads(self.pattern_data) if self.pattern_data else {}


# Database setup
DATABASE_URL = "sqlite:///./meeting_assistant.db"
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session 