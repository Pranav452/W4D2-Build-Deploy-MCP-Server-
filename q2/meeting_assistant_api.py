from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from sqlmodel import Session, select
from datetime import datetime, timedelta
import pytz

from models import (
    User, Meeting, Participant, AvailabilityWindow, MeetingAnalysis,
    MeetingType, MeetingStatus, UserRole, engine, create_db_and_tables
)
from ai_scheduler import AIScheduler

# Initialize FastAPI app
app = FastAPI(
    title="Smart Meeting Assistant API",
    description="AI-powered meeting scheduling and management system with conflict resolution and optimization",
    version="1.0.0"
)

# Initialize AI scheduler
ai_scheduler = AIScheduler()

# Pydantic models for API requests/responses
class MeetingCreateRequest(BaseModel):
    title: str
    participants: List[int]
    duration: int
    start_time: str
    timezone: str = "UTC"
    meeting_type: str = "team_meeting"
    description: Optional[str] = None
    location: Optional[str] = None
    organizer_id: int

class OptimalSlotsRequest(BaseModel):
    participants: List[int]
    duration: int
    start_date: str
    end_date: str
    timezone: str = "UTC"
    max_results: int = 10

class ConflictDetectionRequest(BaseModel):
    user_id: int
    start_time: str
    end_time: str

class MeetingPatternsRequest(BaseModel):
    user_id: int
    period: int = 30

class AgendaSuggestionsRequest(BaseModel):
    meeting_topic: str
    participants: List[int]
    duration: int

class WorkloadBalanceRequest(BaseModel):
    team_members: List[int]

class UserCreateRequest(BaseModel):
    name: str
    email: str
    role: str = "employee"
    timezone: str = "UTC"
    work_start_hour: int = 9
    work_end_hour: int = 17
    work_days: str = "1,2,3,4,5"

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    timezone: str
    work_start_hour: int
    work_end_hour: int
    max_meetings_per_day: int

class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    meeting_type: str
    start_time: str
    end_time: str
    timezone: str
    location: Optional[str]
    organizer_name: str
    status: str
    participant_count: int
    effectiveness_score: Optional[float] = None

class ScheduleOptimizationRequest(BaseModel):
    user_id: int

# Database dependency
def get_session():
    with Session(engine) as session:
        yield session

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

@app.on_event("shutdown")
async def shutdown_event():
    ai_scheduler.close_session()

@app.get("/")
async def root():
    return {
        "message": "Smart Meeting Assistant API",
        "version": "1.0.0",
        "features": [
            "AI-powered scheduling",
            "Conflict detection",
            "Optimal time suggestions",
            "Meeting pattern analysis",
            "Workload balancing",
            "Effectiveness scoring"
        ],
        "endpoints": {
            "meetings": "/meetings",
            "users": "/users",
            "schedule": "/schedule",
            "analytics": "/analytics"
        }
    }

# User Management Endpoints
@app.post("/users", response_model=Dict[str, Any])
async def create_user(user: UserCreateRequest, session: Session = Depends(get_session)):
    """Create a new user"""
    
    # Check if email already exists
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        name=user.name,
        email=user.email,
        role=UserRole(user.role),
        timezone=user.timezone,
        work_start_hour=user.work_start_hour,
        work_end_hour=user.work_end_hour,
        work_days=user.work_days
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return {
        "message": "User created successfully",
        "user_id": db_user.id,
        "name": db_user.name,
        "email": db_user.email
    }

@app.get("/users", response_model=List[UserResponse])
async def list_users(session: Session = Depends(get_session)):
    """List all users"""
    
    users = session.exec(select(User)).all()
    
    return [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            timezone=user.timezone,
            work_start_hour=user.work_start_hour,
            work_end_hour=user.work_end_hour,
            max_meetings_per_day=user.max_meetings_per_day
        )
        for user in users
    ]

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    """Get user by ID"""
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        timezone=user.timezone,
        work_start_hour=user.work_start_hour,
        work_end_hour=user.work_end_hour,
        max_meetings_per_day=user.max_meetings_per_day
    )

# Meeting Management Endpoints
@app.post("/meetings", response_model=Dict[str, Any])
async def create_meeting(meeting: MeetingCreateRequest, session: Session = Depends(get_session)):
    """Create a new meeting with AI conflict detection"""
    
    try:
        # Parse start time
        start_time = datetime.fromisoformat(meeting.start_time)
        if start_time.tzinfo is None:
            start_time = pytz.timezone(meeting.timezone).localize(start_time)
        
        end_time = start_time + timedelta(minutes=meeting.duration)
        
        # Verify organizer exists
        organizer = session.get(User, meeting.organizer_id)
        if not organizer:
            raise HTTPException(status_code=404, detail="Organizer not found")
        
        # Verify participants exist
        participants = session.exec(
            select(User).where(User.id.in_(meeting.participants))
        ).all()
        
        if len(participants) != len(meeting.participants):
            found_ids = [p.id for p in participants]
            missing_ids = [id for id in meeting.participants if id not in found_ids]
            raise HTTPException(status_code=404, detail=f"Participants not found: {missing_ids}")
        
        # Detect conflicts
        conflicts = []
        for participant_id in meeting.participants:
            participant_conflicts = ai_scheduler.detect_scheduling_conflicts(
                participant_id, start_time, end_time
            )
            conflicts.extend(participant_conflicts)
        
        # Create meeting
        db_meeting = Meeting(
            title=meeting.title,
            description=meeting.description,
            meeting_type=MeetingType(meeting.meeting_type),
            start_time=start_time,
            end_time=end_time,
            timezone=meeting.timezone,
            location=meeting.location,
            organizer_id=meeting.organizer_id,
            status=MeetingStatus.SCHEDULED
        )
        
        session.add(db_meeting)
        session.commit()
        session.refresh(db_meeting)
        
        # Add participants
        for participant_id in meeting.participants:
            participant = Participant(
                user_id=participant_id,
                meeting_id=db_meeting.id,
                is_required=True,
                response_status="pending"
            )
            session.add(participant)
        
        session.commit()
        
        return {
            "message": "Meeting created successfully",
            "meeting_id": db_meeting.id,
            "title": db_meeting.title,
            "conflicts_detected": len(conflicts) > 0,
            "conflicts": [
                {
                    "user_name": c.user_name,
                    "type": c.conflict_type,
                    "severity": c.severity,
                    "details": c.conflict_details
                }
                for c in conflicts
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating meeting: {str(e)}")

@app.get("/meetings", response_model=List[MeetingResponse])
async def list_meetings(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """List meetings with optional user filtering"""
    
    query = select(Meeting)
    
    if user_id:
        query = query.join(Participant).where(Participant.user_id == user_id)
    
    meetings = session.exec(query.offset(offset).limit(limit)).all()
    
    results = []
    for meeting in meetings:
        organizer = session.get(User, meeting.organizer_id)
        participant_count = session.exec(
            select(Participant).where(Participant.meeting_id == meeting.id)
        ).all()
        
        results.append(MeetingResponse(
            id=meeting.id,
            title=meeting.title,
            description=meeting.description,
            meeting_type=meeting.meeting_type.value,
            start_time=meeting.start_time.isoformat(),
            end_time=meeting.end_time.isoformat(),
            timezone=meeting.timezone,
            location=meeting.location,
            organizer_name=organizer.name if organizer else "Unknown",
            status=meeting.status.value,
            participant_count=len(participant_count),
            effectiveness_score=meeting.effectiveness_score
        ))
    
    return results

@app.get("/meetings/{meeting_id}", response_model=Dict[str, Any])
async def get_meeting(meeting_id: int, session: Session = Depends(get_session)):
    """Get detailed meeting information"""
    
    meeting = session.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get organizer
    organizer = session.get(User, meeting.organizer_id)
    
    # Get participants
    participants = session.exec(
        select(Participant).where(Participant.meeting_id == meeting_id)
    ).all()
    
    participant_details = []
    for participant in participants:
        user = session.get(User, participant.user_id)
        if user:
            participant_details.append({
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "response_status": participant.response_status,
                "is_required": participant.is_required
            })
    
    return {
        "meeting_id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "meeting_type": meeting.meeting_type.value,
        "start_time": meeting.start_time.isoformat(),
        "end_time": meeting.end_time.isoformat(),
        "duration_minutes": meeting.duration_minutes,
        "timezone": meeting.timezone,
        "location": meeting.location,
        "organizer": {
            "id": organizer.id,
            "name": organizer.name,
            "email": organizer.email
        } if organizer else None,
        "status": meeting.status.value,
        "participants": participant_details,
        "effectiveness_score": meeting.effectiveness_score,
        "productivity_rating": meeting.productivity_rating,
        "engagement_level": meeting.engagement_level
    }

# AI Scheduling Endpoints
@app.post("/schedule/find-optimal-slots", response_model=Dict[str, Any])
async def find_optimal_slots(request: OptimalSlotsRequest):
    """Find optimal time slots for a meeting"""
    
    try:
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # Localize to timezone
        tz = pytz.timezone(request.timezone)
        start_date = tz.localize(start_date)
        end_date = tz.localize(end_date)
        
        optimal_slots = ai_scheduler.find_optimal_time_slots(
            request.participants, request.duration, start_date, end_date,
            request.timezone, request.max_results
        )
        
        return {
            "search_criteria": {
                "participants": len(request.participants),
                "duration_minutes": request.duration,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            },
            "recommended_slots": [
                {
                    "rank": i + 1,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "score": round(slot.score, 2),
                    "availability_percentage": round(
                        (len(slot.participants_available) / len(request.participants)) * 100, 1
                    )
                }
                for i, slot in enumerate(optimal_slots)
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding optimal slots: {str(e)}")

@app.post("/schedule/detect-conflicts", response_model=Dict[str, Any])
async def detect_conflicts(request: ConflictDetectionRequest):
    """Detect scheduling conflicts for a user"""
    
    try:
        start_time = datetime.fromisoformat(request.start_time)
        end_time = datetime.fromisoformat(request.end_time)
        
        conflicts = ai_scheduler.detect_scheduling_conflicts(
            request.user_id, start_time, end_time
        )
        
        return {
            "user_id": request.user_id,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "conflicts_found": len(conflicts),
            "conflicts": [
                {
                    "type": c.conflict_type,
                    "severity": c.severity,
                    "time": c.conflict_time.isoformat(),
                    "details": c.conflict_details
                }
                for c in conflicts
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting conflicts: {str(e)}")

@app.post("/schedule/optimize", response_model=Dict[str, Any])
async def optimize_schedule(request: ScheduleOptimizationRequest):
    """Get schedule optimization recommendations"""
    
    try:
        optimization_data = ai_scheduler.optimize_meeting_schedule(request.user_id)
        return optimization_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing schedule: {str(e)}")

# Analytics Endpoints
@app.post("/analytics/meeting-patterns", response_model=Dict[str, Any])
async def analyze_meeting_patterns(request: MeetingPatternsRequest):
    """Analyze meeting patterns for a user"""
    
    try:
        patterns = ai_scheduler.analyze_meeting_patterns(request.user_id, request.period)
        return patterns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing patterns: {str(e)}")

@app.post("/analytics/workload-balance", response_model=Dict[str, Any])
async def calculate_workload_balance(request: WorkloadBalanceRequest):
    """Calculate workload balance across team members"""
    
    try:
        balance_data = ai_scheduler.calculate_workload_balance(request.team_members)
        return balance_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating workload balance: {str(e)}")

@app.post("/analytics/effectiveness/{meeting_id}", response_model=Dict[str, Any])
async def score_meeting_effectiveness(meeting_id: int):
    """Score meeting effectiveness"""
    
    try:
        effectiveness_data = ai_scheduler.score_meeting_effectiveness(meeting_id)
        return effectiveness_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring effectiveness: {str(e)}")

# AI-Powered Features
@app.post("/ai/generate-agenda", response_model=Dict[str, Any])
async def generate_agenda(request: AgendaSuggestionsRequest):
    """Generate AI-powered agenda suggestions"""
    
    try:
        agenda_items = ai_scheduler.generate_agenda_suggestions(
            request.meeting_topic, request.participants, request.duration
        )
        
        return {
            "meeting_topic": request.meeting_topic,
            "duration_minutes": request.duration,
            "participant_count": len(request.participants),
            "suggested_agenda": agenda_items
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating agenda: {str(e)}")

# Health Check and Status
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/stats")
async def get_stats(session: Session = Depends(get_session)):
    """Get system statistics"""
    
    total_users = session.exec(select(User)).all()
    total_meetings = session.exec(select(Meeting)).all()
    
    # Calculate some basic stats
    completed_meetings = [m for m in total_meetings if m.status == MeetingStatus.COMPLETED]
    upcoming_meetings = [m for m in total_meetings if m.status == MeetingStatus.SCHEDULED and m.start_time > datetime.now()]
    
    return {
        "total_users": len(total_users),
        "total_meetings": len(total_meetings),
        "completed_meetings": len(completed_meetings),
        "upcoming_meetings": len(upcoming_meetings),
        "average_effectiveness": sum(m.effectiveness_score for m in completed_meetings if m.effectiveness_score) / len([m for m in completed_meetings if m.effectiveness_score]) if completed_meetings else 0,
        "timezone_distribution": {
            tz: len([u for u in total_users if u.timezone == tz])
            for tz in set(u.timezone for u in total_users)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 